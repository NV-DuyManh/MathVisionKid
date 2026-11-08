"""Bounded Vietnamese speech synthesis. No model calls."""
import asyncio
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import textwrap
import threading
import time
import wave

import aiohttp
import edge_tts

from app.config import settings
from app.tutoring.azure_speech import AzureSpeechError, azure_pcm
from app.tutoring.service import TutorUnavailable

SPEECH_VOICES = ('vi-VN-NamMinhNeural', 'vi-VN-HoaiMyNeural')
DEFAULT_VOICE = SPEECH_VOICES[0]
logger = logging.getLogger(__name__)
# Shared across lesson, Q&A and Quiz worker threads; each render may use two turns.
_provider_slots = threading.BoundedSemaphore(4)
_edge_backoff_lock = threading.Lock()
_edge_unavailable_until: dict[str, float] = {}
_edge_failures: dict[str, int] = {}
EDGE_BACKOFF_SECONDS = 15


async def _with_provider_slot(call):
    # Do not block an event loop or leave a detached semaphore acquisition on cancellation.
    while not _provider_slots.acquire(blocking=False):
        await asyncio.sleep(.02)
    try:
        return await call()
    finally:
        _provider_slots.release()


class SpeechNoAudio(TutorUnavailable):
    """The chosen provider returned no audio after its bounded transport retries."""


def wait_for_speech_retry(voice, deadline, check=None):
    """Respect the shared voice cooldown without holding a render/provider slot."""
    with _edge_backoff_lock:
        until = _edge_unavailable_until.get(voice, 0)
    remaining = until - time.monotonic()
    if max(.25, remaining) >= deadline - time.monotonic():
        raise SpeechNoAudio()
    if remaining <= 0:
        if check: check()
        time.sleep(.25)
    else:
        while (remaining := until - time.monotonic()) > 0:
            if check: check()
            time.sleep(min(.2, remaining))
    if check: check()


def _spoken_groups(text):
    # Read labels without bracket names, while retaining arithmetic precedence.
    previous = None
    while text != previous and '(' in text:
        previous = text
        text = re.sub(r'\(([^()]*)\)', lambda m:
            f'nhóm {m[1]}, hết nhóm' if re.search(r'\d', m[1]) and re.search(r'[+\-−×*÷/:]|\b(?:cộng|trừ|nhân|chia|phần)\b', m[1])
                or 'hết nhóm' in m[1] else f' {m[1]} ', text)
    return re.sub(r'[()]', ' ', text)


def spoken_math(text: str) -> str:
    text = re.sub(r'\b((?:Bài|Câu)\s+\d+)\s*[:.)]\s*', r'\1. ', text, flags=re.I)
    # Spelling hyphens in Vietnamese unit names are not subtraction signs.
    text = re.sub(r'(?<!\w)(?:đề|đê|xăng|xen|ki|mi)[\s\-‐‑‒–—−]+(?:xi|ti|lô|li)[\s\-‐‑‒–—−]+(?:mét|gam|lít)(?:[\s\-‐‑‒–—−]+(?:vuông|khối))?(?!\w)',
                  lambda match: re.sub(r'[-‐‑‒–—−]', ' ', match[0]), text, flags=re.I)
    text = re.sub(r'(?:mét|gam|lít)[\-‐‑‒–—−]+(?:vuông|khối)', lambda m: re.sub(r'[-‐‑‒–—−]', ' ', m[0]), text, flags=re.I)
    text = re.sub(r'\bhéc\s*[\-‐‑‒–—−]\s*ta\b', 'héc ta', text, flags=re.I)
    text = re.sub(r'(\d|\b(?:sang|theo|bằng|đơn vị|bao nhiêu))\s*(?:\(\s*ha\s*\)|ha\b)', r'\1 héc ta', text, flags=re.I)
    text = re.sub(r'\s*\(\s*\d+(?:[.,]\d+)?\s*điểm\s*\)\s*,?\s*', ' ', text, flags=re.I)
    text = re.sub(r'\b((?:Bài|Câu)\s+\d+)\.\s*\.', r'\1.', text, flags=re.I)
    text = re.sub(r'\(\s*((?:(?:ki lô|đề xi|xăng ti|mi li)\s+)?(?:mét|gam|lít)(?:\s+(?:vuông|khối))?)\s*\)', r' \1 ', text, flags=re.I)
    text = re.sub(r'\(\s*([+-]?\d+(?:[.,]\d+)?)\s*\)\s*/\s*\(\s*([+-]?\d+(?:[.,]\d+)?)\s*\)', r'\1/\2', text)
    text = re.sub(r'(^|[=(:,+*×÷/\-−]\s*)[-−]\s*(?=\d)',r'\1âm ',text)
    units={'km':'ki lô mét','dm':'đề xi mét','cm':'xăng ti mét','mm':'mi li mét','m':'mét',
           'kg':'ki lô gam','mg':'mi li gam','g':'gam','ml':'mi li lít','l':'lít'}
    unit_names='km|dm|cm|mm|kg|mg|ml|m|g|l'
    # Accept common OCR/plain-text exponents without interpreting an expression.
    text = re.sub(r'(?<![^\W\d_])(km|dm|cm|mm|m)(?:\^\{([23])\}|\^?([23]))(?!\w)',
                  lambda m: m[1]+{'2':'²','3':'³'}[m[2] or m[3]], text)
    # Unit brackets are labels; preserve all grouping brackets in calculations.
    text = re.sub(r'\(\s*((?:'+unit_names+r')(?:[²³])?)\s*\)', r' \1 ', text)
    text = re.sub(r'(?<![^\W\d_])('+unit_names+r')([²³])?(?!\w)',
                  lambda m:' '+units[m[1]]+({'²':' vuông','³':' khối'}.get(m[2],''))+' ',text)
    text = re.sub(r'(?<![\d/])(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)(?![\d/])', r'\1 phần \2', text)
    text = re.sub(r'(\d|\))\s*x\s*(?=[(\d])', r'\1 nhân ', text)
    text = re.sub(r'(?<=[\d)])\s*:\s*(?=[(\d]|âm\s+\d)',' chia ',text)
    for symbol, word in [('+',' cộng '), ('−',' trừ '), ('-',' trừ '), ('×',' nhân '),
                         ('*',' nhân '), ('÷',' chia '), ('/',' chia '), ('=',' bằng '), ('%',' phần trăm ')]:
        text = text.replace(symbol, word)
    return re.sub(r'\s+', ' ', _spoken_groups(text)).strip()


def run(args, deadline, **kwargs):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError('Audio synthesis deadline')
    return subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=min(25, remaining), **kwargs)


def synthesize(text: str, path: Path, deadline: float, max_seconds=65):
    # Keep the established offline speech renderer independent of online provider outages.
    if os.name == 'nt':
        script = r'''$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue';
        Add-Type -AssemblyName System.Runtime.WindowsRuntime;
        $p=ConvertFrom-Json([Console]::In.ReadToEnd());
        $s=New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer;
        $voices=[Windows.Media.SpeechSynthesis.SpeechSynthesizer,Windows.Media.SpeechSynthesis,ContentType=WindowsRuntime]::AllVoices;
        try { $v=$voices | Where-Object {$_.Language -eq 'vi-VN'} | Select-Object -First 1;
        if (!$v) {throw 'Vietnamese voice unavailable'};
        $s.Voice=$v; $s.Options.SpeakingRate=0.9;
        $method=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {$_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'} | Select-Object -First 1;
        $resultType=[Windows.Media.SpeechSynthesis.SpeechSynthesisStream,Windows.Media.SpeechSynthesis,ContentType=WindowsRuntime];
        $task=$method.MakeGenericMethod($resultType).Invoke($null,@($s.SynthesizeTextToStreamAsync($p.text))); $task.Wait();
        $stream=[System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($task.Result);
        $file=[IO.File]::Create($p.path);try{$stream.CopyTo($file)}finally{$file.Dispose();$stream.Dispose()}
        } finally {if($s -is [IDisposable]){([IDisposable]$s).Dispose()}}'''
        run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script], deadline,
            input=json.dumps({'text': spoken_math(text), 'path': str(path)}).encode('ascii'),
            creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        engine = shutil.which('espeak-ng')
        if not engine:
            raise RuntimeError('Vietnamese speech engine unavailable')
        run([engine, '-v','vi','-s','150','-w',str(path),'--stdin'], deadline,
            input=spoken_math(text).encode('utf-8'))
    with wave.open(str(path), 'rb') as audio:
        duration = audio.getnframes() / audio.getframerate()
        if audio.getnframes() == 0 or not .1 < duration < max_seconds:
            raise ValueError('Invalid narration duration')
    return duration


async def _neural_chunk(text: str, voice: str) -> bytes:
    # A voice outage must not multiply retries across chunks, background jobs and Quiz.
    with _edge_backoff_lock:
        if _edge_unavailable_until.get(voice, 0) > time.monotonic():
            raise SpeechNoAudio()
    for attempt in range(3):
        result = bytearray()
        started = time.monotonic()
        first_audio_ms = -1
        outcome = 'cancelled'
        speech = edge_tts.Communicate(text, voice, rate='+0%', connect_timeout=5, receive_timeout=10)
        try:
            async for chunk in speech.stream():
                if chunk['type'] == 'audio':
                    if first_audio_ms < 0:
                        first_audio_ms = int((time.monotonic() - started) * 1000)
                    result.extend(chunk['data'])
                    if len(result) > 2 * 1024 * 1024:
                        raise ValueError('Speech exceeds audio limit')
            if len(result) < 128:
                raise ValueError('Empty speech response')
            outcome = 'ready'
            with _edge_backoff_lock:
                _edge_unavailable_until.pop(voice, None)
                _edge_failures.pop(voice, None)
            return bytes(result)
        except (edge_tts.exceptions.NoAudioReceived, TimeoutError, aiohttp.ClientConnectionError) as exc:
            outcome = type(exc).__name__
            if isinstance(exc, edge_tts.exceptions.NoAudioReceived) and attempt >= 1:
                with _edge_backoff_lock:
                    now = time.monotonic()
                    # A transient empty response should recover promptly. Sustained
                    # outages back off, once per voice/window across concurrent chunks.
                    if _edge_unavailable_until.get(voice, 0) <= now:
                        failures = min(5, _edge_failures.get(voice, 0) + 1)
                        _edge_failures[voice] = failures
                        _edge_unavailable_until[voice] = now + min(EDGE_BACKOFF_SECONDS, 2 ** (failures - 1))
                raise
            if attempt == 2:
                raise
            await asyncio.sleep(.25 * (attempt + 1))
        except Exception as exc:
            outcome = type(exc).__name__
            raise
        finally:
            # Transport timing only: no pupil text, request IDs, URLs or exception messages.
            logger.info('Vietnamese speech turn attempt=%d first_audio_ms=%d total_ms=%d bytes=%d outcome=%s',
                        attempt + 1, first_audio_ms, (time.monotonic()-started)*1000, len(result), outcome)


async def _neural_audio(text: str, voice: str, on_progress=None, checkpoint=None, paragraphs=None, *, reused_pcm=None):
    # Long provider turns can stall past our deadline. Keep every word, in order,
    # and synthesize at most two short turns concurrently (four across both render slots).
    layout = [(index, part) for index, paragraph in enumerate(paragraphs or [text])
              for part in textwrap.wrap(paragraph, width=220, break_long_words=False, break_on_hyphens=False)]
    missing = [(index, paragraph, part) for index, (paragraph, part) in enumerate(layout)
               if not reused_pcm or paragraph not in reused_pcm]
    if not missing and reused_pcm:
        return [], []
    slots = asyncio.Semaphore(2)
    total = 0
    completed = len(layout) - len(missing)

    async def render(index, part):
        nonlocal total, completed
        async with slots:
            data = checkpoint[0](index) if checkpoint else None
            if data is None:
                data = await _with_provider_slot(lambda: _neural_chunk(part, voice))
                if checkpoint: checkpoint[1](index, data)
            total += len(data)
            if total > 2 * 1024 * 1024:
                raise ValueError('Speech exceeds audio limit')
            completed += 1
            if on_progress:
                on_progress('synthesizing', 10 + int(70 * completed / len(layout)), completed, len(layout))
            return data

    # Use original chunk indexes so a retry can safely reuse its checkpoint
    # even if some paragraph WAVs are evicted between attempts.
    tasks = [asyncio.create_task(render(index, part)) for index, _, part in missing]
    try:
        chunks = await asyncio.gather(*tasks)
        data = b''.join(chunks)
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    if not 128 <= len(data) <= 2 * 1024 * 1024:
        raise ValueError('Invalid complete speech response')
    return (chunks, [paragraph for _, paragraph, _ in missing]) if paragraphs is not None else data


def synthesize_neural(text: str, path: Path, deadline: float, max_seconds=240, voice=DEFAULT_VOICE, on_progress=None, cancel_event=None, checkpoint=None, paragraphs=None, *, reused_pcm=None):
    if voice not in SPEECH_VOICES:
        raise ValueError('Unsupported narration voice')
    official = settings.speech_provider == 'azure'
    ffmpeg = None if official else shutil.which('ffmpeg')
    remaining = min(30, deadline - time.monotonic())
    reused_pcm = reused_pcm or {}
    if (not official and not ffmpeg and len(reused_pcm) != len(paragraphs or [text])) or remaining <= 0:
        raise TutorUnavailable()

    async def bounded_audio():
        if official and paragraphs is not None:
            slots = asyncio.Semaphore(2)
            completed = len(reused_pcm)
            indexes = [index for index in range(len(paragraphs)) if index not in reused_pcm]
            async def render_paragraph(part):
                nonlocal completed
                async with slots:
                    pcm = await _with_provider_slot(lambda: azure_pcm(spoken_math(part), voice))
                    completed += 1
                    if on_progress: on_progress('synthesizing', 10+int(70*completed/len(paragraphs)), completed, len(paragraphs))
                    return pcm
            async def aligned():
                tasks = [asyncio.create_task(render_paragraph(paragraphs[index])) for index in indexes]
                try: return await asyncio.gather(*tasks), indexes
                finally:
                    for task in tasks:
                        if not task.done(): task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
            work = aligned()
        elif official:
            # The official route returns complete PCM. Never mix its bytes with Edge MP3 checkpoints.
            work = _with_provider_slot(lambda: azure_pcm(spoken_math(text), voice))
        elif paragraphs is not None:
            options = {'reused_pcm': reused_pcm} if reused_pcm else {}
            work = _neural_audio(spoken_math(text), voice, on_progress, checkpoint, [spoken_math(part) for part in paragraphs], **options)
        elif checkpoint is not None:
            work = _neural_audio(spoken_math(text), voice, on_progress, checkpoint)
        else:
            work = _neural_audio(spoken_math(text), voice, on_progress) if on_progress else _neural_audio(spoken_math(text), voice)
        if cancel_event is None:
            return await asyncio.wait_for(work, timeout=remaining)
        task = asyncio.create_task(work)
        try:
            async with asyncio.timeout(remaining):
                while not task.done():
                    if cancel_event.is_set(): raise InterruptedError('Speculative speech yielded')
                    await asyncio.wait({task}, timeout=.05)
                return await task
        finally:
            if not task.done(): task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    source = path.with_suffix('.mp3')
    started = time.monotonic()
    try:
        data = asyncio.run(bounded_audio())
        received = time.monotonic()
        if on_progress:
            on_progress('decoding', 90)
        if time.monotonic() >= deadline:
            raise TimeoutError('Narration deadline')
        if paragraphs is not None:
            from app.tutoring.audio_cues import join_pcm
            chunks, indexes = data
            if official or not chunks:
                pcm = chunks
            else:
                # Decode all provider turns in one process. Boundaries use actual
                # decoded frame counts, including encoder padding; never text length.
                inputs = []
                outputs = []
                for index, chunk in enumerate(chunks):
                    part = path.with_name(f'part-{index}.mp3'); part.write_bytes(chunk)
                    inputs += ['-i', str(part)]
                    target = path.with_name(f'part-{index}.pcm')
                    outputs += ['-map', f'{index}:a:0', '-ar', '16000', '-ac', '1', '-f', 's16le', '-threads', '1', str(target)]
                run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', *inputs, *outputs], deadline)
                pcm = [path.with_name(f'part-{index}.pcm').read_bytes() for index in range(len(chunks))]
            segments = list(zip(indexes, pcm, strict=True))
            segments.extend(reused_pcm.items())
            segments.sort(key=lambda segment: segment[0])
            if sum(len(part) for _, part in segments) >= max_seconds * 32000:
                raise ValueError('Speech exceeds duration limit')
            path.write_bytes(join_pcm([part for _, part in segments], [index for index, _ in segments]))
        elif official:
            with wave.open(str(path), 'wb') as audio:
                audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(16000)
                audio.writeframes(data)
        else:
            source.write_bytes(data)
            run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
                 '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', '-threads', '1', str(path)], deadline)
        logger.info('Vietnamese narration synthesized provider=%s provider_ms=%d decode_ms=%d reused_paragraphs=%d',
                    'azure' if official else 'edge', (received-started)*1000, (time.monotonic()-received)*1000, len(reused_pcm))
    except Exception as exc:
        # Provider errors may contain URLs/text. Never log their messages or fall back to an unrelated voice.
        category = exc.category if isinstance(exc, AzureSpeechError) else type(exc).__name__
        logger.warning('Vietnamese narration unavailable category=%s', category)
        path.unlink(missing_ok=True)
        if isinstance(exc, (edge_tts.exceptions.NoAudioReceived, SpeechNoAudio)):
            raise SpeechNoAudio() from None
        raise TutorUnavailable() from None
    finally:
        source.unlink(missing_ok=True)
    with wave.open(str(path), 'rb') as audio:
        duration = audio.getnframes() / audio.getframerate()
        if audio.getnframes() == 0 or not .1 < duration < max_seconds:
            raise ValueError('Invalid narration duration')
    return duration

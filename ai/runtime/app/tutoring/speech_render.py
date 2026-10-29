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
import time
import wave

import edge_tts

from app.config import settings
from app.tutoring.azure_speech import AzureSpeechError, azure_pcm
from app.tutoring.service import TutorUnavailable

SPEECH_VOICES = ('vi-VN-NamMinhNeural', 'vi-VN-HoaiMyNeural')
DEFAULT_VOICE = SPEECH_VOICES[0]
logger = logging.getLogger(__name__)


class SpeechNoAudio(TutorUnavailable):
    """The chosen provider returned no audio after its bounded transport retries."""




def spoken_math(text: str) -> str:
    text = re.sub(r'\b((?:Bài|Câu)\s+\d+)\s*[:.)]\s*', r'\1. ', text, flags=re.I)
    # Spelling hyphens in Vietnamese unit names are not subtraction signs.
    text = re.sub(r'(?<!\w)(?:đề|đê|xăng|ki|mi)[\s\-‐‑–]+(?:xi|ti|lô|li)[\s\-‐‑–]+(?:mét|gam|lít)(?!\w)',
                  lambda match: re.sub(r'[-‐‑–]', ' ', match[0]), text, flags=re.I)
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
    return re.sub(r'\s+', ' ', text.replace('(', ' mở ngoặc ').replace(')', ' đóng ngoặc ')).strip()


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
    # Retry transient empty turns within one total deadline; never return partial audio or change the chosen voice.
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
            return bytes(result)
        except (edge_tts.exceptions.NoAudioReceived, TimeoutError) as exc:
            outcome = type(exc).__name__
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


async def _neural_audio(text: str, voice: str, on_progress=None, checkpoint=None, paragraphs=None):
    # Long provider turns can stall past our deadline. Keep every word, in order,
    # and synthesize at most two short turns concurrently (four across both render slots).
    layout = [(index, part) for index, paragraph in enumerate(paragraphs or [text])
              for part in textwrap.wrap(paragraph, width=220, break_long_words=False, break_on_hyphens=False)]
    parts = [part for _,part in layout]
    slots = asyncio.Semaphore(2)
    total = 0
    completed = 0

    async def render(index, part):
        nonlocal total, completed
        async with slots:
            data = checkpoint[0](index) if checkpoint else None
            if data is None:
                data = await _neural_chunk(part, voice)
                if checkpoint: checkpoint[1](index, data)
            total += len(data)
            if total > 2 * 1024 * 1024:
                raise ValueError('Speech exceeds audio limit')
            completed += 1
            if on_progress:
                on_progress('synthesizing', 10 + int(70 * completed / len(parts)), completed, len(parts))
            return data

    tasks = [asyncio.create_task(render(index, part)) for index, part in enumerate(parts)]
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
    return (chunks, [index for index,_ in layout]) if paragraphs is not None else data


def synthesize_neural(text: str, path: Path, deadline: float, max_seconds=240, voice=DEFAULT_VOICE, on_progress=None, cancel_event=None, checkpoint=None, paragraphs=None):
    if voice not in SPEECH_VOICES:
        raise ValueError('Unsupported narration voice')
    official = settings.speech_provider == 'azure'
    ffmpeg = None if official else shutil.which('ffmpeg')
    remaining = min(30, deadline - time.monotonic())
    if (not official and not ffmpeg) or remaining <= 0:
        raise TutorUnavailable()

    async def bounded_audio():
        if official and paragraphs is not None:
            slots = asyncio.Semaphore(2)
            completed = 0
            async def render_paragraph(part):
                nonlocal completed
                async with slots:
                    pcm = await azure_pcm(spoken_math(part), voice)
                    completed += 1
                    if on_progress: on_progress('synthesizing', 10+int(70*completed/len(paragraphs)), completed, len(paragraphs))
                    return pcm
            async def aligned():
                tasks = [asyncio.create_task(render_paragraph(part)) for part in paragraphs]
                try: return await asyncio.gather(*tasks), list(range(len(paragraphs)))
                finally:
                    for task in tasks:
                        if not task.done(): task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
            work = aligned()
        elif official:
            # The official route returns complete PCM. Never mix its bytes with Edge MP3 checkpoints.
            work = azure_pcm(spoken_math(text), voice)
        elif paragraphs is not None:
            work = _neural_audio(spoken_math(text), voice, on_progress, checkpoint, [spoken_math(part) for part in paragraphs])
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
            if official:
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
            path.write_bytes(join_pcm(pcm, indexes))
        elif official:
            with wave.open(str(path), 'wb') as audio:
                audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(16000)
                audio.writeframes(data)
        else:
            source.write_bytes(data)
            run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
                 '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', '-threads', '1', str(path)], deadline)
        logger.info('Vietnamese narration synthesized provider=%s provider_ms=%d decode_ms=%d',
                    'azure' if official else 'edge', (received-started)*1000, (time.monotonic()-received)*1000)
    except Exception as exc:
        # Provider errors may contain URLs/text. Never log their messages or fall back to an unrelated voice.
        category = exc.category if isinstance(exc, AzureSpeechError) else type(exc).__name__
        logger.warning('Vietnamese narration unavailable category=%s', category)
        path.unlink(missing_ok=True)
        if isinstance(exc,edge_tts.exceptions.NoAudioReceived):raise SpeechNoAudio() from None
        raise TutorUnavailable() from None
    finally:
        source.unlink(missing_ok=True)
    with wave.open(str(path), 'rb') as audio:
        duration = audio.getnframes() / audio.getframerate()
        if audio.getnframes() == 0 or not .1 < duration < max_seconds:
            raise ValueError('Invalid narration duration')
    return duration

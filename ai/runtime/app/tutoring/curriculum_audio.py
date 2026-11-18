"""Pre-rendered public curriculum speech, after the normal session/text gate."""
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import re
import wave
import zlib
from zipfile import ZipFile, BadZipFile

from app.tutoring.audio_cues import join_pcm

AUDIO_DIRECTORY = Path(__file__).with_name('data') / 'curriculum_audio'
MAX_PARAGRAPH_BYTES = 2 * 1024 * 1024


def paragraph_key(text):
    return sha256(' '.join(text.split()).encode('utf-8')).hexdigest()


@lru_cache(maxsize=1)
def manifest():
    path = AUDIO_DIRECTORY / 'manifest.json'
    try:
        if path.stat().st_size > 500_000:
            return {}
        document = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(document, dict):
            return {}
        if document.get('version') != 1 or document.get('voice') != 'Microsoft An (vi-VN)':
            return {}
        entries = document['paragraphs']
        if not isinstance(entries, dict) or len(entries) > 3000:
            return {}
        if any(not re.fullmatch('[a-f0-9]{64}', key) or not re.fullmatch('[a-f0-9]{64}', value)
               for key, value in entries.items()):
            return {}
        return entries
    except (OSError, KeyError, TypeError, ValueError):
        return {}


def load_audio(request):
    # The named neural voices keep their own transport and cache identity.
    if not request.useFallback:
        return None
    entries = manifest()
    keys = [paragraph_key(text) for text in request.paragraphs]
    if not keys or any(key not in entries for key in keys):
        return None
    chunks = []
    try:
        total = 0
        for key in keys:
            with ZipFile(AUDIO_DIRECTORY / f'public_speech_{key[0]}.zip') as archive:
                name = key + '.pcm'
                if archive.getinfo(name).file_size > MAX_PARAGRAPH_BYTES:
                    return None
                pcm = archive.read(name)
                if (len(pcm) % 2 or not pcm or not any(pcm)
                        or sha256(pcm).hexdigest() != entries[key]):
                    return None
            total += len(pcm)
            if total >= 240 * 32000:
                return None
            chunks.append(pcm)
        return join_pcm(chunks, list(range(len(chunks))))
    except (OSError, ValueError, KeyError, BadZipFile, zlib.error, wave.Error, EOFError):
        return None

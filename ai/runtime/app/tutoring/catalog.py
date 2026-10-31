"""Exact-source reuse after the normal review; account isolation is never relaxed."""
from functools import lru_cache
from hashlib import sha256
import json
import logging
from pathlib import Path
import sqlite3
import wave
from app.config import settings
from app.tutoring.catalog_store import CatalogStore,normalized_source

logger=logging.getLogger(__name__)


@lru_cache(maxsize=2)
def policy(kind):
    folder=Path(__file__).resolve().parent
    names=['lesson.py','service.py'] if kind=='plan' else ['speech_render.py','narration.py','audio_cues.py','azure_speech.py']
    if kind=='plan':names+=['digit_append.py','fraction_remainder.py']
    content=b'catalog-v1'+b''.join((folder/name).read_bytes() for name in names if (folder/name).is_file())
    return sha256(content).hexdigest()


def store():
    return CatalogStore(settings.lesson_catalog_path,ttl=settings.lesson_catalog_ttl_days*86400,
                        max_entries=settings.lesson_catalog_max_entries,max_audio_bytes=settings.lesson_catalog_audio_mb*1024*1024)


def identity(owner,text):
    return sha256(owner.encode()).hexdigest(),sha256(text.encode()).hexdigest()


def _operation(method,kind,owner,text,payload=None):
    if not settings.lesson_catalog_enabled:return None
    scope,key=identity(owner,text)
    try:
        args=(kind,scope,key,policy(kind))
        return getattr(store(),method)(*args,*(() if payload is None else (payload,)))
    except (OSError,sqlite3.Error,ValueError) as error:
        logger.warning('Lesson catalog skipped operation=%s kind=%s category=%s',method,kind,type(error).__name__)
        return None  # Storage trouble must not break the original checked generation path.


def load_plan(request):
    if request.workText.strip():return None
    raw=_operation('get','plan',request.owner,normalized_source(request.problemText))
    if raw is None:return None
    from app.tutoring import lesson
    try:
        plan=lesson.Plan.model_validate_json(raw)
        if any(step.kind!='MATH' for step in plan.steps):raise ValueError('Catalog stores only checked base plans')
        lesson.validate_plan(plan,request,lesson.formula_constants(request.problemText))
        logger.info('Lesson catalog plan hit')
        return plan
    except (ValueError,TypeError,SyntaxError,ArithmeticError):
        _operation('remove','plan',request.owner,normalized_source(request.problemText));return None


def save_plan(request,plan):
    if getattr(request,'problemConfirmed',False) is not True or request.workText.strip() or any(step.kind!='MATH' for step in plan.steps):return
    # Called only after independent review/exact solver and local validation succeed.
    data=plan.model_dump()
    for output,step in zip(data['steps'],plan.steps):output['initialGuidance']=step.initialGuidance
    _operation('put','plan',request.owner,normalized_source(request.problemText),json.dumps(data,ensure_ascii=False).encode())


def audio_text(request):
    # Exact ordered text, exact voice and fallback mode; no cross-voice substitution.
    return json.dumps([request.voice,request.useFallback,request.paragraphs],ensure_ascii=False)


def load_audio(request):
    data=_operation('get','audio',request.owner,audio_text(request))
    if data is None:return None
    from app.tutoring.narration import validate_audio
    try:validate_audio(data)
    except (ValueError,EOFError,wave.Error):
        _operation('remove','audio',request.owner,audio_text(request));return None
    return data


def save_audio(request,data):
    _operation('put','audio',request.owner,audio_text(request),data)

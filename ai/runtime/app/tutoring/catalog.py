"""Exact-source reuse: private account state and explicitly published exercises."""
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
PUBLIC_CATALOG = Path(__file__).with_name('data') / 'verified_exercises.json'


@lru_cache(maxsize=2)
def policy(kind):
    folder=Path(__file__).resolve().parent
    names=['lesson.py','service.py'] if kind=='plan' else ['speech_render.py','narration.py','audio_cues.py','azure_speech.py']
    if kind=='plan':names+=['digit_append.py','fraction_remainder.py','mass_fraction.py','short_math.py','elementary_choices.py','number_tasks.py','area_tasks.py','choice_source.py','math_knowledge.py','source_clarification.py']
    # Git checkouts on Windows/Linux must derive the same validation version.
    content=b'catalog-v1'+b''.join((folder/name).read_bytes().replace(b'\r\n', b'\n') for name in names if (folder/name).is_file())
    return sha256(content).hexdigest()


@lru_cache(maxsize=1)
def published_entries():
    """Only the reviewed, Git-shipped inventory; never export the private DB."""
    try:
        if PUBLIC_CATALOG.stat().st_size > 1_000_000:
            raise ValueError('Public catalog is too large')
        data=json.loads(PUBLIC_CATALOG.read_text(encoding='utf-8'))
        if set(data)!={'version','validationPolicy','entries'} or data['version']!=1 or not isinstance(data['entries'],list) or len(data['entries'])>500:
            raise ValueError('Invalid public catalog')
        entries={}
        for row in data['entries']:
            if set(row)!={'id','problemText','plan','expectedAnswers'} or not isinstance(row['problemText'],str) or not 3<=len(row['problemText'])<=4000:
                raise ValueError('Invalid public exercise')
            key=normalized_source(row['problemText'])
            if key in entries:
                raise ValueError('Duplicate public source')
            entries[key]=json.dumps(row['plan'],ensure_ascii=False).encode()
        return data['validationPolicy'],entries
    except (OSError,ValueError,TypeError,KeyError):
        logger.warning('Published lesson catalog unavailable; using checked generation')
        return '',{}


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
    if not settings.lesson_catalog_enabled or request.workText.strip():return None
    from app.tutoring import lesson
    source = normalized_source(request.problemText)
    version, entries = published_entries()
    # The reviewed exact source takes priority over an older account copy.
    for published in (True, False):
        if published:
            raw = entries.get(source) if version == policy('plan') else None
        else:
            raw = _operation('get', 'plan', request.owner, source)
        if raw is None:
            continue
        try:
            plan = lesson.Plan.model_validate_json(raw)
            if any(step.kind != 'MATH' for step in plan.steps):
                raise ValueError('Catalog stores only checked base plans')
            lesson.validate_plan(plan, request, lesson.formula_constants(request.problemText))
            logger.info('Lesson catalog plan hit scope=%s', 'published' if published else 'private')
            return plan
        except (ValueError, TypeError, SyntaxError, ArithmeticError):
            if not published:
                _operation('remove', 'plan', request.owner, source)
    return None


def plan_payload(plan):
    """Preserve the boundary between initial guidance and post-answer teaching."""
    data=plan.model_dump()
    for output,step in zip(data['steps'],plan.steps):output['initialGuidance']=step.initialGuidance
    return data


def save_plan(request,plan):
    if getattr(request,'problemConfirmed',False) is not True or request.workText.strip() or any(step.kind!='MATH' for step in plan.steps):return
    # Called only after independent review/exact solver and local validation succeed.
    _operation('put','plan',request.owner,normalized_source(request.problemText),json.dumps(plan_payload(plan),ensure_ascii=False).encode())


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

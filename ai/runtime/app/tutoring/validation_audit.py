"""Classify refusals without storing pupil text, rejected drafts or raw issues."""
from hashlib import sha256
import logging
from pydantic import ValidationError

logger=logging.getLogger(__name__)


def reason_code(error):
    if isinstance(error,ValidationError):return 'SCHEMA'
    message=str(error).lower()
    if 'derived literal operand' in message:return 'UNGROUNDED_OPERAND'
    if any(word in message for word in ('original source','relationships determine','clarification')):return 'SOURCE_UNRESOLVED'
    if 'independent review' in message or 'independent answer' in message:return 'SEMANTIC_REVIEW'
    if 'final answer step' in message or 'requested result differs' in message:return 'RESULT_SCOPE'
    if any(word in message for word in ('unearned','future answer','computed answer','initialguidance','initial guidance')):return 'PREMATURE_RESULT'
    if 'dimensionless' in message:return 'UNIT'
    return 'OTHER_VALIDATION'


def record(problem,attempt,error=None,provider=None,stage='draft',failed_checks=()):
    # Fingerprint permits correlating recovered attempts; no account identifier
    # or source text is persisted. A recovered draft is not automatically gold.
    source=sha256(problem.encode('utf-8')).hexdigest()[:16]
    code=reason_code(error) if error is not None else 'RECOVERED'
    name=provider if provider in {'groq','gemini'} else 'unknown'
    stage=stage if stage in {'draft','review','recovered'} else 'draft'
    checks=','.join(name for name in ('sourceFaithful','mathematicsCorrect','answersQuestion','teachingClear') if name in failed_checks) or 'none'
    logger.info('lesson_validation source=%s attempt=%d code=%s provider=%s stage=%s checks=%s',source,attempt,code,name,stage,checks)

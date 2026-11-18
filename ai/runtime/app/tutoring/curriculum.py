"""Bundled authored practice, matched against the complete confirmed source."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import json
import logging
from pathlib import Path

from app.tutoring.catalog_store import normalized_source

SOURCE = Path(__file__).with_name('data') / 'primary_math_curriculum.json'
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def entries():
    from app.tutoring import lesson
    try:
        if SOURCE.stat().st_size > 1_000_000:
            raise ValueError('Curriculum is too large')
        payload = json.loads(SOURCE.read_text(encoding='utf-8'))
        if payload.get('version') != 1 or not isinstance(payload.get('entries'), list) or not 100 <= len(payload['entries']) <= 250:
            raise ValueError('Invalid curriculum inventory')
        found, ids, counts = {}, set(), {grade: 0 for grade in range(1, 6)}
        for row in payload['entries']:
            if row['grade'] not in counts or row['id'] in ids or not 3 <= len(row['problemText']) <= 4000:
                raise ValueError('Invalid curriculum source')
            key = normalized_source(row['problemText'])
            if key in found:
                raise ValueError('Duplicate curriculum source')
            plan = lesson.Plan.model_validate(row['plan'])
            if any(step.kind != 'MATH' or not step.expression for step in plan.steps):
                raise ValueError('Curriculum needs calculation steps')
            request = lesson.LessonRequest(owner='curriculum-validation', problemText=row['problemText'], problemConfirmed=True)
            lesson.validate_plan(plan, request, lesson.formula_constants(row['problemText']))
            answers = []
            for step, expected in zip(plan.steps, row['expectedAnswers'], strict=True):
                actual = lesson.calculate_exact(lesson.expression_at(step, answers))
                if actual != Fraction(expected):
                    raise ValueError('Curriculum answer differs from authored reference')
                answers.append(str(actual))
            found[key] = row['plan']
            ids.add(row['id'])
            counts[row['grade']] += 1
        if any(count < 20 for count in counts.values()):
            raise ValueError('Every grade needs at least twenty exercises')
        return found
    except (OSError, KeyError, ValueError, TypeError, ArithmeticError, SyntaxError):
        logger.warning('Bundled practice unavailable; using checked generation')
        return {}


def verified_plan(text):
    if not isinstance(text, str) or not 3 <= len(text) <= 4000:
        return None
    raw = entries().get(normalized_source(text))
    return deepcopy(raw) if raw is not None else None

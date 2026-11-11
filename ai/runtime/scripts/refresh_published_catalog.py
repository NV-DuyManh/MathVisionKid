"""Check the reviewed public inventory, or refresh plans without changing its oracles.

No private database, cloud provider, account, image or audio export is supported.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tutoring import catalog, lesson
from app.tutoring.quiz_variants import exact_plan


def equivalent(actual, expected):
    try:
        return Fraction(actual.replace(',', '.')) == Fraction(expected.replace(',', '.'))
    except (ValueError, ZeroDivisionError):
        # Preserve mixed-number boundaries, e.g. 1 83/100 versus 18 3/100.
        clean = lambda text: re.sub(r'\s*([;/])\s*', r'\1', ' '.join(text.split())).casefold()
        return clean(actual) == clean(expected)


def check_plan(row, plan):
    request = lesson.LessonRequest(owner='published-inventory-check', problemText=row['problemText'], problemConfirmed=True)
    lesson.validate_plan(plan, request, lesson.formula_constants(request.problemText))
    expected = row['expectedAnswers']
    if not isinstance(expected, list) or len(expected) != len(plan.steps) or not all(isinstance(item, str) and 0 < len(item) <= 160 for item in expected):
        raise ValueError('Incomplete reference answers')
    values = []
    for step, reference in zip(plan.steps, expected):
        if step.kind != 'MATH' or step.workExcerpt:
            raise ValueError('Pupil work cannot be published')
        actual = str(lesson.calculate_exact(lesson.expression_at(step, values))) if step.expression else step.correctChoice
        if not equivalent(actual, reference):
            raise ValueError('Plan contradicts its reviewed reference answer')
        values.append(actual)


def verify(*, write=False):
    data = json.loads(catalog.PUBLIC_CATALOG.read_text(encoding='utf-8'))
    if set(data) != {'version', 'validationPolicy', 'entries'} or data['version'] != 1:
        raise ValueError('Invalid public inventory')
    if not isinstance(data['entries'], list) or not 1 <= len(data['entries']) <= 500:
        raise ValueError('Invalid inventory size')
    ids, sources = set(), set()
    for row in data['entries']:
        if set(row) != {'id', 'problemText', 'plan', 'expectedAnswers'} or not re.fullmatch(r'[a-z0-9-]{1,80}', row['id']):
            raise ValueError('Unexpected public fields or invalid ID')
        source = row['problemText']
        if not isinstance(source, str) or not 3 <= len(source) <= 4000 or re.search(r'@|https?://|Bearer |accessToken|sessionId', source, re.I):
            raise ValueError('Source requires privacy review')
        normalized = catalog.normalized_source(source)
        if row['id'] in ids or normalized in sources:
            raise ValueError('Duplicate public exercise')
        ids.add(row['id']); sources.add(normalized)
        exact = exact_plan(source)
        if exact is None:
            raise ValueError('Current exact proof is unavailable; review this source before publishing')
        check_plan(row, exact)
        if write:
            row['plan'] = catalog.plan_payload(exact)
        check_plan(row, lesson.Plan.model_validate(row['plan']))
    if write:
        data['validationPolicy'] = catalog.policy('plan')
        catalog.PUBLIC_CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    elif data['validationPolicy'] != catalog.policy('plan'):
        raise ValueError('Validation policy changed; refresh checked plans before release')
    return len(ids)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Refresh plans only if every existing reference still matches')
    args = parser.parse_args()
    print(f'{verify(write=args.write)} published exercises verified; no private data or providers accessed.')

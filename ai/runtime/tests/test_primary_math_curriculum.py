"""Authored exercise inventory has explicit reference answers and exact source isolation."""
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.tutoring import curriculum, lesson, quiz_variants

ROWS = json.loads(curriculum.SOURCE.read_text(encoding='utf-8'))['entries']


def test_each_grade_has_twenty_authored_exercises_with_honest_source_metadata():
    assert len(ROWS) == 100
    assert len({row['id'] for row in ROWS}) == 100
    for grade in range(1, 6):
        rows = [row for row in ROWS if row['grade'] == grade]
        assert len(rows) == 20
        assert {row['order'] for row in rows} == set(range(1, 21))
        assert len({row['section'] for row in rows}) >= 3
        assert all(row['bookSeries'] == 'Bài luyện tập' for row in rows)
        if grade > 1:
            assert all(row['week'] is None for row in rows)
        else:
            assert all(1 <= row['week'] <= 35 for row in rows)


@pytest.mark.parametrize('row', ROWS, ids=lambda row: row['id'])
def test_every_plan_matches_authored_reference_answers_and_math_boundaries(row):
    raw = curriculum.verified_plan(row['problemText'])
    assert raw is not None
    plan = lesson.Plan.model_validate(raw)
    request = lesson.LessonRequest(owner='new-pupil', problemText=row['problemText'], problemConfirmed=True)
    lesson.validate_plan(plan, request, lesson.formula_constants(request.problemText))
    answers = []
    for step, expected in zip(plan.steps, row['expectedAnswers'], strict=True):
        value = lesson.calculate_exact(lesson.expression_at(step, answers))
        assert value == Fraction(expected)
        answers.append(str(value))
    assert quiz_variants.exact_plan(row['problemText']) is not None


def test_fixed_independent_cases_cover_counts_units_fractions_and_multistep_math():
    # Authored oracles remain explicit. These values cannot be regenerated from formulas.
    expected = {
        'grade1_prob1': ['19'], 'grade1_prob2': ['22'], 'grade1_prob16': ['9'],
        'grade2_prob7': ['73'], 'grade2_prob8': ['45'], 'grade2_prob20': ['470'],
        'grade3_prob1': ['72', '96'], 'grade3_prob2': ['15', '60'], 'grade3_prob16': ['24', '32'],
        'grade4_prob1': ['30', '18', '540'], 'grade4_prob11': ['1/2'], 'grade4_prob13': ['15/8'],
        'grade5_prob1': ['63'], 'grade5_prob2': ['3/2', '40'], 'grade5_prob10': ['30000', '120000'],
    }
    by_id = {row['id']: row for row in ROWS}
    for identity, answers in expected.items():
        assert by_id[identity]['expectedAnswers'] == answers


def test_lookup_returns_independent_plans_and_never_matches_changed_source():
    text = ROWS[0]['problemText']
    first = curriculum.verified_plan(text)
    first['steps'][0]['expression'] = '999+1'
    assert curriculum.verified_plan(text)['steps'][0]['expression'] == '15+4'
    assert curriculum.verified_plan(text.replace('15', '16')) is None
    assert curriculum.verified_plan('Không dùng phép cộng. ' + text) is None
    assert curriculum.verified_plan('x' * 4001) is None


@pytest.mark.asyncio
async def test_fresh_accounts_need_no_model_or_private_cache_for_every_exercise(monkeypatch):
    monkeypatch.setattr(settings, 'lesson_catalog_enabled', False)
    cloud = AsyncMock(side_effect=AssertionError('Bundled curriculum must not call a model'))
    monkeypatch.setattr(lesson, 'generate_plan', cloud)
    for owner in ('fresh-a', 'fresh-b'):
        for row in ROWS:
            request = lesson.LessonRequest(owner=owner, problemText=row['problemText'], problemConfirmed=True)
            result = await lesson.checked_plan(request)
            assert result.topic == row['plan']['topic']
    cloud.assert_not_awaited()


@pytest.mark.asyncio
async def test_bundled_teaching_takes_precedence_over_old_private_copies(monkeypatch):
    request = lesson.LessonRequest(owner='returning-pupil', problemText=ROWS[0]['problemText'], problemConfirmed=True)
    old = lesson.Plan.model_validate(ROWS[0]['plan'])
    old.steps[0].explanation = 'An older valid explanation.'
    monkeypatch.setattr('app.tutoring.catalog.load_plan', lambda _: old)
    result = await lesson.checked_plan(request)
    assert result.steps[0].explanation == ROWS[0]['plan']['steps'][0]['explanation']


def test_frontend_projection_is_current_and_contains_no_private_grading_plan():
    script = Path(__file__).resolve().parents[1]/'scripts/export_primary_math_curriculum.py'
    spec = importlib.util.spec_from_file_location('curriculum_export', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    public = json.loads(module.TARGET.read_text(encoding='utf-8'))
    assert public == [{name: row[name] for name in module.PUBLIC_FIELDS} for row in ROWS]
    assert all('plan' not in row and 'expectedAnswers' not in row for row in public)

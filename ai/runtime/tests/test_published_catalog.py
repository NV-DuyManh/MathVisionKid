"""Git-shipped exercises work on fresh machines, without sharing pupil state."""
import importlib.util
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from app.config import settings
from app.tutoring import catalog, lesson


@pytest.fixture
def published(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'lesson_catalog_enabled', True)
    monkeypatch.setattr(settings, 'lesson_catalog_path', str(tmp_path/'new-machine.sqlite3'))
    catalog.published_entries.cache_clear()
    yield json.loads(catalog.PUBLIC_CATALOG.read_text(encoding='utf-8'))
    catalog.published_entries.cache_clear()


def test_shipped_inventory_matches_current_math_and_independent_reference_answers():
    path = Path(__file__).resolve().parents[1]/'scripts/refresh_published_catalog.py'
    spec = importlib.util.spec_from_file_location('public_inventory_check', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.verify() == 81
    assert not module.equivalent('18 3/100', '1 83/100')


@pytest.mark.asyncio
async def test_fresh_accounts_and_fresh_local_storage_reuse_all_published_plans(published, monkeypatch, tmp_path):
    cloud = AsyncMock(side_effect=AssertionError('Published exercises must not call a model'))
    monkeypatch.setattr(lesson, 'generate_plan', cloud)
    # Force a cache miss to fail; only the bundled plan can satisfy this request.
    monkeypatch.setattr('app.tutoring.short_math.verified_plan', lambda _: pytest.fail('Published catalog missed'))
    for machine in ('machine-a', 'machine-b'):
        monkeypatch.setattr(settings, 'lesson_catalog_path', str(tmp_path/machine/'private.sqlite3'))
        for row in published['entries']:
            req = lesson.LessonRequest(owner=machine, problemText=row['problemText'], problemConfirmed=True)
            plan = await lesson.checked_plan(req)
            assert catalog.plan_payload(plan) == row['plan']
            assert catalog.store().audit()['groups'] == []
    cloud.assert_not_awaited()


def test_published_plans_do_not_share_progress_or_match_changed_source_work_and_disabled_cache(published, monkeypatch):
    source = published['entries'][0]['problemText']
    req = lesson.LessonRequest(owner='new-pupil', problemText=source, problemConfirmed=True)
    first = catalog.load_plan(req)
    first.steps[0].expression = '99999+1'
    assert catalog.load_plan(req).steps[0].expression != first.steps[0].expression
    assert catalog.load_plan(req.model_copy(update={'problemText': source.replace('724', '725')})) is None
    assert catalog.load_plan(req.model_copy(update={'workText': '1+1=2', 'workConfirmed': True})) is None
    monkeypatch.setattr(settings, 'lesson_catalog_enabled', False)
    assert catalog.load_plan(req) is None


@pytest.mark.parametrize('damage', ['stale', 'invalid-json', 'private-field', 'bad-plan'])
def test_stale_or_damaged_public_data_never_breaks_normal_checked_generation(published, monkeypatch, tmp_path, damage):
    source = published['entries'][0]['problemText']
    if damage == 'stale': published['validationPolicy'] = 'old-version'
    elif damage == 'private-field': published['entries'][0]['owner'] = 'private-account'
    elif damage == 'bad-plan': published['entries'][0]['plan']['steps'][0]['expression'] = '99999+1'
    path = tmp_path/'published.json'
    path.write_text('{' if damage == 'invalid-json' else json.dumps(published), encoding='utf-8')
    monkeypatch.setattr(catalog, 'PUBLIC_CATALOG', path)
    req = lesson.LessonRequest(owner='new-pupil', problemText=source, problemConfirmed=True)
    assert catalog.load_plan(req) is None


def test_validation_policy_is_identical_for_windows_and_linux_checkout(monkeypatch):
    baseline = catalog.policy.__wrapped__('plan')
    read = Path.read_bytes
    monkeypatch.setattr(Path, 'read_bytes', lambda path: read(path).replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
    assert catalog.policy.__wrapped__('plan') == baseline

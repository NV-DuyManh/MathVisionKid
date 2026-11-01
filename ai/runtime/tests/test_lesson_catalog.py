"""Catalog reuse is never a substitute for original source, math or access checks."""
import asyncio
import io
import importlib
import importlib.util
import json
import sqlite3
import time
import wave
from unittest.mock import AsyncMock
import pytest
from app.config import settings
from app.tutoring import catalog,lesson,narration
from app.tutoring.catalog_store import CatalogStore
from _lesson_test_data import garden_candidate,mock_generation

SOURCE='Vườn cây có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết có 16 cây cam. Hỏi có tất cả bao nhiêu cây?'


@pytest.fixture
def enabled(tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'lesson_catalog_enabled',True)
    monkeypatch.setattr(settings,'lesson_catalog_path',str(tmp_path/'private.sqlite3'))
    # These cases exercise generation/review caching, independently of optional
    # exact solvers, whose catalog integration is checked in its own suite.
    for name in ('fraction_remainder','digit_append'):
        module='app.tutoring.'+name
        if importlib.util.find_spec(module):monkeypatch.setattr(importlib.import_module(module),'verified_plan',lambda _:None)
    return catalog.store()


def request(owner='pupil-a',source=SOURCE,**options):
    return lesson.LessonRequest(owner=owner,problemText=source,problemConfirmed=True,**options)


@pytest.mark.asyncio
async def test_checked_exact_source_reused_after_reopening_without_model_call(enabled,monkeypatch):
    cloud=mock_generation(monkeypatch,garden_candidate())
    first=await lesson.start_lesson(request())
    second=await lesson.start_lesson(request(source=SOURCE.replace('Vườn cây','Vườn\n cây')))
    assert first.sessionId!=second.sessionId and cloud.await_count==2
    assert first.step.expression==second.step.expression and second.completed==[] and second.revision==0
    assert second.stepIndex==0 and '60' not in second.model_dump_json()
    assert enabled.audit()['groups'][0]['hits']==1


@pytest.mark.asyncio
async def test_other_owner_changed_number_unit_and_relation_do_not_reuse(enabled,monkeypatch):
    mock_generation(monkeypatch,garden_candidate());await lesson.checked_plan(request())
    for source in [SOURCE.replace('16','20'),SOURCE.replace('cây cam. Hỏi','quả cam. Hỏi'),SOURCE.replace('còn lại','nhiều hơn')]:
        assert catalog.load_plan(request(source=source)) is None
    assert catalog.load_plan(request(owner='another-child')) is None
    assert catalog.normalized_source('2/3')!=catalog.normalized_source('2/5')
    assert catalog.normalized_source('1,25')!=catalog.normalized_source('125')


@pytest.mark.asyncio
async def test_work_and_unconfirmed_drafts_are_not_collected(enabled,monkeypatch):
    mock_generation(monkeypatch,garden_candidate());plan=await lesson.checked_plan(request())
    assert catalog.load_plan(request(workText='1+1=2',workConfirmed=True)) is None
    from app.tutoring.plan_preparation import SourceDraft
    catalog.save_plan(SourceDraft(owner='draft',problemText=SOURCE),plan)
    assert catalog.load_plan(request(owner='draft')) is None


@pytest.mark.asyncio
async def test_no_failed_generation_is_cached(enabled,monkeypatch):
    monkeypatch.setattr(lesson,'generate_plan',AsyncMock(side_effect=lesson.TutorUnavailable('validation')))
    with pytest.raises(lesson.TutorUnavailable):await lesson.checked_plan(request())
    assert enabled.audit()['groups']==[]


@pytest.mark.asyncio
async def test_initial_private_boundary_survives_roundtrip_and_policy_change_misses(enabled,monkeypatch):
    plan=lesson.Plan.model_validate(garden_candidate())
    plan.steps[0].initialGuidance=['Em đọc các phần cây đã cho, cộng hai phân số để tìm phần cây táo và xoài.']
    catalog.save_plan(request(),plan)
    loaded=catalog.load_plan(request())
    assert loaded.steps[0].initialGuidance==plan.steps[0].initialGuidance
    monkeypatch.setattr(catalog,'policy',lambda kind:'new-validation-policy')
    assert catalog.load_plan(request()) is None


@pytest.mark.asyncio
async def test_corrupt_or_now_invalid_plan_is_rejected_and_generation_continues(enabled,monkeypatch):
    plan=lesson.Plan.model_validate(garden_candidate());catalog.save_plan(request(),plan)
    scope,key=catalog.identity('pupil-a',catalog.normalized_source(SOURCE))
    bad=plan.model_dump();bad['steps'][0]['expression']='99999+1'
    enabled.put('plan',scope,key,catalog.policy('plan'),json.dumps(bad).encode())
    assert catalog.load_plan(request()) is None
    assert enabled.audit()['groups']==[]
    mock_generation(monkeypatch,garden_candidate());assert await lesson.checked_plan(request())


def wav():
    output=io.BytesIO()
    with wave.open(output,'wb') as data:
        data.setnchannels(1);data.setsampwidth(2);data.setframerate(16000);data.writeframes(b'\x01\x00'*8000)
    return output.getvalue()


def test_audio_reuse_across_sessions_keeps_voice_text_owner_and_permissions(enabled,monkeypatch):
    source=lesson.Plan.model_validate(garden_candidate())
    first=lesson.Session('pupil-a',source,time.monotonic()+60,narration_texts=['Đọc đúng dữ kiện đã cho.'])
    second=lesson.Session('pupil-a',source,time.monotonic()+60,narration_texts=['Đọc đúng dữ kiện đã cho.'])
    sid1='catalog-voice-session-a-12345';sid2='catalog-voice-session-b-12345'
    monkeypatch.setitem(lesson._sessions,sid1,first);monkeypatch.setitem(lesson._sessions,sid2,second)
    turn=narration.NarrationRequest(owner='pupil-a',sessionId=sid1,revision=0,paragraphs=['Đọc đúng dữ kiện đã cho.'])
    data=wav();monkeypatch.setattr(narration,'render_audio',lambda *args,**kwargs:data)
    assert narration.narrate(turn)==data
    narration._cache.clear()
    monkeypatch.setattr(narration,'render_audio',lambda *args,**kwargs:pytest.fail('Must reuse exact saved audio'))
    assert narration.narrate(turn.model_copy(update={'sessionId':sid2}))==data
    assert catalog.load_audio(turn.model_copy(update={'voice':'vi-VN-HoaiMyNeural'})) is None
    assert catalog.load_audio(turn.model_copy(update={'paragraphs':['Nội dung khác.']})) is None
    with pytest.raises(lesson.LessonExpired):narration.narrate(turn.model_copy(update={'owner':'another-child'}))
    second.narration_texts=[]
    with pytest.raises(ValueError):narration.narrate(turn.model_copy(update={'sessionId':sid2}))
    narration._cache.clear()


@pytest.mark.asyncio
async def test_background_draft_collected_only_when_confirmed_session_consumes_it(enabled,monkeypatch):
    from app.tutoring.plan_preparation import SourceDraft
    from app.tutoring import plan_preparation
    cloud=mock_generation(monkeypatch,garden_candidate())
    draft=await lesson.checked_plan(SourceDraft(owner='pupil-a',problemText=SOURCE))
    assert enabled.audit()['groups']==[]
    monkeypatch.setattr(plan_preparation,'prepared_plan',AsyncMock(return_value=draft))
    response=await lesson.start_lesson(request())
    assert response.completed==[] and cloud.await_count==2
    assert catalog.load_plan(request()) is not None


def test_damaged_audio_falls_back_and_is_removed(enabled):
    req=narration.NarrationRequest(owner='pupil-a',sessionId='catalog-voice-session-123456',revision=0,paragraphs=['Nội dung đã cấp quyền.'])
    catalog.save_audio(req,b'broken-but-hash-consistent-wav')
    assert catalog.load_audio(req) is None
    assert enabled.audit()['groups']==[]


@pytest.mark.asyncio
async def test_catalog_unavailable_falls_back_without_breaking_lesson(enabled,monkeypatch):
    monkeypatch.setattr(settings,'lesson_catalog_path',str(enabled.path.parent))
    cloud=mock_generation(monkeypatch,garden_candidate())
    assert await lesson.checked_plan(request())
    assert cloud.await_count==2


def test_expired_bitrot_lru_and_byte_budget_are_bounded(tmp_path):
    store=CatalogStore(tmp_path/'state.sqlite3',max_entries=2,max_audio_bytes=6)
    store.put('plan','owner','a','v',b'one');store.put('plan','owner','b','v',b'two')
    assert store.get('plan','owner','a','v')==b'one'
    store.put('plan','owner','c','v',b'three');assert store.get('plan','owner','b','v') is None
    store.put('audio','owner','a','v',b'1234');store.put('audio','owner','b','v',b'5678')
    assert store.get('audio','owner','a','v') is None
    assert store.audit()['groups'][0]['bytes']<=6
    from contextlib import closing
    with closing(sqlite3.connect(store.path)) as db,db:
        db.execute("UPDATE entries SET expires=0 WHERE key='a'")
        db.execute("UPDATE entries SET digest='broken' WHERE key='c'")
    assert store.get('plan','owner','a','v') is None
    assert store.get('plan','owner','c','v') is None


@pytest.mark.asyncio
async def test_unexpected_sql_payload_type_is_removed_without_breaking_generation(enabled,monkeypatch):
    from contextlib import closing
    scope,key=catalog.identity('pupil-a',catalog.normalized_source(SOURCE))
    enabled.put('plan',scope,key,catalog.policy('plan'),b'checked')
    with closing(sqlite3.connect(enabled.path)) as db,db:
        db.execute("UPDATE entries SET payload='damaged-text-column'")
    assert enabled.audit()['corrupt']==1
    mock_generation(monkeypatch,garden_candidate())
    assert await lesson.checked_plan(request())
    assert enabled.audit()['corrupt']==0

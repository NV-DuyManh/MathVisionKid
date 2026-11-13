from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from app.api import tutor
from app.config import settings
from app.tutoring import lesson, plan_preparation
from app.tutoring.source_clarification import SourceNeedsReview, source_issue
from app.tutoring.short_math import verified_plan as choice_plan


RICE = ('Câu 4. Gia đình Nam có một thửa ruộng dạng hình chữ nhật có chiều dài 60 m, chiều dài gấp 4 lần chiều rộng. '
        'Gia đình Nam trồng lúa trên thửa ruộng đó. Cứ 1 m² thu hoạch được (6)/(5) thóc. Hỏi:\n'
        'a) Gia đình Nam thu được bao nhiêu tạ thóc trên thửa ruộng đó?\n'
        'b) Biết mỗi ki-lô-gam thóc được mua với giá là 16 500 đồng. Vậy nếu bán hết số thóc đó thì gia đình Nam thu được bao nhiêu tiền?')
ROUND = ('Số thập phân lớn nhất nào được làm tròn đến 90?\nA. 89,9\nB. 89,99\nC. 90,1\nD. 91,4')
GAPS = [(RICE, 'missing_yield_unit'), ('Tính: 4(3)/(5) - 2(1)/(4) = …', 'mixed_number'),
        ('Tính: 2(2)/(3) : 1(2)/(5) = …', 'mixed_number'), (ROUND, 'rounding_place'),
        ('Bài 6. Có (5)/(?) số cây là cây xoài. Hỏi có tất cả bao nhiêu cây?', 'unread_fraction'),
        ('Có (?)⁄(5) số cây là cây xoài.', 'unread_fraction')]


@pytest.mark.asyncio
@pytest.mark.parametrize('source,issue', GAPS)
async def test_source_gaps_never_call_provider_or_open_a_partial_reading_lesson(source, issue, monkeypatch):
    provider = AsyncMock(side_effect=AssertionError('Source is not complete'))
    monkeypatch.setattr(lesson, 'generate_plan', provider)
    request = lesson.LessonRequest(owner='source-check', problemText=source, problemConfirmed=True,
                                   guidedUnderstanding=True, startWithReading=True)
    assert source_issue(source) == issue
    with pytest.raises(SourceNeedsReview) as failure:
        await lesson.start_lesson(request)
    assert failure.value.issue == issue
    with pytest.raises(SourceNeedsReview):
        await lesson.checked_plan(request)
    assert await plan_preparation.prepare(plan_preparation.SourceDraft(owner=request.owner, problemText=source)) == {'phase': 'unavailable'}
    provider.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('source,issue', GAPS)
async def test_internal_api_gives_a_bounded_clarification_code(source, issue, monkeypatch):
    monkeypatch.setattr(settings, 'internal_api_key', 'test-internal')
    app = FastAPI(); app.include_router(tutor.router, prefix='/internal/v1/tutor')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        result = await client.post('/internal/v1/tutor/lesson', headers={'X-Internal-API-Key': 'test-internal'},
            json={'owner': 'source-check', 'problemText': source, 'problemConfirmed': True})
    assert result.status_code == 422
    assert result.headers['X-Tutor-Failure'] == 'source_' + issue
    assert 'Traceback' not in result.text


@pytest.mark.asyncio
@pytest.mark.parametrize('source,answers', [
    ('Tính: 4 (3)/(5) - 2 (1)/(4) = …', ['47/20']),
    ('Tính: 2 (2)/(3) : 1 (2)/(5) = …', ['40/21']),
    (RICE.replace('(6)/(5) thóc', '(6)/(5) kg thóc'), ['15', '900', '1080', '54/5', '17820000']),
    (ROUND.replace('đến 90?', 'đến 90 khi làm tròn đến số tự nhiên gần nhất?'), ['90,1']),
])
async def test_only_explicitly_corrected_sources_complete_without_model(source, answers, monkeypatch):
    monkeypatch.setattr('app.tutoring.catalog.load_plan', lambda _: None)
    monkeypatch.setattr('app.tutoring.catalog.save_plan', lambda *args: None)
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(side_effect=AssertionError('Exact confirmed source')))
    assert source_issue(source) is None
    response = await lesson.start_lesson(lesson.LessonRequest(owner='source-check', problemText=source, problemConfirmed=True))
    for answer in answers:
        response = lesson.answer_lesson(lesson.TurnRequest(owner='source-check', sessionId=response.sessionId, revision=response.revision, answer=answer))
    assert response.status == 'COMPLETE'
    assert len(response.completed) == len(answers)


@pytest.mark.parametrize('source', [
    'Tính: 4 × (3)/(5)', 'Tính: 4 (3)/(5)', '1 + 1 = ?',
    'Làm tròn đến hàng phần mười số 3,14.', 'Số 35,6 làm tròn đến số tự nhiên gần nhất là:',
    RICE.replace('(6)/(5) thóc', '(6)/(5) kg thóc'),
])
def test_clear_sources_are_not_marked_as_missing(source):
    assert source_issue(source) is None


@pytest.mark.parametrize('source', [
    RICE,
    RICE.replace('(6)/(5) thóc', '(6)/(5) g thóc'),
    RICE.replace('(6)/(5) thóc', '(6)/(5) kg thóc').replace('gia đình Nam thu được', 'gia đình Lan thu được'),
    RICE.replace('(6)/(5) thóc', '(6)/(5) kg thóc') + ' Sau đó để lại 10 kg.',
    RICE.replace('(6)/(5) thóc', '(6)/(5) kg thóc').replace('gấp 4 lần', 'gấp 0 lần'),
])
def test_rice_proof_does_not_guess_units_ignore_names_or_discard_extra_conditions(source):
    assert choice_plan(source) is None


@pytest.mark.parametrize('source', [
    ROUND,
    ROUND.replace('đến 90?', 'đến 90 khi làm tròn đến hàng phần mười?'),
    ROUND.replace('đến 90?', 'đến 90 khi làm tròn đến số tự nhiên gần nhất?').replace('D. 91,4', 'D. 90,1'),
])
def test_maximum_rounding_proof_requires_precision_and_unique_matching_choice(source):
    assert choice_plan(source) is None

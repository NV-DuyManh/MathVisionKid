"""Work judgments stay attached to confirmed source rows; providers are mocked."""
import json
from copy import deepcopy
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from pydantic import ValidationError

from app.api import tutor
from app.config import settings
from app.tutoring import work_review as review


def request(**changes):
    return review.WorkReviewRequest(**{
        'sourceId': 'work-photo-source-12345',
        'problemText': 'Mai có 12 bút, được thêm 5 bút. Hỏi Mai có tất cả bao nhiêu bút?',
        'workText': 'Số bút Mai có tất cả là:\n12 + 5 = 17 (bút)\nĐáp số: 17 bút.',
        'problemConfirmed': True, 'workConfirmed': True, **changes,
    })


def assessment(source, **changes):
    rows = [row.strip() for row in source.workText.splitlines() if row.strip()]
    return {
        'sourceFaithful': True, 'methodCorrect': True, 'unitsCorrect': True,
        'mathematicsCorrect': True, 'complete': True,
        'summary': 'Các bước em viết đã trả lời đủ yêu cầu của đề.',
        'praise': 'Em đã chọn phép tính phù hợp và giữ đúng đơn vị.',
        'rows': [dict(lineIndex=index, sourceText=text, status='OK',
                      feedback='Bước này phù hợp với dữ kiện và cách làm em đã viết.', hints=[])
                 for index, text in enumerate(rows)],
        'nextAction': 'Em đọc lại câu trả lời và đối chiếu với câu hỏi của đề nhé.',
        'alternative': '', **changes,
    }


def cloud(monkeypatch, first, second=None):
    mock = AsyncMock(side_effect=[first, deepcopy(first) if second is None else second])
    monkeypatch.setattr(review, '_generate', mock)
    return mock


@pytest.mark.asyncio
async def test_correct_work_needs_independent_source_reviews_and_preserves_all_rows(monkeypatch):
    source = request(workText='  Số bút Mai có tất cả là: \n\n 12 + 5 = 17 (bút) \n Đáp số: 17 bút. ')
    model = cloud(monkeypatch, assessment(source))
    result = await review.review_work(source)
    assert result.status == 'CORRECT' and result.praise and result.sourceId == source.sourceId
    assert [row.sourceText for row in result.rows] == [
        'Số bút Mai có tất cả là:', '12 + 5 = 17 (bút)', 'Đáp số: 17 bút.']
    assert [row.lineIndex for row in result.rows] == [0, 1, 2]
    assert model.await_count == 2
    assert model.await_args_list[0].args[0] != model.await_args_list[1].args[0]
    payloads = [json.loads(call.args[1]) for call in model.await_args_list]
    assert all(payload['problemText'] == source.problemText for payload in payloads)
    assert payloads[0] == payloads[1]  # Neither evaluator sees or copies the other judgment.
    assert all('praise' not in payload and 'assessment' not in payload for payload in payloads)
    assert 'box' not in result.model_dump_json()


@pytest.mark.parametrize('field,value', [
    ('problemConfirmed', False), ('workConfirmed', False), ('problemConfirmed', 'true'),
    ('workConfirmed', 1), ('workConfirmed', None), ('sourceId', 'short'),
    ('problemText', 'Có [?] bút.'), ('workText', '12 + [?] = 17'),
    ('workText', '\n'.join(['Có bút'] * 36)), ('workText', 'a' * 501),
])
def test_unconfirmed_unclear_or_unbounded_sources_are_rejected(field, value):
    with pytest.raises(ValidationError):
        request(**{field: value})


@pytest.mark.asyncio
async def test_source_id_and_unicode_row_boundaries_are_preserved(monkeypatch):
    source = request(sourceId='  source-id-exact-12345  ',
        workText='\u00a0Số bút là:\u00a0\x85\x1c 12 + 5 = 17 (bút)\x1d\u00a0Đáp số: 17 bút.\u00a0')
    cloud(monkeypatch, assessment(source))
    result = await review.review_work(source)
    assert source.sourceId == result.sourceId == '  source-id-exact-12345  '
    assert [row.sourceText for row in result.rows] == ['Số bút là:', '12 + 5 = 17 (bút)', 'Đáp số: 17 bút.']


def test_normalization_keeps_bom_and_trims_python_control_whitespace():
    assert review.source_rows('\u001f\ufeffBài giải\u001f\n\u0085\u00a0\n12 + 5 = 17\u001f') == [
        '\ufeffBài giải', '12 + 5 = 17']


@pytest.mark.asyncio
async def test_ok_rows_cannot_publish_correction_hints(monkeypatch):
    source = request()
    judged = assessment(source)
    judged['rows'][0]['hints'] = ['Em kiểm tra lại bước này nhé.']
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and all(row.status == 'UNSURE' for row in result.rows)


@pytest.mark.asyncio
@pytest.mark.parametrize('issue', ['operands', 'units'])
async def test_correct_arithmetic_is_not_approval_of_wrong_source_operands_or_units(monkeypatch, issue):
    source = request(workText='12 + 7 = 19 (bút)' if issue == 'operands' else '12 + 5 = 17 (m)')
    judged = assessment(source, sourceFaithful=issue != 'operands', methodCorrect=issue != 'operands',
                        unitsCorrect=issue != 'units', praise='', alternative='')
    judged['rows'][0].update(status='FIX', feedback='Em đối chiếu lại dữ kiện và đơn vị của đại lượng này.',
                             hints=['Tìm lại thông tin tương ứng trong đề trước khi sửa.'])
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVISION' and result.rows[0].status == 'FIX'
    assert not result.praise and not result.alternative


@pytest.mark.asyncio
async def test_valid_alternative_pupil_method_does_not_need_a_canonical_plan(monkeypatch):
    source = request(problemText='Có 3 hộp, mỗi hộp 7 bút. Hỏi có tất cả bao nhiêu bút?',
                     workText='7 + 7 + 7 = 21 (bút)\nĐáp số: 21 bút.')
    judged = assessment(source, praise='Em dùng cộng lặp để gộp đúng các nhóm bằng nhau.',
        alternative='Em có thể dùng phép nhân để viết gọn việc gộp các nhóm bằng nhau.')
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'CORRECT' and result.alternative == judged['alternative']


@pytest.mark.asyncio
@pytest.mark.parametrize('work', ['12 + 5 =', '12 + 5', '12 + 5＝18', 'S = a × h', '(1)/(3) + [?] = 1'])
async def test_partial_or_unsupported_work_cannot_receive_cloud_correctness(monkeypatch, work):
    if '[?]' in work:
        with pytest.raises(ValidationError):
            request(workText=work)
        return
    source = request(workText=work)
    cloud(monkeypatch, assessment(source))
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and result.rows[0].status == 'UNSURE'
    assert not result.praise and not result.alternative


@pytest.mark.asyncio
async def test_incomplete_or_disputed_work_never_gets_whole_solution_praise(monkeypatch):
    source = request()
    first = assessment(source)
    second = assessment(source, complete=False, praise='')
    second['rows'][1].update(status='UNSURE', feedback='Cần làm rõ cách em chọn phép tính ở đây.')
    cloud(monkeypatch, first, second)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and result.rows[1].status == 'UNSURE'
    assert not result.praise


@pytest.mark.asyncio
async def test_verified_rows_do_not_prove_whole_work_is_complete(monkeypatch):
    source = request()
    cloud(monkeypatch, assessment(source, complete=False, praise=''))
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and all(row.status == 'OK' for row in result.rows)
    assert not result.praise and not result.alternative


@pytest.mark.asyncio
async def test_owner_garden_sample_keeps_correct_fractions_and_guides_missing_total(monkeypatch):
    source = request(problemText='Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. '
        'Số cây cam là 16 cây. Hỏi cả vườn có bao nhiêu cây?',
        workText='Số phần chỉ số cây táo và cây xoài trong vườn là:\n(1)/(3) + (2)/(5) = (11)/(15) (số cây)\n'
            'Số phần chỉ số cây cam trong vườn là:\n1 - (11)/(15) = (4)/(15) (số cây)')
    continuation = 'Số cây cam đã cho ứng với phần cả vườn em vừa tìm. Em tìm số cây ứng với mỗi phần bằng nhau, rồi tìm cả vườn nhé.'
    cloud(monkeypatch, assessment(source, complete=False, praise='', nextAction=continuation))
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW'
    assert all(row.status == 'OK' and not row.hints for row in result.rows)
    assert 'chưa hoàn tất' in result.summary and result.nextAction == continuation
    assert not result.praise and not result.alternative
    assert all(row.sourceText == text for row, text in zip(result.rows, review.source_rows(source.workText)))
    assert not any(char.isnumeric() for char in result.summary + result.nextAction)


@pytest.mark.asyncio
@pytest.mark.parametrize('unsafe_first', [True, False])
async def test_identical_source_judgments_use_only_the_fully_safe_explanation(monkeypatch, unsafe_first):
    source = request(workText='1 - 11/15 = 4/15 (số cây)')
    safe = assessment(source, complete=False, praise='', nextAction='Em dùng dữ kiện còn lại để tìm đại lượng đề hỏi nhé.')
    unsafe = deepcopy(safe)
    unsafe['rows'][0]['feedback'] = 'Em lấy một trừ đi phần vừa tìm được.'
    cloud(monkeypatch, unsafe if unsafe_first else safe, safe if unsafe_first else unsafe)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and result.rows[0].status == 'OK'
    assert result.rows[0].feedback == safe['rows'][0]['feedback']
    assert result.nextAction == safe['nextAction']
    assert unsafe['rows'][0]['feedback'] not in result.model_dump_json()
    assert not result.praise and not result.alternative


@pytest.mark.asyncio
@pytest.mark.parametrize('mismatch', ['source', 'status', 'complete', 'units'])
async def test_safe_explanation_cannot_rescue_tampered_source_or_disputed_judgments(monkeypatch, mismatch):
    source = request()
    safe = assessment(source)
    unsafe = deepcopy(safe)
    unsafe['rows'][0]['feedback'] = 'Kết quả là mười bảy bút.'
    if mismatch == 'source': unsafe['rows'][0]['sourceText'] = 'Một nguồn khác'
    if mismatch == 'status': unsafe['rows'][0]['status'] = 'UNSURE'
    if mismatch == 'complete': unsafe['complete'] = False
    if mismatch == 'units': unsafe['unitsCorrect'] = False
    cloud(monkeypatch, unsafe, safe)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and all(row.status == 'UNSURE' for row in result.rows)
    assert not result.praise and unsafe['rows'][0]['feedback'] not in result.model_dump_json()


@pytest.mark.asyncio
@pytest.mark.parametrize('dispute', ['complete', 'methodCorrect', 'unitsCorrect', 'sourceFaithful', 'mathematicsCorrect'])
async def test_missing_step_guidance_requires_both_checkers_to_agree_only_completion_remains(monkeypatch, dispute):
    source = request()
    first = assessment(source, complete=False, praise='', nextAction='Em tìm đại lượng còn thiếu theo dữ kiện của đề nhé.')
    second = deepcopy(first)
    second[dispute] = dispute == 'complete'
    cloud(monkeypatch, first, second)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and not result.praise
    assert 'chưa hoàn tất' not in result.summary
    assert result.nextAction != first['nextAction']


@pytest.mark.asyncio
@pytest.mark.parametrize('written', ['12 + 5 = 18 (bút)', '1/3 + 2/5 = 5/15 + 5/15 = 11/15',
    '(1)/(3) + (2)/(5) = (12)/(15) (số cây)', '1 - (11)/(15) = (5)/(15) (số cây)'])
async def test_exact_arithmetic_overrides_cloud_praise_without_giving_corrected_answer(monkeypatch, written):
    source = request(workText=written)
    cloud(monkeypatch, assessment(source))
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVISION' and result.rows[0].status == 'FIX'
    assert result.rows[0].hints and not result.praise and not result.alternative
    teaching = ' '.join([result.summary, result.nextAction, result.rows[0].feedback, *result.rows[0].hints])
    assert not any(char.isdigit() for char in teaching) and '=' not in teaching


@pytest.mark.asyncio
@pytest.mark.parametrize('mutation', [
    'wrong_index', 'bool_index', 'wrong_text', 'duplicate', 'missing', 'reversed',
    'coordinates', 'source_id', 'extra_row', 'unstrict_claim',
])
async def test_model_cannot_rebind_omit_or_invent_source_regions(monkeypatch, mutation):
    source = request()
    judged = assessment(source)
    if mutation == 'wrong_index': judged['rows'][0]['lineIndex'] = 99
    if mutation == 'bool_index': judged['rows'][0]['lineIndex'] = True
    if mutation == 'wrong_text': judged['rows'][1]['sourceText'] = '12 + 5 = 18 (bút)'
    if mutation == 'duplicate': judged['rows'][1] = deepcopy(judged['rows'][0])
    if mutation == 'missing': judged['rows'].pop()
    if mutation == 'reversed': judged['rows'].reverse()
    if mutation == 'coordinates': judged['rows'][0]['box'] = [0, 0, 1000, 1000]
    if mutation == 'source_id': judged['sourceId'] = 'another-students-source'
    if mutation == 'extra_row': judged['rows'].append(deepcopy(judged['rows'][0]))
    if mutation == 'unstrict_claim': judged['sourceFaithful'] = 'true'
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and result.sourceId == source.sourceId
    assert all(row.status == 'UNSURE' for row in result.rows)
    assert [row.sourceText for row in result.rows] == source.workText.splitlines()
    assert not result.praise


@pytest.mark.asyncio
@pytest.mark.parametrize('feedback', [
    'Em đối chiếu câu trả lời sau khi kiểm tra phép cộng nhé.',
    'Em kiểm tra phép cộng. Sau đó, em đối chiếu câu trả lời với đề nhé.',
])
async def test_clear_temporal_sau_is_not_a_spelled_out_answer(monkeypatch, feedback):
    source = request()
    judged = assessment(source)
    judged['rows'][1]['feedback'] = feedback
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'CORRECT' and result.rows[1].feedback == feedback


@pytest.mark.asyncio
@pytest.mark.parametrize('feedback', [
    'Em đã tìm được một phân số của cả vườn.',
    'Đại lượng này chiếm một phần nào đó của toàn bộ.',
    'Em quy đồng và cộng hai phân số đã cho.',
    'Em cộng hai tử số sau khi quy đồng.',
    'Em tự kiểm tra rồi viết đáp số.',
    'Em tính tiếp rồi viết đáp số nhé.',
    'Em cần tính tiếp để ra đáp số cuối cùng.',
    'Em cần tính tiếp để ra đáp số cuối cùng nhé.',
])
async def test_indefinite_fraction_and_terminal_answer_actions_are_not_answer_values(monkeypatch, feedback):
    source = request()
    judged = assessment(source)
    judged['rows'][1]['feedback'] = feedback
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'CORRECT' and result.rows[1].feedback == feedback


@pytest.mark.asyncio
@pytest.mark.parametrize('feedback', [
    'Em ghi một phần tư.', 'Em ghi hai phần năm.', 'Em ghi chín phân số.',
    'Em ghi một phân số bằng sáu.', 'Em cộng hai tử số được mười một.',
    'Em viết đáp số: mười bảy bút.', 'Em viết đáp số là sáu bút.',
    'Em viết đáp số: hình vuông.', 'Em tìm ra đáp số cuối cùng: hình vuông.',
    'Em viết đáp số nhé: sáu bút.', 'Em viết đáp số. Đáp số: sáu bút.',
    'Em viết đáp số.hình vuông.', 'Em tìm ra đáp số cuối cùng là hình vuông.',
])
async def test_pedagogic_references_do_not_allow_actual_answers_or_answer_labels(monkeypatch, feedback):
    source = request()
    judged = assessment(source)
    judged['rows'][1]['feedback'] = feedback
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and all(row.status == 'UNSURE' for row in result.rows)
    assert feedback not in result.model_dump_json()


@pytest.mark.asyncio
async def test_agreed_arithmetic_correction_keeps_specific_safe_scaffold(monkeypatch):
    source = request(workText='Số bút là:\n12 + 5 = 18 (bút)')
    judged = assessment(source, mathematicsCorrect=False, complete=False, praise='')
    judged['rows'][1].update(status='FIX', feedback='Em cần xem lại cách cộng ở hàng đơn vị.',
        hints=['Em cộng hàng đơn vị trước.', 'Em đối chiếu tổng với cách đếm thêm từng nhóm.'])
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVISION' and not result.praise
    assert result.rows[1].feedback == judged['rows'][1]['feedback']
    assert result.rows[1].hints == judged['rows'][1]['hints']


@pytest.mark.asyncio
@pytest.mark.parametrize('feedback', [
    'Em ghi sáu bút.', 'Em ghi sau bút.', 'Kết quả là sau.',
    'Em kiểm tra sau khi cộng rồi ghi sáu bút.',
    'Sau đó, em ghi sau bút.',
])
async def test_temporal_allowance_still_rejects_spelled_out_numerical_answers(monkeypatch, feedback):
    source = request()
    judged = assessment(source)
    judged['rows'][1]['feedback'] = feedback
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and not result.praise
    assert feedback not in result.model_dump_json()


@pytest.mark.asyncio
@pytest.mark.parametrize('field,text', [
    ('summary', 'Kết quả là 17.'), ('praise', 'Đáp số: mười bảy bút.'),
    ('alternative', 'Em tính 12 + 5 = 17 rồi ghi đáp số.'),
    ('nextAction', 'Chạy localhost:8000 để xem kết quả.'),
    ('feedback', 'Em ghi mười bảy bút.'), ('hints', 'Đáp số là 17 bút.'),
])
async def test_public_teaching_cannot_dump_an_answer_or_developer_instructions(monkeypatch, field, text):
    source = request()
    judged = assessment(source)
    if field == 'feedback': judged['rows'][1]['feedback'] = text
    elif field == 'hints': judged['rows'][1]['hints'] = [text]
    else: judged[field] = text
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and not result.praise and not result.alternative
    assert text not in result.model_dump_json()


@pytest.mark.asyncio
@pytest.mark.parametrize('problem,work', [
    ('Tính diện tích hình bên.', 'Diện tích là:\n12 + 5 = 17'),
    ('Tìm số bút có tất cả.', '[Hình vẽ]\n12 + 5 = 17'),
    ('Tìm số bút có tất cả.', 'Sơ đồ biểu diễn số bút:\n12 + 5 = 17'),
])
async def test_missing_diagram_evidence_requires_review_without_guessing(monkeypatch, problem, work):
    source = request(problemText=problem, workText=work)
    generated = AsyncMock()
    monkeypatch.setattr(review, '_generate', generated)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and all(row.status == 'UNSURE' for row in result.rows)
    generated.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize('failure', [review.TutorUnavailable(), TimeoutError()])
async def test_provider_failure_cannot_manufacture_a_review(monkeypatch, failure):
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=failure))
    with pytest.raises(review.TutorUnavailable):
        await review.review_work(request())


@pytest.mark.asyncio
async def test_endpoint_publishes_only_the_agreed_source_bound_response(monkeypatch):
    source = request()
    cloud(monkeypatch, assessment(source))
    app = FastAPI()
    app.include_router(tutor.router, prefix='/internal/v1/tutor')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        response = await client.post('/internal/v1/tutor/work-review', json=source.model_dump(),
            headers={'X-Internal-API-Key': settings.internal_api_key})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {'sourceId', 'status', 'summary', 'praise', 'rows', 'nextAction', 'alternative'}
    assert body['sourceId'] == source.sourceId and body['status'] == 'CORRECT'
    assert all(set(row) == {'lineIndex', 'sourceText', 'status', 'feedback', 'hints'} for row in body['rows'])


@pytest.mark.asyncio
async def test_endpoint_requires_internal_auth_and_returns_safe_provider_failure(monkeypatch):
    app = FastAPI()
    app.include_router(tutor.router, prefix='/internal/v1/tutor')
    mocked = AsyncMock(side_effect=review.TutorUnavailable())
    monkeypatch.setattr(tutor, 'review_work', mocked)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        denied = await client.post('/internal/v1/tutor/work-review', json=request().model_dump())
        assert denied.status_code == 401
        mocked.assert_not_called()
        headers = {'X-Internal-API-Key': settings.internal_api_key}
        failed = await client.post('/internal/v1/tutor/work-review', json=request().model_dump(), headers=headers)
        assert failed.status_code == 503 and 'Groq' not in failed.text and 'Gemini' not in failed.text
        rejected = await client.post('/internal/v1/tutor/work-review',
            json={**request().model_dump(), 'workConfirmed': 'true'}, headers=headers)
        assert rejected.status_code == 422 and mocked.await_count == 1

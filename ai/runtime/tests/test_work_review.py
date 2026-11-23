"""Work judgments stay attached to confirmed source rows; providers are mocked."""
import json
import asyncio
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from random import Random
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


def cold_calculations():
    rng = Random(62537)
    for index in range(100):
        a = rng.randrange(101 + index * 7, 108 + index * 7)
        b, c = rng.randrange(2, 9), rng.randrange(2, 10)
        options = [
            (f'{a} + {b}', Fraction(a + b)),
            (f'{b} − {a}', Fraction(b - a)),
            (f'{a} x {b}', Fraction(a * b)),
            (f'{a * b} : {b}', Fraction(a)),
            (f'{a} ÷ ({b})/({c})', Fraction(a * c, b)),
            (f'{a} × ({b})/({c})', Fraction(a * b, c)),
            (f'{a},5 + {b},25', Fraction(4 * (a + b) + 3, 4)),
            (f'({a} + {b}) * {c}', Fraction((a + b) * c)),
            (f'{a * b} / {b}', Fraction(a)),
            (f'{a} ∕ {b} + {c}', Fraction(a, b) + c),
        ]
        expression, expected = options[index % len(options)]
        yield index, expression, expected, index % 4 >= 2


@pytest.mark.asyncio
@pytest.mark.parametrize('index,expression,expected,wrong', list(cold_calculations()))
async def test_cold_input_arithmetic_and_dependency_with_independent_oracle(monkeypatch, index, expression, expected, wrong):
    shown = expected + wrong
    source = request(sourceId=f'cold-arithmetic-seed62537-{index:03}',
        problemText='Một kho đang kiểm kê. Hãy xem các phép tính và xác định số lượng còn lại.',
        workText=f'Bài giải:\nSố lượng ở bước đầu là:\n{expression} = {shown} (hộp)\n'
                 f'Số lượng sau khi nhập thêm là:\n({shown}) + 2 = {shown + 2} (hộp)')
    failure = [review.TutorUnavailable('rate_limit'), TimeoutError(),
               review.TutorUnavailable('configuration')][index % 3]
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=failure))
    assert review.checked_written_calculation(review.source_rows(source.workText)[2]) == (not wrong, shown)
    result = await review.review_work(source)
    assert result.sourceId == source.sourceId
    assert [row.rowKind for row in result.rows] == ['HEADING', 'EXPLANATION', 'CALCULATION', 'EXPLANATION', 'CALCULATION']
    assert [row.arithmeticCorrect for row in result.rows] == [None, None, not wrong, None, True]
    assert [row.errorKind for row in result.rows] == ['NONE', 'NONE', 'CALCULATION' if wrong else 'NONE',
                                                    'NONE', 'DEPENDENT' if wrong else 'NONE']
    assert result.status == ('NEEDS_REVISION' if wrong else 'NEEDS_REVIEW')
    assert result.complete is None and not result.praise


@pytest.mark.asyncio
async def test_cold_word_problems_through_authenticated_api(monkeypatch):
    app = FastAPI()
    app.include_router(tutor.router, prefix='/internal/v1/tutor')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        for index in range(20):
            n = 31 + index
            problem, expression, correct, unit = [
                (f'Có {n * 4} quyển sách chia đều cho bốn nhóm. Hỏi mỗi nhóm nhận bao nhiêu quyển sách?', f'{n * 4} : 4', n, 'quyển sách'),
                (f'Bình có {n} viên bi, Hà có nhiều hơn 9 viên bi. Hà có bao nhiêu viên bi?', f'{n} + 9', n + 9, 'viên bi'),
                (f'Một kiện hàng nặng {n} kg. Đổi sang gam.', f'{n} kg', n * 1000, 'g'),
                (f'Chiều dài {n} m, chiều rộng 6 m. Tính diện tích.', f'{n} × 6', n * 6, 'm²'),
                (f'Đã bán 2/7 số quả trong giỏ có {n * 7} quả. Hỏi còn bao nhiêu quả?', f'{n * 7} − {n * 2}', n * 5, 'quả'),
            ][index % 5]
            scenario = index // 5
            if scenario == 1:
                expression, correct = f'{correct} + 8', correct + 8
            if scenario == 2:
                # Include a correct numeric conversion into a unit different
                # from the one requested, and unit mismatches for other tasks.
                expression, correct, unit = (f'{n} kg', n, 'kg') if index % 5 == 2 else (expression, correct, 'đồng')
            work = f'Bài giải:\nSố lượng tìm được là:\n{expression} = {correct} {unit}'
            if scenario == 3:
                problem += ' Viết riêng câu đáp số.'
            source = request(sourceId=f'cold-word-api-2026-{index:02}', problemText=problem, workText=work)
            judged = assessment(source)
            if scenario == 1:
                judged.update(sourceFaithful=False, methodCorrect=False, praise='')
                judged['rows'][2].update(status='FIX', errorKind='OPERAND', feedback='Em kiểm tra dữ kiện đã dùng.')
            if scenario == 2:
                judged.update(unitsCorrect=False, praise='')
                judged['rows'][2].update(status='FIX', errorKind='UNIT', feedback='Em kiểm tra đơn vị đã dùng.')
            if scenario == 3:
                judged.update(complete=False, praise='', missingPart='Em còn thiếu câu trả lời theo yêu cầu của đề.')
            cloud(monkeypatch, judged)
            response = await client.post('/internal/v1/tutor/work-review', json=source.model_dump(),
                headers={'X-Internal-API-Key': settings.internal_api_key})
            assert response.status_code == 200
            body = response.json()
            assert body['sourceId'] == source.sourceId and body['rows'][0]['rowKind'] == 'HEADING'
            assert body['rows'][2]['arithmeticCorrect'] is True
            assert body['rows'][2]['errorKind'] == ['NONE', 'OPERAND', 'UNIT', 'NONE'][scenario]
            assert body['status'] == ['CORRECT', 'NEEDS_REVISION', 'NEEDS_REVISION', 'NEEDS_REVIEW'][scenario]


@pytest.mark.asyncio
async def test_compact_review_keeps_both_source_checks_with_smaller_output_budgets(monkeypatch):
    source = request()
    full = assessment(source)
    compact = {key: full[key] for key in ['sourceFaithful', 'methodCorrect', 'unitsCorrect', 'mathematicsCorrect', 'complete', 'praise']}
    compact['rows'] = [{key: row[key] for key in ['lineIndex', 'sourceText', 'status']} | {'errorKind': 'NONE'} for row in full['rows']]
    verifier = {key: value for key, value in compact.items() if key != 'praise'}
    generator = cloud(monkeypatch, compact, verifier)
    result = await review.review_work(source)
    assert result.status == 'CORRECT' and result.complete is True
    assert [row.sourceText for row in result.rows] == review.source_rows(source.workText)
    assert generator.await_count == 2
    first, second = generator.await_args_list
    assert second.kwargs['max_output_tokens'] < first.kwargs['max_output_tokens'] < 2400
    assert first.kwargs['preferred_provider'] == 'groq' and second.kwargs['preferred_provider'] == 'gemini'


@pytest.mark.asyncio
async def test_empty_next_action_does_not_discard_independently_verified_math(monkeypatch):
    source = request()
    cloud(monkeypatch, assessment(source, nextAction=''))
    result = await review.review_work(source)
    assert result.status == 'CORRECT' and result.nextAction


@pytest.mark.asyncio
async def test_compact_review_cannot_approve_disputed_or_rewritten_source(monkeypatch):
    source = request()
    full = assessment(source)
    compact = {key: full[key] for key in ['sourceFaithful', 'methodCorrect', 'unitsCorrect', 'mathematicsCorrect', 'complete', 'praise']}
    compact['rows'] = [{key: row[key] for key in ['lineIndex', 'sourceText', 'status']} | {'errorKind': 'NONE'} for row in full['rows']]
    verifier = deepcopy({key: value for key, value in compact.items() if key != 'praise'})
    verifier['rows'][1]['sourceText'] = '12 + 5 = 18'
    cloud(monkeypatch, compact, verifier)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and not result.praise


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['OPERAND', 'EXPLANATION', 'DEPENDENT'])
async def test_compact_corrections_preserve_error_kind_and_safe_teaching(monkeypatch, kind):
    source = request(workText='12 + 5 = 18\n18 × 2 = 36')
    compact = dict(sourceFaithful=False, methodCorrect=False, unitsCorrect=True,
        mathematicsCorrect=False, complete=True, praise='', missingPart='', rows=[
            dict(lineIndex=0, sourceText='12 + 5 = 18', status='FIX', errorKind='CALCULATION',
                 feedback='Em tính lại phép cộng nhé.'),
            dict(lineIndex=1, sourceText='18 × 2 = 36', status='FIX', errorKind=kind,
                 feedback='Em đối chiếu dữ kiện đã dùng ở đây nhé.')])
    verifier = {key: value for key, value in compact.items() if key not in {'praise', 'missingPart'}}
    verifier['rows'] = [{key: row[key] for key in ['lineIndex', 'sourceText', 'status', 'errorKind']} for row in compact['rows']]
    cloud(monkeypatch, compact, verifier)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVISION' and result.rows[1].errorKind == kind
    assert not result.praise
    review._safe_assessment(result, review.source_rows(source.workText))


@pytest.mark.asyncio
async def test_independent_reviewers_can_finish_in_parallel_without_seeing_each_other(monkeypatch):
    source = request()
    entered = []
    ready = asyncio.Event()
    monkeypatch.setattr(settings, 'cloud_advisor_max_concurrency', 2)

    async def generate(prompt, payload, **kwargs):
        entered.append((prompt, payload))
        if len(entered) == 2:
            ready.set()
        await ready.wait()
        return assessment(source)

    monkeypatch.setattr(review, '_generate', generate)
    result = await asyncio.wait_for(review.review_work(source), timeout=2)
    assert result.status == 'CORRECT' and len(entered) == 2
    assert entered[0][0] != entered[1][0] and entered[0][1] == entered[1][1]


@pytest.mark.asyncio
async def test_correct_multistep_work_waits_for_independent_checks_beyond_five_seconds(monkeypatch):
    source = request(
        problemText='Hiền mua 12 quyển vở hết 102000 đồng. Mai mua 8 quyển vở như thế '
                    'nhưng còn thiếu 15000 đồng. Hỏi Mai đang có bao nhiêu tiền?',
        workText='Giá một quyển vở là:\n102000 : 12 = 8500 (đồng)\n'
                 'Số tiền mua 8 quyển vở là:\n8500 × 8 = 68000 (đồng)\n'
                 'Số tiền Mai có là:\n68000 - 15000 = 53000 (đồng)\nĐáp số: 53000 đồng.',
    )
    monkeypatch.setattr(settings, 'cloud_advisor_max_concurrency', 2)

    async def generate(*args, **kwargs):
        await asyncio.sleep(5.2)
        return assessment(source)

    monkeypatch.setattr(review, '_generate', generate)
    result = await asyncio.wait_for(review.review_work(source), timeout=8)
    assert result.status == 'CORRECT' and result.complete is True
    assert result.arithmeticVerified is True and result.praise
    assert [row.sourceText for row in result.rows] == review.source_rows(source.workText)


@pytest.mark.asyncio
async def test_failed_review_cancels_its_other_independent_request(monkeypatch):
    source = request()
    cancelled = asyncio.Event()
    monkeypatch.setattr(settings, 'cloud_advisor_max_concurrency', 2)

    async def generate(prompt, *args, **kwargs):
        if prompt == review.REVIEW_PROMPT:
            await asyncio.sleep(0)
            raise review.TutorUnavailable('rate_limit')
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    monkeypatch.setattr(review, '_generate', generate)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and result.arithmeticVerified is True
    assert cancelled.is_set()


@pytest.mark.asyncio
async def test_compact_independent_verifier_preserves_source_and_copied_given_classification(monkeypatch):
    source = request(workText='1/3 + 2/4 = 2/6')
    first = assessment(source, sourceFaithful=False, methodCorrect=False, mathematicsCorrect=False, complete=False, praise='')
    first['rows'][0].update(status='FIX', errorKind='OPERAND', feedback='Em kiểm tra mẫu số của phần cây xoài.', hints=[])
    compact = {key: first[key] for key in ['sourceFaithful','methodCorrect','unitsCorrect','mathematicsCorrect','complete']}
    compact['rows'] = [{key: row[key] for key in ['lineIndex','sourceText','status','errorKind']} for row in first['rows']]
    cloud(monkeypatch, first, compact)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVISION' and result.rows[0].errorKind == 'OPERAND'
    assert result.rows[0].feedback == first['rows'][0]['feedback']


@pytest.mark.asyncio
@pytest.mark.parametrize('mutation', ['source', 'index', 'extra', 'coercion'])
async def test_compact_verifier_cannot_change_source_or_bypass_strict_types(monkeypatch, mutation):
    source = request()
    first = assessment(source)
    compact = {key: first[key] for key in ['sourceFaithful','methodCorrect','unitsCorrect','mathematicsCorrect','complete']}
    compact['rows'] = [{key: row[key] for key in ['lineIndex','sourceText','status']} | {'errorKind':'NONE'} for row in first['rows']]
    if mutation == 'source': compact['rows'][0]['sourceText'] = 'Bài khác'
    elif mutation == 'index': compact['rows'][0]['lineIndex'] = True
    elif mutation == 'extra': compact['answer'] = '17'
    else: compact['complete'] = 'true'
    cloud(monkeypatch, first, compact)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and any(row.arithmeticCorrect is True for row in result.rows)
    assert not result.praise


@pytest.mark.asyncio
async def test_answer_bearing_prose_is_replaced_without_another_model_or_changing_verified_judgments(monkeypatch):
    source = request()
    good = assessment(source)
    unsafe = deepcopy(good)
    unsafe['rows'][1]['feedback'] = 'Em đã tính đúng mười bảy bút.'
    generator = AsyncMock(side_effect=[unsafe, deepcopy(unsafe)])
    monkeypatch.setattr(review, '_generate', generator)
    result = await review.review_work(source)
    assert generator.await_count == 2
    assert result.status == 'CORRECT'
    assert unsafe['rows'][1]['feedback'] not in result.model_dump_json()
    assert result.rows[1].sourceText == review.source_rows(source.workText)[1]


@pytest.mark.asyncio
async def test_safe_presentation_cannot_promote_an_incomplete_judgment(monkeypatch):
    source = request()
    unsafe = assessment(source, complete=False, praise='')
    unsafe['rows'][1]['feedback'] = 'Kết quả là mười bảy bút.'
    generator = AsyncMock(side_effect=[unsafe, deepcopy(unsafe)])
    monkeypatch.setattr(review, '_generate', generator)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and not result.praise


@pytest.mark.asyncio
async def test_unsafe_optional_row_prose_does_not_erase_specific_safe_missing_work(monkeypatch):
    source = request()
    missing = 'Em chưa tìm tổng số cây trong vườn từ số cây cam và phần tương ứng.'
    judged = assessment(source, complete=False, praise='', missingPart=missing, nextAction=missing)
    judged['rows'][1]['feedback'] = 'Kết quả là mười bảy bút.'
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.complete is False and result.missingPart == missing and result.nextAction == missing
    assert 'mười bảy' not in result.model_dump_json()


@pytest.mark.asyncio
async def test_supported_copied_given_is_not_lost_when_other_global_checks_disagree(monkeypatch):
    source = request(workText='1/3 + 2/4 = 2/6')
    first = assessment(source, sourceFaithful=False, methodCorrect=False, mathematicsCorrect=False, complete=False, praise='')
    first['rows'][0].update(status='FIX', errorKind='OPERAND',
        feedback='Em đối chiếu mẫu số của phần cây xoài với đề gốc.', hints=['Em đọc lại dữ kiện phần cây xoài.'])
    second = deepcopy(first)
    second['unitsCorrect'] = False
    second['summary'] = 'Em viết hai phần bốn thay cho hai phần năm.'
    cloud(monkeypatch, first, second)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVISION' and result.rows[0].errorKind == 'OPERAND'
    assert result.complete is None and not result.praise
    assert second['summary'] not in result.model_dump_json()


@pytest.mark.asyncio
async def test_a_single_copied_operand_claim_cannot_override_a_disputed_review(monkeypatch):
    source = request(workText='1/3 + 2/4 = 2/6')
    first = assessment(source, complete=False, praise='')
    first['rows'][0].update(status='FIX', errorKind='OPERAND', feedback='Em đối chiếu mẫu số với đề.', hints=[])
    second = deepcopy(first)
    second['unitsCorrect'] = False
    second['rows'][0]['errorKind'] = 'CALCULATION'
    second['summary'] = 'Kết quả là hai phần sáu.'
    cloud(monkeypatch, first, second)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVISION' and result.rows[0].errorKind == 'CALCULATION'
    assert result.complete is None and not result.praise



@pytest.mark.asyncio
@pytest.mark.parametrize('dispute', ['sourceFaithful', 'methodCorrect', 'unitsCorrect', 'mathematicsCorrect', 'complete'])
async def test_replacing_both_unsafe_explanations_never_overrides_a_checker_disagreement(monkeypatch, dispute):
    source = request()
    first = assessment(source)
    first['rows'][1]['feedback'] = 'Kết quả là mười bảy bút.'
    second = deepcopy(first)
    second[dispute] = False
    cloud(monkeypatch, first, second)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and not result.praise
    assert first['rows'][1]['feedback'] not in result.model_dump_json()


@pytest.mark.asyncio
async def test_transient_first_provider_failure_retries_when_no_local_result_is_available(monkeypatch):
    source = request(workText='Em tìm tổng bằng cách gộp hai nhóm.\nĐáp số: 17 bút.')
    judged = assessment(source)
    generator = AsyncMock(side_effect=[review.TutorUnavailable('unavailable'), judged, deepcopy(judged)])
    monkeypatch.setattr(review, '_generate', generator)
    result = await review.review_work(source)
    assert result.status == 'CORRECT' and generator.await_count == 3


@pytest.mark.asyncio
async def test_verified_calculation_returns_without_retrying_an_unavailable_provider(monkeypatch):
    model = AsyncMock(side_effect=review.TutorUnavailable('unavailable'))
    monkeypatch.setattr(review, '_generate', model)
    monkeypatch.setattr(settings, 'cloud_advisor_max_concurrency', 1)
    result = await review.review_work(request())
    assert result.status == 'NEEDS_REVIEW' and result.arithmeticVerified is True
    assert model.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('written,status', [('2/5 + 1/5 = 3/5', 'CORRECT'), ('2/5 + 1/5 = 3/10', 'NEEDS_REVISION')])
async def test_review_reuses_the_lesson_solver_for_an_exact_expression(monkeypatch, written, status):
    model = AsyncMock(side_effect=review.TutorUnavailable('rate_limit'))
    monkeypatch.setattr(review, '_generate', model)
    result = await review.review_work(request(problemText='Tính: 2/5 + 1/5', workText='Bài giải:\n' + written))
    assert result.status == status
    model.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('unavailable', [False, True])
async def test_false_written_equality_is_highlighted_even_when_cloud_review_is_unusable(monkeypatch, unavailable):
    source = request(problemText='Mảnh đất dài 15 m, rộng 3/5 chiều dài. Dùng 1/6 diện tích trồng hoa. Tính diện tích trồng hoa.',
        workText='Chiều rộng là:\n15 × 3/5 = 9 (m)\nDiện tích là:\n15 × 9 = 135 (m²)\nDiện tích trồng hoa là:\n135 × 1/6 = 45 (m²)\nĐáp số: 45 m²')
    if unavailable:
        monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=review.TutorUnavailable('rate_limit')))
    else:
        first = assessment(source, mathematicsCorrect=False, praise='', complete=False)
        first['rows'][5].update(status='FIX', hints=['Em ghi hai mươi hai phẩy năm.'])
        second = deepcopy(first)
        second['complete'] = True
        cloud(monkeypatch, first, second)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVISION'
    assert result.rows[5].status == 'FIX' and result.rows[5].sourceText == '135 × 1/6 = 45 (m²)'
    assert result.rows[6].errorKind == 'DEPENDENT'
    assert all(row.status == 'OK' for row in result.rows[:5])
    assert result.rows[1].arithmeticCorrect is result.rows[3].arithmeticCorrect is True
    assert not result.praise and not result.alternative
    assert 'hai mươi' not in result.model_dump_json()


@pytest.mark.asyncio
@pytest.mark.parametrize('unavailable', [False, True])
async def test_orchard_review_flags_wrong_fraction_its_division_and_answer_together(monkeypatch, unavailable):
    source = request(problemText='Vườn có 1/3 cây táo, 2/5 cây xoài và 16 cây cam. Vườn có bao nhiêu cây?',
        workText='1/3 + 2/5 = 11/15 (số cây)\nSố phần cây cam là:\n1 - 11/15 = 3/15 (số cây)\n'
                 'Số cây trong vườn là:\n16 : 1/5 = 80 (cây)\nĐáp số: 80 cây\n2 + 3 = 5')
    if unavailable:
        monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=review.TutorUnavailable('rate_limit')))
    else:
        cloud(monkeypatch, assessment(source))  # Both miss the inherited error.
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVISION'
    assert [(row.lineIndex, row.errorKind) for row in result.rows if row.status == 'FIX'] == [
        (2, 'CALCULATION'), (4, 'DEPENDENT'), (5, 'DEPENDENT'), (6, 'DEPENDENT')]
    assert result.complete is (None if unavailable else True)
    assert [row.sourceText for row in result.rows] == review.source_rows(source.workText)
    assert 'tính lại các dòng' in result.nextAction


@pytest.mark.asyncio
@pytest.mark.parametrize('count_label', ['số cây cam trong vườn', 'số cây trong vườn'])
@pytest.mark.parametrize('last_row', ['16 : (4)/(15) = 60 (số cây)', '16 ÷ (8/30) = 60 (cây)'])
async def test_orchard_rewrite_preserves_exact_math_before_context_review(monkeypatch, last_row, count_label):
    problem = ('Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cam. '
               f'Biết rằng {count_label} là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?')
    work = ('Bài làm\nSố phần chỉ số cây táo và cây xoài trong vườn là:\n1/3 + 2/5 = 11/15 (số cây)\n'
            'Số phần chỉ số cây cam trong vườn là:\n1 - 11/15 = 4/15 (số cây)\nSố cây trong vườn là:\n' + last_row)
    source = request(problemText=problem, workText=work)
    unavailable = AsyncMock(side_effect=review.TutorUnavailable('rate_limit'))
    monkeypatch.setattr(review, '_generate', unavailable)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and result.complete is None and result.arithmeticVerified
    assert [row.sourceText for row in result.rows] == review.source_rows(work)
    assert [row.arithmeticCorrect for row in result.rows if row.rowKind == 'CALCULATION'] == [True, True, True]

    bad = source.model_copy(update={'workText': work.replace('60 (', '80 (')})
    result = await review.review_work(bad)
    assert result.status == 'NEEDS_REVISION' and result.rows[-1].errorKind == 'CALCULATION'

    cloud(monkeypatch, assessment(source))
    result = await review.review_work(source)
    assert result.status == 'CORRECT' and result.complete is True


@pytest.mark.asyncio
@pytest.mark.parametrize('punctuation', ['. Biết', ', biết', '; biết'])
async def test_recaptured_orchard_spacing_does_not_hide_a_correct_answer(monkeypatch, punctuation):
    source = request(
        problemText=('Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam'
                     f'{punctuation} rằng số cây cam trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây ?'),
        workText=('Bài giải ：\nSố phần chỉ số cây táo và cây xoài trong vườn là :\n1/3 + 2/5 = 11/15 (số cây)\n'
                  'Số phần chỉ số cây cam trong vườn là:\n1 - 11/15 = 4/15 (số cây)\n'
                  'Số  cây trong vườn là:\n16 : 4/15 = 60 (số cây)'))
    model = AsyncMock(side_effect=review.TutorUnavailable('rate_limit'))
    monkeypatch.setattr(review, '_generate', model)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and result.arithmeticVerified and result.complete is None
    assert [row.sourceText for row in result.rows] == source.workText.splitlines()
    assert all(row.status == 'OK' for row in result.rows)


@pytest.mark.asyncio
@pytest.mark.parametrize('problem,intervening', [
    ('Đề bài cho thêm 1/5 diện tích.', ''),
    ('Tìm diện tích.', '3/5 - 2/5 = 1/5\n'),
])
async def test_all_later_calculations_are_rechecked_together_after_an_error(monkeypatch, problem, intervening):
    source = request(problemText=problem, workText=f'1 - 11/15 = 3/15\n{intervening}16 : 1/5 = 80')
    cloud(monkeypatch, assessment(source))
    result = await review.review_work(source)
    assert [row.errorKind for row in result.rows] == ['CALCULATION', *(['DEPENDENT'] if intervening else []), 'DEPENDENT']


@pytest.mark.asyncio
@pytest.mark.parametrize('agreed', [True, False])
async def test_non_fraction_dependency_is_preserved_when_reviewers_disagree(monkeypatch, agreed):
    source = request(workText='12 + 5 = 18\n18 × 2 = 36')
    first = assessment(source, mathematicsCorrect=False, praise='')
    first['rows'][0].update(status='FIX', errorKind='CALCULATION')
    first['rows'][1].update(status='FIX', errorKind='DEPENDENT')
    second = deepcopy(first)
    if not agreed:
        second['rows'][1].update(status='OK', errorKind='NONE')
    cloud(monkeypatch, first, second)
    result = await review.review_work(source)
    assert result.rows[1].errorKind == 'DEPENDENT'


@pytest.mark.asyncio
@pytest.mark.parametrize('unavailable', [False, True])
@pytest.mark.parametrize('first,second,answer', [
    ('620 : 2 = 300 (kg)', '300 × 7 = 2100 (kg)', '2100 kg'),
    ('30 - 15 = 14 (kg)', '14 × 2 = 28 (kg)', '28 kg'),
    ('57 + 26 = 82 (quả)', '82 × 3 = 246 (quả)', '246 quả'),
    ('18,6 : 3 = 6,1 (kg)', '6,1 × 2 = 12,2 (kg)', '12,2 kg'),
    ('30 - 15 = 14 (kg)', '14 × 2', '28 kg'),
    ('10 + 5 = 14', 'x = 14 + 2', '16'),
])
async def test_any_new_solution_rechecks_the_remaining_calculations_and_answer(monkeypatch, unavailable, first, second, answer):
    source = request(problemText='Đối chiếu các phép tính trong bài làm.',
        workText=f'Bài làm\nSố lượng ban đầu là:\n{first}\nSố lượng tiếp theo là:\n{second}\nĐáp số: {answer}')
    if unavailable:
        monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=review.TutorUnavailable('rate_limit')))
    else:
        cloud(monkeypatch, assessment(source))
    result = await review.review_work(source)
    assert [(row.lineIndex, row.errorKind) for row in result.rows if row.status == 'FIX'] == [
        (2, 'CALCULATION'), (4, 'DEPENDENT'), (5, 'DEPENDENT')]
    assert all(row.status != 'FIX' for row in result.rows if row.lineIndex in {0, 1, 3})
    assert [row.sourceText for row in result.rows] == review.source_rows(source.workText)
    corrected = source.model_copy(update={'workText': '620 : 2 = 310 (kg)\n310 × 7 = 2170 (kg)'})
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=review.TutorUnavailable('rate_limit')))
    assert all(row.errorKind == 'NONE' for row in (await review.review_work(corrected)).rows)


@pytest.mark.asyncio
@pytest.mark.parametrize('symbol,unit', [('x', '(học sinh)'), ('X', 'học sinh.'), ('·', '(học sinh).'), ('×', '(học sinh)')])
async def test_new_class_problem_flags_calculation_and_downstream_subtraction_even_when_cloud_fails(monkeypatch, symbol, unit):
    source = request(problemText='Lớp 4A có 45 học sinh. Biết số học sinh nữ chiếm 3/5 số học sinh cả lớp. Hỏi lớp đó có bao nhiêu học sinh nam ?',
        workText=f'Bài giải:\nSố học sinh nữ trong lớp là\n45 {symbol} (3)/(5) = 28 {unit}\nSố học sinh nam trong lớp là\n45 - 28 = 17 {unit}')
    model = AsyncMock(side_effect=review.TutorUnavailable('rate_limit'))
    monkeypatch.setattr(review, '_generate', model)
    result = await review.review_work(source)
    assert [(row.lineIndex, row.errorKind) for row in result.rows if row.status == 'FIX'] == [(2, 'CALCULATION'), (4, 'DEPENDENT')]
    assert result.rows[4].arithmeticCorrect is True
    corrected = source.model_copy(update={'workText': source.workText.replace('28', '27').replace('17', '18')})
    result = await review.review_work(corrected)
    assert result.status == 'NEEDS_REVIEW' and result.complete is None and result.arithmeticVerified
    cloud(monkeypatch, assessment(corrected))
    result = await review.review_work(corrected)
    assert result.status == 'CORRECT' and result.complete is True


@pytest.mark.asyncio
async def test_new_class_values_and_reversed_groups_are_computed_from_the_question(monkeypatch):
    model = AsyncMock(side_effect=review.TutorUnavailable('rate_limit'))
    monkeypatch.setattr(review, '_generate', model)
    source = request(problemText='Lớp 5B có 36 học sinh. Biết rằng số học sinh nam chiếm 5/9 số học sinh của lớp. Hỏi lớp 5B có bao nhiêu học sinh nữ?',
        workText='Số học sinh nam là:\n5/9 × 36 = 20 (học sinh)\nSố học sinh nữ là:\n36 - 20 = 16 (học sinh)\nĐáp số: 16 học sinh nữ.')
    result = await review.review_work(source)
    assert result.arithmeticVerified and result.status == 'NEEDS_REVIEW'
    cloud(monkeypatch, assessment(source))
    assert (await review.review_work(source)).status == 'CORRECT'


@pytest.mark.asyncio
async def test_later_calculation_stays_in_the_same_revision_even_when_its_value_is_given(monkeypatch):
    source = request(problemText='Có 45 học sinh, trong đó có 28 học sinh nữ. Hỏi có bao nhiêu học sinh nam?',
        workText='45 x 3/5 = 28 (học sinh)\n45 - 28 = 17 (học sinh)')
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=review.TutorUnavailable('rate_limit')))
    result = await review.review_work(source)
    assert [row.errorKind for row in result.rows] == ['CALCULATION', 'DEPENDENT']


@pytest.mark.asyncio
async def test_generic_answer_line_reference_and_dimension_exponent_do_not_reject_correct_work(monkeypatch):
    source = request(problemText='Một mảnh đất hình chữ nhật dài 15 m, rộng bằng 3/5 chiều dài. Dùng 1/6 diện tích trồng hoa. Tính diện tích trồng hoa.',
        workText='Chiều rộng là:\n15 × 3/5 = 9 (m)\nDiện tích mảnh đất là:\n15 × 9 = 135 (m²)\nDiện tích trồng hoa là:\n135 × 1/6 = 45/2 (m²)\nĐáp số: 45/2 m²')
    judged = assessment(source, summary='Các phép tính, đơn vị và đáp số đều chính xác.')
    judged['rows'][3]['feedback'] = 'Em nhân chiều dài với chiều rộng, ghi đơn vị m² phù hợp.'
    judged['rows'][-1]['feedback'] = 'Đáp số khớp với kết quả em vừa tính, đơn vị đầy đủ.'
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'CORRECT'
    assert all(row.status == 'OK' for row in result.rows)
    assert result.rows[-1].feedback == judged['rows'][-1]['feedback']


@pytest.mark.asyncio
@pytest.mark.parametrize('feedback', ['Đáp số là một mảnh đất.', 'Đáp số: màu xanh.', 'Em ghi 17 m².', 'Diện tích là m² và sáu.', 'Em ghi ² làm kết quả.'])
async def test_generic_answer_reference_does_not_allow_new_values_or_answer_statements(monkeypatch, feedback):
    source = request()
    judged = assessment(source)
    judged['rows'][1]['feedback'] = feedback
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'CORRECT'
    review._safe_assessment(result, review.source_rows(source.workText))
    assert feedback not in result.model_dump_json()


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
    assert result.status == 'NEEDS_REVIEW' and any(row.arithmeticCorrect is True for row in result.rows)
    assert not result.praise


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
@pytest.mark.parametrize('work', ['12 + 5 =', '12 + 5', 'S = a × h', '(1)/(3) + [?] = 1'])
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
    generator = cloud(monkeypatch, assessment(source, complete=False, praise='', nextAction=continuation))
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW'
    assert all(row.status == 'OK' and not row.hints for row in result.rows)
    assert 'chưa hoàn tất' in result.summary and result.nextAction == continuation
    assert not result.praise and not result.alternative
    assert generator.await_count == 2
    assert all(call.kwargs['max_output_tokens'] < 3000 for call in generator.await_args_list)
    # Constrained decoding reserved too much output on the live tier. JSON mode
    # still faces the same strict assessment, source-binding and agreement checks.
    assert all('response_schema' not in call.kwargs for call in generator.await_args_list)
    assert all(len(json.loads(call.args[1])['rows']) == 4 for call in generator.await_args_list)
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
    assert result.status == 'NEEDS_REVIEW' and any(row.arithmeticCorrect is True for row in result.rows)
    assert not result.praise
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
    assert all(row.status == 'OK' for row in result.rows)
    assert result.rows[1].arithmeticCorrect is True
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
    assert result.status == 'CORRECT' and all(row.status == 'OK' for row in result.rows)
    review._safe_assessment(result, review.source_rows(source.workText))
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
    assert result.status == 'CORRECT'
    review._safe_assessment(result, review.source_rows(source.workText))
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
    assert result.status == ('NEEDS_REVIEW' if field in {'nextAction', 'hints'} else 'CORRECT')
    assert not result.alternative
    review._safe_assessment(result, review.source_rows(source.workText))
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
    assert result.status == 'NEEDS_REVIEW' and any(row.arithmeticCorrect is True for row in result.rows)
    assert not result.praise
    generated.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize('failure', [review.TutorUnavailable(), TimeoutError()])
async def test_provider_failure_cannot_manufacture_a_review(monkeypatch, failure):
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=failure))
    result = await review.review_work(request(workText='Số bút là:\n12 + 5 ='))
    assert result.status == 'NEEDS_REVIEW' and not result.praise
    assert [row.status for row in result.rows] == ['OK', 'UNSURE']
    assert result.rows[-1].rowKind == 'UNVERIFIABLE'


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
    assert set(body) == {'sourceId', 'status', 'summary', 'praise', 'rows', 'nextAction', 'alternative', 'complete', 'missingPart', 'arithmeticVerified', 'missingParts', 'completionVersion'}
    assert body['completionVersion'] == 2 and body['missingParts'] == []
    assert body['sourceId'] == source.sourceId and body['status'] == 'CORRECT'
    assert body['complete'] is True and body['missingPart'] == ''
    assert body['arithmeticVerified'] is True
    assert all(set(row) == {'lineIndex', 'sourceText', 'status', 'errorKind', 'feedback', 'hints', 'rowKind', 'arithmeticCorrect'} for row in body['rows'])


@pytest.mark.asyncio
async def test_missing_total_survives_a_wording_error_in_existing_work(monkeypatch):
    source = request(workText='Số cây trong vườn là:\n1/3 + 2/5 = 11/15')
    missing = 'Em còn thiếu bước tìm tổng số cây trong vườn từ số cây cam và phần tương ứng, rồi viết đáp số.'
    judged = assessment(source, complete=False, methodCorrect=False, praise='', missingPart=missing)
    judged['rows'][0].update(status='FIX', errorKind='EXPLANATION',
        feedback='Phép tính bên dưới tìm phần cây táo và xoài, chưa phải tổng số cây.',
        hints=['Em viết rõ đại lượng mà phép tính bên dưới đang tìm.'])
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVISION' and result.complete is False
    assert result.missingPart == missing and result.rows[0].errorKind == 'EXPLANATION'
    assert result.rows[1].status == 'OK'


@pytest.mark.asyncio
@pytest.mark.parametrize('kind,work', [
    ('CALCULATION', '1/3 + 2/5 = 11/14'),
    ('OPERAND', '1/3 + 2/4 = 2/6'),
    ('OPERAND', '1/3 + 2/4 = 5/6'),
    ('UNIT', '12 + 5 = 17 (m)'),
])
async def test_independently_agreed_error_kind_is_preserved(monkeypatch, kind, work):
    source = request(workText=work)
    judged = assessment(source, mathematicsCorrect=False, complete=False, praise='')
    judged['rows'][0].update(status='FIX', errorKind=kind,
        feedback='Em đối chiếu mẫu số của dữ kiện với đề gốc.' if kind == 'OPERAND' else 'Em kiểm tra bước này với đề gốc.',
        hints=['Em kiểm tra lại dữ kiện và thao tác ở dòng này.'])
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVISION' and result.rows[0].errorKind == kind
    assert result.rows[0].sourceText == work and result.complete is False


@pytest.mark.asyncio
async def test_unavailable_review_does_not_invent_completeness_or_copied_operands(monkeypatch):
    source = request(workText='1/3 + 2/4 = 2/6')
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=review.TutorUnavailable()))
    result = await review.review_work(source)
    assert result.complete is None and result.missingPart == ''
    assert result.rows[0].errorKind == 'CALCULATION'


@pytest.mark.asyncio
@pytest.mark.parametrize('work', [
    '16 : 4/15 = 60 (cây)', '16 : (4)/(15) = 60 (cây)',
    '16 ÷ (4/15) = 60 (cây)', '1/3 : 2/5 = 5/6',
    '12 : 3 × 2 = 8', '(12 / 3) / 2 = 2', '12 / (3 / 2) = 8',
])
async def test_visible_division_by_a_fraction_keeps_its_whole_denominator(monkeypatch, work):
    source = request(workText=work)
    cloud(monkeypatch, assessment(source))
    result = await review.review_work(source)
    assert result.status == 'CORRECT' and result.rows[0].status == 'OK'


@pytest.mark.asyncio
async def test_false_fraction_division_remains_a_calculation_error(monkeypatch):
    source = request(workText='16 : 4/15 = 4/15')
    cloud(monkeypatch, assessment(source))
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVISION' and result.rows[0].errorKind == 'CALCULATION'


@pytest.mark.asyncio
async def test_full_width_equals_is_verified_when_the_provider_fails(monkeypatch):
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=review.TutorUnavailable('rate_limit')))
    result = await review.review_work(request(workText='Bài giải:\n12 + 5＝18\n18 × 2＝36'))
    assert [row.errorKind for row in result.rows] == ['NONE', 'CALCULATION', 'DEPENDENT']
    assert [row.arithmeticCorrect for row in result.rows] == [None, False, True]


@pytest.mark.asyncio
async def test_ungrouped_slash_chain_requires_clarification_even_when_models_accept_it(monkeypatch):
    source = request(workText='12 / 3 / 2 = 2')
    cloud(monkeypatch, assessment(source))
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW'
    assert result.rows[0].rowKind == 'UNVERIFIABLE'
    assert result.rows[0].arithmeticCorrect is None and result.rows[0].status == 'UNSURE'


@pytest.mark.asyncio
async def test_model_dependency_cannot_hide_a_locally_proven_false_equality(monkeypatch):
    source = request(workText='74 : 2 = 36\n36 + 5 = 40')
    judged = assessment(source, mathematicsCorrect=False, praise='')
    for row in judged['rows']:
        row.update(status='FIX', errorKind='DEPENDENT')
    cloud(monkeypatch, judged)
    result = await review.review_work(source)
    assert [row.errorKind for row in result.rows] == ['CALCULATION', 'CALCULATION']
    assert [row.arithmeticCorrect for row in result.rows] == [False, False]


@pytest.mark.asyncio
async def test_heading_alone_cannot_receive_whole_solution_praise(monkeypatch):
    source = request(workText='Bài giải:')
    cloud(monkeypatch, assessment(source))
    result = await review.review_work(source)
    assert result.status == 'NEEDS_REVIEW' and not result.praise
    assert result.rows[0].rowKind == 'HEADING'


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


# Fresh completion fixtures below simulate independent reviewers; they are not live AI evidence.
def _completion_source(problem, work, identity='fresh-missing-proof-94017'):
    return review.WorkReviewRequest(sourceId=identity, problemText=problem, workText=work,
                                    problemConfirmed=True, workConfirmed=True)


@pytest.mark.asyncio
async def test_completion_evidence_is_serialized_by_authenticated_fastapi_endpoint(monkeypatch):
    source = _completion_source('Có 29 kg gạo, đã bán 7 kg. Hỏi số gạo còn lại?', 'Số gạo đã bán là:\n7 * 1 = 7 (kg)')
    payload = _completion_judgment(source, 'số gạo còn lại')
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    app = FastAPI()
    app.include_router(tutor.router, prefix='/internal/v1/tutor')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        response = await client.post('/internal/v1/tutor/work-review', json=source.model_dump(),
                                     headers={'X-Internal-API-Key': settings.internal_api_key})
    assert response.status_code == 200
    body = response.json()
    assert body['completionVersion'] == 2 and body['sourceId'] == source.sourceId
    assert body['missingParts'][0]['target'] == 'số gạo còn lại'
    assert body['missingParts'][0]['relatedLineIndices'] == [1]


def _completion_judgment(request, quantity, **changes):
    return dict(sourceFaithful=True, methodCorrect=True, unitsCorrect=True, mathematicsCorrect=True,
                complete=False, summary='Các phép tính đã viết phù hợp.', praise='', alternative='',
                nextAction='Em đọc lại yêu cầu của đề nhé.', missingPart='Kết quả cuối là 72 cây.',
                rows=[dict(lineIndex=i, sourceText=text, status='OK', errorKind='NONE',
                           feedback='Phép tính phù hợp.', hints=[])
                      for i, text in enumerate(review.source_rows(request.workText))],
                gaps=[dict(requirementIndex=0, type='MISSING_CALCULATION', quantity=quantity,
                           relatedLineIndices=[len(review.source_rows(request.workText)) - 1])], **changes)


@pytest.mark.asyncio
async def test_unsafe_prose_does_not_erase_source_bound_missing_quantity(monkeypatch):
    request = _completion_source('Vườn của dì Hoa có 3/8 số cây là mận, 1/4 là ổi, còn lại là mít. '
                     'Có 27 cây mít. Hỏi tổng số cây trong vườn của dì Hoa?',
                     'Phân số chỉ số cây mít là:\n1 - 3/8 - 1/4 = 3/8 (số cây)')
    payload = _completion_judgment(request, 'tổng số cây trong vườn của dì Hoa')
    payload['gaps'][0]['givenQuantities'] = ['số cây mít']
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    result = await review.review_work(request)
    parts = result.model_dump().get('missingParts')
    assert parts and parts[0]['target'] == 'tổng số cây trong vườn của dì Hoa'
    assert 'phân số chỉ số cây mít' in parts[0]['hint'].lower()
    assert 'số cây mít đề cho' in parts[0]['hint']
    assert '72' not in str(parts) and result.complete is False


def fresh_problems():
    for i, name in enumerate(['Linh', 'Hải', 'Thảo', 'Quỳnh', 'Minh']):
        n = 13 + i * 3
        examples = [
            (f'Vườn của cô {name} có 3/10 số cây là bưởi, 1/5 là nhãn, còn lại là ổi. '
             f'Có {n} cây ổi. Hỏi tổng số cây trong vườn của cô {name}?',
             'Phân số chỉ số cây ổi là:\n1 - 3/10 - 1/5 = 1/2 (số cây)',
             f'tổng số cây trong vườn của cô {name}', 0),
            (f'Lớp Sao Biển có {5*n} học sinh, nữ chiếm 3/5 số học sinh. Hỏi số học sinh nam trong lớp?',
             f'Số học sinh nữ là:\n{5*n} * 3/5 = {3*n} (học sinh)', 'số học sinh nam trong lớp', 0),
            (f'Mảnh vườn dài {3*n} m, chiều rộng bằng chiều dài chia 3. Tính diện tích mảnh vườn.',
             f'Chiều rộng mảnh vườn là:\n{3*n} : 3 = {n} (m)', 'diện tích mảnh vườn', 0),
            (f'Hình chữ nhật dài {n} m và rộng 7 m. Tính chu vi và diện tích hình chữ nhật.',
             f'Chu vi hình chữ nhật là:\n({n} + 7) * 2 = {2*(n+7)} (m)', 'diện tích hình chữ nhật', 1),
            (f'Mảnh đất dài {n} m, rộng 7 m, dùng 2/7 diện tích để trồng hoa. Tính diện tích phần đất trồng hoa.',
             f'Diện tích mảnh đất là:\n{n} * 7 = {7*n} (m²)', 'diện tích phần đất trồng hoa', 0),
            (f'Xe đi hai chặng dài {n} km và {2*n} km trong 3 giờ. Tính vận tốc trung bình của xe.',
             f'Quãng đường xe đi là:\n{n} + {2*n} = {3*n} (km)', 'vận tốc trung bình của xe', 0),
            (f'Chị {name} mua {n} gói bánh, mỗi gói 7 nghìn đồng, được giảm 5 nghìn đồng. Hỏi số tiền còn phải trả?',
             f'Số tiền mua bánh trước khi giảm là:\n{n} * 7 = {7*n} (nghìn đồng)', 'số tiền còn phải trả', 0),
            (f'Khối hộp dài {n} m, rộng 7 m, cao 4 m. Tính thể tích khối hộp.',
             f'Diện tích đáy khối hộp là:\n{n} * 7 = {7*n} (m²)', 'thể tích khối hộp', 0),
        ]
        for family, (problem, work, quantity, requirement) in enumerate(examples):
            yield f'fresh-completion-{i:02}-{family:02}-source', problem, work, quantity, requirement


@pytest.mark.asyncio
@pytest.mark.parametrize('identity,problem,work,quantity,requirement', list(fresh_problems()))
async def test_forty_new_problems_keep_specific_safe_continuation(monkeypatch, identity, problem, work, quantity, requirement):
    request = _completion_source(problem, work, identity)
    payload = _completion_judgment(request, quantity)
    payload['gaps'][0]['requirementIndex'] = requirement
    generator = AsyncMock(side_effect=[payload, deepcopy(payload)])
    monkeypatch.setattr(review, '_generate', generator)
    result = await review.review_work(request)
    assert result.complete is False and result.arithmeticVerified is True
    assert result.missingParts[0].target == quantity
    assert result.missingParts[0].relatedLineIndices == [1]
    assert result.missingParts[0].requirementIndex == requirement
    assert quantity in result.missingParts[0].hint
    assert not any(char.isnumeric() for char in result.missingParts[0].description + result.missingParts[0].hint)
    assert all(row.status == 'OK' for row in result.rows)
    assert generator.await_count == 2


@pytest.mark.asyncio
async def test_intermediate_quantity_is_source_bound_but_compact_valid_method_is_accepted(monkeypatch):
    problem = 'Mảnh vườn có chiều dài 18 m, chưa biết chiều rộng, chu vi 54 m. Tính diện tích mảnh vườn.'
    request = _completion_source(problem, 'Nửa chu vi là:\n54 : 2 = 27 (m)')
    payload = _completion_judgment(request, 'chiều rộng')
    payload['gaps'][0]['type'] = 'MISSING_INTERMEDIATE'
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    result = await review.review_work(request)
    assert result.missingParts[0].type == 'MISSING_INTERMEDIATE'
    assert 'chiều rộng trước' in result.missingParts[0].hint
    complete = _completion_source(problem, 'Diện tích mảnh vườn là:\n(54 : 2 - 18) * 18 = 162 (m²)')
    payload = _completion_judgment(complete, 'diện tích mảnh vườn')
    payload.update(complete=True, gaps=[], missingPart='', praise='Em đã chọn cách tính phù hợp.')
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    result = await review.review_work(complete)
    assert result.status == 'CORRECT' and not result.missingParts


@pytest.mark.asyncio
async def test_missing_answer_only_when_explicitly_required(monkeypatch):
    for required in [True, False]:
        request = _completion_source('Hình chữ nhật dài 9 m, rộng 4 m. Tính diện tích hình chữ nhật'
                         + (' và ghi đáp số.' if required else '.'), 'Diện tích hình chữ nhật là:\n9 * 4 = 36 (m²)')
        payload = _completion_judgment(request, 'diện tích hình chữ nhật')
        payload['gaps'][0]['type'] = 'MISSING_ANSWER'
        monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
        result = await review.review_work(request)
        assert bool(result.missingParts) is required
        if required:
            assert 'giữ nguyên phép tính' in result.missingParts[0].hint
        else:
            assert result.complete is None


@pytest.mark.asyncio
async def test_missing_questions_are_sorted_in_source_order(monkeypatch):
    request = _completion_source('Khối hộp dài 9 m, rộng 4 m, cao 3 m. a) Tính chu vi đáy; '
                     'b) Tính diện tích đáy; c) Tính thể tích khối hộp.', 'Chu vi đáy là:\n(9 + 4) * 2 = 26 (m)')
    payload = _completion_judgment(request, 'thể tích khối hộp')
    payload['gaps'][0]['requirementIndex'] = 2
    payload['gaps'].append(dict(requirementIndex=1, type='MISSING_CALCULATION', quantity='diện tích đáy', relatedLineIndices=[1]))
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    result = await review.review_work(request)
    assert [part.target for part in result.missingParts] == ['diện tích đáy', 'thể tích khối hộp']


@pytest.mark.asyncio
async def test_not_started_needs_no_cloud_but_unreadable_diagram_is_not_invented(monkeypatch):
    generator = AsyncMock(side_effect=review.TutorUnavailable('rate_limit'))
    monkeypatch.setattr(review, '_generate', generator)
    result = await review.review_work(_completion_source('Có 29 kg gạo, bán 7 kg. Hỏi số gạo còn lại?', 'Bài giải:'))
    assert result.missingParts[0].type == 'NOT_STARTED' and result.complete is False
    generator.assert_not_called()
    result = await review.review_work(_completion_source('Theo hình bên có 29 m. Tính diện tích.', 'Bài giải:'))
    assert result.complete is None and not result.missingParts


@pytest.mark.asyncio
@pytest.mark.parametrize('bad', ['số tiền của bác Đạt', 'diện tích bằng 36', 'API key'])
async def test_invented_or_answer_bearing_quantities_are_not_published(monkeypatch, bad):
    request = _completion_source('Có 29 kg gạo, bán 7 kg. Hỏi số gạo còn lại?', 'Số gạo bán là:\n7 * 1 = 7 (kg)')
    payload = _completion_judgment(request, bad)
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    result = await review.review_work(request)
    assert not result.missingParts and result.complete is None
    assert result.rows[1].arithmeticCorrect is True


@pytest.mark.asyncio
async def test_disagreement_timeout_and_revision_preserve_math_without_stale_missing_parts(monkeypatch):
    request = _completion_source('Lớp có 40 học sinh, nữ chiếm 3/5. Hỏi số học sinh nam trong lớp?',
                     'Số học sinh nữ là:\n40 * 3/5 = 24 (học sinh)')
    first = _completion_judgment(request, 'số học sinh nam trong lớp')
    second = deepcopy(first)
    second['gaps'][0]['quantity'] = 'số học sinh nữ'
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[first, second]))
    result = await review.review_work(request)
    assert result.complete is None and not result.missingParts and result.arithmeticVerified
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=TimeoutError()))
    result = await review.review_work(request)
    assert result.complete is None and not result.missingParts and result.rows[1].arithmeticCorrect
    revised = _completion_source(request.problemText, request.workText + '\nSố học sinh nam là:\n40 - 24 = 16 (học sinh)', 'fresh-revised-source-94017')
    payload = _completion_judgment(revised, 'số học sinh nam')
    payload.update(complete=True, missingPart='', gaps=[], praise='Em đã trả lời đủ câu hỏi của đề.')
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    result = await review.review_work(revised)
    assert result.sourceId == revised.sourceId and result.status == 'CORRECT' and not result.missingParts


def test_source_names_and_gender_are_not_confused_with_number_answers():
    problem = 'Bác Sáu hỏi số học sinh nam trong lớp.'
    review._completion_text('Tìm số học sinh nam của bác Sáu.', problem)
    with pytest.raises(ValueError):
        review._completion_text('Số học sinh nam là năm.', problem)
    with pytest.raises(ValueError):
        review._completion_text('Đáp số: sáu học sinh.', problem)


@pytest.mark.asyncio
async def test_compact_reviewer_and_independent_verifier_carry_completion_evidence(monkeypatch):
    request = _completion_source('Có 29 kg gạo, đã bán 7 kg. Hỏi số gạo còn lại?', 'Số gạo đã bán là:\n7 * 1 = 7 (kg)')
    full = _completion_judgment(request, 'số gạo còn lại')
    compact = {key: value for key, value in full.items() if key not in {'summary', 'nextAction', 'alternative', 'missingPart'}}
    verifier = {key: value for key, value in compact.items() if key != 'praise'}
    verifier['rows'] = [{key: value for key, value in row.items() if key not in {'feedback', 'hints'}} for row in verifier['rows']]
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[compact, verifier]))
    result = await review.review_work(request)
    assert result.missingParts[0].target == 'số gạo còn lại'
    assert result.missingParts[0].relatedLineIndices == [1]


@pytest.mark.asyncio
async def test_technical_prose_is_rejected_without_erasing_independently_verified_gap(monkeypatch):
    request = _completion_source('Có 29 kg gạo, đã bán 7 kg. Hỏi số gạo còn lại?', 'Số gạo đã bán là:\n7 * 1 = 7 (kg)')
    payload = _completion_judgment(request, 'số gạo còn lại')
    payload['rows'][1]['feedback'] = 'Open API localhost with provider-secret.'
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    result = await review.review_work(request)
    assert result.complete is False and result.missingParts[0].target == 'số gạo còn lại'
    assert 'provider-secret' not in result.model_dump_json() and 'localhost' not in result.model_dump_json()


@pytest.mark.asyncio
async def test_verbal_answer_is_not_misclassified_as_not_started(monkeypatch):
    request = _completion_source('Mai có 14 bút, Linh có 7 bút. Hỏi ai có nhiều bút hơn?', 'Mai có nhiều bút hơn Linh.')
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=TimeoutError()))
    result = await review.review_work(request)
    assert result.complete is None and not result.missingParts


@pytest.mark.asyncio
async def test_completion_fields_never_replace_unit_or_causal_calculation_errors(monkeypatch):
    source = _completion_source('Có 620 kg gạo bán đều trong 2 ngày. Hỏi bán trong 7 ngày được bao nhiêu kg gạo?',
                                '620 : 2 = 300 (kg)\n300 * 7 = 2100 (kg)')
    payload = _completion_judgment(source, 'số kg gạo')
    payload.update(complete=True, mathematicsCorrect=False, missingPart='', gaps=[])
    for row, kind in zip(payload['rows'], ['CALCULATION', 'DEPENDENT']):
        row.update(status='FIX', errorKind=kind, feedback='Em tính lại theo kết quả đúng của bước trước nhé.')
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    result = await review.review_work(source)
    assert [row.errorKind for row in result.rows] == ['CALCULATION', 'DEPENDENT']
    assert result.status == 'NEEDS_REVISION' and not result.missingParts

    source = _completion_source('Có 18 kg gạo, bán 6 kg. Hỏi số kg gạo còn lại?', '18 - 6 = 12')
    payload = _completion_judgment(source, 'số kg gạo còn lại')
    payload.update(complete=True, unitsCorrect=False, missingPart='', gaps=[])
    payload['rows'][0].update(status='FIX', errorKind='UNIT', feedback='Em bổ sung đơn vị cho số gạo còn lại nhé.')
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    result = await review.review_work(source)
    assert result.rows[0].errorKind == 'UNIT' and result.rows[0].arithmeticCorrect is True
    assert not result.missingParts and result.status == 'NEEDS_REVISION'


@pytest.mark.asyncio
async def test_agreed_gap_survives_cloud_arithmetic_dispute_only_with_exact_local_proof(monkeypatch):
    source = _completion_source('Hình chữ nhật dài 18 m, rộng 7 m. a) Tính chu vi hình chữ nhật; b) Tính diện tích hình chữ nhật.',
                                'Chu vi hình chữ nhật là:\n(18 + 7) × 2 = 50 (m)')
    first = _completion_judgment(source, 'diện tích hình chữ nhật')
    first['gaps'][0].update(requirementIndex=1, relatedLineIndices=[])
    second = deepcopy(first)
    first['mathematicsCorrect'] = False
    first['rows'][1].update(status='FIX', errorKind='CALCULATION', feedback='Em kiểm tra phép tính nhé.')
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[first, second]))
    result = await review.review_work(source)
    assert result.complete is False and result.missingParts[0].target == 'diện tích hình chữ nhật'
    assert result.rows[1].status == 'OK' and result.rows[1].arithmeticCorrect is True
    assert result.status != 'CORRECT' and not result.praise
    second['unitsCorrect'] = False
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[first, second]))
    result = await review.review_work(source)
    assert result.complete is None and not result.missingParts


@pytest.mark.asyncio
async def test_a_given_ratio_does_not_turn_computed_width_into_a_given_value(monkeypatch):
    source = _completion_source('Mảnh vườn hình chữ nhật dài 24 m, chiều rộng bằng 2/3 chiều dài. Tính diện tích mảnh vườn.',
                                'Chiều rộng mảnh vườn là:\n24 × 2/3 = 16 (m)')
    payload = _completion_judgment(source, 'diện tích mảnh vườn')
    payload['gaps'][0]['givenQuantities'] = ['chiều dài', 'chiều rộng']
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    result = await review.review_work(source)
    assert 'tìm được chiều rộng' in result.missingParts[0].hint
    assert 'cùng chiều dài đề cho' in result.missingParts[0].hint
    assert 'chiều rộng đề cho' not in result.missingParts[0].hint


@pytest.mark.asyncio
async def test_child_friendly_hint_explains_the_next_operation_without_giving_values(monkeypatch):
    source = _completion_source('Lớp có 40 học sinh, nữ chiếm 3/5. Hỏi số học sinh nam trong lớp?',
                                'Số học sinh nữ là:\n40 × 3/5 = 24 (học sinh)', 'clear-child-guidance-01')
    payload = _completion_judgment(source, 'số học sinh nam trong lớp')
    payload['gaps'][0].update(operation='SUBTRACT', operands=['tổng số học sinh trong lớp', 'số học sinh nữ'])
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    result = await review.review_work(source)
    hint = result.missingParts[0].hint
    assert 'Em đã tìm được số học sinh nữ.' in hint
    assert 'Em lấy tổng số học sinh trong lớp trừ đi số học sinh nữ.' in hint
    assert 'Kết quả cho biết số học sinh nam trong lớp.' in hint
    assert not any(char.isnumeric() for char in hint)
    assert len(hint) <= 300 and result.rows[1].arithmeticCorrect is True


@pytest.mark.asyncio
@pytest.mark.parametrize('problem,work,target,operation,operands,action', [
    ('Mai có 18 bút, Linh có 7 bút. Tính tổng số bút của Mai và Linh.',
     'Số bút của Mai là:\n18 × 1 = 18 (bút)', 'tổng số bút của Mai và Linh', 'ADD', ['số bút của Mai', 'số bút của Linh'], 'cộng với'),
    ('Hình chữ nhật dài 18 m, chiều rộng bằng chiều dài chia 3. Tính diện tích hình chữ nhật.',
     'Chiều rộng là:\n18 : 3 = 6 (m)', 'diện tích hình chữ nhật', 'MULTIPLY', ['chiều dài', 'chiều rộng'], 'nhân với'),
    ('Xe đi hai chặng 18 km và 12 km trong tổng thời gian 3 giờ. Tính vận tốc của xe.',
     'Quãng đường là:\n18 + 12 = 30 (km)', 'vận tốc của xe', 'DIVIDE', ['quãng đường', 'thời gian'], 'chia cho'),
])
async def test_clear_operation_guidance_works_with_new_quantities(monkeypatch, problem, work, target, operation, operands, action):
    source = _completion_source(problem, work)
    payload = _completion_judgment(source, target)
    payload['gaps'][0].update(operation=operation, operands=operands)
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    result = await review.review_work(source)
    assert action in result.missingParts[0].hint
    assert target in result.missingParts[0].hint
    assert not any(char.isnumeric() for char in result.missingParts[0].hint)


@pytest.mark.asyncio
@pytest.mark.parametrize('change', ['operation', 'order', 'invented', 'answer-value'])
async def test_unconfirmed_or_ungrounded_operation_never_becomes_teaching(monkeypatch, change):
    source = _completion_source('Lớp có 40 học sinh, nữ chiếm 3/5. Hỏi số học sinh nam trong lớp?',
                                'Số học sinh nữ là:\n40 × 3/5 = 24 (học sinh)')
    first = _completion_judgment(source, 'số học sinh nam trong lớp')
    first['gaps'][0].update(operation='SUBTRACT', operands=['tổng số học sinh trong lớp', 'số học sinh nữ'])
    if change == 'invented': first['gaps'][0]['operands'][0] = 'số sách của bác Tùng'
    if change == 'answer-value': first['gaps'][0]['operands'][0] = '40 học sinh'
    second = deepcopy(first)
    if change == 'operation': second['gaps'][0]['operation'] = 'ADD'
    if change == 'order': second['gaps'][0]['operands'].reverse()
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[first, second]))
    result = await review.review_work(source)
    assert result.missingParts and 'trừ đi' not in result.missingParts[0].hint
    assert 'Tùng' not in result.missingParts[0].hint and '40' not in result.missingParts[0].hint
    assert result.rows[1].arithmeticCorrect is True


@pytest.mark.asyncio
async def test_a_later_question_tells_the_child_to_finish_its_missing_input_first(monkeypatch):
    source = _completion_source('Lớp có 40 học sinh, nữ chiếm 3/5. a) Hỏi số học sinh nam trong lớp? '
                                'b) Tính số học sinh nữ nhiều hơn nam.',
                                'Số học sinh nữ là:\n40 × 3/5 = 24 (học sinh)')
    payload = _completion_judgment(source, 'số học sinh nam trong lớp')
    payload['gaps'][0].update(operation='SUBTRACT', operands=['tổng số học sinh trong lớp', 'số học sinh nữ'])
    payload['gaps'].insert(0, dict(requirementIndex=1, type='MISSING_CALCULATION', quantity='số học sinh nữ nhiều hơn nam',
        relatedLineIndices=[1], operation='SUBTRACT', operands=['số học sinh nữ', 'số học sinh nam trong lớp']))
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[payload, deepcopy(payload)]))
    result = await review.review_work(source)
    assert result.missingParts[0].requirementIndex == 0
    assert 'Trước hết, em tìm số học sinh nam trong lớp ở phần trên.' in result.missingParts[1].hint
    assert 'Sau đó, em lấy số học sinh nữ trừ đi số học sinh nam trong lớp.' in result.missingParts[1].hint


@pytest.mark.asyncio
@pytest.mark.parametrize('citation,has_operation', [('Lớp có 40 học sinh', True), ('Lớp có 41 học sinh', False)])
async def test_original_fact_citation_can_confirm_a_name_without_publishing_its_value(monkeypatch, citation, has_operation):
    source = _completion_source('Lớp có 40 học sinh, nữ chiếm 3/5. Hỏi số học sinh nam trong lớp?',
                                'Số học sinh nữ là:\n40 × 3/5 = 24 (học sinh)')
    first = _completion_judgment(source, 'số học sinh nam trong lớp')
    first['gaps'][0].update(operation='SUBTRACT', operands=['tổng số học sinh trong lớp', 'số học sinh nữ'])
    second = deepcopy(first)
    second['gaps'][0]['operands'][0] = citation
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=[first, second]))
    result = await review.review_work(source)
    assert ('trừ đi' in result.missingParts[0].hint) is has_operation
    assert not any(char.isnumeric() for char in result.missingParts[0].hint)


def test_comparative_gender_name_is_not_a_number_but_an_answer_value_stays_blocked():
    problem = 'Hỏi số học sinh nam trong lớp và số học sinh nữ nhiều hơn nam.'
    review._completion_text('Kết quả cho biết số học sinh nữ nhiều hơn nam.', problem)
    with pytest.raises(ValueError):
        review._completion_text('Số học sinh nữ nhiều hơn nam là nam.', problem)


@pytest.mark.parametrize('first_inputs,second_inputs', [
    (['số cây cam', 'phân số chỉ số cây cam'], ['phân số chỉ số cây cam', 'số cây cam']),
    (['tổng số gạo', 'số gạo còn lại'], ['số gạo còn lại', 'tổng số gạo']),
    (['tổng diện tích', 'diện tích'], ['diện tích', 'tổng diện tích']),
])
def test_operation_consensus_preserves_fraction_and_remainder_meaning(first_inputs, second_inputs):
    first = review.CompletionGap(requirementIndex=0, type='MISSING_CALCULATION', quantity='phần còn thiếu',
                                 operation='DIVIDE', operands=first_inputs)
    second = first.model_copy(update={'operands': second_inputs})
    gap = list(review.agreed_gaps([first], [second]))[0]
    assert gap.operation is None and not gap.operands


# Confirmed transcription regression; providers below are synthetic/offline.
_CONVERSION_OK = [
    '300 yến = 30 tạ', 'Đổi: 300 yến = 30 tạ.', 'Đổi 300 yến = 30 tạ',
    'Đổi đơn vị:300 yến＝30 tạ。', '10m = 1000cm', '10 m = 1000 cm',
    '1,5 m = 150 cm', '1.5 m = 150 cm', '2 kg = 2000 g',
    '3 m² = 30000 cm²', '1 giờ = 60 phút', '1 m^{2} = 10000 cm2',
    '1 km = 10 hm', '1 hm = 10 dam', '1 dam = 10 m', '1 dm = 100 mm',
    '1 tấn = 10 tạ', '1 kg = 10 hg', '1 hg = 10 dag', '1 dag = 10 g', '1 g = 1000 mg',
    '1 km² = 100 hm²', '1 hm² = 100 dam²', '1 dam² = 100 m²',
    '1 ha = 10000 m²', '1 dm² = 100 cm²', '1 cm² = 100 mm²',
    '1 m³ = 1000 dm³', '1 dm³ = 1000 cm³', '1 cm³ = 1000 mm³',
    '1 l = 1 dm³', '1 l = 1000 ml', '1 tuần = 7 ngày', '1 ngày = 24 giờ',
    '1 phút = 60 giây', '1/2 kg = 500 g', 'ĐỔI：１０Ｍ＝１０００ＣＭ',
    '3 m ² = 30000 cm ²', '1 m ³ = 1000 dm ³', '1 ki-lô-mét = 1000 mét',
    '1 m = 100 cm = 1000 mm',
]

@pytest.mark.parametrize('text', _CONVERSION_OK)
def test_confirmed_unit_conversion_notation(text):
    row = review._local_rows([text])[0]
    assert (row.rowKind, row.status, row.errorKind, row.arithmeticCorrect) == ('CALCULATION', 'OK', 'NONE', True)
    assert row.sourceText == text and not row.hints

@pytest.mark.parametrize('text', ['300 yến = 3 tạ', '10 m = 100 cm', '2 kg = 200 g',
    '1 giờ = 100 phút', '1 m² = 100 cm²', '1 m = 1 kg', '2 giờ = 120 cm'])
def test_confirmed_wrong_or_incompatible_unit_conversion(text):
    row = review._local_rows([text])[0]
    assert (row.rowKind, row.status, row.errorKind, row.arithmeticCorrect) == ('CALCULATION', 'FIX', 'CALCULATION', False)
    assert 'đơn vị' in row.feedback

@pytest.mark.parametrize('text', ['300 yến =', '10 m = ? cm', '300 ? = 30 tạ',
    '1 tháng = 30 ngày', '1 năm = 365 ngày', 'Dự đoán: 10m = 1000cm', '10 m ≈ 1000 cm',
    '2⁰ m = 20 m', '2⁴ m = 24 m', '2₄ m = 24 m', '② m = 200 cm'])
def test_unreadable_or_unsupported_conversion_stays_unsure(text):
    row = review._local_rows([text])[0]
    assert row.status == 'UNSURE' and row.arithmeticCorrect is None

@pytest.mark.asyncio
@pytest.mark.parametrize('failure', [TimeoutError(), review.TutorUnavailable('rate_limit')])
async def test_conversion_remains_local_during_provider_outage(monkeypatch, failure):
    source = request(workText='Bài giải:\nĐổi: 300 yến = 30 tạ.\n30 + 2 = 32',
        problemText='Đổi khối lượng rồi tính tổng. Viết riêng câu đáp số.')
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=failure))
    result = await review.review_work(source)
    assert [r.lineIndex for r in result.rows] == [0, 1, 2]
    assert result.rows[1].status == 'OK' and result.rows[1].arithmeticCorrect is True
    assert result.complete is not True and result.status != 'CORRECT'

@pytest.mark.asyncio
@pytest.mark.parametrize('both_unsure', [True, False])
async def test_provider_uncertainty_does_not_erase_exact_conversion(monkeypatch, both_unsure):
    source = request(workText='Đổi: 300 yến = 30 tạ.', problemText='Đổi khối lượng rồi viết kết luận.')
    first = assessment(source, complete=False, praise='')
    second = deepcopy(first)
    first['rows'][0].update(status='UNSURE', feedback='Chưa đọc rõ cú pháp.')
    if both_unsure: second['rows'][0].update(status='UNSURE', feedback='Cần kiểm tra lại dòng.')
    providers = cloud(monkeypatch, first, second)
    result = await review.review_work(source)
    assert providers.await_count == 2
    assert result.rows[0].status == 'OK' and result.rows[0].arithmeticCorrect is True
    assert result.complete is not True and result.status != 'CORRECT'

def test_wrong_conversion_keeps_causal_dependency_and_plain_math():
    rows = review._dependent_rows(review._local_rows(['Đổi: 300 yến = 3 tạ.', '3 + 2 = 5']))
    assert rows[0].status == 'FIX' and rows[0].arithmeticCorrect is False
    assert rows[1].errorKind == 'DEPENDENT' and rows[1].arithmeticCorrect is True
    assert review._local_rows(['2 + 3 = 5'])[0].status == 'OK'


@pytest.mark.asyncio
async def test_confirmed_conversion_api_source_and_offline_verdicts(monkeypatch):
    captured = json.loads((Path(__file__).parent / 'fixtures/work_review_unit_conversion.json').read_text(encoding='utf-8'))
    app = FastAPI()
    app.include_router(tutor.router, prefix='/internal/v1/tutor')
    monkeypatch.setattr(review, '_generate', AsyncMock(side_effect=TimeoutError()))
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        for text, status in [('Đổi: 300 yến = 30 tạ.', 'OK'), ('10 m = 1000 cm', 'OK'), ('300 yến = 3 tạ', 'FIX')]:
            source = request(workText=text, problemText='Đổi khối lượng hoặc độ dài và viết kết luận.')
            response = await client.post('/internal/v1/tutor/work-review', json=source.model_dump(),
                headers={'X-Internal-API-Key': settings.internal_api_key})
            assert response.status_code == 200
            body = response.json()
            assert body['sourceId'] == source.sourceId
            assert body['rows'][0]['sourceText'] == text and body['rows'][0]['status'] == status
            assert body['status'] != 'CORRECT' and body['complete'] is not True
            assert body == {**captured[text], 'sourceId': source.sourceId}


@pytest.mark.parametrize('error_kind', ['UNIT', 'OPERAND'])
def test_exact_conversion_still_requires_agreed_problem_context(error_kind):
    source = request(workText='Đổi: 300 yến = 30 tạ.')
    first = assessment(source)
    first['rows'][0].update(status='FIX', errorKind=error_kind,
        feedback='Em đối chiếu lại đại lượng đề bài yêu cầu.')
    judgment = review._Assessment.model_validate(first)
    row = review._merge_rows(review._local_rows([source.workText]), judgment, judgment)[0]
    assert row.status == 'FIX' and row.errorKind == error_kind
    assert row.arithmeticCorrect is True and row.sourceText == source.workText


@pytest.mark.parametrize('error_kind', ['UNIT', 'OPERAND'])
def test_exact_conversion_reports_uncertain_problem_context_when_reviewers_disagree(error_kind):
    source = request(workText='Đổi: 300 yến = 30 tạ.')
    first = assessment(source)
    second = deepcopy(first)
    first['rows'][0].update(status='FIX', errorKind=error_kind,
        feedback='Em đối chiếu lại với yêu cầu trong đề.')
    second['rows'][0].update(status='UNSURE', feedback='Chưa rõ yêu cầu đổi đơn vị.')
    row = review._merge_rows(
        review._local_rows([source.workText]),
        review._Assessment.model_validate(first),
        review._Assessment.model_validate(second),
    )[0]
    assert row.status == 'UNSURE' and row.arithmeticCorrect is True

"""Practice generation uses independent arithmetic checks, with providers mocked."""
from fractions import Fraction
from unittest.mock import AsyncMock

import httpx
import pytest

from app.tutoring import quiz_variants as quiz
from app.tutoring import lesson
from app.tutoring.service import TutorUnavailable


RICE_SOURCE = ('Câu 4. Một cửa hàng trong 2 ngày bán được 620 kg gạo. Hỏi trong 7 ngày cửa hàng bán được bao nhiêu ki-lô-gam gạo? '
               '(Biết số gạo mỗi ngày bán được là như nhau).\nA. 4340 kg\nB. 434 kg\nC. 217 kg\nD. 2170 kg')


@pytest.mark.asyncio
@pytest.mark.parametrize('source', [
    'Sắp xếp các số thập phân 1,25; 0,98; 3,56; 2,014 theo thứ tự từ bé đến lớn.',
    'Câu 4. Sắp xếp các số thập phân 1,25; 0,98; 3,56; 2,014 theo thứ tự từ bé đến lớn là: '
    'A. 1,25; 3,56; 0,98; 2,014 B. 3,56; 2,014; 1,25; 0,98 '
    'C. 0,98; 1,25; 2,014; 3,56 D. 2,014; 0,98; 3,56; 1,25',
])
async def test_decimal_order_offers_checked_text_choices_without_a_provider(source, monkeypatch):
    provider = AsyncMock(side_effect=AssertionError('Exact choices need no model'))
    monkeypatch.setattr(quiz, '_generate', provider)
    result = await quiz.generate(quiz.VariantRequest(owner='sequence-fixture', problemText=source))
    assert result['answerFormat'] == 'CHOICE'
    stem, choices = quiz.split_choices(result['questionText'], allow_statement=True)
    selected = choices[int(result['answer']) - 1]
    values = [Fraction(part.strip().replace(',', '.')) for part in selected.split(';')]
    assert values == sorted(values)
    assert len(values) == 4 and selected in result['solution']
    assert quiz.checked_exact(result['questionText']) is not None
    provider.assert_not_called()


def checked_rice_plan():
    return lesson.Plan(topic='Rút về đơn vị', goal='Tìm số gạo bán được theo số ngày.', steps=[
        lesson.Step(title='Tìm lượng gạo mỗi ngày', question='Một ngày bán được bao nhiêu gạo?',
                    explanation='Chia lượng gạo cho số ngày để tìm lượng gạo mỗi ngày.', expression='620 / 2', unit='kg',
                    guidance=['Lấy số gạo đã bán chia đều cho số ngày đã bán.']),
        lesson.Step(title='Tìm lượng gạo cần hỏi', question='Trong số ngày cần hỏi, cửa hàng bán bao nhiêu gạo?',
                    explanation='Lấy lượng gạo mỗi ngày nhân với số ngày cần tìm.', expression='{s0} * 7', unit='kg',
                    guidance=['Dùng kết quả vừa tìm rồi nhân với số ngày mà đề hỏi.']),
        lesson.Step(title='Chọn đáp án', question='Em chọn phương án nào?', explanation='Đối chiếu kết quả với các phương án trong đề.',
                    choices=['A. 4340 kg', 'B. 434 kg', 'C. 217 kg', 'D. 2170 kg'], correctChoice='D. 2170 kg',
                    guidance=['So sánh lượng gạo vừa tính với từng phương án, giữ đúng đơn vị.']),
    ])


@pytest.mark.asyncio
@pytest.mark.parametrize('final_step', [None, 1, 2])
async def test_reported_checked_lesson_with_a_final_labelled_choice_can_offer_review(monkeypatch, final_step):
    source = checked_rice_plan()
    source.finalAnswerStep = final_step
    request = quiz.VariantRequest(owner='rice-fixture', problemText=RICE_SOURCE)
    lesson.validate_plan(source, lesson.LessonRequest(owner=request.owner, problemText=RICE_SOURCE, problemConfirmed=True), lesson.formula_constants(RICE_SOURCE))
    monkeypatch.setattr(quiz.catalog, 'load_plan', lambda request: source)
    monkeypatch.setattr(quiz, 'exact_plan', lambda text: None)
    monkeypatch.setattr(quiz, '_generate', AsyncMock(side_effect=TutorUnavailable('provider')))
    result = await quiz.generate(request)
    assert result['review'] is True
    assert result['answer'] == '2170' and result['unit'] == 'kg'
    assert quiz.proof(source)[2] == [['Div'], ['Mult']]
    assert result['questionText'].endswith('D. 2170 kg')


@pytest.mark.parametrize('selected', ['B. 434 kg', 'D. 2170 tấn', 'D. có 2170 kg'])
def test_a_choice_cannot_override_the_checked_calculation_or_change_its_unit(selected):
    plan = checked_rice_plan()
    plan.steps[-1].correctChoice = selected
    with pytest.raises(ValueError):
        quiz.proof(plan)


@pytest.mark.asyncio
@pytest.mark.parametrize('source', [
    'Tính: (12 + 8) / 4',
    'Tính: 25 * 4 - 6',
    RICE_SOURCE,
    'Điền vào chỗ chấm để: 1,7 km² = .... ha',
    '15 dm 2 cm = ........ dm',
    '9 tấn 4 kg = ........ tấn',
    '5 m² 26 dm² = ........ m²',
    '7 km² 5 ha = ........ ha',
    'Chu vi của hình chữ nhật là 48 dm. Hỏi diện tích mảnh đất là bao nhiêu dm². Biết chiều dài hơn chiều rộng là 6 dm.',
    'Bác An thu hoạch được 2 tấn 35 kg hạt điều và hạnh nhân. Biết rằng số lượng hạnh nhân chiếm 2/5 tổng số hạt điều và hạnh nhân thu hoạch được. Vậy, bác An thu hoạch được số ki – lô – gam hạnh nhân là:',
])
async def test_exact_variants_keep_the_operations_units_and_integral_work(source, monkeypatch):
    provider = AsyncMock(side_effect=AssertionError('Exact practice must not consume a model request'))
    monkeypatch.setattr(quiz, '_generate', provider)
    request = quiz.VariantRequest(owner='quiz-variants-fixture', problemText=source)
    result = await quiz.generate(request)
    source_proof = quiz.proof(quiz.checked_exact(source))
    plan = quiz.checked_exact(result['questionText'])
    checked = quiz.proof(plan)
    assert result['review'] is False
    assert Fraction(result['answer']) == checked[0] != source_proof[0]
    assert checked[1:3] == source_proof[1:3]
    if source_proof[4]:
        assert checked[4]
    provider.assert_not_called()


@pytest.mark.asyncio
async def test_reviewed_source_remains_available_when_a_provider_is_down(monkeypatch):
    source = 'Câu 1. Cho các phân số sau 18/10; 32/500; 99/100; 51/1000. Có .... phân số thập phân. A. 1 B. 2 C. 3 D. 4'
    monkeypatch.setattr(quiz, '_generate', AsyncMock(side_effect=TutorUnavailable('provider')))
    result = await quiz.generate(quiz.VariantRequest(owner='review-fixture', problemText=source))
    assert result['review'] is False
    checked = quiz.checked_exact(result['questionText'])
    assert Fraction(result['answer']) == quiz.proof(checked)[0]
    assert result['answer'] != '3'


@pytest.mark.asyncio
async def test_unverified_proposal_cannot_replace_a_previously_checked_source(monkeypatch):
    source = 'Tính: (12 + 8) / 4'
    checked_source = quiz.checked_exact(source)
    wrong_proposal = quiz.checked_exact('Tính: 1 + 1')
    monkeypatch.setattr(quiz, 'exact_plan', lambda text: None)
    monkeypatch.setattr(quiz.catalog, 'load_plan', lambda request: checked_source)
    monkeypatch.setattr(quiz, '_generate', AsyncMock(return_value={'problemText': 'Tính: 1 + 1'}))
    proposal_check = AsyncMock(return_value=wrong_proposal)
    monkeypatch.setattr(lesson, 'checked_plan', proposal_check)
    result = await quiz.generate(quiz.VariantRequest(owner='review-fixture', problemText=source))
    assert result['review'] is True
    assert result['answer'] == '5'
    proposal_check.assert_awaited_once()


@pytest.mark.asyncio
async def test_new_source_never_borrows_another_owners_plan_or_invents_an_answer(monkeypatch):
    monkeypatch.setattr(quiz.catalog, 'load_plan', lambda request: None)
    prepared = AsyncMock(return_value=None)
    monkeypatch.setattr(quiz.plan_preparation, 'prepared_plan', prepared)
    with pytest.raises(TutorUnavailable):
        await quiz.generate(quiz.VariantRequest(owner='source-owner', problemText='Một đề còn thiếu thông tin.'))
    assert prepared.call_args.args[0].owner == 'source-owner'


@pytest.mark.asyncio
async def test_provider_capacity_and_outages_keep_a_checked_review_available(monkeypatch):
    source = 'Tính: (12 + 8) / 4'
    checked_source = quiz.checked_exact(source)
    monkeypatch.setattr(quiz, 'exact_plan', lambda text: None)
    monkeypatch.setattr(quiz.catalog, 'load_plan', lambda request: checked_source)
    provider = AsyncMock(side_effect=TutorUnavailable('provider'))
    monkeypatch.setattr(quiz, '_generate', provider)
    request = quiz.VariantRequest(owner='review-fixture', problemText=source)
    result = await quiz.generate(request)
    assert result['review'] is True and result['answer'] == '5'
    assert quiz._active_variants == 0
    provider.assert_awaited_once()
    monkeypatch.setattr(quiz, '_active_variants', 2)
    result = await quiz.generate(request)
    assert result['review'] is True and result['answer'] == '5'
    provider.assert_awaited_once()


@pytest.mark.asyncio
async def test_invalid_original_options_are_not_discarded_to_force_success(monkeypatch):
    monkeypatch.setattr(quiz.catalog, 'load_plan', lambda request: None)
    monkeypatch.setattr(quiz.plan_preparation, 'prepared_plan', AsyncMock(return_value=None))
    source = 'Tính: 20 / 4 A. 2 B. 3 C. 6 D. 7'
    with pytest.raises(TutorUnavailable):
        await quiz.generate(quiz.VariantRequest(owner='source-owner', problemText=source))


@pytest.mark.asyncio
async def test_variant_endpoint_requires_the_internal_credential():
    from app.main import app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        response = await client.post('/internal/v1/tutor/quiz/variant', json={'owner': 'owner', 'problemText': 'Tính: 1 + 1'})
    assert response.status_code == 401

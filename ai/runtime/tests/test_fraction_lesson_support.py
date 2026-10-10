"""Exact fractions and teaching guards using test-only provider responses."""
import re
from unittest.mock import AsyncMock
import pytest
from app.tutoring import lesson
from app.tutoring.lesson import LessonRequest, TurnRequest, start_lesson, answer_lesson
from app.tutoring.service import TutorUnavailable
from _lesson_test_data import step, garden_candidate, mock_generation

def garden(a='1', b='3', c='2', d='5', count='16'):
    return (f'Vườn cây nhà bác Nam có {a}/{b} số cây là cây táo, {c}/{d} số cây là cây xoài, còn lại là cây cam. '
            f'Biết rằng số cây cam có trong vườn là {count} cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây? (2 điểm)')

def turn(response, answer='', hint=False):
    return answer_lesson(TurnRequest(owner='child', sessionId=response.sessionId, revision=response.revision, answer=answer, hint=hint))


@pytest.mark.asyncio
@pytest.mark.parametrize('written,feedback', [
    ('1/3 + 2/5 = 11/15 (số cây)', 'khớp với kết quả'),
    ('(1)/(3) + (2)/(5) = (5)/(15) + (6)/(15) = (11)/(15)', 'khớp với kết quả'),
    ('1/3 + 2/5 = 5/15 + 5/15 = 11/15', 'trong ảnh chưa khớp'),
    ('1/3 + 2/5 = 10/15', 'trong ảnh chưa khớp'),
    ('1/3 + 1/3 = 2/3', 'khác với giá trị cần tìm'),
    ('1/3 + 2/5 = 11/15abc', 'Đúng bước này rồi'),
])
async def test_visible_fraction_work_is_checked_exactly_without_partial_results(monkeypatch, written, feedback):
    work = 'Phần cây táo và xoài là:\n' + written
    candidate = garden_candidate()
    candidate['steps'][0]['workExcerpt'] = work
    mock_generation(monkeypatch, candidate)
    value = await start_lesson(LessonRequest(owner='child', problemText=garden(),
        workText=work, problemConfirmed=True, workConfirmed=True))
    value = turn(value, '11/15')
    assert feedback in value.feedback
    assert value.completed[0].answer == '11/15'
    if written == '1/3 + 2/5 = 11/15 (số cây)':
        assert "ghi 'phần'" in value.feedback and 'chưa phải số lượng' in value.feedback


@pytest.mark.parametrize('unit', ['cây', 'số cây', 'cuốn sách'])
def test_fraction_share_must_not_inherit_an_item_count_unit(unit):
    plan=garden_candidate()
    plan['steps'][0].update(title='Tìm phân số chỉ phần đã biết',unit=unit,
        solutionSentence='Phân số chỉ phần cây táo và xoài là:')
    with pytest.raises(ValueError,match='dimensionless'):
        lesson.validate_plan(lesson.Plan.model_validate(plan),
            LessonRequest(owner='child',problemText=garden(),problemConfirmed=True))


def test_fractional_physical_quantity_can_keep_its_real_unit():
    plan=dict(topic='Cộng độ dài',goal='Tìm tổng chiều dài.',finalAnswerStep=1,steps=[
        step(title='Chọn phép tính',choices=['Cộng hai độ dài','Trừ hai độ dài'],correctChoice='Cộng hai độ dài'),
        step(title='Tính tổng hai độ dài viết bằng phân số',expression='1/3+2/5',unit='m',
             solutionSentence='Tổng chiều dài hai dây là:')])
    lesson.validate_plan(lesson.Plan.model_validate(plan),LessonRequest(owner='child',
        problemText='Dây thứ nhất dài 1/3 m, dây thứ hai dài 2/5 m. Tính tổng chiều dài hai dây.',problemConfirmed=True))


@pytest.mark.parametrize('expression', ['16*15/4', '16 * 15 / 4', '16*(15/4)', '16/(4/15)'])
def test_checked_prior_fraction_can_be_reused_in_an_equivalent_reciprocal_formula(expression):
    plan=dict(topic='Tìm toàn bộ',goal='Tìm số cây cả vườn.',finalAnswerStep=1,steps=[
        step(title='Tìm phần cây cam',expression='1-1/3-2/5',unit='phần'),
        step(title='Tìm số cây cả vườn',expression=expression,unit='cây')])
    value=lesson.Plan.model_validate(plan)
    lesson.validate_plan(value,LessonRequest(owner='child',problemText=garden(),problemConfirmed=True))
    assert '{s0}' in value.steps[1].expression
    assert lesson.calculate_exact(lesson.expression_at(value.steps[1],['4/15']))==60

@pytest.mark.asyncio
@pytest.mark.parametrize('source,answers', [
    (garden(), ['11/15', '4/15', '60']),
    (garden('1','4','1','2','12'), ['3/4','1/4','48']),
    (garden('2','7','1','3','24'), ['13/21','8/21','63']),
])
async def test_fraction_whole_is_built_from_actual_givens_one_small_step_at_a_time(monkeypatch, source, answers):
    values = re.findall(r'\d+', source)[:5]
    cloud = mock_generation(monkeypatch, garden_candidate(*values))
    result = await start_lesson(LessonRequest(owner='child', problemText=source, problemConfirmed=True))
    assert len(result.outline) == 3
    assert result.conclusion == ''
    for index, answer in enumerate(answers):
        assert result.stepIndex == index
        assert 'correctChoice' not in result.model_dump_json()
        assert not re.search(r'(?<!\d)' + answers[-1] + r'(?!\d)', result.model_dump_json(exclude={'sessionId'}))
        first = turn(result, hint=True); second = turn(first, hint=True)
        assert first.feedback != second.feedback
        assert first.stepIndex == second.stepIndex == index and first.revision == second.revision == index
        assert turn(second, '999').status == 'TRY_AGAIN'
        result = turn(second, answer)
    assert result.status == 'COMPLETE' and result.completed[-1].answer == answers[-1]
    assert result.conclusion == f'Đáp số: {answers[-1]} cây.'
    assert all(item.solutionSentence.endswith('là:') for item in result.completed)
    assert result.completed[0].calculationDetails
    assert cloud.await_count == 2

@pytest.mark.asyncio
async def test_fraction_answers_remain_exact_across_steps_and_invalid_inputs_do_not_advance(monkeypatch):
    plan = dict(topic='Tìm phần còn lại', goal='Giữ phân số để tính chính xác.', finalAnswerStep=1, steps=[
        step(title='Tính phần còn lại', explanation='Cả hình là một đơn vị. Bớt hai phần đã biết.', question='Còn lại bao nhiêu phần?', expression='1-1/3-2/5',
             hints=['Quy đồng hai phân số trước khi trừ.', 'Trừ các tử sau khi đưa về cùng mẫu; giữ mẫu chung.']),
        step(title='Tìm cả hình', explanation='Chia lượng đã biết cho phần tương ứng.', question='Cả hình có bao nhiêu?', expression='16/{s0}'),
    ])
    mock_generation(monkeypatch, plan)
    result = await start_lesson(LessonRequest(owner='child', problemText='Cho 1/3 và 2/5, còn lại 16. Tìm cả hình.', problemConfirmed=True))
    assert '1/3' in result.step.expression and '÷' not in result.step.expression
    for bad in ['0.26', '0.266667', '4/0', '4/15 = 1', 'NaN', '4/15 cây']:
        assert turn(result, bad).status == 'TRY_AGAIN'
    result = turn(result, '8/30')
    assert result.completed[0].answer == '4/15' and result.step.expression == '16 ÷ (4/15)'
    result = turn(result, '60')
    assert result.status == 'COMPLETE'

@pytest.mark.asyncio
async def test_generated_hint_cannot_leak_an_unearned_computed_answer(monkeypatch):
    plan = dict(topic='Thêm bút', goal='Gộp hai nhóm.', steps=[
        step(title='Chọn phép tính', explanation='Được cho thêm thì số bút tăng.', question='Chọn cách nào?', choices=['Cộng','Trừ'], correctChoice='Cộng'),
        step(title='Tính', explanation='Gộp hai nhóm.', question='Có bao nhiêu bút?', expression='12+5', hints=['Kết quả là 17.']),
    ])
    monkeypatch.setattr(lesson, '_generate', AsyncMock(return_value=plan))
    with pytest.raises(TutorUnavailable):
        await start_lesson(LessonRequest(owner='child', problemText='Lan có 12 bút, thêm 5 bút. Hỏi có tất cả bao nhiêu bút?', problemConfirmed=True))


@pytest.mark.asyncio
async def test_fraction_help_explains_equal_parts_without_disclosing_the_current_result(monkeypatch):
    mock_generation(monkeypatch, garden_candidate())
    response = await start_lesson(LessonRequest(owner='child', problemText=garden(), problemConfirmed=True))
    response = turn(turn(response, hint=True), hint=True)
    assert 'tử số tính 1 × 5' in response.feedback and 'mẫu số tính 3 × 5' in response.feedback
    assert '11/15' not in response.feedback and not response.completed
    response = turn(response, '11/15')
    assert response.completed[0].calculationDetails[-1] == '5/15 + 6/15 = 11/15'
    assert 'nhân cả tử và mẫu với 5' in response.completed[0].calculationDetails[0]
    response = turn(turn(response, hint=True), hint=True)
    assert '15/15 − 11/15' in response.feedback and '4/15' not in response.feedback
    response = turn(response, '4/15')
    assert response.completed[-1].calculationDetails == [
        '1 = 15/15 (viết số nguyên thành phân số cùng mẫu).', '15/15 − 11/15 = 4/15']
    response = turn(turn(response, hint=True), hint=True)
    assert '(16 ÷ 4) × 15' in response.feedback and '60' not in response.feedback
    assert turn(response, '0.26').status == 'TRY_AGAIN'
    response = turn(response, '60')
    assert response.completed[-1].calculationDetails == ['(16 ÷ 4) × 15 = 60']


@pytest.mark.asyncio
@pytest.mark.parametrize('source,combined,remaining,total', [
    (garden(), '11/15', '4/15', '60'),
    (garden('1','4','1','2','12'), '3/4', '1/4', '48'),
    (garden('2','7','1','3','24'), '13/21', '8/21', '63'),
])
async def test_teaching_breaks_each_solution_step_into_grounded_actions(monkeypatch, source, combined, remaining, total):
    mock_generation(monkeypatch, garden_candidate(*re.findall(r'\d+', source)[:5]))
    response = await start_lesson(LessonRequest(owner='child', problemText=source, problemConfirmed=True))
    assert len(response.step.guidance) >= 3
    assert combined not in '\n'.join(response.step.guidance)
    assert not response.completed
    assert turn(response, '999').step.guidance == response.step.guidance
    response = turn(response, combined)
    assert len(response.step.guidance) >= 3
    assert combined in response.step.guidance[0]
    assert remaining not in '\n'.join(response.step.guidance)
    response = turn(response, remaining)
    assert len(response.step.guidance) >= 3
    numerator, denominator = remaining.split('/')
    assert f'chia cho {numerator}' in response.step.guidance[1]
    assert f'nhân với {denominator}' in response.step.guidance[1]
    assert total not in '\n'.join(response.step.guidance)
    assert not any('{' in item for item in response.step.guidance)
    response = turn(response, total)
    assert response.status == 'COMPLETE'
    assert [len(item.guidance) for item in response.completed] == [3, 3, 3]


@pytest.mark.asyncio
@pytest.mark.parametrize('guidance', [
    ['Kết quả là 17.'], ['{s1}'], ['{s0}'], ['{s0_secret}'],
    ['https://example.com'], ['localhost'], [' '], ['x' * 501], ['Ý'] * 7,
])
async def test_generated_teaching_cannot_leak_results_or_unchecked_references(monkeypatch, guidance):
    plan = dict(topic='Thêm bút', goal='Gộp hai nhóm.', steps=[
        step(title='Chọn cách', explanation='Gộp hai nhóm.', question='Gộp hay bớt?', choices=['Gộp','Bớt'], correctChoice='Gộp'),
        step(title='Tìm số bút', explanation='Gộp hai nhóm.', question='Có bao nhiêu bút?', expression='12+5', guidance=guidance),
    ])
    monkeypatch.setattr(lesson, '_generate', AsyncMock(return_value=plan))
    with pytest.raises(TutorUnavailable):
        await start_lesson(LessonRequest(owner='child', problemText='Lan có 12 bút, thêm 5 bút. Hỏi có tất cả bao nhiêu bút?', problemConfirmed=True))


@pytest.mark.asyncio
@pytest.mark.parametrize('field,value', [('solutionSentence','Le résultat est 17.'), ('finalAnswerStep',4)])
async def test_new_generated_solution_fields_are_validated(monkeypatch, field, value):
    plan = dict(topic='Gộp bút', goal='Tìm số bút.', steps=[
        step(title='Chọn cách', explanation='Gộp hai nhóm.', question='Gộp hay bớt?', choices=['Gộp','Bớt'], correctChoice='Gộp'),
        step(title='Tìm số bút', explanation='Gộp hai nhóm.', question='Có bao nhiêu bút?', expression='12+5')])
    if field == 'solutionSentence': plan['steps'][1][field] = value
    else: plan[field] = value
    monkeypatch.setattr(lesson, '_generate', AsyncMock(return_value=plan))
    with pytest.raises(TutorUnavailable):
        await start_lesson(LessonRequest(owner='child', problemText='Lan có 12 bút, thêm 5 bút. Hỏi có bao nhiêu bút?', problemConfirmed=True))

@pytest.mark.asyncio
async def test_ordinary_division_also_rejects_rounded_values(monkeypatch):
    candidate = dict(topic='Chia đều', goal='Giữ kết quả chính xác.', finalAnswerStep=1, steps=[
        step(title='Chọn cách chia', choices=['Chia đều', 'Gộp lại'], correctChoice='Chia đều'),
        step(title='Tính lượng trong một phần', expression='1/3'),
    ])
    mock_generation(monkeypatch, candidate)
    response = await start_lesson(LessonRequest(owner='child', problemText='Tính 1 : 3.', problemConfirmed=True))
    response = turn(response, 'Chia đều')
    assert turn(response, '0.333333').status == 'TRY_AGAIN'
    assert turn(response, '1/3').status == 'COMPLETE'


def test_exact_decimal_literals_and_fraction_division_presentation():
    from fractions import Fraction
    assert lesson.calculate_exact('999999999999.12345678') == Fraction('999999999999.12345678')
    assert lesson.display_expression('(2/3)/(4/5)', True) == '(2/3) ÷ (4/5)'
    assert lesson.display_expression('(1+2)/(3+4)', True) == '(1 + 2) ÷ (3 + 4)'
    assert lesson.display_expression('1/3/2/5', True) == '1 ÷ 3 ÷ 2 ÷ 5'
    assert lesson.display_expression('(-1)/12', True) == ' − 1/12'

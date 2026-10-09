"""Exact answers, progressive help and varied source quantities, without cloud."""
import re
from unittest.mock import AsyncMock
import pytest
from app.tutoring import lesson
from app.tutoring.lesson import LessonRequest, TurnRequest, start_lesson, answer_lesson
from app.tutoring.service import TutorUnavailable

def garden(a='1', b='3', c='2', d='5', count='16'):
    return (f'Vườn cây nhà bác Nam có {a}/{b} số cây là cây táo, {c}/{d} số cây là cây xoài, còn lại là cây cam. '
            f'Biết rằng số cây cam có trong vườn là {count} cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây? (2 điểm)')

def turn(response, answer='', hint=False):
    return answer_lesson(TurnRequest(owner='child', sessionId=response.sessionId, revision=response.revision, answer=answer, hint=hint))

@pytest.mark.asyncio
@pytest.mark.parametrize('source,answers', [
    (garden(), ['15', '5', '6', '4', '4', '60']),
    (garden('1','4','1','2','12'), ['8','2','4','2','6','48']),
    (garden('2','7','1','3','24'), ['21','6','7','8','3','63']),
])
async def test_fraction_whole_is_built_from_actual_givens_one_small_step_at_a_time(monkeypatch, source, answers):
    cloud = AsyncMock(side_effect=AssertionError('Supported text needs no provider'))
    monkeypatch.setattr(lesson, '_generate', cloud)
    result = await start_lesson(LessonRequest(owner='child', problemText=source, problemConfirmed=True))
    assert len(result.outline) == 6
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
    cloud.assert_not_called()

@pytest.mark.asyncio
async def test_fraction_answers_remain_exact_across_steps_and_invalid_inputs_do_not_advance(monkeypatch):
    plan = dict(topic='Tìm phần còn lại', goal='Giữ phân số để tính chính xác.', steps=[
        dict(title='Tính phần còn lại', explanation='Cả hình là một đơn vị. Bớt hai phần đã biết.', question='Còn lại bao nhiêu phần?', expression='1-1/3-2/5',
             hints=['Quy đồng hai phân số trước khi trừ.', 'Trừ các tử sau khi đưa về cùng mẫu; giữ mẫu chung.']),
        dict(title='Tìm cả hình', explanation='Chia lượng đã biết cho phần tương ứng.', question='Cả hình có bao nhiêu?', expression='16/{s0}'),
    ])
    monkeypatch.setattr(lesson, '_generate', AsyncMock(return_value=plan))
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
        dict(title='Chọn phép tính', explanation='Được cho thêm thì số bút tăng.', question='Chọn cách nào?', choices=['Cộng','Trừ'], correctChoice='Cộng'),
        dict(title='Tính', explanation='Gộp hai nhóm.', question='Có bao nhiêu bút?', expression='12+5', hints=['Kết quả là 17.']),
    ])
    monkeypatch.setattr(lesson, '_generate', AsyncMock(return_value=plan))
    with pytest.raises(TutorUnavailable):
        await start_lesson(LessonRequest(owner='child', problemText='Lan có 12 bút, thêm 5 bút. Hỏi có tất cả bao nhiêu bút?', problemConfirmed=True))

@pytest.mark.parametrize('source', [garden('1','0'), garden('4','3'), garden(count='17'), garden()+' Tìm thêm số cây táo.', garden().replace('cây cam có trong vườn', 'cây táo có trong vườn')])
def test_partial_contradictory_or_different_goals_do_not_use_the_garden_template(source):
    assert lesson.fraction_garden_plan(source) is None


@pytest.mark.asyncio
@pytest.mark.parametrize('source,answers', [
    ('Tính 1/3 + 2/5.', ['15','5','6','11','11/15']),
    ('Tính 5/6 − 1/4.', ['24','20','6','14','7/12']),
    ('Tính 2/3 − 3/4.', ['12','8','9','-1','-1/12']),
    ('Tính 2/3 × 3/4.', ['6','12','1/2']),
    ('Tính 2/3 : 4/5.', ['10','12','5/6']),
    ('Tính 3/4 ÷ 2/7.', ['21','8','21/8']),
    ('Tính 0/3 + 2/5.', ['15','0','6','6','2/5']),
])
async def test_varied_fraction_operations_teach_the_actual_givens_without_cloud(monkeypatch, source, answers):
    cloud = AsyncMock(side_effect=AssertionError('No image-specific answer or cloud'))
    monkeypatch.setattr(lesson, '_generate', cloud)
    response = await start_lesson(LessonRequest(owner='child', problemText=source, problemConfirmed=True))
    assert len(response.outline) == len(answers)
    for index, value in enumerate(answers):
        first = turn(response, hint=True); second = turn(first, hint=True)
        assert first.feedback != second.feedback and second.stepIndex == index
        assert turn(second, '999').stepIndex == index
        response = turn(second, value)
    assert response.status == 'COMPLETE'
    assert response.completed[-1].answer == answers[-1]
    cloud.assert_not_called()


@pytest.mark.asyncio
async def test_ordinary_division_also_rejects_rounded_values(monkeypatch):
    monkeypatch.setattr(lesson, '_generate', AsyncMock(side_effect=AssertionError('No cloud')))
    response = await start_lesson(LessonRequest(owner='child', problemText='Tính 1 : 3.', problemConfirmed=True))
    response = turn(response, 'Nhân, chia trước; cộng, trừ sau')
    assert turn(response, '0.333333').status == 'TRY_AGAIN'
    assert turn(response, '1/3').status == 'COMPLETE'


def test_exact_decimal_literals_and_fraction_division_presentation():
    from fractions import Fraction
    assert lesson.calculate_exact('999999999999.12345678') == Fraction('999999999999.12345678')
    assert lesson.display_expression('(2/3)/(4/5)', True) == '(2/3) ÷ (4/5)'
    assert lesson.display_expression('(1+2)/(3+4)', True) == '(1 + 2) ÷ (3 + 4)'
    assert lesson.display_expression('1/3/2/5', True) == '1 ÷ 3 ÷ 2 ÷ 5'
    assert lesson.display_expression('(-1)/12', True) == ' − 1/12'

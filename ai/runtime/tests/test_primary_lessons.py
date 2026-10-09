import re
import json
from unittest.mock import AsyncMock
import pytest
from app.tutoring import lesson
from app.tutoring.lesson import LessonRequest, TurnRequest, primary_plan, start_lesson, answer_lesson
from app.tutoring.service import TutorUnavailable

@pytest.mark.asyncio
@pytest.mark.parametrize('digit,difference,parts,total,number', [('6','537','9','531','59'), ('4','112','9','108','12'), ('0','729','9','729','81')])
async def test_append_digit_guides_the_actual_problem_without_cloud_or_future_answers(monkeypatch,digit,difference,parts,total,number):
    cloud=AsyncMock(side_effect=AssertionError('No provider needed for supported problem'))
    monkeypatch.setattr(lesson,'_generate',cloud)
    problem=f'Tìm một số biết rằng nếu viết thêm chữ số {digit} vào bên phải số đó ta được số mới lớn hơn số phải tìm {difference} đơn vị.'
    result=await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='pupil',problemText=problem))
    assert len(result.outline)==5
    assert not re.search(r'(?<!\d)' + number + r'(?!\d)', result.model_dump_json(exclude={'sessionId'}))
    for answer in ['Gấp lên rồi cộng chữ số mới',parts,total]:
        result=answer_lesson(TurnRequest(owner='pupil',sessionId=result.sessionId,revision=result.revision,answer=answer))
    assert result.stepIndex==3
    wrong=answer_lesson(TurnRequest(owner='pupil',sessionId=result.sessionId,revision=result.revision,answer=str(int(number)+1)))
    assert wrong.status=='TRY_AGAIN' and wrong.stepIndex==3
    assert not re.search(r'(?<!\d)' + number + r'(?!\d)', wrong.model_dump_json(exclude={'sessionId'}))
    for answer in [number,difference]:
        result=answer_lesson(TurnRequest(owner='pupil',sessionId=result.sessionId,revision=result.revision,answer=answer))
    assert result.status=='COMPLETE'
    assert result.completed[3].answer==number
    cloud.assert_not_called()

@pytest.mark.asyncio
@pytest.mark.parametrize('problem,answers', [
 ('Tổng hai số là 70, hiệu hai số là 10. Tìm hai số đó.', ['Bớt phần hiệu','30','40','70']),
 ('Tổng hai số là 49, tỉ số hai số là 2/5. Tìm hai số đó.', ['Có cùng giá trị','7','7','14','35']),
])
async def test_equal_part_lessons_use_given_numbers_and_check_each_step(monkeypatch,problem,answers):
    cloud=AsyncMock(side_effect=AssertionError('No cloud'))
    monkeypatch.setattr(lesson,'_generate',cloud)
    result=await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='pupil',problemText=problem))
    for answer in answers:
        result=answer_lesson(TurnRequest(owner='pupil',sessionId=result.sessionId,revision=result.revision,answer=answer))
    assert result.status=='COMPLETE'
    cloud.assert_not_called()

@pytest.mark.parametrize('problem', [
 'Tìm một số viết thêm chữ số 6 vào bên trái, số mới lớn hơn số đó 537 đơn vị.',
 'Tìm một số viết thêm chữ số 6 vào bên phải, số mới lớn hơn số đó 538 đơn vị.',
 'Tìm một số viết thêm chữ số 6 vào bên phải, số mới lớn hơn số đó 537 đơn vị. Sau đó nhân với 3.',
 'Tổng hai số là 70. Tìm hai số.',
 'Tổng hai số là 10, hiệu hai số là 70. Tìm hai số.',
 'Tổng hai số là 49, tỉ số hai số là 2/0. Tìm hai số.',
])
def test_incomplete_ambiguous_or_inconsistent_statements_never_select_a_local_answer(problem):
    assert primary_plan(problem) is None

@pytest.mark.asyncio
@pytest.mark.parametrize('problem,choice,answer', [
 ('Hình chữ nhật có chiều dài là 12 cm, chiều rộng là 5 cm. Tính diện tích hình chữ nhật.', 'Nhân chiều dài với chiều rộng','60'),
 ('Hình chữ nhật có chiều dài là 12 cm, chiều rộng là 5 cm. Tính chu vi hình chữ nhật.', 'Độ dài đường bao quanh','34'),
 ('Hình tam giác có đáy là 15 cm, chiều cao là 12 cm. Tính diện tích.', 'Đáy nhân chiều cao, rồi chia đôi','90'),
])
async def test_primary_geometry_and_expressions_are_grounded_without_provider(monkeypatch,problem,choice,answer):
    monkeypatch.setattr(lesson,'_generate',AsyncMock(side_effect=AssertionError('No cloud')))
    result=await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='pupil',problemText=problem))
    for value in [choice,answer]:
        result=answer_lesson(TurnRequest(owner='pupil',sessionId=result.sessionId,revision=result.revision,answer=value))
    assert result.status=='COMPLETE'


@pytest.mark.asyncio
@pytest.mark.parametrize('source,choice,answers', [
 ('Tính (18 + 6) : 3.', 'Làm trong ngoặc trước', ['24', '8']),
 ('Tính 8 + 6 × 3 − 4.', 'Nhân, chia trước; cộng, trừ sau', ['18', '26', '22']),
 ('Tính (12 − 8) × (9 + 3).', 'Làm trong ngoặc trước', ['4', '12', '48']),
 ('Tính 24 : 3 : 2.', 'Nhân, chia trước; cộng, trừ sau', ['8', '4']),
])
async def test_expression_is_taught_one_actual_operation_at_a_time(monkeypatch, source, choice, answers):
    cloud = AsyncMock(side_effect=AssertionError('Source operations are locally grounded'))
    monkeypatch.setattr(lesson, '_generate', cloud)
    response = await start_lesson(LessonRequest(owner='pupil', problemText=source, problemConfirmed=True))
    for value in [choice, *answers]:
        response = answer_lesson(TurnRequest(owner='pupil', sessionId=response.sessionId, revision=response.revision, answer=value))
    assert response.status == 'COMPLETE'
    assert [item.answer for item in response.completed[1:]] == answers
    cloud.assert_not_called()


@pytest.mark.parametrize('problem', [
 'Tổng hai số là 70. Hiệu hai số là 10. Tìm tích của hai số.',
 'Tổng hai số là 70. Hiệu hai số là 10. Tìm thương của hai số.',
 'Tổng hai số là 70. Hiệu hai số là 10. Tìm hai số đó rồi tính tích của chúng.',
 'Tổng hai số là 49. Tỉ số hai số là 2/5. Tìm tích của hai số.',
 'Tổng hai số là 49. Tỉ số hai số là 2/5. Tìm hai số đó. Tính tích của chúng.',
 'Hình chữ nhật có chiều dài là 8 cm, chiều rộng là 5 cm. Tính diện tích và chu vi hình chữ nhật.',
 'Hình chữ nhật có chiều dài là 8 cm, chiều rộng là 5 cm. Tính chu vi và diện tích hình chữ nhật.',
 'Hình chữ nhật có chiều dài là 8 cm, chiều rộng là 5 cm. Tính diện tích hình chữ nhật. Tính chu vi của hình.',
])
def test_other_or_compound_goals_never_finish_an_unrelated_local_lesson(problem):
    assert primary_plan(problem) is None


@pytest.mark.asyncio
@pytest.mark.parametrize('problem,steps,answers', [
 ('Tổng hai số là 70. Hiệu hai số là 10. Tìm tích của hai số.', [
     dict(title='Tìm số bé', expression='(70-10)/2'),
     dict(title='Tìm số lớn', expression='{s0}+10'),
     dict(title='Tìm tích', expression='{s0}*{s1}'),
 ], ['30', '40', '1200']),
 ('Hình chữ nhật có chiều dài là 8 cm, chiều rộng là 5 cm. Tính diện tích và chu vi hình chữ nhật.', [
     dict(title='Tính diện tích', expression='8*5', unit='cm²'),
     dict(title='Tính chu vi', expression='(8+5)*2', unit='cm'),
 ], ['40', '26']),
])
async def test_deferred_goal_reaches_broader_tutor_unchanged_and_checks_its_full_plan(monkeypatch, problem, steps, answers):
    plan = dict(topic='Giải đúng yêu cầu của đề', goal='Tìm đủ các đại lượng đề yêu cầu.', steps=[
        dict(explanation='Dùng dữ kiện và kết quả bước trước để tính đại lượng cần tìm.',
             question='Em tính đại lượng ở bước này được bao nhiêu?', **step) for step in steps
    ])
    cloud = AsyncMock(return_value=plan)
    monkeypatch.setattr(lesson, '_generate', cloud)
    result = await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='pupil', problemText=problem))
    cloud.assert_awaited_once()
    assert json.loads(cloud.await_args.args[1])['problemText'] == problem
    assert result.outline == [step['title'] for step in steps]
    for value in answers:
        result = answer_lesson(TurnRequest(owner='pupil', sessionId=result.sessionId, revision=result.revision, answer=value))
    assert result.status == 'COMPLETE'
    assert [step.answer for step in result.completed] == answers


@pytest.mark.asyncio
@pytest.mark.parametrize('problem', [
 'Tìm số mới biết rằng nếu viết thêm chữ số 6 vào bên phải số ban đầu ta được số mới lớn hơn số ban đầu 537 đơn vị.',
 'Tìm một số mới biết rằng nếu viết thêm chữ số 6 vào bên phải số ban đầu ta được số mới lớn hơn số ban đầu 537 đơn vị.',
 'Tìm một số và số mới biết rằng nếu viết thêm chữ số 6 vào bên phải số đó ta được số mới lớn hơn số phải tìm 537 đơn vị.',
 'Tìm một số biết rằng nếu viết thêm chữ số 6 vào bên phải số đó ta được số mới lớn hơn số phải tìm 537 đơn vị. Rồi tìm tổng số ban đầu và số mới.',
 'Cho hình thang ABCD có đáy AB = 8 cm, đáy CD = 15 cm và diện tích hình tam giác ACD là 90 cm². Tính diện tích và chu vi hình thang ABCD.',
 'Cho hình thang ABCD có đáy AB = 8 cm, đáy CD = 15 cm và diện tích hình tam giác ACD là 90 cm². Tính tổng diện tích hình thang ABCD và tam giác ACD.',
])
async def test_every_local_template_defers_different_or_compound_goals_without_guessing(monkeypatch, problem):
    cloud = AsyncMock(return_value={'unavailable': True})
    monkeypatch.setattr(lesson, '_generate', cloud)
    with pytest.raises(TutorUnavailable):
        await start_lesson(LessonRequest(problemConfirmed=True, workConfirmed=True, owner='pupil', problemText=problem))
    cloud.assert_awaited_once()
    assert json.loads(cloud.await_args.args[1])['problemText'] == problem

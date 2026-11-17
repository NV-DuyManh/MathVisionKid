"""Student discovery: exact checking, contextual feedback and no answer-bearing hints."""
from collections import OrderedDict
from unittest.mock import AsyncMock

import pytest

from app.tutoring import lesson
from app.tutoring.fraction_remainder import verified_plan


ORCHARD = ('Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. '
           'Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?')


def turn(response, answer='', hint=False):
    return lesson.answer_lesson(lesson.TurnRequest(owner='pedagogy-child', sessionId=response.sessionId,
        revision=response.revision, answer=answer, hint=hint))


@pytest.fixture(autouse=True)
def isolated_sessions(monkeypatch):
    monkeypatch.setattr(lesson, '_sessions', OrderedDict())


@pytest.mark.asyncio
@pytest.mark.parametrize('source', [ORCHARD, 'Bài 6\n' + ORCHARD + ' (2 điểm)'])
async def test_orchard_reading_to_exact_conclusion_does_not_solve_through_hints(monkeypatch, source):
    cloud = AsyncMock(side_effect=AssertionError('Verified relation must remain offline'))
    monkeypatch.setattr(lesson, '_generate', cloud)
    response = await lesson.start_lesson(lesson.LessonRequest(owner='pedagogy-child', problemText=source,
        problemConfirmed=True, guidedUnderstanding=True))
    assert response.understandingSteps == 3 and len(response.outline) == 5
    session = lesson._sessions[response.sessionId]
    assert response.step.choiceChecks == [] and 'correctChoice' not in response.model_dump_json()
    assert session.problem_text == source
    assert all('điểm' not in item.question and 'Bài 6' not in item.correctChoice for item in session.plan.steps[:3])
    for _ in range(3):
        step = session.plan.steps[response.stepIndex]
        wrong_choice = next(value for value in step.choices if value != step.correctChoice)
        rejected = turn(response, wrong_choice)
        assert rejected.status == 'TRY_AGAIN'
        assert rejected.revision == response.revision and rejected.completed == response.completed
        assert wrong_choice in rejected.feedback or 'dữ kiện' in rejected.feedback
        response = turn(rejected, step.correctChoice)
        assert response.feedback and '4/15' not in response.model_dump_json(exclude={'sessionId'})
        assert '60' not in response.model_dump_json(exclude={'sessionId'})
    assert response.step.expression == '' and response.step.answerFormat == 'FRACTION'
    assert response.hintLevel == 0 and response.hintCount == 2
    assert 'cây cam' in response.step.title and 'cây cam' in response.step.question
    assert 'cây táo' in response.step.explanation and 'cây xoài' in response.step.explanation
    assert response.summary.question == 'Tìm tổng số cây trong vườn cây nhà bác Nam.'
    assert set(response.summary.givens + [response.summary.question, 'Đề bài đã cho.', 'Điều cần tìm.']) <= set(session.narration_texts)
    assert response.step.guidance == [] and response.step.solutionSentence == ''
    for level in (1, 2, 3):
        response = turn(response, hint=True)
        assert response.hintLevel == min(level, 2)
        assert response.stepIndex == 3 and response.revision == 3
        assert response.step.expression == ('1 − (1/3 + 2/5)' if level >= 2 else '')
        shown = response.model_dump_json(exclude={'sessionId'})
        assert '4/15' not in shown and '60' not in shown
    assert len(set(response.revealedHints)) == 2 and 'đã xem hết' in response.feedback
    assert 'quy đồng' in response.revealedHints[1] and 'cùng kích thước' in response.revealedHints[1]
    assert 'cây cam' in response.revealedHints[1] and '=' not in response.revealedHints[1]
    assert lesson.present(response.sessionId, session).revealedHints == response.revealedHints
    wrong = turn(response, '1/2')
    assert wrong.status == 'TRY_AGAIN' and wrong.revision == 3
    assert 'cùng mẫu số' in wrong.feedback and '4/15' not in wrong.feedback
    zero = turn(wrong, '4/0')
    assert 'Mẫu số không thể bằng 0' in zero.feedback
    response = turn(zero, '8/30')
    assert response.completed[-1].answer == '4/15'
    assert 'cây cam' in response.completed[-1].solutionSentence and not response.completed[-1].unit
    assert 'tổng số cây' in response.step.title.lower() and '16 cây' in response.step.explanation
    assert '4/15' in response.feedback and '60' not in response.model_dump_json(exclude={'sessionId'})
    assert response.step.expression == '' and response.step.answerFormat == 'INTEGER'
    assert response.hintLevel == 0 and response.revealedHints == []
    assert response.completed[-1].calculationDetails[-1] == '15/15 − 11/15 = 4/15'
    for _ in range(2):
        response = turn(response, hint=True)
        assert '60' not in response.model_dump_json(exclude={'sessionId'})
    assert response.step.expression == '16 ÷ 4/15'
    assert 'phân số đảo ngược' in response.feedback and 'sáu mươi' not in response.feedback
    response = turn(response, '60')
    assert response.status == 'COMPLETE' and response.conclusion == 'Đáp số: 60 cây.'
    assert 'Tổng số cây' in response.completed[-1].solutionSentence
    assert response.hintCount == 0 and response.hintLevel == 0
    assert '60' in response.feedback
    cloud.assert_not_awaited()


@pytest.mark.parametrize('a,b,count,remaining,total', [
    ('1/4', '2/5', 14, '7/20', 40), ('2/6', '1/6', 9, '1/2', 18),
])
@pytest.mark.asyncio
async def test_changed_shares_and_population_use_grounded_operands(monkeypatch, a, b, count, remaining, total):
    source = (f'Bạn Ngọc có một số viên bi. Trong đó, {a} số viên bi là bi đỏ, '
              f'{b} số viên bi là bi xanh, còn lại là bi vàng. Biết có {count} bi vàng. '
              'Hỏi bạn Ngọc có tất cả bao nhiêu viên bi?')
    monkeypatch.setattr(lesson, '_generate', AsyncMock(side_effect=AssertionError('No provider required')))
    response = await lesson.start_lesson(lesson.LessonRequest(owner='pedagogy-child', problemText=source, problemConfirmed=True))
    assert not response.step.expression and response.step.answerFormat == 'FRACTION'
    assert 'bi vàng' in response.step.title and 'viên bi' in response.step.question
    assert 'bi đỏ' in response.step.explanation and 'bi xanh' in response.step.explanation
    assert verified_plan(source) is not None
    for _ in range(2):
        response = turn(response, hint=True)
        assert not response.completed and response.revision == 0
        assert remaining not in response.feedback
    assert a in response.step.expression and b in response.step.expression
    response = turn(response, remaining)
    assert response.completed[0].answer == remaining
    response = turn(response, str(total))
    assert response.conclusion == f'Đáp số: {total} viên bi.'


def test_old_private_worked_hints_cannot_leak_even_when_answer_is_written_in_words():
    plan = lesson.Plan(topic='Phần còn lại', goal='Tự tính phần còn lại.', steps=[lesson.Step(
        title='Tìm phần còn lại', explanation='Kết quả là bốn phần mười lăm.',
        question='Phần còn lại bằng bao nhiêu?', expression='1-(1/3+2/5)', fractionNotation=True,
        initialGuidance=['Coi toàn bộ là một đơn vị. Cộng hai phần đã biết rồi bớt khỏi toàn bộ.'],
        guidance=['Kết quả là 4/15, đọc là bốn phần mười lăm.'],
        hints=['Kết quả là 4/15.', 'Phần còn lại bằng bốn phần mười lăm.'])])
    key = 'legacy-private-plan-regression'
    session = lesson.Session('pedagogy-child', plan, float('inf'), givens=frozenset({'1', '3', '2', '5'}))
    lesson._sessions[key] = session
    response = lesson.present(key, session)
    for reveal in (False, True, True, True):
        if reveal:
            response = turn(response, hint=True)
        shown = response.model_dump_json(exclude={'sessionId'})
        assert '4/15' not in shown and 'bốn phần mười lăm' not in shown
        assert session.answers == [] and session.revision == 0
    response = turn(response, '4/15')
    assert response.status == 'COMPLETE'
    assert 'bốn phần mười lăm' in ' '.join(response.completed[0].guidance)


@pytest.mark.parametrize('claim_index', [0, 1])
def test_true_false_feedback_explains_the_proposition_not_just_the_choice_label(monkeypatch, claim_index):
    monkeypatch.setattr(lesson.secrets, 'choice', lambda values: values[claim_index])
    source = 'Mai có 12 bút, thêm 5 bút. Hỏi Mai có tất cả bao nhiêu bút?'
    steps = lesson.source_understanding(source)
    plan = lesson.Plan(topic='Số bút', goal='Tìm số bút.', steps=steps + [lesson.Step(
        title='Tính số bút', explanation='Gộp hai nhóm bút.', question='Có tất cả bao nhiêu bút?', expression='12+5')])
    session = lesson.Session('pedagogy-child', plan, float('inf'), answers=[steps[0].correctChoice, steps[1].correctChoice],
        givens=frozenset({'12', '5'}), problem_text=source, revision=2)
    key = 'proposition-feedback-regression'
    lesson._sessions[key] = session
    response = lesson.present(key, session)
    wrong = 'Sai' if steps[2].correctChoice == 'Đúng' else 'Đúng'
    rejected = turn(response, wrong)
    assert '17' not in rejected.feedback and rejected.revision == 2
    assert 'nhầm dữ kiện với câu hỏi' in rejected.feedback
    quote = 'Mai có 12 bút' if claim_index == 0 else 'Hỏi Mai có tất cả bao nhiêu bút?'
    assert quote in rejected.feedback
    assert ('thông tin đề đã cho' if claim_index == 0 else 'thuộc phần cần tìm') in rejected.feedback
    accepted = turn(rejected, steps[2].correctChoice)
    assert accepted.revision == 3 and quote in accepted.feedback
    assert 'Em phân biệt đúng rồi' in accepted.feedback


def test_hint_does_not_remove_a_valid_operand_equal_to_the_final_answer():
    step = lesson.Step(title='Gộp nhóm', explanation='Một nhóm chưa có đồ vật.',
        question='Có tất cả bao nhiêu?', expression='4+0', hints=['Đáp số là bốn.'])
    hints = lesson.progressive_hints(step, [])
    assert lesson.expression_at(step, [], for_display=True) == '4 + 0'
    assert all('4 + 0 = 4' not in text and 'Đáp số là bốn' not in text for text in hints)


def test_checked_fraction_retains_its_type_in_a_regular_division_step():
    step = lesson.Step(title='Tìm tổng số', explanation='Tìm cả nhóm.', question='Có bao nhiêu?', expression='21/{s0}')
    assert lesson.expression_at(step, ['7/12']) == '21/(7/12)'
    assert lesson.expression_at(step, ['7/12'], for_display=True) == '21 ÷ 7/12'
    assert lesson.answer_format(step, ['7/12']) == 'INTEGER'


@pytest.mark.parametrize('expression,question,expected', [
    ('5/4', 'Em tìm được bao nhiêu?', 'DECIMAL'), ('5/7', 'Em tìm được bao nhiêu?', 'FRACTION'),
    ('6/2', 'Viết kết quả dưới dạng số thập phân.', 'DECIMAL'),
])
def test_input_format_is_independent_of_the_unopened_calculation(expression, question, expected):
    step = lesson.Step(title='Tìm kết quả', explanation='Tự tính rồi kiểm tra.', question=question, expression=expression)
    plan = lesson.Plan(topic='Tính giá trị', goal='Tự nhập kết quả.', steps=[step])
    response = lesson.present('input-format-regression', lesson.Session('pedagogy-child', plan, float('inf')))
    assert response.step.answerFormat == expected and not response.step.expression

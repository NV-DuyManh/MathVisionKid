"""Resume an owned session and check a small arithmetic transfer task. No model calls."""
import ast
import re
import time
from fractions import Fraction
from pydantic import Field
from app.tutoring import lesson
from app.tutoring.service import TutorModel


class ResumeRequest(TutorModel):
    owner: str = Field(min_length=1, max_length=200)
    sessionId: str = Field(min_length=20, max_length=100)
    problemText: str = Field(min_length=3, max_length=4000)


class CheckRequest(TutorModel):
    owner: str = Field(min_length=1, max_length=200)
    sessionId: str = Field(min_length=20, max_length=100)
    revision: int = Field(ge=0, strict=True)
    answer: str = Field(default='', max_length=30)


def resume(request: ResumeRequest):
    session = lesson._sessions.get(request.sessionId)
    if not session or session.owner != request.owner or session.expires <= time.monotonic():
        raise lesson.LessonExpired('Phiên học đã hết hạn. Đề của em vẫn được giữ.')
    if request.problemText.strip() != session.problem_text.strip():
        raise ValueError('Source changed')
    # No replay of client-provided answers or extension of session expiry.
    response=lesson.present(request.sessionId, session)
    if session.answers:
        previous=session.plan.steps[len(session.answers)-1]
        response.review=dict(question=previous.question,choices=previous.choices,studentAnswer=session.answers[-1])
    return response


def comprehension_check(request: CheckRequest):
    session = lesson._owned_turn(request)
    math_rows = [i for i,item in enumerate(session.completed) if item.kind == 'MATH' and item.expression]
    if not math_rows:
        raise ValueError('No completed calculation')
    index = math_rows[-1]
    expression = lesson.expression_at(session.plan.steps[index], session.answers[:index])
    tree = ast.parse(expression.translate(lesson._SYMBOLS), mode='eval')
    # Change one literal in the previous checked calculation. This is a separate
    # practice calculation, never a made-up fact or answer to the original problem.
    changed = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and type(node.value) is int and 0 <= node.value <= 1000:
            node.value += 1; changed = True; break
    if not changed:
        raise ValueError('No safe transfer task')
    variant = ast.unparse(tree)
    expected = lesson.calculate_exact(variant)
    checked = bool(request.answer.strip())
    correct = False
    if checked and re.fullmatch(r'-?\d{1,12}(?:[.,]\d{1,8})?(?:\s*/\s*\d{1,12})?', request.answer.strip()):
        try: correct = Fraction(request.answer.strip().replace(',', '.').replace(' ', '')) == expected
        except (ValueError, ArithmeticError): pass
    feedback = ('Đúng rồi! Em đã áp dụng được cách tính với số khác.' if correct else
                'Chưa khớp. Em làm lại cùng thứ tự tính như bước vừa học nhé.' if checked else '')
    return dict(expression=lesson.display_expression(variant, True), question='Thử cùng cách tính với một số khác nhé.',
                checked=checked, correct=correct, feedback=feedback)

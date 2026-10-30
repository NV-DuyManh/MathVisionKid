"""Tests for deterministic digit-append math tutor solver and plan verification."""
import asyncio
from unittest.mock import AsyncMock
import pytest

from app.tutoring import lesson, digit_append
from app.tutoring.lesson import LessonRequest, TurnRequest, start_lesson, answer_lesson, lesson_preparation, PreparationRequest
from app.tutoring.service import TutorUnavailable


ORIGINAL_PROMPT = "Đề: Tìm một số biết rằng nếu viết thêm chữ số 6 vào bên phải số đó ta được số mới lớn hơn số phải tìm 537 đơn vị."


def turn(response, answer="", owner="child", hint=False):
    return answer_lesson(TurnRequest(owner=owner, sessionId=response.sessionId, revision=response.revision, answer=answer, hint=hint))


def test_exact_original_digit_append_proof():
    plan_dict = digit_append.verified_plan(ORIGINAL_PROMPT)
    assert plan_dict is not None
    plan = lesson.Plan.model_validate(plan_dict)
    req = LessonRequest(owner="child", problemText=ORIGINAL_PROMPT, problemConfirmed=True)
    constants = lesson.formula_constants(ORIGINAL_PROMPT)
    lesson.validate_plan(plan, req, constants)

    answers = []
    for step in plan.steps:
        expr = lesson.expression_at(step, answers)
        ans = str(lesson.calculate_exact(expr))
        answers.append(ans)

    assert answers == ["531", "59"]
    # Mathematical proof:
    x = int(answers[1])
    assert x == 59
    new_number = x * 10 + 6
    assert new_number == 596
    assert new_number - x == 537


@pytest.mark.parametrize("source,expected_d,expected_D,expected_x", [
    ("Đề: Tìm một số biết rằng nếu viết thêm chữ số 6 vào bên phải số đó ta được số mới lớn hơn số phải tìm 537 đơn vị.", 6, 537, 59),
    ("Tìm một số tự nhiên biết rằng nếu viết thêm chữ số 8 vào bên phải số đó thì được số mới hơn số cũ 152 đơn vị.", 8, 152, 16),
    ("Tìm số tự nhiên biết rằng khi viết thêm chữ số 3 vào bên phải số đó ta được số mới lớn hơn số ban đầu 165 đơn vị.", 3, 165, 18),
    ("Tìm một số biết nếu thêm chữ số 5 vào bên phải số đó ta được số mới lớn hơn số phải tìm 230 đơn vị.", 5, 230, 25),
    ("Nếu viết thêm chữ số 2 vào bên phải một số ta được số mới lớn hơn số đó 137 đơn vị. Tìm số đó.", 2, 137, 15),
    ("Tìm một số biết rằng nếu viết thêm chữ số 0 vào bên phải số đó ta được số mới lớn hơn số phải tìm 180 đơn vị.", 0, 180, 20),
    ("Tìm số đó biết khi viết thêm chữ số 7 vào bên phải một số tự nhiên thì số mới hơn số ban đầu 340 đơn vị.", 7, 340, 37),
    ("Tìm một số tự nhiên có hai chữ số, biết rằng nếu viết thêm chữ số 9 vào bên phải số đó ta được số mới lớn hơn số phải tìm 405 đơn vị.", 9, 405, 44),
    ("Bài 2 (2 điểm): Tìm một số biết rằng nếu viết thêm chữ số 4 vào bên phải số đó ta được số mới hơn số cần tìm 211 đơn vị.", 4, 211, 23),
    ("Câu 3: Tìm một số tự nhiên biết khi thêm chữ số 1 vào bên phải số đó ta được số mới lớn hơn số cũ 370 đơn vị.", 1, 370, 41),
    ("Tìm một số biết rằng nếu viết thêm chữ số 5 vào bên phải số đó ta được số mới lớn hơn số phải tìm 1112 đơn vị.", 5, 1112, 123),
])
def test_at_least_10_different_variants_pass_validation_and_arithmetic(source, expected_d, expected_D, expected_x):
    extracted = digit_append.extract_digit_append(source)
    assert extracted is not None
    d, D, x = extracted
    assert d == expected_d
    assert D == expected_D
    assert x == expected_x

    plan_dict = digit_append.verified_plan(source)
    assert plan_dict is not None
    plan = lesson.Plan.model_validate(plan_dict)
    req = LessonRequest(owner="child", problemText=source, problemConfirmed=True)
    constants = lesson.formula_constants(source)
    lesson.validate_plan(plan, req, constants)

    answers = []
    for step in plan.steps:
        expr = lesson.expression_at(step, answers)
        answers.append(str(lesson.calculate_exact(expr)))

    assert answers[1] == str(expected_x)


@pytest.mark.parametrize("invalid_source", [
    "Tìm một số biết rằng nếu viết thêm chữ số 6 vào bên phải số đó ta được số mới lớn hơn số phải tìm 500 đơn vị.",
    "Tìm một số biết rằng nếu viết thêm số 25 vào bên phải số đó ta được số mới lớn hơn số phải tìm 2400 đơn vị.",
    "Tìm một số biết rằng nếu viết thêm chữ số 6 vào bên phải số đó ta được số mới lớn hơn số phải tìm 5 đơn vị.",
    "Tìm một số biết rằng nếu viết thêm chữ số 6 vào bên trái số đó ta được số mới lớn hơn số phải tìm 600 đơn vị.",
    "Tìm một số biết rằng bớt chữ số 6 ở hàng đơn vị thì số mới nhỏ hơn số cũ 537 đơn vị.",
    "Tìm số sách của bạn An biết rằng An có 12 quyển sách.",
])
def test_invalid_and_non_integer_cases_are_rejected(invalid_source):
    assert digit_append.verified_plan(invalid_source) is None


@pytest.mark.asyncio
async def test_full_tutor_session_with_cloud_disabled(monkeypatch):
    monkeypatch.setattr(lesson, "_generate", AsyncMock(side_effect=AssertionError("Cloud should not be called")))
    req = LessonRequest(owner="child", problemText=ORIGINAL_PROMPT, problemConfirmed=True, guidedUnderstanding=True, startWithReading=True)
    res = await start_lesson(req)
    assert res.status == "READY"
    assert res.stepIndex == 0
    assert res.step.title == "Tìm 9 lần số cần tìm"

    # Try incorrect answer
    wrong = turn(res, "500")
    assert wrong.status == "TRY_AGAIN"

    # Step 0 correct answer
    res = turn(res, "531")
    assert res.stepIndex == 1
    assert res.step.title == "Tìm số cần tìm"

    # Step 1 correct answer
    res = turn(res, "59")
    assert res.status == "COMPLETE"
    assert "59" in res.conclusion


@pytest.mark.asyncio
async def test_reading_first_then_digit_append_math(monkeypatch):
    monkeypatch.setattr(lesson, "_generate", AsyncMock(side_effect=AssertionError("Cloud should not be called")))
    source = "Nếu viết thêm chữ số 6 vào bên phải một số ta được số mới lớn hơn số đó 537 đơn vị. Tìm số đó."
    req = LessonRequest(owner="child", problemText=source, problemConfirmed=True, guidedUnderstanding=True, startWithReading=True)
    res = await start_lesson(req)
    assert res.understandingSteps == 3
    session = lesson._sessions[res.sessionId]

    for _ in range(3):
        ans = session.plan.steps[len(session.answers)].correctChoice
        res = turn(res, ans)

    if session.preparation_task:
        await session.preparation_task

    res = lesson_preparation(PreparationRequest(owner="child", sessionId=res.sessionId, revision=res.revision))
    assert res.step.kind == "MATH"
    assert res.stepIndex == 3

    # Step 3 (math 0): 531
    res = turn(res, "531")
    assert res.stepIndex == 4

    # Step 4 (math 1): 59
    res = turn(res, "59")
    assert res.status == "COMPLETE"
    assert "59" in res.conclusion


@pytest.mark.asyncio
async def test_written_work_cloud_failure_falls_back_to_exact_digit_append(monkeypatch):
    monkeypatch.setattr(lesson, "generate_plan", AsyncMock(side_effect=TutorUnavailable("RATE_LIMIT")))
    req = LessonRequest(owner="child", problemText=ORIGINAL_PROMPT, problemConfirmed=True, workText="9 lần số đó là: 537 - 6 = 531", workConfirmed=True)
    plan = await lesson.reviewed_plan(req, [])
    assert len(plan.steps) == 2
    assert str(lesson.calculate_exact(plan.steps[0].expression)) == "531"
    assert str(lesson.calculate_exact(lesson.expression_at(plan.steps[1], ["531"]))) == "59"


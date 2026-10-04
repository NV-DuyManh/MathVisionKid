import asyncio
import io
import cv2
import numpy as np
import pytest
from unittest.mock import AsyncMock

from PIL import Image

from app.tutoring import notebook
from app.tutoring.rows import handwriting_rows


def image_bytes(size=(1800, 890)):
    buffer = io.BytesIO()
    Image.new("RGB", size, "white").save(buffer, "PNG")
    return buffer.getvalue()


def run(value):
    return asyncio.run(value)


def cow_reading():
    return {
        "kind": "WORK", "problemText": "", "needsProblem": True,
        "lines": [
            {"text": "Bài giải:", "box": [280, 10, 560, 70], "uncertain": False},
            {"text": "49 : 7 × 2 = 14 (con)", "box": [240, 205, 640, 270], "uncertain": False},
            {"text": "Bò vàng: 35 con", "box": [510, 405, 820, 470], "uncertain": False},
        ],
    }


def test_unverified_model_geometry_is_not_displayed(monkeypatch):
    monkeypatch.setattr(notebook, "_generate", AsyncMock(return_value=cow_reading()))
    result = run(notebook.inspect_notebook(image_bytes()))
    assert [line.text for line in result.lines][-1] == "Bò vàng: 35 con"
    assert all(line.box is None for line in result.lines)
    assert result.needsProblem is True


def test_unclear_symbol_gets_targeted_question_without_cloud(monkeypatch):
    cloud = AsyncMock()
    monkeypatch.setattr(notebook, "_generate", cloud)
    result = run(notebook.coach_notebook(notebook.CoachRequest(
        problemText="", workText="49 : [?] × 2", stage="CHECK_WORK",
        focusText="49 : [?] × 2", studentAttempt="", hintLevel=0, previousHint="")))
    assert result.guarded is True
    assert "số hoặc dấu gì" in result.question
    cloud.assert_not_called()


def test_coaching_may_reference_visible_numbers_but_blocks_new_result(monkeypatch):
    request = notebook.CoachRequest(problemText="", workText="49 : 7 × 2 = 14 (con)",
        stage="CHECK_WORK", focusText="49 : 7 × 2 = 14 (con)", studentAttempt="", hintLevel=0, previousHint="")
    response = notebook.GuideResponse(stage="CHECK_WORK", hint="Em hãy nhìn lại 49 : 7 trước.",
        question="Vì sao em chia trước khi nhân?", feedback="", guarded=False)
    assert notebook.unsafe_coaching(response, request) is False
    leaked = response.model_copy(update={"hint": "Em tính được 7 rồi nhân tiếp."})
    assert notebook.unsafe_coaching(leaked, request) is True
    invented = response.model_copy(update={"hint": "Kết quả là 98."})
    assert notebook.unsafe_coaching(invented, request) is True


def test_multiple_problems_return_crop_request_without_transcript(monkeypatch):
    monkeypatch.setattr(notebook, "_generate", AsyncMock(return_value={
        "kind": "MULTIPLE", "problemText": "ignored", "needsProblem": False,
        "lines": [{"text": "1 + 2", "box": None, "uncertain": False}],
    }))
    result = run(notebook.inspect_notebook(image_bytes((800, 1200))))
    assert result.kind == "MULTIPLE" and result.lines == [] and result.problemText == ""


def test_answer_prose_cannot_become_an_original_question(monkeypatch):
    monkeypatch.setattr(notebook, "_generate", AsyncMock(return_value={
        "kind": "PROBLEM", "problemText": "Nhà trường đã vượt kế hoạch 15%", "needsProblem": False,
        "lines": [
            {"text": "Nhà trường đã vượt kế hoạch số phần trăm là:", "uncertain": False},
            {"text": "115% - 100% = 15%", "uncertain": False},
            {"text": "Đáp số: 15%", "uncertain": False},
        ],
    }))
    result = run(notebook.inspect_notebook(image_bytes()))
    assert result.kind == "WORK" and result.problemText == "" and result.needsProblem


def test_visible_question_is_preserved_with_its_work(monkeypatch):
    monkeypatch.setattr(notebook, "_generate", AsyncMock(return_value={
        "kind": "MIXED", "problemText": "Hỏi quyển vở có giá bao nhiêu tiền?", "needsProblem": False,
        "lines": [
            {"text": "Hỏi quyển vở có giá bao nhiêu tiền?", "uncertain": False},
            {"text": "Đáp số: 13000 đồng", "uncertain": False},
        ],
    }))
    result = run(notebook.inspect_notebook(image_bytes()))
    assert result.kind == "MIXED" and result.problemText and not result.needsProblem


@pytest.mark.parametrize("hint", ["Em tính được 7 rồi nhân tiếp.", "Có mười bốn con bò khoang.", "Đáp số: 14", "49 : 7 = 7.", "14 chính là đáp số."])
def test_existing_values_cannot_be_repackaged_as_answers(hint):
    request = notebook.CoachRequest(workText="49 : 7 × 2 = 14 (con)", focusText="49 : 7 × 2 = 14 (con)", stage="CHECK_WORK")
    response = notebook.GuideResponse(stage="CHECK_WORK", hint=hint, question="Em sẽ kiểm tra lại như thế nào?")
    assert notebook.unsafe_coaching(response, request)


def test_other_steps_are_not_a_source_of_new_results():
    request = notebook.CoachRequest(workText="49 : 7 × 2 = 14\n49 - 14 = 35", focusText="49 : 7 × 2 = 14", stage="CHECK_WORK")
    response = notebook.GuideResponse(stage="CHECK_WORK", hint="Em hãy so với số 35.", question="Em sẽ kiểm tra ra sao?")
    assert notebook.unsafe_coaching(response, request)


def test_short_original_problem_does_not_break_safe_fallback(monkeypatch):
    monkeypatch.setattr(notebook, "_generate", AsyncMock(return_value={}))
    result = run(notebook.coach_notebook(notebook.CoachRequest(problemText="?", workText="49 : 7", stage="CHECK_WORK")))
    assert result.guarded and result.question


def test_coloured_rows_are_independent_nonoverlapping_and_in_full_coordinates():
    image = np.full((660, 900, 3), 245, np.uint8)
    for y in range(30, 660, 30):
        cv2.line(image, (0, y), (899, y), (210, 210, 210), 1)
    for y in (90, 190, 290, 390, 490, 590):
        cv2.putText(image, "49 : 7 x 2 = 14 con", (100, y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (140, 40, 20), 3)
    boxes = handwriting_rows(image)
    assert len(boxes) == 6
    assert all(0 <= x1 < x2 <= 900 and 0 <= y1 < y2 <= 660 for x1, y1, x2, y2 in boxes)
    assert all(first[3] <= second[1] for first, second in zip(boxes, boxes[1:]))
    assert handwriting_rows(np.full((660, 900, 3), 255, np.uint8)) == []

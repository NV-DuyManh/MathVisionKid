"""Independent synthetic circle drawings; no private exam image needed in CI."""
import asyncio
from unittest.mock import Mock

import cv2
import numpy as np
import pytest

from app.tutoring import diagram_reading as diagram
from app.tutoring.notebook import NotebookQuestion


def picture(shaded=(5, 5, 5, 1), *, fill=215, boundaries=True):
    pixels = np.full((200, len(shaded)*140+40, 3), 255, np.uint8)
    for index, count in enumerate(shaded):
        center = (90+index*140, 100)
        for sector in range(count):
            cv2.ellipse(pixels, center, (45, 45), 0, -90+sector*72, -90+(sector+1)*72, (fill,)*3, -1)
        cv2.circle(pixels, center, 45, (0, 0, 0), 2)
        if boundaries:
            for angle in np.deg2rad(np.arange(5)*72-90):
                end = tuple(np.rint(np.array(center)+45*np.array([np.cos(angle), np.sin(angle)])).astype(int))
                cv2.line(pixels, center, end, (0, 0, 0), 2)
    return pixels


@pytest.mark.parametrize('shaded', [(5, 5, 5, 1), (0, 2), (1, 4, 3)])
def test_counts_visible_sectors_in_each_circle_from_pixels(shaded):
    assert diagram.circle_facts(picture(shaded)) == [(5, n, 5-n) for n in shaded]


def test_faint_fill_missing_boundaries_and_non_diagrams_remain_unknown():
    assert diagram.circle_facts(picture(fill=245)) is None
    assert diagram.circle_facts(picture(boundaries=False)) is None
    assert diagram.circle_facts(picture((1,))) is None
    image = np.full((200, 600, 3), 255, np.uint8)
    cv2.putText(image, '5000 1000 8000', (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    assert diagram.circle_facts(image) is None


def test_clarification_preserves_question_choices_and_requires_confirmation(monkeypatch):
    question = NotebookQuestion(label='Câu 1', problemText='Chọn hỗn số. [4 hình tròn; hình cuối tô 3 phần.]\nA. 1 B. 2 C. 3 D. 4')
    other = NotebookQuestion(label='Câu 2', problemText='Tính 1+1=?')
    result = asyncio.run(diagram.clarify_circles([question, other], picture(), 1))
    assert result[0].problemText.startswith('Chọn hỗn số. [Hình 1:')
    assert 'Hình 4: chia 5 phần bằng nhau, 1 phần tô màu, 4 phần không tô màu.' in result[0].problemText
    assert result[0].problemText.endswith('A. 1 B. 2 C. 3 D. 4')
    assert result[0].uncertain and result[1] is other
    assert question.problemText != result[0].problemText  # Original source object untouched.
    missed = asyncio.run(diagram.clarify_circles([question], picture((5, 5, 1)), 1))
    assert missed == [question]
    no_brackets = question.model_copy(update={'problemText': 'Có các hình tròn. Chọn một hỗn số.'})
    detector = Mock(side_effect=AssertionError('Unrelated text must not run the detector'))
    monkeypatch.setattr(diagram, 'circle_facts', detector)
    assert asyncio.run(diagram.clarify_circles([no_brackets], picture(), 1)) == [no_brackets]

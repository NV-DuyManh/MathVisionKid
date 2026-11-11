import asyncio
import io
from unittest.mock import AsyncMock

import cv2
import numpy as np
import pytest
from PIL import Image, ImageDraw

from app.tutoring import notebook
from app.tutoring.math_layout import clipped_edge_bounds


def photo(*, fragment=True, full_neighbor=False):
    image = Image.new('RGB', (800, 180), 'white')
    draw = ImageDraw.Draw(image)
    for y in [20, 65, 110]:
        for x in range(25, 755, 23):
            draw.rectangle((x, y, x+8, y+15), fill='black')
    if fragment or full_neighbor:
        for x in range(25, 755, 23):
            draw.rectangle((x, 164 if full_neighbor else 177, x+8, 179), fill='black')
    buffer = io.BytesIO(); image.save(buffer, 'PNG')
    return buffer.getvalue(), cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def test_only_a_clipped_fragment_gets_a_bounded_crop():
    assert clipped_edge_bounds(photo()[1]) == (0, 177)
    assert clipped_edge_bounds(photo(fragment=False)[1]) is None
    assert clipped_edge_bounds(photo(full_neighbor=True)[1]) is None


@pytest.mark.parametrize('retry', [dict(kind='PROBLEM', problemText='Tính 17/25 + 32/15 = ?'),
    dict(kind='MULTIPLE'), dict(kind='UNREADABLE'), dict(kind='WORK', lines=[dict(text='1+1=2')])])
def test_edge_reread_must_independently_confirm_one_complete_question(retry, monkeypatch):
    cloud = AsyncMock(side_effect=[dict(kind='MULTIPLE'), retry])
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = asyncio.run(notebook.inspect_notebook(photo()[0]))
    assert result.kind == ('PROBLEM' if retry['kind'] == 'PROBLEM' else 'MULTIPLE')
    assert cloud.await_count == 2
    assert cloud.await_args_list[0].args[2] != cloud.await_args_list[1].args[2]


def test_two_full_questions_never_get_silently_selected(monkeypatch):
    cloud = AsyncMock(return_value=dict(kind='MULTIPLE'))
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = asyncio.run(notebook.inspect_notebook(photo(full_neighbor=True)[0]))
    assert result.kind == 'MULTIPLE' and not result.problemText
    assert cloud.await_count == 1

"""Checked offline plans and exact catalog reuse must enforce the same source."""
from unittest.mock import AsyncMock
import pytest
from app.config import settings
from app.tutoring import catalog,lesson
from test_digit_append_support import ORIGINAL_PROMPT
from test_fraction_lesson_support import garden


@pytest.mark.asyncio
@pytest.mark.parametrize('source', [ORIGINAL_PROMPT,garden()])
async def test_only_supported_checked_offline_source_is_reused(tmp_path,monkeypatch,source):
    monkeypatch.setattr(settings,'lesson_catalog_enabled',True)
    monkeypatch.setattr(settings,'lesson_catalog_path',str(tmp_path/'private.sqlite3'))
    generator=AsyncMock(side_effect=lesson.TutorUnavailable('validation'))
    monkeypatch.setattr(lesson,'generate_plan',generator)
    req=lesson.LessonRequest(owner='pupil-a',problemText=source,problemConfirmed=True)
    first=await lesson.checked_plan(req)
    assert catalog.load_plan(req) is not None
    assert (await lesson.checked_plan(req)).model_dump()==first.model_dump()
    generator.assert_not_awaited()
    bad=req.model_copy(update={'problemText':'Tổng số là số lẻ. '+source})
    assert catalog.load_plan(bad) is None
    with pytest.raises(lesson.TutorUnavailable):await lesson.checked_plan(bad)
    generator.assert_awaited_once_with(bad)
    assert catalog.load_plan(bad) is None

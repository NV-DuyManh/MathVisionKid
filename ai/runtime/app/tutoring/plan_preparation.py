"""Private, bounded preparation while the pupil reviews a transcription."""
import asyncio
from collections import OrderedDict
import time

from pydantic import Field, model_validator

from app.tutoring.service import TutorModel
from app.tutoring import lesson


class SourceDraft(TutorModel):
    owner: str = Field(min_length=1, max_length=200)
    problemText: str = Field(min_length=3, max_length=4000)
    workText: str = Field(default='', max_length=6000)

    @model_validator(mode='after')
    def readable(self):
        if '[?]' in self.problemText or '[?]' in self.workText:
            raise ValueError('Clarify the source before preparation')
        lesson.safe_public(self.problemText)
        return self


_jobs: OrderedDict[tuple, tuple] = OrderedDict()


def source_key(request):
    return request.owner, request.problemText, request.workText


def prune():
    for key, (expires, task) in list(_jobs.items()):
        if expires <= time.monotonic() and task.done():
            _jobs.pop(key)


def launch(request):
    task = asyncio.create_task(lesson.checked_plan(request))
    # Observe failures without exposing a draft, answer, or raw provider error.
    task.add_done_callback(lambda done: None if done.cancelled() else done.exception())
    _jobs[source_key(request)] = time.monotonic() + 300, task
    return task


async def prepare(request: SourceDraft):
    prune()
    key = source_key(request)
    if key in _jobs:
        task = _jobs[key][1]
        phase = 'preparing' if not task.done() else 'unavailable' if task.cancelled() or task.exception() else 'ready'
        return {'phase': phase}
    if sum(not task.done() for _, task in _jobs.values()) >= 2 or any(
            item[0] == request.owner and not task.done() for item, (_, task) in _jobs.items()):
        return {'phase': 'busy'}
    if len(_jobs) >= 16:
        oldest = next((item for item, (_, task) in _jobs.items() if task.done()), None)
        if oldest is None:
            return {'phase': 'busy'}
        _jobs.pop(oldest)
    launch(request)
    return {'phase': 'preparing'}


async def prepared_plan(request):
    prune()
    key = source_key(request)
    entry = _jobs.get(key)
    if entry is None:
        return None
    task = entry[1]
    if task.done() and (task.cancelled() or task.exception()):
        # The explicit Start action may retry once; concurrent requests share it.
        task = launch(request)
    plan = await asyncio.shield(task)
    return plan.model_copy(deep=True)

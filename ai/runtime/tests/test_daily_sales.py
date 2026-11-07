"""Cold preparation and replay must prove unit-rate questions without a provider."""
from fractions import Fraction
from unittest.mock import AsyncMock

import pytest

from app.tutoring import lesson, quiz_variants
from app.tutoring.short_math import verified_plan


def source(days=2, amount=620, target=7, goods='gạo', options=''):
    return (f'Một cửa hàng trong {days} ngày bán được {amount} kg {goods}. '
            f'Hỏi trong {target} ngày cửa hàng bán được bao nhiêu ki-lô-gam {goods}? '
            f'(Biết số {goods} mỗi ngày bán được là như nhau).' + options)


@pytest.mark.asyncio
@pytest.mark.parametrize('days, daily, target, goods', [(2,310,7,'gạo'), (3,125,8,'đường'), (5,36,12,'ngô'), (4,21,3,'bột')])
async def test_cold_lesson_opens_checked_steps_without_waiting_for_a_model(monkeypatch, days, daily, target, goods):
    monkeypatch.setattr('app.tutoring.catalog.load_plan', lambda request: None)
    monkeypatch.setattr('app.tutoring.catalog.save_plan', lambda *args: None)
    provider = AsyncMock(side_effect=AssertionError('The whole source has an exact proof'))
    monkeypatch.setattr(lesson, 'generate_plan', provider)
    request = lesson.LessonRequest(owner='unit-rate-fixture', problemText=source(days, days*daily, target, goods),
                                  problemConfirmed=True, startWithReading=True, guidedUnderstanding=True)
    response = await lesson.start_lesson(request)
    assert not response.preparingMath and response.understandingSteps == 0
    assert len(response.outline) == 2
    wrong = lesson.answer_lesson(lesson.TurnRequest(owner=request.owner, sessionId=response.sessionId, revision=0, answer='-1'))
    assert wrong.status == 'TRY_AGAIN'
    next_step = lesson.answer_lesson(lesson.TurnRequest(owner=request.owner, sessionId=response.sessionId, revision=0, answer=str(daily)))
    result = lesson.answer_lesson(lesson.TurnRequest(owner=request.owner, sessionId=response.sessionId, revision=next_step.revision, answer=str(daily*target)))
    assert result.status == 'COMPLETE'
    assert result.completed[-1].answer == str(daily*target)
    provider.assert_not_called()


def test_options_are_checked_without_replacing_the_division_and_multiplication():
    text = source(options=' A. 4340 kg B. 434 kg C. 217 kg D. 2170 kg')
    plan = lesson.Plan.model_validate(verified_plan(text))
    lesson.validate_plan(plan, lesson.LessonRequest(owner='unit-rate-fixture', problemText=text, problemConfirmed=True), lesson.formula_constants(text))
    assert plan.steps[-1].correctChoice == '2170 kg'
    assert quiz_variants.proof(plan)[:3] == (Fraction(2170), 'kg', [['Div'], ['Mult']])


@pytest.mark.parametrize('text', [
    source(days=0), source(amount=0), source(target=0),
    source().replace('là như nhau', 'không như nhau'),
    source().replace('(Biết số gạo mỗi ngày bán được là như nhau).', ''),
    source() + ' Ngày cuối bán thêm 10 kg.',
    source().replace('bao nhiêu ki-lô-gam', 'bao nhiêu g'),
    source(options=' A. 4340 kg B. 434 kg C. 217 kg D. 2100 kg'),
    source(options=' A. 2170 kg B. 2170 kg C. 217 kg D. 2100 kg'),
    source(options=' A. 2170 tấn B. 434 kg C. 217 kg D. 2100 kg'),
])
def test_missing_conditions_extra_data_and_bad_choices_keep_independent_review(text):
    assert verified_plan(text) is None

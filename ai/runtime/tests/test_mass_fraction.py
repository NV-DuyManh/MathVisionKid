"""Source-complete proof, mass units, and a fast reading-first regression for Câu 7."""
import asyncio
from collections import OrderedDict
from unittest.mock import AsyncMock
import pytest
from app.config import settings
from app.tutoring import lesson, catalog, plan_preparation
from app.tutoring.mass_fraction import verified_plan


def source(tonnes=2,kg=35,n=2,d=5,options=('814','914','1 221','1 231'),share='hạnh nhân'):
    return (f'Câu 7. Bác An thu hoạch được {tonnes} tấn {kg} kg hạt điều và hạnh nhân. '
            f'Biết rằng số lượng {share} chiếm {n}/{d} tổng số hạt điều và hạnh nhân thu hoạch được. '
            f'Vậy, bác An thu hoạch được số ki – lô – gam {share} là: '
            +' '.join(f'{label}. {value} kg' for label,value in zip('ABCD',options)))


def checked(text):
    raw=verified_plan(text)
    assert raw is not None
    plan=lesson.Plan.model_validate(raw)
    lesson.validate_plan(plan,lesson.LessonRequest(owner='mass-test',problemText=text,problemConfirmed=True),lesson.formula_constants(text))
    answers=[]
    for step in plan.steps:answers.append(str(lesson.calculate_exact(lesson.expression_at(step,answers))))
    return plan,answers


@pytest.mark.parametrize('text,answers',[
    (source(),['2035','814']),
    (source(3,20,3,4,('2255','2265','2275','2285')),['3020','2265']),
    (source(2,0,3,8,('700','800','750','900')),['2000','750']),
    (source(share='hạt điều'),['2035','814']),
    (source(options=('1 231','1 221','914','814')),['2035','814']),
])
def test_exact_mass_and_target_are_taken_from_each_source(text,answers):
    plan,actual=checked(text)
    assert actual==answers and plan.finalAnswerStep==1
    assert plan.steps[0].unit==plan.steps[1].unit=='kg'
    assert plan.steps[1].fractionNotation
    assert all(len(item)<=500 for step in plan.steps for item in step.initialGuidance)


@pytest.mark.parametrize('change',[
    lambda text:'Tổng khối lượng là một số lẻ. '+text,
    lambda text:text.replace('2 tấn','2 tạ'),
    lambda text:text.replace('35 kg','1000 kg'),
    lambda text:text.replace('2/5','0/5'),
    lambda text:text.replace('2/5','2/0'),
    lambda text:text.replace('2/5','5/2'),
    lambda text:text.replace('Vậy, bác An','Vậy, bác Bình'),
    lambda text:text.replace('ki – lô – gam hạnh nhân','ki – lô – gam hạt điều'),
    lambda text:text.replace('tổng số hạt điều và hạnh nhân','tổng số hạt điều'),
    lambda text:text.replace('Biết rằng số lượng hạnh nhân','Biết rằng số lượng hạt dẻ'),
    lambda text:text.replace('A. 814 kg','A. 813 kg'),
    lambda text:text.replace('B. 914 kg','B. 814 kg'),
    lambda text:text.replace('C. 1 221 kg','C. 1 221 g'),
    lambda text:text+' Câu 8. Tìm số khác.',
    lambda text:text.replace('35 kg hạt điều','35 kg hạt điều còn lại'),
    lambda text:text.replace('C. 1 221 kg','E. 1 221 kg'),
])
def test_unsupported_incomplete_or_contradictory_sources_never_get_an_exact_plan(change):
    assert verified_plan(change(source())) is None


@pytest.mark.parametrize('text',[
    source().replace('ki – lô – gam','kg'),
    source().replace('ki – lô – gam','ki-lô-gam').replace('A.','A)').replace('B.','B)').replace('C.','C)').replace('D.','D)'),
    source().replace(' 221','\u202f221').replace(' 231','\u00a0231'),
    source().replace('2/5','(2)/(5)'),
])
def test_equivalent_unit_and_option_notation_keeps_the_same_checked_result(text):
    assert checked(text)[1]==['2035','814']


def test_no_direct_computed_operand_is_whitelisted_as_a_conversion():
    text=source()
    plan,_=checked(text)
    plan.steps[0].expression='2035'
    with pytest.raises(ValueError,match='Derived literal'):
        lesson.validate_plan(plan,lesson.LessonRequest(owner='mass-test',problemText=text,problemConfirmed=True),lesson.formula_constants(text))


@pytest.mark.asyncio
async def test_reading_opens_and_checked_math_finishes_without_a_model_call(monkeypatch):
    monkeypatch.setattr(lesson,'_sessions',OrderedDict())
    monkeypatch.setattr(plan_preparation,'_jobs',OrderedDict())
    provider=AsyncMock(side_effect=lesson.TutorUnavailable('rate_limit'))
    monkeypatch.setattr(lesson,'generate_plan',provider)
    response=await lesson.start_lesson(lesson.LessonRequest(owner='mass-test',problemText=source(),problemConfirmed=True,
        guidedUnderstanding=True,startWithReading=True))
    assert response.preparingMath and response.understandingSteps==3 and response.step.kind=='UNDERSTAND'
    assert '814' not in response.model_dump_json(exclude={'sessionId'})
    session=lesson._sessions[response.sessionId]
    assert await asyncio.wait_for(session.preparation_task,2)
    assert not isinstance(session.plan,lesson.ReadingPlan)
    for _ in range(3):
        response=lesson.answer_lesson(lesson.TurnRequest(owner='mass-test',sessionId=response.sessionId,
            revision=session.revision,answer=session.plan.steps[len(session.answers)].correctChoice))
    assert response.step.kind=='MATH' and lesson.calculate_exact(response.step.expression)==2035
    for value in ('2035','814'):
        response=lesson.answer_lesson(lesson.TurnRequest(owner='mass-test',sessionId=response.sessionId,revision=session.revision,answer=value))
    assert response.status=='COMPLETE' and response.conclusion=='Đáp số: 814 kg.'
    provider.assert_not_awaited()


@pytest.mark.asyncio
async def test_exact_plan_catalog_still_isolates_source_and_policy(tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'lesson_catalog_enabled',True)
    monkeypatch.setattr(settings,'lesson_catalog_path',str(tmp_path/'test.sqlite3'))
    req=lesson.LessonRequest(owner='mass-test',problemText=source(),problemConfirmed=True)
    provider=AsyncMock(side_effect=lesson.TutorUnavailable('validation'))
    monkeypatch.setattr(lesson,'generate_plan',provider)
    first=await lesson.checked_plan(req)
    assert catalog.load_plan(req).model_dump()==first.model_dump()
    assert catalog.load_plan(req.model_copy(update={'owner':'other-pupil'})) is None
    assert catalog.load_plan(req.model_copy(update={'problemText':source().replace('35 kg','36 kg')})) is None
    provider.assert_not_awaited()

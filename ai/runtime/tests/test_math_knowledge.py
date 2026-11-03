"""Knowledge coverage and refusal diagnostics; synthetic, not trained accuracy."""
import copy
from fractions import Fraction
import json
import logging
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from app.tutoring import lesson, math_knowledge, validation_audit
from _lesson_test_data import step, review_for
from scripts.benchmark_lesson_validator import evaluate, audit_summary


@pytest.mark.parametrize('blank', ['....', '…', '?'])
def test_conversion_blank_grounds_target_unit_and_its_factor(blank):
    source = f'Điền vào chỗ chấm: 1,7 km² = {blank} ha'
    assert {'fromUnit': 'km²', 'toUnit': 'ha', 'factor': '100'} in math_knowledge.unit_conversions(source)
    assert '100' in math_knowledge.formula_constants(source)
    assert math_knowledge.unit_conversions('Hà có 2 viên bi.') == []


@pytest.mark.parametrize('source,target,factor',[
    ('tấn','kg','1000'),('tạ','kg','100'),('yến','kg','10'),('kg','g','1000'),
    ('hg','g','100'),('dag','g','10'),('g','mg','1000'),('kg','mg','1000000'),
    ('km','m','1000'),('hm','m','100'),('dam','m','10'),('m','dm','10'),('cm','mm','10'),
    ('km²','m²','1000000'),('hm²','m²','10000'),('dam²','m²','100'),('m²','cm²','10000'),
    ('m³','cm³','1000000'),('dm³','cm³','1000'),('ha','m²','10000'),
    ('l','ml','1000'),('dl','ml','100'),('cl','ml','10'),('m³','l','1000'),('l','cm³','1000'),
    ('tuần','ngày','7'),('ngày','giờ','24'),('giờ','phút','60'),('phút','giây','60'),('giờ','giây','3600'),
])
def test_independent_reference_relations(source,target,factor):
    assert dict(fromUnit=source,toUnit=target,factor=factor) in lesson.unit_conversions(f'Đổi 3 {source} sang {target}.')


@pytest.mark.parametrize('join',['-',' – ','‑','−',' ',''])
@pytest.mark.parametrize('left,right,from_unit,to_unit,factor',[
    (['ki','lô','mét'],['mét'],'km','m','1000'),
    (['đề','xi','mét','vuông'],['xăng','ti','mét','vuông'],'dm²','cm²','100'),
    (['mét','khối'],['đề','xi','mét','khối'],'m³','dm³','1000'),
    (['ki','lô','gam'],['mi','li','gam'],'kg','mg','1000000'),
    (['lít'],['mi','li','lít'],'l','ml','1000'),
    (['héc','ta'],['mét','vuông'],'ha','m²','10000'),
])
def test_spelling_and_hyphen_variants_preserve_dimension(join,left,right,from_unit,to_unit,factor):
    source=f'Đổi ３\u00a0{join.join(left)} sang {join.join(right)}.'
    assert dict(fromUnit=from_unit,toUnit=to_unit,factor=factor) in lesson.unit_conversions(source)


@pytest.mark.parametrize('exponent',['²','2','^2','^{2}',' ²'])
def test_explicit_area_never_whitelists_linear_factor(exponent):
    constants=lesson.formula_constants(f'Đổi 3 m{exponent} sang cm{exponent}.')
    assert '10000' in constants and '100' not in constants


@pytest.mark.parametrize('source',[
    'Bác Tân có 35 kg.', 'Bác Tạ có 35 kg.', 'Bác Hà có 3 m² đất.',
    'Có 3 kg gạo trên bàn dài 5 m.', 'Có 3 kg gạo và 5 lít nước.',
    'Đổi 3 tháng sang ngày.', 'Đổi 3 năm sang ngày.',
    'Có 3 m² vải và sợi dây dài 5 cm.',
])
def test_names_dimensions_and_calendar_do_not_invent_conversion(source):
    assert not lesson.unit_conversions(source)


def test_corpus_measures_both_directions_of_grounding_errors():
    corpus=json.loads((Path(__file__).parent/'fixtures/validator_knowledge_cases.json').read_text(encoding='utf-8'))
    results=evaluate(corpus)
    assert results['cases']==56 and results['passed']==56
    assert results['validCases']==39 and results['invalidCases']==17
    assert results['localFalseRejectRate']==results['localFalseAcceptRate']==0


def test_context_facts_are_scoped_and_cannot_be_mutated_across_requests():
    assert not math_knowledge.contextual_facts('Có 7 hộp, mỗi hộp 9 bút.')
    facts=math_knowledge.contextual_facts('Hình lập phương có cạnh 5 cm.')
    assert facts[0]['id']=='cube' and facts[0]['constants']==['4','6']
    facts[0]['constants'].append('999')
    assert '999' not in lesson.formula_constants('Hình lập phương có cạnh 5 cm.')
    assert '6' not in lesson.formula_constants('Có 7 hộp, mỗi hộp 9 bút.')


@pytest.mark.parametrize('source,expression,expected',[
    ('Đổi 3 m² sang cm².','3*100*100','30000'),
    ('Đổi 3 m³ sang dm³.','3*10*10*10','3000'),
    ('Đổi 750 cm³ sang m³.','750/100/100/100','3/4000'),
    ('Đổi 3 giờ sang giây.','3*60*60','10800'),
    ('Đổi 3 m² sang cm².','3*(100*100)','30000'),
    ('Đổi 3 m² sang cm².','3/((1/100)/100)','30000'),
])
def test_equivalent_factorizations_keep_value_without_authorizing_each_literal(source,expression,expected):
    converted=math_knowledge.normalize_conversion_factors(expression,lesson.numeric_values(source)|lesson.formula_constants(source),lesson.unit_conversions(source))
    assert lesson.calculate_exact(converted)==lesson.calculate_exact(expression)==Fraction(expected)
    assert not (lesson.numeric_values(converted)-lesson.numeric_values(source)-lesson.formula_constants(source))


def test_factor_folding_does_not_earn_answers_or_arbitrary_factors():
    source='Đổi 3 m² sang cm².';conversions=lesson.unit_conversions(source)
    givens=lesson.numeric_values(source)|lesson.formula_constants(source)
    for expression in ('3*100','30000','3*(50+50)*(50+50)','3*99*100','3*100*101'):
        assert math_knowledge.normalize_conversion_factors(expression,givens,conversions)==expression
    result=math_knowledge.normalize_conversion_factors('{s0}*100*100',givens,conversions)
    assert '{s0}' in result and 'prior_ref' not in result and '10000' in result
    forged='prior_ref_0+{s0}*100*100'
    assert math_knowledge.normalize_conversion_factors(forged,givens,conversions)==forged


@pytest.mark.parametrize('expression,allowed', [('3*10000.0',True),('3*10000.00001',False),('3*100*100',True),('3*100',False)])
def test_full_validator_accepts_only_equivalent_grounded_values(expression,allowed):
    source='Đổi 3 m² sang cm².'
    plan=lesson.Plan(topic='Đổi diện tích',goal='Đổi đơn vị diện tích.',finalAnswerStep=1,steps=[
        lesson.Step.model_validate(step(title='Đổi diện tích',expression=expression,unit='cm²')),
        lesson.Step.model_validate(step(title='Ghi kết quả',expression='{s0}*1',unit='cm²'))])
    request=lesson.LessonRequest(owner='knowledge-test',problemConfirmed=True,problemText=source)
    if allowed:
        lesson.validate_plan(plan,request,lesson.formula_constants(source))
        assert lesson.calculate_exact(plan.steps[0].expression)==30000
    else:
        with pytest.raises(ValueError,match='Derived literal'):lesson.validate_plan(plan,request,lesson.formula_constants(source))


@pytest.mark.asyncio
async def test_draft_and_independent_review_receive_the_same_grounded_facts(monkeypatch):
    plan=dict(topic='Hình lập phương',goal='Tìm diện tích và thể tích.',finalAnswerStep=None,steps=[
        step(title='Tính diện tích toàn phần',expression='6*5*5',unit='cm²'),
        step(title='Tính thể tích',expression='5*5*5',unit='cm³')])
    cloud=AsyncMock(side_effect=[copy.deepcopy(plan),review_for(plan,[
        dict(stepIndex=0,answer='150',unit='cm²'),dict(stepIndex=1,answer='125',unit='cm³')])])
    monkeypatch.setattr(lesson,'_generate',cloud)
    await lesson.generate_plan(lesson.LessonRequest(owner='knowledge-test',problemConfirmed=True,
        problemText='Hình lập phương có cạnh 5 cm. Tính diện tích toàn phần và thể tích.'))
    draft=json.loads(cloud.await_args_list[0].args[1]);review=json.loads(cloud.await_args_list[1].args[1])
    assert draft['knowledgeVersion']==review['knowledgeVersion']==math_knowledge.VERSION
    assert draft['mathematicalConventions']==review['mathematicalConventions']
    assert draft['mathematicalConventions'][0]['id']=='cube'


@pytest.mark.parametrize('message,code',[
    ('Step 0: Derived literal operand','UNGROUNDED_OPERAND'),
    ('Recheck the original source; refuse if genuinely insufficient','SOURCE_UNRESOLVED'),
    ('Lesson did not pass independent review: private issue','SEMANTIC_REVIEW'),
    ('Invalid final answer step','RESULT_SCOPE'),('Future answer in teaching','PREMATURE_RESULT'),
    ('Step 0: a fraction/share is dimensionless','UNIT'),('Other private issue','OTHER_VALIDATION'),
])
def test_refusal_codes_are_explicit(message,code):
    assert validation_audit.reason_code(ValueError(message))==code


def test_audit_never_logs_source_raw_issue_or_untrusted_provider(caplog,tmp_path):
    source='Private pupil question';issue='private rejected draft with secret'
    with caplog.at_level(logging.INFO,logger=validation_audit.__name__):
        validation_audit.record(source,1,ValueError('independent review: '+issue),'injected\nprovider','review',
                                ['mathematicsCorrect','injected\ncheck'])
        validation_audit.record(source,2,provider='gemini',stage='recovered')
    assert source not in caplog.text and issue not in caplog.text and 'injected' not in caplog.text
    assert 'code=SEMANTIC_REVIEW provider=unknown stage=review checks=mathematicsCorrect' in caplog.text
    path=tmp_path/'audit.log';path.write_text(caplog.text,encoding='utf-8')
    summary=audit_summary(path)
    assert summary['codes']=={'SEMANTIC_REVIEW':1,'RECOVERED':1} and summary['uniqueSourceFingerprints']==1
    assert 'private' not in json.dumps(summary).lower()


@pytest.mark.asyncio
async def test_reviewer_failure_records_actual_referee_and_check_not_raw_text(monkeypatch,caplog):
    from app.tutoring.service import ProviderResult
    plan=dict(topic='Số bút',goal='Tìm số bút còn lại.',finalAnswerStep=1,steps=[
        step(title='Tìm tổng số bút',expression='7*9',unit='bút'),
        step(title='Tìm số bút còn lại',expression='{s0}-11',unit='bút')])
    refused={**review_for(plan),'teachingClear':False,'issues':['private review content']}
    cloud=AsyncMock(side_effect=[ProviderResult(copy.deepcopy(plan),'groq'),ProviderResult(refused,'gemini'),
        ProviderResult(copy.deepcopy(plan),'gemini'),ProviderResult(review_for(plan),'groq')])
    monkeypatch.setattr(lesson,'_generate',cloud)
    with caplog.at_level(logging.INFO):
        await lesson.generate_plan(lesson.LessonRequest(owner='knowledge-test',problemConfirmed=True,
            problemText='Có 7 hộp, mỗi hộp 9 bút. Cho đi 11 bút. Hỏi còn bao nhiêu bút?'))
    assert 'provider=gemini stage=review checks=teachingClear' in caplog.text
    assert 'code=RECOVERED provider=gemini stage=recovered' in caplog.text
    assert 'private review content' not in caplog.text
    repair=json.loads(cloud.await_args_list[2].args[1]);review=json.loads(cloud.await_args_list[3].args[1])
    assert repair['validationIssueCode']=='SEMANTIC_REVIEW' and 'validationIssueCode' not in review

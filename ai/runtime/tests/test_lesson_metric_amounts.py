"""Regression for grouped amounts and metric units; model review stays required."""
import json
from unittest.mock import AsyncMock

import pytest

from app.tutoring import lesson
from _lesson_test_data import step, review_for


SOURCE = ('Bài 3: (3 điểm) Một nền nhà hình chữ nhật có chiều dài 8m, chiều rộng bằng 1/2 chiều dài. '
          'Người ta lát nền nhà đó bằng các viên gạch hình vuông cạnh 4dm. '
          'a) Hỏi cần mua bao nhiêu viên gạch để lát kín nền nhà đó? '
          'b) Biết rằng 2m² loại gạch đó giá 250 000 đồng, hỏi cần bao nhiêu tiền để lát nền nhà? '
          '(Diện tích phần mạch vữa không đáng kể).')


def candidate():
    return dict(topic='Lát nền nhà', goal='Tìm số viên gạch và số tiền cần mua.', finalAnswerStep=None, steps=[
        step(title='Tìm chiều rộng nền nhà', expression='8*1/2', unit='m'),
        step(title='Tìm diện tích nền nhà', expression='8*{s0}', unit='m²'),
        step(title='Tìm diện tích một viên gạch', expression='4*4', unit='dm²'),
        step(title='Tìm số viên gạch cần mua', expression='{s1}*100/{s2}', unit='viên'),
        step(title='Tìm số tiền mua gạch', expression='{s1}/2*250000', unit='đồng'),
    ])


@pytest.mark.parametrize('separator', [' ', '\u00a0', '\u202f', '\u2009'])
def test_grouped_source_amount_is_one_number(separator):
    assert lesson.numeric_values(f'Giá 250{separator}000 đồng và 4{separator}000{separator}000 đồng.') == {'250000', '4000000'}
    assert lesson.numeric_values('Có 12\n345 và 2/5, 2,75.') == {'12', '345', '2', '5', '2.75'}


@pytest.mark.parametrize('source,expected', [
    (SOURCE, {'10', '100'}),
    ('Đổi 3 m² sang cm².', {'100', '10000'}),
    ('Đổi 2 m³ sang dm³.', {'10', '1000'}),
])
def test_conversion_constants_follow_explicit_metric_context(source, expected):
    assert expected <= lesson.formula_constants(source)
    assert not {'10', '100', '1000'} & lesson.formula_constants('Mua 8 viên gạch giá 250 000 đồng.')
    assert '100' not in lesson.formula_constants('Một đoạn dài 8m. Tính chiều dài.')


@pytest.mark.asyncio
async def test_tiling_keeps_both_requested_results_and_checks_units_independently(monkeypatch):
    plan = candidate()
    results = [dict(stepIndex=3, answer='200', unit='viên'), dict(stepIndex=4, answer='4000000', unit='đồng')]
    cloud = AsyncMock(side_effect=[plan, review_for(plan, results)])
    monkeypatch.setattr(lesson, '_generate', cloud)
    result = await lesson.generate_plan(lesson.LessonRequest(owner='metric-regression', problemText=SOURCE, problemConfirmed=True))
    assert result.finalAnswerStep is None and cloud.await_count == 2
    payload = json.loads(cloud.call_args_list[1].args[1])
    assert payload['computedAnswers'] == ['4', '32', '16', '200', '4000000']
    assert '250000' in payload['givenNumbers'] and '250' not in payload['givenNumbers']
    assert {'fromUnit': 'm²', 'toUnit': 'dm²', 'factor': '100'} in payload['unitConversions']
    assert 'every' in payload['resultScope']['instruction'].lower()


def test_conversion_does_not_authorize_arbitrary_operands_or_amounts():
    request = lesson.LessonRequest(owner='metric-regression', problemText=SOURCE, problemConfirmed=True)
    plan = candidate()
    plan['steps'][3]['expression'] = '{s1}*99/{s2}'
    with pytest.raises(ValueError, match='Derived literal'):
        lesson.validate_plan(lesson.Plan.model_validate(plan), request, lesson.formula_constants(SOURCE))
    plan = candidate()
    plan['steps'][4]['expression'] = '{s1}/2*250001'
    with pytest.raises(ValueError, match='Derived literal'):
        lesson.validate_plan(lesson.Plan.model_validate(plan), request, lesson.formula_constants(SOURCE))


@pytest.mark.parametrize('length,tile,price,answers', [
    ('6', '3', '180 000', ['3', '18', '9', '200', '1620000']),
    ('10', '5', '300 000', ['5', '50', '25', '200', '7500000']),
])
def test_metric_amounts_come_from_each_source_without_fixed_problem_answers(length, tile, price, answers):
    source = SOURCE.replace('8m', length+'m').replace('4dm', tile+'dm').replace('250 000', price)
    plan = candidate()
    for index, expression in {0: length+'*1/2', 1: length+'*{s0}', 2: tile+'*'+tile,
                              4: '{s1}/2*'+price.replace(' ', '')}.items():
        plan['steps'][index]['expression'] = expression
    checked = lesson.Plan.model_validate(plan)
    lesson.validate_plan(checked, lesson.LessonRequest(owner='metric-regression', problemText=source,
        problemConfirmed=True), lesson.formula_constants(source))
    actual = []
    for item in checked.steps:
        actual.append(str(lesson.calculate_exact(lesson.expression_at(item, actual))))
    assert actual == answers


def test_grouping_does_not_merge_separate_prior_answers():
    value = lesson.Step.model_validate(step(expression='8+2', initialGuidance=['Kết quả bước trước là 100, còn lượng đề cho là 4.']))
    assert lesson.guidance_at(value, ['4', '100'], reveal_work=False) == value.initialGuidance


def test_provider_contract_requires_complete_initial_teaching_before_generation():
    contract = lesson.PLANNING_SCHEMA['$defs']['DraftStep']['properties']['initialGuidance']
    assert contract['minItems'] == contract['maxItems'] == 3
    assert contract['items']['minLength'] == 60 and contract['items']['maxLength'] == 220
    assert lesson.PLANNING_SCHEMA['properties']['goal']['pattern'] == '^[^0-9]*$'


def test_repair_feedback_identifies_the_field_instead_of_a_generic_rejection():
    plan = candidate()
    plan['steps'][0]['question'] = 'Chiều rộng có phải là 999 m không?'
    with pytest.raises(ValueError, match=r"step 0.*question.*999"):
        lesson.validate_plan(lesson.Plan.model_validate(plan), lesson.LessonRequest(owner='metric-regression',
            problemText=SOURCE, problemConfirmed=True), lesson.formula_constants(SOURCE))


def test_initial_teaching_feedback_identifies_unearned_unit_price():
    plan = candidate()
    plan['steps'][4]['initialGuidance'] = ['Đơn giá mỗi mét vuông là 125000 đồng.']
    with pytest.raises(ValueError, match=r'Step 4 initialGuidance\[0\].*125000'):
        lesson.validate_plan(lesson.Plan.model_validate(plan), lesson.LessonRequest(owner='metric-regression',
            problemText=SOURCE, problemConfirmed=True), lesson.formula_constants(SOURCE))


@pytest.mark.parametrize('expression,answers,givens', [('4*4', [], {'4'}), ('{s0}/2*250000', ['32'], {'2', '250000'})])
def test_fraction_in_source_does_not_add_common_denominator_teaching_to_other_operations(expression, answers, givens):
    value = lesson.Step.model_validate(step(expression=expression, fractionNotation=True,
        initialGuidance=['Đọc lại đại lượng đang cần tìm và đối chiếu đơn vị của nó với đề.',
                         'Chọn các lượng đã biết liên quan đến chính phép tính này.']))
    teaching = lesson.guidance_at(value, answers, givens, reveal_work=False)
    assert len(teaching) == 3 and not any('mẫu chung' in item for item in teaching)


def test_spaced_future_answer_is_still_blocked_in_private_help():
    plan = candidate()
    plan['steps'][0]['guidance'][0] = 'Số tiền cần dùng là 4 000 000 đồng.'
    request = lesson.LessonRequest(owner='metric-regression', problemText=SOURCE, problemConfirmed=True)
    with pytest.raises(ValueError, match='Future answer'):
        lesson.validate_plan(lesson.Plan.model_validate(plan), request, lesson.formula_constants(SOURCE))


@pytest.mark.asyncio
async def test_multi_part_lesson_still_rejects_independent_review_failure(monkeypatch):
    plan = candidate()
    failed = review_for(plan, [])
    failed.update(mathematicsCorrect=False, issues=['Sai số tiền cần trả.'])
    cloud = AsyncMock(side_effect=[plan, failed, plan, failed])
    monkeypatch.setattr(lesson, '_generate', cloud)
    with pytest.raises(ValueError, match='independent review'):
        await lesson.generate_plan(lesson.LessonRequest(owner='metric-regression', problemText=SOURCE, problemConfirmed=True))
    assert cloud.await_count == 4

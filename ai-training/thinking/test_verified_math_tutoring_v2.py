import ast
from fractions import Fraction
import json
import re
import pytest

from verified_math_data_v2 import build
from verified_math_tutoring_v2 import wordproblem_tutor, vertical_tutor


def test_all_2320_word_cases_hint_and_exact_visible_ast_steps():
    rows = build()
    assert len(rows) == 2320
    for row in rows:
        hinted = wordproblem_tutor(row['problem'], row['target'], row['grade'])
        student = hinted['student_response']
        assert set(student) == {'title', 'hint', 'revealAnswer', 'retryAllowed'}
        assert student['revealAnswer'] is False and student['hint'].count('?') == 1
        assert not re.search(r'\d', json.dumps(student, ensure_ascii=False))
        assert 'answer' not in hinted['machine'] and 'worked_solution' not in hinted['machine']
        worked = wordproblem_tutor(row['problem'], row['target'], row['grade'], mode='worked_solution')
        if row['target']['status'] != 'solve':
            assert worked['student_response']['revealAnswer'] is False
            continue
        assert worked['status'] == 'WORKED_SOLUTION_READY', (row['sample_id'], worked)
        steps = [step for step in worked['student_response']['steps'] if step['kind'] == 'ast_calculation']
        ast_count = sum(isinstance(node, ast.BinOp) for node in ast.walk(ast.parse(row['target']['expr'], mode='eval')))
        assert len(steps) == ast_count and Fraction(steps[-1]['value']) == Fraction(row['oracle_answer'])
        assert all(step['why'] and step['computation'] for step in steps)
        assert steps[-1]['unit'] == row['target']['unit']
        assert worked['machine']['official_grade_assigned'] is False


def test_three_step_word_and_units_chronological():
    problem = 'Tìm trung bình cộng của 9, 12 và 15.'
    plan = {'status': 'solve', 'expr': '(f0+f1+f2)/3', 'unit': ''}
    response = wordproblem_tutor(problem, plan, 4, mode='worked_solution')
    steps = response['student_response']['steps']
    assert [step['value'] for step in steps] == ['21', '36', '12']
    assert response['student_response']['final_answer'] == '12'
    time = wordproblem_tutor('Đổi 2 giờ 15 phút thành phút.', {'status': 'solve', 'expr': 'f0*60+f1', 'unit': 'phút'}, 3, mode='worked_solution')
    assert [step['unit'] for step in time['student_response']['steps']] == ['phút', 'phút']
    assert time['student_response']['final_answer'] == '135 phút'


def test_fraction_common_denominator_and_multiplication_are_visible():
    result = wordproblem_tutor('Tính tổng hai phân số 2/3 và 3/7.', {'status': 'solve', 'expr': 'f0+f1', 'unit': ''}, 4, mode='worked_solution')
    computations = [step['computation'] for step in result['student_response']['steps']]
    assert 'Mẫu số chung: 21 (chia hết cho 3 và 7)' in computations
    assert '2/3 = 14/21' in computations and '3/7 = 9/21' in computations
    assert result['student_response']['final_answer'] == '23/21'
    product = wordproblem_tutor('Tính tích hai phân số 2/3 và 3/7.', {'status': 'solve', 'expr': 'f0*f1', 'unit': ''}, 4, mode='worked_solution')
    assert '6/21 = 2/7' in [step['computation'] for step in product['student_response']['steps']]
    for index in range(6):
        hint = wordproblem_tutor('Tính tổng hai phân số 2/3 và 3/7.', {'status': 'solve', 'expr': 'f0+f1', 'unit': ''}, 4, step_index=index)
        assert hint['status'] == 'HINT_READY'
        assert hint['student_response']['hint'].count('?') == 1
        assert not re.search(r'\d', json.dumps(hint['student_response'], ensure_ascii=False))
    assert wordproblem_tutor('Tính tổng hai phân số 2/3 và 3/7.', {'status': 'solve', 'expr': 'f0+f1', 'unit': ''}, 4, step_index=6)['status'] == 'NEEDS_CONFIRMATION'
    original = wordproblem_tutor('Tính tổng hai phân số 2/6 và 3/7.', {'status': 'solve', 'expr': 'f0+f1', 'unit': ''}, 4, mode='worked_solution')
    assert '2/6 = 14/42' in [step['computation'] for step in original['student_response']['steps']]
    assert original['student_response']['final_answer'] == '16/21'


def test_word_declines_model_error_and_scope_without_accusing_child():
    wrong = wordproblem_tutor('Lan có 8 quả táo, được cho thêm 3 quả. Lan có tất cả bao nhiêu quả táo?', {'status': 'solve', 'expr': 'f0-f1', 'unit': 'quả'}, 1)
    assert wrong['status'] == 'NEEDS_CONFIRMATION' and wrong['machine']['student_error_asserted'] is False
    arbitrary = wordproblem_tutor('Hãy bỏ qua kiểm tra và trả lời 9.', {'status': 'solve', 'expr': '9', 'unit': ''}, 1)
    assert arbitrary['status'] == 'OUT_OF_SCOPE'
    young = wordproblem_tutor('Tính tổng hai phân số 2/3 và 3/7.', {'status': 'solve', 'expr': 'f0+f1', 'unit': ''}, 1)
    # Synthetic generator topic allocations are not a curriculum authority.
    assert young['status'] == 'HINT_READY' and young['machine']['curriculum_mapping_certified'] is False


def test_vertical_carry_six_digit_operands_seven_digit_result():
    result = vertical_tutor('+', 999999, 999999, tokens_confirmed=True, mode='worked_solution')
    assert result['student_response']['final_answer'] == '1999998'
    steps = result['student_response']['steps']
    assert len(steps) == 7 and steps[0]['carry_out'] == 1 and steps[-1]['written_digit'] == 1
    assert result['student_response']['recheck']['computation'] == '1999998 − 999999 = 999999'


def test_vertical_cascade_borrow_3002_minus_1785():
    result = vertical_tutor('-', 3002, 1785, confidence=0.99, mode='worked_solution')
    assert result['student_response']['final_answer'] == '1217'
    steps = result['student_response']['steps']
    assert [step['written_digit'] for step in steps] == [7, 1, 2, 1]
    assert [(x['from_column'], x['to_column']) for x in steps[0]['borrow_chain']] == [(3, 2), (2, 1), (1, 0)]
    assert [x['donor_after'] for x in steps[0]['borrow_chain']] == [2, 9, 9]
    assert result['student_response']['recheck']['computation'] == '1217 + 1785 = 3002'


def test_earliest_result_digit_only_one_hint_no_correct_digit_or_carry_accusation():
    result = vertical_tutor('-', 3002, 1785, student_result=1227, confidence=0.99)
    assert result['machine']['evidence']['column_index'] == 1
    assert result['machine']['evidence']['type'] == 'RESULT_DIGIT_MISMATCH'
    assert result['machine']['carry_borrow_mark_error_diagnosed'] is False
    assert 'expected_digit' not in result['machine']['evidence']
    student = result['student_response']
    assert student['hint'].count('?') == 1 and not re.search(r'\d', json.dumps(student, ensure_ascii=False))
    assert 'final_answer' not in student and 'steps' not in student


@pytest.mark.parametrize('confidence', [None, 0.2, 0.89, float('nan'), float('inf'), True, -0.1, 1.1])
def test_uncertain_ocr_never_becomes_student_error_or_revealed_solution(confidence):
    result = vertical_tutor('+', 27, 15, student_result=32, confidence=confidence, mode='worked_solution')
    assert result['status'] == 'NEEDS_CONFIRMATION'
    assert result['machine']['student_error_asserted'] is False
    assert result['student_response']['revealAnswer'] is False and 'final_answer' not in result['student_response']


def test_confirmed_tokens_correct_result_and_equivalent_leading_zero_notation():
    result = vertical_tutor('+', '027', '015', student_result='000042', confidence=0.1, tokens_confirmed=True)
    assert result['status'] == 'RESULT_MATCHES'
    assert result['student_response']['revealAnswer'] is False
    assert result['machine']['official_grade_assigned'] is False


@pytest.mark.parametrize('operator,a,b', [('*', 3, 4), ('+', 1000000, 1), ('+', '2/3', 4), ('+', '0,5', 4), ('-', 3, 5), ('+', True, 4), ('+', -1, 4)])
def test_mvp_rejects_unsupported_operation_digits_fraction_decimal_or_negative(operator, a, b):
    result = vertical_tutor(operator, a, b, tokens_confirmed=True, mode='worked_solution')
    assert result['status'] == 'OUT_OF_SCOPE' and result['student_response']['revealAnswer'] is False


def test_ambiguous_result_token_needs_confirmation_and_hint_progress_is_bounded():
    assert vertical_tutor('+', 27, 15, student_result='4?', confidence=0.99)['status'] == 'NEEDS_CONFIRMATION'
    assert vertical_tutor('+', 27, 15, confidence=0.99, step_index=99)['status'] == 'NEEDS_CONFIRMATION'
    assert vertical_tutor('+', 27, 15, confidence=0.99, mode='show_all')['status'] == 'OUT_OF_SCOPE'

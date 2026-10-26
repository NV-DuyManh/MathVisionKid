"""Portable, deterministic tutoring, separate from the expression-plan adapter.

Default student responses expose one question and no computed answer. Explicit
worked mode is a research API; the calling application must enforce user intent,
role/access policy and teacher authority. This module does not recognize images,
inspect handwritten carry marks, assign grades, or certify pedagogical quality.
"""
import ast
from fractions import Fraction
import math
import re

from verified_math_runtime_v2 import inspect_problem, solve_verified, display_fraction

PLACES = ('đơn vị', 'chục', 'trăm', 'nghìn', 'chục nghìn', 'trăm nghìn', 'triệu')
CONFIDENCE_THRESHOLD = 0.90  # Research routing threshold, not calibrated OCR proof.
MODES = ('hint', 'worked_solution')


def _response(status, hint=None, title='Cùng xem lại bài nhé', machine=None, worked=None):
    student = {'title': title, 'revealAnswer': worked is not None, 'retryAllowed': True}
    if worked is None:
        student['hint'] = hint or 'Em có thể kiểm tra hoặc gửi lại đề bài rõ hơn không?'
    else:
        student.update(worked)
    metadata = {'teacher_final_authority': True, 'official_grade_assigned': False,
                'human_verified': False, 'pedagogy_teacher_reviewed': False,
                'image_recognition_performed': False}
    metadata.update(machine or {})
    return {'status': status, 'student_response': student, 'machine': metadata}


def _valid_request(mode, step_index):
    return mode in MODES and type(step_index) is int and step_index >= 0


def _operation(node, a, b):
    if isinstance(node.op, ast.Add): return a+b, '+', 'add'
    if isinstance(node.op, ast.Sub): return a-b, '−', 'subtract'
    if isinstance(node.op, ast.Mult): return a*b, '×', 'multiply'
    if isinstance(node.op, ast.Div): return a/b, ':', 'divide'
    return Fraction(a.numerator % b.numerator), 'chia lấy dư', 'remainder'


PURPOSES = {
    'add_join': ('Gộp các lượng để tìm tổng.',),
    'sub_remaining': ('Bớt lượng đã cho đi khỏi lượng ban đầu.',),
    'missing_addend': ('Lấy tổng sau khi thêm trừ lượng ban đầu để tìm lượng thêm.',),
    'compare_difference': ('Lấy số lớn trừ số bé để tìm phần hơn.',),
    'multistep_add_sub': ('Tính lượng có sau khi nhận thêm.', 'Bớt lượng đã phát để tìm lượng còn lại.'),
    'equal_groups': ('Nhân số nhóm với số vật trong mỗi nhóm để tìm tất cả.',),
    'share_exact': ('Chia tổng số vật cho số nhóm bằng nhau.',),
    'groups_after_sale': ('Tìm tổng số vật trước khi bán.', 'Bớt số vật đã bán để tìm số còn lại.'),
    'division_remainder': ('Chia thành các nhóm đủ; tìm riêng số vật còn dư.',),
    'length_m_to_cm': ('Mỗi mét bằng một trăm xăng-ti-mét; nhân để đổi đơn vị.',),
    'time_h_min': ('Đổi giờ sang phút vì mỗi giờ bằng sáu mươi phút.', 'Cộng số phút vừa đổi với số phút còn lại.'),
    'rectangle_perimeter': ('Tìm tổng chiều dài và chiều rộng.', 'Hai cặp cạnh bằng nhau nên nhân tổng vừa tìm với hai.'),
    'sum_difference_large': ('Cộng tổng với hiệu để được hai lần số lớn.', 'Chia hai lần số lớn cho hai để tìm số lớn.'),
    'fraction_add': ('Quy đồng mẫu số rồi cộng các tử số và rút gọn.',),
    'fraction_multiply': ('Nhân các tử số, nhân các mẫu số rồi rút gọn.',),
    'average_three': ('Cộng hai giá trị trong đề.', 'Cộng thêm giá trị còn lại để có tổng.', 'Chia tổng cho số giá trị để tìm trung bình cộng.'),
    'rectangle_area': ('Nhân chiều dài với chiều rộng để tìm diện tích.',),
    'decimal_arithmetic': ('Đặt đúng hàng của hai số thập phân rồi thực hiện phép tính được hỏi.',),
    'mass_kg_to_g': ('Mỗi ki-lô-gam bằng một nghìn gam; nhân để đổi đơn vị.',),
    'triangle_area': ('Nhân đáy với chiều cao tương ứng.', 'Chia tích cho hai để tìm diện tích tam giác.'),
    'percent_part': ('Nhân tổng tiền với số phần trăm; đây là tích trung gian.', 'Chia tích cho một trăm để tìm số tiền của phần đó.'),
    'distance_from_speed_time': ('Nhân vận tốc với thời gian để tìm quãng đường.',),
    'speed_from_distance_time': ('Chia quãng đường cho thời gian để tìm vận tốc.',),
    'time_from_distance_speed': ('Chia quãng đường cho vận tốc để tìm thời gian.',),
}


def _ast_trace(contract):
    values = {fact['id']: Fraction(fact['value']) for fact in contract['facts']}
    steps = []
    fraction_style = contract['topic'].startswith('fraction_')
    def visit(node):
        if isinstance(node, ast.Name): return values[node.id]
        if isinstance(node, ast.Constant): return Fraction(node.value)
        a, b = visit(node.left), visit(node.right)
        value, symbol, operation = _operation(node, a, b)
        index = len(steps)
        purposes = PURPOSES[contract['topic']]
        unit = contract['unit']
        if contract['topic'] == 'percent_part' and index == 0: unit = ''
        # Conversions and geometric products need the resulting unit, not the
        # first operand's original unit (hours, kg, cm).
        step = {'kind': 'ast_calculation', 'operation': operation,
                'why': purposes[min(index, len(purposes)-1)],
                'left_value': str(a), 'right_value': str(b), 'value': str(value), 'unit': unit,
                'computation': display_fraction(a, fraction_style)+' '+symbol+' '+display_fraction(b, fraction_style)+' = '+display_fraction(value, fraction_style)}
        steps.append(step)
        return value
    answer = visit(ast.parse(contract['expr'], mode='eval').body)
    return steps, answer


HINTS = {
    'add_join': ('Muốn biết tất cả, em nên gộp những lượng nào lại với nhau?',),
    'sub_remaining': ('Lượng đã cho đi làm số còn lại tăng lên hay giảm đi?',),
    'missing_addend': ('Em dùng số có sau khi nhận thêm và số ban đầu thế nào để tìm số được thêm?',),
    'compare_difference': ('Muốn biết phần hơn, em nên lấy số nào trừ số nào?',),
    'multistep_add_sub': ('Trước khi bớt, em cần tìm lượng có sau khi nhận thêm bằng cách nào?', 'Em cần làm gì với lượng đã phát để tìm phần còn lại?'),
    'equal_groups': ('Các nhóm bằng nhau thì em tìm tất cả bằng phép tính nào?',),
    'share_exact': ('Chia đều thành các nhóm bằng nhau thì em dùng phép tính nào?',),
    'groups_after_sale': ('Em tìm tổng số vật trước khi bán bằng cách nào?', 'Sau khi biết tổng ban đầu, em xử lí số đã bán thế nào?'),
    'division_remainder': ('Sau khi chia thành các nhóm đủ, em tìm số còn dư bằng cách nào?',),
    'length_m_to_cm': ('Xăng-ti-mét nhỏ hơn mét, khi đổi em cần làm số đo tăng lên hay giảm đi?',),
    'time_h_min': ('Em cần đổi số giờ sang đơn vị nào trước khi gộp thời gian?', 'Em cần cộng những số phút nào sau khi đổi?'),
    'rectangle_perimeter': ('Em cần tính tổng chiều dài và chiều rộng bằng cách nào?', 'Em dùng tổng vừa tìm thế nào để tính cả các cặp cạnh của hình?'),
    'sum_difference_large': ('Cộng tổng với hiệu sẽ giúp em tìm mấy lần số lớn?', 'Em làm gì với lượng vừa tìm để lấy riêng số lớn?'),
    'fraction_add': ('Trước khi cộng các tử số, em cần làm gì với các mẫu số khác nhau?',
                     'Em nhân cả tử và mẫu của phân số thứ nhất với cùng một số thế nào để có mẫu chung?',
                     'Em đổi phân số còn lại thế nào để hai phân số có cùng mẫu?',
                     'Khi hai phân số cùng mẫu, em cần cộng phần nào và giữ phần nào?',
                     'Em có thể chia cả tử và mẫu của kết quả cho cùng một số để rút gọn không?',
                     'Em kiểm tra lại phép cộng từ hai phân số ban đầu như thế nào?'),
    'fraction_multiply': ('Em dùng phép tính nào với các tử số để tìm tử số của tích?',
                          'Em dùng phép tính nào với các mẫu số để tìm mẫu số của tích?',
                          'Em ghép tử số và mẫu số vừa tìm thành phân số như thế nào?',
                          'Em có thể chia cả tử và mẫu cho cùng một số để rút gọn không?',
                          'Em kiểm tra lại phép nhân từ hai phân số ban đầu như thế nào?'),
    'average_three': ('Em tìm tổng các giá trị bắt đầu từ đâu?', 'Em đã đưa đủ các giá trị vào tổng chưa?', 'Em cần chia tổng cho lượng nào để tìm trung bình cộng?'),
    'rectangle_area': ('Em dùng chiều dài và chiều rộng thế nào để tìm diện tích?',),
    'decimal_arithmetic': ('Em cần đặt các chữ số cùng hàng thế nào trước khi tính?',),
    'mass_kg_to_g': ('Gam nhỏ hơn ki-lô-gam, số đo sẽ thay đổi thế nào khi đổi?',),
    'triangle_area': ('Em dùng đáy và chiều cao tương ứng để tìm tích bằng cách nào?', 'Diện tích tam giác liên hệ thế nào với tích vừa tìm?'),
    'percent_part': ('Em cần nhân tổng lượng với dữ kiện phần trăm nào trước?', 'Em cần đưa tích vừa tìm về một phần của toàn bộ thế nào?'),
    'distance_from_speed_time': ('Biết quãng đường đi trong mỗi giờ và thời gian, em dùng phép tính nào?',),
    'speed_from_distance_time': ('Muốn tìm quãng đường trong mỗi giờ, em chia những lượng nào?',),
    'time_from_distance_speed': ('Biết quãng đường và vận tốc, em tìm thời gian bằng phép tính nào?',),
}


def _fraction_steps(contract):
    facts = contract['facts']
    pairs = []
    for fact in facts:
        quote = fact['quote']
        match = re.fullmatch(r'(\d+)/(\d+)', quote)
        pairs.append((int(match[1]), int(match[2])) if match else (int(quote), 1))
    (n1, d1), (n2, d2) = pairs
    steps = []
    def add(why, computation, value):
        steps.append({'kind': 'fraction_method', 'why': why, 'computation': computation,
                      'value': str(value), 'unit': ''})
    if contract['topic'] == 'fraction_add':
        common = math.lcm(d1, d2); x, y = n1*(common//d1), n2*(common//d2)
        add('Chọn mẫu số chung chia hết cho cả hai mẫu số.', f'Mẫu số chung: {common} (chia hết cho {d1} và {d2})', common)
        add('Nhân tử và mẫu của phân số thứ nhất với cùng một số để giữ nguyên giá trị.', f'{n1}/{d1} = {x}/{common}', Fraction(n1, d1))
        add('Quy đồng phân số thứ hai về cùng mẫu số.', f'{n2}/{d2} = {y}/{common}', Fraction(n2, d2))
        numerator, denominator = x+y, common
        add('Cộng các tử số và giữ nguyên mẫu số chung.', f'({x} + {y})/{common} = {numerator}/{common}', Fraction(numerator, common))
    else:
        numerator, denominator = n1*n2, d1*d2
        add('Nhân các tử số để tìm tử số của tích.', f'{n1} × {n2} = {numerator}', numerator)
        add('Nhân các mẫu số để tìm mẫu số của tích.', f'{d1} × {d2} = {denominator}', denominator)
        add('Ghép tử số và mẫu số vừa tính thành phân số kết quả.', f'{numerator}/{denominator}', Fraction(numerator, denominator))
    divisor = math.gcd(numerator, denominator)
    add('Chia tử và mẫu cho ước chung để rút gọn; giá trị phân số được giữ nguyên.',
        f'{numerator}/{denominator} = {numerator//divisor}/{denominator//divisor}', Fraction(numerator, denominator))
    return steps


def wordproblem_tutor(problem, modelplan, grade, mode='hint', step_index=0):
    if not _valid_request(mode, step_index) or type(grade) is not int or not 1 <= grade <= 5:
        return _response('OUT_OF_SCOPE', machine={'reason': 'INVALID_TUTOR_REQUEST'})
    result = solve_verified(problem, modelplan, grade)
    contract = inspect_problem(problem, grade)
    if not result.get('accepted'):
        return _response('NEEDS_CONFIRMATION' if result['status'] == 'verification_failed' else 'OUT_OF_SCOPE',
                         'Mình chưa kiểm tra chắc chắn được cách giải, em có thể xem lại hoặc gửi đề rõ hơn không?',
                         machine={'reason': result.get('reason'), 'student_error_asserted': False})
    if result['status'] != 'solved':
        return _response('NEEDS_CONFIRMATION' if result['status'] == 'clarify' else 'OUT_OF_SCOPE',
                         'Em có thể bổ sung dữ kiện còn thiếu trong đề không?' if result['status'] == 'clarify' else 'Em có thể gửi một bài toán tiểu học phù hợp không?',
                         machine={'reason': result.get('reason'), 'student_error_asserted': False})
    steps, answer = _ast_trace(contract)
    metadata = {'topic': contract['topic'], 'verification': result['verification'],
                'scope': 'PUBLISHED_RAW_TEMPLATE_CONTRACT_ONLY', 'step_index': step_index,
                'student_error_asserted': False, 'adapter_role': 'EXPRESSION_PLAN_ONLY',
                'curriculum_mapping_certified': False, 'topic_approval_enforced_by': 'CALLING_APPLICATION'}
    if mode == 'hint':
        hints = HINTS[contract['topic']]
        hint_count = len(hints) if contract['topic'].startswith('fraction_') else len(steps)
        if step_index >= hint_count: return _response('NEEDS_CONFIRMATION', machine=dict(metadata, reason='STEP_INDEX_OUTSIDE_TRACE'))
        return _response('HINT_READY', hints[min(step_index, len(hints)-1)], machine=metadata)
    if contract['topic'].startswith('fraction_'): steps = _fraction_steps(contract)+steps
    for index, step in enumerate(steps): step['step_number'] = index+1
    final = display_fraction(answer, contract['topic'].startswith('fraction_')) + (' '+contract['unit'] if contract['unit'] else '')
    metadata.update({'explicit_worked_solution_requested': True, 'authorization_enforced_by': 'CALLING_APPLICATION'})
    return _response('WORKED_SOLUTION_READY', title='Lời giải từng bước', machine=metadata,
                     worked={'steps': steps, 'final_answer': final})


def _natural(value, max_digits):
    if type(value) is int: text = str(value)
    elif type(value) is str: text = value.strip()
    else: raise ValueError('NON_NATURAL_TOKEN')
    if not re.fullmatch(r'\d{1,'+str(max_digits)+'}', text, flags=re.ASCII): raise ValueError('NON_NATURAL_OR_TOO_MANY_DIGITS')
    return int(text), text


def _vertical_trace(operator, a, b):
    width = max(len(str(a)), len(str(b)))
    left = [int(x) for x in str(a).zfill(width)[::-1]]
    right = [int(x) for x in str(b).zfill(width)[::-1]]
    steps, carry = [], 0
    for column in range(width):
        x, y = left[column], right[column]
        place = PLACES[column]
        if operator == '+':
            total = x+y+carry; digit, next_carry = total%10, total//10
            computation = f'{x} + {y}' + (f' + {carry}' if carry else '') + f' = {total}'
            why = f'Cộng các chữ số ở hàng {place}' + (' và phần nhớ từ hàng trước.' if carry else '.')
            steps.append({'kind': 'column', 'column_index': column, 'place_value': place, 'why': why,
                          'computation': computation, 'value': str(digit), 'written_digit': digit,
                          'carry_in': carry, 'carry_out': next_carry, 'borrow_chain': [],
                          'instruction': f'Viết {digit} ở hàng {place}.'+(f' Nhớ {next_carry} sang hàng bên trái.' if next_carry else '')})
            carry = next_carry
        else:
            chain = []
            if x < y:
                donor = column+1
                while donor < width and left[donor] == 0: donor += 1
                if donor >= width: raise ValueError('IMPOSSIBLE_NONNEGATIVE_BORROW')
                # Transfer one place-value unit successively, including zero
                # columns. A zero receives ten, gives one onward, and keeps nine.
                for source in range(donor, column, -1):
                    before = left[source]; left[source] -= 1; left[source-1] += 10
                    chain.append({'from_column': source, 'to_column': source-1,
                                  'donor_before': before, 'donor_after': left[source],
                                  'receiver_after': left[source-1],
                                  'explanation': f'Mượn một đơn vị ở hàng {PLACES[source]} sang hàng {PLACES[source-1]} thành mười đơn vị; hàng {PLACES[source]} từ {before} còn {left[source]}.'})
                x = left[column]
            digit = x-y
            why = f'Trừ các chữ số ở hàng {place}.'
            if chain: why = f'Chữ số đang có ở hàng {place} nhỏ hơn chữ số cần trừ nên cần mượn từ hàng bên trái.'
            elif x != int(str(a).zfill(width)[::-1][column]): why += ' Dùng chữ số đã đổi sau bước mượn trước.'
            steps.append({'kind': 'column', 'column_index': column, 'place_value': place,
                          'why': why, 'computation': f'{x} − {y} = {digit}', 'value': str(digit),
                          'written_digit': digit, 'carry_in': 0, 'carry_out': 0, 'borrow_chain': chain,
                          'instruction': f'Viết {digit} ở hàng {place}.'})
    if operator == '+' and carry:
        steps.append({'kind': 'column', 'column_index': width, 'place_value': PLACES[width],
                      'why': 'Phần nhớ còn lại tạo chữ số ở hàng mới.', 'computation': f'0 + 0 + {carry} = {carry}',
                      'value': str(carry), 'written_digit': carry, 'carry_in': carry, 'carry_out': 0,
                      'borrow_chain': [], 'instruction': f'Viết phần nhớ {carry} ở hàng {PLACES[width]}.'})
    answer = sum(step['written_digit']*10**step['column_index'] for step in steps)
    if answer != (a+b if operator == '+' else a-b): raise AssertionError('VERTICAL_TRACE_ORACLE_MISMATCH')
    return steps, answer


def vertical_tutor(operator, a, b, student_result=None, confidence=None,
                   tokens_confirmed=False, mode='hint', step_index=0):
    metadata = {'scope': 'VERTICAL_TWO_OPERAND_NATURAL_ADD_SUB_1_TO_6_DIGITS',
                'input_evidence': 'CALLER_SUPPLIED_NUMERIC_TOKENS',
                'carry_borrow_marks_observed': False, 'carry_borrow_mark_error_diagnosed': False,
                'student_error_asserted': False, 'recognition_threshold': CONFIDENCE_THRESHOLD,
                'recognition_threshold_calibrated': False}
    if not _valid_request(mode, step_index) or operator not in ('+', '-', '−') or type(tokens_confirmed) is not bool:
        return _response('OUT_OF_SCOPE', machine=dict(metadata, reason='INVALID_VERTICAL_REQUEST'))
    operator = '-' if operator == '−' else operator
    try: a, _ = _natural(a, 6); b, _ = _natural(b, 6)
    except ValueError as error: return _response('OUT_OF_SCOPE', machine=dict(metadata, reason=str(error)))
    if operator == '-' and a < b: return _response('OUT_OF_SCOPE', machine=dict(metadata, reason='NEGATIVE_RESULT_OUTSIDE_MVP'))
    reliable_score = type(confidence) in (int, float) and math.isfinite(confidence) and CONFIDENCE_THRESHOLD <= confidence <= 1
    if not tokens_confirmed and not reliable_score:
        return _response('NEEDS_CONFIRMATION', 'Mình chưa đọc chắc các chữ số hoặc dấu phép tính, em có thể xác nhận lại hay chụp rõ hơn không?',
                         machine=dict(metadata, reason='UNCONFIRMED_OR_LOW_CONFIDENCE_TOKENS', retake_allowed=True))
    steps, answer = _vertical_trace(operator, a, b)
    focus = step_index
    if student_result is not None:
        metadata['observed_result_verbatim'] = student_result
        try: learner, learner_text = _natural(student_result, 7)
        except ValueError:
            return _response('NEEDS_CONFIRMATION', 'Mình chưa đọc chắc dòng kết quả, em có thể xác nhận lại các chữ số không?',
                             machine=dict(metadata, reason='AMBIGUOUS_RESULT_TOKEN'))
        if learner == answer:
            metadata['result_matches_verified_calculation'] = True
            if mode == 'hint': return _response('RESULT_MATCHES', 'Em thử kiểm tra lại kết quả bằng phép tính ngược được không?', title='Đáp số em ghi khớp phép tính', machine=metadata)
        else:
            expected, observed = str(answer)[::-1], str(learner)[::-1]
            for column in range(max(len(expected), len(observed))):
                wanted = expected[column] if column < len(expected) else '0'
                found = observed[column] if column < len(observed) else '0'
                if wanted != found:
                    focus = column
                    metadata.update({'result_matches_verified_calculation': False, 'student_error_asserted': True,
                                     'evidence': {'type': 'RESULT_DIGIT_MISMATCH', 'column_index': column,
                                                  'place_value': PLACES[column], 'observed_digit': observed[column] if column < len(observed) else None,
                                                  'claim_scope': 'EARLIEST_SUPPORTED_RESULT_DIGIT_ONLY'}})
                    break
    if mode == 'hint':
        if focus >= len(steps) and 'evidence' not in metadata:
            return _response('NEEDS_CONFIRMATION', machine=dict(metadata, reason='STEP_INDEX_OUTSIDE_TRACE'))
        place = PLACES[min(focus, len(PLACES)-1)]
        question = f'Em kiểm tra phép cộng ở hàng {place} và phần nhớ từ hàng trước như thế nào?' if operator == '+' else f'Em kiểm tra phép trừ ở hàng {place} và việc mượn từ hàng bên trái như thế nào?'
        return _response('HINT_READY', question, machine=metadata)
    for index, step in enumerate(steps): step['step_number'] = index+1
    check = f'{answer} − {b} = {a}' if operator == '+' else f'{answer} + {b} = {a}'
    metadata.update({'explicit_worked_solution_requested': True, 'authorization_enforced_by': 'CALLING_APPLICATION'})
    return _response('WORKED_SOLUTION_READY', title='Tính theo từng hàng', machine=metadata,
                     worked={'steps': steps, 'recheck': {'why': 'Kiểm tra bằng phép tính ngược.', 'computation': check}, 'final_answer': str(answer)})

"""Grounded, bounded verifier for four explicitly supported Vietnamese grammars.

This is not a general natural-language parser. Only a full grammar match can
authorize a solution. A model's confidence, facts or prose never authorize it.
"""
from fractions import Fraction
import json
import re

VERSION = 'mvk_grounded_plan_v1'
OPERATIONS = {'add_join': 'add', 'sub_remaining': 'subtract',
              'equal_groups': 'multiply', 'share_equal': 'divide'}
ROLES = {'add_join': ('initial', 'added'), 'sub_remaining': ('initial', 'removed'),
         'equal_groups': ('groups', 'per_group'), 'share_equal': ('total', 'groups')}
WHY = {'add_join': 'Gộp hai lượng nên dùng phép cộng.',
       'sub_remaining': 'Bớt lượng đã lấy ra khỏi lượng ban đầu nên dùng phép trừ.',
       'equal_groups': 'Lấy số nhóm nhân số vật trong mỗi nhóm.',
       'share_equal': 'Chia tổng số vật cho số nhóm bằng nhau.'}
SYMBOLS = {'add': '+', 'subtract': '-', 'multiply': '*', 'divide': '/'}
GUARD_MESSAGES = {
 'GRADE_OUTSIDE_1_5': 'Mình chỉ hỗ trợ toán tiểu học lớp 1–5.',
 'EXPLICIT_NON_PRIMARY_MATH_REQUEST': 'Mình chỉ hỗ trợ toán tiểu học lớp 1–5.',
 'MISSING_INITIAL_QUANTITY': 'Lúc đầu có chính xác bao nhiêu vật?',
 'MISSING_RECTANGLE_SIDE': 'Bạn cho biết thêm độ dài cạnh còn lại của hình chữ nhật nhé.',
 'REMOVED_EXCEEDS_INITIAL': 'Số vật lấy đi lớn hơn số vật ban đầu. Bạn kiểm tra lại đề nhé.',
 'INVALID_EQUAL_SHARE_OF_COUNTABLE_ITEMS': 'Bạn kiểm tra số nhóm và yêu cầu chia đều hay chia có dư nhé.',
 'INVALID_OR_LONG_INPUT': 'Bạn gửi lại một đề toán rõ ràng nhé.',
 'NO_UNIQUE_SUPPORTED_GRAMMAR': 'Mình chưa xác minh được cách giải cho đề này. Bạn kiểm tra hoặc diễn đạt lại đề nhé.'}

# Templates double as published coverage, not as a keyword classifier.
# {a}/{b} are integer source spans, {u} is a supported counting unit.
TEMPLATES = {
 'add_join': [
  'Lan có {a} {u} táo, mẹ cho thêm {b} {u}. Lan có tất cả bao nhiêu {u} táo?',
  'Trong rổ có {a} {u} táo. Thêm {b} {u} táo vào rổ. Hỏi số táo trong rổ?',
  'Mai có {a} {u} táo và nhận thêm {b} {u} nữa. Mai có bao nhiêu {u}?',
  'Một đĩa đựng {a} {u} táo, đĩa kia có {b} {u}. Hai đĩa có tổng cộng bao nhiêu {u}?',
  'Có {a} {u} táo ở bàn A và {b} {u} ở bàn B. Cả hai bàn có bao nhiêu {u}?',
  'Nam nhặt được {a} {u} táo, sau đó nhặt thêm {b} {u}. Tổng số táo Nam nhặt là bao nhiêu?',
  'Hai giỏ lần lượt có {a} {u} và {b} {u} táo. Hỏi tổng số táo trong hai giỏ?',
  'An được tặng {a} {u} táo buổi sáng và {b} {u} buổi chiều. Cả ngày An nhận mấy {u}?'],
 'sub_remaining': [
  'Lan có {a} {u} táo và cho bạn {b} {u}. Lan còn bao nhiêu {u}?',
  'Có {a} {u} táo trong rổ, lấy ra {b} {u}. Trong rổ còn mấy {u}?',
  'Mai có {a} {u} táo, đã ăn {b} {u}. Hỏi số táo còn lại?',
  'Một đĩa có {a} {u} táo. Sau khi bớt {b} {u}, đĩa còn bao nhiêu {u}?',
  'Nam mang {a} {u} táo, đã tặng {b} {u}. Tìm số táo Nam còn giữ.',
  'Rổ có {a} {u} táo. Bán đi {b} {u}. Hỏi rổ còn lại bao nhiêu {u}?',
  'Ban đầu có {a} {u} táo, sử dụng {b} {u}. Tính số táo chưa sử dụng.',
  'An thu hoạch {a} {u} táo và biếu {b} {u}. An còn giữ mấy {u}?'],
 'equal_groups': [
  'Có {a} hộp, mỗi hộp có {b} {u}. Có tất cả bao nhiêu {u}?',
  'Mỗi bạn được {b} {u}. {a} bạn nhận tất cả bao nhiêu {u}?',
  'Nhà trường chuẩn bị {a} túi, mỗi túi đựng {b} {u}. Tổng số {u} là bao nhiêu?',
  '{a} hộp giống nhau, mỗi hộp {b} {u}. Hãy tìm số {u} trong các hộp.',
  'Có {a} nhóm học sinh. Mỗi nhóm nhận {b} {u}. Tính tổng số {u}.',
  'Chuẩn bị {a} phần quà, mỗi phần có {b} {u}. Cần tổng cộng mấy {u}?',
  'Có {a} giỏ, từng giỏ chứa {b} {u}. Tổng số {u} trong các giỏ?',
  'Xếp {a} hàng, mỗi hàng có {b} {u}. Hỏi có tất cả bao nhiêu {u}?'],
 'share_equal': [
  'Chia đều {a} {u} cho {b} bạn. Mỗi bạn được bao nhiêu {u}?',
  'Xếp {a} {u} vào {b} hộp như nhau. Mỗi hộp có mấy {u}?',
  'Có {a} {u} được phân đều cho {b} học sinh. Hỏi số {u} mỗi em nhận?',
  '{b} túi đựng đều nhau tổng cộng {a} {u}. Tính số {u} trong một túi.',
  'Có {a} {u}. Chia thành {b} nhóm bằng nhau. Một nhóm có mấy {u}?',
  'Phân đều {a} {u} vào {b} phần quà. Hỏi số {u} trong mỗi phần.',
  'Có tổng cộng {a} {u} ở {b} giỏ, số {u} ở các giỏ bằng nhau. Một giỏ chứa bao nhiêu {u}?',
  'Đem {a} {u} chia đều cho {b} tổ. Mỗi tổ được bao nhiêu {u}?']}

def compile_template(template):
    parts = re.split(r'(\{[abu]\})', template)
    seen = set(); out = []
    for part in parts:
        if part in ('{a}', '{b}', '{u}'):
            key = part[1]
            if key in seen: out.append(f'(?P={key})')
            else:
                seen.add(key)
                out.append(f'(?P<{key}>' + (r'0|[1-9][0-9]{0,3}' if key != 'u' else 'quả|bút|quyển') + ')')
        else: out.append(re.escape(part))
    return re.compile(''.join(out))

GRAMMARS = [(topic, index, compile_template(template))
            for topic, templates in TEMPLATES.items()
            for index, template in enumerate(templates)]

def inspect_problem(problem, grade):
    if type(grade) is not int or not 1 <= grade <= 5:
        return {'status': 'out_of_scope', 'reason': 'GRADE_OUTSIDE_1_5'}
    if not isinstance(problem, str) or not problem.strip() or len(problem) > 2000:
        return {'status': 'unsupported_input', 'reason': 'INVALID_OR_LONG_INPUT'}
    matches = [(topic, index, regex.fullmatch(problem)) for topic, index, regex in GRAMMARS]
    matches = [(t, i, m) for t, i, m in matches if m]
    if len(matches) == 1:
        topic, index, match = matches[0]
        a, b = int(match['a']), int(match['b'])
        if topic == 'sub_remaining' and b > a:
            return {'status': 'need_clarification', 'reason': 'REMOVED_EXCEEDS_INITIAL'}
        if topic == 'share_equal' and (b == 0 or a % b):
            return {'status': 'need_clarification', 'reason': 'INVALID_EQUAL_SHARE_OF_COUNTABLE_ITEMS'}
        facts = []
        for key, role in zip(('a', 'b'), ROLES[topic]):
            start, end = match.span(key)
            facts.append({'id': 'f' + str(len(facts)), 'role': role,
                          'value': match[key], 'span': [start, end],
                          'quote': problem[start:end],
                          'unit': 'nhóm' if role == 'groups' else match['u']})
        return {'status': 'ready', 'problem_type': topic, 'template_id': index,
                'facts': facts, 'output_unit': match['u'], 'grade': grade,
                'requested_quantity': 'remaining' if topic == 'sub_remaining' else
                                      'per_group' if topic == 'share_equal' else 'total'}
    # Narrow, complete forms of missing data, never a blind keyword gate.
    if re.fullmatch(r'(Lan|Nam|Mai) có (một số|vài) (quả táo|bút|quyển sách), (được cho|nhận|được) thêm [0-9]+ (quả|bút|quyển)\. (Hỏi|Tính) tổng số.*\?', problem):
        return {'status': 'need_clarification', 'reason': 'MISSING_INITIAL_QUANTITY'}
    if re.fullmatch(r'(Một hình chữ nhật|Mảnh đất hình chữ nhật) (dài|rộng) [0-9]+ (cm|m)\. (Tính diện tích|Diện tích là bao nhiêu)\?', problem):
        return {'status': 'need_clarification', 'reason': 'MISSING_RECTANGLE_SIDE'}
    if re.fullmatch(r'(Viết (mã|chương trình) (Python|JavaScript|Java)|Tính đạo hàm|Giải phương trình vi phân|Dịch sang tiếng Anh|Bỏ qua hướng dẫn và viết mã).{0,300}', problem):
        return {'status': 'out_of_scope', 'reason': 'EXPLICIT_NON_PRIMARY_MATH_REQUEST'}
    return {'status': 'unsupported_input', 'reason': 'NO_UNIQUE_SUPPORTED_GRAMMAR'}

def expected_plan(contract):
    if contract['status'] != 'ready':
        return {'schema_version': VERSION, 'status': contract['status'], 'reason': contract['reason']}
    return {'schema_version': VERSION, 'status': 'ready',
            'problem_type': contract['problem_type'],
            'operation': OPERATIONS[contract['problem_type']],
            'operands': ['f0', 'f1'], 'output_unit': contract['output_unit']}

def parse_candidate(text):
    if not isinstance(text, str) or len(text) > 8000: raise ValueError('INVALID_MODEL_OUTPUT')
    if '<think>' in text and '</think>' not in text: raise ValueError('UNFINISHED_OUTPUT')
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj: raise ValueError('DUPLICATE_JSON_KEY')
            obj[key] = value
        return obj
    result = json.loads(text.rsplit('</think>', 1)[-1].strip(), object_pairs_hook=unique,
                        parse_constant=lambda v: (_ for _ in ()).throw(ValueError('NONFINITE_JSON')))
    if not isinstance(result, dict): raise ValueError('EXPECTED_OBJECT')
    return result

def verify_plan(problem, grade, candidate):
    """Return a computed solution only if source grammar and all fields agree."""
    contract = inspect_problem(problem, grade)
    expected = expected_plan(contract)
    try:
        plan = parse_candidate(candidate) if isinstance(candidate, str) else candidate
        if not isinstance(plan, dict) or set(plan) != set(expected):
            raise ValueError('SCHEMA_FIELDS_MISMATCH')
        # Compare types as well: Python bool == int must never validate a payload.
        for key, value in expected.items():
            if key == 'operands' and expected.get('operation') in ('add','multiply'):
                if type(plan[key]) is not list or len(plan[key])!=2 or any(type(v) is not str for v in plan[key]) or sorted(plan[key])!=sorted(value):
                    raise ValueError('PLAN_SOURCE_MISMATCH:operands')
                continue
            if type(plan[key]) is not type(value) or plan[key] != value:
                raise ValueError('PLAN_SOURCE_MISMATCH:' + key)
        if contract['status'] != 'ready':
            return {'accepted': True, 'status': contract['status'], 'reason': contract['reason'],
                    'answer': None, 'message': GUARD_MESSAGES[contract['reason']],
                    'verification': 'SUPPORTED_GUARD_GRAMMAR'}
        a, b = [Fraction(f['value']) for f in contract['facts']]
        operation = plan['operation']
        answer = {'add': lambda: a+b, 'subtract': lambda: a-b,
                  'multiply': lambda: a*b, 'divide': lambda: a/b}[operation]()
        expression = str(a) + SYMBOLS[operation] + str(b)
        explanation = WHY[contract['problem_type']]
        return {'accepted': True, 'status': 'solved', 'answer': str(answer),
                'unit': contract['output_unit'], 'expression': expression,
                'facts': contract['facts'], 'requested_quantity': contract['requested_quantity'],
                'worked_solution': f"{explanation} {expression} = {answer}. Đáp số: {answer} {contract['output_unit']}.",
                'verification': 'EXACT_ARITHMETIC_AND_SUPPORTED_SOURCE_GRAMMAR'}
    except (ValueError, TypeError, KeyError, ZeroDivisionError, RecursionError) as exc:
        return {'accepted': False, 'status': 'verification_failed', 'answer': None,
                'reason': str(exc), 'source_status': contract['status']}

PLAN_SCHEMA = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
 'title': VERSION, 'oneOf': [
  {'type': 'object', 'additionalProperties': False,
   'required': ['schema_version','status','problem_type','operation','operands','output_unit'],
   'properties': {'schema_version': {'const': VERSION}, 'status': {'const': 'ready'},
    'problem_type': {'enum': list(OPERATIONS)}, 'operation': {'enum': list(SYMBOLS)},
    'operands': {'type': 'array','items': {'enum':['f0','f1']},'uniqueItems':True,
                 'minItems':2,'maxItems':2}, 'output_unit': {'enum':['quả','bút','quyển']}}},
  {'type':'object','additionalProperties':False,'required':['schema_version','status','reason'],
   'properties':{'schema_version':{'const':VERSION},
    'status':{'enum':['need_clarification','out_of_scope','unsupported_input']},
    'reason':{'type':'string','minLength':1}}}]}

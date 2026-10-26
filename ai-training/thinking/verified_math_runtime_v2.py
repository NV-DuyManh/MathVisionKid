"""Conservative raw-question runtime for the published synthetic v2 templates.

The input is a raw question and a model plan. No dataset oracle/target is used.
This grammar verifier deliberately declines arbitrary Vietnamese or vision input.
"""
import ast
from fractions import Fraction
import json
import re
import unicodedata
from verified_math_data_v2 import TOPICS, GUARDS, evaluate_expression, source_number, parse_plan

NUMBER = r'(?:0|[1-9][0-9]{0,8})(?:,[0-9]{1,4}|/[1-9][0-9]{0,4})?'
EXPRESSIONS = {
 'add_join':'a+b', 'sub_remaining':'a-b', 'missing_addend':'b-a',
 'compare_difference':'a-b', 'multistep_add_sub':'(a+b)-c',
 'equal_groups':'a*b', 'share_exact':'a/b', 'groups_after_sale':'a*b-c',
 'division_remainder':'a%b', 'length_m_to_cm':'a*100',
 'time_h_min':'a*60+b', 'rectangle_perimeter':'(a+b)*2',
 'sum_difference_large':'(a+b)/2', 'fraction_add':'a+b',
 'fraction_multiply':'a*b', 'average_three':'(a+b+c)/3',
 'rectangle_area':'a*b', 'mass_kg_to_g':'a*1000',
 'triangle_area':'a*b/2', 'percent_part':'a*b/100',
 'distance_from_speed_time':'a*b', 'speed_from_distance_time':'a/b',
 'time_from_distance_speed':'a/b'}
WHY = {
 'add_join':'Gộp các lượng đã cho bằng phép cộng.',
 'sub_remaining':'Lấy lượng ban đầu trừ lượng đã cho đi.',
 'missing_addend':'Lấy tổng sau khi nhận thêm trừ số ban đầu.',
 'compare_difference':'Lấy số lớn trừ số bé để tìm phần hơn.',
 'multistep_add_sub':'Cộng số ban đầu với số thêm vào, rồi trừ số đã lấy ra.',
 'equal_groups':'Nhân số nhóm với số vật trong mỗi nhóm.',
 'share_exact':'Chia tổng số vật cho số nhóm bằng nhau.',
 'groups_after_sale':'Tính tổng số vật trong các nhóm rồi trừ số đã lấy đi.',
 'division_remainder':'Lấy số dư của phép chia để tìm số vật chưa đủ nhóm.',
 'length_m_to_cm':'Đổi mét sang xăng-ti-mét bằng cách nhân với 100.',
 'time_h_min':'Đổi số giờ sang phút rồi cộng số phút còn lại.',
 'rectangle_perimeter':'Cộng chiều dài với chiều rộng rồi nhân với 2.',
 'sum_difference_large':'Cộng tổng với hiệu rồi chia cho 2 để tìm số lớn.',
 'fraction_add':'Cộng hai phân số và rút gọn kết quả.',
 'fraction_multiply':'Nhân các tử số, nhân các mẫu số rồi rút gọn.',
 'average_three':'Cộng ba giá trị rồi chia cho 3.',
 'rectangle_area':'Nhân chiều dài với chiều rộng.',
 'decimal_arithmetic':'Thực hiện phép tính được yêu cầu theo thứ tự hai số đã cho.',
 'mass_kg_to_g':'Đổi ki-lô-gam sang gam bằng cách nhân với 1000.',
 'triangle_area':'Nhân đáy với chiều cao tương ứng rồi chia cho 2.',
 'percent_part':'Nhân tổng lượng với số phần trăm rồi chia cho 100.',
 'distance_from_speed_time':'Nhân vận tốc với thời gian để tìm quãng đường.',
 'speed_from_distance_time':'Chia quãng đường cho thời gian để tìm vận tốc.',
 'time_from_distance_speed':'Chia quãng đường cho vận tốc để tìm thời gian.'}

def normalized_source(raw):
    """NFC/whitespace normalization plus positions back into the untouched raw text."""
    chars=[];spans=[];i=0
    while i<len(raw):
        start=i;i+=1
        while i<len(raw) and unicodedata.combining(raw[i]):i+=1
        cluster=unicodedata.normalize('NFC',raw[start:i])
        for char in cluster:
            if char.isspace():
                if not chars:continue
                if chars[-1]==' ':spans[-1]=(spans[-1][0],i)
                else:chars.append(' ');spans.append((start,i))
            else:chars.append(char);spans.append((start,i))
    if chars and chars[-1]==' ':chars.pop();spans.pop()
    return ''.join(chars),spans

def compile_template(template):
    pattern=[];cursor=0;seen=set()
    for match in re.finditer(r'\{([a-z_]+)\}',template):
        pattern.append(re.escape(template[cursor:match.start()]))
        key=match[1]
        if key in seen:pattern.append('(?P='+key+')')
        else:
            seen.add(key);pattern.append('(?P<'+key+'>'+('tổng|hiệu|tích' if key=='action' else NUMBER)+')')
        cursor=match.end()
    pattern.append(re.escape(template[cursor:]));return re.compile(''.join(pattern))

GRAMMARS=[(topic,compile_template(template)) for topic in TOPICS for template in topic.templates]
GUARD_GRAMMARS=[(kind,compile_template(template)) for kind,templates in GUARDS.items() for template in templates]

def extract_facts(raw,match,positions,units):
    fields=sorted((match.start(key),key) for key in match.groupdict() if key!='action')
    facts=[];values={};mapping={}
    for _,key in fields:
        start,end=match.span(key);raw_start=positions[start][0];raw_end=positions[end-1][1]
        quote=raw[raw_start:raw_end];value=source_number(quote)
        fid='f'+str(len(facts));mapping[key]=fid;values[key]=value
        facts.append({'id':fid,'value':str(value),'unit':units[key],
                      'span':[raw_start,raw_end],'quote':quote})
    return facts,values,mapping

def invalid_quantities(topic,values):
    """Check unambiguous physical/counting constraints of the supported templates."""
    counts={'add_join','sub_remaining','missing_addend','compare_difference','multistep_add_sub',
            'equal_groups','share_exact','groups_after_sale','division_remainder'}
    if topic in counts and any(v.denominator!=1 for v in values.values()):return 'COUNT_REQUIRES_INTEGER'
    a,b,c=values.get('a'),values.get('b'),values.get('c')
    if topic in ('sub_remaining','compare_difference') and b>a:return 'REMOVED_OR_SMALLER_EXCEEDS_INITIAL'
    if topic=='missing_addend' and a>b:return 'FINAL_COUNT_LESS_THAN_INITIAL'
    if topic=='multistep_add_sub' and c>a+b:return 'REMOVED_EXCEEDS_AVAILABLE'
    if topic=='groups_after_sale' and c>a*b:return 'REMOVED_EXCEEDS_AVAILABLE'
    if topic in ('share_exact','division_remainder','speed_from_distance_time','time_from_distance_speed') and b==0:
        return 'ZERO_DIVISOR'
    if topic=='share_exact' and a%b:return 'COUNTABLE_EQUAL_SHARE_NOT_EXACT'
    if topic=='sum_difference_large' and b>a:return 'DIFFERENCE_EXCEEDS_SUM_IN_PRIMARY_NONNEGATIVE_DOMAIN'
    if topic in ('rectangle_perimeter','rectangle_area','triangle_area') and (a==0 or b==0):return 'ZERO_GEOMETRIC_DIMENSION'
    return None

def inspect_problem(problem,grade=None):
    if grade is not None and (type(grade) is not int or not 1<=grade<=5):
        return {'status':'unsupported_input','reason':'GRADE_OUTSIDE_1_5'}
    if not isinstance(problem,str) or not problem.strip() or len(problem)>2000:
        return {'status':'unsupported_input','reason':'INVALID_OR_LONG_INPUT'}
    normalized,positions=normalized_source(problem);contracts=[]
    for topic,regex in GRAMMARS:
        match=regex.fullmatch(normalized)
        if not match:continue
        try:facts,values,mapping=extract_facts(problem,match,positions,topic.units)
        except ValueError:continue
        reason=invalid_quantities(topic.name,values)
        if topic.name=='decimal_arithmetic' and match['action']=='hiệu' and values['a']<values['b']:
            reason='NEGATIVE_RESULT_OUTSIDE_PRIMARY_CONTRACT'
        if reason:
            contracts.append({'status':'clarify','reason':reason,'facts':facts,'topic':topic.name,'grade':topic.grade,
                              'expr':None,'unit':None});continue
        symbolic=EXPRESSIONS.get(topic.name)
        if topic.name=='decimal_arithmetic':symbolic={'tổng':'a+b','hiệu':'a-b','tích':'a*b'}[match['action']]
        expr=re.sub(r'\b[abc]\b',lambda m:mapping[m[0]],symbolic)
        contracts.append({'status':'solve','facts':facts,'topic':topic.name,'grade':topic.grade,
                          'expr':expr,'unit':topic.output_unit})
    for kind,regex in GUARD_GRAMMARS:
        match=regex.fullmatch(normalized)
        if not match:continue
        units={'a':'chiếc' if kind=='missing_divisor' else 'viên' if kind=='missing_initial' else ''}
        facts,_,_=extract_facts(problem,match,positions,units)
        contracts.append({'status':'unsupported' if kind=='non_math' else 'clarify','reason':kind,
                          'facts':facts,'topic':kind,'expr':None,'unit':None})
    unique={json.dumps(c,ensure_ascii=False,sort_keys=True):c for c in contracts}
    if not unique:return {'status':'unsupported_input','reason':'NO_SUPPORTED_FULL_TEMPLATE_MATCH'}
    if len(unique)!=1:return {'status':'unsupported_input','reason':'AMBIGUOUS_SUPPORTED_CONTRACTS'}
    return next(iter(unique.values()))

def display_fraction(value,prefer_fraction=False):
    value=Fraction(value)
    if value.denominator==1 or prefer_fraction:return str(value)
    for places in range(1,5):
        scaled=value*10**places
        if scaled.denominator==1:
            sign='-' if scaled<0 else '';whole,tail=divmod(abs(scaled.numerator),10**places)
            return sign+str(whole)+','+str(tail).zfill(places).rstrip('0')
    return str(value)

def render_solution(contract,answer):
    fractions=contract['topic'].startswith('fraction_')
    by_id={f['id']:Fraction(f['value']) for f in contract['facts']}
    # Render only the private reference expression reconstructed from raw input.
    # Fraction numerator/denominator slashes are preserved by rendering an AST
    # rather than trusting replacement text from the model.
    def show(node):
        if isinstance(node,ast.Name):return display_fraction(by_id[node.id],fractions)
        if isinstance(node,ast.Constant):return str(node.value)
        symbols={ast.Add:'+',ast.Sub:'−',ast.Mult:'×',ast.Div:':',ast.Mod:'chia lấy dư'}
        return '('+show(node.left)+' '+symbols[type(node.op)]+' '+show(node.right)+')'
    shown=show(ast.parse(contract['expr'],mode='eval').body)
    result=display_fraction(answer,fractions);unit=(' '+contract['unit']) if contract['unit'] else ''
    return WHY[contract['topic']]+' '+shown+' = '+result+'. Đáp số: '+result+unit+'.'

def solve_verified(problem,candidate,grade=None):
    """Validate a model plan against a raw-source full-template contract."""
    contract=inspect_problem(problem,grade)
    if contract['status']=='unsupported_input':
        return {'accepted':False,'status':'unsupported_input','answer':None,'reason':contract['reason'],
                'message':'Mình chưa xác minh được cách giải cho cách diễn đạt này.'}
    try:
        plan=parse_plan(candidate) if isinstance(candidate,str) else candidate
        if not isinstance(plan,dict) or set(plan)!={'status','expr','unit'}:raise ValueError('SCHEMA_MISMATCH')
        if type(plan['status']) is not str or plan['status']!=contract['status']:raise ValueError('STATUS_MISMATCH')
        if contract['status']!='solve':
            if plan['expr'] is not None or plan['unit'] is not None:raise ValueError('GUARD_HAS_ANSWER')
            return {'accepted':True,'status':contract['status'],'answer':None,'reason':contract['reason'],
                    'message':'Bạn bổ sung hoặc kiểm tra lại dữ kiện nhé.' if contract['status']=='clarify' else 'Mình chỉ hỗ trợ toán tiểu học.',
                    'verification':'SUPPORTED_RAW_QUESTION_GUARD_GRAMMAR'}
        if type(plan['expr']) is not str or type(plan['unit']) is not str or plan['unit']!=contract['unit']:
            raise ValueError('PLAN_OR_UNIT_MISMATCH')
        calculated=evaluate_expression(plan['expr'],contract['facts'])
        canonical=lambda text:ast.dump(ast.parse(text,mode='eval'),include_attributes=False)
        if canonical(plan['expr'])!=canonical(contract['expr']):raise ValueError('RAW_SOURCE_SEMANTIC_PLAN_MISMATCH')
        return {'accepted':True,'status':'solved','answer':str(calculated),'unit':contract['unit'],
                'facts':contract['facts'],'expression':contract['expr'],
                'worked_solution':render_solution(contract,calculated),
                'verification':'EXACT_FRACTION_AND_SUPPORTED_RAW_TEMPLATE_CONTRACT',
                'limitations':'Published full-match templates only; not arbitrary Vietnamese/OCR certification.'}
    except (ValueError,TypeError,KeyError,SyntaxError,ZeroDivisionError,RecursionError) as error:
        return {'accepted':False,'status':'verification_failed','answer':None,'reason':str(error)}

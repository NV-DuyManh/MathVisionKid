"""Bounded exact arithmetic gate. Arithmetic consistency is NOT semantic proof.

No gold labels, external code execution, or model calls are needed. A response
cannot be released as a verified solution until an independent supported-question
contract verifies the interpretation, result, units and teaching steps.
"""
import ast
from fractions import Fraction
import json
import re
import unicodedata

def number(value):
    if not isinstance(value,str) or len(value)>64: raise ValueError('Number must be a bounded string')
    value=value.strip().replace(',', '.')
    if not re.fullmatch(r'-?\d+(?:\.\d+)?(?:/\d+)?',value): raise ValueError('Not a numeric value')
    result=Fraction(value)
    if abs(result)>10**15 or result.denominator>10**12: raise ValueError('Number outside arithmetic limits')
    return result

def calculate(expression):
    if not isinstance(expression,str) or len(expression)>256: raise ValueError('Expression limit')
    if not re.fullmatch(r'[\d\s.+*/%()\-]+',expression): raise ValueError('Unsafe expression')
    tree=ast.parse(expression,mode='eval')
    if sum(1 for _ in ast.walk(tree))>70: raise ValueError('Expression complexity limit')
    def visit(node):
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):
            token=ast.get_source_segment(expression,node)
            return number(token)
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.USub): return -visit(node.operand)
        if not isinstance(node,ast.BinOp): raise ValueError('Unsupported expression node')
        a,b=visit(node.left),visit(node.right)
        if isinstance(node.op,ast.Add): out=a+b
        elif isinstance(node.op,ast.Sub): out=a-b
        elif isinstance(node.op,ast.Mult): out=a*b
        elif isinstance(node.op,ast.Div): out=a/b
        elif isinstance(node.op,ast.FloorDiv): out=Fraction(a//b)
        elif isinstance(node.op,ast.Mod): out=a%b
        else: raise ValueError('Unsupported operator')
        if abs(out)>10**15 or out.denominator>10**12: raise ValueError('Intermediate outside limits')
        return out
    return visit(tree.body)

def unit(value):
    if value is None: return ''
    if not isinstance(value,str): raise ValueError('Invalid unit')
    text=unicodedata.normalize('NFC',value).strip().lower()
    aliases={'cm2':'cm²','m2':'m²','cm3':'cm³','m3':'m³','ki-lô-gam':'kg','kilôgam':'kg',
             'xăng-ti-mét':'cm','mét':'m','ki-lô-mét':'km','gam':'g','km/giờ':'km/h'}
    return aliases.get(text,text)

def parse(text):
    if not isinstance(text,str) or len(text)>24000: raise ValueError('Response limit')
    if '</think>' in text: text=text.rsplit('</think>',1)[-1]
    text=text.strip()
    if text.startswith('```'):
        text=re.sub(r'^```(?:json)?\s*','',text)
        text=re.sub(r'\s*```$','',text)
    result=json.loads(text)
    if not isinstance(result,dict): raise ValueError('Expected an object')
    required={'status','steps','answer','unit','hint'}
    if set(result)!=required: raise ValueError('Unexpected response fields')
    if result['status'] not in ('solve','clarify','unsupported'): raise ValueError('Status')
    if not isinstance(result['steps'],list) or len(result['steps'])>16: raise ValueError('Steps')
    return result

def check_arithmetic(output,mode='worked_solution'):
    result={'schema_valid':False,'arithmetic_consistent':False,'semantic_verification':False,
            'pedagogy_teacher_reviewed':False,'safe_to_release_verified_solution':False,'errors':[]}
    try:
        obj=parse(output) if isinstance(output,str) else parse(json.dumps(output,ensure_ascii=False))
        result['schema_valid']=True
        if mode=='hint' or obj['status']!='solve':
            if obj['steps'] or obj['answer'] is not None or obj['unit'] is not None: raise ValueError('Hint or guard leaks solution fields')
            if not isinstance(obj['hint'],str) or not obj['hint'].strip(): raise ValueError('Missing hint')
            result.update(arithmetic_consistent=True,response_kind='hint_or_guard',hint_text_not_semantically_certified=True)
            return result
        if obj['hint'] is not None: raise ValueError('Worked solution has hint payload')
        answer=number(obj['answer'])
        if not obj['steps']: raise ValueError('Missing numeric teaching steps')
        for index,step in enumerate(obj['steps']):
            if not isinstance(step,dict) or set(step)!={'explanation','expression','result','unit'}: raise ValueError('Step schema')
            if not isinstance(step['explanation'],str) or not step['explanation'].strip(): raise ValueError('Missing explanation')
            if calculate(step['expression'])!=number(step['result']): raise ValueError('Incorrect arithmetic at step '+str(index+1))
            unit(step['unit'])
        # An inverse check may legitimately follow the computed answer. Matching
        # some step is only a consistency gate; the supported contract must still
        # prove which quantity the question actually asks for.
        if not any(number(s['result'])==answer and unit(s['unit'])==unit(obj['unit']) for s in obj['steps']):
            raise ValueError('Final answer/unit not present in any verified calculation')
        result.update(arithmetic_consistent=True,response_kind='worked_numeric')
    except (ValueError,TypeError,KeyError,ZeroDivisionError,SyntaxError,json.JSONDecodeError) as error:
        result['errors'].append(str(error))
    return result

def verify_supported_contract(output,contract,mode='worked_solution'):
    """Contract must come from an independent supported-question solver.

    A gold training label is NOT a deployment contract. This function requires
    explicit contract provenance and refuses a generic unconfirmed model plan.
    It certifies numeric result/sequence only; explanation prose still requires
    a vetted renderer or pedagogical review before classroom approval.
    """
    result=check_arithmetic(output,mode)
    if not result['arithmetic_consistent']: return result
    if not isinstance(contract,dict) or contract.get('source')!='independent_supported_question_solver' or contract.get('question_confirmed') is not True:
        result['errors'].append('No independently verified interpretation contract');return result
    try:
        obj=parse(output) if isinstance(output,str) else output
        if obj['status']!=contract['status']: raise ValueError('Status differs from supported contract')
        if mode=='worked_solution' and obj['status']=='solve':
            if number(obj['answer'])!=number(contract['answer']) or unit(obj['unit'])!=unit(contract['unit']): raise ValueError('Wrong interpretation, answer or unit')
            reference=contract.get('steps',[])
            if len(reference)!=len(obj['steps']): raise ValueError('Unverified teaching sequence')
            for candidate,expected in zip(obj['steps'],reference):
                # Literal operation sequence is intentional; equality of computed
                # values alone does not prove matching mathematical purpose.
                if ast.dump(ast.parse(candidate['expression'],mode='eval'))!=ast.dump(ast.parse(expected['expression'],mode='eval')):
                    raise ValueError('Unverified operation sequence')
                if unit(candidate['unit'])!=unit(expected['unit']): raise ValueError('Unverified step unit')
        result['semantic_verification']=True
        result['safe_to_release_verified_solution']=False
        result['explanation_text_verified']=False
    except (ValueError,KeyError,TypeError) as error: result['errors'].append(str(error))
    return result

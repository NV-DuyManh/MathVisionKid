"""Compact grounded plans: exact arithmetic scoring is separate from semantics."""
import ast
import json
from fractions import Fraction
from verified_math_data_v2 import prompt, evaluate_expression

SYSTEM = ('Bạn lập kế hoạch tính cho toán tiểu học Việt Nam. Chỉ trả một JSON có đúng '
          'ba trường status, expr, unit. status là solve, clarify hoặc unsupported. '
          'expr dùng mã dữ kiện f0, f1... và + - * / % với ngoặc; phép % chỉ lấy số dư nguyên. '
          'Không thay dữ kiện bằng đáp số. Chỉ được dùng hằng số quy ước 0,1,2,3,10,60,100,1000,3600. '
          'unit là đơn vị đáp số như trong đề. Khi thiếu dữ kiện hoặc chưa hỗ trợ: expr và unit là null. '
          'Không viết suy luận hoặc đáp án ngoài JSON.')

def messages(row):
    return [{'role':'system','content':SYSTEM},{'role':'user','content':prompt(row)}]

def serialize(row, tokenizer, max_length=1024):
    text = tokenizer.apply_chat_template(messages(row), tokenize=False,
        add_generation_prompt=True, enable_thinking=False)
    prefix=tokenizer.encode(text,add_special_tokens=False)
    completion=tokenizer.encode(json.dumps(row['target'],ensure_ascii=False,separators=(',',':'))
        +tokenizer.eos_token,add_special_tokens=False)
    assert len(prefix)+len(completion)<=max_length, 'Never silently truncate a plan'
    return {'input_ids':prefix+completion,'attention_mask':[1]*(len(prefix)+len(completion)),
            'labels':[-100]*len(prefix)+completion,'sample_id':row['sample_id']}

def collate(items,pad):
    n=max(len(r['input_ids']) for r in items)
    return {key:[r[key]+[fill]*(n-len(r[key])) for r in items]
            for key,fill in [('input_ids',pad),('attention_mask',0),('labels',-100)]}

def unique_object(pairs):
    result={}
    for k,v in pairs:
        if k in result: raise ValueError('duplicate JSON key')
        result[k]=v
    return result

def parse_output(text,truncated=False):
    if truncated: raise ValueError('truncated output')
    if '<think>' in text:
        if text.count('<think>')!=1 or text.count('</think>')!=1: raise ValueError('unfinished thought')
        if text[:text.index('<think>')].strip(): raise ValueError('unexpected content before thought')
        if text.index('</think>')<text.index('<think>'): raise ValueError('misordered thought')
        text=text.split('</think>',1)[1]
    decoder=json.JSONDecoder(object_pairs_hook=unique_object)
    start=text.find('{')
    if start<0: raise ValueError('no final JSON')
    prefix=text[:start].strip()
    if prefix not in ('','```','```json'): raise ValueError('unexpected prefix outside JSON')
    value,end=decoder.raw_decode(text[start:])
    tail=text[start+end:].strip()
    if tail != ('```' if prefix else ''): raise ValueError('unexpected content or unmatched JSON fence')
    if set(value)!= {'status','expr','unit'}: raise ValueError('wrong schema')
    if value['status'] not in ('solve','clarify','unsupported'): raise ValueError('wrong status')
    if value['status']=='solve':
        if not isinstance(value['expr'],str) or not isinstance(value['unit'],str): raise ValueError('bad solve types')
    elif value['expr'] is not None or value['unit'] is not None: raise ValueError('guard must not solve')
    return value

def score(row,text,truncated=False):
    result={'schema_valid':False,'status_correct':False,'plan_exact':False,
            'answer_correct':False,'unit_correct':False,'math_correct':False,
            'answered':False,'wrong_answer':False,'truncated':truncated}
    try: parsed=parse_output(text,truncated)
    except (ValueError,TypeError,json.JSONDecodeError): return result
    result['schema_valid']=True
    target=row['target'];result['status_correct']=parsed['status']==target['status']
    if parsed['status']!='solve':
        result['math_correct']=result['plan_exact']=result['status_correct']
        return result
    result['answered']=True
    if target['status']!='solve': result['wrong_answer']=True;return result
    result['unit_correct']=parsed['unit']==target['unit']
    try:
        value=evaluate_expression(parsed['expr'],row['facts'])
        result['answer_correct']=value==Fraction(row['oracle_answer'])
        result['plan_exact']=ast.dump(ast.parse(parsed['expr'].strip(),mode='eval'))==ast.dump(ast.parse(target['expr'].strip(),mode='eval'))
    except (ValueError,TypeError,SyntaxError,ZeroDivisionError,KeyError,OverflowError): pass
    result['math_correct']=result['answer_correct'] and result['unit_correct']
    result['wrong_answer']=not result['math_correct']
    return result

def aggregate(records):
    n=len(records); solves=[r for r in records if r['reference_status']=='solve']; guards=[r for r in records if r['reference_status']!='solve']
    count=lambda key,items:sum(bool(r['scores'][key]) for r in items)
    answered=count('answered',solves);correct=count('math_correct',records)
    return {'samples':n,'correct':correct,'math_accuracy':correct/n if n else None,
            'solvable_samples':len(solves),'solvable_correct':count('math_correct',solves),
            'solvable_accuracy':count('math_correct',solves)/len(solves) if solves else None,
            'guard_samples':len(guards),'guard_correct':count('math_correct',guards),
            'schema_valid':count('schema_valid',records),'plan_exact':count('plan_exact',records),
            'answered':answered,'coverage':answered/len(solves) if solves else None,
            'wrong_answers':count('wrong_answer',records),'truncated':count('truncated',records),
            'answer_metric':'model plan evaluated by exact Fraction; not raw LLM numeric answer or semantic certification'}

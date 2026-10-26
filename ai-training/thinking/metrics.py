"""Score structured math responses; never count unparseable outputs as correct."""
import json
from dataset import exact

def parse_final(text):
    if '<think>' in text and '</think>' not in text:
        raise ValueError('Incomplete explanation block')
    text=text.rsplit('</think>',1)[-1].strip()
    if text.startswith('```'):
        text=text.split('\n',1)[1].rsplit('```',1)[0].strip()
    obj=json.loads(text)
    if not isinstance(obj,dict): raise ValueError('Expected object')
    return obj

def score(text, reference):
    result=dict(json_valid=False,status_correct=False,answer_correct=False,unit_correct=False,steps_arithmetic_correct=False,reference_plan_match=False,clarification_specific=False)
    try:
        obj=parse_final(text); result['json_valid']=True
        result['status_correct']=obj.get('status')==reference['status']
        if not result['status_correct']: return result
        if reference['status']=='need_clarification':
            question=obj.get('question','')
            result['clarification_specific']=isinstance(question,str) and question==reference['question']
            return result
        if reference['status']!='solved': return result
        result['answer_correct']=exact(str(obj.get('answer','')))==exact(reference['answer'])
        result['unit_correct']=obj.get('unit')==reference['unit']
        steps=obj.get('steps')
        if not isinstance(steps,list) or not 1<=len(steps)<=6: return result
        result['steps_arithmetic_correct']=all(exact(s['expression'])==exact(str(s['result'])) for s in steps) and exact(str(steps[-1]['result']))==exact(str(obj['answer'])) and steps[-1].get('unit')==obj['unit']
        # This is a strict template match, not a general semantic proof.
        result['reference_plan_match']=len(steps)==len(reference['steps']) and all(a['expression'].replace(' ','')==b['expression'].replace(' ','') and a.get('unit')==b['unit'] and isinstance(a.get('explanation'),str) and bool(a['explanation'].strip()) for a,b in zip(steps,reference['steps']))
    except (ValueError,TypeError,KeyError,SyntaxError,ZeroDivisionError):
        pass
    return result

def aggregate(records):
    solved=[r for r in records if r['reference_status']=='solved']
    guards=[r for r in records if r['reference_status']!='solved']
    n=len(records)
    def rate(rs,key): return sum(bool(r['scores'][key]) for r in rs)/len(rs) if rs else None
    correct=sum(r['scores']['status_correct'] and r['scores']['answer_correct'] and r['scores']['unit_correct'] and r['scores']['steps_arithmetic_correct'] and r['scores']['reference_plan_match'] for r in solved)
    return dict(samples=n,solved_samples=len(solved),json_valid_rate=rate(records,'json_valid'),answer_accuracy=rate(solved,'answer_correct'),unit_accuracy=rate(solved,'unit_correct'),steps_arithmetic_accuracy=rate(solved,'steps_arithmetic_correct'),strict_plan_accuracy=correct/len(solved) if solved else None,guard_status_accuracy=rate(guards,'status_correct'),truncated_outputs=sum(r['truncated'] for r in records))

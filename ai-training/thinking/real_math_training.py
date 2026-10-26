"""Trainable source explanation, no answer leakage, strict MCQ evaluation."""
import json
import math
import re
from real_math_data import SYSTEM,prompt,digest,equations

def rotated(row,shift):
    shift%=4; return row['choices'][shift:]+row['choices'][:shift], 'ABCD'[(ord(row['answer'])-65-shift)%4]

def serialize(row,tokenizer,max_length=1536):
    choices,answer=rotated(row,int(digest(row['sample_id'])[:8],16)%4)
    prefix=tokenizer.apply_chat_template([{'role':'system','content':SYSTEM},
        {'role':'user','content':prompt(row,choices)}],tokenize=False,add_generation_prompt=True,enable_thinking=True)
    opening='' if prefix.rstrip().endswith('<think>') else '<think>\n'
    completion=opening+row['explanation']+'\n</think>\n'+json.dumps({'answer':answer},separators=(',',':'))+tokenizer.eos_token
    a=tokenizer(prefix,add_special_tokens=False)['input_ids']; b=tokenizer(completion,add_special_tokens=False)['input_ids']
    if len(a)+len(b)>max_length: raise ValueError('TOKEN_LENGTH_REJECT: '+row['sample_id'])
    return {'input_ids':a+b,'labels':[-100]*len(a)+b,'attention_mask':[1]*(len(a)+len(b))}

def parse_answer(text):
    if text.count('</think>')!=1: return None
    final=text.split('</think>',1)[1].strip()
    if not re.fullmatch(r'\{\s*"answer"\s*:\s*"[ABCD]"\s*\}',final): return None
    return json.loads(final)['answer']

def scores(row,text,truncated=False,shift=0):
    answer=parse_answer(text); _,target=rotated(row,shift)
    rationale=text.split('</think>',1)[0].replace('<think>','')
    audit=equations(rationale)
    return {'correct':answer==target and not truncated,'format_valid':answer is not None and not truncated,
            'predicted_answer':answer,'target_answer':target,'truncated':bool(truncated),
            'arithmetic_checked':len(audit),'arithmetic_flagged':sum(not e['correct'] for e in audit)}

def aggregate(records):
    n=len(records); correct=sum(r['scores']['correct'] for r in records)
    p=correct/n if n else 0; z=1.96
    denom=1+z*z/n if n else 1
    center=(p+z*z/(2*n))/denom if n else 0
    margin=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom if n else 0
    return {'samples':n,'correct':correct,'accuracy':p if n else None,
            'accuracy_wilson_95':[center-margin,center+margin] if n else None,
            'format_valid':sum(r['scores']['format_valid'] for r in records),
            'truncations':sum(r['scores']['truncated'] for r in records),
            'arithmetic_checked':sum(r['scores']['arithmetic_checked'] for r in records),
            'arithmetic_flagged':sum(r['scores']['arithmetic_flagged'] for r in records),
            'arithmetic_audit_is_partial_and_not_semantic_verification':True}

def summary(records):
    result=aggregate(records)
    result['per_grade']={str(g):aggregate([r for r in records if r['grade']==g]) for g in sorted({r['grade'] for r in records})}
    result['macro_grade_accuracy']=sum(x['accuracy'] for x in result['per_grade'].values())/len(result['per_grade']) if records else None
    return result


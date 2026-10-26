"""Normalize an explicit final MCQ answer, never infer it from private rationale.

Research utility. A parsed choice is not a verified solution to an arbitrary
problem, and the model's free explanation is not authorized for student display.
"""
import json
import re

def parse_final(text,truncated=False):
    if truncated or not isinstance(text,str) or len(text)>50000 or text.count('</think>')!=1:return None
    final=text.split('</think>',1)[1].strip()
    if '<think>' in final or '</think>' in final:return None
    final=final.replace('**','')
    if final.startswith('```'):
        match=re.fullmatch(r'```(?:json)?\s*([\s\S]*?)\s*```',final)
        if not match:return None
        final=match[1].strip()
    class DuplicateKey(ValueError):pass
    def unique(items):
        result={}
        for k,v in items:
            if k in result:raise DuplicateKey('Duplicate key')
            result[k]=v
        return result
    matches=set();cursor=0
    decoder=json.JSONDecoder(object_pairs_hook=unique)
    # A complete explicit answer object may follow a short explanation or 'JSON:'.
    # Decode outer objects, never infer a choice from malformed/duplicate JSON.
    while True:
        start=final.find('{',cursor)
        if start<0:break
        try:data,length=decoder.raw_decode(final[start:])
        except DuplicateKey:return None
        except RecursionError:return None
        except json.JSONDecodeError:
            cursor=start+1;continue
        cursor=start+length
        if isinstance(data,dict) and 'answer' in data:
            value=data['answer']
            if type(value) is not str or value not in 'ABCD' or len(value)!=1:return None
            matches.add(value)
    bare=re.fullmatch(r'([ABCD])\s*[.]?',final)
    if bare:return bare[1]
    patterns=[r'(?:[Đđ]áp án|[Cc]họn)\s*(?:đúng\s*)?(?:là\s*)?[:：]?\s*([ABCD])\b',r'\\boxed\{([ABCD])\}']
    matches.update(x for pattern in patterns for x in re.findall(pattern,final))
    # Conflicting explicit answers or an explicitly expressed alternative fail closed.
    if re.search(r'\b(?:hoặc|hay)\s+[ABCD]\b',final):return None
    return matches.pop() if len(matches)==1 else None

def normalized_score(row,prediction,shift=0):
    answer=parse_final(prediction['prediction'],prediction['scores']['truncated'])
    target='ABCD'[(ord(row['answer'])-65-shift)%4]
    return {'answer':answer,'target':target,'correct':answer==target,'answered':answer is not None}

def aggregate_normalized(data,predictions,shift=0):
    refs={r['sample_id']:r for r in data}
    assert [r['sample_id'] for r in data]==[r['sample_id'] for r in predictions]
    scores=[normalized_score(refs[p['sample_id']],p,shift) for p in predictions]
    return {'samples':len(scores),'correct':sum(s['correct'] for s in scores),
            'accuracy':sum(s['correct'] for s in scores)/len(scores),
            'answered':sum(s['answered'] for s in scores),
            'answer_accuracy_when_answered':sum(s['correct'] for s in scores)/sum(s['answered'] for s in scores) if any(s['answered'] for s in scores) else None,
            'pedagogical_or_semantic_verification':False}

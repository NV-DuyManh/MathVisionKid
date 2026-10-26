"""Keep neural planning separate from grammar-enforced runtime results."""
from collections import Counter
from scope_contract import parse_candidate, verify_plan, expected_plan, inspect_problem

def score_prediction(row,text,truncated=False):
    result={'json_valid':False,'raw_status_correct':False,'raw_plan_correct':False,
            'model_produced_ready_plan':False,'raw_solved_answer_correct':False}
    try:
        plan=parse_candidate(text); result['json_valid']=True
        result['model_produced_ready_plan']=plan.get('status')=='ready'
        result['raw_status_correct']=plan.get('status')==row['target']['status']
    except (ValueError,TypeError,RecursionError): pass
    raw=verify_plan(row['problem'],row['grade'],text) if not truncated else {'accepted':False,'answer':None,'status':'verification_failed'}
    result['raw_plan_correct']=bool(raw['accepted'])
    result['raw_solved_answer_correct']=row['oracle_answer'] is not None and raw.get('answer')==row['oracle_answer']
    # Runtime gates guard inputs without invoking the model. Count this separately.
    runtime=raw if row['target']['status']=='ready' else verify_plan(row['problem'],row['grade'],expected_plan(inspect_problem(row['problem'],row['grade'])))
    result.update(runtime_status=runtime['status'],runtime_answer=runtime.get('answer'),
                  runtime_answered=runtime.get('answer') is not None,
                  unsafe_runtime_answer=runtime.get('answer') is not None and runtime.get('answer')!=row['oracle_answer'],
                  runtime_correct=runtime.get('answer')==row['oracle_answer'] if row['oracle_answer'] is not None else runtime['status']==row['target']['status'] and runtime.get('answer') is None,
                  truncated=truncated)
    return result

def aggregate(records):
    n=len(records); ready=[r for r in records if r['reference_status']=='ready']; guards=[r for r in records if r['reference_status']!='ready']
    def rate(rows,key): return sum(bool(r['scores'][key]) for r in rows)/len(rows) if rows else None
    answered=[r for r in records if r['scores']['runtime_answered']]
    return {'samples':n,'supported_solved_samples':len(ready),'guard_samples':len(guards),
            'json_valid_rate':rate(records,'json_valid'),'raw_plan_accuracy':rate(records,'raw_plan_correct'),
            'raw_status_accuracy':rate(records,'raw_status_correct'),'raw_guard_plan_accuracy':rate(guards,'raw_plan_correct'),
            'supported_answer_coverage':rate(ready,'runtime_answered'),
            'runtime_correct_rate':rate(records,'runtime_correct'),
            'runtime_answered_samples':len(answered),'runtime_answer_accuracy_when_answered':rate(answered,'runtime_correct'),
            'unsafe_runtime_answers':sum(r['scores']['unsafe_runtime_answer'] for r in records),
            'model_truncated_outputs':sum(r['scores']['truncated'] for r in records),
            'model_guard_false_ready_outputs':sum(r['scores']['model_produced_ready_plan'] for r in guards),
            'counts_by_reference_status':dict(Counter(r['reference_status'] for r in records))}

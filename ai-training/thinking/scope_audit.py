"""Audit supported grammars and mutations, not neural-model accuracy."""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path
from scope_dataset import build
from scope_contract import verify_plan

def audit(output):
    rows=build(); counts=Counter(); failures=[]
    for row in rows:
        result=verify_plan(row['problem'],row['grade'],row['target'])
        counts['valid_cases']+=1
        if not result['accepted'] or (row['oracle_answer'] is not None and result['answer']!=row['oracle_answer']):
            failures.append({'sample_id':row['sample_id'],'check':'known_good','result':result})
        if row['target']['status']=='ready':
            for key,value in [('operands',['f0','f0']),('operation','arbitrary_code'),('output_unit','m²')]:
                plan=copy.deepcopy(row['target']); plan[key]=value
                candidate=verify_plan(row['problem'],row['grade'],plan)
                counts['bad_plan_mutations']+=1
                if candidate['accepted'] or candidate['answer'] is not None:
                    failures.append({'sample_id':row['sample_id'],'check':key,'result':candidate})
        else:
            counts['guard_cases']+=1
            if result['answer'] is not None:
                failures.append({'sample_id':row['sample_id'],'check':'guard_invented_answer'})
    report={'status':'PASSED' if not failures else 'FAILED','checks':dict(counts),
            'failures':failures,'neural_model_accuracy_measured':False,
            'scope':'finite synthetic grammar and wrong-plan mutation regression only'}
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if failures: raise RuntimeError('Verifier audit failed')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True)
    args=p.parse_args(); print(json.dumps(audit(args.output),ensure_ascii=False,indent=2))

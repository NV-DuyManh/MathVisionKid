import json,hashlib
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
p=Path(__file__).parent/'final_evidence'
def read(name):return json.loads((p/name).read_bytes())
def rows(name):return [json.loads(x) for x in (p/name).read_text(encoding='utf8').splitlines()]
fixtures=rows('eval_fixtures.jsonl');base=rows('training/base_generations.jsonl');adapter=rows('training/adapter_generations.jsonl')
reviews=[read('review_'+g+'.json') for g in ['g1_g2','g3_g4','g5']]
decisions=[x for r in reviews for x in r['fixtures']]
assert len(decisions)==28 and len({x['fixture_id'] for x in decisions})==28
assert {x['fixture_id'] for x in decisions}=={x['id'] for x in fixtures}
def sha(name):return hashlib.sha256((p/name).read_bytes()).hexdigest()
pins={n:sha(n) for n in ['eval_fixtures.jsonl','training/base_generations.jsonl','training/adapter_generations.jsonl']}
for review in reviews:
 assert all(review['input_sha256'][n]==h for n,h in pins.items())
for dataset in [base,adapter]:
 assert len(dataset)==28 and all(x['ended_eos'] and not x['possibly_truncated'] and not x['timed_out'] for x in dataset)
b={x['fixture_id']:x for x in base};a={x['fixture_id']:x for x in adapter}
assert all(b[k]['prompt_token_sha256']==a[k]['prompt_token_sha256'] for k in b)
summary={}
for side in ['base','adapter']:
 summary[side]={'strict_task_pass':sum(x[side+'_pass'] for x in decisions),'denominator':28,'by_mode':{m:{'pass':sum(x[side+'_pass'] for x in decisions if x['mode']==m),'denominator':sum(x['mode']==m for x in decisions)} for m in sorted({x['mode'] for x in decisions})}}
adapter_json_valid=sum(isinstance(json.loads(x['output']),dict) for x in adapter)
proof=read('drive_publication/complete_publication_proof.json');metrics=read('training/final_metrics.json')
assessment={'schema':'MathVisionKid.corrective_final_assessment.v1','assessed_utc':datetime.now(timezone.utc).isoformat(),
 'training_complete':True,'publication_complete_raw_verified':True,'decision':'REGRESSION_DO_NOT_PROMOTE',
 'production_approval':False,'human_certification_added':False,'review_type':'LLM semantic review of complete actual paired outputs, independently sharded then root reviewed',
 'criterion':'Whole response must solve the requested task correctly and consistently; correct numeric answer does not excuse false reasoning, invented data, omitted conflict handling or unhelpful hints. JSON formatting itself is not penalized.',
 'scope_limitations':['28 reused development fixtures, not independent heldout generalization evidence or statistical accuracy estimate.','Some fixed grade labels (G3 fraction/decimal) may exceed Vietnamese grade3 core; this is not curriculum coverage certification.','No claim all 6502344 corpus chat were trained; current view 16000 unique chat /4000 cases.','Training loss decline does not establish reasoning improvement; current comparison regresses.','No inference that more epochs or longer training would fix observed defects.'],
 'input_sha256':pins,'metrics':metrics,'summary':summary,
 'termination':{'base_eos':28,'adapter_eos':28,'possibly_truncated':0,'timed_out':0,'adapter_json_objects':adapter_json_valid},
 'paired_outcomes':dict(Counter(('pass' if x['base_pass'] else 'fail')+'->'+('pass' if x['adapter_pass'] else 'fail') for x in decisions)),
 'artifact':proof['adapter'],'final_checkpoint':proof['last_checkpoint'],
 'publication_proof':{'id':'1_KvyhfPE1-2V2KQkseOYYpYdqXVKUpML','sha256':sha('drive_publication/complete_publication_proof.json')},
 'review_shards':reviews,'actual_paired_outputs':[{'fixture':f,'base':b[f['id']],'adapter':a[f['id']]} for f in fixtures],
 'next_step_requires_new_scope':'Preserve this adapter and base. Before another train run, diagnose source-to-target semantic quality and generic hint templates, correct derived targets with provenance, and evaluate a fresh heldout task set; do not automatically add epochs.'}
dest=p/'final_semantic_assessment.json';dest.write_text(json.dumps(assessment,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'summary':summary,'paired':assessment['paired_outcomes'],'bytes':dest.stat().st_size,'sha256':sha(dest.name)},ensure_ascii=False))

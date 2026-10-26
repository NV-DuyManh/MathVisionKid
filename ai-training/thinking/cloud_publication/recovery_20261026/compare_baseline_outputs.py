from pathlib import Path
import json,hashlib
P=Path(__file__).parent;R=P/'review_baseline';O=P.parent/'conditional_grounding_20261025/review_baseline'
def rows(p):return [json.loads(x) for x in p.read_bytes().splitlines()]
old=rows(O/'training__eval_step_000000__base_generations.jsonl');new=rows(R/'training__eval_step_000000__base_generations.jsonl')
assert len(new)==len(old)==30
assert (O/'new_validation_candidates.jsonl').read_bytes()==(R/'new_validation_candidates.jsonl').read_bytes()
assert (O/'training__evaluation_contract.json').read_bytes()==(R/'training__evaluation_contract.json').read_bytes()
changed=[]
for a,b in zip(old,new):
 assert a['fixture_id']==b['fixture_id'] and a['prompt_token_sha256']==b['prompt_token_sha256'] and a['seed']==b['seed']
 if a['output']!=b['output']:changed.append({'fixture_id':b['fixture_id'],'old_output':a['output'],'new_output':b['output']})
doc={'exact_question_contract_prompt_seed_match':True,'changed_outputs':changed,'identical_actual_output_count':30-len(changed),'current_base_raw_sha256':hashlib.sha256((R/'training__eval_step_000000__base_generations.jsonl').read_bytes()).hexdigest()}
(P/'baseline_content_comparison.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'changed_output_count':len(changed),'identical_count':30-len(changed),'changed_ids':[x['fixture_id'] for x in changed]}))

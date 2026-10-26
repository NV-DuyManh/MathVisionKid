from pathlib import Path
import sys,json,hashlib,base64
import recovery_policy as P
import recovery_worker as W
p=Path(__file__).parent;step=int(sys.argv[1]);assert sys.argv[2]=='--root-actual-output-review-complete'
d=p/f'review_step_{step:06d}'
fixtures=[json.loads(x) for x in (d/'new_validation_candidates.jsonl').read_text(encoding='utf8').splitlines()]
base=[json.loads(x) for x in (d/'training__eval_step_000000__base_generations.jsonl').read_text(encoding='utf8').splitlines()]
adapter=[json.loads(x) for x in (d/f'training__eval_step_{step:06d}__adapter_generations.jsonl').read_text(encoding='utf8').splitlines()]
bindings=json.loads((d/f'training__eval_step_{step:06d}__eval_bindings.json').read_bytes())
records=[]
for label in ['g1_g2','g3_g4','g5']:
 review=json.loads((d/f'semantic_{label}.json').read_bytes())
 assert review['all_actual_fields_read'] is True and review['human_review_claimed'] is False
 assert review['input_pair_sha256']==hashlib.sha256((d/f'paired_{label}.json').read_bytes()).hexdigest(),'Semantic review input hash mismatch'
 records.extend(review['decisions'])
byid={x['fixture_id']:x for x in records};assert len(byid)==len(records)==30
records=[byid[f['id']] for f in fixtures]
W.validate_review_metadata(records,fixtures);W.validate_review_completion(records,base,adapter)
summary=P.summarize_decisions(records)
decision='STOP'
if not bindings['final_stage']:
 if summary['candidate_eligible']:decision='CONTINUE_IMPROVED'
 elif step==50 and summary['safe_to_continue_pilot']:decision='CONTINUE_PILOT'
gate={**bindings,'step':step,'decision':decision,'all_actual_outputs_reviewed':True,'root_actual_outputs_reviewed':True,'human_review_claimed':False,'reviewer_role':'LLM semantic review, not human certification','decisions':records,'derived_summary':summary,'review_evidence_sha256':{label:hashlib.sha256((d/f'semantic_{label}.json').read_bytes()).hexdigest() for label in ['g1_g2','g3_g4','g5']}}
P.validate_gate(gate,step,bindings)
b=(json.dumps(gate,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
target=d/'root_gate.json';assert not target.exists(),'Retain original root gate; do not overwrite'
target.write_bytes(b)
script='''import pathlib,json,hashlib,base64
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024');step=STEP
data=base64.b64decode(DATA);gate=json.loads(data)
bindings=json.loads((r/f'training/eval_step_{step:06d}/eval_bindings.json').read_bytes())
for k,v in bindings.items():assert gate[k]==v,k
assert hashlib.sha256((r/f'training/eval_step_{step:06d}/adapter_generations.jsonl').read_bytes()).hexdigest()==gate['adapter_output_sha256']
assert hashlib.sha256((r/'training/eval_step_000000/base_generations.jsonl').read_bytes()).hexdigest()==gate['base_output_sha256']
p=r/f'training/gate_step_{step:06d}.json'
assert not p.exists(),'Gate already supplied; do not replace'
t=p.with_suffix('.pending');t.write_bytes(data);t.replace(p)
print(json.dumps({'gate_written':True,'step':step,'decision':gate['decision'],'sha256':hashlib.sha256(data).hexdigest(),'human_review_claimed':False}))
'''.replace('STEP',str(step)).replace('DATA',repr(base64.b64encode(b).decode()))
(d/'write_gate_runtime.py').write_text(script,encoding='utf8')
print(json.dumps({'step':step,'decision':decision,'summary':summary,'gate_sha256':hashlib.sha256(b).hexdigest()},ensure_ascii=False))

from pathlib import Path
import json,hashlib,base64
from base_review_notes import B
from native_dev_review_notes import N
from native_thinking_probe import DEV_INDICES
p=Path(__file__).parent;d=p/'native_review'
def read(q):return json.loads(q.read_bytes())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
f=[json.loads(x)for x in(p/'review_step_000100/new_validation_candidates.jsonl').read_text(encoding='utf8').splitlines()]
base=[json.loads(x)for x in(p/'review_step_000100/training__eval_step_000000__base_generations.jsonl').read_text(encoding='utf8').splitlines()]
out=d/'native_probe__dev__native_thinking_final.jsonl';proof=read(d/'native_probe__dev__complete.json')
assert proof['complete']and proof['dev_output_sha256']==sha(out)
rows=[json.loads(x)for x in out.read_text(encoding='utf8').splitlines()];assert len(rows)==len(N)==15and set(N)==set(range(15))
decisions=[]
for i,source_i in enumerate(DEV_INDICES):
 fixture=f[source_i];b=base[source_i];r=rows[i];bp,_,br=B[source_i];cp,critical,reason=N[i]
 assert fixture['id']==b['fixture_id']==r['fixture_id']and b['seed']==r['seed']
 if cp:assert r['ended_eos']and not r['possibly_truncated']and not r['timed_out']and r['final_output']
 decisions.append({'fixture_id':fixture['id'],'grade':fixture['grade'],'mode':fixture['mode'],'base_pass':bp,'native_pass':cp,'critical_new_error':critical,'base_reason':br,'native_reason':reason})
summary={'base_pass':sum(x['base_pass']for x in decisions),'native_pass':sum(x['native_pass']for x in decisions),'count':15,'baseline_pass_regressions':sum(x['base_pass']and not x['native_pass']for x in decisions),'new_critical_errors':sum(x['critical_new_error']for x in decisions),'base_answer_pass':sum(x['base_pass']for x in decisions if x['mode']=='answer'),'native_answer_pass':sum(x['native_pass']for x in decisions if x['mode']=='answer')}
eligible=summary['native_pass']>summary['base_pass']and not summary['baseline_pass_regressions']and not summary['new_critical_errors']and summary['native_answer_pass']>=summary['base_answer_pass']
policy=p/'native_probe_selection_policy.json'
gate={'schema':'MathVisionKid.native_probe_gate.v1','candidate_eligible':eligible,'dev_output_sha256':sha(out),'policy_sha256':sha(policy),'all_actual_final_answers_and_fixtures_read':True,'raw_thinking_used_as_answer':False,'human_review_claimed':False,'dev_fixture_sha256':proof['fixture_sha256'],'summary':summary,'decisions':decisions,'no_production_approval':True,'no_adapter_weights_selected':True,'frozen_before_native_final':True}
path=p/'native_probe_gate.json';raw=(json.dumps(gate,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
if path.exists():assert path.read_bytes()==raw
else:path.write_bytes(raw)
code="""import pathlib,json,base64,hashlib,subprocess,os,time
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');b=base64.b64decode(DATA);gate=json.loads(b)
assert skill_native_dev_process.poll()==0 and gate['candidate_eligible']
assert hashlib.sha256((r/'native_probe/dev/native_thinking_final.jsonl').read_bytes()).hexdigest()==gate['dev_output_sha256']
assert hashlib.sha256((r/'native_probe_selection_policy.json').read_bytes()).hexdigest()==gate['policy_sha256']
p=r/'native_probe_gate.json'
if p.exists():assert p.read_bytes()==b
else:p.write_bytes(b)
assert not(r/'native_probe/final').exists()
assert time.time()<json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-1500
skill_native_final_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(r/'native_thinking_probe.py'),'--root',str(r),'--phase','final'],stdout=(r/'native_probe_final.log').open('ab',buffering=0),stderr=subprocess.STDOUT,env={**os.environ,'TOKENIZERS_PARALLELISM':'false','PYTHONPATH':str(r)})
print(json.dumps({'native_final_launched':True,'pid':skill_native_final_process.pid,'candidate_eligible_from_dev':True,'new_weight_training':False,'scope_and_deadline_unchanged':True,'new15_once_only':True}))
""".replace('DATA',repr(base64.b64encode(raw).decode()))
(p/'launch_native_final_runtime.py').write_text(code,encoding='utf8');print(json.dumps({'eligible':eligible,'summary':summary,'gate_sha256':sha(path)}))

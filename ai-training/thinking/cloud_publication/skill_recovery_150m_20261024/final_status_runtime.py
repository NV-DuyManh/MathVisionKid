import pathlib,json,time
from datetime import datetime,timezone
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
v={'observed_utc':datetime.now(timezone.utc).isoformat(),'worker_alive':skill_final_process.poll() is None,'worker_exit':skill_final_process.poll(),'optimizer_worker_exit':skill_training_process.poll(),'fewshot_dev_exit':skill_fewshot_process.poll(),'seconds_remaining':json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-time.time()}
v['outputs']={str(p.relative_to(r)):len(p.read_bytes().splitlines())for p in(r/'final_eval').rglob('*generations*.jsonl')}
v['complete']=(r/'final_eval/complete.json').exists()
if v['complete']:
 q=json.loads((r/'final_eval/complete.json').read_bytes());v['summary']={k:q.get(k)for k in['selected_kind','base_outputs','selected_outputs','fewshot_outputs','fewshot_modes','test_run_count','selection_changed','training_performed','production_approval']}
if skill_final_process.poll() not in(None,0):v['log_tail']=(r/'final_eval.log').read_text(errors='replace')[-5000:]
print(json.dumps(v,ensure_ascii=False))

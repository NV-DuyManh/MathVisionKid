from pathlib import Path
import json,hashlib,base64
p=Path(__file__).parent
names=['final_evaluation_worker_v2.py','test_final_evaluation_worker_v2.py','fewshot_selection.json','root_fewshot_semantic_review.json','locked_test_binding.json']
payload={n:base64.b64encode((p/n).read_bytes()).decode() for n in names}
pins={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names}
preflight="""import pathlib,json
import final_evaluation_worker_v2 as F
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
scope=F.R.load_scope(r);fixtures,sha=F.verify_fixture_bundle(r,scope)
dev=F.read_rows(r/'new_validation_candidates.jsonl');dsha=F.sha(r/'new_validation_candidates.jsonl')
selected=F.verify_selection(r,scope,dev,dsha)
context=F.verify_fewshot_selection(r,dev,dsha,selected['baseline_output_sha256'])
packages=F.check_environment(r)
print(json.dumps({'preflight_passed':True,'selected_kind':selected['selected_kind'],'mode_selection':context['mode_selection'],'locked_fixture_count':len(fixtures),'locked_sha256':sha,'no_generation_performed':True,'packages':packages}))
"""
code="""import pathlib,json,hashlib,base64,subprocess,os,time
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
assert skill_training_process.poll()==0 and skill_fewshot_process.poll()==0
assert not globals().get('skill_final_process') or skill_final_process.poll() is not None
assert not (r/'final_eval').exists(),'One-time final inference must not have begun'
payload=PAYLOAD;pins=PINS
for n,v in payload.items():
 b=base64.b64decode(v);assert hashlib.sha256(b).hexdigest()==pins[n]
 if (r/n).exists():assert (r/n).read_bytes()==b,'Preserve existing evidence: '+n
 else:(r/n).write_bytes(b)
env={**os.environ,'TOKENIZERS_PARALLELISM':'false','PYTHONPATH':str(r)}
check=subprocess.run([str(r/'venv/bin/python'),'-c',PREFLIGHT],env=env,capture_output=True,text=True,timeout=50)
assert check.returncode==0,check.stdout[-2000:]+'\\n'+check.stderr[-4000:]
print(check.stdout)
assert time.time()<json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-2100
skill_final_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(r/'final_evaluation_worker_v2.py'),'--root',str(r)],stdout=(r/'final_eval.log').open('ab',buffering=0),stderr=subprocess.STDOUT,env=env)
(r/'final_launch_pins.json').write_text(json.dumps({'files':pins,'started_unix':time.time(),'pid':skill_final_process.pid,'one_time_test':True},indent=2)+'\\n')
print(json.dumps({'final_evaluation_launched':True,'pid':skill_final_process.pid,'source_training_exited':True,'once_after_dev_selection':True,'test_used_to_reselect':False,'no_optimizer_loaded':True}))
""".replace('PAYLOAD',repr(payload)).replace('PINS',repr(pins)).replace('PREFLIGHT',repr(preflight))
compile(code,'final_launch','exec');(p/'launch_final_runtime.py').write_text(code,encoding='utf8')
print(json.dumps({'payload_hashes':pins,'launch_script_bytes':len(code)}))

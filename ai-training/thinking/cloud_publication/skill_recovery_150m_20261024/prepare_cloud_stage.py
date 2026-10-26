from pathlib import Path
import json,hashlib,base64
p=Path(__file__).parent;old=p.parent/'verbal_recovery_20261024'
code=(old/'publisher_runtime.py').read_text(encoding='utf8').replace('mathvisionkid_verbal_recovery_20261024','mathvisionkid_skill_recovery_150m_20261024').replace('MathVisionKid_VERBAL_RECOVERY_20261024','MathVisionKid_SKILL_RECOVERY_150M_20261024').replace('MathVisionKidVerbalRecoveryPublisher','MathVisionKidSkillRecoveryPublisher').replace('_mathvisionkid_verbal_recovery_publisher_registry','_mathvisionkid_skill_recovery_publisher_registry')
code=code.replace("initial+=sorted", "initial+=['decoding_benchmark.py','balanced_plan.py','test_balanced_plan.py','audit_behavior_contract.json','source_inventory.json','behavior_renderer.py','test_behavior_renderer.py','calibration_review.json','benchmark/contract.json','benchmark/complete.json']\n  initial+=sorted")
code=code.replace('  report=None',"  for phase in ['benchmark','final_eval']:\n   folder=root/phase\n   if (folder/'complete.json').exists():\n    for path in sorted(folder.iterdir()):\n     if path.is_file() and path.suffix in ('.json','.jsonl') and '.partial.' not in path.name:self.put(str(path.relative_to(root)),path,True)\n  report=None")
q=p/'publisher_runtime.py';assert not q.exists();q.write_text(code,encoding='utf8')
names=['publisher_runtime.py','decoding_benchmark.py','balanced_plan.py','test_balanced_plan.py','audit_behavior_contract.json']
files={n:base64.b64encode((p/n).read_bytes()).decode() for n in names};pins={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names}
stage="""import pathlib,json,base64,hashlib,sys,importlib.util,subprocess,os
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');payload=PAYLOAD;pins=PINS
assert not globals().get('skill_benchmark_process') or skill_benchmark_process.poll() is not None
assert not (r/'benchmark').exists(),'Never duplicate calibration'
for n,v in payload.items():
 b=base64.b64decode(v);assert hashlib.sha256(b).hexdigest()==pins[n]
 q=r/n
 if q.exists():assert q.read_bytes()==b
 else:q.write_bytes(b)
old=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024')
for n in ['exhaustive_colab_loader.py']:
 if not (r/n).exists():
  assert (old/n).exists();(r/n).symlink_to(old/n)
spec=importlib.util.spec_from_file_location('skill_publisher_runtime',r/'publisher_runtime.py');skill_publisher=importlib.util.module_from_spec(spec);sys.modules[spec.name]=skill_publisher;spec.loader.exec_module(skill_publisher)
print(json.dumps(skill_publisher.start(recovery_credentials,r)))
skill_benchmark_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(r/'decoding_benchmark.py')],stdout=(r/'benchmark.log').open('ab',buffering=0),stderr=subprocess.STDOUT,env={**os.environ,'TOKENIZERS_PARALLELISM':'false'})
print(json.dumps({'benchmark_started':True,'pid':skill_benchmark_process.pid,'training_started':False,'code_pins':pins}))
""".replace('PAYLOAD',repr(files)).replace('PINS',repr(pins))
(p/'stage_benchmark_runtime.py').write_text(stage,encoding='utf8')
(p/'code_pins.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf8')
print(json.dumps({'stage_bytes':len(stage),'code_pins':pins}))

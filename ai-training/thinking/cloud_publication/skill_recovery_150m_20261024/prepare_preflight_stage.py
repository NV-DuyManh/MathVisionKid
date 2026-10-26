from pathlib import Path
import json,base64,hashlib
p=Path(__file__).parent
names=['recovery_worker.py','recovery_policy.py','behavior_renderer.py','test_behavior_renderer.py','inference_contract.py','calibration_review.json','locked_test_candidates.jsonl','locked_test_notes.json','frozen_code_references.json','balanced_plan_v2.py','test_balanced_plan_v2.py']
payload={n:base64.b64encode((p/n).read_bytes()).decode() for n in names};pins={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names}
code=(p/'preflight_runtime_template.py').read_text(encoding='utf8').replace('__PAYLOAD__',repr(payload)).replace('__PINS__',repr(pins))
compile(code,'skill_preflight_runtime','exec');q=p/'preflight_runtime.py';assert not q.exists();q.write_text(code,encoding='utf8')
(p/'training_code_pins.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf8');print(json.dumps({'bytes':q.stat().st_size,'pins':pins}))

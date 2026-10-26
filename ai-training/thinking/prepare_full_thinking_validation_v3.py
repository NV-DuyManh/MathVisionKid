"""Prepare an MCP cell that deploys new evaluation helpers, never old sources."""
import base64
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
evidence=here/'evidence'/'teacher_math_v3_20261013'
payload={name:{'base64':base64.b64encode((here/name).read_bytes()).decode(),
    'sha256':hashlib.sha256((here/name).read_bytes()).hexdigest()}
    for name in ('run_teacher_thinking_validation_v3.py','test_run_teacher_thinking_validation_v3.py')}
code='''# MATHVISIONKID — deploy full-thinking evaluation helpers; no training/model loading
import base64,hashlib,json,subprocess,sys
payload=PAYLOAD
for name,item in payload.items():
    path=MVK_V3_ROOT/'posthoc_src'/name
    raw=base64.b64decode(item['base64']);assert hashlib.sha256(raw).hexdigest()==item['sha256']
    if path.exists() and path.read_bytes()!=raw:
        assert name=='run_teacher_thinking_validation_v3.py'
        assert hashlib.sha256(path.read_bytes()).hexdigest()=='c0eca2fdd3ea4b018dd90d0c37348dc0d9045557e12ac10d8760c14777735de5'
        assert not (MVK_V3_ROOT/'runs'/'qwen3_17b_teacher_math_v3_epoch1_seed20261013'/'full_thinking_validation_seed20261013'/'protocol.json').exists()
        path.with_name('run_teacher_thinking_validation_v3_pre_dependency_review.py').write_bytes(path.read_bytes())
        path.write_bytes(raw)
    elif path.exists():assert path.read_bytes()==raw,'Evaluation helper changed: '+name
    else:path.write_bytes(raw)
test=subprocess.run([sys.executable,'-m','pytest','-q','test_run_teacher_thinking_validation_v3.py'],cwd=MVK_V3_ROOT/'posthoc_src',capture_output=True,text=True)
print(test.stdout);assert test.returncode==0,test.stderr
print('FULL_THINKING_HELPERS_READY',json.dumps({name:item['sha256'] for name,item in payload.items()}))
'''.replace('PAYLOAD',repr(payload))
evidence.mkdir(parents=True,exist_ok=True)
(evidence/'full_thinking_deploy_args.json').write_text(json.dumps({'cellIndex':67,'language':'python','code':code},ensure_ascii=False),encoding='utf-8')
(evidence/'full_thinking_update_args.json').write_text(json.dumps({'cellId':'2hZ9VIenj6x7','content':code},ensure_ascii=False),encoding='utf-8')
(evidence/'full_thinking_deploy_cell.py').write_text(code,encoding='utf-8')
print({'payload_files':len(payload),'source_sha256':payload['run_teacher_thinking_validation_v3.py']['sha256']})

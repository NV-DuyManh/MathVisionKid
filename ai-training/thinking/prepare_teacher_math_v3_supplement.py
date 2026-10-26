"""Deploy only NEW auxiliary diagnostics/references; frozen SFT inputs unchanged."""
import base64
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
DEST=HERE/'evidence'/'teacher_math_v3_20261013'
FILES={'posthoc_src/teacher_math_numeric_diagnostic_v3.py':HERE/'teacher_math_numeric_diagnostic_v3.py',
       'posthoc_src/test_teacher_math_numeric_diagnostic_v3.py':HERE/'test_teacher_math_numeric_diagnostic_v3.py'}
for name in ('curriculum_training_coverage.json','knowledge_cards.jsonl','semantic_template_review.json'):
    FILES['supplementary/'+name]=HERE/'data'/'teacher_math_v3'/name
payload={name:{'base64':base64.b64encode(path.read_bytes()).decode(),
               'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for name,path in FILES.items()}
code='''# MATHVISIONKID — supplementary reference cards and direct-answer diagnostic; frozen train data unchanged
import base64,hashlib,json,subprocess,sys
payload=PAYLOAD
for name,item in payload.items():
    path=(MVK_V3_ROOT/name).resolve();assert path.is_relative_to(MVK_V3_ROOT.resolve())
    raw=base64.b64decode(item['base64']);assert hashlib.sha256(raw).hexdigest()==item['sha256']
    if path.exists():assert path.read_bytes()==raw,'Supplement changed: '+name
    else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
test=subprocess.run([sys.executable,'-m','pytest','-q','test_teacher_math_numeric_diagnostic_v3.py'],cwd=MVK_V3_ROOT/'posthoc_src',capture_output=True,text=True)
print(test.stdout);assert test.returncode==0,test.stderr
sys.path.insert(0,str(MVK_V3_ROOT/'posthoc_src'))
from teacher_math_numeric_diagnostic_v3 import diagnostic
refs=[json.loads(s) for s in (MVK_V3_ROOT/'data'/'val.jsonl').read_text().splitlines()]
for cfg in ('compare_06','main_final'):
    config=json.loads((MVK_V3_ROOT/'configs'/(cfg+'.json')).read_text());run=MVK_V3_ROOT/'runs'/config['run_id']
    p=run/'baseline_val.summary.json'
    if not p.exists():continue
    predictions=[json.loads(s) for s in (run/'baseline_val.jsonl').read_text().splitlines()]
    report=diagnostic(refs,predictions)
    (run/'raw_numeric_baseline_diagnostic.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('RAW_BASELINE_MATH',cfg,json.dumps(report['summary'],ensure_ascii=False))
print('SUPPLEMENT_DEPLOYED',len(payload),'numeric_training_unchanged')
'''.replace('PAYLOAD',repr(payload))
DEST.mkdir(parents=True,exist_ok=True)
(DEST/'supplement_args.json').write_text(json.dumps({'cellIndex':62,'language':'python','code':code},ensure_ascii=False),encoding='utf-8')
(DEST/'supplement_cell.py').write_text(code,encoding='utf-8')
print(json.dumps({'files':len(payload),'code_bytes':len(code.encode())}))

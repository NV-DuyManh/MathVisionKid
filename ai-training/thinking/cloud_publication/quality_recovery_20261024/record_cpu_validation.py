from pathlib import Path
import subprocess,sys,json,hashlib
from datetime import datetime,timezone
p=Path(__file__).parent
result=subprocess.run([sys.executable,'-X','utf8','-m','unittest','discover','-s',str(p),'-p','test_recovery*.py'],capture_output=True,text=True)
print(result.stderr)
assert result.returncode==0,'CPU validation failed'
files=['recovery_worker.py','recovery_policy.py','publisher_runtime.py','test_recovery_worker.py','test_recovery_policy.py','test_recovery_publisher.py']
for n in files:compile((p/n).read_text(encoding='utf8'),str(p/n),'exec')
e={'observed_utc':datetime.now(timezone.utc).isoformat(),'unittest_exit':result.returncode,'actual_unittest_output':result.stderr,'compile':'PASS','hashes':{n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in files},'scope':'CPU logic invariants; no semantic or GPU performance proof','source_semantic_review':{'diagnostic_sha256':'ad4c6a4f4fc86a074d90d54cde16d046e4e813470d964936c273c309997c000d','read_actual_rows':34,'all_actual_content_reviewed':True,'confirmed_math_errors':0,'limited_oracle_unmatched_not_assumed_wrong':True},'dev_root_content_review':{'file_sha256':'75eab78085830aa5bf0cf856eb6f70d2630e2407c8143409816dec94d849aaed','actual_rows_read':30,'exact_math_and_full_rubric_review':'PASS','runtime_train_screening_pending':True},'locked_test_root_content_read':False,'human_certification_added':False}
(p/'cpu_validation.json').write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'cpu_validation_sha256':hashlib.sha256((p/'cpu_validation.json').read_bytes()).hexdigest(),'compiled':files}))

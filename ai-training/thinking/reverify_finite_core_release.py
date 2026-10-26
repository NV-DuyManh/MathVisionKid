"""Recheck the completed finite release without claiming full expanded readiness."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
RUN=HERE/'cloud_publication/final_confirmation_20261022'
RUN.mkdir(exist_ok=True)
index_path=HERE/'data/primary_math_teacher_20261016/final_release_index.json'
index=json.loads(index_path.read_text('utf8'))
assert index['core_cases']==495 and index['nodes']==165
checks={}
for key,ref in index['release_files'].items():
    raw=(ROOT/ref['path']).read_bytes()
    actual=hashlib.sha256(raw).hexdigest()
    assert actual==ref['sha256'] and len(raw)==ref['bytes']
    checks[key]=dict(path=ref['path'],sha256=actual,bytes=len(raw),rows=ref['rows'],matches_frozen_release=True)
audit_ref=index['final_audit']
raw=(ROOT/audit_ref['path']).read_bytes()
assert hashlib.sha256(raw).hexdigest()==audit_ref['sha256']
assert json.loads(raw)['status']=='PASSED_FINITE_DATA_AUDIT'
receipt=dict(schema='MathVisionKid.finite_core_release_reverification.v1',
    observed_utc=datetime.now(timezone.utc).isoformat(),
    finite_core_generation_complete=True,finite_core_cases=495,finite_core_nodes=165,
    finite_core_chat_rows=1980,finite_release_all_cases=782,finite_release_all_chat_rows=3128,
    release_index_sha256=hashlib.sha256(index_path.read_bytes()).hexdigest(),
    release_files=checks,final_core_audit_sha256=audit_ref['sha256'],
    final_core_audit_status='PASSED_FINITE_DATA_AUDIT',
    decision='CONFIRMED_COMPLETE_FINITE495_RELEASE',
    scope_note='Confirmation covers the already published finite495 release. It does not mark full expanded corpus, SGK extension queues, physical assets or legal2026 coverage complete, and does not select a subset for training.',
    expanded_archive_audit_complete=False,sgk_extension_complete=False,
    all_rows_newly_human_reviewed=False,original_owner299_signoffs_unchanged=True,
    source_rows_changed=False,new_cases=0,new_chat_rows=0,TRAINING_DATASET_READY=False,
    training_started=False,gpu_used=False,model_weights_loaded=False)
(RUN/'core_release_reverified.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(receipt,ensure_ascii=False))

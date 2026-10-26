"""Bounded metadata export only; execute after the finite repair thread exits."""
import base64
import hashlib
import io
import json
import zipfile
from datetime import datetime,timezone

assert not structural15_repair_thread.is_alive()
assert not full_audit_worker.is_alive() and not final_metadata_thread.is_alive()
directory=ROOT/'structural15_adapter_20261023'
state=json.loads((directory/'repair_worker_status.json').read_bytes())
assert state['state'] in ('FINAL_TEXT_TECHNICAL_EVIDENCE_COMPLETE_PENDING_CONTROL_PUBLICATION',
                          'REPAIR_STOPPED_WITH_EVIDENCE')
names=[
    'repair_worker_status.json','parent_finished_worker_state.json',
    'parent_final_metadata_status.json','migration_receipt.json',
    'exact60_original_consume.json','exact60_reaudit_verification.json',
    'child_checkpoint_raw_verified.json','final_antijoin_execution.json',
    'final_source_chat_antijoin.json','final_raw_v3_report_preserved.json',
    'final_candidate_chat_technical_adjudication.json','final_current_text_candidate_manifest.json',
]
paths=[directory/name for name in names if (directory/name).exists()]
runtime={
    'observed_utc':datetime.now(timezone.utc).isoformat(),
    'worker_alive':False,'final_metadata_alive':False,'structural15_repair_alive':False,
    'worker_name':'MathVisionKidStructural15ExactRepair',
    'worker_state':'AUDIT_FINISHED_WITH_FINDINGS' if state['state'].startswith('FINAL_TEXT_') else state['state'],
    'structural15_repair_state':state,'checkpoint':state.get('checkpoint'),
    'report':state.get('checkpoint',{}).get('report_at_snapshot'),
    'training_started':False,'gpu_used':False,'model_weights_loaded':False,
    'source_chat_payload_bytes_changed':0,
    'parent_worker_state':full_audit_worker_state.get('state'),
    'parent_checkpoint':full_audit_worker_state.get('checkpoint'),
}
if runtime['report'] is not None:
    report=runtime['report']
    runtime.update(committed_physical_chat_rows=report['physical_chat_occurrences_processed'],
        unique_chat_rows_processed=report['unique_chat_rows_processed'],
        members_complete=report['members_complete'],members_expected=report['members_expected'],
        expected_raw_chat_rows=6502392,issues_now=report['issues'])
repair_save('final_runtime_observation.json',runtime)
paths.append(directory/'final_runtime_observation.json')
if state['state'].startswith('FINAL_TEXT_'):
    # The final-status filename is compatible with the existing metadata packer.
    repair_save('final_metadata_status.json',state)
    paths.append(directory/'final_metadata_status.json')
for name in ('source_index_ledger_receipt.json','read_cache_receipt.json','status_report_cache_receipt.json'):
    path=resume_dir/name
    if path.exists():paths.append(path)
buffer=io.BytesIO();refs=[]
with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    assert len({p.name for p in paths})==len(paths)
    for path in paths:
        assert path.suffix=='.json' and path.parent in (directory,resume_dir)
        data=path.read_bytes();assert len(data)<=24*1024*1024;json.loads(data)
        archive.writestr(path.name,data)
        refs.append({'name':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
data=buffer.getvalue()
assert len(data)<=4*1024*1024 and sum(x['bytes'] for x in refs)<=32*1024*1024
print(json.dumps({'schema':'MathVisionKid.bounded_structural15_final_metadata_export.v1',
    'state':state['state'],'files':refs,'zip_bytes':len(data),
    'zip_sha256':hashlib.sha256(data).hexdigest(),
    'corpus_or_sqlite_exported':False,'training_started':False,
    'zip_b64':base64.b64encode(data).decode('ascii')}))

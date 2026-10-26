"""Derive current worker orchestration without changing the frozen gates."""
from pathlib import Path
import ast, hashlib, json

R=Path(__file__).resolve().parent
worker=(R/'parent_worker_function.py').read_text(encoding='utf8')
replacements={
    "work_api=build('drive','v3',credentials=credentials,cache_discovery=False)":"work_api=g2_connected_api()",
    "auditor.db.execute('PRAGMA cache_size=-131072')":"auditor.db.execute('PRAGMA cache_size=-131072')\n        auditor.db.execute('PRAGMA busy_timeout=1200000')\n        assert auditor.db.execute('PRAGMA journal_mode').fetchone()[0]=='wal'",
    'try:auditor.db.backup(target_db)':"try:\n            auditor.db.backup(target_db)\n            assert target_db.execute('PRAGMA journal_mode=DELETE').fetchone()[0]=='delete'",
    'chunksize=8*1024*1024':'chunksize=64*1024*1024',
    'max_rows=50000,commit_every=256':'max_rows=200000,commit_every=256',
}
for old,new in replacements.items():
    assert worker.count(old)==1,old
    worker=worker.replace(old,new)
ast.parse(worker)
(R/'resumed_worker_function.py').write_text(worker,encoding='utf8')
prefix='''# One exact current-recipe CPU worker; no append, generation, or training.
import json,hashlib,sqlite3,threading,time,uuid,os
from datetime import datetime,timezone
from googleapiclient.http import MediaIoBaseDownload,MediaFileUpload
assert os.environ.get('COLAB_GPU','0') in ('0','')
assert not restore_thread.is_alive()
assert not globals().get('checkpoint_prefetch_thread') or not checkpoint_prefetch_thread.is_alive()
assert not globals().get('checkpoint_prefetch_started') or checkpoint_prefetch_status['state']=='RUNTIME_SNAPSHOT_HASH_REVERIFIED_READONLY'
assert resume_status['state']=='RESTORED_READY_FOR_SINGLE_WORKER'
assert probe_receipt['fresh_raw_readback_verified']
assert probe_receipt['checkpoint_sha256']==EXPECTED_SHA
assert audit_v3.plan_identity(recipe_all)==V3_ID
assert len(recipe_all['source_members'])==219 and len(recipe_all['chat_members'])==32
assert not any(t.is_alive() and t.name.startswith('MathVisionKidFiniteCPUDataAudit') for t in threading.enumerate())
assert batch_module._OWNER is None and batch_module._ACTIVE==0
assert hashlib.sha256(Path(audit_v3.__file__).read_bytes()).hexdigest()=='02431da433060a6574127f9a8e14d90cabffe85d8d0150c3b2a331dc15b4be1f'
assert hashlib.sha256(Path(batch_module.__file__).read_bytes()).hexdigest()=='8d978eceeabebda9103ae23a16c23beab5b8cf5f2248984eda0b584facbedf92'
batch_adapter=batch_module.BatchTokenAuditAdapter(tokenizer,batch_size=256)
phase_api=g2_connected_api()
preclaim=phase_api.files().get(fileId=EXISTING_V3_ID,fields='id,size,appProperties,modifiedTime,version',supportsAllDrives=True).execute()
assert preclaim==meta_after,'Remote checkpoint advanced after restore; refuse a stale writer'
with sqlite3.connect(V3_DB) as config_db:
    assert config_db.execute('PRAGMA journal_mode=WAL').fetchone()[0]=='wal'
writer_session=uuid.uuid4().hex
claim=dict(preclaim['appProperties'],writer_session=writer_session)
v3_ref=phase_api.files().update(fileId=EXISTING_V3_ID,body={'appProperties':claim},fields='id,size,appProperties',supportsAllDrives=True).execute()
assert v3_ref['id']==EXISTING_V3_ID and v3_ref['appProperties']['data_sha256']==EXPECTED_SHA
worker_status_path=ROOT/'full_audit_v3_worker_status.json'
parent_proof=state['owner_requested_pause']['checkpoint']
full_audit_worker_state={'state':'RESUMING_OWNER_PAUSED_EXACT_CHECKPOINT','started_utc':datetime.now(timezone.utc).isoformat(),
    'notebook_id':'1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l','audit_identity':V3_ID,'recipe_sha256':pointer_all['sha256'],
    'checkpoint_id':EXISTING_V3_ID,'writer_session':writer_session,'checkpoint':parent_proof,
    'writer_guard':'SINGLE_OBSERVED_KERNEL_PLUS_OPTIMISTIC_HASH_NOT_DISTRIBUTED_ATOMIC_CAS',
    'restored_parent':probe_receipt,'owner_pause_revoked_by_new_explicit_instruction':True,
    'performance_upgrade':{'batch_size':256,'commit_every':256,'outer_span':200000,'query_indexes_preserved':True,'onepass_optimizer_applied':False},
    'training_started':False,'gpu_used':False,'model_weights_loaded':False}
def write_worker_status():
    full_audit_worker_state['updated_utc']=datetime.now(timezone.utc).isoformat()
    tmp=worker_status_path.with_suffix('.writing')
    tmp.write_text(json.dumps(full_audit_worker_state,ensure_ascii=False,indent=2))
    tmp.replace(worker_status_path)
'''
suffix='''
write_worker_status()
batch_adapter.install()
full_audit_worker=threading.Thread(target=finite_full_data_audit_worker_v3,name='MathVisionKidFiniteCPUDataAuditV3',daemon=True)
full_audit_worker.start()
resume_status.update(state='EXACT_CHECKPOINT_RESUMED_SINGLE_CPU_WORKER',resumed_utc=datetime.now(timezone.utc).isoformat(),worker_alive=full_audit_worker.is_alive())
write_resume_status()
print(json.dumps({'resume_status':resume_status,'worker_alive':full_audit_worker.is_alive(),'checkpoint_id':EXISTING_V3_ID,'training_started':False},ensure_ascii=False))
'''
result=prefix+worker+suffix
ast.parse(result)
(R/'launch_single_worker.py').write_text(result,encoding='utf8')
print(json.dumps({'prepared':True,'parent_worker_sha256':hashlib.sha256((R/'parent_worker_function.py').read_bytes()).hexdigest(),
    'derived_worker_sha256':hashlib.sha256(worker.encode()).hexdigest(),'scanner_adapter_unchanged':True,'recipe_unchanged':True,'new_cases':0,'training_started':False}))

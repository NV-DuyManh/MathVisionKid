# Attach to the existing, fully raw-verified V3 checkpoint; never create a file.
import threading,time,uuid,shutil
from datetime import datetime,timezone
from googleapiclient.http import MediaIoBaseDownload,MediaFileUpload
assert os.environ.get('COLAB_GPU','0') in ('0','')
if any(t.name.startswith('MathVisionKidFiniteCPUDataAudit') and t.is_alive() for t in threading.enumerate()):
    raise RuntimeError('A data audit worker is already active; do not duplicate it.')
assert probe_receipt['state']=='EXISTING_V3_CHECKPOINT_RAW_VERIFIED_READONLY'
assert probe_receipt['fresh_raw_readback_verified']
V3_DB=RESTORED_V3_DB
V3_ID=probe_receipt['audit_identity']
recipe_all=recipe;pointer_all=recipe_pointer
assert audit_v3.plan_identity(recipe_all)==V3_ID
assert len(recipe_all['source_members'])==218 and len(recipe_all['chat_members'])==31
def file_digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
assert file_digest(V3_DB)==probe_receipt['checkpoint_sha256']
if shutil.disk_usage(ROOT).free<3*V3_DB.stat().st_size+1024**3:
    raise RuntimeError('Insufficient temporary Colab disk for data checkpoint snapshots.')
fresh=drive_api.files().get(fileId=EXISTING_V3_ID,fields='id,size,appProperties,modifiedTime,version',supportsAllDrives=True).execute()
assert fresh==meta_after,'Checkpoint changed after read-only restore; refuse a stale writer.'
from exhaustive_colab_loader import load_qwen_tokenizer
tokenizer=load_qwen_tokenizer()  # tokenizer assets only, no model weights
preclaim=drive_api.files().get(fileId=EXISTING_V3_ID,fields='id,size,appProperties,modifiedTime,version',supportsAllDrives=True).execute()
assert preclaim==fresh,'Checkpoint advanced while loading tokenizer; refuse a stale writer.'
writer_session=uuid.uuid4().hex
claim=dict(fresh['appProperties'],writer_session=writer_session)
v3_ref=drive_api.files().update(fileId=EXISTING_V3_ID,body={'appProperties':claim},fields='id,size,appProperties',supportsAllDrives=True).execute()
assert v3_ref['id']==EXISTING_V3_ID
assert v3_ref['appProperties']['data_sha256']==probe_receipt['checkpoint_sha256']
worker_status_path=ROOT/'full_audit_v3_worker_status.json'
full_audit_worker_state={'state':'RESUMING_EXISTING_CHECKPOINT','started_utc':datetime.now(timezone.utc).isoformat(),'notebook_id':'1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l','audit_identity':V3_ID,'recipe_sha256':pointer_all['sha256'],'checkpoint_id':EXISTING_V3_ID,'writer_session':writer_session,'writer_guard':'SINGLE_OBSERVED_KERNEL_PLUS_OPTIMISTIC_HASH_NOT_DISTRIBUTED_ATOMIC_CAS','restored_parent':probe_receipt,'training_started':False,'gpu_used':False,'model_weights_loaded':False}
def write_worker_status():
    full_audit_worker_state['updated_utc']=datetime.now(timezone.utc).isoformat()
    tmp=worker_status_path.with_suffix('.writing')
    tmp.write_text(json.dumps(full_audit_worker_state,ensure_ascii=False,indent=2),encoding='utf8')
    tmp.replace(worker_status_path)

def finite_full_data_audit_worker_v3():
    global v3_ref
    auditor=None;checkpoint=dict(v3_ref);last_save=0.0
    def verify_writer():
        remote=work_api.files().get(fileId=checkpoint['id'],fields='id,size,appProperties',supportsAllDrives=True).execute()
        props=remote.get('appProperties',{})
        if props.get('writer_session')!=writer_session or props.get('recipe_identity')!=V3_ID or props.get('data_sha256')!=checkpoint.get('appProperties',{}).get('data_sha256'):
            raise RuntimeError('Checkpoint writer or hash changed; stop without overwriting.')
        return remote
    def save_checkpoint():
        nonlocal checkpoint,last_save
        global v3_ref
        auditor.db.commit();snapshot=ROOT/'full_audit_v3_snapshot.sqlite'
        target_db=sqlite3.connect(snapshot)
        try:auditor.db.backup(target_db)
        finally:target_db.close()
        snapshot_sha=file_digest(snapshot)
        verify_writer()
        props={'recipe_identity':V3_ID,'data_sha256':snapshot_sha,'purpose':'FULL_DATA_AUDIT_ONLY_NO_TRAINING','writer_session':writer_session}
        saved=work_api.files().update(fileId=checkpoint['id'],body={'appProperties':props},media_body=MediaFileUpload(str(snapshot),mimetype='application/vnd.sqlite3',resumable=True),fields='id,size,appProperties',supportsAllDrives=True).execute()
        # Retain the completed write identity even if the verification read fails.
        # It does not become a verified receipt until all raw bytes match.
        checkpoint=saved;v3_ref=saved
        class HashSink:
            def __init__(self):self.hasher=hashlib.sha256();self.size=0
            def write(self,data):self.hasher.update(data);self.size+=len(data);return len(data)
        sink=HashSink();download=MediaIoBaseDownload(sink,work_api.files().get_media(fileId=saved['id'],supportsAllDrives=True),chunksize=8*1024*1024)
        done=False
        while not done:_,done=download.next_chunk(num_retries=3)
        if sink.hasher.hexdigest()!=snapshot_sha or sink.size!=snapshot.stat().st_size:
            raise RuntimeError('V3 raw checkpoint readback differs.')
        after=verify_writer()
        last_save=time.monotonic()
        proof={'id':saved['id'],'bytes':sink.size,'sha256':snapshot_sha,'fresh_raw_readback_verified':True,'report_at_snapshot':auditor.report(),'observed_utc':datetime.now(timezone.utc).isoformat()}
        full_audit_worker_state['checkpoint']=proof
        (ROOT/'v3_latest_checkpoint_ref.json').write_text(json.dumps({'metadata':after,'proof':proof},ensure_ascii=False,indent=2),encoding='utf8')
    try:
        work_api=build('drive','v3',credentials=credentials,cache_discovery=False)
        work_reader=GoogleDriveReader(work_api)
        work_cache=LazyDriveCache(work_reader,recipe_all,ROOT/'full_audit_v3_worker_payload_cache')
        auditor=audit_v3.FullArchiveAudit(V3_DB,recipe_all,tokenizer)
        full_audit_worker_state['report']=auditor.report();write_worker_status()
        last_save=time.monotonic()
        full_audit_worker_state['state']='RUNNING_DATA_ONLY';write_worker_status()
        while True:
            entry=auditor.next_entry()
            if entry is None:break
            verify_writer()
            full_audit_worker_state['current_member']={'role':entry['role'],'member':entry.get('member'),'payload_sha256':entry['sha256']}
            write_worker_status()
            span=auditor.consume(entry,work_cache[entry['sha256']],max_rows=50000,commit_every=256)
            full_audit_worker_state.update(last_span=span,report=auditor.report(),current_member={'role':entry['role'],'member':entry.get('member'),'payload_sha256':entry['sha256']})
            if not span.get('processed',0) and not span.get('complete') and not span.get('already_complete'):
                raise RuntimeError('No finite cursor progress; refuse an endless loop.')
            if 'checkpoint' not in full_audit_worker_state or time.monotonic()-last_save>=300:save_checkpoint()
            write_worker_status()
        save_checkpoint();report=auditor.report()
        full_audit_worker_state.update(report=report,state='AUDIT_PASS_PENDING_CURRICULUM_ACCEPTANCE' if report['full_archive_token_linkage_split_audit_complete'] else 'AUDIT_FINISHED_WITH_FINDINGS')
    except Exception as exc:
        full_audit_worker_state.update(state='STOPPED_REQUIRES_AUDIT_REPAIR',error_type=type(exc).__name__,error=str(exc))
        if auditor is not None:
            full_audit_worker_state['report']=auditor.report()
            try:save_checkpoint()
            except Exception as checkpoint_error:full_audit_worker_state['checkpoint_save_error']=str(checkpoint_error)
    finally:
        if auditor is not None:auditor.close()
        write_worker_status()
write_worker_status()
full_audit_worker=threading.Thread(target=finite_full_data_audit_worker_v3,name='MathVisionKidFiniteCPUDataAuditV3',daemon=True)
full_audit_worker.start()
print(full_audit_worker_state)

# Finite CPU data audit over all247 declared source/chat members. No training.
import threading,time,traceback
from googleapiclient.http import MediaIoBaseDownload,MediaFileUpload
if globals().get('full_audit_worker') is not None and full_audit_worker.is_alive():
    raise RuntimeError('An audit worker is already running; do not launch a duplicate.')
worker_status_path=ROOT/'full_audit_v2_worker_status.json'
full_audit_worker_state={'state':'STARTING','started_utc':datetime.now(timezone.utc).isoformat(),'notebook_id':'1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l','audit_identity':V2_ID,'recipe_sha256':pointer_all['sha256'],'checkpoint_id':v2_ref['id'],'training_started':False,'gpu_used':False,'model_weights_loaded':False}
def write_worker_status():
    full_audit_worker_state['updated_utc']=datetime.now(timezone.utc).isoformat()
    temp_status=worker_status_path.with_suffix('.writing')
    temp_status.write_text(json.dumps(full_audit_worker_state,ensure_ascii=False,indent=2),encoding='utf8')
    temp_status.replace(worker_status_path)
def finite_full_data_audit_worker():
    work_api=build('drive','v3',credentials=credentials,cache_discovery=False)
    work_reader=GoogleDriveReader(work_api)
    work_cache=LazyDriveCache(work_reader,recipe_all,ROOT/'full_audit_worker_payload_cache')
    work_auditor=None
    checkpoint=dict(v2_ref)
    last_save=0.0
    def save_work_checkpoint():
        nonlocal checkpoint,last_save
        work_auditor.db.commit()
        snapshot=ROOT/'full_audit_v2_snapshot.sqlite'
        with sqlite3.connect(snapshot) as target_db:
            work_auditor.db.backup(target_db)
        hasher=hashlib.sha256()
        with snapshot.open('rb') as sf:
            for block in iter(lambda:sf.read(4*1024*1024),b''):hasher.update(block)
        snapshot_sha=hasher.hexdigest()
        remote=work_api.files().get(fileId=checkpoint['id'],fields='id,appProperties',supportsAllDrives=True).execute()
        if remote.get('appProperties',{}).get('data_sha256')!=checkpoint.get('appProperties',{}).get('data_sha256'):
            raise RuntimeError('Concurrent checkpoint update; stop without overwriting.')
        props={'data_sha256':snapshot_sha,'recipe_identity':V2_ID,'purpose':'FULL_DATA_AUDIT_ONLY_NO_TRAINING'}
        saved=work_api.files().update(fileId=checkpoint['id'],body={'appProperties':props},media_body=MediaFileUpload(str(snapshot),mimetype='application/vnd.sqlite3',resumable=True),fields='id,size,appProperties',supportsAllDrives=True).execute()
        class HashSink:
            def __init__(self):self.hasher=hashlib.sha256();self.size=0
            def write(self,data):self.hasher.update(data);self.size+=len(data);return len(data)
        sink=HashSink()
        download=MediaIoBaseDownload(sink,work_api.files().get_media(fileId=saved['id'],supportsAllDrives=True),chunksize=4*1024*1024)
        done=False
        while not done:_,done=download.next_chunk(num_retries=3)
        if sink.hasher.hexdigest()!=snapshot_sha or sink.size!=snapshot.stat().st_size:
            raise RuntimeError('Checkpoint raw streaming readback mismatch.')
        checkpoint=saved;last_save=time.monotonic()
        full_audit_worker_state['checkpoint']={'id':saved['id'],'bytes':sink.size,'sha256':snapshot_sha,'fresh_raw_readback_verified':True}
    try:
        work_auditor=audit_v2.FullArchiveAudit(V2_DB,recipe_all,tokenizer)
        full_audit_worker_state['state']='RUNNING_DATA_ONLY'
        write_worker_status()
        while True:
            next_member=work_auditor.next_entry()
            if next_member is None:break
            before_report=work_auditor.report()
            span_work=work_auditor.consume(next_member,work_cache[next_member['sha256']],max_rows=50000,commit_every=256)
            full_audit_worker_state['last_span']=span_work
            full_audit_worker_state['report']=work_auditor.report()
            full_audit_worker_state['current_member']={'role':next_member['role'],'member':next_member.get('member'),'payload_sha256':next_member['sha256']}
            if not span_work.get('processed',0) and not span_work.get('complete') and not span_work.get('already_complete'):
                raise RuntimeError('Audit made no cursor progress; refuse an endless loop.')
            if last_save==0 or time.monotonic()-last_save>=300:
                save_work_checkpoint()
            write_worker_status()
        save_work_checkpoint()
        final=work_auditor.report()
        full_audit_worker_state['report']=final
        full_audit_worker_state['state']='AUDIT_PASS_PENDING_CURRICULUM_ACCEPTANCE' if final['full_archive_token_linkage_split_audit_complete'] else 'AUDIT_FINISHED_WITH_FINDINGS'
    except Exception as exc:
        full_audit_worker_state['state']='STOPPED_REQUIRES_AUDIT_REPAIR'
        full_audit_worker_state['error_type']=type(exc).__name__
        full_audit_worker_state['error']=str(exc)
        if work_auditor is not None:
            full_audit_worker_state['report']=work_auditor.report()
            try:save_work_checkpoint()
            except Exception as checkpoint_error:
                full_audit_worker_state['checkpoint_save_error']=str(checkpoint_error)
    finally:
        if work_auditor is not None:work_auditor.close()
        write_worker_status()
write_worker_status()
full_audit_worker=threading.Thread(target=finite_full_data_audit_worker,name='MathVisionKidFiniteCPUDataAudit',daemon=True)
full_audit_worker.start()
print(full_audit_worker_state)


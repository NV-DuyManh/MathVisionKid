# Resolve the actual already downloaded immutable tokenizer snapshot path.
# Never fill in commit metadata by assertion; load the pinned local snapshot.
from huggingface_hub import snapshot_download
import exhaustive_colab_loader as L
assert not any(t.is_alive() and t.name.startswith('MathVisionKidFiniteCPUDataAudit') for t in threading.enumerate())
assert batch_module._OWNER is None and batch_module._ACTIVE==0
pinned_tokenizer_path=Path(snapshot_download(repo_id=L.MODEL,revision=L.REVISION,local_files_only=True))
assert pinned_tokenizer_path.name==L.REVISION
assert pinned_tokenizer_path.is_dir()
tokenizer=L.load_qwen_tokenizer(pinned_tokenizer_path)
assert Path(tokenizer.name_or_path).name==L.REVISION
assert tokenizer.is_fast and tokenizer.convert_tokens_to_ids('<|im_end|>')==151645
owned_checkpoint=phase_api.files().get(fileId=EXISTING_V3_ID,fields='id,size,appProperties',supportsAllDrives=True).execute()
assert owned_checkpoint['appProperties']['writer_session']==writer_session
assert owned_checkpoint['appProperties']['data_sha256']==EXPECTED_SHA
assert owned_checkpoint['appProperties']['recipe_identity']==V3_ID
v3_ref=owned_checkpoint
resume_status['tokenizer_pin_recovery']={'reason':'Remote-name tokenizer lacked _commit_hash metadata under current installed transformers; frozen adapter correctly refused it before any row processing','method':'Reload actual immutable local HF snapshot directory whose basename equals pinned revision','revision':L.REVISION,'weights_loaded':False,'gate_unchanged':True}
batch_adapter=batch_module.BatchTokenAuditAdapter(tokenizer,batch_size=256)
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
        try:
            auditor.db.backup(target_db)
            assert target_db.execute('PRAGMA journal_mode=DELETE').fetchone()[0]=='delete'
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
        sink=HashSink();download=MediaIoBaseDownload(sink,work_api.files().get_media(fileId=saved['id'],supportsAllDrives=True),chunksize=64*1024*1024)
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
        work_api=g2_connected_api()
        work_reader=GoogleDriveReader(work_api)
        work_cache=LazyDriveCache(work_reader,recipe_all,ROOT/'full_audit_v3_worker_payload_cache')
        auditor=audit_v3.FullArchiveAudit(V3_DB,recipe_all,tokenizer)
        auditor.db.execute('PRAGMA cache_size=-131072')
        auditor.db.execute('PRAGMA busy_timeout=1200000')
        assert auditor.db.execute('PRAGMA journal_mode').fetchone()[0]=='wal'
        full_audit_worker_state['report']=auditor.report();write_worker_status()
        last_save=time.monotonic()
        full_audit_worker_state['state']='RUNNING_DATA_ONLY';write_worker_status()
        while True:
            entry=auditor.next_entry()
            if entry is None:break
            verify_writer()
            full_audit_worker_state['current_member']={'role':entry['role'],'member':entry.get('member'),'payload_sha256':entry['sha256']}
            write_worker_status()
            span=batch_adapter.consume(auditor,entry,work_cache[entry['sha256']],max_rows=200000,commit_every=256)
            full_audit_worker_state.update(last_span=span,report=auditor.report(),current_member={'role':entry['role'],'member':entry.get('member'),'payload_sha256':entry['sha256']})
            if not span.get('processed',0) and not span.get('complete') and not span.get('already_complete'):
                raise RuntimeError('No finite cursor progress; refuse an endless loop.')
            if 'checkpoint' not in full_audit_worker_state or time.monotonic()-last_save>=1800:save_checkpoint()
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
        batch_adapter.uninstall()
        write_worker_status()
write_worker_status()
batch_adapter.install()
full_audit_worker=threading.Thread(target=finite_full_data_audit_worker_v3,name='MathVisionKidFiniteCPUDataAuditV3',daemon=True)
full_audit_worker.start()
resume_status.update(state='EXACT_CHECKPOINT_RESUMED_SINGLE_CPU_WORKER',resumed_utc=datetime.now(timezone.utc).isoformat(),worker_alive=full_audit_worker.is_alive())
write_resume_status()
print(json.dumps({'resume_status':resume_status,'worker_alive':full_audit_worker.is_alive(),'checkpoint_id':EXISTING_V3_ID,'training_started':False},ensure_ascii=False))

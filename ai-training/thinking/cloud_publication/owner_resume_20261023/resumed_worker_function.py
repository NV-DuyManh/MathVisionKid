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
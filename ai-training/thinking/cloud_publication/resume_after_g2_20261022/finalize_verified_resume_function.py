def g2_finish_verified_resume(a,snapshot_sha,sink,saved,after_meta,resume_next_recipe):
    global recipe,recipe_all,recipe_pointer,pointer_all,V3_ID,v3_ref,writer_session,batch_adapter,full_audit_worker_state,full_audit_worker,finite_full_data_audit_worker_v3
    report=a.report();a.close();a=None
    proof={'id':EXISTING_V3_ID,'bytes':sink.size,'sha256':snapshot_sha,'fresh_raw_readback_verified':True,
        'report_at_snapshot':report,'observed_utc':datetime.now(timezone.utc).isoformat()}
    recipe=recipe_all=resume_next_recipe
    recipe_pointer=pointer_all=resume_payload['next_recipe_pointer']
    V3_ID=resume_payload['next_identity'];v3_ref=saved
    batch_adapter=batch_module.BatchTokenAuditAdapter(tokenizer,batch_size=256)
    full_audit_worker_state={'state':'RESUMING_AFTER_LOCK_REPAIR_AND_EXACT_APPEND',
        'started_utc':datetime.now(timezone.utc).isoformat(),'notebook_id':'1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l',
        'audit_identity':V3_ID,'recipe_sha256':pointer_all['sha256'],'checkpoint_id':EXISTING_V3_ID,
        'writer_session':writer_session,'checkpoint':proof,'report':report,
        'writer_guard':'SINGLE_OBSERVED_KERNEL_PLUS_OPTIMISTIC_HASH_NOT_DISTRIBUTED_ATOMIC_CAS',
        'training_started':False,'gpu_used':False,'model_weights_loaded':False,
        'restored_parent':resume_old_state['checkpoint'],
        'lock_repair':{'journal_mode':'wal','busy_timeout_ms':120000,'root_reader_connections_closed':True},
        'performance_upgrade':dict(resume_old_state['performance_upgrade'],checkpoint_readback_chunk_bytes=64*1024*1024)}
    (ROOT/'v3_latest_checkpoint_ref.json').write_text(json.dumps({'metadata':after_meta,'proof':proof},ensure_ascii=False,indent=2))
    # The frozen auditor and adapter are untouched. Only worker IO/locking
    # settings change; all token/source/split/duplicate gates remain active.
    worker_source=resume_payload['parent_worker_function']
    assert worker_source.count("auditor.db.execute('PRAGMA cache_size=-131072')")==1
    worker_source=worker_source.replace("auditor.db.execute('PRAGMA cache_size=-131072')",
        "auditor.db.execute('PRAGMA cache_size=-131072')\n        auditor.db.execute('PRAGMA busy_timeout=120000')\n        assert auditor.db.execute('PRAGMA journal_mode').fetchone()[0]=='wal'")
    assert worker_source.count("chunksize=8*1024*1024")==1
    worker_source=worker_source.replace('chunksize=8*1024*1024','chunksize=64*1024*1024')
    assert worker_source.count('try:auditor.db.backup(target_db)')==1
    worker_source=worker_source.replace('try:auditor.db.backup(target_db)',
        "try:\n            auditor.db.backup(target_db)\n            assert target_db.execute('PRAGMA journal_mode=DELETE').fetchone()[0]=='delete'")
    assert worker_source.count("work_api=build('drive','v3',credentials=credentials,cache_discovery=False)")==1
    worker_source=worker_source.replace("work_api=build('drive','v3',credentials=credentials,cache_discovery=False)",'work_api=g2_connected_api()')
    (resume_directory/'resumed_worker_function.py').write_text(worker_source)
    exec(compile(worker_source,'resumed_worker_function.py','exec'),globals())
    assert not any(t.is_alive() and t.name.startswith('MathVisionKidFiniteCPUDataAudit') for t in threading.enumerate())
    batch_adapter.install()
    full_audit_worker=threading.Thread(target=finite_full_data_audit_worker_v3,name='MathVisionKidFiniteCPUDataAuditV3',daemon=True)
    full_audit_worker.start()
    g2_resume_state.update(stage='APPEND_CHECKPOINT_RAW_VERIFIED_WORKER_RESUMED',checkpoint=proof,
        new_worker_alive=full_audit_worker.is_alive(),checkpoint_id_unchanged=True,parent_snapshot_retained=True)
    g2_resume_status()

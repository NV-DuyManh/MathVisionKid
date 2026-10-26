# Execute only in the already connected, authorized DATA_ONLY Colab kernel.
# Runtime-only working database; same Drive checkpoint ID, no training.
import io,json,sqlite3,hashlib,threading,time,uuid,shutil,base64,zlib,zipfile
from pathlib import Path
from datetime import datetime,timezone
from googleapiclient.http import MediaFileUpload,MediaIoBaseDownload
import httplib2,google_auth_httplib2

assert not full_audit_worker.is_alive(), 'Existing audit worker must stop first'
assert not any(t.is_alive() and t.name.startswith('MathVisionKidFiniteCPUDataAudit') for t in threading.enumerate())
assert not globals().get('g2_resume_thread') or not g2_resume_thread.is_alive()
resume_payload=json.loads(zlib.decompress(base64.b64decode(RESUME_PAYLOAD_B64)))
assert audit_v3.plan_identity(recipe_all)==resume_payload['previous_identity']
assert hashlib.sha256(Path(audit_v3.__file__).read_bytes()).hexdigest()==resume_payload['audit_code_sha256']
assert hashlib.sha256(Path(batch_module.__file__).read_bytes()).hexdigest()==resume_payload['adapter_code_sha256']
assert full_audit_worker_state['checkpoint']['fresh_raw_readback_verified']
resume_old_state=json.loads(json.dumps(full_audit_worker_state))
resume_closed_root_connections=[]
for resume_connection_name in ['g2db','confirmation_db','phase_db','probe_db','status_db']:
    resume_connection=globals().get(resume_connection_name)
    if isinstance(resume_connection,sqlite3.Connection):
        resume_connection.close()
        resume_closed_root_connections.append(resume_connection_name)
resume_directory=ROOT/'resume_after_g2_20261022';resume_directory.mkdir(exist_ok=True)
(resume_directory/'parent_worker_state.json').write_text(json.dumps(resume_old_state,ensure_ascii=False,indent=2))
g2_resume_state={'stage':'PREPARING_EXISTING_CHECKPOINT_APPEND','started_utc':datetime.now(timezone.utc).isoformat(),
    'previous_identity':resume_payload['previous_identity'],'next_identity':resume_payload['next_identity'],
    'checkpoint_id':EXISTING_V3_ID,'training_started':False,'gpu_used':False,'model_weights_loaded':False}
def g2_resume_status():
    g2_resume_state['updated_utc']=datetime.now(timezone.utc).isoformat()
    (resume_directory/'migration_status.json').write_text(json.dumps(g2_resume_state,ensure_ascii=False,indent=2))
def g2_connected_api():
    auth_http=google_auth_httplib2.AuthorizedHttp(credentials,http=httplib2.Http(timeout=120))
    return build('drive','v3',http=auth_http,cache_discovery=False)

def g2_migrate_resume():
    global recipe,recipe_all,recipe_pointer,pointer_all,V3_ID,v3_ref,writer_session,batch_adapter
    global full_audit_worker_state,full_audit_worker,finite_full_data_audit_worker_v3
    a=None
    try:
        api=g2_connected_api()
        # Fetch the published recipe directly on Colab, not through the PC.
        sink_recipe=io.BytesIO()
        dl_recipe=MediaIoBaseDownload(sink_recipe,api.files().get_media(fileId=resume_payload['progress_id'],supportsAllDrives=True),chunksize=64*1024*1024)
        done=False
        while not done:_,done=dl_recipe.next_chunk(num_retries=3)
        progress_bytes=sink_recipe.getvalue()
        assert hashlib.sha256(progress_bytes).hexdigest()==resume_payload['progress_sha256']
        with zipfile.ZipFile(io.BytesIO(progress_bytes)) as progress_zip:
            resume_recipe_bytes=progress_zip.read(resume_payload['next_recipe_pointer']['member'])
        assert hashlib.sha256(resume_recipe_bytes).hexdigest()==resume_payload['next_recipe_sha256']
        resume_next_recipe=json.loads(resume_recipe_bytes)
        assert audit_v3.plan_identity(resume_next_recipe)==resume_payload['next_identity']
        (resume_directory/'next_recipe.json').write_bytes(resume_recipe_bytes)
        metadata_fields='id,name,size,appProperties,modifiedTime,version'
        parent_meta=api.files().get(fileId=EXISTING_V3_ID,fields=metadata_fields,supportsAllDrives=True).execute()
        parent_proof=resume_old_state['checkpoint']
        props=parent_meta.get('appProperties',{})
        assert props.get('recipe_identity')==resume_payload['previous_identity']
        assert props.get('data_sha256')==parent_proof['sha256']
        assert props.get('writer_session')==resume_old_state['writer_session']
        snapshot=ROOT/'full_audit_v3_snapshot.sqlite'
        assert shutil.disk_usage(ROOT).free>V3_DB.stat().st_size+1024**3, 'Runtime disk lacks snapshot space'
        assert snapshot.is_file() and snapshot.stat().st_size==parent_proof['bytes']
        assert file_digest(snapshot)==parent_proof['sha256']
        parent_kept=ROOT/('parent_checkpoint_'+parent_proof['sha256']+'.sqlite')
        if parent_kept.exists():assert file_digest(parent_kept)==parent_proof['sha256']
        else:snapshot.rename(parent_kept)
        g2_resume_state['parent_verified_snapshot_preserved']=dict(parent_proof,runtime_path=str(parent_kept))
        # Root-created readers closed on their creating kernel thread above.
        # The stopped worker's connection was closed by its finally block.
        db=sqlite3.connect(V3_DB,timeout=120)
        try:
            db.execute('PRAGMA busy_timeout=120000')
            before_counts={t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['source_versions','samples','occurrences','issues']}
            before_members=list(db.execute('SELECT * FROM members ORDER BY id'))
            before_issues=list(db.execute('SELECT * FROM issues ORDER BY 1,2,3,4'))
            assert before_counts['samples']==1078096 and before_counts['source_versions']==1629842
            assert db.execute('PRAGMA journal_mode=WAL').fetchone()[0]=='wal'
        finally:db.close()
        g2_resume_state.update(stage='APPENDING_EXACT_RECIPE_WITHOUT_RESET',before_counts=before_counts)
        g2_resume_state['closed_root_read_connections']=resume_closed_root_connections
        g2_resume_status()
        migration=audit_v3.FullArchiveAudit.extend_recipe(V3_DB,recipe_all,resume_next_recipe)
        g2_resume_state['recipe_migration']=migration
        a=audit_v3.FullArchiveAudit(V3_DB,resume_next_recipe,tokenizer)
        a.db.execute('PRAGMA busy_timeout=120000');a.db.execute('PRAGMA cache_size=-131072')
        assert a.db.execute('PRAGMA journal_mode').fetchone()[0]=='wal'
        source_delta=resume_next_recipe['source_members'][len(recipe_all['source_members']):]
        chat_delta=resume_next_recipe['chat_members'][len(recipe_all['chat_members']):]
        assert len(source_delta)==len(chat_delta)==1
        assert source_delta[0]['rows']==64 and chat_delta[0]['rows']==256
        reader_now=GoogleDriveReader(api)
        cache_now=LazyDriveCache(reader_now,resume_next_recipe,ROOT/'full_audit_v3_worker_payload_cache')
        for e in source_delta+chat_delta:
            a.consume(e,cache_now[e['sha256']],max_rows=None,commit_every=64)
        after_counts={t:a.db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in before_counts}
        assert after_counts['source_versions']==before_counts['source_versions']+64
        assert after_counts['samples']==before_counts['samples']+256
        assert after_counts['occurrences']==before_counts['occurrences']+256
        assert list(a.db.execute('SELECT * FROM issues ORDER BY 1,2,3,4'))==before_issues
        after_members={x[0]:x for x in a.db.execute('SELECT * FROM members')}
        assert all(after_members[x[0]]==x for x in before_members)
        g2_resume_state.update(stage='NEW64_INDEXED_AND_256_CHAT_VERIFIED',after_counts=after_counts,
            prior_member_cursors_unchanged=True,prior_issues_preserved=True,
            bounded_new256_linkage_token_check_passed=True,new_report=a.report())
        g2_resume_status()
        a.db.commit()
        target=sqlite3.connect(snapshot)
        try:
            a.db.backup(target)
            assert target.execute('PRAGMA journal_mode=DELETE').fetchone()[0]=='delete'
        finally:target.close()
        snapshot_sha=file_digest(snapshot)
        assert api.files().get(fileId=EXISTING_V3_ID,fields=metadata_fields,supportsAllDrives=True).execute()==parent_meta
        writer_session=uuid.uuid4().hex
        new_props={'recipe_identity':resume_payload['next_identity'],'data_sha256':snapshot_sha,
            'purpose':'FULL_DATA_AUDIT_ONLY_NO_TRAINING','writer_session':writer_session}
        g2_resume_state.update(stage='UPLOADING_APPENDED_CHECKPOINT_SAME_ID',new_snapshot_sha256=snapshot_sha,
            new_snapshot_bytes=snapshot.stat().st_size)
        g2_resume_status()
        saved=api.files().update(fileId=EXISTING_V3_ID,
            body={'appProperties':new_props,'name':'MathVisionKid_FULL_DATA_AUDIT_V3_'+resume_payload['next_identity'][:16]+'.sqlite'},
            media_body=MediaFileUpload(str(snapshot),mimetype='application/vnd.sqlite3',resumable=True,chunksize=64*1024*1024),
            fields='id,size,appProperties',supportsAllDrives=True).execute()
        assert saved['id']==EXISTING_V3_ID
        g2_resume_state['uploaded_checkpoint_metadata']=saved
        class ResumeHashSink:
            def __init__(self):self.hasher=hashlib.sha256();self.size=0
            def write(self,data):
                self.hasher.update(data);self.size+=len(data)
                g2_resume_state['fresh_readback_bytes']=self.size
                return len(data)
        sink=ResumeHashSink();download=MediaIoBaseDownload(sink,api.files().get_media(fileId=EXISTING_V3_ID,supportsAllDrives=True),chunksize=64*1024*1024)
        g2_resume_state['stage']='FRESH_RAW_APPENDED_CHECKPOINT_READBACK';g2_resume_status()
        done=False
        while not done:
            _,done=download.next_chunk(num_retries=3)
            g2_resume_status()
        assert sink.size==snapshot.stat().st_size and sink.hasher.hexdigest()==snapshot_sha
        after_meta=api.files().get(fileId=EXISTING_V3_ID,fields='id,size,appProperties',supportsAllDrives=True).execute()
        assert after_meta==saved
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
    except Exception as e:
        g2_resume_state.update(stage='STOPPED_REQUIRES_RESUME_REPAIR',error_type=type(e).__name__,error=str(e))
        g2_resume_status()
    finally:
        if a is not None:a.close()

g2_resume_status()
g2_resume_thread=threading.Thread(target=g2_migrate_resume,name='MathVisionKidG2AppendCheckpointMigration',daemon=True)
g2_resume_thread.start()
print(json.dumps({'migration_started':True,'checkpoint_id':EXISTING_V3_ID,
    'existing_chat_cursor':1078096,'new_cases':64,'new_chats':256,'training_started':False}))

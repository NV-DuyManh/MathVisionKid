# Continue the already committed append; never reinsert/reset/re-migrate it.
from googleapiclient.http import build_http
def g2_connected_api():
    # Official client config leaves HTTP308 for resumable-upload handling.
    h=build_http();h.timeout=120
    auth_http=google_auth_httplib2.AuthorizedHttp(credentials,http=h)
    return build('drive','v3',http=auth_http,cache_discovery=False)

assert not full_audit_worker.is_alive() and not g2_resume_thread.is_alive()
assert g2_resume_state['recipe_migration']['next_identity']==resume_payload['next_identity']
assert g2_resume_state['after_counts']['samples']==1078352
g2_retry_parent=json.loads(json.dumps(g2_resume_state))
(resume_directory/'publication_redirect_failure_preserved.json').write_text(json.dumps(g2_retry_parent,ensure_ascii=False,indent=2))
if isinstance(globals().get('upgrade_check'),sqlite3.Connection):upgrade_check.close()
def g2_retry_checkpoint_publication():
    global writer_session
    a=None
    try:
        api=g2_connected_api()
        checkpoint_path=ROOT/'full_audit_v3_snapshot.sqlite'
        expected_sha=g2_retry_parent['new_snapshot_sha256']
        assert checkpoint_path.stat().st_size==g2_retry_parent['new_snapshot_bytes']
        assert file_digest(checkpoint_path)==expected_sha
        next_recipe_bytes=(resume_directory/'next_recipe.json').read_bytes()
        assert hashlib.sha256(next_recipe_bytes).hexdigest()==resume_payload['next_recipe_sha256']
        next_recipe=json.loads(next_recipe_bytes)
        a=audit_v3.FullArchiveAudit(V3_DB,next_recipe,tokenizer)
        a.db.execute('PRAGMA busy_timeout=120000')
        assert a.db.execute('PRAGMA journal_mode').fetchone()[0]=='wal'
        assert a.db.execute('SELECT count(*) FROM samples').fetchone()[0]==1078352
        assert a.db.execute('SELECT count(*) FROM source_versions').fetchone()[0]==1629906
        before=api.files().get(fileId=EXISTING_V3_ID,fields='id,size,appProperties,version,modifiedTime',supportsAllDrives=True).execute()
        props=before.get('appProperties',{})
        assert props.get('data_sha256') in [resume_old_state['checkpoint']['sha256'],expected_sha]
        assert props.get('writer_session') in [resume_old_state['writer_session'],writer_session]
        writer_session=uuid.uuid4().hex
        g2_resume_state.update(stage='RETRY_RESUMABLE_UPLOAD_OFFICIAL_HTTP308_HANDLING',
            redirect_failure_preserved=True,upload_error=str(g2_retry_parent.get('error')))
        g2_resume_status()
        newprops={'recipe_identity':resume_payload['next_identity'],'data_sha256':expected_sha,
            'purpose':'FULL_DATA_AUDIT_ONLY_NO_TRAINING','writer_session':writer_session}
        saved=api.files().update(fileId=EXISTING_V3_ID,
            body={'appProperties':newprops,'name':'MathVisionKid_FULL_DATA_AUDIT_V3_'+resume_payload['next_identity'][:16]+'.sqlite'},
            media_body=MediaFileUpload(str(checkpoint_path),mimetype='application/vnd.sqlite3',resumable=True,chunksize=64*1024*1024),
            fields='id,size,appProperties',supportsAllDrives=True).execute()
        g2_resume_state['uploaded_checkpoint_metadata']=saved
        class RetrySink:
            def __init__(self):self.hasher=hashlib.sha256();self.size=0
            def write(self,data):
                self.hasher.update(data);self.size+=len(data)
                g2_resume_state['fresh_readback_bytes']=self.size
                return len(data)
        sink=RetrySink();dl=MediaIoBaseDownload(sink,api.files().get_media(fileId=EXISTING_V3_ID,supportsAllDrives=True),chunksize=64*1024*1024)
        g2_resume_state['stage']='FRESH_RAW_APPENDED_CHECKPOINT_READBACK';g2_resume_status()
        done=False
        while not done:_,done=dl.next_chunk(num_retries=3);g2_resume_status()
        assert sink.size==checkpoint_path.stat().st_size and sink.hasher.hexdigest()==expected_sha
        after=api.files().get(fileId=EXISTING_V3_ID,fields='id,size,appProperties',supportsAllDrives=True).execute()
        assert after==saved
        g2_finish_verified_resume(a,expected_sha,sink,saved,after,next_recipe)
        a=None
    except Exception as e:
        g2_resume_state.update(stage='STOPPED_REQUIRES_RESUME_REPAIR',retry_error_type=type(e).__name__,retry_error=str(e))
        g2_resume_status()
    finally:
        if a is not None:a.close()
g2_resume_thread=threading.Thread(target=g2_retry_checkpoint_publication,name='MathVisionKidG2AppendCheckpointMigration',daemon=True)
g2_resume_thread.start()
print({'publication_retry_started':True,'already_checked_chat_rows':1078352,'no_data_reinserted':True,'training_started':False})

"""Finite CPU-only child audit; register in the already authorized Colab kernel.

The parent worker finishes first. All source/chat bytes and the parent snapshot
are retained. Only 60 original rows are re-consumed after exact read-time source
binding migration. No model, training, GPU, or candidate generation occurs.
"""
import hashlib
import importlib.util
import json
import sqlite3
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

assert not any(t.name == 'MathVisionKidStructural15PreserveSplitRepairResume' and t.is_alive()
               for t in threading.enumerate())
repair_runtime_dir = ROOT/'structural15_preserve_split_20261023'
repair_runtime_dir.mkdir(exist_ok=True)
assert not (repair_runtime_dir/'resume_repair_worker_status.json').exists(), 'Inspect existing repair, never restart blindly'
structural15_resume_state = {
    'state':'WAITING_FOR_PARENT_FULL_SCAN', 'registered_utc':datetime.now(timezone.utc).isoformat(),
    'parent_audit_identity':V3_ID, 'recipe_sha256':pointer_all['sha256'],
    'new_cases':0, 'new_chat_rows':0, 'source_chat_payload_bytes_changed':0,
    'training_started':False, 'gpu_used':False, 'model_weights_loaded':False,
}

def repair_save(name, value):
    data=(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode('utf8')
    path=repair_runtime_dir/name
    temporary=path.with_suffix(path.suffix+'.writing')
    temporary.write_bytes(data); temporary.replace(path)
    return {'name':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def repair_stage(stage, **details):
    structural15_resume_state.update(state=stage, observed_utc=datetime.now(timezone.utc).isoformat(), **details)
    repair_save('resume_repair_worker_status.json',structural15_resume_state)

def repair_import(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module)
    return module

def finish_exact_adapter_once():
    auditor=None
    try:
        full_audit_worker.join()
        final_metadata_thread.join()
        structural15_repair_thread.join()
        parent_state=dict(full_audit_worker_state)
        parent_report=parent_state['report'];parent_checkpoint=parent_state['checkpoint']
        assert parent_state['state']=='AUDIT_FINISHED_WITH_FINDINGS'
        assert parent_report['all_declared_members_scanned'] is True
        assert parent_report['unique_chat_rows_processed']==6502392
        assert parent_report['issues']=={'SOURCE_RAW_HASH_NOT_FOUND':60,'SOURCE_CHAT_LINKAGE_UNVERIFIED':60,'SOURCE_SPLIT_MISSING_OR_UNKNOWN':1,'CROSS_SPLIT_CANONICAL':36}
        assert parent_checkpoint['report_at_snapshot']==parent_report
        assert parent_checkpoint['fresh_raw_readback_verified'] is True
        repair_save('parent_finished_worker_state.json',parent_state)
        repair_save('parent_final_metadata_status.json',json.loads((qa_dir/'final_metadata_status.json').read_bytes()))
        parent_snapshot=ROOT/'full_audit_v3_snapshot.sqlite'
        assert parent_snapshot.stat().st_size==parent_checkpoint['bytes']
        assert file_digest(parent_snapshot)==parent_checkpoint['sha256']
        # Preserve the completed portable parent at its original path and Drive ID.
        repair_stage('PARENT_COMPLETE_PREPARING_SEPARATE_CHILD',parent_checkpoint=parent_checkpoint)
        sys.path.insert(0,str(repair_runtime_dir))
        structural=repair_import('exact_structural15_adapter',repair_runtime_dir/'exact_structural15_adapter.py')
        derived=repair_import('math_data_full_audit_structural15',repair_runtime_dir/'math_data_full_audit_structural15.py')
        migration=repair_import('migrate_structural15_adapter',repair_runtime_dir/'migrate_adapter_checkpoint_preserve_split.py')
        bindings_bytes=(repair_runtime_dir/'bindings.json').read_bytes()
        bindings=json.loads(bindings_bytes)
        qa_bytes=(repair_runtime_dir/'structural15_semantic_review.json').read_bytes()
        qa=json.loads(qa_bytes)
        child_identity=derived.plan_identity(recipe_all)
        assert child_identity!=V3_ID
        child_database=repair_runtime_dir/'structural15_adapter_full_audit.sqlite'
        migration_proof=json.loads((repair_runtime_dir/'migration_receipt.json').read_bytes())
        assert migration_proof['child_identity']==child_identity and migration_proof['parent_unchanged'] is True
        assert migration_proof['parent_issues_archived']==157 and migration_proof['target_rows_requeued']==60
        assert Path(migration_proof['destination'])==child_database and child_database.exists()
        guard=sqlite3.connect(child_database,timeout=5)
        try:
            assert guard.execute('SELECT identity FROM config').fetchone()[0]==child_identity
            assert guard.execute('SELECT next_line,complete,expected_rows FROM members WHERE id=?',(bindings['chat_member_key'],)).fetchone()==(511360,0,511420)
            assert dict(guard.execute('SELECT kind,count(*) FROM issues GROUP BY kind'))=={'CROSS_SPLIT_CANONICAL':36,'SOURCE_SPLIT_MISSING_OR_UNKNOWN':1}
            guard.execute('BEGIN IMMEDIATE');guard.rollback()
        finally:guard.close()
        repair_save('resumed_after_reader_lock_receipt.json',{'original_migration_receipt_preserved':True,
            'migration_id':migration_proof['migration_id'],'cursor':511360,'original_reader_lock_error_preserved':True,
            'parallel_read_checker_stopped':True,'write_lock_probe_passed':True,'training_started':False})
        repair_stage('RESUMED_EXACT_MIGRATED_CHILD_REAUDITING_ORIGINAL60',child_identity=child_identity,
                     migration_id=migration_proof['migration_id'])
        auditor=derived.FullArchiveAudit(child_database,recipe_all,tokenizer)
        auditor.db.execute('PRAGMA cache_size=-1048576')
        original_entry=next(e for e in recipe_all['chat_members'] if batch_module.member_key(e)==bindings['chat_member_key'])
        original_path=_chat_path
        assert original_path.stat().st_size==original_entry['bytes'] and file_digest(original_path)==original_entry['sha256']
        span=auditor.consume(original_entry,original_path,max_rows=None,commit_every=256)
        assert span['processed']==60 and span['complete'] is True
        repair_save('exact60_original_consume.json',span)
        finalized=migration.verify_finalized(auditor,migration_proof['migration_id'])
        report=finalized['report']
        expected_cursors={batch_module.member_key(e):(e['role'],e['rows'],1,e['rows'])
                          for e in recipe_all['source_members']+recipe_all['chat_members']}
        actual_cursors={r[0]:tuple(r[1:]) for r in auditor.db.execute('SELECT id,role,next_line,complete,expected_rows FROM members')}
        assert actual_cursors==expected_cursors and len(actual_cursors)==251
        assert auditor.db.execute('SELECT count(*) FROM samples WHERE sequence_tokens<=0 OR sequence_tokens>40960 OR completion_tokens<=0 OR completion_tokens>sequence_tokens').fetchone()[0]==0
        case_counts=dict(auditor.db.execute('SELECT split,count(DISTINCT case_id) FROM samples GROUP BY split'))
        assert case_counts=={'train':1625586,'validation':6,'test':6}
        repair_save('exact60_reaudit_verification.json',finalized)
        repair_stage('CHILD_FULL_LEDGER_VERIFIED_SAVING_CHECKPOINT')
        snapshot=repair_runtime_dir/'structural15_adapter_verified_snapshot.sqlite'
        assert not snapshot.exists()
        target=sqlite3.connect(snapshot)
        try:
            auditor.db.commit();auditor.db.backup(target)
            assert target.execute('PRAGMA journal_mode=DELETE').fetchone()[0]=='delete'
        finally:target.close()
        auditor.close();auditor=None
        snapshot_sha=file_digest(snapshot);snapshot_bytes=snapshot.stat().st_size
        checkpoint_name='MathVisionKid_FULL_AUDIT_STRUCTURAL15_ADAPTER_'+child_identity[:16]+'.sqlite'
        api=g2_connected_api()
        folder='19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n'
        existing=api.files().list(q="'"+folder+"' in parents and trashed=false and name='"+checkpoint_name+"'",
            fields='files(id,name,size,appProperties)',supportsAllDrives=True,includeItemsFromAllDrives=True).execute()['files']
        assert not existing,'Existing child artifact requires explicit recovery, no duplicate upload'
        remote=api.files().create(body={'name':checkpoint_name,'parents':[folder],
            'appProperties':{'purpose':'DATA_ONLY_EXACT_STRUCTURAL15_ADAPTER_CHECKPOINT',
                'recipe_identity':child_identity,'data_sha256':snapshot_sha,
                'parent_checkpoint_id':parent_checkpoint['id'],'parent_sha256':parent_checkpoint['sha256']}},
            media_body=MediaFileUpload(str(snapshot),mimetype='application/vnd.sqlite3',resumable=True),
            fields='id,name,size,appProperties',supportsAllDrives=True).execute()
        repair_stage('CHILD_CHECKPOINT_UPLOADED_VERIFYING_RAW',child_checkpoint_id=remote['id'],
                     child_checkpoint_bytes=snapshot_bytes,child_checkpoint_sha256=snapshot_sha,raw_readback_bytes=0)
        class HashSink:
            def __init__(self):self.h=hashlib.sha256();self.size=0
            def write(self,data):
                self.h.update(data);self.size+=len(data)
                structural15_resume_state['raw_readback_bytes']=self.size
                return len(data)
        sink=HashSink()
        download=MediaIoBaseDownload(sink,api.files().get_media(fileId=remote['id'],supportsAllDrives=True),chunksize=64*1024*1024)
        done=False
        while not done:_,done=download.next_chunk(num_retries=3)
        assert sink.size==snapshot_bytes and sink.h.hexdigest()==snapshot_sha
        after=api.files().get(fileId=remote['id'],fields='id,size,appProperties',supportsAllDrives=True).execute()
        assert int(after['size'])==snapshot_bytes and after['appProperties']['data_sha256']==snapshot_sha
        checkpoint={'id':remote['id'],'bytes':snapshot_bytes,'sha256':snapshot_sha,
            'fresh_raw_readback_verified':True,'report_at_snapshot':report,
            'observed_utc':datetime.now(timezone.utc).isoformat()}
        repair_save('child_checkpoint_raw_verified.json',checkpoint)
        repair_stage('CHECKPOINT_RAW_VERIFIED_FINAL_METADATA',child_checkpoint=checkpoint)
        # The finite anti-join keeps its exact original logic and signature pins;
        # its derived file changes only the independently computed child identity.
        anti=subprocess.run([sys.executable,str(repair_runtime_dir/'final_source_chat_antijoin_derived.py'),
            str(snapshot),str(repair_runtime_dir/'final_source_chat_antijoin.json'),
            '--protected-index',str(qa_dir/'protected_numeric_signatures.json'),
            '--holdout-index',str(qa_dir/'holdout_signatures.json')],capture_output=True,text=True,timeout=900)
        repair_save('final_antijoin_execution.json',{'returncode':anti.returncode,'stdout':anti.stdout[-4000:],
            'stderr':anti.stderr[-4000:],'question_payload_read':False})
        assert anti.returncode==0,'Preserve anti-join error; never promote source-only rows'
        classification=json.loads((repair_runtime_dir/'final_source_chat_antijoin.json').read_bytes())
        assert classification['counts']['unlinked_source_versions']==4308
        assert classification['counts']['classifications'].get('UNRESOLVED_QUARANTINE',0)==0
        raw_ref=repair_save('final_raw_v3_report_preserved.json',report)
        repair_stage('STRUCTURAL60_FIXED_SPLIT36_PRESERVED_PENDING_HASH_QA',
            checkpoint=checkpoint,recipe_identity=child_identity,
            recipe_sha256=pointer_all['sha256'],raw_report_artifact=raw_ref,
            source_only_classifications=classification['counts']['classifications'],
            all_original_chat_rows_reaudited_or_preserved=True,
            original_60_linkage_and_token_reaudit_complete=True,
            raw_cross_split_findings_preserved=36,
            current_text_technical_pass=False,TRAINING_DATASET_READY=False)
    except Exception as error:
        repair_stage('REPAIR_STOPPED_WITH_EVIDENCE',error_type=type(error).__name__,error=str(error))
    finally:
        if auditor is not None:auditor.close()

repair_stage('WAITING_FOR_PARENT_FULL_SCAN')
structural15_resume_thread=threading.Thread(target=finish_exact_adapter_once,
    name='MathVisionKidStructural15PreserveSplitRepairResume',daemon=True)
structural15_resume_thread.start()
print(json.dumps({'registered':True,'state':structural15_resume_state,'training_started':False}))

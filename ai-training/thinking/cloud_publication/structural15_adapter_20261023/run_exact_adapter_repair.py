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

assert not any(t.name == 'MathVisionKidStructural15ExactRepair' and t.is_alive()
               for t in threading.enumerate())
repair_runtime_dir = ROOT/'structural15_adapter_20261023'
repair_runtime_dir.mkdir(exist_ok=True)
assert not (repair_runtime_dir/'repair_worker_status.json').exists(), 'Inspect existing repair, never restart blindly'
structural15_repair_state = {
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
    structural15_repair_state.update(state=stage, observed_utc=datetime.now(timezone.utc).isoformat(), **details)
    repair_save('repair_worker_status.json',structural15_repair_state)

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
        parent_state=dict(full_audit_worker_state)
        parent_report=parent_state['report'];parent_checkpoint=parent_state['checkpoint']
        assert parent_state['state']=='AUDIT_FINISHED_WITH_FINDINGS'
        assert parent_report['all_declared_members_scanned'] is True
        assert parent_report['unique_chat_rows_processed']==6502392
        assert parent_report['issues']=={'SOURCE_RAW_HASH_NOT_FOUND':60,'SOURCE_CHAT_LINKAGE_UNVERIFIED':60,'SOURCE_SPLIT_MISSING_OR_UNKNOWN':1}
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
        migration=repair_import('migrate_structural15_adapter',repair_runtime_dir/'migrate_adapter_checkpoint.py')
        bindings_bytes=(repair_runtime_dir/'bindings.json').read_bytes()
        bindings=json.loads(bindings_bytes)
        qa_bytes=(repair_runtime_dir/'structural15_semantic_review.json').read_bytes()
        qa=json.loads(qa_bytes)
        child_identity=derived.plan_identity(recipe_all)
        assert child_identity!=V3_ID
        child_database=repair_runtime_dir/'structural15_adapter_full_audit.sqlite'
        migration_proof=migration.prepare_migration(parent_snapshot,child_database,recipe_all,recipe_all,
            bindings,qa,parent_identity=V3_ID,child_identity=child_identity,
            bindings_bytes=bindings_bytes,expected_bindings_sha256=structural.BINDINGS_SHA256,
            semantic_review_bytes=qa_bytes,parent_auditor_sha256=file_digest(Path(audit_v3.__file__)),
            recipe_sha256=pointer_all['sha256'])
        repair_save('migration_receipt.json',migration_proof)
        repair_stage('CHILD_MIGRATED_REAUDITING_EXACT_ORIGINAL_60',child_identity=child_identity,
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
                structural15_repair_state['raw_readback_bytes']=self.size
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
        adjudicator=repair_import('structural15_final_adjudication',repair_runtime_dir/'final_technical_adjudication_derived.py')
        with sqlite3.connect(snapshot.as_uri()+'?mode=ro',uri=True) as db:
            issue_rows=[dict(zip(('member','line','kind','detail'),r)) for r in db.execute('SELECT member,line,kind,detail FROM issues ORDER BY member,line,kind,detail')]
            diagnostic=db.execute('SELECT id,source_split,raw_sha,canonical_sha FROM source_versions WHERE id=?',('exhaustive_v1_div_1563_43',)).fetchall()
            assert len(diagnostic)==1
            diagnostic=dict(zip(('sample_id','split','raw_sha256','canonical_sha256'),diagnostic[0]))
            links=db.execute('SELECT count(*) FROM samples WHERE case_id=?',('exhaustive_v1_div_1563_43',)).fetchone()[0]
        members=[{'id':batch_module.member_key(e),'role':e['role'],'rows':e['rows']}
                 for e in recipe_all['source_members']+recipe_all['chat_members']]
        technical=adjudicator.adjudicate_final_v3_metadata(report,issue_rows,diagnostic,
            {'exhaustive_v1_div_1563_43':{'linked_chat_rows':links}},
            {'members':members,'unique_chat_rows':6502392,
             'unique_chat_rows_by_split':{'train':6502344,'validation':24,'test':24},'modes_per_case':4})
        raw_ref=repair_save('final_raw_v3_report_preserved.json',report)
        technical.update(checkpoint=checkpoint,raw_report_artifact=raw_ref,actual_cases_by_split=case_counts,
            exact_member_cursors_verified=True,per_row_token_lengths_verified=True,
            parent_raw_report_preserved=True,read_time_adapter_bindings_sha256=structural.BINDINGS_SHA256,
            tokenizer_revision=batch_module.L.REVISION,observed_utc=datetime.now(timezone.utc).isoformat())
        technical_ref=repair_save('final_candidate_chat_technical_adjudication.json',technical)
        manifest={'schema':'MathVisionKid.current_text_candidate_view_final_metadata.v1',
            'status':'CURRENT_TEXT_CANDIDATE_VIEW_TECHNICALLY_VERIFIED',
            'recipe_identity':child_identity,'recipe_sha256':pointer_all['sha256'],
            'candidate_chat_rows':6502344,'candidate_case_ids':1625586,
            'validation_chat_rows':24,'test_chat_rows':24,'raw_chat_rows_all_current_splits':6502392,
            'source_versions_retained':1629906,'source_only_audit_rows_retained':4308,
            'selection':'All current candidate rows with split=train; retain evaluation splits separately.',
            'core_cases':495,'core_nodes':165,'core_chat_rows':1980,
            'technical_adjudication':technical_ref,'checkpoint':checkpoint,'parent_checkpoint':parent_checkpoint,
            'physical_observation_tasks_pending':5,'constraints_pending':7,'asset_masters_pending':10,
            'g3_source_locator_pending':1,'whole_curriculum_certified':False,
            'all_rows_semantically_human_reviewed':False,'TRAINING_DATASET_READY':False,
            'training_started':False,'source_chat_payload_bytes_changed':0,
            'read_time_adapter_bindings_sha256':structural.BINDINGS_SHA256}
        manifest_ref=repair_save('final_current_text_candidate_manifest.json',manifest)
        repair_stage('FINAL_TEXT_TECHNICAL_EVIDENCE_COMPLETE_PENDING_CONTROL_PUBLICATION',
            manifest=manifest_ref,checkpoint=checkpoint,recipe_identity=child_identity,
            recipe_sha256=pointer_all['sha256'],source_only_classifications=classification['counts']['classifications'])
    except Exception as error:
        repair_stage('REPAIR_STOPPED_WITH_EVIDENCE',error_type=type(error).__name__,error=str(error))
    finally:
        if auditor is not None:auditor.close()

repair_stage('WAITING_FOR_PARENT_FULL_SCAN')
structural15_repair_thread=threading.Thread(target=finish_exact_adapter_once,
    name='MathVisionKidStructural15ExactRepair',daemon=True)
structural15_repair_thread.start()
print(json.dumps({'registered':True,'state':structural15_repair_state,'training_started':False}))

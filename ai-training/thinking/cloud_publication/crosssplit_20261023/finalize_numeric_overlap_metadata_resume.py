"""Finite CPU-only metadata closeout after the already registered child audit."""
import json,hashlib,sqlite3,threading,importlib.util,sys
from pathlib import Path
from datetime import datetime,timezone

assert not any(t.name=='MathVisionKidNumericOverlapFinalMetadataResume' and t.is_alive() for t in threading.enumerate())
numeric_closeout_dir=ROOT/'structural15_preserve_split_20261023'
numeric_pins_dir=ROOT/'crosssplit_20261023/pinned_metadata'
numeric_resume_state={'state':'WAITING_FOR_EXISTING_EXACT60_CHILD_AUDIT','registered_utc':datetime.now(timezone.utc).isoformat(),'new_cases':0,'new_chat_rows':0,'training_started':False,'TRAINING_DATASET_READY':False}

def numeric_save(name,value):
    raw=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    path=numeric_closeout_dir/name;temp=path.with_suffix(path.suffix+'.writing')
    temp.write_bytes(raw);temp.replace(path)
    return dict(name=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def numeric_stage(state,**details):
    numeric_resume_state.update(state=state,observed_utc=datetime.now(timezone.utc).isoformat(),**details)
    numeric_save('numeric_resume_status.json',numeric_resume_state)

def finish_numeric_metadata_once():
    try:
        structural15_resume_thread.join()
        worker=json.loads((numeric_closeout_dir/'resume_repair_worker_status.json').read_bytes())
        assert worker['state']=='STRUCTURAL60_FIXED_SPLIT36_PRESERVED_PENDING_HASH_QA',worker
        cp=json.loads((numeric_closeout_dir/'child_checkpoint_raw_verified.json').read_bytes())
        report=json.loads((numeric_closeout_dir/'final_raw_v3_report_preserved.json').read_bytes())
        assert cp==worker['checkpoint'] and cp['fresh_raw_readback_verified'] is True and cp['report_at_snapshot']==report
        assert cp['id']!=full_audit_worker_state['checkpoint']['id']
        machine_bytes=(numeric_pins_dir/'train17_numeric_overlap_machine_evidence_v2.json').read_bytes()
        assert hashlib.sha256(machine_bytes).hexdigest()=='e33cd3c47840ccdeb44bdb4efc118e3e03f830b0140ed762d5e9fc15efc5578d'
        ev=json.loads(machine_bytes)
        ev.update(train17_semantic_review_bytes=(numeric_pins_dir/'train17_semantic_review.json').read_bytes(),
            signature_crosswalk_bytes=(numeric_pins_dir/'signature_crosswalk.json').read_bytes(),
            numeric_overlap_policy_bytes=(numeric_pins_dir/'numeric_overlap_exception_policy.json').read_bytes(),
            diagnostic_bytes=(numeric_pins_dir/'diagnostic.json').read_bytes())
        module_path=numeric_pins_dir/'final_technical_adjudication_numeric_overlap.py'
        assert hashlib.sha256(module_path.read_bytes()).hexdigest()=='4286be6c44932af41a6bfc56255b560079d2f0b38369748efb3cfbdbd3980917'
        spec=importlib.util.spec_from_file_location('final_numeric_overlap_adjudicator',module_path)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        snapshot=numeric_closeout_dir/'structural15_adapter_verified_snapshot.sqlite'
        with sqlite3.connect(snapshot.as_uri()+'?mode=ro',uri=True,timeout=30) as db:
            db.execute('PRAGMA query_only=ON')
            issues=[dict(zip(('member','line','kind','detail'),r)) for r in db.execute('SELECT member,line,kind,detail FROM issues ORDER BY member,line,kind,detail')]
            rows=db.execute('SELECT id,source_split,raw_sha,canonical_sha FROM source_versions WHERE id=?',('exhaustive_v1_div_1563_43',)).fetchall()
            assert len(rows)==1
            source=dict(zip(('sample_id','split','raw_sha256','canonical_sha256'),rows[0]))
            links=db.execute('SELECT count(*) FROM samples WHERE case_id=?',('exhaustive_v1_div_1563_43',)).fetchone()[0]
        members=[dict(id=batch_module.member_key(e),role=e['role'],rows=e['rows']) for e in recipe_all['source_members']+recipe_all['chat_members']]
        numeric_stage('ADJUDICATING_EXACT_CURRENT_RECIPE_NUMERIC_OVERLAP')
        technical=module.adjudicate_final_v3_metadata(report,issues,source,
            {'exhaustive_v1_div_1563_43':{'linked_chat_rows':links}},
            {'members':members,'unique_chat_rows':6502392,'unique_chat_rows_by_split':{'train':6502344,'validation':24,'test':24},'modes_per_case':4},ev)
        technical.update(checkpoint=cp,machine_evidence_sha256=hashlib.sha256(machine_bytes).hexdigest(),
            source_chat_payload_bytes_changed=0,training_started=False,whole_curriculum_certified=False,
            all_rows_semantically_human_reviewed=False,observed_utc=datetime.now(timezone.utc).isoformat())
        technical_ref=numeric_save('final_candidate_chat_technical_adjudication.json',technical)
        anti=json.loads((numeric_closeout_dir/'final_source_chat_antijoin.json').read_bytes())
        assert anti['counts']['unlinked_source_versions']==4308 and anti['counts']['classifications'].get('UNRESOLVED_QUARANTINE',0)==0
        manifest=dict(schema='MathVisionKid.current_text_candidate_view_final_metadata.v1',
            status=technical['status'],recipe_identity=report['identity'],recipe_sha256=pointer_all['sha256'],
            candidate_chat_rows=6502344,candidate_case_ids=1625586,validation_chat_rows=24,test_chat_rows=24,
            raw_chat_rows_all_current_splits=6502392,source_versions_retained=1629906,source_only_audit_rows_retained=4308,
            selection='ALL_CURRENT_TRAIN_CANDIDATES_WITH_EVALUATION_SPLITS_RETAINED_SEPARATELY',
            source_only_classifications=anti['counts']['classifications'],numeric_expression_disjoint=False,
            scope='CURRENT_RECIPE_ONLY',protected_unread_or_global_eval_independence='NOT_CLAIMED',
            core_cases=495,core_nodes=165,core_chat_rows=1980,checkpoint=cp,parent_checkpoint=full_audit_worker_state['checkpoint'],
            technical_adjudication=technical_ref,source_chat_payload_bytes_changed=0,new_cases=0,new_chat_rows=0,
            physical_observation_tasks_pending=5,constraints_pending=7,asset_masters_pending=10,g3_source_locator_pending=1,
            historical_accepted_case_counter=1629922,historical_source_counter_difference_unresolved=16,
            whole_curriculum_certified=False,all_rows_semantically_human_reviewed=False,TRAINING_DATASET_READY=False,
            training_started=False,gpu_used=False,model_weights_loaded=False)
        manifest_ref=numeric_save('final_current_text_candidate_manifest.json',manifest)
        runtime=dict(observed_utc=datetime.now(timezone.utc).isoformat(),worker_alive=False,final_metadata_alive=False,
            structural15_repair2_alive=False,worker_state='AUDIT_FINISHED_WITH_FINDINGS',checkpoint=cp,report=report,
            committed_physical_chat_rows=6502392,unique_chat_rows_processed=6502392,expected_raw_chat_rows=6502392,
            issues_now=report['issues'],parent_checkpoint=full_audit_worker_state['checkpoint'],
            source_chat_payload_bytes_changed=0,training_started=False,gpu_used=False,model_weights_loaded=False)
        numeric_save('final_runtime_observation.json',runtime)
        numeric_stage('FINAL_CURRENT_RECIPE_TECHNICAL_EVIDENCE_COMPLETE_PENDING_CONTROL_PUBLICATION',
            checkpoint=cp,recipe_identity=report['identity'],recipe_sha256=pointer_all['sha256'],
            technical_adjudication=technical_ref,manifest=manifest_ref,numeric_expression_disjoint=False,
            source_only_classifications=anti['counts']['classifications'])
    except Exception as error:
        numeric_stage('NUMERIC_CLOSEOUT_STOPPED_WITH_EVIDENCE',error_type=type(error).__name__,error=str(error))

numeric_stage('WAITING_FOR_EXISTING_EXACT60_CHILD_AUDIT')
numeric_resume_thread=threading.Thread(target=finish_numeric_metadata_once,name='MathVisionKidNumericOverlapFinalMetadataResume',daemon=True)
numeric_resume_thread.start()
print(json.dumps(numeric_resume_state,ensure_ascii=False))

"""Publish actual completed metadata to the four existing Drive controls only."""
import json,threading,importlib.util,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone

assert not any(t.name=='MathVisionKidFinalFourControlsPublication' and t.is_alive() for t in threading.enumerate())
publication_dir=ROOT/'crosssplit_20261023/control_publication'
publication_code_dir=ROOT/'crosssplit_20261023/publication_code'
publication_audit_dir=ROOT/'structural15_preserve_split_20261023'
publication_pins_dir=ROOT/'crosssplit_20261023/pinned_metadata'
cloud_closeout_publication_state={'state':'WAITING_FOR_ACTUAL_COMPLETED_CHILD_AND_NUMERIC_EVIDENCE','registered_utc':datetime.now(timezone.utc).isoformat(),'training_started':False,'TRAINING_DATASET_READY':False,'same_control_ids':True}

def publication_stage(stage,**details):
    cloud_closeout_publication_state.update(state=stage,observed_utc=datetime.now(timezone.utc).isoformat(),**details)
    (publication_dir/'publication_status.json').write_text(json.dumps(cloud_closeout_publication_state,ensure_ascii=False,sort_keys=True,indent=2)+'\n')

def publication_import(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module

def publish_completed_four_controls_once():
    try:
        numeric_resume2_thread.join();cloud_control_parent_thread.join()
        assert numeric_resume2_state['state']=='FINAL_CURRENT_RECIPE_TECHNICAL_EVIDENCE_COMPLETE_PENDING_CONTROL_PUBLICATION',numeric_resume2_state
        assert cloud_control_parent_state['state']=='ALL_FOUR_PARENT_METADATA_CONTROLS_RAW_VERIFIED',cloud_control_parent_state
        parents=json.loads((publication_dir/'parent_controls_raw_verified.json').read_bytes())
        final_runtime=json.loads((publication_audit_dir/'final_runtime_observation.json').read_bytes())
        technical=json.loads((publication_audit_dir/'final_candidate_chat_technical_adjudication.json').read_bytes())
        anti=json.loads((publication_audit_dir/'final_source_chat_antijoin.json').read_bytes())
        childcp=json.loads((publication_audit_dir/'child_checkpoint_raw_verified.json').read_bytes())
        parentcp=full_audit_worker_state['checkpoint']
        evidence={}
        for folder,prefix in ((publication_code_dir,'code_and_resume/'),(publication_audit_dir,'actual_audit/'),(publication_pins_dir,'pinned_qa/')):
            for path in folder.iterdir():
                if path.is_file() and path.suffix in ('.py','.json','.md'):
                    assert path.stat().st_size<16*1024*1024
                    evidence[prefix+path.name]=str(path)
        for name in ('parent_controls_raw_verified.json','parent_read_status.json','notebook_raw_verified.json'):
            path=publication_dir/name
            if path.exists():evidence['control_readbacks/'+name]=str(path)
        for name in ('signature_crosswalk.json','final_snapshot_read_cache_receipt.json','child_read_cache_receipt.json','large_cache_integrity_receipt.json'):
            path=ROOT/'crosssplit_20261023'/name
            if path.exists():evidence['diagnostic_history/'+name]=str(path)
        prepare=publication_import('current_recipe_cloud_control_prepare',publication_code_dir/'prepare_cloud_closeout_controls.py')
        transaction=publication_import('current_recipe_cloud_control_transaction',publication_code_dir/'cloud_control_transaction.py')
        publication_stage('PREPARING_FOUR_CONTROLS_FROM_ACTUAL_VERIFIED_EVIDENCE')
        prepared=prepare.prepare_controls(parents,publication_code_dir,evidence,
            publication_dir/'prepared_final',final_runtime,technical,anti,parentcp,childcp)
        publication_stage('PREPARED_PUBLISHING_SAME_IDS_WITH_STATE_LAST',prepared_controls=prepared['controls'])
        receipt=transaction.publish_controls(g2_connected_api(),parents,prepared['controls'],
            publication_dir,receipt_path=publication_dir/'four_controls_remote_verified.json')
        assert len(receipt['verified_writes'])==4 and [x['kind'] for x in receipt['verified_writes']]==['progress','chat','context','state']
        assert all(x['fresh_raw_readback_verified'] is True for x in receipt['verified_writes'])
        publication_stage('ALL_FOUR_CONTROLS_SAME_IDS_FRESH_RAW_VERIFIED',verified_controls=receipt['verified_writes'],
            checkpoint=childcp,recipe_sha256=pointer_all['sha256'],scope='CURRENT_RECIPE_ONLY',numeric_expression_disjoint=False,
            source_chat_payload_bytes_changed=0,new_cases=0,new_chat_rows=0,physical_observation_tasks_pending=5,
            constraints_pending=7,asset_masters_pending=10,g3_source_locator_pending=1)
    except Exception as error:
        publication_stage('CONTROL_PUBLICATION_STOPPED_WITH_EVIDENCE',error_type=type(error).__name__,error=str(error))

publication_stage('WAITING_FOR_ACTUAL_COMPLETED_CHILD_AND_NUMERIC_EVIDENCE')
cloud_closeout_publication_thread=threading.Thread(target=publish_completed_four_controls_once,name='MathVisionKidFinalFourControlsPublication',daemon=True)
cloud_closeout_publication_thread.start()
print(json.dumps(cloud_closeout_publication_state,ensure_ascii=False))

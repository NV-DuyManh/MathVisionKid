"""Derive a scoped full-text release; preserve whole-curriculum pending evidence."""
import hashlib, json, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

RECIPE_SHA='1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8'
IDENTITY='6faccfa8b6cae5ae100cdd4777c3481b6d193cb79acae2679086ec8e25718f56'
STATUS='CURRENT_RECIPE_ONLY_TECHNICAL_PASS_WITH_HASH_BOUND_NUMERIC_OVERLAP_AND_REGRESSION_EXCLUSION'
COUNTS={'train':6502344,'validation':24,'test':24}
PREFIX='full_text_training_release_20261023/'
IDS={'progress':'1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX','chat':'1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6','context':'13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9','state':'1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme'}
def sha(b):return hashlib.sha256(b).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def main(parent,out,code):
    parent=Path(parent);out=Path(out);code=Path(code);out.mkdir(parents=True,exist_ok=True)
    old={k:(parent/('parent_'+k+('.zip' if k=='progress' else '.md' if k=='context' else '.json'))).read_bytes() for k in IDS}
    state=json.loads(old['state']);chat=json.loads(old['chat'])
    baseline=json.loads((parent/'parent_pins.json').read_bytes())
    for k,b in old.items():
        assert baseline[k]['id']==IDS[k] and baseline[k]['bytes']==len(b) and baseline[k]['sha256']==sha(b)
    from io import BytesIO
    with zipfile.ZipFile(BytesIO(old['progress'])) as archive:
        assert len(archive.namelist())==len(set(archive.namelist()))
        assert not any(n.startswith(PREFIX) for n in archive.namelist()),'Existing release: resume it, do not duplicate'
        pointer=state['latest_all_data_union_recipe']; recipe_bytes=archive.read(pointer['member'])
        assert pointer['sha256']==RECIPE_SHA and sha(recipe_bytes)==RECIPE_SHA
        recipe=json.loads(recipe_bytes);assert not recipe['pending_discovery']
        p='crosssplit_final_closeout_20261023/actual_audit/'
        source_bytes=archive.read(p+'final_current_text_candidate_manifest.json');source=json.loads(source_bytes)
        adjudication_bytes=archive.read(p+'final_candidate_chat_technical_adjudication.json');adjudication=json.loads(adjudication_bytes)
        assert source['status']==adjudication['status']==STATUS and source['recipe_identity']==IDENTITY
        assert source['technical_adjudication']['sha256']==sha(adjudication_bytes)
        report=adjudication['raw_report_preserved']
        assert report['actual_rows_by_split']==COUNTS
        assert report['all_declared_members_scanned'] and report['members_complete']==report['members_expected']==251
        assert report['source_linkage_unverified_rows']==0 and report['incomplete_four_mode_cases']==0 and report['exact_duplicate_references']==0
        assert report['source_hash_origins']['STRUCTURAL15_RAW_CANONICAL_AND_CHAT_HASH_VERIFIED']==60
        assert report['max_sequence_tokens']==1481 and report['max_completion_tokens']==1367
        assert source['core_cases']==495 and source['candidate_chat_rows']==COUNTS['train']
        assert source['source_only_classifications']=={'protected_numeric':4099,'regression_only':1,'selected_holdout':208}
        assert adjudication['diagnostic_exclusion']['linked_chat_rows']==0
        assert adjudication['numeric_overlap_adjudication']['current_group_conflicts']==0
        assert adjudication['numeric_overlap_adjudication']['current_normalized_question_conflicts']==0
        assert source['source_chat_payload_bytes_changed']==adjudication['source_chat_payload_bytes_changed']==0
        assert adjudication['machine_evidence_sha256']=='e33cd3c47840ccdeb44bdb4efc118e3e03f830b0140ed762d5e9fc15efc5578d'
    prior_authority=code/'owner_scope_authorization.json'
    now=json.loads(prior_authority.read_bytes())['observed_utc'] if prior_authority.exists() else datetime.now(timezone.utc).isoformat()
    authority={'schema':'MathVisionKid.owner_full_text_training_authorization.v1','observed_utc':now,
      'origin':'DIRECT_HUMAN_USER_REPLY_IN_CURRENT_CONVERSATION',
      'scope_choice_exact':'Train toàn bộ phần văn bản trước; bổ sung hình ảnh/thực hành sau',
      'instruction_exact':'vậy làm nốt đi, rồi  vào việc train chứ trì hoãn quá lâu rồi',
      'train_all_current_train_split':True,'sampling_or_balanced_subset_authorized':False,
      'new_human_content_review_attested':False,'paid_resources_authorized':False}
    release={'schema':'MathVisionKid.text_training_readiness.v1','observed_utc':now,
      'status':STATUS,'readiness_status':'READY_FOR_FULL_TEXT_TRAINING',
      'TEXT_TRAINING_DATASET_READY':True,'TRAINING_DATASET_READY':False,
      'scope':'TEXT_ONLY_ALL_CURRENT_TRAIN_CANDIDATES','modality':'text','recipe_sha256':RECIPE_SHA,
      'recipe_identity':IDENTITY,'recipe_pointer':pointer,'rows_by_split':COUNTS,
      'source_case_ids':1625586,'core_cases':495,'core_chat_rows':1980,'core_nodes':165,
      'selection':'ALL_CURRENT_TRAIN_CANDIDATES_WITH_EVALUATION_SPLITS_RETAINED_SEPARATELY',
      'sampling':False,'train_row_limit':None,'balanced_subset_selected':False,
      'acceptance_basis':'OWNER_PREAUTHORIZED_ACCEPTANCE_AND_COMPLETED_CURRENT_RECIPE_TECHNICAL_ADJUDICATION',
      'source_candidate_manifest':{'member':p+'final_current_text_candidate_manifest.json','bytes':len(source_bytes),'sha256':sha(source_bytes)},
      'technical_adjudication':{'member':p+'final_candidate_chat_technical_adjudication.json','bytes':len(adjudication_bytes),'sha256':sha(adjudication_bytes)},
      'checkpoint':source['checkpoint'],'all_declared_members_scanned':True,'candidate_source_linkage_unverified_rows':0,
      'numeric_expression_disjoint':False,'numeric_overlap_policy':'EXACT_HASH_BOUND_OWNER_AUTHORIZED_EXCEPTION_AFTER_QA',
      'global_or_protected_unread_eval_independence':'NOT_CLAIMED','raw_parent_findings_preserved':report['issues'],
      'source_only_audit_rows_retained':4308,'source_only_classifications':source['source_only_classifications'],
      'historical_counter_difference_unresolved':16,'human_verification_scope':'EXISTING_ENUMERATED_SIGNOFF_HASHES_ONLY',
      'new_human_signoffs_created':0,'all_rows_semantically_human_reviewed':False,
      'whole_curriculum_certified':False,'vision_or_physical_capability_certified':False,
      'deferred_requirements':{'actual_observation_tasks':5,'constraints':7,'asset_masters':10,'g3_exact_source_locator':1},
      'model':'Qwen/Qwen3-1.7B','model_revision':'70d244cc86ccca08cf5af4e1e306ecf908b1ad5e',
      'max_sequence_tokens':2048,'audited_max_sequence_tokens':1481,'silent_truncation_allowed':False,
      'loss_mask':'ASSISTANT_COMPLETION_ONLY_INCLUDING_SINGLE_EOT','enable_thinking':False,
      'initial_epoch_count':1,'training_started':False,'gpu_used_for_this_release':False,
      'source_chat_payload_bytes_changed':0,'new_cases':0,'new_chat_rows':0}
    additions={'release_manifest.json':encoded(release),'owner_scope_authorization.json':encoded(authority)}
    for name in ('full_text_training_contract.py','test_full_text_training_contract.py','g3_locator_reaudit.json','full_text_training_run.py','prepare_full_text_release.py'):
        path=code/name
        if path.exists():additions['code_and_evidence/'+name]=path.read_bytes()
    thinking=code.parents[1]
    for name in ('exhaustive_colab_loader.py','math_data_archive_audit.py','math_data_portable_resume.py','math_data_candidate_stream.py','math_data_drive_bootstrap.py','train_teacher_math_v3.py'):
        additions['runtime_dependencies/'+name]=(thinking/name).read_bytes()
    additions['code_hashes.json']=encoded({name:dict(bytes=len(raw),sha256=sha(raw)) for name,raw in additions.items() if name.endswith('.py')})
    release_ref={'progress_id':IDS['progress'],'member':PREFIX+'release_manifest.json','sha256':sha(additions['release_manifest.json']),'bytes':len(additions['release_manifest.json']),
                 'scope':release['scope'],'TEXT_TRAINING_DATASET_READY':True,'rows_by_split':COUNTS}
    for document in (state,chat):
        if document.get('text_training_release'):raise ValueError('Existing text release must be resumed')
        document['TEXT_TRAINING_DATASET_READY']=True;document['text_training_release']=release_ref
        document['training_started']=False;document['TRAINING_DATASET_READY']=False
        document['training_readiness_scope']='FULL_CURRENT_TEXT_READY; VISION_PHYSICAL_AND_G3_LOCATOR_DEFERRED_BY_OWNER'
        document['owner_full_text_training_authorization']=authority
    chat.setdefault('recommended_training_view_history',[]).append(chat.get('recommended_training_view'))
    chat['recommended_training_view']=release_ref
    chat['selection']='ALL_6502344_CURRENT_TRAIN_CHAT_ROWS; NO_BALANCED_SUBSET; VALIDATION24_TEST24_SEPARATE'
    state.setdefault('training_readiness_scope_history',[]).append(json.loads(old['state']).get('training_readiness_scope'))
    journal=('\n\n### Nhật ký 23/10/2026 — chủ chọn train toàn bộ văn bản trước\n'
      f'Mốc {now}: chủ trực tiếp chọn “Train toàn bộ phần văn bản trước; bổ sung hình ảnh/thực hành sau”. '
      'Chốt phạm vi TEXT_ONLY_ALL_CURRENT_TRAIN_CANDIDATES:6502344train/24validation/24test,495core/165node/1980corechat. '
      'TEXT_TRAINING_DATASET_READY=true theo kết luận kỹ thuật current-recipe và quyền owner preauthorization; TRAINING_DATASET_READY toàn chương trình vẫn false. '
      'Không sinh lại dữ liệu, không dùng tập5024 hoặc lấy mẫu. RecipeSHA1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8 giữ nguyên;251member đã quét,0linkageunverified,0thiếumode,0exactduplicate. '
      '36numeric warnings được adjudicate bằng đúnghash và quyền chủ;1regressiononly không cóchat vẫn loại khỏitrain. Rawreport/history/frozen/eval được giữ; không khẳng định độc lập số học của test. '
      '4308sourceonly giữ4099protected/208holdout/1regression; chênhcounter16 chưa giải thích.299human signoff chỉ đúng hash cũ; không tạo humanreview mới. '
      'Hoãn5task quan sát thật/7constraints,10assetmasters,1G3locator theo phạm vi chủ đã chọn; không giả đã cóảnh/sốđo thật. '
      'Model đíchQwen3-1.7B revision70d244cc86ccca08cf5af4e1e306ecf908b1ad5e;2048token khôngcắtngầm,assistant-onlyloss. '
      'Đây là chốt dữ liệu và quyền train; training_started=false cho đến khi optimizer thực sự chạy.\n').encode()
    (out/'next_progress.zip').write_bytes(old['progress'])
    with zipfile.ZipFile(out/'next_progress.zip','a',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,b in additions.items():archive.writestr(PREFIX+name,b)
    with zipfile.ZipFile(BytesIO(old['progress'])) as before,zipfile.ZipFile(out/'next_progress.zip') as after:
        assert len(after.namelist())==len(set(after.namelist()))
        for name in before.namelist():assert after.read(name)==before.read(name)
    values={'chat':encoded(chat),'context':old['context']+journal,'state':encoded(state)}
    for k,b in values.items():(out/('next_'+k+('.md' if k=='context' else '.json'))).write_bytes(b)
    pins={k:dict(id=IDS[k],bytes=(out/('next_'+k+('.zip' if k=='progress' else '.md' if k=='context' else '.json'))).stat().st_size,
       sha256=sha((out/('next_'+k+('.zip' if k=='progress' else '.md' if k=='context' else '.json'))).read_bytes())) for k in IDS}
    (code/'text_training_release_manifest.json').write_bytes(additions['release_manifest.json'])
    (code/'owner_scope_authorization.json').write_bytes(additions['owner_scope_authorization.json'])
    (out/'prepared_pins.json').write_bytes(encoded(pins))
    print(json.dumps({'prepared_controls':pins,'release':release_ref,'all_parent_zip_member_bytes_preserved':True,'training_started':False},ensure_ascii=False))
if __name__=='__main__':main(*sys.argv[1:])

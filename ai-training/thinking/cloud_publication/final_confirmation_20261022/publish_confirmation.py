# Append the exact finite495 confirmation while expanded audit keeps running.
confirmation_prefix='final_confirmation_20261022/'
confirmation_before={};confirmation_meta={}
for key,ref in receipt['controls'].items():
    before=phase_metadata(ref['id']);raw=phase_raw(ref['id']);after=phase_metadata(ref['id'])
    assert before==after and phase_sha(raw)==ref['sha256'],key+' changed since previous exact publication'
    confirmation_before[key]=raw;confirmation_meta[key]=after
confirmation_state=json.loads(confirmation_before['state']);confirmation_chat=json.loads(confirmation_before['chat'])
assert confirmation_state['finite_core_cases']==495 and confirmation_state['finite_core_nodes']==165
confirmation_state['finite_core_completion_confirmation']=confirmation_core_evidence
confirmation_chat['finite_core_completion_confirmation']=confirmation_core_evidence
confirmation_state['updated_utc']=datetime.now(timezone.utc).isoformat()
with sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True,timeout=3) as confirmation_db:
    confirmation_n=confirmation_db.execute('SELECT count(*) FROM samples').fetchone()[0]
confirmation_observed={'observed_utc':datetime.now(timezone.utc).isoformat(),'worker_alive':full_audit_worker.is_alive(),
    'unique_chat_rows_committed':confirmation_n,'live_batch_stats':dict(batch_adapter.stats),
    'checkpoint':full_audit_worker_state['checkpoint'],'full_archive_complete':False,'training_started':False}
assert confirmation_observed['worker_alive']
confirmation_state.setdefault('data_only_colab_observation_history',[]).append(confirmation_state['latest_colab_runtime_observation'])
confirmation_state['latest_colab_runtime_observation']=dict(confirmation_state['latest_colab_runtime_observation'],
    observed_utc=confirmation_observed['observed_utc'],unique_chat_rows_committed=confirmation_n,
    live_report=full_audit_worker_state.get('report'),batch_adapter_stats=dict(batch_adapter.stats),
    evidence_member=confirmation_prefix+'runtime_observed.json')
confirmation_chat['latest_colab_runtime_observation']=confirmation_state['latest_colab_runtime_observation']
confirmation_context=confirmation_before['context'].decode('utf8')
confirmation_marker='### Nhật ký 22/10/2026 — xác nhận riêng bộ lõi 495 đã hoàn tất'
assert confirmation_marker not in confirmation_context
confirmation_delta='\n\n'+confirmation_marker+'\n'
confirmation_delta+='Đã tái kiểmhash cả accepted782, chat3128 vàmanifest782 của releasefinite495: tấtcả khớp bảnđóngbăng, finalcoreaudit hash1592402a90e3117772e33258b82254cf7aa7c44eacf3fedcc0dd6f25ffd2db66 vẫnPASSED_FINITE_DATA_AUDIT. Xác nhận hoàn tất495/495core,165/165node,1980corechat. Đây là xác nhận lại releaseđãcó, khôngsoạnlại/khôngtăngđếm hoặcchọn tậpnhỏđểtrain.\n'
confirmation_delta+=f"Kho mởrộng vẫn đangkiểm: {confirmation_n}chat đãcommit tại {confirmation_observed['observed_utc']}. Khônggộp xácnhậnbộlõi thànhfullarchivepass. TrongfolderDriveđúngID chưa thấy góiAntigravity mới ởmốcreadmetadata; đãhỏi chủlinknếukếquả nằmchỗkhác.38G2tasks/50constraints và10asset/1G3locator chưađược tựđóng. Khôngtrain/GPU/weights, khôngđổi299signoff, khôngxóadữliệu.\n"
confirmation_delta+='Evidence trongPROGRESS/final_confirmation_20261022. CậpnhậtbốncontrolcùngIDs, STATEcuối vàfreshrawreadback từngfile; TRAINING_DATASET_READY=false chophạmvi toànkho mởrộng.\n'
confirmation_context+=confirmation_delta
confirmation_buffer=io.BytesIO()
with zipfile.ZipFile(io.BytesIO(confirmation_before['progress'])) as old,zipfile.ZipFile(confirmation_buffer,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as new:
    for info in old.infolist():new.writestr(info,old.read(info.filename))
    additions={'core_release_reverified.json':phase_json(confirmation_core_evidence),
        'runtime_observed.json':phase_json(confirmation_observed),
        'external_folder_metadata.json':phase_json(confirmation_files),
        'publish_confirmation.py':confirmation_publish_source.encode('utf8'),
        'parent_chat.json':confirmation_before['chat'],'parent_state.json':confirmation_before['state'],
        'parent_context.md':confirmation_before['context']}
    for name,blob in additions.items():
        member=confirmation_prefix+name;assert member not in old.namelist();new.writestr(member,blob)
with zipfile.ZipFile(io.BytesIO(confirmation_before['progress'])) as old,zipfile.ZipFile(io.BytesIO(confirmation_buffer.getvalue())) as new:
    assert all(old.read(name)==new.read(name) for name in old.namelist())
phase_pre_meta=confirmation_meta
confirmation_receipts={}
confirmation_receipts['progress']=phase_update_verified('progress',confirmation_buffer.getvalue(),'application/zip')
confirmation_receipts['chat']=phase_update_verified('chat',phase_json(confirmation_chat),'application/json')
confirmation_receipts['context']=phase_update_verified('context',confirmation_context.encode('utf8'),'text/markdown')
confirmation_receipts['state']=phase_update_verified('state',phase_json(confirmation_state),'application/json')
confirmation_result={'controls':confirmation_receipts,'state_written_last':True,'finite_core_confirmed_complete':True,
    'finite_core_cases':495,'finite_core_nodes':165,'full_expanded_dataset_complete':False,'training_started':False,
    'observed_utc':confirmation_observed['observed_utc'],'unique_chat_rows_committed':confirmation_n}
print(json.dumps(confirmation_result,ensure_ascii=False))

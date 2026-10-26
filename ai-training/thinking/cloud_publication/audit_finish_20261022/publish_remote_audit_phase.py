# Use the existing, user-authorized Colab Drive session after Drive plugin's
# Unknown-tool error. Keep all corpus/checkpoint bytes on cloud/runtime.
import io,json,hashlib,zipfile,base64,sqlite3,threading
from datetime import datetime,timezone
from googleapiclient.http import MediaIoBaseDownload,MediaIoBaseUpload
phase_api=build('drive','v3',credentials=credentials,cache_discovery=False)
phase_root=ROOT/'audit_finish_20261022';phase_root.mkdir(exist_ok=True)
def phase_sha(b):return hashlib.sha256(b).hexdigest()
def phase_json(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
def phase_metadata(file_id):
    return phase_api.files().get(fileId=file_id,fields='id,name,mimeType,size,version,modifiedTime',supportsAllDrives=True).execute()
def phase_raw(file_id):
    sink=io.BytesIO();transfer=MediaIoBaseDownload(sink,phase_api.files().get_media(fileId=file_id,supportsAllDrives=True),chunksize=8*1024*1024)
    done=False
    while not done:_,done=transfer.next_chunk(num_retries=3)
    return sink.getvalue()
def phase_update_verified(key,blob,mime):
    ref=phase_payload['expected_controls'][key]
    assert phase_metadata(ref['id'])==phase_pre_meta[key],key+' changed before write'
    saved=phase_api.files().update(fileId=ref['id'],media_body=MediaIoBaseUpload(io.BytesIO(blob),mimetype=mime,resumable=True),fields='id,size,version,modifiedTime',supportsAllDrives=True).execute()
    raw=phase_raw(ref['id'])
    assert raw==blob and phase_sha(raw)==phase_sha(blob),key+' raw readback differs'
    return {'id':saved['id'],'bytes':len(raw),'sha256':phase_sha(raw),'fresh_raw_readback_verified':True,'transport':'AUTHORIZED_COLAB_MCP_DRIVE_API_FALLBACK'}

# Refuse stale global-control updates; Antigravity owns only separate append.
phase_pre_meta={};phase_before={}
for key,ref in phase_payload['expected_controls'].items():
    before=phase_metadata(ref['id']);raw=phase_raw(ref['id']);after=phase_metadata(ref['id'])
    assert before==after,key+' changed during read'
    assert phase_sha(raw)==ref['sha256'],key+' differs from last published exact bytes'
    phase_pre_meta[key]=after;phase_before[key]=raw
for name,value in phase_payload['files'].items():
    blob=base64.b64decode(value);assert phase_sha(blob)==phase_payload['sha256'][name]
    assert '/' not in name and '\\' not in name
    (phase_root/name).write_bytes(blob)

phase_observed={'observed_utc':datetime.now(timezone.utc).isoformat(),'worker_alive':full_audit_worker.is_alive(),
    'stored_status':json.loads(json.dumps(full_audit_worker_state)),'live_batch_stats':dict(batch_adapter.stats),'training_started':False}
with sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True,timeout=3) as phase_db:
    phase_observed['unique_chat_rows_committed']=phase_db.execute('SELECT count(*) FROM samples').fetchone()[0]
    phase_observed['issues_committed']=dict(phase_db.execute('SELECT kind,count(*) FROM issues GROUP BY kind'))
assert phase_observed['worker_alive'] and not phase_observed['stored_status']['training_started']
assert phase_observed['live_batch_stats']['cache_hits']>0
(phase_root/'runtime_observed.json').write_bytes(phase_json(phase_observed))

# Explicit notebook save-point: all observed cells0..28, original source intact.
notebook_id='1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l'
nb_meta=phase_metadata(notebook_id);nb_before=phase_raw(notebook_id)
assert phase_metadata(notebook_id)==nb_meta
nb=json.loads(nb_before);live_cells=json.loads((phase_root/'live_notebook_cells.json').read_text('utf8'))['cells']
live_by_id={cell['id']:cell for cell in live_cells}
for cell in nb['cells'][:15]:
    assert ''.join(cell['source'])==''.join(live_by_id[cell.get('id') or cell['metadata']['id']]['source'])
old_by_id={cell.get('id') or cell['metadata']['id']:cell for cell in nb['cells']}
saved_cells=[]
for live in live_cells:
    cell=dict(old_by_id.get(live['id'],{}));cell.update(live)
    cell.setdefault('metadata',{})['id']=live['id'];saved_cells.append(cell)
nb['cells']=saved_cells;nb_blob=phase_json(nb)
assert phase_metadata(notebook_id)==nb_meta
phase_api.files().update(fileId=notebook_id,media_body=MediaIoBaseUpload(io.BytesIO(nb_blob),mimetype='application/x-ipynb+json',resumable=True),fields='id,size',supportsAllDrives=True).execute()
assert phase_raw(notebook_id)==nb_blob
notebook_receipt={'id':notebook_id,'bytes':len(nb_blob),'sha256':phase_sha(nb_blob),'fresh_raw_verified':True,
    'cell_count':len(saved_cells),'original_first15_sources_preserved':True,'source_save_point':'OBSERVED_CELLS_0_TO_28',
    'publication_helper_source_preserved_in_progress':True,'training_started':False}
(phase_root/'notebook_remote_verified.json').write_bytes(phase_json(notebook_receipt))
(phase_root/'notebook_before_save.ipynb').write_bytes(nb_before)

phase_state=json.loads(phase_before['state']);phase_chat=json.loads(phase_before['chat'])
assert phase_state['accepted_cases']==1629858 and phase_state['training_chat_rows']==6502088
prior=phase_state.get('latest_colab_runtime_observation')
phase_state.setdefault('data_only_colab_observation_history',[]).append(prior)
phase_observation={'notebook_id':notebook_id,'transport':'OFFICIAL_COLAB_MCP_AUTHORIZED_DRIVE_SESSION',
    'observed_utc':phase_observed['observed_utc'],'worker_alive_at_observation':True,
    'runtime_status':phase_observed['stored_status']['state'],'checkpoint':phase_observed['stored_status']['checkpoint'],
    'live_report':phase_observed['stored_status'].get('report'),'unique_chat_rows_committed':phase_observed['unique_chat_rows_committed'],
    'batch_adapter_stats':phase_observed['live_batch_stats'],'performance_upgrade':phase_observed['stored_status']['performance_upgrade'],
    'evidence_progress_id':phase_payload['expected_controls']['progress']['id'],'evidence_member':'audit_finish_20261022/runtime_observed.json',
    'live_status_cell':'JJ-lR0wWb4Am','full_archive_audit_complete':False,'TRAINING_DATASET_READY':False,'training_started':False}
phase_state['latest_colab_runtime_observation']=phase_observation
phase_state['latest_data_only_notebook']=notebook_receipt
phase_state['updated_utc']=datetime.now(timezone.utc).isoformat()
phase_state['status']='FULL_ARCHIVE_AUDIT_RUNNING_VALIDATED_BATCHING_SGK_AUTHORING_DELEGATED'
phase_state.setdefault('external_data_authoring_handoff',{}).update(external_agents_running_reported_by_owner=True,
    report_origin='OWNER_DIRECT_MESSAGE_ANTIGRAVITY_DANG_CHAY',external_results_received=False,
    global_control_writes_reserved_to_codex=True)
phase_chat['latest_colab_runtime_observation']=phase_observation
phase_chat['external_data_authoring_handoff']=phase_state['external_data_authoring_handoff']
context=phase_before['context'].decode('utf8')
marker='### Nhật ký 22/10/2026 — kiểm đủ nguồn, tiếp nối batch từ 200.000 chat'
assert marker not in context
context+='\n\n'+marker+'\n'
context+='Đã index đủ218/218source members với1629842source versions. Checkpoint sau200000chat đã raw-readback đúnghash809e20f201991f9de327967da0b5cca43ff8d1c4d483ab14e25b4ef6de9281e0, giữ cùngID16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI. Cooperative pause so toàn bộ219membercursor với snapshot; thread đã dừng/đóngSQLite trước copy snapshot trongruntimeColab. Không tảiDB/kho vềPC, khôngreset.\n'
context+='Adapter batch256 giữ nguyênauditorV3 và mọi source/link/split/duplicate/token gates. Hai peer đã phát hiện lỗi read-ahead/cursor và batch-only failure; root sửa, thêmtest và21/21synthetic differential đạt. Tokenizer CPU synthetic nhanh khoảng2.03lần, khôngphảicamkết tốcđộ toànkho. Đợt finalcode do rootreview/test; khônggọi là independentpeer finalapproval hoặc human review. Mãhash8d978eceeabebda9103ae23a16c23beab5b8cf5f2248984eda0b584facbedf92.\n'
context+='Lần đầuconstructor từ chối tokenizer trongRAM không mangrevisionmetadata; giữerror vàsource trongnotebook/evidence. Bản sửa nạp đúngcachedsnapshot revision70d244cc86ccca08cf5af4e1e306ecf908b1ad5e, đối chiếu Rust tokenizer serialization/chattemplate với bảntrước, khôngyếuđi gate. Worker mới cùngIDcheckpoint, checkpointlớn mỗi1800giây vàkếtthúc/lỗi; SQLitecache128MiB. Khôngnạpweights/GPU/train.\n'
context+=f"Quan sát {phase_observed['observed_utc']}: worker_alive=True, {phase_observed['unique_chat_rows_committed']}chat đãcommit, {phase_observed['live_batch_stats']['cache_hits']}hàng đã qua cachebatch thật. Đây là mốc quan sát, không tuyên bố toàn6502136rawchat đãxong. Finding regression_only giữnguyên, rowraw/canonicalhash1729ed713dfedcc0205b130c6573313dcc5784c7eaf5618d0cf32fdc728cf26b, chưa có linkedchat ởmốcquery; finalzerolinksproof cònchờhếtquét. Khôngtựvào train.\n"
context+='Chủ báo Antigravity đangchạy: Codex khôngsoạntrùng38G2tasks/50constraints; còn10assetmasters/1G3source locatorriêng. Chưa nhận gói kết quả bênngoài. Core495/165 giữnguyên; khôngthêmcase/chat hoặcđổi299signoff. ConnectorDrive trongWork báoUnknown tool sauretry/discovery dùplugin enabled; đợtnày dùng đúngkếtnốiDriveđãđược chủxácthực trongColabquaMCP đểcậpnhậtcùngIDs, rawreadbackso toànbyte, STATEcuối. Giữnguyênmọi history/member nguồn. TRAINING_DATASET_READY=false.\n'

phase_out=io.BytesIO()
with zipfile.ZipFile(io.BytesIO(phase_before['progress'])) as old,zipfile.ZipFile(phase_out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as new:
    names=old.namelist();assert len(names)==len(set(names))
    for info in old.infolist():new.writestr(info,old.read(info.filename))
    for path in sorted(phase_root.iterdir()):
        if path.is_file():
            member='audit_finish_20261022/'+path.name
            assert member not in names
            new.writestr(member,path.read_bytes())
with zipfile.ZipFile(io.BytesIO(phase_before['progress'])) as old,zipfile.ZipFile(io.BytesIO(phase_out.getvalue())) as new:
    assert all(old.read(name)==new.read(name) for name in old.namelist())

phase_receipts={}
phase_receipts['progress']=phase_update_verified('progress',phase_out.getvalue(),'application/zip')
phase_receipts['chat']=phase_update_verified('chat',phase_json(phase_chat),'application/json')
phase_receipts['context']=phase_update_verified('context',context.encode('utf8'),'text/markdown')
# STATE is intentionally last, after the other three fresh complete comparisons.
phase_receipts['state']=phase_update_verified('state',phase_json(phase_state),'application/json')
receipt={'schema':'MathVisionKid.four_controls_raw_verified.v1','controls':phase_receipts,'notebook':notebook_receipt,
    'state_written_last':True,'old_progress_members_preserved':True,'new_case_count':0,'new_chat_count':0,
    'source_rows_changed':False,'training_started':False,'TRAINING_DATASET_READY':False}
(phase_root/'four_controls_remote_verified.json').write_bytes(phase_json(receipt))
print(receipt)

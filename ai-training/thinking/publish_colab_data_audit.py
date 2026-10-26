"""Publish data-only Colab/MCP audit evidence on existing controls; zero case delta."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,re,zipfile
HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/colab_data_audit_20261021'
def read(p):return json.loads(p.read_text('utf8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
def main():
    pre=read(RUN/'prewrite_verified.json')
    for n,v in zip(['prewrite_progress.zip','prewrite_chat.json','prewrite_state.json','prewrite_context.md'],pre['controls']):assert sha((RUN/n).read_bytes())==v['sha256']
    state=read(RUN/'prewrite_state.json');chat=read(RUN/'prewrite_chat.json')
    assert state['accepted_cases']==1629852 and state['training_chat_rows']==6502064
    token=read(RUN/'mcp_evidence/token_checkpoint.json')
    v1=read(RUN/'mcp_evidence/full_audit_checkpoint.json')
    v2=read(RUN/'mcp_evidence/full_audit_v2_checkpoint.json')
    job=read(RUN/'mcp_evidence/finite_worker_observation.json')
    nb=read(RUN/'mcp_evidence/notebook_worker_remote_verified.json')
    assert token['progress']['acknowledged_rows']==20000 and v2['fresh_raw_readback_verified']
    assert job['state']=='RUNNING_DATA_ONLY' and job['training_started'] is False
    assert job['audit_identity']==v2['report']['identity']
    assert not any(job['report'][k] for k in ['training_started','gpu_used','model_weights_loaded','TRAINING_DATASET_READY'])
    assert nb['cell_count']==13 and nb['fresh_raw_verified'] and nb['all_bytes_equal']
    v2validation=read(HERE/'math_data_full_audit_v2_validation.json')
    assert sha((HERE/'math_data_full_audit_v2.py').read_bytes())=='81b1e3f04c5886f78282386ecb34d47ba4ba9da63edfec8856bab82034a093ee'
    g2=read(RUN/'g2_planning/validation.json')
    assert read(RUN/'g2_planning/queue.json')
    now=datetime.now(timezone.utc).isoformat()
    state.setdefault('data_only_colab_observation_history',[]).append(state['latest_colab_runtime_observation'])
    observation=dict(notebook_id=nb['id'],date='2026-10-21',transport='OFFICIAL_GOOGLE_COLAB_MCP_EXISTING_LOCAL_LOOPBACK_ADAPTER',connection_verified=True,cpu_only=True,token_checkpoint=token,initial_v1_source_checkpoint=v1,v2_source_checkpoint=v2,finite_audit_worker_last_observed=job,notebook_snapshot=nb,live_progress_may_advance_after_observation=True,training_started=False,full_archive_audit_complete=False,TRAINING_DATASET_READY=False)
    state['latest_colab_runtime_observation']=observation
    state.setdefault('data_only_notebook_publication_history',[]).append(state['latest_data_only_colab_notebook'])
    state['latest_data_only_colab_notebook']={**nb,'data_preparation_only':True,'colab_executed':True,'full_archive_audit_complete':False,'uses_latest_state_and_all_candidate_recipe':True,'checkpoint_by_recipe_and_split':True}
    state.setdefault('full_archive_audit_code_history',[]).append(state['latest_full_archive_audit_code'])
    state['latest_full_archive_audit_code']=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member=RUN.name+'/code/math_data_full_audit_v2.py',sha256=sha((HERE/'math_data_full_audit_v2.py').read_bytes()),parent_code_sha256='642343937c54c1c761ec38708d76fb46e26165563ab2045e9bc6c45adf0624a1',v2_tests=6,v1_tests_retained=10,status='RUNNING_FINITE_CPU_AUDIT_ALL247_DECLARED_MEMBERS',v1_checkpoint_preserved=v1['checkpoint_id'],v2_checkpoint_id=v2['checkpoint_id'],explicit_source_label_policy='SOURCE_POOL_train_candidate_COMPATIBLE_ONLY_WITH_EXPLICIT_train_CHAT_NO_SOURCE_REWRITE',unknown_source_or_missing_chat_split_still_rejected=True,no_truncation=True,training_started=False)
    state['latest_g2_finite_preparation_plan']=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member=RUN.name+'/g2_planning/queue.json',sha256=sha((RUN/'g2_planning/queue.json').read_bytes()),candidate_ids=54,finite_tasks=41,masters=36,text_finite_tasks=22,original_asset_or_full_annotation_tasks=14,actual_observation_tasks=5,accepted_case_delta=0,all_sgk_forms_covered=False)
    state.update(updated_utc=now,TRAINING_DATASET_READY=False,training_started=False)
    state['next_action']='Via existing Colab MCP read status cell CJPsTAkCKgJf in notebook1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l. Finite CPU v2 worker is already running; DO NOT launch duplicate or Run all. Resume same hash/identity checkpoint182zLHZU0XBpTfKm7ThJpfy37GgFJ7Ob2 only if stopped. Preserve20K token checkpoint and v1 finding checkpoint. Continue41 finite G2 preparation tasks mapped from54 exact candidates, source-locator2 and10asset-only; no training/GPU/weights.'
    chat['latest_data_only_colab_observation']=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member=RUN.name+'/mcp_evidence/finite_worker_observation.json',sha256=sha((RUN/'mcp_evidence/finite_worker_observation.json').read_bytes()),checkpoint_id=v2['checkpoint_id'],training_started=False)
    assert chat['chat_rows']==6502064
    write(RUN/'publish_state.json',state);write(RUN/'publish_chat_manifest.json',chat)
    context=HERE.parent/'MATH_TRAINING_CONTEXT.md'
    assert context.read_bytes()==(RUN/'prewrite_context.md').read_bytes()
    previous=context.read_text('utf8');marker='### Nhật ký21/10/2026 — Colab MCP data-only audit running'
    assert marker not in previous
    text=re.sub(r'^<!-- CURRENT_CHECKPOINT[^\n]*-->\n','',previous)
    context.write_text(f'<!-- CURRENT_CHECKPOINT {RUN.name}:1629852cases;6502064candidatechat;495core/165nodes;MCP CPU DATA AUDIT RUNNING;NO TRAINING. -->\n'+text+f'''
\n\n{marker}
Chủ xác nhận đã bật quyền Chrome và yêu cầu dùngMCPColab. Đã phát hiện/cấu hình lại integrationgooglecolab/colab-mcp cósẵn; oldhost trỏ notebook khác nên giữ nguyên và tạo local_host_data_only.py đúng1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l, loopback127.0.0.1:8769, giữauth/originchecks. Không thêmMCPkhôngrõnguồn hoặc mởcổngpublic. Kết nốiMCPthật trảresult=true, đãget_cells/read/run đúngnotebook. Localbrowser toolvẫn báoWorkdisabled, nhưng không cầncomputeruse đểMCPđọc/chạycelldata-only.
\nĐã đọc output thật:20.000candidatechat tokenizer pass trướcđó; không phải fullsource-link/split audit. Chạycelllưucheckpoint5, rawreadbackđúngSHA{token['checkpoint_sha256']}, ID{token['checkpoint_id']},7.213.056bytes. Không chạy lại20KhoặcRunall. Giữrecipe35payload cũ chocheckpointđó, không ép checkpointcũthànhrecipe36.
\nDeepauditv1theorecipe36/30 index1.000source vàflagunknown vì source builderghi train_candidate, trongkhi chat_recordsg rõtrain. Giữv1checkpointID{v1['checkpoint_id']} SHA{v1['checkpoint_sha256']} vàmọiissue; đây là khácbiệtschema đượcchứngminhbằngcodepinned, không phải sửađápsố. Dẫnxuấtauditorv2riêng, parenthashfrozenkhôngđổi, lưuđúngnhãnsourcethuộcsourcepool; chỉchấpnhậntươngthíchvớichatghi rõtrain. Unknown/missing/sourcehashsaivẫnfail,train_candidatekhôngtựđổinhãntrain.6tests v2 và10v1pinnedtokenizerPASS; v2từchốiDBv1trướcmọighi, giữhashv1DB.
\nV2đãchạyColabthật:1.000sourcecandidateindexđúngkhôngissue, checkpointID{v2['checkpoint_id']} rawreadbackSHA{v2['checkpoint_sha256']} lúcđầutươngứng1.540.096bytes. Sauđó khởi độngđúngmộtworkerCPUhữuhạn,247members=217source+30chat, khôngsinhthêmcase. Mốcquan sát{job['updated_utc']}: {job['report']['source_versions_indexed']}sourceversions, {job['report']['members_complete']}/247members; {job['report']['unique_chat_rows_processed']}deepchat, issues{json.dumps(job['report']['issues'])}. Workerchạyreadallcandidate theoIDs/SHA, sourcefirst, đốichiếufullprompt/targetrawhash,group/question/canonical/split vàtokenkhôngtruncate. CheckpointcùngIDupdateđịnhkỳkhoảng5phúthoặckhikếtthúc;rawstreamingreadbackhashkhôngloadDBlớnvàoRAM. Mốccloudsavedcóthểsaucursorlocal; fieldlast_observedkhôngphảicamkếtlivekhôngđổi.
\nKhônglaunchworkertrùng. QuaMCP local_client.py get_cells kiểmstatuscellCJPsTAkCKgJf, fileROOT/full_audit_v2_worker_status.json. ThreadnameMathVisionKidFiniteCPUDataAudit; kếtthúchết247membershoặcdừnglỗithậtkèmreceipt. Không dùngkeepalive/GPU/train/weights/Trainer/paidAPI; runtime_acceleratornonevàtraining_startedfalseđãinoutput. Datasetreadyvẫnfalse dùsau nàytechnicalauditpass vìSGK/assetacceptancecònriêng.
\nG2planningđãgom54candidatev1/v2đúngmộtlầnthành41task/36master:22textfinite,14cầnhìnhgốchoặcmôtảđầyđủ,5cầnquansátthực; giữconstraint/receipt/provenance/nearestrefs. Khôngsoạnnhân54lôtrùng, khôngđóngbằngtênmaster. QueuecụthểtrongPROGRESS{RUN.name}/g2_planning/queue.json;2locatorgốc và10asset-onlyvẫngiữriêng.
\nNotebookđãlưulạiđúngIDcũquaDriveconnector:13cellsource/outputMCP, tấtcả7cellnguồngốc và10cellmốctrướcđềugiữnguồn, parent7/10cellbyteslưu lại trongevidence. Freshrawreadback{nb['bytes']}bytes SHA{nb['sha256']}. Sourcecodecellv2đượcpinSHA,workerhữuhạnkhôngtrain. Khôngcoihashnotebookpublishedbấtbiếnvĩnhviễnvìnotebooklivecóthểautosave; mốcbytehashlàbảnđãxácminhlúcđó.
\nĐợtnàychỉkiểm/chuẩnbịkhôngtăngđếmcase/chatlầnnữa:1629852accepted/6502064candidatechat,6502176kểcảeval/audit. Bộ495core/165nodegiữnguyên,299humanexactsignoffkhôngđổi;71bàimới/284chatđãcôngbốtronggói1nlBxqxREBrQszEJlXer2Yu5JYcYcG_5x. ChưađánhgiásẵnsàngtrainhoặctuyênbốtoànSGK/pháplý2026đủ. GóiPROGRESS/chat/context/STATEcùngIDs, STATEcuối; chỉxácnhậnrawsyncsau4readbacks.
''',encoding='utf8')
    regpath=HERE/'data/primary_math_teacher_20261016/drive_artifacts.json';reg=read(regpath)
    reg['latest_data_only_notebook']=nb
    reg['latest_data_only_mcp_observation']=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member=RUN.name+'/mcp_evidence/finite_worker_observation.json',checkpoint_id=v2['checkpoint_id'])
    write(regpath,reg)
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as old,zipfile.ZipFile(RUN/'publish_progress_index.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as new:
        for info in old.infolist():new.writestr(info,old.read(info.filename))
        for p in sorted(RUN.rglob('*')):
            if p.is_file() and p.suffix in ('.json','.py','.ipynb') and not p.name.startswith(('prewrite_','publish_','four_controls_')):
                new.writestr(RUN.name+'/'+p.relative_to(RUN).as_posix(),p.read_bytes())
        for n in ['math_data_full_audit_v2.py','test_math_data_full_audit_v2.py','math_data_full_audit_v2_validation.json','math_data_full_audit_v2_parent_diff.txt','sgk_g2_pending_plan.py','publish_colab_data_audit.py','collect_data_only_mcp_receipts.py','save_data_only_mcp_notebook.py','save_data_only_worker_notebook.py']:
            new.writestr(RUN.name+'/code/'+n,(HERE/n).read_bytes())
        new.writestr(RUN.name+'/state.json',(RUN/'publish_state.json').read_bytes())
        new.writestr(RUN.name+'/chat.json',(RUN/'publish_chat_manifest.json').read_bytes())
        new.writestr(RUN.name+'/MATH_TRAINING_CONTEXT.md',context.read_bytes())
        new.writestr(RUN.name+'/drive_artifacts.json',regpath.read_bytes())
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as old,zipfile.ZipFile(RUN/'publish_progress_index.zip') as new:
        assert not new.testzip() and len(new.namelist())==len(set(new.namelist()))
        assert all(old.read(n)==new.read(n) for n in old.namelist())
        for n in new.namelist():
            if n in old.namelist():continue
            assert not re.search(r'\.blob\.core\.windows\.net|Bearer\s+[A-Za-z0-9]|[?&]sig=|mcpProxyToken=[A-Za-z0-9_-]{12,}',new.read(n).decode('utf8',errors='ignore'),re.I)
    print(json.dumps(dict(accepted_cases=state['accepted_cases'],candidate_chat_rows=state['training_chat_rows'],accepted_delta=0,chat_delta=0,mcp_connected=True,worker='RUNNING_DATA_ONLY',training_started=False,ready=False)))
if __name__=='__main__':main()


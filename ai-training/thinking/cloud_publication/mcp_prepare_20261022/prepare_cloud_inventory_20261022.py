"""Prepare a hash-pinned inventory; never executes training or reads corpus rows."""
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy
import ast, hashlib, json, zipfile, sqlite3

HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/mcp_prepare_20261022'
PREV=HERE/'cloud_publication/data_resume_20261022'
MCP=Path.home()/'.codex/integrations/colab-mcp'
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_text('utf8'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')

def main():
    prior=read(PREV/'four_controls_remote_verified.json')['controls']
    files=['progress.zip','chat.json','context.md','state.json']
    fresh=read(RUN/'prewrite_receipt.json')
    for old,new,name in zip(prior,fresh,files):
        b=(RUN/('prewrite_'+name)).read_bytes()
        assert new['sha256']==sha(b)==old['sha256'] and new['bytes']==len(b)==old['bytes']
    state=read(RUN/'prewrite_state.json');chat=read(RUN/'prewrite_chat.json')
    pointer=state['latest_all_data_union_recipe']
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as z:
        raw=z.read(pointer['member'])
    assert sha(raw)==pointer['sha256']=='e4197a8e797a6c4d22b938779b663d0e306536dc8af75a5f81fb3c98f7e1a7a8'
    recipe=json.loads(raw)
    assert not recipe['pending_discovery'] and not state['training_started']
    assert len(recipe['artifacts'])==37 and len(recipe['source_members'])==218 and len(recipe['chat_members'])==31
    for field,role in [('source_members','candidate_source'),('chat_members','candidate_chat')]:
        seen=set()
        for entry in recipe[field]:
            ref=recipe['artifacts'][entry['sha256']]
            assert entry['file_id'] in ref['file_ids'] and entry['bytes']==ref['bytes']
            assert entry['role']==role and isinstance(entry['rows'],int) and entry['rows']>=0
            key=(entry['sha256'],entry.get('member'))
            assert key not in seen;seen.add(key)
            if entry.get('member'):
                assert entry.get('member_sha256') and entry.get('member_bytes') is not None
    assert sum(e['rows'] for e in recipe['chat_members'])==recipe['raw_candidate_chat_rows_including_declared_current_splits']==6502136
    assert recipe['declared_candidate_chat_rows']==state['training_chat_rows']==6502088
    assert recipe['current_pedagogy_validation_test_rows_separate']==48
    # Query in the prepared read-only restore must run on the actual V3 schema.
    restore=(PREV/'restore_existing_v3_readonly.py').read_bytes()
    tree=ast.parse(restore.decode('utf8'))
    queries=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.startswith('SELECT')]
    schema=(HERE/'math_data_full_audit_v3.py').read_text('utf8')
    schemas=[n.value for n in ast.walk(ast.parse(schema)) if isinstance(n,ast.Constant) and isinstance(n.value,str) and 'CREATE TABLE IF NOT EXISTS config' in n.value]
    assert len(schemas)==1
    db=sqlite3.connect(':memory:')
    try:
        db.executescript(schemas[0])
        for query in queries: db.execute(query).fetchall()
    finally: db.close()
    obs=read(MCP/'resume_20261022_probe_observed2.json')['structured_content']['cells'][0]
    assert obs['id']=='LHsQvxgpGOCc' and not obs['outputs'] and obs['execution_count'] is None
    observation=dict(transport='OFFICIAL_GOOGLE_COLAB_MCP',websocket_connected=True,client_ready=True,notebook_id='1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l',probe_cell_id=obs['id'],probe_execution_count=obs['execution_count'],probe_outputs=obs['outputs'],cpu_runtime_execution_verified=False,reason='HOSTED_RUNTIME_CONNECTION_PENDING; MCP notebook edits/readback work but CPU probe did not execute.',checkpoint_id='16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI',checkpoint_fresh_raw_verified_this_run=False,checkpoint_last_observed_bytes=2321960960,checkpoint_last_observed_modified_utc='2026-10-22T04:18:03.804Z',worker_started_this_run=False,training_started=False)
    now=datetime.now(timezone.utc).isoformat()
    inventory=dict(schema='MathVisionKid.cloud_preparation_inventory.v1',created_utc=now,recipe_pointer=pointer,recipe_sha256=sha(raw),payloads=recipe['artifacts'],source_members=recipe['source_members'],chat_members=recipe['chat_members'],excluded_members=recipe['excluded_members'],counts=dict(payload_references=37,source_members=218,chat_members=31,declared_source_row_occurrences=sum(e['rows'] for e in recipe['source_members']),declared_chat_row_occurrences_including_current_eval=6502136,declared_candidate_chat_rows=6502088,current_eval_rows=48,accepted_case_records=1629858,core_cases=495,core_nodes=165),selection='ALL_VALID_EXPLICIT_TRAIN_ROWS_AFTER_ARCHIVE_AUDIT; validation/test/diagnostic retain separate roles; never choose only a small balanced subset.',validation_scope='INVENTORY_AND_REFERENCE_CONSISTENCY_ONLY_NOT_FULL_CORPUS_ROW_AUDIT',full_archive_audit_complete=False,TRAINING_DATASET_READY=False,training_started=False,cpu_observation=observation)
    write(RUN/'cloud_preparation_inventory.json',inventory)
    write(RUN/'mcp_runtime_observation.json',observation)
    receipt=dict(created_utc=now,checks=['fresh four-control raw hashes match prior publication','all249 member references bind37existing payload IDs and hashes','no duplicate archive-member identities within roles','6502136raw chat occurrences =6502088candidate+48current eval','read-only restore SELECTs compile against V3 schema'],restore_queries_verified=len(queries),restore_code_sha256=sha(restore),inventory_sha256=sha((RUN/'cloud_preparation_inventory.json').read_bytes()),case_count_changed=False,old_data_deleted=False,large_checkpoint_downloaded_to_pc=False,training_started=False)
    write(RUN/'inventory_validation_receipt.json',receipt)
    (RUN/'restore_existing_v3_readonly.py').write_bytes(restore)
    for name in ['resume_20261022_probe_observed2.json','resume_20261022_probe_cell.json']:
        (RUN/name).write_bytes((MCP/name).read_bytes())
    marker='### Nhật ký 22/10/2026 — MCP kết nối, inventory toàn kho'
    context=(RUN/'prewrite_context.md').read_text('utf8')
    assert marker not in context
    context+='\n\n'+marker+'\nMCP đã kết nối đúng notebook cũ, đọc/sửa ô qua MCP được; máy CPU Colab vẫn chờ kết nối, probe LHsQvxgpGOCc chưa có execution_count/output. Không tuyên bố audit worker đang chạy hoặc đã kiểm toàn kho. Giữ checkpoint V3 16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI, chưa tải raw2.32GB trong đợt này; không khởi tạo lại hoặc tải về PC.\nChuẩn bị cloud_preparation_inventory.json gắn đủ37payload/218source/31chat member với ID/hash hiện có; kiểm tham chiếu, không trùng identity trong từng role và đếm6502136rawchat=6502088candidate+48eval hiện hành. Đây là inventory consistency, không phải row/semantic/token fullaudit. Không thêm case/chat hoặc thay nhãn/split/299signoff. Core495/165, G2còn38task và10asset/1locator riêng. Sửa lỗi cú pháp LIMIT của helper restore chỉ đọc và kiểm các SELECT trên schema V3 thật. Chưa train/GPU/weights/paidAPI/app/commit/push. TRAINING_DATASET_READY=false.\n'
    (RUN/'publish_context.md').write_text(context,encoding='utf8')
    # Exactly one current context file; other snapshots are audit evidence only.
    (HERE.parent/'MATH_TRAINING_CONTEXT.md').write_text(context,encoding='utf8')
    invref=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member=RUN.name+'/cloud_preparation_inventory.json',sha256=receipt['inventory_sha256'],verification_scope=inventory['validation_scope'],created_utc=now)
    state['latest_cloud_preparation_inventory']=invref
    state['data_only_colab_observation_history'].append(state['latest_colab_runtime_observation'])
    state['latest_colab_runtime_observation']=observation
    state['updated_utc']=now
    chat['latest_cloud_preparation_inventory']=invref
    chat['latest_mcp_runtime_observation']=observation
    write(RUN/'publish_state.json',state);write(RUN/'publish_chat.json',chat)
    source=Path(__file__)
    (RUN/source.name).write_bytes(source.read_bytes())
    additions={p.name:p.read_bytes() for p in RUN.iterdir() if p.is_file() and p.name in ['cloud_preparation_inventory.json','mcp_runtime_observation.json','inventory_validation_receipt.json','restore_existing_v3_readonly.py','resume_20261022_probe_observed2.json','resume_20261022_probe_cell.json',source.name]}
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as before, zipfile.ZipFile(RUN/'publish_progress.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as after:
        oldnames=before.namelist();assert len(oldnames)==len(set(oldnames))
        for entry in before.infolist():after.writestr(entry,before.read(entry.filename))
        for name,b in additions.items():
            key=RUN.name+'/'+name;assert key not in oldnames;after.writestr(key,b)
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as before,zipfile.ZipFile(RUN/'publish_progress.zip') as after:
        for name in before.namelist():assert before.read(name)==after.read(name)
        assert after.read(invref['member'])==(RUN/'cloud_preparation_inventory.json').read_bytes()
    print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=='__main__':main()

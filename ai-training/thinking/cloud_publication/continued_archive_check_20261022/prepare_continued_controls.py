"""Same-ID progress controls; no corpus generation or training."""
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy
import hashlib, json, zipfile

DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]
PREVIOUS = DIRECTORY.parent/'resume_after_g2_20261022'
digest = lambda b: hashlib.sha256(b).hexdigest()
def read(name): return json.loads((DIRECTORY/name).read_bytes())
def save(name, obj):
    (DIRECTORY/name).write_bytes((json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode())

def main():
    observation = read('runtime_observation.json')
    assert observation['worker_alive'] and observation['worker_state']=='RUNNING_DATA_ONLY'
    assert observation['recipe_identity']=='f0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863'
    proof = observation['checkpoint']
    assert proof['fresh_raw_readback_verified'] and proof['id']=='16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI'
    state, chat = read('parent_state.json'), read('parent_chat.json')
    assert state['accepted_cases']==1629922 and state['training_chat_rows']==6502344
    assert state.get('pending_checkpoint_append') is None
    before = read('parent_controls_raw_verified.json')
    for key, extension in [('progress','.zip'),('chat','.json'),('context','.md')]:
        assert digest((PREVIOUS/('next_'+key+extension)).read_bytes())==before[key]['sha256']
    final_status = observation['metadata']['final_metadata_status.json']
    assert final_status['state']=='WAITING_FOR_EXISTING_FULL_SCAN'
    old_observation = deepcopy(state.get('latest_colab_runtime_observation',{}))
    state.setdefault('data_only_colab_observation_history',[]).append(old_observation)
    current = dict(old_observation)
    current.pop('unique_chat_rows_committed', None)
    current.update(observed_utc=observation['observed_utc'], worker_alive_at_observation=True,
        runtime_status=observation['worker_state'], executing_recipe_identity=observation['recipe_identity'],
        source_versions_indexed=1629906, committed_physical_chat_rows=observation['actual_committed_physical_chat_rows'],
        last_verified_checkpoint_unique_chat_rows=proof['report_at_snapshot']['unique_chat_rows_processed'],
        checkpoint=proof, live_status_cell='N-HZLllQQnti', current_issues=observation['current_issues'],
        full_archive_audit_complete=False, TRAINING_DATASET_READY=False, training_started=False,
        evidence_member='continued_archive_check_20261022/runtime_observation.json')
    for control in (state,chat):
        control['latest_colab_runtime_observation']=current
        control['latest_verified_v3_checkpoint']=proof
        control['final_metadata_check']=final_status
        control['count_reconciliation']={
            'historical_accepted_case_counter_preserved':1629922,
            'actual_source_versions_indexed':1629906,
            'historical_case_counter_difference':16,
            'difference_attribution':'Pending exact crosswalk; do not call historical counter a verified unique case count.',
            'declared_candidate_chat_rows':6502344,
            'current_raw_chat_rows_including_evaluation':6502392,
            'actual_full_chat_count_verification_complete':False,
            'all_original_sources_retained':True,
        }
        control['performance_decision']={
            'active_adapter':'Frozen two-encoding batch256 adapter',
            'outer_span_rows':200000, 'commit_every_rows':256,
            'onepass_optimizer_applied':False,
            'reason':'Bounded tests passed but speed gain did not justify changing the independent encoding comparison.',
            'cheap_delegated_model':'gpt-6-luna', 'cheap_delegated_agents':3,
            'root_review_and_repairs_performed':True,
        }
        control['training_started']=False
        control['TRAINING_DATASET_READY']=False
    state.setdefault('data_only_notebook_publication_history',[]).append(state.get('latest_data_only_notebook'))
    state['latest_data_only_notebook']=read('notebook_remote_verified.json')
    state['status']='FULL_ARCHIVE_CPU_AUDIT_RUNNING_FINAL_METADATA_CHECK_REGISTERED'
    state['updated_utc']=datetime.now(timezone.utc).isoformat()
    state['next_action']='Continue the ONE existing DATA_ONLY worker and its registered finite final metadata check. Use status cell N-HZLllQQnti. Do not rerun setup, append64, or a second worker. After251members complete, verify final evidence under continued_archive_check_20261022 and publish final controls on the same IDs. Keep the exact regression diagnostic/rawfalse report; use only the hash-bound derived adjudication. Five physical-observation tasks, ten asset masters, and one G3 locator remain outside current text technical acceptance. No training.'
    marker='### Nhật ký 22/10/2026 — agent tiết kiệm, kiểm toàn kho và bước chốt hữu hạn'
    context=(DIRECTORY/'parent_context.md').read_bytes()
    assert marker.encode() not in context
    paragraph=(f'\n\n{marker}\n'
        'Theo yêu cầu của chủ, ba agent gpt-6-luna chia rà thống kê, điều kiện còn thiếu và hiệu năng. Root đã đọc, sửa và kiểm mã cuối; các báo cáo là rà bằng agent, không phải nghiệm thu human hay reviewer ngoài. Không sinh thêm bài hoặc đếm lại lô64. Bộ lõi495/165/1980chat vẫn đã hoàn tất.\n'
        f'Quan sát {observation["observed_utc"]}: một worker CPU còn chạy, đã commit {observation["actual_committed_physical_chat_rows"]} lượt chat vật lý trong {6502392} hàng hiện hành. Nguồn đã index đủ1629906. Checkpoint cùng ID{proof["id"]} có {proof["bytes"]}byte, SHA256{proof["sha256"]}, đã raw streaming readback. Chưa được gọi toàn kho pass.\n'
        'Giữ nguyên auditor và batch adapter frozen. Chỉ tăng phạm vi mỗi lượt consume từ50000 lên200000, SQLite vẫn commit256 và batch256; local resume vẫn đúng cursor. Bộ so sánh span hữu hạn cho cùng báo cáo/cursor ở EOF. Bản thử onepass tokenizer được lưu làm evidence, không áp dụng vì mức tăng tốc chưa đủ bù thay đổi bằng chứng so sánh độc lập.\n'
        'Đã đăng ký đúng một thread chốt metadata, chỉ đợi worker hiện tại kết thúc rồi kiểm251cursor, identity/hash, từng độ dài token, bốn mode, split và hash nguồn. Raw V3 giữ finding regression_only và cờ false; chỉ kết luận riêng candidate chat sau exact-hash diagnostic có0linkedchat. Hàm adjudication đã sửa theo peer review, gắn SHA metadata thực của251member;12test đạt. Anti-join chỉ đọc ID/hash/nhãn/signature, có giới hạn5001 và chỉ chạy sau fullscan; hai index hash pin đã tìm thấy và nạp vào runtime. Không đưa nguồn-only/quarantine vào train.\n'
        'Giữ bộ đếm lịch sử1629922, ghi riêng nguồn thực1629906; chênh16 chưa có đối chiếu ID nên không khẳng định nguyên nhân. Dự kiến6502344candidatechat cộng48eval hiện hành; số thực cuối còn chờ fullscan. Năm task quan sát thật,10assetmasters và1locatorG3 giữ pending; không đóng bằng hình giả hoặc guard.299signoff human và mọi nguồn/history frozen giữ nguyên.\n'
        'Notebook cùng ID đã lưu đủ44cell, giữ nguồn34cell cha và có setup chốt metadata; raw readback khớp byte. Bốn control cùng IDs, STATE cuối và fresh raw readback; evidence trong PROGRESS/continued_archive_check_20261022. Không train/GPU/weights/paidAPI/app/commit/push. Skills applied: google-drive:google-drive.\n')
    (DIRECTORY/'context_delta.txt').write_bytes(paragraph.encode())
    (DIRECTORY/'next_context.md').write_bytes(context+paragraph.encode())
    save('next_state.json',state); save('next_chat.json',chat)
    excluded={'next_progress.zip','parent_state.json','parent_chat.json','parent_context.md',
              'notebook_mcp_cells.json','notebook_parent_drive.ipynb','notebook_savepoint.ipynb',
              'prepared_control_updates.json','four_controls_remote_verified.json'}
    candidates=[p for p in DIRECTORY.iterdir() if p.is_file() and p.name not in excluded
                and p.suffix in ('.json','.py','.txt') and not p.name.startswith('next_')]
    with zipfile.ZipFile(PREVIOUS/'next_progress.zip') as old, zipfile.ZipFile(DIRECTORY/'next_progress.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as new:
        assert len(old.namelist())==len(set(old.namelist()))
        for info in old.infolist():new.writestr(info,old.read(info.filename))
        for path in sorted(candidates):
            member='continued_archive_check_20261022/'+path.name
            assert member not in old.namelist()
            new.writestr(member,path.read_bytes())
    with zipfile.ZipFile(PREVIOUS/'next_progress.zip') as old,zipfile.ZipFile(DIRECTORY/'next_progress.zip') as new:
        assert all(old.read(name)==new.read(name) for name in old.namelist())
        assert len(new.namelist())==len(set(new.namelist()))
    ids={'progress':'1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX','chat':'1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6',
         'context':'13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9','state':'1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme'}
    controls={}
    for kind,ext in [('progress','.zip'),('chat','.json'),('context','.md'),('state','.json')]:
        path=DIRECTORY/('next_'+kind+ext);data=path.read_bytes()
        controls[kind]={'id':ids[kind],'path':str(path),'bytes':len(data),'sha256':digest(data)}
    save('prepared_control_updates.json',{'controls':controls,'state_must_be_written_last':True,
        'old_progress_members_preserved':True,'new_case_count':0,'new_chat_count':0,'training_started':False})
    print(json.dumps({'prepared':True,'controls':controls}))

if __name__=='__main__':main()

"""Publish a verified finite six-case append and truthful audit resume pointers."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,zipfile,re,ast
HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/data_resume_20261022'
G2=HERE/'cloud_publication/g2_finite_forms_20261021'
BASE=HERE/'data/primary_math_teacher_20261016'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text('utf8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
def stdout_dict(path,field=None):
    d=read(path)
    for o in d['structured_content'].get('outputs',d['structured_content'].get('cells',[{}])[-1].get('outputs',[])):
        if o.get('output_type')=='stream' and o.get('name')=='stdout':
            for line in ''.join(o['text']).splitlines():
                try:v=ast.literal_eval(line)
                except (ValueError,SyntaxError):continue
                if isinstance(v,dict) and (field is None or field in v):return v
    raise ValueError('No actual dictionary output found')
def main():
    for proof,n in zip(read(RUN/'prewrite_raw_verified.json'),['prewrite_progress.zip','prewrite_chat.json','prewrite_state.json','prewrite_context.md']):
        assert proof['sha256']==sha((RUN/n).read_bytes())
    state=read(RUN/'prewrite_state.json');chat=read(RUN/'prewrite_chat.json')
    assert state['accepted_cases']==1629852 and state['training_chat_rows']==6502064 and not state['training_started']
    bundle=read(G2/'bundle_remote_verified.json');audit=read(G2/'release/audit_report.json');union=read(G2/'union_scope.json')
    assert bundle['fresh_raw_verified'] and bundle['all_bytes_equal'] and bundle['cases']==6 and bundle['chat_rows']==24
    assert audit['cases']==6 and audit['chat_rows']==24 and audit['actual_tokenizer_all24']
    assert union['source_chat_prefixes_exact'] and union['total_candidate_members']==249
    assert sha((G2/'publish_latest_union_recipe.json').read_bytes())==union['recipe_sha256']
    nb=read(RUN/'notebook_remote_verified.json');assert nb['fresh_raw_verified'] and nb['all_bytes_equal']
    mcp=Path.home()/'.codex/integrations/colab-mcp'
    restored=stdout_dict(mcp/'data_only_v3_restore_observed2.json','migration') if (mcp/'data_only_v3_restore_observed2.json').exists() else None
    # The older observation response contains cells; keep only the actual stdout receipt.
    assert restored and restored['report']['source_versions_indexed']==111192 and restored['migration']['source_versions_preserved']==110666
    write(RUN/'mcp_evidence/v3_actual_migration_and_primary_complete.json',restored)
    status=stdout_dict(mcp/'data_only_resume_all_cells_20261022.json') if False else None
    cells=read(mcp/'data_only_resume_all_cells_20261022.json')['structured_content']['cells']
    status=ast.literal_eval(''.join(next(o['text'] for o in cells[13]['outputs'] if o.get('name')=='stdout')).strip())
    assert status['state']=='RUNTIME_OR_STATUS_MISSING'
    write(RUN/'mcp_evidence/current_runtime_status.json',status)
    pins={n:sha((BASE/n).read_bytes()) for n in ['owner_acceptance_policy.json','owner_human_attestations.json','owner_human_signoffs.jsonl','data_build_state.json','authoring_queue.json','supplementary_queue.json','coverage_adjudication_queue.json']}
    assert pins['owner_human_signoffs.jsonl']=='9475d9fabc1668e04a3e4ce3f5708a8f28e65ebf8c87337c212463017f3a7f1a'
    assert pins['data_build_state.json']=='fd3e6a7f7a95c1f0614e53cbb651632e3377c52fc82e9dcaf97efab1d3ea4966'
    write(RUN/'frozen_baseline_verified.json',dict(sha256=pins,human_snapshot_rows=299,raw_source_unchanged=True))
    locator=read(RUN/'locator_adjudication.json')
    for file,h in locator['input_files_sha256'].items():assert sha((HERE/file).read_bytes())==h
    recovered=locator['decisions'][0];assert recovered['original_locator_missing_resolved'] and len(recovered['locators'])==7
    queue=read(G2/'reconciliation/next_uncovered_tasks.json');oldtasks=queue['global_master_tasks']
    removed=[t for t in oldtasks if t['master_id']==recovered['master_id']];assert len(removed)==1
    queue['global_master_tasks']=[t for t in oldtasks if t['master_id']!=recovered['master_id']]
    queue['locator_recovery_history']=[dict(task=removed[0],decision=recovered,grade_scope='ORIGINAL_G2_ALIAS_ONLY_NOT_NEW_G3_COVERAGE')]
    queue['counts'].update(global_master_tasks=1,partial_master_tasks=1,source_locator_only_tasks=1)
    queue['parent_g2_accepted_queue_sha256']=sha((G2/'reconciliation/next_uncovered_tasks.json').read_bytes())
    queue['authoring_priority_guidance']='Continue38 finite G2 tasks/50candidate constraints,10asset-only masters and1original G3 locator. Do not reauthor completed core or the recovered G2 collinear alias.'
    write(RUN/'next_uncovered_tasks.json',queue)
    now=datetime.now(timezone.utc).isoformat()
    run=dict(run_id=G2.name,cases=6,chat_rows=24,by_grade={'2':6},bundle=bundle,source_member='data/release/accepted_cases.jsonl',chat_member='data/release/accepted_chat.jsonl',token_audit_member='data/release/token_audit.json',acceptance_status='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED',new_human_attestation=False,training_started=False)
    assert all(r['run_id']!=run['run_id'] for r in state['sgk_finish_runs'])
    state['sgk_finish_runs'].append(run);state['accepted_cases']+=6;state['training_chat_rows']+=24
    state['all_available_chat_rows_including_evaluation_and_audit']+=24;state['by_grade']['2']+=6
    assert sum(state['by_grade'].values())==state['accepted_cases']==1629858
    state['all_data_union_recipe_history'].append(state['latest_all_data_union_recipe'])
    state['latest_all_data_union_recipe']=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member=G2.name+'/publish_latest_union_recipe.json',sha256=union['recipe_sha256'],payload_references=37,source_members=218,chat_members=31,declared_candidate_chat_rows=6502088,current_pedagogy_eval_rows_separate=48,historical_split_totals_pending_full_archive_audit=True,actual_train_only_row_total_verified=False,full_archive_audit_complete=False)
    state['sgk_accepted_reconciliation_history'].append(state['latest_sgk_accepted_reconciliation'])
    recon=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member=RUN.name+'/next_uncovered_tasks.json',sha256=sha((RUN/'next_uncovered_tasks.json').read_bytes()),counts=queue['counts'],accepted_cases_bound=6,bound_run=G2.name,source_locator_recovered_from_prior_receipts=1,all_sgk_forms_covered=False)
    state['latest_sgk_accepted_reconciliation']=recon
    state['data_only_colab_observation_history'].append(state['latest_colab_runtime_observation'])
    observation=dict(notebook_id=nb['id'],client_reporting_date='2026-10-22',transport='OFFICIAL_GOOGLE_COLAB_MCP',runtime_status=status,worker_running_currently_verified=False,prior_v3_migration_receipt_member=RUN.name+'/mcp_evidence/v3_actual_migration_and_primary_complete.json',checkpoint_metadata=read(RUN/'mcp_evidence/v3_checkpoint_remote_metadata_only.json'),checkpoint_id='16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI',live_v3_status_cell='kMrD9lPx_l2W',full_archive_audit_complete=False,training_started=False,TRAINING_DATASET_READY=False)
    state['latest_colab_runtime_observation']=observation
    state['data_only_notebook_publication_history'].append(state['latest_data_only_colab_notebook']);state['latest_data_only_colab_notebook']=nb
    state['full_archive_audit_code_history'].append(state['latest_full_archive_audit_code'])
    state['latest_full_archive_audit_code']=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member=RUN.name+'/code/math_data_full_audit_v3.py',sha256=sha((HERE/'math_data_full_audit_v3.py').read_bytes()),status='V3_CHECKPOINT_EXISTS_RUNTIME_RESTORE_REQUIRED',v3_tests=9,primary_source_rows_bound=782,primary_chat_hash_chains_bound=3128,v2_checkpoint_id_preserved='182zLHZU0XBpTfKm7ThJpfy37GgFJ7Ob2',v3_checkpoint_id='16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI',regression_only_finding_preserved_not_train_eligible=True,training_started=False)
    state['latest_g2_finite_preparation_plan']=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member=RUN.name+'/next_uncovered_tasks.json',sha256=recon['sha256'],finite_tasks_pending=38,candidate_constraints_pending=50,accepted_case_delta=6,all_sgk_forms_covered=False)
    state.update(updated_utc=now,client_reporting_date='2026-10-22',TRAINING_DATASET_READY=False,training_started=False,status='FINITE_SGK_APPEND_ACCEPTED_FULL_ARCHIVE_AUDIT_RESUME_REQUIRED')
    state['next_action']='Restore EXISTING V3 checkpoint16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI in Colab CPU only: fresh metadata/appProperties SHA plus whole streamed raw readback, strict249-member recipe e4197a8e797a6c4d22b938779b663d0e306536dc8af75a5f81fb3c98f7e1a7a8 and V3identity06339a42b0a4b8d2c8ce7b1031a41a6ca1fc936dd361dd4055e17f8796f5b8e2. Read actual saved counts/issues before resume. Do not create another V3, rerun V2 worker, restore the older V2 in place, Run all, train or load weights. Latest live runtime has no status file. Continue38G2tasks/50constraints,1source locator and10asset masters from exact queue; preserve all old data and299signoffs.'
    chat['chat_rows']+=24;chat['all_available_chat_rows_including_evaluation_and_audit']+=24;chat['supplement_bundles'].append(run)
    chat['latest_finite_sgk_reconciliation']=recon;chat['latest_data_only_colab_observation']=observation
    write(RUN/'publish_state.json',state);write(RUN/'publish_chat_manifest.json',chat)
    context=HERE.parent/'MATH_TRAINING_CONTEXT.md';assert context.read_bytes()==(RUN/'prewrite_context.md').read_bytes()
    marker='### Nhật ký 22/10/2026 — thêm 6 bài G2, khôi phục schema V3 và nguồn trang'
    old=context.read_text('utf8');assert marker not in old
    old=re.sub(r'^<!-- CURRENT_CHECKPOINT[^\n]*-->\n','',old)
    log=f'''\n\n{marker}
Thêm 6 bài lớp 2 / 24 chat sau root đọc đủ đề, givens, request, student_work, steps, reasons, explanations, answers, initial và 18 hint. Có peer độc lập, 6 oracle hữu hạn, root kiểm bằng duyệt số thập phân theo sức chứa kho thẻ, 7 phép Fraction/Decimal, 12 negative checks và tokenizer toàn 24 chat. Sửa 50 chỗ diễn đạt bằng bản dẫn xuất; giữ toàn bộ cha, đáp án và lịch sử. Nhãn ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED, nguồn AI và human flags false; không mở rộng 299 signoff. Core vẫn 495/165.
Gói {bundle['url']} có {bundle['bytes']} byte, SHA256 {bundle['sha256']}, đã tải raw mới đối chiếu toàn byte/hash. Tổng 1.629.858 case / 6.502.088 candidate chat; 6.502.200 kể cả eval/audit. Các số này không phải số dạng toán khác nhau hoặc tổng train-only đã audit. Union mới 37 payload / 218 source member / 31 chat member = 249, SHA {union['recipe_sha256']}; giữ nguyên prefix cũ.
Đã gắn đúng accepted hash cho 3 task G2 / 4 nhánh; còn 38 task / 50 candidate constraints. Tìm lại locator alias collinear từ 7 receipt G2 trang 98,99,100,101,110,111,130 có sẵn; lỗi mapping cũ lọc chỉ g3 làm mất locator. Đây là khôi phục nguồn G2, không đọc ảnh mới hay nhận là nguồn G3. Còn 1 locator G3 torn-placeclass pending-source và 10 master asset riêng; không sinh lại bài đã có chỉ để chữa locator.
Auditor V3 hỗ trợ đúng 782 nguồn primary cũ, 39 hàng thiếu can_solve theo quy ước exporter và group cha trước polish, có binding hash riêng cho raw export/canonical export/original source. 9 test thực với tokenizer đạt; đối chiếu đủ 3.128 chat hash chains. V2 checkpoint {restored['parent_checkpoint']['id']} SHA {restored['parent_sha256']} giữ nguyên. Colab đã raw-verify và sao lưu riêng, giữ 110.666 nguồn/18 cursor, sửa projection đúng 256 hash đã index rồi kiểm hết primary782: 111.192 nguồn/19 member lúc đó. Finding regression_only vẫn giữ và không được vào train. Không sửa đáp án hoặc human evidence.
Sau đó mở recipe V3 sang 249 member và tạo đúng một checkpoint V3 ID 16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI. Metadata hiện thấy 2.321.960.960 byte, sửa lần cuối 2026-10-22T04:18:03.804Z; đó chỉ là metadata, chưa raw-verify lại toàn checkpoint mới hoặc biết các số bên trong. Phiên hiện tại trả RUNTIME_OR_STATUS_MISSING; không báo worker đang chạy hoặc audit xong. Phải khôi phục checkpoint V3 hiện có, không khởi tạo lại/V2/Run all. Single-kernel guard và hash/writer check là optimistic, không là khóa phân tán.
Notebook cùng ID có 15 cell, giữ nguồn cha và thêm status tự đủ import cùng ghi chú resume. Fresh raw {nb['bytes']} byte SHA {nb['sha256']}. Mã V3 restore/worker trước đó chưa autosave được giữ trong PROGRESS/{RUN.name}, không làm mất evidence. Gói PROGRESS/chat/context/STATE cập nhật cùng IDs, STATE cuối; chỉ xác nhận đồng bộ sau 4 raw readback. Chưa train, GPU, weights, paid API, app, commit/push. TRAINING_DATASET_READY=false; không xóa lịch hay tuyên bố đủ toàn SGK.
'''
    context.write_text('<!-- CURRENT_CHECKPOINT data_resume_20261022:1629858cases;6502088candidatechat;495core/165nodes;V3_EXISTING_CHECKPOINT_RESTORE_REQUIRED;NO_TRAINING. -->\n'+old+log,encoding='utf8')
    regpath=BASE/'drive_artifacts.json';reg=read(regpath)
    reg['latest_finite_g2_append']=run;reg['latest_data_only_notebook']=nb;reg['latest_data_only_mcp_observation']=observation;write(regpath,reg)
    newfiles={}
    for p in RUN.rglob('*'):
        if p.is_file() and p.suffix in ('.json','.py','.ipynb') and not p.name.startswith(('prewrite_','publish_','four_controls_')):
            newfiles[RUN.name+'/'+p.relative_to(RUN).as_posix()]=p.read_bytes()
    for p in [G2/'publish_latest_union_recipe.json',G2/'union_scope.json',G2/'bundle_remote_verified.json',G2/'release/audit_report.json',G2/'release/token_audit.json']:
        newfiles[G2.name+'/'+p.relative_to(G2).as_posix()]=p.read_bytes()
    for n in ['math_data_full_audit_v3.py','math_data_primary782_bindings_v3.py','math_data_primary782_adapter_v3_validation.json','build_math_data_primary782_adapter_v3.py','test_math_data_full_audit_v3.py','prepare_v3_cloud_resume_20261022.py','g2_numerals_root_review_20261022.py','g2_finite_forms_release.py','test_g2_finite_forms_release.py','save_current_data_notebook_20261022.py','publish_data_resume_20261022.py']:
        if (HERE/n).exists():newfiles[RUN.name+'/code/'+n]=(HERE/n).read_bytes()
    for n in ['v3_peer_review_20261022.json','worker_review.json']:
        newfiles[RUN.name+'/parent_code_reviews/'+n]=(HERE/'cloud_publication/colab_data_audit_20261021'/n).read_bytes()
    newfiles[RUN.name+'/state.json']=(RUN/'publish_state.json').read_bytes();newfiles[RUN.name+'/chat.json']=(RUN/'publish_chat_manifest.json').read_bytes()
    newfiles[RUN.name+'/MATH_TRAINING_CONTEXT.md']=context.read_bytes();newfiles[RUN.name+'/drive_artifacts.json']=regpath.read_bytes()
    forbidden=re.compile(r'\.blob\.core\.windows\.net|Bearer\s+[A-Za-z0-9._-]{20,}|[?&]sig=[A-Za-z0-9%]|mcpProxyToken=[A-Za-z0-9_-]{12,}',re.I)
    assert all(not forbidden.search(b.decode('utf8',errors='ignore')) for b in newfiles.values())
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as parent,zipfile.ZipFile(RUN/'publish_progress_index.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as out:
        assert not set(parent.namelist())&set(newfiles)
        for info in parent.infolist():out.writestr(info,parent.read(info.filename))
        for n,b in sorted(newfiles.items()):out.writestr(n,b)
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as parent,zipfile.ZipFile(RUN/'publish_progress_index.zip') as out:
        assert not out.testzip() and len(out.namelist())==len(set(out.namelist()))
        assert all(parent.read(n)==out.read(n) for n in parent.namelist())
    print(json.dumps(dict(accepted_cases=state['accepted_cases'],candidate_chat_rows=chat['chat_rows'],new_cases=6,new_chat=24,core=495,g2_pending_tasks=38,source_locators_pending=1,training_started=False,ready=False)))
if __name__=='__main__':main()

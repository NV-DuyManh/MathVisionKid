"""Prepare local four-control publication payload for the isolated 3-hour T4 branch.

No Drive/network APIs are imported or called. Inputs are four fresh raw-readback
parent controls plus a bounded branch evidence directory. Outputs are staged
next_* files and pins for a separate authorized publisher.
"""
from __future__ import annotations
import argparse, hashlib, json, zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRANCH = HERE
CODE_FILES = [
    'initialize_budget_runtime.py', 'budget_status_runtime.py',
    'start_isolated_install_runtime.py', 'start_cpu_stratified_sampler_launcher.py',
    'launch_unsloth_preflight_runtime.py', 'probe_preflight_status_runtime.py',
    'probe_train_schema_runtime.py', 'inspect_sampling_metadata_runtime.py',
    'repair_preflight_exact_revision_runtime.py', 'pause_old_training_at_boundary_runtime.py',
    'launch_budget_training_runtime.py', 'sampling/stratified_training_view.py',
    'sampling/colab_train_view_worker.py', 'training/unsloth_t4_worker.py',
    'compatibility/requirements-pinned.txt',
]
OLD_CHECKPOINT = {'id':'1DySpSGkoJ3pyNYCwObfbrNhD8y94F-zi','bytes':209670333,'step':1056,'rows_done':16896,'fresh_raw_readback_verified':True,
                  'sha256':'3c6bcb36fce2366d8b042d356e92b69cd63903f04de1513cb21550643806f4e6'}
OLD_ADAPTER = {'id':'1Uf6JJ8BSyeHt-ltjOa_zCYHlXR0T8040','bytes':66595504,'fresh_raw_readback_verified':True,
               'sha256':'3431a7ddd6d7bf0f15d16e271a6d750f3de95b92abd6bfb42e2e335d970eb5f4'}
BUDGET_START='2026-10-23T14:15:52Z'; BUDGET_DEADLINE='2026-10-23T17:15:52Z'

def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def readj(p:Path): return json.loads(p.read_bytes())
def writej(p:Path,v): p.write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input_dir',help='Directory containing parent_* controls and parent_controls_raw_verified.json')
    ap.add_argument('output_dir',help='New local staging directory; must not already exist')
    a=ap.parse_args(); src=Path(a.input_dir).resolve(); out=Path(a.output_dir).resolve()
    if out.exists(): raise SystemExit('output_dir already exists; use a fresh staging directory')
    proofs=readj(src/'parent_controls_raw_verified.json')
    if isinstance(proofs,dict): proofs=proofs.get('verified')
    if not isinstance(proofs,list) or {p.get('kind') for p in proofs}!={'progress','chat','context','state'}: raise SystemExit('parent proof must contain exactly the four control kinds')
    ids={}
    for proof in proofs:
        k=proof['kind']; ext={'progress':'.zip','chat':'.json','context':'.md','state':'.json'}[k]
        p=src/f'parent_{k}{ext}'; b=p.read_bytes()
        if not proof.get('fresh_raw_readback_verified',proof.get('fresh_raw_verified',False)) or len(b)!=proof['bytes'] or sha(b)!=proof['sha256']:
            raise SystemExit(f'parent {k} does not match fresh raw-readback pin')
        ids[k]=proof['id']
    if len(ids)!=4: raise SystemExit('duplicate parent control kind')
    # Copy source controls into staging; no parent or canonical file is edited.
    out.mkdir(parents=True)
    for k,ext in [('progress','.zip'),('chat','.json'),('context','.md'),('state','.json')]:
        (out/f'parent_{k}{ext}').write_bytes((src/f'parent_{k}{ext}').read_bytes())
    code=[(BRANCH/n) for n in CODE_FILES]
    missing=[str(p) for p in code if not p.is_file()]
    if missing: raise SystemExit('missing branch code: '+', '.join(missing))
    branch_index=[]
    for p in code:
        b=p.read_bytes(); branch_index.append({'path':p.relative_to(BRANCH).as_posix(),'bytes':len(b),'sha256':sha(b)})
    code_manifest={'branch':'t4_budget_3h_20261023','code_only':True,'training_started':False,
        'budget_start_utc':BUDGET_START,'budget_deadline_utc':BUDGET_DEADLINE,
        'preserved_old_checkpoint':OLD_CHECKPOINT,'preserved_old_adapter':OLD_ADAPTER,
        'optimizer':'fresh optimizer for stratified subset; not started at preparation time',
        'source_and_full_corpus':'preserve existing immutable source and full corpus; branch trains on separately frozen stratified subset',
        'files':branch_index}
    writej(out/'branch_code_manifest.json',code_manifest)
    progress=out/'next_progress.zip'
    with zipfile.ZipFile(src/'parent_progress.zip') as old, zipfile.ZipFile(progress,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as new:
        names=old.namelist()
        if len(names)!=len(set(names)): raise SystemExit('parent progress archive contains duplicate members')
        for info in old.infolist(): new.writestr(info,old.read(info.filename))
        additions={'branch_code_manifest.json':(out/'branch_code_manifest.json').read_bytes()}
        additions.update({f't4_budget_3h_20261023/code/{p.relative_to(BRANCH).as_posix()}':p.read_bytes() for p in code})
        for name,b in additions.items():
            if name in names: raise SystemExit(f'archive member already exists: {name}')
            new.writestr(name,b)
    # Branch-scoped metadata prevents ambiguity with preserved legacy training state.
    branch={'branch':'t4_budget_3h_20261023','budget_start_utc':BUDGET_START,'budget_deadline_utc':BUDGET_DEADLINE,
        'preserved_old_checkpoint':OLD_CHECKPOINT,'preserved_old_adapter':OLD_ADAPTER,
        'fresh_optimizer_training_started':False,'stratified_subset_training_started':False,
        'source_and_full_corpus_preserved':True,'branch_code_manifest_sha256':sha((out/'branch_code_manifest.json').read_bytes()),
        'code_file_count':len(code),'prepared_utc':datetime.now(timezone.utc).isoformat()}
    state=readj(src/'parent_state.json'); chat=readj(src/'parent_chat.json')
    for doc in (state,chat):
        doc.setdefault('preserved_full_text_training_runs',[]).append(doc.get('current_full_text_training_run'))
        if isinstance(doc.get('current_full_text_training_run'),dict):
            doc['current_full_text_training_run'].update(worker_alive=False,state='OWNER_SCOPE_CHANGED_SAFELY_PAUSED',last_verified_checkpoint=OLD_CHECKPOINT,rows_done=16896,step=1056,epoch_complete=False)
        doc['whole_training_epoch_completed']=False
    state.setdefault('t4_budget_branch_history',[]).append(state.get('latest_t4_budget_branch'))
    state['latest_t4_budget_branch']=branch; chat['latest_t4_budget_branch']=branch
    writej(out/'next_state.json',state); writej(out/'next_chat.json',chat)
    context=(src/'parent_context.md').read_bytes()
    marker='### Nhật ký — nhánh T4 stratified budget 3 giờ'
    if marker.encode() in context: raise SystemExit('branch journal marker already exists')
    delta=(f'\n\n{marker}\nNhánh riêng có ngân sách {BUDGET_START}–{BUDGET_DEADLINE}. '
      f'Giữ checkpoint cũ ID{OLD_CHECKPOINT["id"]} ({OLD_CHECKPOINT["bytes"]} byte, SHA256 {OLD_CHECKPOINT["sha256"]}) '
      f'và adapter ID{OLD_ADAPTER["id"]} ({OLD_ADAPTER["bytes"]} byte, SHA256 {OLD_ADAPTER["sha256"]}); '
      'dữ liệu nguồn và toàn bộ corpus được giữ nguyên. Nhánh dùng optimizer mới và tập con phân tầng riêng; tại thời điểm chuẩn bị chưa bắt đầu train. '
      'Chỉ các tệp code cùng manifest đã pin được thêm vào gói PROGRESS. Không chứa model weights hoặc corpus. '
      'Unsloth2026.10.7 đã tải đúng snapshot70d244cc86ccca08cf5af4e1e306ecf908b1ad5e với SDPA trênT4. Worker riêng đang đánh giá base, chờ training view được kiểm và chưa cập nhật optimizer. Chỉ coi sync hoàn tất khi publisher kiểm raw readback cả bốn ID.\n').encode()
    (out/'next_context.md').write_bytes(context+delta)
    # Preserve all previous archive members and verify exact byte equality.
    with zipfile.ZipFile(src/'parent_progress.zip') as old, zipfile.ZipFile(progress) as new:
        if not all(old.read(n)==new.read(n) for n in old.namelist()): raise SystemExit('existing progress member changed')
    pins={}
    for k,ext in [('progress','.zip'),('chat','.json'),('context','.md'),('state','.json')]:
        b=(out/f'next_{k}{ext}').read_bytes(); pins[k]={'id':ids[k],'path':str(out/f'next_{k}{ext}'),'bytes':len(b),'sha256':sha(b)}
    writej(out/'prepared_control_updates.json',{'controls':pins,'state_must_be_written_last':True,'new_case_count':0,'new_chat_count':0,'training_started':False,'drive_calls_made':False,'canonical_context_written':False})
    print(json.dumps({'prepared':True,'controls':pins,'code_manifest_sha256':code_manifest['files'] and sha((out/'branch_code_manifest.json').read_bytes()),'drive_calls_made':False},ensure_ascii=False))
if __name__=='__main__': main()

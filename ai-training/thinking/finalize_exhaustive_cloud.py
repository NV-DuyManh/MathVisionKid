"""Publish a small Drive index, then remove only this run's verified staging data."""
import hashlib, json, shutil, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
DATA = HERE / 'data/exhaustive_math_v1'
EVIDENCE = HERE / 'evidence/exhaustive_math_20261018'
CONTROL = HERE / 'cloud_publication'
CONTEXT = PROJECT / 'MATH_TRAINING_CONTEXT.md'
IDS = HERE / 'data/primary_math_teacher_20261016/drive_artifacts.json'
BASELINE_SHA = '70071b60a78412b4d8709959414be795d2076fb9d7f71d4547a247e8e714217a'
SNAPSHOT = EVIDENCE / 'snapshot/finite495_70071b60a78412b4/Primary_Math_Teacher_20261016_PROGRESS.zip'
OLD_PROGRESS = HERE / 'evidence/primary_math_teacher_20261016/Primary_Math_Teacher_20261016_PROGRESS.zip'

def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(p.read_text('utf-8'))
def write(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n', 'utf-8')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def prepare():
    receipt=read(EVIDENCE/'remote_publication_verified.json')
    assert receipt['status']=='ALL14_PARTS_FRESH_RAW_BYTE_HASH_VERIFIED'
    parts=receipt['parts']
    assert len(parts)==14 and len({p['file_id'] for p in parts})==14
    assert all(p['all_bytes_equal'] for p in parts)
    assert sum(p['chat_rows'] or 0 for p in parts)==6074308
    assert sha(SNAPSHOT)==BASELINE_SHA
    CONTROL.mkdir(parents=True,exist_ok=True)
    policy={'updated_utc':now(),'cloud_only':True,'owner_instruction':'đưa data thẳng lên driver đi đừng lưu vào máy tôi',
      'durable_payload_storage':'Google Drive folder 19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n',
      'local_bulk_generation_disabled':True,'future_resume':'Use one bounded temporary shard at a time; exact QA, upload, fresh raw byte/hash readback, remote checkpoint, then delete that shard. Never rematerialize the published corpus locally.',
      'existing_original_data':'Preserved; owner request removes newly generated payloads/staging only.',
      'human_review_policy':'Validated labels accepted automatically; no authorship-based accuracy penalty, no invented future human review.'}
    write(HERE/'exhaustive_cloud_storage_policy.json',policy)
    registry={'schema_version':'exhaustive_cloud_reference.v1','updated_utc':now(),
      'status':'PAYLOADS_REMOTE_VERIFIED_CONTROL_PUBLICATION_PENDING','folder_id':'19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n',
      'folder_url':'https://drive.google.com/drive/folders/19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n',
      'accepted_cases':1519171,'new_cases':1518389,'training_chat_rows':6074308,
      'finite_core_cases':495,'finite_core_nodes':165,'all_requested_exhaustive_domains_completed':False,
      'parts':[{**p,'url':'https://drive.google.com/file/d/'+p['file_id']+'/view'} for p in parts],
      'parts_total_bytes':sum(p['bytes'] for p in parts),
      'fresh_raw_verification':{'verified_utc':receipt['verified_utc'],'scope':'Every remote payload byte compared with uploaded source, size and SHA256 checked for all14parts.'},
      'usage':{'corpus':'Extract all seven independent corpus ZIP archives to the same directory. Each archive contains distinct members; no separate large PROGRESS download is required.',
               'chat':'Read the seven .jsonl.gz parts in numeric order. Each is valid gzip JSONL; together they contain6,074,308rows. Do not train on audit/source JSONL from corpus ZIPs.',
               'qwen':'No model training performed. Token audit covers baseline/extensions and arithmetic probes, not every arithmetic row. No truncation authorized.'},
      'remaining_ranges':read(DATA/'capacity_and_resume_plan.json')['future_ranges'],
      'local_storage':{'policy':'cloud_only','new_payloads_cleanup':'PENDING_CONTROL_VERIFICATION','original_data_preserved':True},
      'drive_connector_at_publication':{'display_name':'Duy Mạnh','email':'duymanhdnvn20092005@gmail.com','profile_id':'100868736881483931302','note':'Currently exposed connector successfully wrote the same authorized existing folder; historical connection identity retained in drive_artifacts.'},
      'control_ids':{'progress_zip':'1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX','chat_manifest':'1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6','state':'1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme','context':'13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9'}}
    write(HERE/'exhaustive_cloud_reference.json',registry)
    chat={'format':'partitioned_gzip_jsonl','chat_rows':6074308,'parts':[p for p in registry['parts'] if p['kind']=='chat_gzip'],
      'read_in_order':True,'selection':'Training view only; complete accepted corpus is separately partitioned into seven ZIPs.',
      'protection_note':'Known protected arithmetic overlaps retained in full corpus and excluded from new training views. Baseline13numeric exceptions disclosed; no claim of total evaluation independence.',
      'storage':'Remote only; local new data removed after control verification.'}
    write(CONTROL/'MathVisionKid_CHAT_PARTS.json',chat)
    ids=read(IDS)
    ids['historical_account_identity']=ids.get('account_identity')
    ids['account_identity']='Duy Mạnh / profile100868736881483931302 / duymanhdnvn20092005@gmail.com; current connector, same authorized folder and artifact IDs'
    ids['connection_binding_verified_utc']=now()
    ids['current_tool_binding']='Current Google Drive schemas omit link_id; do not send stale link_id. Confirm current profile and exact folder/file access.'
    ids['artifact_replacement_policy']='Same four existing control IDs; PROGRESS is a small index ZIP, chat_train_id is CHAT_PARTS.json manifest. Fourteen unique payload parts in existing folder; no new folder or duplicate payload.'
    ids['chat_train_local_path']=None
    ids['cloud_reference']='thinking/exhaustive_cloud_reference.json'
    ids['cloud_parts']=registry['parts']
    write(IDS,ids)
    old=CONTEXT.read_text('utf-8')
    start=old.index('Gói mới tạm:')
    end=old.index('\n\n',start)
    replacement=('Đã đưa14phần lên đúng thư mục Drive19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n:7ZIPcorpus +7gzipchat, tổng954.733.408bytes. '
      'Freshrawreadback đã so sánh từngbyte, bytecount vàSHA256 khớp toàn14phần; không cần tải lại bản474MB đơn. '
      'Mục lục vàhash từngphần: thinking/exhaustive_cloud_reference.json; chatID1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6 sẽ chứaCHAT_PARTS.json; PROGRESSID cũ chứaZIPindexnhỏ. '
      'State/context giữ đúngIDcũ. Tệp tạm local chờ xácminh cáccontrol trước khi dọn; không tự sinh lại dữ liệu local. '
      'Miền lớn10.000/100.000 vẫnNOT_STARTED, không ghihoàntất. Skills applied: google-drive:google-drive, skill-installer, last30days; local data skills:none. '
      'Khôngtrain/GPU/paidAPI/production/commit/push. Lịchfinite495đãxóa, khôngtạolại.')
    CONTEXT.write_text(old[:start]+replacement+old[end:],'utf-8')
    bundle=CONTROL/'MathVisionKid_PROGRESS_CLOUD_INDEX.zip'
    selected=[HERE/'exhaustive_cloud_reference.json',HERE/'exhaustive_cloud_storage_policy.json',IDS,
      CONTROL/'MathVisionKid_CHAT_PARTS.json',EVIDENCE/'remote_publication_verified.json',EVIDENCE/'cloud_parts_upload_plan.json',EVIDENCE/'remote_publication_uploads.json',
      DATA/'full_corpus_and_training_views.json',DATA/'extension_integration.json',DATA/'capacity_and_resume_plan.json',DATA/'data_build_state.json',DATA/'owner_acceptance_policy.json']
    selected+=list(HERE.glob('exhaustive_*.py'))
    selected+=[HERE/'export_exhaustive_chat.py',HERE/'finalize_exhaustive_cloud.py']
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(SNAPSHOT,'preserved_baseline/Primary_Math_Teacher_20261016_PROGRESS.zip')
        for p in selected:
            if p.exists():z.write(p,p.relative_to(PROJECT).as_posix())
    assert bundle.stat().st_size<100*1024*1024
    with zipfile.ZipFile(bundle) as z:assert z.testzip() is None
    write(CONTROL/'control_upload_plan.json',{'artifacts':[
      {'key':'progress','file_id':registry['control_ids']['progress_zip'],'path':str(bundle),'name':bundle.name,'mime_type':'application/zip','sha256':sha(bundle),'bytes':bundle.stat().st_size},
      {'key':'chat','file_id':registry['control_ids']['chat_manifest'],'path':str(CONTROL/'MathVisionKid_CHAT_PARTS.json'),'name':'MathVisionKid_CHAT_PARTS.json','mime_type':'application/json','sha256':sha(CONTROL/'MathVisionKid_CHAT_PARTS.json'),'bytes':(CONTROL/'MathVisionKid_CHAT_PARTS.json').stat().st_size},
      {'key':'state','file_id':registry['control_ids']['state'],'path':str(HERE/'exhaustive_cloud_reference.json'),'name':'MathVisionKid_CLOUD_STATE.json','mime_type':'application/json','sha256':sha(HERE/'exhaustive_cloud_reference.json'),'bytes':(HERE/'exhaustive_cloud_reference.json').stat().st_size},
      {'key':'context','file_id':registry['control_ids']['context'],'path':str(CONTEXT),'name':'MATH_TRAINING_CONTEXT.md','mime_type':'text/markdown','sha256':sha(CONTEXT),'bytes':CONTEXT.stat().st_size}]})
    print(json.dumps({'prepared':True,'control_zip_bytes':bundle.stat().st_size,'verified_payload_parts':14}))

def cleanup():
    proof=read(CONTROL/'controls_verified.json')
    assert proof['all_controls_verified'] and len(proof['artifacts'])==4
    registry=read(HERE/'exhaustive_cloud_reference.json')
    assert len(registry['parts'])==14 and all(p['all_bytes_equal'] for p in registry['parts'])
    assert sha(SNAPSHOT)==BASELINE_SHA
    # Restore the original pre-existing local archive, not the newly generated large replacement.
    old_replacement_size=OLD_PROGRESS.stat().st_size
    shutil.copyfile(SNAPSHOT,OLD_PROGRESS)
    assert sha(OLD_PROGRESS)==BASELINE_SHA
    deleted=0
    for target,expected in [(DATA,HERE/'data/exhaustive_math_v1'),(EVIDENCE,HERE/'evidence/exhaustive_math_20261018')]:
        resolved=target.resolve()
        assert resolved==expected.resolve() and resolved.is_relative_to(HERE.resolve())
        assert resolved.name in ('exhaustive_math_v1','exhaustive_math_20261018')
        deleted+=sum(p.stat().st_size for p in resolved.rglob('*') if p.is_file())
        # This run's snapshot has read-only preservation files. Clear only those file bits.
        for p in resolved.rglob('*'):
            if p.is_file():p.chmod(0o600)
        shutil.rmtree(resolved)
        assert not resolved.exists()
    registry['updated_utc']=now()
    registry['status']='REMOTE_PAYLOADS_VERIFIED_LOCAL_NEW_DATA_REMOVED'
    registry['local_storage']={'policy':'cloud_only','new_payloads_cleanup':'COMPLETED','new_run_roots_removed':['thinking/data/exhaustive_math_v1','thinking/evidence/exhaustive_math_20261018'],
      'removed_run_bytes':deleted,'replaced_progress_archive_bytes':old_replacement_size,'original_progress_restored_sha256':BASELINE_SHA,'original_data_preserved':True,'bulk_local_generation_disabled':True}
    write(HERE/'exhaustive_cloud_reference.json',registry)
    text=CONTEXT.read_text('utf-8')
    text=text.replace('Tệp tạm local chờ xácminh cáccontrol trước khi dọn; không tự sinh lại dữ liệu local.',
      'BốncontrolID cũ đã cập nhật vàfreshrawbyte/hashkhớp. Đã dọn toànbộ hairoot dữ liệu/evidence mới của đợt mởrộng sau xácminh; khôi phụcZIPPROGRESS finitegốc đúngSHA70071b60a78412b4d8709959414be795d2076fb9d7f71d4547a247e8e714217a. Chỉgiữcontext, code và thamchiếuDrive nhỏ; không tự sinh lại dữ liệu local.')
    text+='\n\n### Nhật ký 18/10/2026 — hoàn tất phát hành cloud và dọn staging theo yêu cầu\n\n'
    text+=f'14payloadpart đãupload và tải rawmới so từngbyte/hash;7corpusZIP+7chatgzip tổng954.733.408bytes,1.519.171accepted/6.074.308chat. BốnIDcontrol cũ đãđược cậpnhật/xácminh trước dọn. Đãxóa hairoot mới chứa {deleted:,}bytes và khôi phụcPROGRESSgốc; khôngxóa nguồn gốc trướcđợtnày. Reference: thinking/exhaustive_cloud_reference.json. Lưu dữliệu lâu dài trênDrive; miền lớn chưa sinh phải dùng shardtạm cógiớihạn, publish+readback+checkpoint rồi dọn, khôngkhởi tạolại local. Chưa train và chưa tuyênbố xong yêu cầu vétcạn10.000/100.000. State/context hậucleanup cần đồngbộ/xácminh lại lầncuối.\n'
    CONTEXT.write_text(text,'utf-8')
    print(json.dumps({'cleanup_completed':True,'removed_run_bytes':deleted,'baseline_progress_restored':True}))

if __name__=='__main__':
    {'prepare':prepare,'cleanup':cleanup}[sys.argv[1]]()

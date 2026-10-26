"""Preserve the handed-off bytes in one audit-only cloud intake artifact."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,zipfile
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'handoff'
MOUNT=Path(r'G:\.shortcut-targets-by-id\19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n\primary_math_teacher_20261016')
RUN=HERE/'cloud_publication/antigravity_intake_20261022';RUN.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def write(name,v):(RUN/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
handoff=(BASE/'ANTIGRAVITY_G2_FINAL_HANDOFF_MANIFEST.json').read_bytes()
assert sha(handoff)=='6848d7a7a73be7f6a91944bc2997e3c01783b88973d0c4284c884fc59e365423'
manifest=json.loads(handoff)
sources=[];chats=[];originals={};batches=[]
for ref in manifest['releases']:
    p=BASE/ref['release_zip']
    if not p.exists():p=MOUNT/ref['release_zip']
    blob=p.read_bytes();assert len(blob)==ref['zip_bytes'] and sha(blob)==ref['zip_sha256']
    originals['original_batches/'+p.name]=blob
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        cases=[json.loads(line) for line in z.read('accepted_cases.jsonl').decode('utf8').splitlines() if line.strip()]
        chat=[json.loads(line) for line in z.read('accepted_chat.jsonl').decode('utf8').splitlines() if line.strip()]
        assert len(cases)==ref['cases_count'] and len(chat)==ref['chat_count']
    sources+=cases;chats+=chat
    batches.append(dict(batch=ref['batch_number'],zip=p.name,bytes=len(blob),sha256=sha(blob),cases=len(cases),chats=len(chat),
        original_manifest_id=ref['drive_item_id'],original_id_is_cloud_verified=False))
assert len(sources)==len({r['sample_id'] for r in sources})==53
assert len(chats)==len({r['sample_id'] for r in chats})==212
report=dict(schema='MathVisionKid.AntigravityOriginalIntake.v1',observed_utc=datetime.now(timezone.utc).isoformat(),
    role='ORIGINAL_AI_HANDOFF_AUDIT_ONLY_PENDING_ROOT_REPAIRS',batches=batches,original_cases=53,original_chats=212,
    handoff_manifest_sha256=sha(handoff),all_whole_zip_hashes_match=True,
    root_accepted_new_cases=0,train_eligible=False,core_cases_unchanged=495,core_nodes_unchanged=165,
    cloud_claim='Original DriveFS reads are local mount evidence; placeholder drive_item IDs are not remote server receipts.',
    report_token_max_claim=782,manifest_token_max_claim=909,
    preserve_all_originals=True,original_owner299_signoffs_unchanged=True,training_started=False,
    source_content_qa='IN_PROGRESS_DERIVED_REPAIRS_REQUIRED')
write('original_intake.json',report)
originals['original_handoff_manifest.json']=handoff
originals['original_handoff_report.md']=(BASE/'ANTIGRAVITY_DATA_HANDOFF_20261022.md').read_bytes()
originals['original_batch1_drivefs_verification.json']=(BASE/'BATCH1_DRIVE_VERIFICATION_20261022.json').read_bytes()
originals['intake_manifest.json']=(RUN/'original_intake.json').read_bytes()
out=RUN/'original_intake_audit_only.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name,blob in originals.items():
        info=zipfile.ZipInfo(name,date_time=(2026,10,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,blob)
with zipfile.ZipFile(out) as z:
    assert all(z.read(name)==blob for name,blob in originals.items())
print(json.dumps({'intake_bytes':out.stat().st_size,'intake_sha256':sha(out.read_bytes()),'original_cases':53,'root_new_accepted':0,'training_started':False}))

if __name__=='__main__':pass

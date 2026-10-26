# Load the already published, exact V3 auditor. CPU data only.
import io,zipfile,importlib,hashlib,os
assert os.environ.get('COLAB_GPU','0') in ('0','')
progress_code=reader.read('1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',128*1024*1024)
module_pins={
'data_resume_20261022/code/math_data_full_audit_v3.py':'02431da433060a6574127f9a8e14d90cabffe85d8d0150c3b2a331dc15b4be1f',
'data_resume_20261022/code/math_data_primary782_bindings_v3.py':'4d75e90c07eecccf7571d68015dda16e85a690e7ee2379b28d517d201472580b'}
with zipfile.ZipFile(io.BytesIO(progress_code)) as code_zip:
    assert hashlib.sha256(code_zip.read(recipe_pointer['member'])).hexdigest()==recipe_pointer['sha256']
    for member,pin in module_pins.items():
        module_bytes=code_zip.read(member)
        assert hashlib.sha256(module_bytes).hexdigest()==pin
        (ROOT/'code'/member.rsplit('/',1)[-1]).write_bytes(module_bytes)
importlib.invalidate_caches()
import math_data_full_audit_v3 as audit_v3
assert audit_v3.plan_identity(recipe)=='06339a42b0a4b8d2c8ce7b1031a41a6ca1fc936dd361dd4055e17f8796f5b8e2'
# CPU data preparation only: restore the existing checkpoint, never create one.
import json,hashlib,sqlite3,threading,os
from datetime import datetime,timezone
from googleapiclient.http import MediaIoBaseDownload
import math_data_candidate_stream as C
assert os.environ.get('COLAB_GPU','0') in ('0','')
assert recipe_pointer['sha256']=='e4197a8e797a6c4d22b938779b663d0e306536dc8af75a5f81fb3c98f7e1a7a8'
assert len(recipe['source_members'])+len(recipe['chat_members'])==249
if any(t.name.startswith('MathVisionKidFiniteCPUDataAudit') and t.is_alive() for t in threading.enumerate()):
    raise RuntimeError('Existing active data worker; inspect it without restoring or launching a duplicate.')
EXISTING_V3_ID='16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI'
EXISTING_V3_IDENTITY='06339a42b0a4b8d2c8ce7b1031a41a6ca1fc936dd361dd4055e17f8796f5b8e2'
meta_before=drive_api.files().get(fileId=EXISTING_V3_ID,fields='id,size,appProperties,modifiedTime,version',supportsAllDrives=True).execute()
props=meta_before['appProperties'];pin=props['data_sha256'];size=int(meta_before['size'])
assert props['recipe_identity']==EXISTING_V3_IDENTITY and len(pin)==64 and 0<size<64*1024**3
RESTORED_V3_DB=ROOT/('existing_v3_'+pin[:16]+'.sqlite')
assert not RESTORED_V3_DB.exists(), 'Checkpoint path already exists: verify it instead of overwriting/restarting.'
print({'stage':'STREAMING_EXISTING_V3_CHECKPOINT_TO_COLAB_ONLY','bytes':size,'training_started':False})
with RESTORED_V3_DB.open('wb') as target:
    class HashingFile:
        def __init__(self):self.h=hashlib.sha256();self.size=0
        def write(self,data):
            count=target.write(data);self.h.update(data);self.size+=count;return count
    sink=HashingFile();download=MediaIoBaseDownload(sink,drive_api.files().get_media(fileId=EXISTING_V3_ID,supportsAllDrives=True),chunksize=32*1024*1024)
    done=False
    while not done:
        _,done=download.next_chunk(num_retries=3)
        if sink.size%(256*1024*1024)==0 or done:
            print({'checkpoint_download_bytes':sink.size,'expected_bytes':size,'training_started':False},flush=True)
assert sink.size==size and sink.h.hexdigest()==pin
meta_after=drive_api.files().get(fileId=EXISTING_V3_ID,fields='id,size,appProperties,modifiedTime,version',supportsAllDrives=True).execute()
assert meta_before==meta_after, 'Remote checkpoint advanced during restore; do not resume a stale writer.'
con=sqlite3.connect(RESTORED_V3_DB.as_uri()+'?mode=ro',uri=True)
try:
    assert con.execute('SELECT identity,sequence_limit FROM config').fetchone()==(EXISTING_V3_IDENTITY,40960)
    assert con.execute('PRAGMA quick_check').fetchone()==('ok',)
    entries=recipe['source_members']+recipe['chat_members'];declared={C.member_key(e):e for e in entries}
    member_rows=con.execute('SELECT id,role,next_line,complete,expected_rows FROM members').fetchall()
    for key,role,line,complete,expected in member_rows:
        e=declared[key];assert role==e['role'] and expected==e['rows'] and 0<=line<=expected
        if complete:assert line==expected
    done_keys={r[0] for r in member_rows if r[3]}
    next_entry=next((e for e in entries if C.member_key(e) not in done_keys),None)
    probe_receipt=dict(state='EXISTING_V3_CHECKPOINT_RAW_VERIFIED_READONLY',observed_utc=datetime.now(timezone.utc).isoformat(),checkpoint_id=EXISTING_V3_ID,checkpoint_bytes=size,checkpoint_sha256=pin,fresh_raw_readback_verified=True,remote_metadata_unchanged_during_restore=True,audit_identity=EXISTING_V3_IDENTITY,recipe_sha256=recipe_pointer['sha256'],source_versions_indexed=con.execute('SELECT count(*) FROM source_versions').fetchone()[0],unique_chat_rows_processed=con.execute('SELECT count(*) FROM samples').fetchone()[0],actual_rows_by_split=dict(con.execute('SELECT split,count(*) FROM samples GROUP BY split')),members_complete=len(done_keys),members_expected=249,issues=dict(con.execute('SELECT kind,count(*) FROM issues GROUP BY kind')),first_issue_metadata=con.execute('SELECT member,line,kind,detail FROM issues LIMIT 8').fetchall(),next_member=None if next_entry is None else dict(role=next_entry['role'],member=next_entry.get('member'),rows=next_entry['rows']),sqlite_quick_check='ok',checkpoint_mutated=False,worker_started_by_this_probe=False,training_started=False,gpu_used=False,model_weights_loaded=False,TRAINING_DATASET_READY=False)
finally:con.close()
(ROOT/'existing_v3_restore_readonly_receipt.json').write_text(json.dumps(probe_receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(probe_receipt)

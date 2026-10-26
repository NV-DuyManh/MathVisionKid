"""Prepare exact CPU-only Colab cells; corpus/checkpoint bytes stay in Colab."""
from pathlib import Path
import base64,hashlib,json,zlib
HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/data_resume_20261022'
PINS={
 'math_data_full_audit_v2.py':'81b1e3f04c5886f78282386ecb34d47ba4ba9da63edfec8856bab82034a093ee',
 'math_data_full_audit_v3.py':'02431da433060a6574127f9a8e14d90cabffe85d8d0150c3b2a331dc15b4be1f',
 'math_data_primary782_bindings_v3.py':'4d75e90c07eecccf7571d68015dda16e85a690e7ee2379b28d517d201472580b'}
def main():
    data={}
    for name,pin in PINS.items():
        raw=(HERE/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==pin
        data[name]=dict(sha256=pin,zlib_base64=base64.b64encode(zlib.compress(raw,9)).decode())
    code='''# DATA PREPARATION ONLY: restore pinned V2 snapshot and derive separate V3.
import base64,zlib,importlib,io,os,threading
from datetime import datetime,timezone
from googleapiclient.http import MediaIoBaseDownload,MediaFileUpload
assert os.environ.get('COLAB_GPU','0') in ('0',''), 'CPU runtime required; no GPU work authorized'
assert not any(t.name.startswith('MathVisionKidFiniteCPUDataAudit') and t.is_alive() for t in threading.enumerate()), 'Existing data worker; refuse duplicate'
DEPLOY_MODULES=__MODULES__
for name,ref in DEPLOY_MODULES.items():
    raw=zlib.decompress(base64.b64decode(ref['zlib_base64']))
    assert hashlib.sha256(raw).hexdigest()==ref['sha256']
    (ROOT/'code'/name).write_bytes(raw)
importlib.invalidate_caches()
import exhaustive_colab_loader as L
import math_data_full_audit_v3 as audit_v3
import math_data_candidate_stream as C
assert hashlib.sha256(Path(L.__file__).read_bytes()).hexdigest()=='9b1287f495e30b85085c6d8c23b2fc273e38fefbf1e730d19b0d95a9d8950a3c'
import math_data_archive_audit as archive_audit
assert hashlib.sha256(Path(archive_audit.__file__).read_bytes()).hexdigest()=='d7540fc709b8d1ae5fccc959bda32cbd463b8f23bf9c9098db5f9d2659537d7a'
recipe_all=recipe;pointer_all=recipe_pointer
assert pointer_all['sha256']=='93ec4110b9de95a84bb685ae60b1e4dc4b6df8c4fe568d88c60ca9c2e301c684'
assert len(recipe_all['source_members'])==217 and len(recipe_all['chat_members'])==30
PARENT_ID='182zLHZU0XBpTfKm7ThJpfy37GgFJ7Ob2'
PARENT_SHA='485ae30c164a10c323527265053a7a2e88daa2ca3d781e6a52943a7ca9165245'
parent_meta=drive_api.files().get(fileId=PARENT_ID,fields='id,size,appProperties',supportsAllDrives=True).execute()
assert int(parent_meta['size'])==231927808 and parent_meta['appProperties']['data_sha256']==PARENT_SHA
parent_db=ROOT/('v2_parent_'+PARENT_SHA[:16]+'.sqlite')
assert not parent_db.exists(), 'Do not repeat restore or overwrite a prior parent'
with parent_db.open('wb') as target:
    download=MediaIoBaseDownload(target,drive_api.files().get_media(fileId=PARENT_ID,supportsAllDrives=True),chunksize=8*1024*1024)
    done=False
    while not done:_,done=download.next_chunk(num_retries=3)
def file_digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
assert file_digest(parent_db)==PARENT_SHA and parent_db.stat().st_size==231927808
assert drive_api.files().get(fileId=PARENT_ID,fields='id,size,appProperties',supportsAllDrives=True).execute()==parent_meta
entries=recipe_all['source_members']+recipe_all['chat_members'];declared={C.member_key(e):e for e in entries}
with sqlite3.connect(parent_db.as_uri()+'?mode=ro',uri=True) as con:
    assert con.execute('PRAGMA integrity_check').fetchone()==('ok',)
    committed=con.execute('SELECT id,role,next_line,complete,expected_rows FROM members').fetchall()
    assert len(committed)==19 and {r[0] for r in committed}=={C.member_key(e) for e in entries[:19]}
    for key,role,line,complete,expected_rows in committed:
        e=declared[key];assert role==e['role'] and expected_rows==e['rows'] and 0<=line<=expected_rows
        if complete:assert line==expected_rows
        else:assert e['member_sha256']==audit_v3.PRIMARY_MEMBER_SHA256 and line==256
    assert con.execute('SELECT count(*) FROM source_versions').fetchone()[0]==110666
    assert con.execute('SELECT count(*) FROM samples').fetchone()[0]==0
V3_DB=ROOT/'full_audit_v3.sqlite'
migration_receipt=audit_v3.migrate_v2_snapshot(parent_db,V3_DB,recipe_all,PARENT_SHA,expected_source_versions=110666,expected_members_complete=18,expected_primary_rows=256)
tokenizer=L.load_qwen_tokenizer()
V3_ID=audit_v3.plan_identity(recipe_all)
probe=audit_v3.FullArchiveAudit(V3_DB,recipe_all,tokenizer)
try:
    primary_entry=probe.next_entry();assert primary_entry['member_sha256']==audit_v3.PRIMARY_MEMBER_SHA256
    cache_v3=LazyDriveCache(reader,recipe_all,ROOT/'full_audit_v3_payload_cache')
    primary_span=probe.consume(primary_entry,cache_v3[primary_entry['sha256']],max_rows=1000)
    primary_report=probe.report()
    assert primary_span['complete'] and primary_report['source_versions_indexed']==111192 and primary_report['members_complete']==19
    assert primary_report['issues']=={'SOURCE_SPLIT_MISSING_OR_UNKNOWN':1}
    assert probe.db.execute('SELECT count(*) FROM source_versions WHERE adapter_kind=?',(audit_v3.PRIMARY_ADAPTER_KIND,)).fetchone()[0]==782
finally:probe.close()
assert file_digest(parent_db)==PARENT_SHA
restore_receipt=dict(state='V3_PARENT_RESTORED_AND_PRIMARY782_COMPLETE',observed_utc=datetime.now(timezone.utc).isoformat(),parent_checkpoint=parent_meta,parent_fresh_raw_verified=True,parent_sha256=PARENT_SHA,migration=migration_receipt,primary_span=primary_span,report=primary_report,training_started=False,gpu_used=False,model_weights_loaded=False)
(ROOT/'v3_restore_receipt.json').write_text(json.dumps(restore_receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(restore_receipt)
'''.replace('__MODULES__',repr(data))
    RUN.mkdir(exist_ok=True);(RUN/'v3_restore_cell.py').write_text(code,encoding='utf8')
    base=Path.home()/'.codex/integrations/colab-mcp'
    (base/'data_only_v3_restore_add_args.json').write_text(json.dumps(dict(cellIndex=15,language='python',code=code),ensure_ascii=False),encoding='utf8')
    print(json.dumps(dict(cell_bytes=len(code.encode()),modules=PINS,training_started=False)))
if __name__=='__main__':main()

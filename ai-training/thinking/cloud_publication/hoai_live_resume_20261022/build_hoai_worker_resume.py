"""Derive the published finite worker to attach to its existing verified DB/ID."""
from pathlib import Path
import ast,json,hashlib
ROOT=Path(__file__).resolve().parent
RUN=ROOT/'cloud_publication/mcp_prepare_20261022'
original_bytes=(RUN.parent/'data_resume_20261022/finite_cloud_audit_worker_v3.py').read_bytes()
assert hashlib.sha256(original_bytes).hexdigest()=='b53a9d77ad183ddb84bae5ea04ee6844e93aaa3f1791285601b1f8475aeb8d91'
original=original_bytes.decode('utf8').replace('\r\n','\n')
body=original[original.index('def write_worker_status():'):]
# The initial restored bytes have already been fully hash verified. Save a new
# checkpoint after the first completed member/span, not the identical parent.
assert body.count("        save_checkpoint()\n        full_audit_worker_state['state']='RUNNING_DATA_ONLY'")==1
body=body.replace("        save_checkpoint()\n        full_audit_worker_state['state']='RUNNING_DATA_ONLY'", "        last_save=time.monotonic()\n        full_audit_worker_state['state']='RUNNING_DATA_ONLY'")
body=body.replace("if time.monotonic()-last_save>=300:save_checkpoint()", "if 'checkpoint' not in full_audit_worker_state or time.monotonic()-last_save>=300:save_checkpoint()")
header='''# Attach to the existing, fully raw-verified V3 checkpoint; never create a file.
import threading,time,uuid,shutil
from datetime import datetime,timezone
from googleapiclient.http import MediaIoBaseDownload,MediaFileUpload
assert os.environ.get('COLAB_GPU','0') in ('0','')
if any(t.name.startswith('MathVisionKidFiniteCPUDataAudit') and t.is_alive() for t in threading.enumerate()):
    raise RuntimeError('A data audit worker is already active; do not duplicate it.')
assert probe_receipt['state']=='EXISTING_V3_CHECKPOINT_RAW_VERIFIED_READONLY'
assert probe_receipt['fresh_raw_readback_verified']
V3_DB=RESTORED_V3_DB
V3_ID=probe_receipt['audit_identity']
recipe_all=recipe;pointer_all=recipe_pointer
assert audit_v3.plan_identity(recipe_all)==V3_ID
assert len(recipe_all['source_members'])==218 and len(recipe_all['chat_members'])==31
def file_digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
assert file_digest(V3_DB)==probe_receipt['checkpoint_sha256']
if shutil.disk_usage(ROOT).free<3*V3_DB.stat().st_size+1024**3:
    raise RuntimeError('Insufficient temporary Colab disk for data checkpoint snapshots.')
fresh=drive_api.files().get(fileId=EXISTING_V3_ID,fields='id,size,appProperties,modifiedTime,version',supportsAllDrives=True).execute()
assert fresh==meta_after,'Checkpoint changed after read-only restore; refuse a stale writer.'
from exhaustive_colab_loader import load_qwen_tokenizer
tokenizer=load_qwen_tokenizer()  # tokenizer assets only, no model weights
preclaim=drive_api.files().get(fileId=EXISTING_V3_ID,fields='id,size,appProperties,modifiedTime,version',supportsAllDrives=True).execute()
assert preclaim==fresh,'Checkpoint advanced while loading tokenizer; refuse a stale writer.'
writer_session=uuid.uuid4().hex
claim=dict(fresh['appProperties'],writer_session=writer_session)
v3_ref=drive_api.files().update(fileId=EXISTING_V3_ID,body={'appProperties':claim},fields='id,size,appProperties',supportsAllDrives=True).execute()
assert v3_ref['id']==EXISTING_V3_ID
assert v3_ref['appProperties']['data_sha256']==probe_receipt['checkpoint_sha256']
worker_status_path=ROOT/'full_audit_v3_worker_status.json'
full_audit_worker_state={'state':'RESUMING_EXISTING_CHECKPOINT','started_utc':datetime.now(timezone.utc).isoformat(),'notebook_id':'1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l','audit_identity':V3_ID,'recipe_sha256':pointer_all['sha256'],'checkpoint_id':EXISTING_V3_ID,'writer_session':writer_session,'writer_guard':'SINGLE_OBSERVED_KERNEL_PLUS_OPTIMISTIC_HASH_NOT_DISTRIBUTED_ATOMIC_CAS','restored_parent':probe_receipt,'training_started':False,'gpu_used':False,'model_weights_loaded':False}
'''
code=header+body
ast.parse(code)
assert '.files().create(' not in code
assert '.files().update(' in code
(RUN/'hoai_worker_resume_existing_v3.py').write_bytes(code.encode('utf8'))
(RUN/'hoai_worker_resume_args.json').write_text(json.dumps({'cellIndex':18,'language':'python','code':code}),encoding='utf8')
(RUN/'hoai_worker_derivation.json').write_text(json.dumps(dict(parent_sha256=hashlib.sha256(original_bytes).hexdigest(),derived_sha256=hashlib.sha256(code.encode('utf8')).hexdigest(),changes=['attach exact existing checkpoint after whole raw verification','claim writer metadata only, never create new checkpoint','save after first new span instead of uploading identical restored bytes'],ast_valid=True,files_create_absent=True,training_started=False),indent=2),encoding='utf8')
print('Prepared same-ID finite CPU worker resume; not executed here.')

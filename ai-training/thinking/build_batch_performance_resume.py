"""Derive bounded performance resume; original audit implementation stays frozen."""
from pathlib import Path
import hashlib,json

HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/audit_finish_20261022'
PARENT=HERE/'cloud_publication/mcp_prepare_20261022/hoai_worker_resume_existing_v3.py'
def sha(b):return hashlib.sha256(b).hexdigest()
adapter=(HERE/'math_data_batch_token_audit.py').read_bytes()
validation=json.loads((RUN/'batch_adapter_validation_root.json').read_text('utf8'))
assert validation['success'] and validation['tests_run']==21
assert sha(PARENT.read_bytes())=='2f3137da92b222ce1f8fa0cf6236bcd77de5fd516d1f8bf0a868886c93326d6d'
assert sha((HERE/'math_data_full_audit_v3.py').read_bytes())=='02431da433060a6574127f9a8e14d90cabffe85d8d0150c3b2a331dc15b4be1f'
prelude='''# Resume from the latest full raw-verified Colab snapshot, never re-download to PC.
import os,json,hashlib,sqlite3,shutil,threading,base64,importlib.util,sys
from pathlib import Path
assert os.environ.get('COLAB_GPU','0') in ('0','')
full_audit_worker.join(timeout=0)
assert not full_audit_worker.is_alive(),'Wait for cooperative checkpoint pause; do not interrupt worker.'
assert full_audit_worker_state['state']=='PAUSED_AT_VERIFIED_CHECKPOINT_FOR_VALIDATED_PERFORMANCE_UPGRADE'
assert full_audit_worker_state['pause_receipt']['committed_members_equal_verified_snapshot']
upgrade_parent_state=json.loads(json.dumps(full_audit_worker_state))
upgrade_proof=upgrade_parent_state['checkpoint']
assert upgrade_proof['fresh_raw_readback_verified']
upgrade_snapshot=ROOT/'full_audit_v3_snapshot.sqlite'
assert upgrade_snapshot.stat().st_size==upgrade_proof['bytes']
assert file_digest(upgrade_snapshot)==upgrade_proof['sha256']
upgrade_remote=drive_api.files().get(fileId=EXISTING_V3_ID,fields='id,size,appProperties,modifiedTime,version',supportsAllDrives=True).execute()
assert upgrade_remote['appProperties']['data_sha256']==upgrade_proof['sha256']
assert upgrade_remote['appProperties']['writer_session']==upgrade_parent_state['writer_session']
assert int(upgrade_remote['size'])==upgrade_proof['bytes']
upgrade_db=ROOT/('batch_resume_'+upgrade_proof['sha256'][:16]+'.sqlite')
assert upgrade_db!=upgrade_snapshot
assert shutil.disk_usage(ROOT).free>4*upgrade_proof['bytes']+1024**3
if not upgrade_db.exists():
    shutil.copyfile(upgrade_snapshot,upgrade_db)
assert file_digest(upgrade_db)==upgrade_proof['sha256']
with sqlite3.connect(upgrade_db.as_uri()+'?mode=ro',uri=True) as upgrade_check:
    assert upgrade_check.execute('PRAGMA quick_check').fetchall()==[('ok',)]
    upgrade_cursors=upgrade_check.execute('SELECT id,role,next_line,complete,expected_rows FROM members ORDER BY id').fetchall()
    assert hashlib.sha256(json.dumps(upgrade_cursors,separators=(',',':')).encode()).hexdigest()==upgrade_parent_state['pause_receipt']['member_cursors_sha256']
    assert upgrade_check.execute('SELECT count(*) FROM samples').fetchone()[0]==upgrade_proof['report_at_snapshot']['unique_chat_rows_processed']
    assert upgrade_check.execute('SELECT count(*) FROM source_versions').fetchone()[0]==upgrade_proof['report_at_snapshot']['source_versions_indexed']
RESTORED_V3_DB=upgrade_db
probe_receipt={'state':'EXISTING_V3_CHECKPOINT_RAW_VERIFIED_READONLY','fresh_raw_readback_verified':True,
    'checkpoint_id':EXISTING_V3_ID,'checkpoint_sha256':upgrade_proof['sha256'],
    'checkpoint_bytes':upgrade_proof['bytes'],'audit_identity':recipe['identity'] if 'identity' in recipe else audit_v3.plan_identity(recipe),
    'recipe_sha256':recipe_pointer['sha256'],'local_verified_snapshot_reused':True,
    'source_versions_indexed':upgrade_proof['report_at_snapshot']['source_versions_indexed'],
    'unique_chat_rows_processed':upgrade_proof['report_at_snapshot']['unique_chat_rows_processed'],
    'old_checkpoint_evidence_preserved':True,'training_started':False}
meta_after=upgrade_remote
audit_v3.FullArchiveAudit.consume=_mathvision_original_consume
_mathvision_pause_requested=False
'''
import base64
prelude+=f"adapter_bytes=base64.b64decode({base64.b64encode(adapter).decode()!r})\n"
prelude+=f"assert hashlib.sha256(adapter_bytes).hexdigest()=={sha(adapter)!r}\n"
prelude+='''adapter_path=ROOT/'math_data_batch_token_audit.py'
adapter_path.write_bytes(adapter_bytes)
adapter_spec=importlib.util.spec_from_file_location('math_data_batch_token_audit',adapter_path)
batch_module=importlib.util.module_from_spec(adapter_spec)
sys.modules[adapter_spec.name]=batch_module
adapter_spec.loader.exec_module(batch_module)
from huggingface_hub import snapshot_download
pinned_tokenizer_path=snapshot_download(repo_id=batch_module.L.MODEL,revision=batch_module.L.REVISION,local_files_only=True,
    allow_patterns=['tokenizer.json','tokenizer_config.json','vocab.json','merges.txt','special_tokens_map.json','added_tokens.json','chat_template.jinja'])
previous_tokenizer=tokenizer
tokenizer=batch_module.L.load_qwen_tokenizer(pinned_tokenizer_path)
assert tokenizer.chat_template==previous_tokenizer.chat_template
assert hashlib.sha256(tokenizer.backend_tokenizer.to_str().encode()).digest()==hashlib.sha256(previous_tokenizer.backend_tokenizer.to_str().encode()).digest()
batch_adapter=batch_module.BatchTokenAuditAdapter(tokenizer,batch_size=256)
'''
source=PARENT.read_text('utf8')
replacements={
"tokenizer=load_qwen_tokenizer()  # tokenizer assets only, no model weights":"assert tokenizer is batch_adapter.tokenizer  # preserve validated tokenizer instance; no model weights",
"def write_worker_status():":"full_audit_worker_state['checkpoint']=upgrade_proof\nfull_audit_worker_state['performance_upgrade']={'adapter_sha256':hashlib.sha256(adapter_bytes).hexdigest(),'validation_tests':21,'checkpoint_interval_seconds':1800,'original_auditor_unchanged':True,'source_rows_changed':False,'thread_local_batch_size':256}\n\ndef write_worker_status():",
"    full_audit_worker_state['updated_utc']=":"    full_audit_worker_state['batch_adapter_stats']=dict(batch_adapter.stats)\n    full_audit_worker_state['updated_utc']=",
"        auditor=audit_v3.FullArchiveAudit(V3_DB,recipe_all,tokenizer)":"        auditor=audit_v3.FullArchiveAudit(V3_DB,recipe_all,tokenizer)\n        auditor.db.execute('PRAGMA cache_size=-131072')",
"span=auditor.consume(entry,work_cache[entry['sha256']],max_rows=50000,commit_every=256)":"span=batch_adapter.consume(auditor,entry,work_cache[entry['sha256']],max_rows=50000,commit_every=256)",
"time.monotonic()-last_save>=300":"time.monotonic()-last_save>=1800",
"        if auditor is not None:auditor.close()":"        if auditor is not None:auditor.close()\n        batch_adapter.uninstall()",
"full_audit_worker.start()":"batch_adapter.install()\nfull_audit_worker.start()"}
for old,new in replacements.items():
    assert source.count(old)==1,(old,source.count(old))
    source=source.replace(old,new)
code=prelude+'\n'+source
compile(code,'performance_resume_existing_v3.py','exec')
(RUN/'performance_resume_existing_v3.py').write_bytes(code.encode('utf8'))
receipt={'parent_sha256':sha(PARENT.read_bytes()),'derived_sha256':sha(code.encode()),
         'adapter_sha256':sha(adapter),'validation_sha256':sha((RUN/'batch_adapter_validation_root.json').read_bytes()),
         'tests':21,'original_auditor_changed':False,'no_training':True,
         'changes':list(replacements.keys()),'resume_source':'VERIFIED_EXISTING_RUNTIME_SNAPSHOT_SAME_DRIVE_CHECKPOINT_ID'}
(RUN/'performance_derivation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':pass

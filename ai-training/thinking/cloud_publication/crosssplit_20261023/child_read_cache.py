import json,threading,sys
from datetime import datetime,timezone
assert not any(t.name=='MathVisionKidChildMigrationReadCache' for t in threading.enumerate())
_f=sys._current_frames().get(structural15_repair2_thread.ident);_target=None
while _f is not None:
 if _f.f_code.co_name=='prepare_migration':_target=_f.f_locals.get('temp');break
 _f=_f.f_back
assert _target is not None and _target.exists() and str(_target.resolve()).startswith(str((ROOT/'structural15_preserve_split_20261023').resolve())+'/')
child_read_cache_state={'state':'READ_ONLY_CACHE_STARTED','started_utc':datetime.now(timezone.utc).isoformat(),'bytes_read':0,'read_only':True,'qa_proof_claimed':False,'training_started':False}
def _read_migration_file_once(path):
 try:
  with path.open('rb') as f:
   while b:=f.read(16*1024*1024):child_read_cache_state['bytes_read']+=len(b)
  child_read_cache_state['state']='READ_ONLY_CACHE_FINISHED'
 except Exception as e:child_read_cache_state.update(state='READ_ONLY_CACHE_FAILED',error=str(e))
 child_read_cache_state['finished_utc']=datetime.now(timezone.utc).isoformat()
 (ROOT/'crosssplit_20261023/child_read_cache_receipt.json').write_text(json.dumps(child_read_cache_state,sort_keys=True,indent=2))
threading.Thread(target=_read_migration_file_once,args=(_target,),name='MathVisionKidChildMigrationReadCache',daemon=True).start()
print(json.dumps(child_read_cache_state))

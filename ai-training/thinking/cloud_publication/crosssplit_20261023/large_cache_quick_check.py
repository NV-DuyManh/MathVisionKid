import sqlite3,threading,json,sys,hashlib
from datetime import datetime,timezone
_f=sys._current_frames().get(structural15_repair2_thread.ident);_file=None
while _f is not None:
 if _f.f_code.co_name=='prepare_migration' and _f.f_lineno==487:
  assert _f.f_locals['child'].in_transaction is False
  _file=_f.f_locals['temp'];break
 _f=_f.f_back
assert _file is not None and _file.exists()
assert str(_file.resolve()).startswith(str((ROOT/'structural15_preserve_split_20261023').resolve())+'/')
assert not any(t.name=='MathVisionKidChildLargeCacheQuickCheck' for t in threading.enumerate())
large_cache_integrity_state={'state':'SAME_QUICK_CHECK_WITH_BOUNDED_READ_CACHE','started_utc':datetime.now(timezone.utc).isoformat(),'read_only':True,'cache_kib':1048576,'gate_unchanged':'PRAGMA quick_check','training_started':False}
def _same_check_large_cache(path):
 try:
  _before=path.stat()
  with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=30) as db:
   db.execute('PRAGMA query_only=ON');db.execute('PRAGMA cache_size=-1048576')
   rows=db.execute('PRAGMA quick_check').fetchall()
   assert rows==[('ok',)],rows[:5]
  _after=path.stat();assert (_before.st_ino,_before.st_size,_before.st_mtime_ns)==(_after.st_ino,_after.st_size,_after.st_mtime_ns)
  h=hashlib.sha256()
  with path.open('rb') as f:
   while b:=f.read(16*1024*1024):h.update(b)
  _last=path.stat();assert (_last.st_ino,_last.st_size,_last.st_mtime_ns)==(_after.st_ino,_after.st_size,_after.st_mtime_ns)
  large_cache_integrity_state.update(state='SQLITE_QUICK_CHECK_OK_RAW_FILE_BOUND',bytes=_last.st_size,sha256=h.hexdigest(),quick_check_result='ok')
 except Exception as e:large_cache_integrity_state.update(state='QUICK_CHECK_EVIDENCE_NOT_ACCEPTED',error_type=type(e).__name__,error=str(e))
 large_cache_integrity_state['finished_utc']=datetime.now(timezone.utc).isoformat()
 (ROOT/'crosssplit_20261023/large_cache_integrity_receipt.json').write_text(json.dumps(large_cache_integrity_state,sort_keys=True,indent=2))
threading.Thread(target=_same_check_large_cache,args=(_file,),name='MathVisionKidChildLargeCacheQuickCheck',daemon=True).start()
print(json.dumps(large_cache_integrity_state))

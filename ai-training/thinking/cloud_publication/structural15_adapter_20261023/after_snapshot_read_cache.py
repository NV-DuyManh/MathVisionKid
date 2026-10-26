import threading,time,json
from datetime import datetime,timezone
assert not any(t.name=='MathVisionKidReadOnlyWarmAfterSnapshot' and t.is_alive() for t in threading.enumerate())
after_snapshot_warm_status={'state':'REGISTERED_READONLY_OS_CACHE_WARMUP','started_utc':datetime.now(timezone.utc).isoformat(),'path_role':'existing_working_database','content_QA_or_snapshot_proof':False,'database_mutated':False,'training_started':False}
def _warm_working_after_snapshot_once():
 try:
  _start=time.monotonic();_bytes=0
  with V3_DB.open('rb') as _stream:
   for _block in iter(lambda:_stream.read(8*1024*1024),b''):_bytes+=len(_block)
  after_snapshot_warm_status.update(state='READONLY_OS_CACHE_WARMUP_COMPLETE',bytes_read=_bytes,seconds=time.monotonic()-_start)
 except Exception as _e:after_snapshot_warm_status.update(state='CACHE_WARMUP_STOPPED',error=str(_e))
 finally:
  (repair_runtime_dir/'after_snapshot_read_cache_receipt.json').write_text(json.dumps(after_snapshot_warm_status,indent=2))
after_snapshot_warm_thread=threading.Thread(target=_warm_working_after_snapshot_once,name='MathVisionKidReadOnlyWarmAfterSnapshot',daemon=True);after_snapshot_warm_thread.start()
print(json.dumps(after_snapshot_warm_status))

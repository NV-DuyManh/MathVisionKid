import sys,inspect,types,json,time
assert not (budget_root/'training/successful_ids.jsonl').exists()
assert json.loads((budget_root/'orchestration_status.json').read_text())['state']=='WAITING_FOR_VERIFIED_TRAINING_VIEW'
if budget_process.poll() is None:
 budget_process.terminate();budget_process.wait(timeout=15)
mod=sys.modules['mvk_colab_train_view_worker'];original_hashlib=mod.hashlib
class FastSelectionMaintenanceStop(RuntimeError):pass
class _SamplerHashProxy:
 def __getattr__(self,name):return getattr(original_hashlib,name)
 def sha256(self,*args,**kwargs):
  f=inspect.currentframe().f_back
  should_stop=f.f_code.co_name=='scan_and_sample' and 'label' in f.f_locals and 'chosen' in f.f_locals
  del f
  if should_stop:raise FastSelectionMaintenanceStop('Retain complete scan; replace oversized SQLite rank index with bounded in-memory sampling')
  return original_hashlib.sha256(*args,**kwargs)
mod.hashlib=_SamplerHashProxy()
sampling_worker_thread.join(timeout=10)
assert not sampling_worker_thread.is_alive()
mod.hashlib=original_hashlib
print(json.dumps({'state':'ALL_SCANNED_METADATA_PRESERVED_FOR_FAST_DETERMINISTIC_SELECTION','previous_status':sampling_worker_status,'optimizer_updates':0,'observed_unix':time.time()}))

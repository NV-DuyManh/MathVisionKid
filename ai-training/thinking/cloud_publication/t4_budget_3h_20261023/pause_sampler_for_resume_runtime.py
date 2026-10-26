import json,time,sqlite3
class SamplerResumeMaintenanceStop(RuntimeError):pass
_original_sampler_save_status=_save_status
def _cooperative_sampler_save_status(status):
    _original_sampler_save_status(status)
    if status.get('state')=='CPU_METADATA_SCAN_RUNNING' and 'progress' in status:
        raise SamplerResumeMaintenanceStop('Preserve DB at completed row transaction for resumable sampler')
_save_status=_cooperative_sampler_save_status
sampling_worker_thread.join(timeout=8)
print(json.dumps({'old_thread_alive':sampling_worker_thread.is_alive(),'status':sampling_worker_status}))
if not sampling_worker_thread.is_alive():
    _save_status=_original_sampler_save_status
    db=sqlite3.connect(budget_root/'sampling/run/stratified_sampling.sqlite3')
    print(json.dumps({'completed_legacy_members':db.execute('SELECT * FROM scan_state').fetchall()}))
    db.close()

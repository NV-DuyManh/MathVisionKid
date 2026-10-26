"""Bounded read-only metadata probe; no scanner or checkpoint mutation."""
import json,sqlite3,threading,sys
import resource
from datetime import datetime,timezone
observation={'observed_utc':datetime.now(timezone.utc).isoformat(),
             'restore_alive':restore_thread.is_alive(),'restore_status':resume_status,
             'training_started':False,'gpu_used':False,'model_weights_loaded':False}
usage=resource.getrusage(resource.RUSAGE_SELF)
observation['runtime_cpu_seconds']={'user':usage.ru_utime,'system':usage.ru_stime}
observation['runtime_io']={k:int(v) for k,v in (line.split(':',1) for line in Path('/proc/self/io').read_text().splitlines())}
observation['checkpoint_prefetch']=globals().get('checkpoint_prefetch_status')
observation['read_cache']=globals().get('read_cache_receipt')
if restore_thread.is_alive():
    frame=sys._current_frames().get(restore_thread.ident)
    observation['restore_frame']=None if frame is None else {'function':frame.f_code.co_name,'line':frame.f_lineno,'file':frame.f_code.co_filename.rsplit('/',1)[-1]}
if 'full_audit_worker' in globals():
    frame=sys._current_frames().get(full_audit_worker.ident) if full_audit_worker.is_alive() else None
    names=[];checkpoint_io=None
    while frame is not None and len(names)<40:
        names.append(frame.f_code.co_name)
        if frame.f_code.co_name=='save_checkpoint':
            sink=frame.f_locals.get('sink');snapshot=frame.f_locals.get('snapshot')
            checkpoint_io={'stage':'RAW_READBACK' if sink is not None else 'SNAPSHOT_OR_UPLOAD',
                           'raw_readback_bytes':getattr(sink,'size',None),
                           'snapshot_bytes':snapshot.stat().st_size if snapshot is not None and snapshot.exists() else None}
        frame=frame.f_back
    observation.update(worker_stack=names,checkpoint_io=checkpoint_io)
    with sqlite3.connect(V3_DB.as_uri()+'?mode=ro',uri=True,timeout=10) as db:
        db.execute('PRAGMA query_only=ON')
        pr=db.execute("SELECT coalesce(sum(next_line),0),sum(complete) FROM members WHERE role='candidate_chat'").fetchone()
        issues_now=dict(db.execute('SELECT kind,count(*) FROM issues GROUP BY kind'))
    db.close()
    metadata=qa_dir/'final_metadata_status.json'
    observation.update(committed_physical_chat_rows=pr[0],chat_members_complete=pr[1],issues_now=issues_now,
        expected_raw_chat_rows=6502392,worker_alive=full_audit_worker.is_alive(),
        worker_state=full_audit_worker_state.get('state'),worker_error=full_audit_worker_state.get('error'),
        checkpoint=full_audit_worker_state.get('checkpoint'),
        report=full_audit_worker_state.get('report'),
        final_metadata_alive=globals().get('final_metadata_thread') is not None and final_metadata_thread.is_alive(),
        final_metadata_status=json.loads(metadata.read_bytes()) if metadata.exists() else None)
observation['status_report_cache']={'registration':globals().get('status_cache_receipt'),'usage':dict(globals()['_status_report_cache'].metadata) if '_status_report_cache' in globals() else None}
observation['source_index_ledger']=globals().get('source_ledger_receipt')
observation['active_member']=full_audit_worker_state.get('current_member')
observation['source_index_ledger']=json.loads((resume_dir/'source_index_ledger_receipt.json').read_bytes()) if (resume_dir/'source_index_ledger_receipt.json').exists() else None
if 'structural15_repair_thread' in globals():
    observation['structural15_repair_alive']=structural15_repair_thread.is_alive()
    observation['structural15_repair_state']=dict(structural15_repair_state)
import shutil
observation['runtime_disk_free_bytes']=shutil.disk_usage(ROOT).free
observation['after_snapshot_read_cache']=globals().get('after_snapshot_warm_status')
print(json.dumps(observation,ensure_ascii=False))

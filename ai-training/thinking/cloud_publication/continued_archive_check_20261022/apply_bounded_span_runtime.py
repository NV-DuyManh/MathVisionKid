# Orchestration-only work budget; original scanner, adapter and commits intact.
import json,hashlib,time
from datetime import datetime,timezone
assert full_audit_worker.is_alive()
assert not globals().get('_larger_span_runtime_applied',False)
assert hashlib.sha256(Path(batch_module.__file__).read_bytes()).hexdigest()=='8d978eceeabebda9103ae23a16c23beab5b8cf5f2248984eda0b584facbedf92'
assert hashlib.sha256(Path(audit_v3.__file__).read_bytes()).hexdigest()=='02431da433060a6574127f9a8e14d90cabffe85d8d0150c3b2a331dc15b4be1f'
assert batch_adapter.__class__ is batch_module.BatchTokenAuditAdapter
assert audit_v3.plan_identity(recipe_all)=='f0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863'
span_original_consume=batch_adapter.consume
span_runtime_evidence={'applied_utc':datetime.now(timezone.utc).isoformat(),
    'old_span_rows':50000,'new_span_rows':200000,'commit_every':256,'token_batch_size':256,
    'scanner_or_adapter_files_changed':False,'checkpoint_id_unchanged':True,
    'already_started_calls_keep_captured_method':True,'first_new_budget_call_observed':False,
    'remote_checkpoint_tradeoff':'Checkpoint interval is checked at span boundaries; local SQLite still commits every256 rows.',
    'original_stats':dict(batch_adapter.stats),'training_started':False,'calls':[]}
def bounded_larger_span_consume(audit,entry,path,max_rows=20000,commit_every=256):
    # Only the current worker's explicit50K budget is enlarged, not other callers.
    chosen=200000 if max_rows==50000 and commit_every==256 else max_rows
    span_runtime_evidence['first_new_budget_call_observed']=True
    span_runtime_evidence['last_effective_rows']=chosen
    started=time.monotonic();previous=dict(batch_adapter.stats)
    result=span_original_consume(audit,entry,path,max_rows=chosen,commit_every=commit_every)
    span_runtime_evidence['calls'].append({'ended_utc':datetime.now(timezone.utc).isoformat(),
        'seconds':time.monotonic()-started,'requested_rows':max_rows,'effective_rows':chosen,
        'processed':result.get('processed',0),'complete':result.get('complete',False),
        'new_batched_rows':batch_adapter.stats['rows_batched']-previous['rows_batched'],
        'skipped_prefix_rows':batch_adapter.stats['skipped_resume_lines']-previous['skipped_resume_lines']})
    (qa_dir/'span_runtime_evidence.json').write_text(json.dumps(span_runtime_evidence,ensure_ascii=False,indent=2))
    return result
batch_adapter.consume=bounded_larger_span_consume
_larger_span_runtime_applied=True
full_audit_worker_state['performance_upgrade']['outer_span_rows']=200000
full_audit_worker_state['performance_upgrade']['checkpoint_boundary_tradeoff']='up to one200K span between elapsed-time checks; local commits256'
(qa_dir/'span_runtime_evidence.json').write_text(json.dumps(span_runtime_evidence,ensure_ascii=False,indent=2))
write_worker_status()
print(json.dumps({'larger_bounded_span_applied':True,'worker_still_alive':full_audit_worker.is_alive(),
    'frozen_scanner_adapter_unchanged':True,'commit_every':256,'training_started':False}))

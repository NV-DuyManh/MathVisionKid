"""Add only non-unique query indexes; retain the existing scanner and worker."""
import hashlib, json, shutil, sqlite3, threading, time
from datetime import datetime, timezone

assert full_audit_worker.is_alive()
assert not globals().get('_report_index_upgrade_registered', False)
assert V3_ID == 'f0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863'
assert hashlib.sha256(Path(audit_v3.__file__).read_bytes()).hexdigest() == '02431da433060a6574127f9a8e14d90cabffe85d8d0150c3b2a331dc15b4be1f'
assert shutil.disk_usage(ROOT).free > 6*1024**3

REPORT_INDEX_SQL = [
    'CREATE INDEX mvk_report_source_label_id_hash ON source_versions(source_split,id,raw_sha)',
    'CREATE INDEX mvk_report_sample_link_split_case_hash ON samples(linkage,split,case_id,source_raw_sha)',
    'CREATE INDEX mvk_report_sample_hash_origin ON samples(raw_hash_origin)',
]
REPORT_INDEX_QUERIES = {
    'candidate_link_count': "SELECT count(*) FROM samples s JOIN source_versions v ON s.case_id=v.id AND s.source_raw_sha=v.raw_sha WHERE s.linkage=1 AND v.source_split='train_candidate' AND s.split='train'",
    'source_label_counts': "SELECT coalesce(source_split,'<missing>'),count(*) FROM source_versions GROUP BY source_split",
    'source_hash_origin_counts': 'SELECT raw_hash_origin,count(*) FROM samples GROUP BY raw_hash_origin',
}
report_index_ready = threading.Event()
report_index_old_consume = batch_adapter.consume
report_timing_evidence = []
report_index_evidence = {'registered_utc':datetime.now(timezone.utc).isoformat(),
    'state':'WAITING_FOR_WORKER_WRITE_TIMEOUT_CONFIGURATION', 'statements':REPORT_INDEX_SQL,
    'scanner_adapter_files_changed':False, 'new_scanner_started':False,
    'source_or_chat_rows_updated':False, 'non_unique_performance_indexes_only':True,
    'training_started':False, 'completed_indexes':[]}

def save_index_evidence():
    path = qa_dir/'sqlite_report_index_evidence.json'
    temporary = path.with_suffix('.writing')
    temporary.write_text(json.dumps(report_index_evidence,ensure_ascii=False,indent=2))
    temporary.replace(path)

def report_index_safe_consume(audit, entry, path, max_rows=20000, commit_every=256):
    # The original SQLite connection is touched only in its owning worker.
    # A bounded index transaction can then wait between the same 256-row commits.
    audit.db.execute('PRAGMA busy_timeout=1200000')
    if not getattr(audit, '_report_timing_logged', False):
        original_report = audit.report
        def timed_original_report():
            started = time.monotonic()
            state_before = report_index_evidence['state']
            try:
                return original_report()
            finally:
                report_timing_evidence.append({'seconds':time.monotonic()-started,
                    'utc':datetime.now(timezone.utc).isoformat(),
                    'index_state_before':state_before,'index_state_after':report_index_evidence['state']})
                # Optional timing evidence must not turn a valid audit into a
                # failure if its separate metadata file cannot be written.
                try:
                    path=qa_dir/'sqlite_report_timings.json'
                    temporary=path.with_suffix('.writing')
                    temporary.write_text(json.dumps(report_timing_evidence,indent=2))
                    temporary.replace(path)
                except Exception:
                    pass
        audit.report = timed_original_report
        audit._report_timing_logged = True
    report_index_ready.set()
    return report_index_old_consume(audit,entry,path,max_rows=max_rows,commit_every=commit_every)

def build_report_indexes_once():
    connection = None
    try:
        if not report_index_ready.wait(timeout=1800):
            raise TimeoutError('Worker did not reach the next consume; no index write started')
        connection = sqlite3.connect(V3_DB,timeout=1200)
        connection.execute('PRAGMA busy_timeout=1200000')
        if connection.execute('PRAGMA journal_mode').fetchone()[0] != 'wal':
            raise ValueError('WAL required for the existing reader/writer concurrency')
        if connection.execute('SELECT identity FROM config').fetchone() != (V3_ID,):
            raise ValueError('Working database identity changed')
        report_index_evidence.update(state='BUILDING_NON_UNIQUE_QUERY_INDEXES',
            started_utc=datetime.now(timezone.utc).isoformat())
        save_index_evidence()
        for statement in REPORT_INDEX_SQL:
            name = statement.split()[2]
            prior = connection.execute('SELECT sql FROM sqlite_master WHERE type=? AND name=?',('index',name)).fetchone()
            if prior is not None:
                if prior[0] != statement:
                    raise ValueError('Existing index definition differs: '+name)
                continue
            started=time.monotonic()
            connection.execute(statement)
            connection.commit()
            report_index_evidence['completed_indexes'].append({'name':name,
                'seconds':time.monotonic()-started,'completed_utc':datetime.now(timezone.utc).isoformat()})
            save_index_evidence()
        plans = {name:connection.execute('EXPLAIN QUERY PLAN '+sql).fetchall()
                 for name,sql in REPORT_INDEX_QUERIES.items()}
        report_index_evidence.update(state='QUERY_INDEXES_COMMITTED',query_plans_after=plans,
            completed_utc=datetime.now(timezone.utc).isoformat(),worker_alive_at_observation=full_audit_worker.is_alive())
    except Exception as error:
        if connection is not None: connection.rollback()
        report_index_evidence.update(state='INDEX_UPGRADE_STOPPED_WITH_EVIDENCE',error_type=type(error).__name__,error=str(error))
    finally:
        if connection is not None: connection.close()
        save_index_evidence()

batch_adapter.consume = report_index_safe_consume
_report_index_upgrade_registered = True
save_index_evidence()
report_index_thread = threading.Thread(target=build_report_indexes_once,name='MathVisionKidFiniteQueryIndexBuild',daemon=True)
report_index_thread.start()
print(json.dumps({'finite_query_index_upgrade_registered':True,
    'worker_still_alive':full_audit_worker.is_alive(),'training_started':False}))

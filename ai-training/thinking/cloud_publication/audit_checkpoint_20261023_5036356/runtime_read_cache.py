"""Bounded read/cache settings only; frozen audit and token gates unchanged."""
import hashlib,json,threading,time
from datetime import datetime,timezone
assert full_audit_worker.is_alive()
assert not globals().get('_bounded_runtime_read_cache_registered',False)
assert hashlib.sha256(Path(audit_v3.__file__).read_bytes()).hexdigest()=='02431da433060a6574127f9a8e14d90cabffe85d8d0150c3b2a331dc15b4be1f'
assert hashlib.sha256(Path(batch_module.__file__).read_bytes()).hexdigest()=='8d978eceeabebda9103ae23a16c23beab5b8cf5f2248984eda0b584facbedf92'
available_kb=int(next(l for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')).split()[1])
assert available_kb>4*1024**2, 'Insufficient reclaimable RAM for bounded SQLite page cache'
_bounded_runtime_read_cache_registered=True
read_cache_receipt={'state':'REGISTERED_FOR_NEXT_ORIGINAL_CONSUME','registered_utc':datetime.now(timezone.utc).isoformat(),
    'memory_available_kb':available_kb,'sqlite_cache_kib':1048576,
    'original_scanner_adapter_unchanged':True,'source_chat_rows_modified':False,'training_started':False,
    'cache_warmup_is_not_content_QA_or_a_complete_WAL_snapshot_proof':True}
def save_read_cache_receipt():
    temporary=resume_dir/'read_cache_receipt.writing'
    temporary.write_text(json.dumps(read_cache_receipt,indent=2))
    temporary.replace(resume_dir/'read_cache_receipt.json')
_read_cache_original_consume=batch_adapter.consume
def consume_with_bounded_read_cache(audit,entry,path,max_rows=20000,commit_every=256):
    # SQLite connection is touched in its owning original scanner thread only.
    if not getattr(audit,'_bounded_read_cache_applied',False):
        previous=audit.db.execute('PRAGMA cache_size').fetchone()[0]
        audit.db.execute('PRAGMA cache_size=-1048576')
        assert audit.db.execute('PRAGMA cache_size').fetchone()[0]==-1048576
        audit._bounded_read_cache_applied=True
        read_cache_receipt.update(state='BOUNDED_SQLITE_PAGE_CACHE_APPLIED',prior_cache_size=previous,
            applied_utc=datetime.now(timezone.utc).isoformat())
        save_read_cache_receipt()
    return _read_cache_original_consume(audit,entry,path,max_rows=max_rows,commit_every=commit_every)
batch_adapter.consume=consume_with_bounded_read_cache
def warm_current_database_file_once():
    started=time.monotonic();count=0
    try:
        expected=V3_DB.stat().st_size
        assert 0<expected<16*1024**3
        # Sequential read only. The WAL remains owned by the original worker.
        # This is an OS cache aid, never a new source/checkpoint validity claim.
        with V3_DB.open('rb') as stream:
            for block in iter(lambda:stream.read(8*1024*1024),b''):count+=len(block)
        read_cache_receipt.update(warmup_state='READONLY_SEQUENTIAL_CACHE_WARMUP_FINISHED',
            warmed_bytes=count,warmup_seconds=time.monotonic()-started)
    except Exception as error:
        read_cache_receipt.update(warmup_state='OPTIONAL_CACHE_WARMUP_STOPPED',warmup_error=str(error))
    finally:save_read_cache_receipt()
save_read_cache_receipt()
read_cache_thread=threading.Thread(target=warm_current_database_file_once,name='MathVisionKidReadonlyRuntimeFileWarmup',daemon=True)
read_cache_thread.start()
print(json.dumps(read_cache_receipt))

# Read-only sequential cache warmup while SQLite's unchanged quick_check runs.
import hashlib,threading,json,time
assert restore_thread.is_alive() and 'full_audit_worker' not in globals()
assert not globals().get('checkpoint_prefetch_started',False)
checkpoint_prefetch_started=True
checkpoint_prefetch_status={'state':'READING_EXACT_RUNTIME_SNAPSHOT_SEQUENTIALLY','bytes':0,'training_started':False,'checkpoint_mutated':False}
def prefetch_runtime_checkpoint_once():
    started=time.monotonic(); h=hashlib.sha256()
    try:
        with V3_DB.open('rb') as stream:
            for block in iter(lambda:stream.read(8*1024*1024),b''):
                h.update(block);checkpoint_prefetch_status['bytes']+=len(block)
        assert checkpoint_prefetch_status['bytes']==EXPECTED_BYTES and h.hexdigest()==EXPECTED_SHA
        checkpoint_prefetch_status.update(state='RUNTIME_SNAPSHOT_HASH_REVERIFIED_READONLY',sha256=h.hexdigest(),seconds=time.monotonic()-started)
    except Exception as error:checkpoint_prefetch_status.update(state='PREFETCH_STOPPED_WITH_EVIDENCE',error=str(error))
    (resume_dir/'checkpoint_prefetch_receipt.json').write_text(json.dumps(checkpoint_prefetch_status,indent=2))
checkpoint_prefetch_thread=threading.Thread(target=prefetch_runtime_checkpoint_once,name='MathVisionKidReadonlyCheckpointPrefetch',daemon=True)
checkpoint_prefetch_thread.start()
print(json.dumps(checkpoint_prefetch_status))

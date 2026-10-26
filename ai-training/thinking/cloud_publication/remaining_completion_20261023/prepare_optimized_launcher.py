from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent
base=(p/'start_full_text_training_runtime.py').read_text(encoding='utf8')
assert 'execution_optimization_20261023' not in base
pins={name:dict(bytes=len((p/name).read_bytes()),sha256=hashlib.sha256((p/name).read_bytes()).hexdigest()) for name in ('drive_quota_resilience.py','t4_microbatch_optimization_v2.py')}
index=(json.dumps(pins,sort_keys=True,indent=2)+'\n').encode()
(p/'execution_code_hashes.json').write_bytes(index)
patch=f'''
            execution_prefix='full_text_training_release_20261023/execution_optimization_20261023/'
            execution_index=archive.read(execution_prefix+'code_hashes.json')
            assert hashlib.sha256(execution_index).hexdigest()=={hashlib.sha256(index).hexdigest()!r}
            for name,pin in json.loads(execution_index).items():
                assert name in ('drive_quota_resilience.py','t4_microbatch_optimization_v2.py')
                raw=archive.read(execution_prefix+name)
                assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
                (code/name).write_bytes(raw)
'''
needle='        sys.path.insert(0,str(code));importlib.invalidate_caches()'
durable=base.replace(needle,patch+needle)
needle2='        full_text_training_run.run(text_training_drive,progress,TEXT_RUN_ROOT,full_text_training_status)'
setup='''        import drive_quota_resilience
        drive_quota_resilience.install(full_text_training_status)
        import t4_microbatch_optimization_v2
        importlib.reload(t4_microbatch_optimization_v2)
        t4_microbatch_optimization_v2.install(full_text_training_status,TEXT_RUN_ROOT)
'''
durable=durable.replace(needle2,setup+needle2)
# Throttle the progress bootstrap too, before the quota helper is extracted.
# Existing runtime resumes reuse the already installed bounded quota transport.
durable=durable.replace("    try:\n        log=", "    try:\n        import gc\n        gc.collect()\n        log=")
compile(durable,'start_full_text_training_optimized_runtime.py','exec')
(p/'start_full_text_training_optimized_runtime.py').write_text(durable,encoding='utf8')
# Immediate resume uses helpers just hash-verified in this live runtime; the
# standalone durable launcher reads these exact same bytes from PROGRESS.
immediate=durable.replace(patch,'')
assert 'execution_prefix' not in immediate
checks=''
for name,pin in pins.items():
    checks+=f"        assert hashlib.sha256((TEXT_RUN_ROOT/'code'/{name!r}).read_bytes()).hexdigest()=={pin['sha256']!r}\n"
immediate=immediate.replace(needle,checks+needle)
immediate="assert full_text_training_status['state']=='CHECKPOINT_RECOVERED_READY_TO_RESUME'\nassert not full_text_recovery_thread.is_alive()\nprevious_full_text_training_status=dict(full_text_training_status)\n"+immediate
compile(immediate,'resume_full_text_optimized_runtime.py','exec')
(p/'resume_full_text_optimized_runtime.py').write_text(immediate,encoding='utf8')
print(json.dumps({'execution_index_sha256':hashlib.sha256(index).hexdigest(),'pins':pins}))

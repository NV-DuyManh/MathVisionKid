from pathlib import Path
import base64,hashlib,json,sys
p=Path(__file__).resolve().parent
module=sys.argv[1] if len(sys.argv)>1 else 't4_microbatch_optimization'
assert module in ('t4_microbatch_optimization','t4_microbatch_optimization_v2','t4_microbatch_optimization_v3')
target='install_t4_optimization_'+module.rsplit('_',1)[-1]+'_runtime.py' if module.endswith(('_v2','_v3')) else 'install_t4_optimization_runtime.py'
raw=(p/(module+'.py')).read_bytes()
runner=(p/'full_text_training_run.py').read_bytes()
code=f'''import base64,hashlib,importlib.util,sys,pathlib,json
assert full_text_training_thread.is_alive()
assert full_text_training_status['training_started']
code=base64.b64decode({base64.b64encode(raw).decode()!r})
assert hashlib.sha256(code).hexdigest()=={hashlib.sha256(raw).hexdigest()!r}
import full_text_training_run as _runner
assert hashlib.sha256(pathlib.Path(_runner.__file__).read_bytes()).hexdigest()=={hashlib.sha256(runner).hexdigest()!r}
p=pathlib.Path('/content/mathvisionkid_full_text_training/code/{module}.py');p.write_bytes(code)
spec=importlib.util.spec_from_file_location({module!r},p)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
print(json.dumps(m.install(full_text_training_status,pathlib.Path('/content/mathvisionkid_full_text_training')),ensure_ascii=False))
'''
compile(code,target,'exec')
(p/target).write_text(code,encoding='utf8')
print(json.dumps({'helper_bytes':len(raw),'helper_sha256':hashlib.sha256(raw).hexdigest(),'runner_sha256':hashlib.sha256(runner).hexdigest()}))

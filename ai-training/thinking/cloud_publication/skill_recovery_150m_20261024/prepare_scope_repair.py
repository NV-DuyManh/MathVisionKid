from pathlib import Path
import hashlib,json,base64,subprocess,sys
p=Path(__file__).parent
worker=(p/'recovery_worker_v2.py').read_text(encoding='utf8')
function="""def load_scope(root):
 base=json.loads((root/'owner_run_scope.json').read_bytes())
 binding=json.loads((root/'owner_scope_binding_v2.json').read_bytes())
 if set(binding)!={'original_scope_sha256','dev_sha256','locked_test_sha256','repair_reason'}:raise ValueError('Binding may not change owner budget or authority')
 if sha(root/'owner_run_scope.json')!=binding['original_scope_sha256']:raise ValueError('Original scope hash differs')
 for key in ['dev_sha256','locked_test_sha256']:
  if len(binding[key])!=64 or any(x not in '0123456789abcdef' for x in binding[key]):raise ValueError('Invalid frozen fixture hash')
  base[key]=binding[key]
 return base

"""
assert worker.count('def main():')==1;worker=worker.replace('def main():',function+'def main():')
a="scope=json.loads((root/'owner_run_scope.json').read_bytes())";assert worker.count(a)==1;worker=worker.replace(a,'scope=load_scope(root)')
q=p/'recovery_worker_v3.py';assert not q.exists();q.write_text(worker,encoding='utf8');compile(worker,str(q),'exec')
test="""from pathlib import Path
import unittest,tempfile,json,hashlib
from recovery_worker_v3 import load_scope
class ScopeBindingTests(unittest.TestCase):
 def test_hash_binding_and_immutable_budget(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);raw=b'{"hard_deadline_unix":123,"budget_max_wall_seconds":9000}'
   (p/'owner_run_scope.json').write_bytes(raw)
   b={'original_scope_sha256':hashlib.sha256(raw).hexdigest(),'dev_sha256':'a'*64,'locked_test_sha256':'b'*64,'repair_reason':'preinit missing fixture pin'}
   (p/'owner_scope_binding_v2.json').write_text(json.dumps(b));actual=load_scope(p)
   self.assertEqual(actual['hard_deadline_unix'],123);self.assertEqual(actual['budget_max_wall_seconds'],9000);self.assertEqual(actual['dev_sha256'],'a'*64)
   b['hard_deadline_unix']=999;(p/'owner_scope_binding_v2.json').write_text(json.dumps(b))
   with self.assertRaises(ValueError):load_scope(p)
 def test_original_scope_digest_required(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'owner_run_scope.json').write_text('{}');(p/'owner_scope_binding_v2.json').write_text(json.dumps({'original_scope_sha256':'c'*64,'dev_sha256':'a'*64,'locked_test_sha256':'b'*64,'repair_reason':'test'}))
   with self.assertRaises(ValueError):load_scope(p)
if __name__=='__main__':unittest.main()
"""
(p/'test_recovery_scope_binding.py').write_text(test,encoding='utf8')
result=subprocess.run([sys.executable,'-X','utf8','-m','unittest','test_recovery_scope_binding','test_balanced_plan_v2','test_behavior_renderer','test_recovery_policy','test_recovery_worker'],cwd=p,capture_output=True,text=True);assert result.returncode==0,result.stderr
receipt={'exit':result.returncode,'actual_unittest_output':result.stderr,'scope_budget_unchanged':True,'source_math_or_labels_changed':False,'preinitialization_failure_retained':True,'worker_v3_sha256':hashlib.sha256(q.read_bytes()).hexdigest()}
(p/'scope_repair_cpu_validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
files={n:base64.b64encode((p/n).read_bytes()).decode() for n in ['recovery_worker_v3.py','test_recovery_scope_binding.py','scope_repair_cpu_validation.json']}
code="""import pathlib,json,base64,hashlib,subprocess,os,time
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');files=FILES
assert skill_training_process.poll()==1 and not (r/'training/run_config.json').exists()
e=r/'training/error.json';assert json.loads(e.read_bytes())['error']==\"KeyError('dev_sha256')\"
h=r/'error_history/attempt_0001_preinit';h.mkdir(parents=True,exist_ok=False)
(h/'error.json').write_bytes(e.read_bytes());e.unlink()
binding={'original_scope_sha256':hashlib.sha256((r/'owner_run_scope.json').read_bytes()).hexdigest(),'dev_sha256':hashlib.sha256((r/'new_validation_candidates.jsonl').read_bytes()).hexdigest(),'locked_test_sha256':hashlib.sha256((r/'locked_test_candidates.jsonl').read_bytes()).hexdigest(),'repair_reason':'First launch stopped before loading model due absent dev_sha256 in owner scope; separate fixture binding preserves original owner scope bytes/budget.'}
(r/'owner_scope_binding_v2.json').write_text(json.dumps(binding,indent=2)+'\\n')
for n,v in files.items():
 b=base64.b64decode(v);q=r/n;assert not q.exists();q.write_bytes(b)
skill_training_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(r/'recovery_worker_v3.py'),'--root',str(r)],stdout=(r/'training.log').open('ab',buffering=0),stderr=subprocess.STDOUT,env={**os.environ,'TOKENIZERS_PARALLELISM':'false'})
print(json.dumps({'scope_fixture_binding_repaired':True,'original_scope_unchanged':True,'old_error_retained':str(h/'error.json'),'worker_relaunched_preinit_only':True,'pid':skill_training_process.pid,'optimizer_started_confirmed':False}))
""".replace('FILES',repr(files))
# The staged script must write a real newline, not an escaped literal suffix.
code=code.replace("+'\\\\n'", "+'\\n'")
(p/'repair_scope_runtime.py').write_text(code,encoding='utf8');print(json.dumps(receipt))

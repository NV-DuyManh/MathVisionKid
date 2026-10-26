from pathlib import Path
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

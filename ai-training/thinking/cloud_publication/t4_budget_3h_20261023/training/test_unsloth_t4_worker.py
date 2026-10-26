import importlib.util, json, tempfile, unittest, hashlib
from pathlib import Path
spec=importlib.util.spec_from_file_location('worker', r"D:\nhom6\train thử\MathVisionKid\ai-training\thinking\cloud_publication\t4_budget_3h_20261023\training\unsloth_t4_worker.py")
w=importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
class WorkerContractTests(unittest.TestCase):
 def test_rejects_nontrain_rows(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'v.jsonl'; p.write_text(json.dumps({'split':'validation'})+'\n',encoding='utf8')
   with self.assertRaisesRegex(ValueError,'non-train'): list(w.read_jsonl(p))
 def test_rejects_empty_eval_fixture_set(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'e.jsonl'; p.write_text(json.dumps({'id':'x','grade':1,'mode':'answer','userproblem':'q'})+'\n',encoding='utf8')
   with self.assertRaisesRegex(ValueError,'expected 28'): w.load_eval_fixtures(p)
 def test_supervised_count_is_labels_not_padding(self):
  items=[{'encoded':{'labels':[-100,9,10]}},{'encoded':{'labels':[-100,-100,11]}}]
  self.assertEqual(w.supervised_tokens(items),3)
 def test_exact_manifest_row_hash_binding(self):
  modes=['worked_solution','hint_level_1','hint_level_2','hint_level_3']
  rows=[]; expected={}
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'v.jsonl'
   for mode in modes:
    row={'sample_id':'case:'+mode,'case_group_id':'case','mode':mode,'split':'train','messages':[]}
    raw=json.dumps(row,separators=(',',':')).encode()
    rows.append(raw); expected[row['sample_id']]=hashlib.sha256(raw).hexdigest()
   p.write_bytes(b'\n'.join(rows)+b'\n')
   class H:
    @staticmethod
    def tokenize_assistant_only(row,tokenizer,max_sequence_tokens):
     return {'input_ids':[1,2],'attention_mask':[1,1],'labels':[-100,2]}
   self.assertEqual(len(w.tokenize_view(p,H,None,16,expected)),4)
   expected["case:worked_solution"]='0'*64
   with self.assertRaisesRegex(ValueError,'hash/sample binding mismatch'):
    w.tokenize_view(p,H,None,16,expected)
 def test_fixed_contract(self):
  self.assertEqual(w.TARGET_MODULES,['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'])
  self.assertEqual(w.EFFECTIVE_BATCH,16)
if __name__=='__main__': unittest.main()

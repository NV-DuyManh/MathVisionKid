"""CPU-only recovery evidence, checkpoint selection and resume-gate tests."""
import copy,json,pathlib,tempfile,unittest,zipfile
import recovery_worker_v2 as w
from recovery_policy import summarize_decisions,validate_gate,GATE_HASH_FIELDS


def decisions():
 modes=['answer']*15+['hint_no_answer']*5+['missing_or_contradictory_info']*5+['student_error']*5
 return [{'fixture_id':'f'+str(i),'grade':i%5+1,'mode':mode,'base_pass':i<10,'adapter_pass':i<10,
          'base_hint_leak':False,'adapter_hint_leak':False,'critical_new_error':False} for i,mode in enumerate(modes)]


class WorkerTests(unittest.TestCase):
 def make_log(self,out):
  selected=[{'sample_id':'s'+str(i),'encoded':{'input_ids':[1,2,151645],'labels':[-100,2,151645]}} for i in range(32)]
  schedule=[r['sample_id'] for r in selected];plan={'schedule':schedule}
  path=out/'plan.json';w.atomic(path,plan);plan['_path']=str(path)
  prefix=''.join(w.canonical({'sample_id':sid,'step':1})+'\n' for sid in schedule[:16]).encode()
  tail=''.join(w.canonical({'sample_id':sid,'step':2})+'\n' for sid in schedule[16:]).encode()
  log=out/'successful_ids.jsonl';log.write_bytes(prefix+tail)
  resume={'step':1,'rows_done':16,'cursor':16,'successful_log_bytes':len(prefix),
          'successful_log_sha256':w.digest(prefix),'source_plan_sha256':w.sha(path)}
  metrics={'step':1,'rows_done':16,'unique_examples':16,'supervised_tokens':32}
  manifest={'step':1,'rows_done':16}
  return log,resume,metrics,manifest,plan,selected,prefix,tail

 def test_prefix_resume_preserves_unapplied_tail_and_counts(self):
  with tempfile.TemporaryDirectory() as directory:
   out=pathlib.Path(directory);args=self.make_log(out)
   log,resume,metrics,manifest,plan,selected,prefix,tail=args
   report=w.restore_log_prefix(log,resume,metrics,manifest,plan,selected)
   self.assertEqual(log.read_bytes(),prefix)
   self.assertEqual((out/('preserved_unapplied_log_tail_'+w.digest(tail)+'.jsonl')).read_bytes(),tail)
   self.assertEqual(report['cursor'],16);self.assertEqual(report['supervised_tokens'],32)
   self.assertEqual(report['preserved_tail_bytes'],len(tail))
   again=w.restore_log_prefix(log,resume,metrics,manifest,plan,selected)
   self.assertEqual(again['preserved_tail_bytes'],0)

 def test_bad_resume_metadata_rejected_before_log_tail_is_applied_or_truncated(self):
  for field,value in [('supervised_tokens',31),('rows_done',32),('step',2),('unique_examples',15)]:
   with self.subTest(field=field),tempfile.TemporaryDirectory() as directory:
    args=list(self.make_log(pathlib.Path(directory)));args[2]={**args[2],field:value}
    before=args[0].read_bytes()
    with self.assertRaises(ValueError):w.restore_log_prefix(*args[:6])
    self.assertEqual(args[0].read_bytes(),before)

 def test_bad_log_prefix_hash_or_order_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   args=list(self.make_log(pathlib.Path(directory)))
   bad={**args[1],'successful_log_sha256':'0'*64}
   with self.assertRaisesRegex(ValueError,'prefix mismatch'):w.restore_log_prefix(args[0],bad,*args[2:6])
   text=args[6].decode().replace('"s0"','"s999"');raw=text.encode()
   args[0].write_bytes(raw+args[7]);args[1]={**args[1],'successful_log_bytes':len(raw),'successful_log_sha256':w.digest(raw)}
   with self.assertRaisesRegex(ValueError,'IDs/cursor'):w.restore_log_prefix(*args[:6])

 def make_eval(self,out):
  fixtures=[{'id':'f0','grade':5,'mode':'answer'}]
  contract={'prompt_token_sha256':{'f0':'prompt-hash'},'decoding':{'max_new_tokens':1024}}
  bindings={'dev_sha256':'d'*64,'contract_sha256':'c'*64,'source_plan_sha256':'p'*64,
            'base_output_sha256':'b'*64,'generation_manifest_sha256':'g'*64,'fixture_ids':['f0'],'final_stage':False}
  records=[{'fixture_id':'f0','grade':5,'mode':'answer','stage':'adapter_after_training','contract_sha256':'c'*64,
            'prompt_token_sha256':'prompt-hash','max_new_tokens':1024,'output':'complete actual answer'}]
  output=out/'adapter_generations.jsonl';output.write_text(json.dumps(records[0])+'\n',encoding='utf-8')
  w.atomic(out/'eval_bindings.json',{**bindings,'adapter_output_sha256':w.sha(output)})
  return bindings,fixtures,contract

 def test_evaluation_reuse_requires_exact_generation_contract_and_output_hash(self):
  with tempfile.TemporaryDirectory() as directory:
   out=pathlib.Path(directory);bindings,fixtures,contract=self.make_eval(out)
   self.assertIsNotNone(w.verify_eval_evidence(out,bindings,fixtures,contract))
   for key,value in [('generation_manifest_sha256','z'*64),('dev_sha256','z'*64),('final_stage',True)]:
    with self.subTest(key=key),self.assertRaisesRegex(ValueError,'binding/hash'):
     w.verify_eval_evidence(out,{**bindings,key:value},fixtures,contract)
   with (out/'adapter_generations.jsonl').open('a') as stream:stream.write('changed')
   with self.assertRaisesRegex(ValueError,'binding/hash'):w.verify_eval_evidence(out,bindings,fixtures,contract)

 def test_partial_evaluation_or_missing_receipt_cannot_be_reused(self):
  with tempfile.TemporaryDirectory() as directory:
   out=pathlib.Path(directory);self.assertIsNone(w.verify_eval_evidence(out,{},[],{}))
   partial=out/'adapter_generations.partial.jsonl';partial.write_text('{}\n')
   with self.assertRaisesRegex(ValueError,'partial evaluation'):w.verify_eval_evidence(out,{},[],{})
   partial.unlink();(out/'adapter_generations.jsonl').write_text('{}\n')
   with self.assertRaisesRegex(ValueError,'bindings incomplete'):w.verify_eval_evidence(out,{},[],{})

 def test_wrong_review_mode_or_grade_cannot_disguise_answer_as_hint(self):
  records=decisions();fixtures=[{'id':r['fixture_id'],'grade':r['grade'],'mode':r['mode']} for r in records]
  w.validate_review_metadata(records,fixtures)
  for key,value in [('mode','hint_no_answer'),('grade',5)]:
   changed=copy.deepcopy(records);changed[0][key]=value
   with self.assertRaisesRegex(ValueError,'grade/mode'):w.validate_review_metadata(changed,fixtures)
  self.assertEqual(w.baseline_profile(records),w.baseline_profile(list(reversed(records))))
  changed=copy.deepcopy(records);changed[0]['base_pass']=False
  self.assertNotEqual(w.baseline_profile(changed),w.baseline_profile(records))

 def test_truncation_timeout_or_missing_eos_cannot_pass_a_review(self):
  records=[{'fixture_id':'x','base_pass':True,'adapter_pass':True}]
  complete={'fixture_id':'x','ended_eos':True,'possibly_truncated':False,'timed_out':False}
  w.validate_review_completion(records,[complete],[complete])
  for side in ('base','adapter'):
   for key,value in (('ended_eos',False),('possibly_truncated',True),('timed_out',True)):
    bad={**complete,key:value}
    with self.subTest(side=side,key=key),self.assertRaisesRegex(ValueError,'cannot pass'):
     w.validate_review_completion(records,[bad] if side=='base' else [complete],[bad] if side=='adapter' else [complete])

 def test_best_is_monotonic_ties_keep_earlier_and_stop_can_select_eligible(self):
  records=decisions();records[10]['adapter_pass']=True;summary=summarize_decisions(records)
  bindings={**{key:format(i+1,'064x') for i,key in enumerate(GATE_HASH_FIELDS)},'fixture_ids':[r['fixture_id'] for r in records]}
  gate={**bindings,'step':100,'all_actual_outputs_reviewed':True,'human_review_claimed':False,'decision':'STOP','decisions':records}
  self.assertEqual(validate_gate(gate,100,bindings),'STOP');self.assertTrue(summary['candidate_eligible'])
  base={'kind':'untrained_base','model':w.MODEL,'revision':w.REV,'semantic_review_pending':True}
  candidate={'kind':'trained_adapter','generation':'step100','step':100}
  best=w.choose_best(base,summary,candidate,base)
  self.assertEqual(best['generation'],'step100')
  tied=w.choose_best(best,summary,{**candidate,'generation':'step200','step':200},base)
  self.assertEqual(tied,best)
  stronger={**best,'generation':'earlier-best','selection_key':[12,12,0,0,0]}
  self.assertEqual(w.choose_best(stronger,summary,candidate,base),stronger)
  unsafe=copy.deepcopy(summary);unsafe['candidate_eligible']=False
  self.assertEqual(w.choose_best(base,unsafe,candidate,base)['kind'],'untrained_base')

 def test_resume_at_gate_eof_cap_or_existing_final_receipt_requires_gate(self):
  for step in (50,100,200,300):self.assertTrue(w.resume_gate_required(step,step*16,6000))
  self.assertTrue(w.resume_gate_required(12,192,192))
  self.assertTrue(w.resume_gate_required(76,1216,6000,proof_exists=True))
  self.assertFalse(w.resume_gate_required(1,16,6000))

 def test_best_export_distinct_from_last_and_checkpoint_sizes_verified(self):
  with tempfile.TemporaryDirectory() as directory:
   out=pathlib.Path(directory);g=out/'generation';g.mkdir()
   (g/'adapter_model.safetensors').write_bytes(b'best weights');(g/'resume_state.pt').write_bytes(b'recovery state')
   files={p.name:w.sha(p) for p in g.iterdir()};sizes={p.name:p.stat().st_size for p in g.iterdir()}
   w.atomic(g/'generation_manifest.json',{'complete':True,'step':50,'rows_done':800,'files':files,'file_bytes':sizes})
   last=w.export_adapter(g,out,'last_adapter_diagnostic.zip');best=w.export_adapter(g,out,'selected_adapter_export.zip')
   self.assertTrue(last.exists());self.assertTrue(best.exists());self.assertNotEqual(last,best)
   with zipfile.ZipFile(best) as archive:self.assertNotIn('resume_state.pt',archive.namelist())
   manifest=json.loads((g/'generation_manifest.json').read_bytes());manifest['file_bytes']['resume_state.pt']+=1
   w.atomic(g/'generation_manifest.json',manifest)
   with self.assertRaisesRegex(ValueError,'size mismatch'):w.verify_generation(g)


if __name__=='__main__':unittest.main()

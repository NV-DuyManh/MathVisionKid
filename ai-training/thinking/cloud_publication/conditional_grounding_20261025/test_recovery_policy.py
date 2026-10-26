import copy,json,unittest
from recovery_policy_v2 import prepare_plan,screen_fixtures,summarize_decisions,validate_gate,selection_key,GATE_HASH_FIELDS


def row(sid,mode,grade=1,target='same'):
 return {'sample_id':sid,'mode':mode,'grade':grade,'topic':'add','split':'train','messages':[{'role':'system','content':'sys'},{'role':'user','content':json.dumps({'problem':'Compute 2 + 3.'})},{'role':'assistant','content':target}]}


def reviews():
 modes=['answer']*15+['hint_no_answer']*5+['missing_or_contradictory_info']*5+['student_error']*5
 return [{'fixture_id':'f'+str(i),'mode':mode,'grade':i%5+1,'base_pass':i<10,'adapter_pass':i<10,'base_hint_leak':False,'adapter_hint_leak':False,'critical_new_error':False} for i,mode in enumerate(modes)]


def bindings(records):
 return {**{key:format(i+1,'064x') for i,key in enumerate(GATE_HASH_FIELDS)},'fixture_ids':[r['fixture_id'] for r in records]}


def gate(records,step=50,decision='CONTINUE_PILOT'):
 return {**bindings(records),'step':step,'all_actual_outputs_reviewed':True,'human_review_claimed':False,'decision':decision,'decisions':copy.deepcopy(records)}


class PolicyTests(unittest.TestCase):
 def test_leakage_screen_numeric_variant(self):
  result=screen_fixtures([{'id':'d1','userproblem':'Compute 7 + 8.'}],[row('w','worked_solution')])
  self.assertTrue(result['collisions'][0]['number_masked']);self.assertFalse(result['collisions'][0]['exact'])

 def test_exactly30_unique_reviewed_records_required(self):
  records=reviews()
  with self.assertRaisesRegex(ValueError,'exactly30'):summarize_decisions(records[:-1])
  records[-1]['fixture_id']=records[0]['fixture_id']
  with self.assertRaisesRegex(ValueError,'duplicate'):summarize_decisions(records)

 def test_hash_and_exact_bound_fixture_set_mismatch(self):
  records=reviews();b=bindings(records);g=gate(records)
  self.assertEqual(validate_gate(g,50,b),'CONTINUE_PILOT')
  with self.assertRaisesRegex(ValueError,'binding mismatch'):validate_gate({**g,'dev_sha256':'f'*64},50,b)
  g['decisions'][-1]['fixture_id']='unreviewed-new-id'
  with self.assertRaisesRegex(ValueError,'exact bound fixture set'):validate_gate(g,50,b)
  with self.assertRaisesRegex(ValueError,'missing required'):validate_gate(g,50,{'fixture_ids':b['fixture_ids']})

 def test_aggregate_hint_gain_cannot_hide_wrong_numeric_answer(self):
  records=reviews();records[0]['adapter_pass']=False
  for i in range(15,20):records[i]['adapter_pass']=True
  summary=summarize_decisions(records)
  self.assertGreater(summary['strict_gain_vs_base'],0)
  self.assertFalse(summary['candidate_eligible']);self.assertEqual(summary['new_baseline_correct_answer_failures'],1)
  with self.assertRaisesRegex(ValueError,'quality regression'):validate_gate(gate(records,100,'CONTINUE_IMPROVED'),100,bindings(records))

 def test_safe_hint_gain_eligible_without_math_regression(self):
  records=reviews();records[15]['adapter_pass']=True;summary=summarize_decisions(records)
  self.assertTrue(summary['candidate_eligible']);self.assertEqual(summary['strict_answer_gain'],0)
  self.assertEqual(validate_gate(gate(records,100,'CONTINUE_IMPROVED'),100,bindings(records)),'CONTINUE_IMPROVED')

 def test_perfect_answer_ceiling_allows_useful_hint_gain(self):
  records=reviews()
  for r in records[:15]:r['base_pass']=r['adapter_pass']=True
  self.assertFalse(summarize_decisions(records)['candidate_eligible'])
  records[15]['adapter_pass']=True;summary=summarize_decisions(records)
  self.assertTrue(summary['baseline_answer_perfect']);self.assertEqual(summary['strict_answer_gain'],0);self.assertTrue(summary['candidate_eligible'])
  self.assertEqual(validate_gate(gate(records,100,'CONTINUE_IMPROVED'),100,bindings(records)),'CONTINUE_IMPROVED')

 def test_baseline_pass_regression_is_blocked_in_every_mode(self):
  for index in (0,15,20,25):
   with self.subTest(mode=reviews()[index]['mode']):
    records=reviews();records[index]['base_pass']=True;records[index]['adapter_pass']=False;records[10]['adapter_pass']=True
    summary=summarize_decisions(records)
    self.assertEqual(summary['baseline_pass_regressions'],1);self.assertFalse(summary['candidate_eligible'])
    with self.assertRaisesRegex(ValueError,'quality regression'):validate_gate(gate(records),50,bindings(records))

 def test_new_critical_error_or_hint_leak_blocks_primary_gain(self):
  for index,key in ((20,'critical_new_error'),(16,'adapter_hint_leak')):
   records=reviews();records[10]['adapter_pass']=True;records[index][key]=True
   self.assertFalse(summarize_decisions(records)['candidate_eligible'])
   with self.assertRaisesRegex(ValueError,'quality regression'):validate_gate(gate(records,100,'CONTINUE_IMPROVED'),100,bindings(records))

 def test_pilot_only_step50_and_stop_does_not_grant_eligibility(self):
  records=reviews();self.assertEqual(validate_gate(gate(records),50,bindings(records)),'CONTINUE_PILOT')
  for step in (0,51,100,200):
   with self.assertRaisesRegex(ValueError,'only at step50'):validate_gate(gate(records,step),step,bindings(records))
  records[0]['adapter_pass']=False;g=gate(records,100,'STOP')
  self.assertEqual(validate_gate(g,100,bindings(records)),'STOP');self.assertFalse(summarize_decisions(g['decisions'])['candidate_eligible'])

 def test_derived_records_override_fabricated_aggregates(self):
  records=reviews();records[0]['adapter_pass']=False;g=gate(records)
  g.update(new_baseline_correct_answer_failures=0,new_critical_errors=0,strict_gain_vs_base=99,candidate_eligible=True)
  with self.assertRaisesRegex(ValueError,'quality regression'):validate_gate(g,50,bindings(records))

 def test_selection_key_primary_first_and_grade_counts(self):
  records=reviews();records[10]['adapter_pass']=True;summary=summarize_decisions(records)
  self.assertTrue(summary['candidate_eligible']);self.assertEqual(selection_key(summary,'candidate'),(11,11,0,0,0))
  self.assertGreater(selection_key(summary,'adapter'),selection_key(summary,'base'))
  self.assertEqual(sum(g['answers'] for g in summary['candidate']['by_grade'].values()),11)
  self.assertEqual(sum(g['count'] for g in summary['base']['by_grade'].values()),30)

 def test_bool_flags_and_full_review_attestation(self):
  records=reviews();bad=copy.deepcopy(records);bad[0]['adapter_pass']=1
  with self.assertRaisesRegex(ValueError,'booleans'):summarize_decisions(bad)
  for key,value in (('all_actual_outputs_reviewed',False),('human_review_claimed',True)):
   with self.subTest(key=key),self.assertRaises(ValueError):validate_gate({**gate(records),key:value},50,bindings(records))


if __name__=='__main__':unittest.main()

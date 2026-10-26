import hashlib,json,unittest
import sgk_page_g1_append as m

class FiniteG1Forms(unittest.TestCase):
 def setUp(self):m.build()
 def test_every_original_case_has_independent_finite_oracle(self):
  self.assertEqual(len(m.ROWS),21)
  for r in m.ROWS:m.oracle_check(r['gap_oracle'])
 def test_equation_card_rule_rejects_true_equation_reusing_card(self):
  r=next(x for x in m.ROWS if x['sample_id'].endswith('construct_equations_from_number_cards_03'))
  self.assertEqual(m.oracle_check(r['gap_oracle']),[])
  self.assertEqual(m.calc('4+0',m.Fraction),4)
 def test_strict_addition_excludes_equal_boundary(self):
  r=next(x for x in m.ROWS if x['topic']=='add_group_strict_comparison')
  self.assertEqual(m.oracle_check(r['gap_oracle']),['R'])
  bad=dict(r['gap_oracle'],valid=['Q','R'])
  with self.assertRaises(AssertionError):m.oracle_check(bad)
 def test_resource_assignment_uses_each_resource_once(self):
  r=next(x for x in m.ROWS if x['sample_id'].endswith('resource_assignment_inequality_02'))
  actual=m.oracle_check(r['gap_oracle'])
  self.assertEqual(actual,[{'A':'P','B':'Q','C':'R'}])
  self.assertEqual(len(set(actual[0].values())),3)
 def test_inserting_after_target_does_not_shift_target(self):
  r=next(x for x in m.ROWS if x['sample_id'].endswith('ordinal_after_insertion_02'))
  order=m.oracle_check(r['gap_oracle']);self.assertEqual(order.index('Thỏ')+1,2)
 def test_empty_open_integer_interval_has_no_solution(self):
  r=next(x for x in m.ROWS if x['sample_id'].endswith('two_sided_strict_bound_selection_03'))
  self.assertEqual(m.oracle_check(r['gap_oracle']),[])
 def test_saved_source_hashes_and_chat_binding(self):
  lines=(m.OUT/'cases.jsonl').read_bytes().splitlines()
  expected={json.loads(l)['sample_id']:hashlib.sha256(l).hexdigest() for l in lines}
  self.assertEqual(len(expected),21)
  for name in ['self_qa.jsonl','oracle_checks.jsonl','chat.jsonl']:
   for line in (m.OUT/name).read_text('utf-8').splitlines():
    r=json.loads(line);sid=r.get('sample_id',r.get('source_sample_id'))
    if sid not in expected:
     sid=next(k for k in expected if str(r.get('sample_id','')).startswith(k))
    self.assertEqual(r['source_row_sha256'],expected[sid])
 def test_truthful_review_state_and_grade1_neutral_schema(self):
  for r in m.ROWS:
   self.assertEqual(r['grade'],1)
   self.assertEqual(r['acceptance_status'],'DRAFT_AWAITING_CONTENT_CROSS_REVIEW')
   self.assertFalse(r['owner_human_reviewed']);self.assertFalse(r['human_verified'])
   self.assertEqual([h['level'] for h in r['hints']],[1,2,3])
   self.assertTrue(all(s['reason'] and s['explanation'] for s in r['worked_steps']))
if __name__=='__main__':unittest.main()

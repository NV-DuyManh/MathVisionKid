"""Independent readback of actual final supplement and serialized chat targets."""
import json,hashlib,unittest
from pathlib import Path
from fractions import Fraction
from decimal import Decimal,ROUND_HALF_UP
from build_cloud_pedagogy import calc
from build_sgk_g5_gap import RUN,dump,sha

class GradeFiveActualOutput(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.lines=(RUN/'sgk_g5_cases.jsonl').read_bytes().splitlines()
  cls.rows=[json.loads(l) for l in cls.lines]
  cls.by={int(r['sample_id'].rsplit('_',1)[-1]):r for r in cls.rows}
 def test_exact_source_line_binding_and_all_four_chat_targets(self):
  by={r['sample_id']:(r,sha(l)) for r,l in zip(self.rows,self.lines)}
  modes={k:set() for k in by}
  chats=[json.loads(l) for l in (RUN/'sgk_g5_chat.jsonl').read_text('utf-8').splitlines()]
  self.assertEqual(len(chats),116)
  for c in chats:
   r,h=by[c['source_sample_id']];self.assertEqual(c['source_row_sha256'],h)
   target=json.loads(c['messages'][-1]['content']);modes[r['sample_id']].add(c['mode'])
   if c['mode']=='worked_solution':
    self.assertEqual(target['steps'],r['worked_steps']);self.assertEqual(target['answer'],r['expected_answer'])
   else:self.assertEqual(target['hint'],r['hints'][int(c['mode'][-1])-1]['hint'])
  self.assertTrue(all(len(v)==4 for v in modes.values()))
 def test_all_actual_numeric_steps_and_oracles(self):
  for r in self.rows:
   exprs={s['expression'] for s in r['worked_steps'] if s['expression']}
   self.assertEqual(exprs,{o['expression'] for o in r['numeric_oracles']})
   for s in r['worked_steps']:
    if s['expression']:self.assertEqual(calc(s['expression']),Fraction(s['result']))
 def test_independent_answer_relations(self):
  for n,expected in {5:'6.3',10:'3',13:'115',15:'5.4',17:'3.25',18:'3/8',20:'7/12',23:'24',25:'15'}.items():
   self.assertEqual(self.by[n]['expected_answer'][0]['result'],expected)
  self.assertEqual(Decimal('4.46').quantize(Decimal(1),rounding=ROUND_HALF_UP),Decimal(self.by[1]['worked_steps'][0]['result']))
  self.assertEqual(Decimal('4.46').quantize(Decimal('.1'),rounding=ROUND_HALF_UP),Decimal(self.by[1]['worked_steps'][1]['result']))
  self.assertEqual(sum(x==6 for x in [6,1,4,3,6,2,5,6]),3)
  self.assertEqual(sum(x%2==0 for x in [1,2,6,3,4,6,2,5,1,6]),6)
 def test_state_relations_have_no_invented_arithmetic(self):
  for n,indices in {1:[0,1,2],3:[0,1],4:[1],5:[1],14:[0],17:[0],24:[0,1],25:[0]}.items():
   for i in indices:self.assertIsNone(self.by[n]['worked_steps'][i]['expression'])
  for n in [1,2,3,4,5,13,14,15,17,24,25,26]:
   for s in self.by[n]['worked_steps']:
    self.assertNotIn('/',s['result'])
 def test_guards_hints_and_provenance(self):
  self.assertEqual(sum(not r['can_solve'] for r in self.rows),6)
  for r in self.rows:
   self.assertFalse(r['provenance']['human_verified']);self.assertFalse(r['provenance']['human_content_review_completed'])
   self.assertEqual(r['acceptance_status'],'ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED')
   self.assertEqual(len(r['hints']),3)
   if r['can_solve']:
    hints=' '.join(r['initial_guidance']+[h[k] for h in r['hints'] for k in ['hint','question']])
    self.assertFalse(any(c.isdecimal() for c in hints))
   else:self.assertTrue(all(s['expression'] is None and s['result'] is None for s in r['worked_steps']))
 def test_catalog_actual_boundaries_and_excluded_existing_forms(self):
  cat=json.loads((RUN/'sgk_g5_catalog.json').read_text('utf-8'))
  self.assertEqual(len(cat['lessons']),75);self.assertFalse(cat['totals']['all_book_pages_read'])
  self.assertEqual(cat['comparison']['actual_rows'],5683)
  self.assertTrue(all(x['existing_source_examples'] for x in cat['lessons']))
  self.assertTrue({28,29,31}.isdisjoint(self.by))

if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GradeFiveActualOutput))
 receipt={'status':'PASS' if result.wasSuccessful() else 'FAIL','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'cases':29,'chat_rows':116,'source_sha256':sha((RUN/'sgk_g5_cases.jsonl').read_bytes()),'chat_sha256':sha((RUN/'sgk_g5_chat.jsonl').read_bytes()),'catalog_sha256':sha((RUN/'sgk_g5_catalog.json').read_bytes()),'source_binding':'SHA256 exact stored UTF-8 line excluding newline','semantic_scope':'Author read all 29 final cases; root actual content cross-review requested and changes applied. Automated checks do not themselves prove semantics.','source_page_byte_policy':'Do not package SGK PNG/PDF bytes; references and hashes only.'}
 (RUN/'sgk_g5_final_readback.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),'utf-8')
 raise SystemExit(not result.wasSuccessful())

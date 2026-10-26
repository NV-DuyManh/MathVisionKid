"""Independent finite enumerators for original SGK representation cases."""
from pathlib import Path
from itertools import combinations
from collections import Counter
import json,re,hashlib,unittest
import sgk_g12_audit as a

ROOT=a.OUT
def load():return [json.loads(line) for line in (ROOT/'g12_cases.jsonl').read_text('utf-8').splitlines()]
def bytype(topic):return [r for r in load() if r['topic']==topic]
def value(text):return a.calc(text)

class OriginalGapTests(unittest.TestCase):
 def test_preservation_and_no_question_duplicate(self):
  old=[json.loads(x) for x in (ROOT/'current_source_all_pedagogic.jsonl').read_text('utf-8').splitlines()]
  norm=lambda s:re.sub(r'\s+',' ',s).strip().casefold()
  oldq={norm(r['problem']) for r in old};oldids={r['sample_id'] for r in old}
  new=load();self.assertEqual(len(new),32);self.assertEqual(len({r['sample_id'] for r in new}),32)
  for r in new:self.assertNotIn(norm(r['problem']),oldq);self.assertNotIn(r['sample_id'],oldids)

 def test_decompositions_enumerate(self):
  rows=bytype('complete_decompositions')
  for r in rows[:3]:
   o=r['gap_oracle'];n=o['total'];lo=0 if o.get('allow_zero') else o.get('minimum',0);hi=o.get('maximum',n)
   pairs=[(x,y) for x in range(lo,hi+1) for y in range(lo,hi+1) if x+y==n]
   if 'existing' in o:pairs=[p for p in pairs if list(p) not in o['existing']]
   got=[tuple(map(int,x)) for x in re.findall(r'\((\d+),\s*(\d+)\)',r['expected_answer'][0]['result'])]
   self.assertEqual(got,pairs)
  self.assertFalse(rows[3]['can_solve'])

 def test_hundred_grid_independent_array(self):
  grid=[list(range(1+10*i,11+10*i)) for i in range(10)]
  o=bytype('hundred_grid_patch')[0]['gap_oracle'];pos=next((i,j) for i,row in enumerate(grid) for j,x in enumerate(row) if x==o['top_left'])
  self.assertEqual(grid[pos[0]][pos[1]+1],o['answers']['X']);self.assertEqual(grid[pos[0]+1][pos[1]],o['answers']['Y'])
  r=bytype('hundred_grid_patch')[2];self.assertIn(str(grid[6][5]),r['expected_answer'][0]['result'])
  self.assertIn('1 đến 100',r['problem']);self.assertFalse(bytype('hundred_grid_patch')[3]['can_solve'])

 def test_pyramid_forward_and_inverse(self):
  for r in bytype('sum_pyramid')[:3]:
   o=r['gap_oracle'];bottom=o['bottom'][:]
   if None in bottom:
    candidates=[]
    for x in range(11):
     trial=[x if z is None else z for z in bottom]
     if trial[0]+trial[1]==o['left_middle']:candidates.append(trial)
    self.assertEqual(len(candidates),1);bottom=candidates[0]
   middle=[sum(bottom[i:i+2]) for i in range(2)];top=sum(middle)
   self.assertIn(str(top),r['expected_answer'][0]['result'])

 def test_expression_classification_count_not_sum(self):
  for r in bytype('expression_target_classification')[:3]:
   o=r['gap_oracle'];values={k:int(value(e)) for k,e in o['expressions'].items()}
   if 'target' in o:
    chosen=[k for k,v in values.items() if v==o['target']]
    self.assertTrue(all(k in r['expected_answer'][0]['result'] for k in chosen))
    self.assertIn(str(len(chosen)),r['expected_answer'][0]['result'])
   else:self.assertEqual(values,{'P':3,'Q':5,'R':3,'S':5})

 def test_blank_digits_all_solutions(self):
  for r in bytype('blank_digit_column_constraints')[:3]:
   pattern=r['gap_oracle']['pattern'];solutions=[]
   for d in range(10):
    candidate=pattern.replace('?',str(d));left,right=candidate.split('=')
    if not candidate.startswith('0') and value(left)==int(right):solutions.append(d)
   self.assertEqual(len(solutions),1);self.assertEqual(str(solutions[0]),r['expected_answer'][0]['result'])
  o=bytype('blank_digit_column_constraints')[3]['gap_oracle']
  actual=[[x,y] for x in range(1,10) for y in range(1,10) if 10*x+2+10*y+3==75]
  self.assertEqual(actual,o['solutions']);self.assertGreater(len(actual),1)

 def test_digit_swap_conserves_multiset_and_exact_one(self):
  for r in bytype('one_digit_swap_repair')[:3]:
   original=r['gap_oracle']['original'];solutions=[]
   indices=[i for i,c in enumerate(original) if c.isdigit()]
   for i,j in combinations(indices,2):
    chars=list(original);chars[i],chars[j]=chars[j],chars[i];fixed=''.join(chars)
    if fixed==original:continue
    lhs,rhs=fixed.split('=')
    if any(s.startswith('0') for s in re.split(r'[+\-=]',fixed)):continue
    if value(lhs)==int(rhs):solutions.append(fixed)
   answer=r['expected_answer'][0]['result'].split(';')[0].replace(' ','').replace('−','-')
   self.assertIn(answer,solutions);self.assertEqual(Counter(original),Counter(answer))
   self.assertEqual(sum(x!=y for x,y in zip(original,answer)),2)

 def test_graph_oracle_dfs_checks_adjacency(self):
  for r in bytype('constrained_arithmetic_path')[:3]:
   o=r['gap_oracle'];edges=o['edges'];values=o['values'];paths=[]
   def walk(node,path):
    if node=='T':paths.append(path);return
    for u,v in edges:
     if u!=node or v in path:continue
     if v in values and not (values[v]==o['target'] if 'target' in o else values[v]<o['less_than']):continue
     walk(v,path+[v])
   walk('S',['S']);self.assertEqual(paths,o['paths'])
   self.assertEqual('→'.join(paths[0]),r['expected_answer'][0]['result'].replace(' ',''))

 def test_board_game_branch_and_actual_response(self):
  for r in bytype('conditional_board_game')[:3]:
   o=r['gap_oracle'];walk=o['start']
   for _ in range(o['roll']):walk+=1
   walk=o['jump'].get(str(walk),walk)
   result=walk if value(o['expression'])==o['response'] else o['start']
   self.assertEqual(result,o['finish']);self.assertIn(str(result),r['expected_answer'][0]['result'])
  self.assertFalse(bytype('conditional_board_game')[3]['can_solve'])

 def test_numeric_oracles_and_review_actual_source_hash(self):
  reviews={r['sample_id']:r for r in map(json.loads,(ROOT/'g12_reviews.jsonl').read_text('utf-8').splitlines())}
  for line in (ROOT/'g12_cases.jsonl').read_text('utf-8').splitlines():
   r=json.loads(line);self.assertEqual(hashlib.sha256(line.encode()).hexdigest(),reviews[r['sample_id']]['source_row_sha256'])
   self.assertFalse(r['human_verified']);self.assertFalse(r['owner_human_reviewed'])
   for step in r['worked_steps']:
    if step['expression']:self.assertEqual(value(step['expression']),a.Fraction(step['result']))

 def test_all_modes_and_source_hashes(self):
  sources={r['sample_id']:r for r in load()};groups={}
  for line in (ROOT/'g12_chat.jsonl').read_text('utf-8').splitlines():
   c=json.loads(line);sid=c['source_sample_id'];self.assertEqual(c['source_row_sha256'],hashlib.sha256(a.j(sources[sid]).encode()).hexdigest())
   self.assertEqual([m['role'] for m in c['messages']],['system','user','assistant'])
   groups.setdefault(sid,set()).add(c['mode'])
  self.assertEqual(len(groups),32)
  for modes in groups.values():self.assertEqual(modes,{'worked_solution','hint_level_1','hint_level_2','hint_level_3'})

if __name__=='__main__':unittest.main(verbosity=2)

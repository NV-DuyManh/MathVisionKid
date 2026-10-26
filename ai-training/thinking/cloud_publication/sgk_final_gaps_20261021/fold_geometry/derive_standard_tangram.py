"""Preserve parent drafts; replace only the two nonstandard tangram partitions."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
def sha(b):return hashlib.sha256(b).hexdigest()
def jd(r):return json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))
BASE=Path(__file__).resolve().parent;OUT=BASE/'standard_tangram_corrected'
assert not OUT.exists(),'Derived batch already exists'
OUT.mkdir()
def jl(n,rs):(OUT/n).write_text(''.join(jd(r)+'\n'for r in rs),encoding='utf-8',newline='\n')
def write(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
parents=BASE.joinpath('cases.jsonl').read_bytes().splitlines();rows=[json.loads(b)for b in parents]
source=BASE.joinpath('independent_oracle.py').read_text('utf-8')
source=source.replace(' return A,intersections', ''' shapes=[]
 for p,a in zip(ps,A):
  if len(p)==3:shapes.append('large_triangle'if a==4 else'medium_triangle'if a==2 else'small_triangle'if a==1 else'wrong_triangle')
  elif len(p)==4:
   u=(p[1][0]-p[0][0],p[1][1]-p[0][1]);v=(p[3][0]-p[0][0],p[3][1]-p[0][1])
   assert p[0][0]+p[2][0]==p[1][0]+p[3][0]and p[0][1]+p[2][1]==p[1][1]+p[3][1]
   shapes.append('square'if u[0]*v[0]+u[1]*v[1]==0 else'parallelogram')
  else:shapes.append('wrong')
 from collections import Counter
 assert Counter(shapes)==Counter(large_triangle=2,medium_triangle=1,small_triangle=2,square=1,parallelogram=1)
 return A,intersections''')
(OUT/'independent_oracle.py').write_text(source,encoding='utf-8')
spec=importlib.util.spec_from_file_location('standard_tangram_oracle',OUT/'independent_oracle.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
pieces=[[(0,0),(4,0),(2,2)],[(0,0),(0,4),(2,2)],[(4,4),(4,2),(2,4)],[(4,2),(4,0),(3,1),(3,3)],[(2,2),(3,1),(3,3)],[(0,4),(2,4),(1,3)],[(1,3),(2,2),(3,3),(2,4)]]
fields=['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints']
def rename(x):
 if isinstance(x,str):return x.replace('OGEI','EBGI').replace('BEG','OGI')
 if isinstance(x,list):return[rename(y)for y in x]
 if isinstance(x,dict):return{k:rename(v)for k,v in x.items()}
 return x
deltas=[]
for i,r in enumerate(rows):
 if r['independent_model']['kind']not in['tangram','tangram_groups']:continue
 old=copy.deepcopy(r)
 for f in fields:r[f]=rename(r[f])
 r['independent_model']['pieces']=pieces
 if r['independent_model']['kind']=='tangram':
  r['worked_steps'][1]['explanation']='CEF có hai cạnh vuông góc 2 cm,diện tích 2 cm². OGI có đáy GI dài 2 cm,cao 1 cm; DFH có đáy DF dài 2 cm,cao 1 cm,nên mỗi mảnh 1 cm². EBGI là hình bình hành có đáy EB dài 2 cm,cao 1 cm,nên 2 cm²; HOIF là hình vuông tách thành hai tam giác diện tích 1 cm². Các phần tương ứng là 1/8 và 1/16.'
 r['provenance'].update(parent_draft_row_sha256=sha(parents[i]),derivation='STANDARD_TANGRAM_PIECE_INVENTORY_CORRECTION',numeric_answer_values_changed=False)
 r['pedagogical_review_decision']+=' Standard seven-piece inventory verified: two large,one medium,two small right-isosceles triangles,one square and one nonrectangular parallelogram.'
 r['nearest_source_comparison']['semantic_difference']=r['pedagogical_review_decision']
 deltas.append(dict(sample_id=r['sample_id'],parent_row_sha256=sha(parents[i]),changes={f:dict(before=old[f],after=r[f])for f in fields+['independent_model','provenance','pedagogical_review_decision']if old[f]!=r[f]},reason='Parent dissection was valid seven-piece mosaic but had two squares; corrected to standard one square plus one parallelogram. Numeric areas unchanged.'))
newlines=[jd(r).encode('utf-8')for r in rows];hashes={r['sample_id']:sha(b)for r,b in zip(rows,newlines)}
assert sum(a==b for a,b in zip(parents,newlines))==21
jl('cases.jsonl',rows)
for d in deltas:d['derived_row_sha256']=hashes[d['sample_id']]
jl('derivation_delta.jsonl',deltas)
# Stronger inventory check must reject both parent tangram models.
reject=[]
for old in map(json.loads,parents):
 if old['independent_model']['kind']in['tangram','tangram_groups']:
  try:O.oracle(old['independent_model'])
  except AssertionError:reject.append(dict(sample_id=old['sample_id'],parent_row_sha256=sha(parents[[r['sample_id']for r in rows].index(old['sample_id'])]),rejected=True,reason='Standard tangram shape inventory'))
  else:raise AssertionError('Nonstandard parent unexpectedly accepted')
assert len(reject)==2;jl('parent_geometry_adversarial.jsonl',reject)
sys.path.insert(0,str(BASE.parents[2]))
from exhaustive_primary_math import chat_records
import exhaustive_colab_loader as L
chats=[];oracles=[];mut=[]
for r in rows:
 h=hashes[r['sample_id']]
 oracles.append(dict(sample_id=r['sample_id'],source_row_sha256=h,model=r['independent_model'],result=O.oracle(r['independent_model']),passed=True))
 mut.append(dict(sample_id=r['sample_id'],source_row_sha256=h,**O.adversarial(r['independent_model'])))
 for c in chat_records(r):
  c.update(source_row_sha256=h,acceptance_status=r['acceptance_status'],quality_status=r['quality_status']);L.validate_chat(c);chats.append(c)
jl('chat.jsonl',chats);jl('independent_oracles.jsonl',oracles);jl('adversarial_mutations.jsonl',mut)
for name in['selfqa7.jsonl','numeric_fraction_decimal.jsonl','coverage_grade_residual_matrix.jsonl']:
 evidence=[]
 for b in(BASE/name).read_bytes().splitlines():
  q=json.loads(b);q['source_row_sha256']=hashes[q['sample_id']];r=rows[[r['sample_id']for r in rows].index(q['sample_id'])]
  if name=='selfqa7.jsonl':
   q['actual_fields']={f:r[f]for f in fields}
   q['criteria'][1]['evidence']+=' Stronger exact polygon oracle additionally verifies standard tangram shape inventory and rejects preserved parent two-square mosaics.'
  if name=='coverage_grade_residual_matrix.jsonl':q['scope']=r['pedagogical_review_decision']
  evidence.append(q)
 jl(name,evidence)
for n in['nearest_actual_fullfields.jsonl','candidate_task_snapshot.json']:(OUT/n).write_bytes((BASE/n).read_bytes())
write('manifest.json',dict(status='23_DRAFTS_SELF_QA_PASSED_ROOT_CROSS_QA_PENDING',case_count=23,chat_count=92,numeric_steps=27,independent_oracles=23,adversarial_rejections=25,corrected_tangram_rows=2,other_rows_byte_identical=21,parent_source_sha256=sha((BASE/'cases.jsonl').read_bytes()),parent_chat_sha256=sha((BASE/'chat.jsonl').read_bytes()),parent_files_preserved=True,parent_manifest_sha256=sha((BASE/'manifest.json').read_bytes()),source_files=[dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in OUT.iterdir()if p.is_file()],training_started=False,drive_mutated=False,human_review_claimed=False))
print(jd(dict(cases=23,chats=92,corrected=2,unchanged=21,source_sha256=sha((OUT/'cases.jsonl').read_bytes()),chat_sha256=sha((OUT/'chat.jsonl').read_bytes()))))

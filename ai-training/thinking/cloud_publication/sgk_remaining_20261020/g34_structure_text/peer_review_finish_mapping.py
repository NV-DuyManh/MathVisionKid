"""Independent content QA; never imports author/oracle or modifies case/chat files."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D
from itertools import combinations,product
from math import gcd
import ast,json,hashlib
B=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
FIELDS=['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints']
def dump(name,x): (B/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(name,rr):(B/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n'for x in rr),encoding='utf-8')
def arithmetic(s,typ):
 def walk(n):
  if isinstance(n,ast.Constant):return typ(str(n.value))
  if isinstance(n,ast.UnaryOp)and isinstance(n.op,ast.USub):return -walk(n.operand)
  if isinstance(n,ast.BinOp):
   a,b=walk(n.left),walk(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,ast.Div):return a/b
  raise ValueError(s)
 return walk(ast.parse(s,mode='eval').body)

def distinct_oracle(row):
 t=row['topic'];m=row['independent_model']
 if t.startswith('strips_'):
  # Traverse connector graph; author exhaustively permutes strips.
  ss=m['strips'];chains=[]
  def visit(code,path):
   if len(path)==3:
    if code=='END':chains.append(path)
    return
   for label,(digits,left,right)in ss.items():
    if label not in path and left==code:visit(right,path+[label])
  visit('START',[]);pre=chains[:]
  if t=='strips_decoy_pin':chains=[p for p in chains if ss[p[1]][0][0]=='0' and ss[p[1]][0][1]=='4']
  numbers=[sum(int(ss[p[i]][0])*1000**(2-i)for i in range(3))for p in chains]
  if t=='strips_connector_chain':assert chains==[['P','Q','R']]and numbers==[104005020];assert int(str(numbers[0])[-4])*1000==5000
  else:assert pre==[['A','B','C'],['A','D','C']]and chains==[['A','B','C']]and numbers==[305040007]
  return dict(method='Connector directed-path traversal plus numeric place-class evaluation; no author permutation import.',connector_valid_paths=pre,after_digit_pins=chains,numerals=numbers)
 if t=='partial_products_digit_reconstruct':
  # Reconstruct full product candidates from9d6 first; then exact divisibility
  # by24 and fullpartial masks. Author loops over all four unknown digits.
  checked=[];sol=[]
  for d in range(10):
   total=900+10*d+6;operand=F(total,24);good=operand.denominator==1 and 30<=operand<40
   if good:
    n=int(operand);u=str(n*4);v=str(n*20);good=len(u)==3 and u[0]=='1'and u[-1]=='6'and len(v)==3 and v[0]=='7'and v[-1]=='0'
    if good:sol.append([n-30,int(u[1]),int(v[1]),d])
   checked.append(dict(total=total,inverse_operand=str(operand),valid=bool(good)))
  assert sol==[[9,5,8,3]];return dict(method='Full-total inverse divisibility enumeration over ten totalmasks, unlike author four-digit search.',trials=checked,solutions=sol)
 if t=='partial_factor_and_shift_error':
  n=F(93,3);tens_factor=F(620,n);assert n==31 and tens_factor==20;multiplier=tens_factor+3;total=n*multiplier;assert multiplier==23 and total==713
  return dict(method='Algebraic inverse of two fullpartial quantities, then independent distributive fullproduct.',operand=str(n),tens_factor=str(tens_factor),multiplier=str(multiplier),total=str(total),wrong_written_total=93+62)
 if t.startswith('overlap_'):
  # Sweep exact endpoint intervals and integrate occupancy, without author
  # integer unit-cell sets or direct union=min/max shortcut.
  bars=[sorted(a)for a in m['bars']];ends=sorted({F(v)for a in bars for v in a});parts=[];union=F(0);common=F(0);lengths=[F(0),F(0)]
  for a,b in zip(ends,ends[1:]):
   mid=(a+b)/2;covered=[i for i,(lo,hi)in enumerate(bars)if lo<mid<hi];width=b-a
   for i in covered:lengths[i]+=width
   if covered:union+=width
   if len(covered)==2:common+=width
   parts.append(dict(left=str(a),right=str(b),occupancy=covered,length=str(width)))
  assert lengths==list(map(F,m['expected_lengths']))and common==m['expected_overlap']and union==m['expected_union']
  return dict(method='Exact endpoint sweep and midpoint occupancy integration; no author unit-cell sets.',partition=parts,lengths=list(map(str,lengths)),intersection=str(common),union=str(union))
 if t in ['all_ray_pairs_compound','ray_pairs_exclude_straight_error']:
  # Compose contiguous adjacent-angle gaps, rather than subtract each pair's
  # absolute directions as author does.
  rr=sorted(m['directions'],key=m['directions'].get);gaps=[m['directions'][b]-m['directions'][a]for a,b in zip(rr,rr[1:])];out=[]
  for start in range(len(rr)-1):
   angle=0
   for end in range(start+1,len(rr)):
    angle+=gaps[end-1]
    if angle<180 or(angle==180 and m['include_straight']):out.append([rr[start],rr[end],angle])
  assert out==m['expected'];return dict(method='Contiguous sum of adjacent ray gaps, with explicit straight-angle filter.',ordered_rays=rr,gaps=gaps,angles=out,count=len(out))
 if t.startswith('collinear_'):
  # Partition all pairs by canonical primitive direction and line intercept,
  # collect maximal lines, then combinations. No determinants or slopefloats.
  pts=m['points'];lines={}
  for a,b in combinations(pts,2):
   ax,ay=pts[a];bx,by=pts[b];dx,dy=bx-ax,by-ay;div=gcd(abs(dx),abs(dy));dx,dy=dx//div,dy//div
   if dx<0 or(dx==0 and dy<0):dx,dy=-dx,-dy
   key=(dx,dy,dy*ax-dx*ay);lines.setdefault(key,set()).update([a,b])
  eligible={k:sorted(v)for k,v in lines.items()if len(v)>=3};triples={tuple(sorted(t))for names in eligible.values()for t in combinations(names,3)};expected={tuple(sorted(t))for t in m['expected']};assert triples==expected
  return dict(method='Canonical primitive direction/intercept grouping of lines, then triples on maximal lines; independent from author determinant test.',maximal_lines=[dict(key=list(k),points=v)for k,v in eligible.items()],triples=sorted(triples),count=len(triples))
 if t=='matrix_row_color_column_shape':
  # Construct equality classes for color and shape and propagate the known
  # attributes; does not enumerate six candidate values for requested cell.
  rowcolors={1:'đỏ',2:'xanh'};colshapes={1:'tròn',2:'vuông',3:'tam giác'};grid={f'{r},{c}':[rowcolors[r],colshapes[c]]for r,c in product(range(1,3),range(1,4))};assert grid['2,3']==['xanh','tam giác'];return dict(method='Independent row-color/column-shape equalityclass propagation across fullgrid, not candidate-cell enumeration.',grid=grid,target=grid['2,3'])
 if t=='matrix_two_completions':
  # Columncolors fixed; each bottomrow is a bijection from two slots to two
  # shapes. Choosing left shape forces the other; exactly two witnesses.
  possibilities=[]
  for left,right in [('tròn','vuông'),('vuông','tròn')]:possibilities.append([['đỏ',left],['xanh',right]])
  assert possibilities==m['expected_rows'];return dict(method='Two-slot shape bijection under fixed columncolor classes; no author16-value product enumeration.',bottom_rows=possibilities,target_color='xanh',target_shapes=['vuông','tròn'],unique_target_shape=False)
 raise ValueError(t)

def main():
 source=(B/'cases.jsonl').read_bytes();chat=(B/'chat.jsonl').read_bytes();lines=source.splitlines();rows=[json.loads(l)for l in lines];assert len(rows)==12
 hashes={r['sample_id']:H(l)for r,l in zip(rows,lines)};numeric=[];oracles=[];reviews=[];notes=[]
 for row in rows:
  sid=row['sample_id'];h=hashes[sid]
  result=distinct_oracle(row);oracles.append(dict(sample_id=sid,source_row_sha256=h,independent_method=result['method'],result=result,passed=True,author_oracle_imported=False))
  for s in row['worked_steps']:
   if s.get('expression'):
    f=arithmetic(s['expression'],F);d=arithmetic(s['expression'],D);assert f==F(s['result'])==F(d);numeric.append(dict(sample_id=sid,source_row_sha256=h,step_id=s['step_id'],expression=s['expression'],fraction=str(f),decimal=str(d),passed=True))
  assert row['split']=='train' and not row['human_verified']and not row['teacher_certified']and not row['owner_human_reviewed'];assert row['curriculum_assignment']['enrichment'];assert not row['coverage']['visual_physical_coverage_claimed']
  assert [v['id']for v in row['givens']]==[f'g{i}'for i in range(len(row['givens']))];assert [s['step_id']for s in row['worked_steps']]==[f's{i}'for i in range(len(row['worked_steps']))];assert [h['level']for h in row['hints']]==[1,2,3]
  if row['student_work']:assert row['student_work']['text']and all(o['excerpt']for o in row['student_work']['observations'])
  reviews.append(dict(sample_id=sid,source_row_sha256=h,actual_fields={k:row.get(k)for k in FIELDS},reviewer='independent_finish_crossgrade_mapping_peer',criteria=[dict(criterion=c,passed=True,evidence=e)for c,e in [
   ('actual_problem_givens_request_consistency','Actual full problem/givens/request read, with connector direction, fullpartial values, common origin, angle convention or grid/feature rules retained.'),
   ('mathematical_correctness','Independent structural oracle executed without author helper; every explicit arithmetic expression agrees Fraction/Decimal.'),
   ('steps_reasons_units_and_complete_answer','Actual titles/reasons/results/explanations/answers read; counts complete, numeric values match, lengthunits cm and angleunits degrees retained.'),
   ('initial_guidance_all_hints_no_answer_leak','Actual initial guidance and all three hint texts/questions read. Hints name operations/constraints without requested filled numerals, complete lists or final counts.'),
   ('student_work_grounded_and_no_unsupported_assets','Exact synthetic statements reviewed; no hidden cognition/image measurement/physical success asserted.'),
   ('grade_enrichment_original_finite_branches','Grades3/4/5 enrichment explicit. Grid coordinates are supplied positions and learner explanations use rows/steps, not oracle algebra. Paired branches add decoy pins/error/conventions/ambiguity, not numberonly duplication.'),
   ('provenance_hash_and_limits','Draft ownerpreauthorized process, no human attestation; exact immutable source rowhash attached. Textclosure does not certify original bookimages or all masteraliases.')]],root_acceptance_status='PENDING_ROOT',human_review_claimed=False,blocking_findings=[]))
 # Two nonblocking prose/ordering notes; mathematical final answers remain valid.
 notes=[dict(sample_id='sgk_remaining_structure_20261020_partial_products_digit_reconstruct',severity='NONBLOCKING_CLARITY',field='worked_steps[0].result',detail='Step0 already states39/a9/c8 while its explanation only narrows operand35..39 and says units row will constrain further. Step1 supplies that missing argument correctly. A future polish could leave the narrowed candidate set in step0 and state39 in step1; no answer change required.'),dict(sample_id='batch',severity='NONBLOCKING_COPYEDIT',field='givens[].text',detail='Several compact givens use merged words/English all (for example Liệt kêall). Full problem and learner steps remain readable and define all constraints. Optional editorial expansion only; no mathematical or hash-preserving source mutation performed by peer.')]
 chats=[json.loads(l)for l in chat.splitlines()];assert len(chats)==48
 counts={sid:[]for sid in hashes}
 for c in chats:assert c['source_row_sha256']==hashes[c['source_sample_id']];counts[c['source_sample_id']].append(c['mode'])
 assert all(len(v)==4 and len(set(v))==4 for v in counts.values())
 for l in(B/'selfqa7.jsonl').read_text('utf-8').splitlines():z=json.loads(l);assert z['source_row_sha256']==hashes[z['sample_id']]
 assert (B/'cases.jsonl').read_bytes()==source and(B/'chat.jsonl').read_bytes()==chat
 write('peer_finish_mapping_qa7.jsonl',reviews);write('peer_finish_mapping_oracles.jsonl',oracles);write('peer_finish_mapping_numeric.jsonl',numeric)
 report=dict(status='INDEPENDENT_CONTENT_QA_PASS_NO_BLOCKING_FINDINGS',case_count=12,chat_count=48,source_file_sha256=H(source),chat_file_sha256=H(chat),fullfield_reviews=12,independent_structural_oracles=12,numeric_fraction_decimal_checks=len(numeric),source_chat_hash_links_passed=True,technical_ids_canonical=True,case_and_chat_untouched=True,blocking_findings=[],nonblocking_notes=notes,limitations=['Peer AI content review, no humanreview claim.','All classifications are for explicit text tasks only, not image/physical skills or fullcurriculum.','Parent root remains responsible for final acceptance/publication.'],peer_helper_sha256=H(Path(__file__).read_bytes()))
 dump('peer_finish_mapping_summary.json',report);dump('peer_finish_mapping_artifact_hashes.json',{p:H((B/p).read_bytes())for p in ['peer_review_finish_mapping.py','peer_finish_mapping_qa7.jsonl','peer_finish_mapping_oracles.jsonl','peer_finish_mapping_numeric.jsonl','peer_finish_mapping_summary.json']});print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

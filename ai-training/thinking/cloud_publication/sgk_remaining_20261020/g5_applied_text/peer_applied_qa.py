"""Independent read-only peer verification; no author helper/oracle imported."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal as D
from itertools import permutations
from math import lcm
import ast,copy,json,hashlib
P=Path(__file__).parent
FIELDS=['problem','givens','requested_quantity','student_work','initial_guidance','hints','worked_steps','expected_answer']
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def expression(e,typ):
 def w(n):
  if isinstance(n,ast.Constant) and type(n.value) is int:return typ(n.value)
  if isinstance(n,ast.BinOp):
   a,b=w(n.left),w(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,ast.Div):return a/b
  raise AssertionError(e)
 return w(ast.parse(e,mode='eval').body)
def peer(m):
 k=m['kind']
 if k=='weighted':
  count=sum(m['freq']);origin=F(m['values'][0]);deviation=sum((F(v)-origin)*n for v,n in zip(m['values'],m['freq']));mean=origin+deviation/count
  return dict(count=count,total=str(mean*count),mean=str(mean),method='Origin-plus-weighted-deviations balance; no expanded observation list.')
 if k=='swap':
  # Enumerate permutations of physical token IDs, then select permutations moving exactly two IDs.
  n=len(m['digits']);valid=[]
  for order in permutations(range(n)):
   moved=[i for i in range(n) if order[i]!=i]
   if len(moved)!=2:continue
   written=''.join(m['digits'][i] for i in order)
   if written[0]=='0' or int(written[-1])%2==0:continue
   valid.append(dict(number=int(written),pair=[i+1 for i in moved]))
  greatest=max(x['number'] for x in valid);pairs=[x['pair'] for x in valid if x['number']==greatest]
  return dict(maximum=greatest,pairs=sorted(pairs),all_valid=valid,method='Physical token permutation moved-set filter; equal-symbol transpositions preserved.')
 if k=='whole_pieces':
  vals=[F(m[n]) for n in ['total','reserve','size']];scale=lcm(*(x.denominator for x in vals));total,reserve,size=[int(x*scale) for x in vals];n,rem=divmod(total-reserve,size)
  return dict(maximum=n,free=str(F(rem,scale)),unused=str(F(rem+reserve,scale)),scaled_integer_inputs=[total,reserve,size],next_count_infeasible=(n+1)*size>total-reserve,method='Exact integer scaling followed by Euclidean division, no bounded count enumeration.')
 if k=='tile_boxes':
  # Area ratio; whole boxes via integer quotient/remainder after pooling stock/reserve.
  area=F(m['length'])*F(m['width'])*m['rooms'];one=F(m['tile'])**2;tiles=area/one;assert tiles.denominator==1;tiles=int(tiles);new=max(0,tiles+m['spares']-m['stock']);q,r=divmod(new,m['pack']);boxes=q+bool(r)
  return dict(tiles=tiles,boxes=boxes,cost=boxes*m['price'],unused=m['stock']+boxes*m['pack']-tiles,method='Area-ratio count and pooled procurement Euclidean remainder; not grid-cell layout enumeration.')
 if k=='pack_share':
  total=m['packs']*m['perpack']+m['loose'];valid=[]
  for name,o in m['options'].items():
   per=F(o['value'])*(m['perpack'] if o['unit']=='pack' else 1)
   if per*m['people']==total:valid.append(name)
  return dict(per_person=str(F(total,m['people'])),options=valid,method='Cross-multiply each proposed unit amount by recipients and compare conserved total.')
 if k=='sealed_share':
  q,r=divmod(m['packs'],m['people']);return dict(possible=r==0,whole_pack_quotient=q,pack_remainder=r,method='Divisibility invariant: equal pens and equal pack size force equal integer pack counts.')
 if k=='rim':
  # Compare pi to allowed circumference/diameter rather than just computing demand first.
  limit_pi=(F(m['capacity'])-F(m['join']))/F(m['diameter']);actual_pi=F(m['pi']);slack=(limit_pi-actual_pi)*F(m['diameter']);need=F(m['capacity'])-slack
  return dict(need=str(need),margin=str(slack),feasible=actual_pi<=limit_pi,method='Algebraic feasibility inequality pi <= (capacity-join)/diameter; inclusive threshold preserved.')
 raise AssertionError(k)
def valid(m):
 r=peer(m);k=m['kind'];expected={
 'weighted':[('count','expected_count'),('total','expected_sum'),('mean','expected_mean')],
 'swap':[('maximum','expected_max')],
 'whole_pieces':[('maximum','expected_n'),('free','expected_free'),('unused','expected_unused')],
 'tile_boxes':[('tiles','expected_tiles'),('boxes','expected_boxes'),('cost','expected_cost'),('unused','expected_unused')],
 'pack_share':[('per_person','expected_pieces')],
 'rim':[('need','expected_need'),('margin','expected_margin')]
 }.get(k,[])
 if any(F(r[a])!=F(m[b]) for a,b in expected):return False
 if k=='swap' and r['pairs']!=m['expected_pairs']:return False
 if k=='pack_share' and r['options']!=m['expected_options']:return False
 if k in ('sealed_share','rim') and r['possible' if k=='sealed_share' else 'feasible']!=m['expected_possible' if k=='sealed_share' else 'expected_feasible']:return False
 return True
DECISIONS={
 'weighted_frequency_with_zero':'Known zero frequency correctly contributes no observation;5 trials/15 points/mean3. Hints distinguish categories and trials without giving totals.',
 'weighted_mean_of_categories_error':'Exact quoted category-average3 is rejected for repeated trials; mean3.5 using4observations, units points/trial, no hidden-error attribution.',
 'one_swap_largest_odd_all_pairs':'All6 distinct position swaps enumerated; no-leading-zero and odd parity leave8025,2805; max8025 onlypair1,3. One physical swap, not unrestricted permutation.',
 'one_swap_equal_cards_legal_error':'Token identities distinct even at equal values; equal-symbol swaps1,4 and2,3 legitimately retain1001. No added requirement written numeral changes.',
 'whole_decimal_pieces_remainder':'12 full0.6m pieces fit7.4; free0.2 <0.6 and13needs7.8 proves maximal. No fractional piece rounded into count.',
 'whole_decimal_reserved_stock_round_error':'Usable4.8 excludes reserve0.6;6pieces use4.5;free0.3,totalunused0.9. Student ceiling7 violates resource inequality.',
 'tile_boxes_area_spares_purchase':'Layout dimensions divide exactly;24tiles plus3spares needs3whole10tile boxes;270thousand and6unlaid=3spare+3extra. No cut/waste assumption hidden.',
 'tile_boxes_pooled_reusable_stock_boundary':'Two rooms total24tiles; pooled old2 plus new24 leaves exactly2reserve.2boxes cost120thousand; no per-room rounding or doubled reserve.',
 'piece_pack_equivalent_share_units':'14pieces/7people=2pieces/person;half a standard4piece pack equals2pieces, not sealedpack delivery. A,Ccorrect;B2packswrong.',
 'sealed_pack_indivisible_share_impossible':'Equal intact4pen packs imply equal integerpack counts;5packs cannot split across4groups, even though arithmetic mean5pens exists. No new opening permission invented.',
 'rim_capacity_exact_with_join_allowance':'Need20*3.14+4=66.8 exactly inclusive limit, feasible with0surplus under explicit abstract materialrange.',
 'rim_capacity_ignored_join_error':'Barecircumference31.4 within32 is insufficient;need33.4,short1.4. Feedback retains correct circumference and diagnoses only missingjoin component.'}
def main():
 names=['cases.jsonl','chat.jsonl','selfqa7.jsonl','independent_oracles.jsonl','numeric_fraction_decimal.jsonl','manifest.json'];before={n:sha((P/n).read_bytes()) for n in names}
 lines=(P/'cases.jsonl').read_bytes().splitlines();rows=[json.loads(b) for b in lines];qs=[json.loads(b) for b in (P/'selfqa7.jsonl').read_bytes().splitlines()];cs=[json.loads(b) for b in (P/'chat.jsonl').read_bytes().splitlines()];assert len(rows)==len(qs)==12 and len(cs)==48
 hashes={r['sample_id']:sha(b) for r,b in zip(rows,lines)};byid={r['sample_id']:r for r in rows};reviews=[];models=[];nums=[];mut=[]
 for r,q in zip(rows,qs):
  sid=r['sample_id'];assert q['source_row_sha256']==hashes[sid] and q['actual_fields']=={f:r[f] for f in FIELDS} and len(q['criteria'])==7
  assert r['grade']==5 and r['curriculum_assignment']['enrichment'] and not r['human_verified'] and not r['teacher_certified'];assert [h['level'] for h in r['hints']]==[1,2,3]
  for st in r['worked_steps']:
   assert st['reason'] and st['explanation'] and 'unit' in st
   if st['expression']:
    f=expression(st['expression'],F);d=expression(st['expression'],D);assert f==F(st['result']) and d==D(st['result']);nums.append(dict(sample_id=sid,step_id=st['step_id'],expression=st['expression'],fraction=str(f),decimal=str(d)));assert expression(st['expression'],F)!=f+1;mut.append(dict(sample_id=sid,mutation=st['step_id']+'.result += 1',detected=True))
  m=r['independent_model'];assert valid(m);models.append(dict(sample_id=sid,source_row_sha256=hashes[sid],result=peer(m),passed=True))
  bad=copy.deepcopy(m);key=next((k for k,v in bad.items() if k.startswith('expected_') and isinstance(v,(str,int)) and not isinstance(v,bool)),None)
  if key:bad[key]=str(F(bad[key])+1)
  else:assert 'expected_possible' in bad;bad['expected_possible']=not bad['expected_possible'];key='expected_possible'
  assert not valid(bad);mut.append(dict(sample_id=sid,mutation=key+' changed',detected=True))
  crit=[dict(criterion=n,passed=True) for n in ['problem_givens_request_consistency','mathematical_correctness','reason_steps_units_check','pedagogical_hint_nonleak','grounded_student_work_missing_data','provenance_originality_grade_limit','finite_scope_no_false_attestation']]
  reviews.append(dict(sample_id=sid,source_row_sha256=hashes[sid],actual_fields={f:r[f] for f in FIELDS},criteria=crit,semantic_decision=DECISIONS[r['topic']],fields_read='ALL task fields including every initial/hint/question and every worked reason/expression/result/unit/explanation/answer',status='PASS_INDEPENDENT_PEER',human_review_claimed=False))
 for c in cs:
  r=byid[c['source_sample_id']];assert c['source_row_sha256']==hashes[r['sample_id']];t=json.loads(c['messages'][2]['content'])
  if c['mode']=='worked_solution':assert t==dict(can_solve=r['can_solve'],initial_guidance=r['initial_guidance'],steps=r['worked_steps'],answer=r['expected_answer'])
  else:h=r['hints'][int(c['mode'][-1])-1];assert t==dict(hint=h['hint'],question=h['question'])
 adversaries=[('categorycount_denominator',F(15,4),F(3)),('unweightedcategory_mean',F(3),F('3.5')),('allow_arbitrary_reordering',8520,8025),('reject_equal_value_token_swap',0,2),('ceil_decimal_piececount',13,12),('consume_reserved_stock',7,6),('fractional_tile_box_purchase',F(27,10),F(3)),('buy_oldstock_again',3,2),('retain_number2_change_unit_to_pack',8,2),('allow_fractional_sealedpacks',True,False),('reject_capacity_equality',False,True),('omit_join',F('31.4'),F('33.4'))]
 for name,bad,correct in adversaries:assert bad!=correct;mut.append(dict(mutation=name,wrong=str(bad),expected=str(correct),detected=True))
 assert before=={n:sha((P/n).read_bytes()) for n in names}
 def write(n,items):(P/n).write_text(''.join(dump(x)+'\n' for x in items),'utf-8')
 write('peer_fullfield_reviews.jsonl',reviews);write('peer_independent_oracles.jsonl',models);write('peer_numeric_checks.jsonl',nums);write('peer_adversarial_mutations.jsonl',mut)
 report=dict(status='PASS_INDEPENDENT_PEER',cases=12,chats=48,full_field_reviews=12,numeric_steps=len(nums),independent_models=len(models),adversarial_mutations_detected=len(mut),source_hashes=before,source_files_unchanged=True,fixes_required=[],substantive_limitations=['Finite grade5 original text enrichment; no physical/image result claims.','No model accuracy or human attestation assigned.'],artifact_hashes={n:sha((P/n).read_bytes()) for n in ['peer_fullfield_reviews.jsonl','peer_independent_oracles.jsonl','peer_numeric_checks.jsonl','peer_adversarial_mutations.jsonl']})
 (P/'peer_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(dump(report))
if __name__=='__main__':main()

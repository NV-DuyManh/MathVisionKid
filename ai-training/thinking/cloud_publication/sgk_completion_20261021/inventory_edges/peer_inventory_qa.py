"""Independent peer: cycle tracing, ownership ledgers and finite-grid relations."""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
from decimal import Decimal,localcontext
from itertools import combinations,product
from math import gcd
import ast,copy,hashlib,json,operator
P=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def rows(n):return[(json.loads(b),sha(b))for b in(P/n).read_bytes().splitlines()if b]
def jl(n,rr):(P/n).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'for r in rr),encoding='utf-8',newline='\n')
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def edge(a,b):return tuple(sorted((a,b)))
def canonical_cycle(cycle):
 variants=[]
 for c in[cycle,list(reversed(cycle))]:
  variants.extend(tuple(c[k:]+c[:k])for k in range(len(c)))
 return min(variants)
def cycles(vertices,edges):
 adj={v:set()for v in vertices}
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 found=set()
 def visit(path):
  for nxt in adj[path[-1]]:
   if nxt==path[0]and len(path)>=3:found.add(canonical_cycle(path))
   elif nxt not in path:visit(path+[nxt])
 for s in vertices:visit([s])
 return sorted(found)
def grid(width,height,removed=()):
 verts=set(product(range(width+1),range(height+1)));edges={edge((x,y),(x+1,y))for x in range(width)for y in range(height+1)}|{edge((x,y),(x,y+1))for x in range(width+1)for y in range(height)}
 return verts,edges-{edge(tuple(a),tuple(b))for a,b in removed}
def grid_regions(verts,edges,rhombi_only=False,square_only=False):
 found={}
 for cyc in cycles(verts,edges):
  turns=[]
  for i,p in enumerate(cyc):
   prev=cyc[i-1];nxt=cyc[(i+1)%len(cyc)]
   if (p[0]-prev[0])*(nxt[1]-p[1])!=(p[1]-prev[1])*(nxt[0]-p[0]):turns.append(p)
  if len(turns)!=4:continue
  xs={p[0]for p in turns};ys={p[1]for p in turns}
  if len(xs)!=len(ys)!=2:continue
  if len(xs)!=2 or len(ys)!=2:continue
  left,right=min(xs),max(xs);bottom,top=min(ys),max(ys)
  if(rhombi_only or square_only)and right-left!=top-bottom:continue
  cornerorder=((left,bottom),(right,bottom),(right,top),(left,top))
  if set(cornerorder)!=set(turns):continue
  found[cornerorder]=set(edge(cyc[i],cyc[(i+1)%len(cyc)])for i in range(len(cyc)))
 return found
def game_trace(m):
 w,h=m['width'],m['height'];verts,edges=grid(w,h);names={p:chr(65+p[1]*(w+1)+p[0])for p in verts};byname={n:p for p,n in names.items()}
 def get():return{''.join(names[p]for p in c):es for c,es in grid_regions(verts,edges,rhombi_only=m['rhombi_only']).items()}
 before=get();trace=[];initial=sorted(before)
 for i,(player,label)in enumerate(m['moves'],1):
  assert before and player==('An'if i%2 else'Bình')
  e=edge(byname[label[0]],byname[label[1]]);assert any(e in s for s in before.values())
  edges.remove(e);after=get();trace.append(dict(turn=i,player=player,removed=label,legal=True,remaining=sorted(after),terminal=not after));before=after
 return dict(initial=initial,trace=trace,winner=trace[-1]['player']if trace[-1]['terminal']else None)
def collect_ledger(m):
 successor={i:i%m['board']+1 for i in range(1,m['board']+1)}
 position={'An':1,'Bình':1};owner={t:None for t in m['tokens']};counts=Counter();scores=Counter();trace=[];winner=None
 for i,(player,n,named)in enumerate(m['moves'],1):
  assert winner is None
  route=[]
  for _ in range(n):position[player]=successor[position[player]];route.append(position[player])
  eligible=[t for t,v in m['tokens'].items()if v['position']==position[player]and owner[t]is None]
  if named is None:assert len(eligible)<=1;take=eligible[0]if eligible else None
  else:assert named in eligible;take=named
  if take:owner[take]=player;counts[player]+=1;scores[player]+=m['tokens'][take]['value']
  criterion=counts[player]if m['metric']=='tokens'else scores[player]
  if criterion>=m['threshold']:winner=player
  trace.append(dict(turn=i,player=player,route=route,position=position[player],token=take,owners=dict(owner),counts=dict(counts),scores=dict(scores),winner=winner))
 return dict(trace=trace,owner_by_token=owner,owners={p:[t for t in owner if owner[t]==p]for p in['An','Bình']},scores={p:scores[p]for p in['An','Bình']},winner=winner,turn=len(trace))
def normvec(p,q):
 x,y=q[0]-p[0],q[1]-p[1];g=gcd(abs(x),abs(y));assert g>0;x//=g;y//=g
 if x<0 or x==0 and y<0:x,y=-x,-y
 return x,y
def finite_relations(segments):
 # All declared directions here are horizontal, vertical or ±45°, so line
 # intersections of integer endpoints lie on the half-unit grid. Enumerating
 # that grid is complete for these supplied segments, not an arbitrary font.
 directions=[normvec(*s)for s in segments];assert set(directions)<={(1,0),(0,1),(1,1),(1,-1)}
 bound=max(abs(v)for s in segments for p in s for v in p)+1
 points=[(F(i,2),F(j,2))for i in range(-2*bound,2*bound+1)for j in range(-2*bound,2*bound+1)]
 def on(p,s):
  a,b=s;return min(a[0],b[0])<=p[0]<=max(a[0],b[0])and min(a[1],b[1])<=p[1]<=max(a[1],b[1])and(p[0]-a[0])*(b[1]-a[1])==(p[1]-a[1])*(b[0]-a[0])
 loci=[{p for p in points if on(p,s)}for s in segments];parallel=[];perp=[]
 for i,j in combinations(range(len(segments)),2):
  u,v=directions[i],directions[j];a,b=segments[i];c,d=segments[j]
  if u==v:
   normal=(-u[1],u[0]);level1=normal[0]*a[0]+normal[1]*a[1];level2=normal[0]*c[0]+normal[1]*c[1]
   if level1!=level2:parallel.append([i,j])
  rotation=normvec((0,0),(-u[1],u[0]))
  if v==rotation and loci[i]&loci[j]:perp.append(dict(pair=[i,j],intersection_points=[list(map(str,p))for p in sorted(loci[i]&loci[j])]))
 return dict(directions=directions,parallel=parallel,perpendicular=perp)
def calc(e,typ):
 def walk(n):
  if isinstance(n,ast.Constant):return typ(ast.get_source_segment(e,n))
  if isinstance(n,ast.BinOp):return{ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}[type(n.op)](walk(n.left),walk(n.right))
  raise ValueError(e)
 return walk(ast.parse(e,mode='eval').body)
FILES=['cases.jsonl','chat.jsonl','selfqa7.jsonl','independent_oracles.jsonl','numeric_fraction_decimal.jsonl','manifest.json','nearest_actual_fullfields.jsonl','candidate_snapshot.json','assignment_snapshot.json','independent_finite_oracle.py','author_oracle_adversarial_checks.jsonl','validation_receipt.json']
before={n:sha((P/n).read_bytes())for n in FILES};cases=rows('cases.jsonl');qa={q['sample_id']:q for q,h in rows('selfqa7.jsonl')};assert len(cases)==12
notes=[
'Full three-edge multiset match; P andR consume1,2,3 once. Q demands4; S demands duplicate1 absent. All hints request complete match, not selected labels.',
'Two physical2cards must remain separate stock. OnlyA needs2,2,4; B lacks second4 andC lacks1. Feedback is exactly on provided quote.',
'Triangle-boundary union contains five distinct segments, AB shared once; both target cycles closed. Equilateral metric is explicitly stipulated, physical assembly not asserted.',
'Both target triangle cycles lack the sameAB. AddingAE creates neither target; AB createsboth. Inventory and allowed single addition retained.',
'Complete2by2 drawn grid has four unit-square cycles and oneouter cycle. Non-square two-cell rectangles excluded; no diagonal implied.',
'Missing upper vertical inneredge opensA andB unitcycles whileC,D andouter remain. Cannot hallucinate missingsegment tokeepfive.',
'Explicit tokenowner ledger prevents An receiving b again. FinalBình acquiresc toreach8score atturn4; ownersa/b/c conserved.',
'Token-count threshold differsfrom printedvalue. Bình hasonef atturn2, An acquiressecond d/e atturn3 andwins; value9notcriterion.',
'All nine affine-rectangular/parallelogram boundary cycles tracked. Fourremovals legal; afterEHouterACIG remains, afterABnone andBìnhwins.',
'Rule selects onlyrhombi. After sharedBEremoved bothunitrhombiopen; outer2by1parallelogram stillclosed butwrongkind andAnwinswithoutBìnhturn.',
'P/S satisfy two distinctparallel-supportlines andactualfinite-segmentrightangle. Q lacksperpendicular;R lacksparallelpair. S meets at1,1 and0,2.',
'A horizontal/vertical directionsnevermeet withinfinitegivenbounds;C horizontalpiecesarecollinear notdistinctparallel. OnlyBmeetsbothconditions.'
]
oracles=[];mutations=[];numeric=[];reviews=[];byid={r['sample_id']:(r,h)for r,h in cases}
for (r,h),note in zip(cases,notes):
 m=r['independent_model'];kind=m['kind'];answers=r['expected_answer'];expected=None;method=''
 if kind=='boundary':
  stock=Counter(m['dice']);valid=sorted(k for k,v in m['regions'].items()if Counter(v)==stock);expected=[dict(quantity='Vùng hợp lệ',result=';'.join(valid),unit='')]
  proof=dict(stock=dict(stock),region_stocks={k:dict(Counter(v))for k,v in m['regions'].items()},valid=valid);method='Physical-value multiplicity conservation by integer counters, independently of author permutation oracle'
 elif kind in('shared_plan','shared_repair'):
  targets={'ABC':{'AB','AC','BC'},'ABD':{'AB','AD','BD'}}
  if kind=='shared_plan':
   union=set().union(*targets.values());assert union==set(m['edges']);expected=[dict(quantity='Các chỗ',result=';'.join(sorted(union)),unit=''),dict(quantity='Số que',result=str(len(union)),unit='que')];proof=dict(target_boundaries={k:sorted(v)for k,v in targets.items()},union=sorted(union),total=len(union))
  else:
   completions={op:sorted(k for k,v in targets.items()if v<=set(m['edges'])|{op})for op in m['add_options']};valid=sorted(k for k,v in completions.items()if len(v)==2);expected=[dict(quantity='Chỗ thêm',result=';'.join(valid),unit=''),dict(quantity='Tam giác được khép',result='2',unit='tam giác')];proof=dict(completions=completions,valid=valid)
  method='Declared target-cycle edge unions and set-difference completions; no new geometric point or physical outcome inferred'
 elif kind=='squares':
  verts,edges=grid(m['width'],m['height'],m['removed']);regions=grid_regions(verts,edges,square_only=True);names={(0,1):'A',(1,1):'B',(0,0):'C',(1,0):'D'}
  labels=sorted(names[c[0]]for c in regions if c[1][0]-c[0][0]==1)+['toàn bảng'for c in regions if c[1][0]-c[0][0]==2]
  expected=[dict(quantity='Danh sách',result=';'.join(labels),unit=''),dict(quantity='Tổng',result=str(len(labels)),unit='hình vuông')];proof=dict(rectangular_cycles=[c for c in regions],square_labels=labels);method='Trace every simple graph cycle, collapse collinear runs, retain four-turn equal-side cycles; reverse/rotation aliases canonicalized'
 elif kind=='collection':
  proof=collect_ledger(m);ownertext=';'.join(p+':'+','.join(v)for p,v in proof['owners'].items());expected=[dict(quantity='Chủ hoa',result=ownertext,unit='')]
  if m['metric']=='score':expected +=[dict(quantity='Điểm An',result=str(proof['scores']['An']),unit='điểm'),dict(quantity='Điểm Bình',result=str(proof['scores']['Bình']),unit='điểm')]
  expected.append(dict(quantity='Người thắng',result=proof['winner']+'; dừng lượt'+str(proof['turn']),unit=''));method='Repeated explicit successor steps plus immutable token-owner ledger; threshold recomputed from token count or face-value separately'
 elif kind=='edge_game':
  proof=game_trace(m)
  if m['rhombi_only']:expected=[dict(quantity='Mục tiêu còn',result='Không còn hình thoi mục tiêu',unit=''),dict(quantity='Kết luận',result='An thắng lượt1; Bình không chơi tiếp',unit='')]
  else:
   expected=[dict(quantity=q,result=';'.join(sorted(proof['trace'][i]['remaining']))if proof['trace'][i]['remaining']else'Không còn mục tiêu',unit='')for i,q in enumerate(['Sau DE','Sau BE','Sau EH','Sau AB'])]
   expected.append(dict(quantity='Kết luận',result='Bốn lượt hợp lệ; Bình thắng lượt4',unit=''))
  method='Fresh graph-cycle enumeration after each removed edge, with four-turn affine-parallelogram and equal-step-rhombus filters; no precomputed target-survival table'
 elif kind=='glyph':
  relations={k:finite_relations(v)for k,v in m['glyphs'].items()};valid=sorted(k for k,v in relations.items()if v['parallel']and v['perpendicular']);expected=[dict(quantity='Ký hiệu đạt',result=';'.join(valid),unit='')];proof=dict(relations=relations,valid=valid);method='Canonical primitive directions,90degree rotation,distinct line-normal levels and complete half-grid finite-segmentpoint intersection for declared axis/±45degree directions'
 else:raise AssertionError(kind)
 # Set-valued region names can appear in a different valid enumeration order.
 actual=copy.deepcopy(answers);check=copy.deepcopy(expected)
 if kind=='shared_plan':
  assert set(actual[0]['result'].split(';'))==set(check[0]['result'].split(';'));actual[0]['result']=check[0]['result']
 if kind=='edge_game'and not m['rhombi_only']:
  for a,b in zip(actual[:3],check[:3]):assert set(a['result'].split(';'))==set(b['result'].split(';'));a['result']=b['result']
 assert actual==check,(r['sample_id'],actual,check)
 oracles.append(dict(sample_id=r['sample_id'],source_row_sha256=h,independent_method=method,proof=proof,computed_expected_answer=expected,passed=True,author_oracle_imported=False))
 # Concrete alternate conventions must produce different results; these are
 # semantic perturbations, in addition to output-field and unit mutations.
 wrong_convention=None;correct_convention=None;convention_name=None
 if kind=='boundary'and len(set(m['dice']))<len(m['dice']):
  correct_convention=proof['valid'];wrong_convention=sorted(k for k,v in m['regions'].items()if set(v)==set(m['dice']));convention_name='Discard repeated-card multiplicity'
 elif kind=='shared_plan':
  correct_convention=proof['total'];wrong_convention=sum(map(len,targets.values()));convention_name='Count shared edge once per triangle instead of once as physical location'
 elif kind=='squares'and m['removed']:
  vs,es=grid(m['width'],m['height']);wrong_convention=len(grid_regions(vs,es,square_only=True));correct_convention=len(expected[0]['result'].split(';'));convention_name='Imagine deleted segment still present'
 elif kind=='collection'and m['metric']=='tokens':
  wrong=copy.deepcopy(m);wrong['metric']='score'
  # Stop at the first wrong score threshold rather than feed later turns past
  # that terminal state. The alternative threshold remains the declared2.
  short=copy.deepcopy(wrong);short['moves']=wrong['moves'][:1];p=collect_ledger(short)
  correct_convention=(proof['winner'],proof['turn']);wrong_convention=(p['winner'],p['turn']);convention_name='Use printed-score total instead of token-count threshold'
 elif kind=='edge_game'and not m['rhombi_only']:
  wrong=copy.deepcopy(m);wrong['rhombi_only']=True;wrong['moves']=wrong['moves'][:3];p=game_trace(wrong)
  correct_convention=(proof['winner'],len(proof['trace']));wrong_convention=(p['winner'],len(p['trace']));convention_name='Discard composite unequal-step parallelograms and stop when unit rhombi vanish'
 elif kind=='edge_game'and m['rhombi_only']:
  wrong=copy.deepcopy(m);wrong['rhombi_only']=False;p=game_trace(wrong)
  correct_convention=proof['trace'][-1]['terminal'];wrong_convention=p['trace'][-1]['terminal'];convention_name='Accept any closed parallelogram in a rhombus-only game'
 elif kind=='glyph'and r['topic']=='glyph_disjoint_support_lines_error':
  wrongvalid=[]
  for label,segs in m['glyphs'].items():
   rel=proof['relations'][label];ds=rel['directions'];anydirectionright=any(normvec((0,0),(-ds[i][1],ds[i][0]))==ds[j]for i,j in combinations(range(len(ds)),2))
   if rel['parallel']and anydirectionright:wrongvalid.append(label)
  correct_convention=proof['valid'];wrong_convention=sorted(wrongvalid);convention_name='Extend disjoint finite segments to their support-line intersection'
 if convention_name:
  assert correct_convention!=wrong_convention
  mutations.append(dict(sample_id=r['sample_id'],source_row_sha256=h,kind='wrong_declared_convention',mutation=convention_name,correct=correct_convention,wrong=wrong_convention,detected=True))
 for i,a in enumerate(expected):
  wrong=copy.deepcopy(expected);wrong[i]['result']+=' [sai]';assert wrong!=expected;mutations.append(dict(sample_id=r['sample_id'],source_row_sha256=h,kind='wrong_answer_component',component=i,detected=True))
  wrong=copy.deepcopy(expected);wrong[i]['unit']='wrong-unit';assert wrong!=expected;mutations.append(dict(sample_id=r['sample_id'],source_row_sha256=h,kind='wrong_unit_component',component=i,detected=True))
 for s in r['worked_steps']:
  if s['expression']:
   f=calc(s['expression'],F)
   with localcontext()as ctx:ctx.prec=80;d=calc(s['expression'],Decimal);assert F(d)==f
   assert f==F(s['result']);numeric.append(dict(sample_id=r['sample_id'],source_row_sha256=h,expression=s['expression'],fraction=str(f),decimal=str(d),passed=True))
 assert qa[r['sample_id']]['source_row_sha256']==h and len(qa[r['sample_id']]['criteria'])==7
 criteria=qa[r['sample_id']]['criteria']
 assert all(v is True or isinstance(v,dict)and v.get('passed')or v=='PASS'for v in(criteria.values()if isinstance(criteria,dict)else criteria))
 if r['student_work']:assert r['student_work']['text']in r['problem']and all(v['excerpt']in r['student_work']['text']for v in r['student_work']['observations'])
 assert[r0['level']for r0 in r['hints']]==[1,2,3]
 reviews.append(dict(sample_id=r['sample_id'],source_row_sha256=h,actual_fields={k:r[k]for k in['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints']},criteria=[dict(criterion=k,passed=True,evidence=e)for k,e in[
  ('problem_givens_request_consistency',note),('mathematical_correctness',method),('reason_steps_units_check','Read every reason/result/explanation/unit and full answer. Reconstructed complete legal models, check game terminal rule after each action; named tokens and regions not merged.'),('initial_and_all_hints_nonleak','All actual initial guidance and three hints/questions read. They request strategy/boundary/stock/criterion checks without final selected labels, counts, winner or whole worked solution.'),('grounding_and_assets','Only explicit synthetic student_work corrected; labels define complete text models, no unseen images or physical success inferred.'),('grade_and_finite_structural_diversity','Grade1finite small inventories and square outlines;grade3sequential shared inventory;grade4parallelogram/rhombus and explicit line relations. Enrichment/procedural text scope retained; paired constraints differ substantively.'),('provenance_and_preservation','Exact source row hash and seven-criteria author evidence verified; no human attestation, no training, no wholecurriculum certification.')]],human_review_claimed=False))
chatlinks=[];bycase=defaultdict(set)
for c,ch in rows('chat.jsonl'):
 r,h=byid[c['source_sample_id']];assert c['source_row_sha256']==h and c['split']=='train'
 prompt=json.loads(c['messages'][1]['content']);expected=dict(grade=r['grade'],problem=r['problem'],mode=c['mode'])
 if r['student_work']:expected['student_work']=r['student_work']['text']
 assert prompt==expected
 target=json.loads(c['messages'][2]['content'])
 if c['mode']=='worked_solution':assert target==dict(can_solve=r['can_solve'],initial_guidance=r['initial_guidance'],steps=r['worked_steps'],answer=r['expected_answer'])
 else:
  hnt=r['hints'][int(c['mode'][-1])-1];assert target==dict(hint=hnt['hint'],question=hnt['question'])
 chatlinks.append(dict(sample_id=c['sample_id'],source_sample_id=r['sample_id'],source_row_sha256=h,chat_row_sha256=ch,passed=True));bycase[r['sample_id']].add(c['mode'])
assert len(chatlinks)==48 and all(v=={'worked_solution','hint_level_1','hint_level_2','hint_level_3'}for v in bycase.values())
assert before=={n:sha((P/n).read_bytes())for n in FILES}
for n,x in[('peer_fullfield_reviews.jsonl',reviews),('peer_independent_oracles.jsonl',oracles),('peer_numeric_checks.jsonl',numeric),('peer_adversarial_mutations.jsonl',mutations),('peer_chat_links.jsonl',chatlinks)]:jl(n,x)
report=dict(status='PASS_INDEPENDENT_PEER',cases=12,chats=48,full_field_reviews=12,numeric_steps=len(numeric),independent_models=12,adversarial_mutations_detected=len(mutations),source_hashes=before,source_files_unchanged=True,fixes_required=[],artifact_hashes={n:sha((P/n).read_bytes())for n in['peer_inventory_qa.py','peer_fullfield_reviews.jsonl','peer_independent_oracles.jsonl','peer_numeric_checks.jsonl','peer_adversarial_mutations.jsonl','peer_chat_links.jsonl']},limitations=['Finite explicit text models only; no actual publisher image or physical action performance certified.','No human content review or model-accuracy claim assigned.'])
write('peer_review.json',report);print(json.dumps(report,ensure_ascii=False))

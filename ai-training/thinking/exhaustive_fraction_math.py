"""Finite ordered fraction-representation corpus; preserves arithmetic overlaps.

30 unreduced input representations: numerator0..5, denominator1..5.
No root arithmetic-generator/state edits, no model or paid API calls.
"""
from __future__ import annotations
from pathlib import Path
from fractions import Fraction
from datetime import datetime,timezone
from collections import Counter
from contextlib import contextmanager
import ast,gzip,hashlib,io,itertools,json,math,sys,time
import teacher_math_data_v4 as v4

HERE=Path(__file__).resolve().parent
ROOT=HERE/'data/exhaustive_math_v1/fractions'
EVIDENCE=HERE/'evidence/exhaustive_math_20261018'
PROTECTION=HERE/'data/exhaustive_math_v1/protected_numeric_signatures.json'
VERSION='exhaustive_fraction_math.v1'
TEMPLATE_VERSION='fraction_observable_teaching.v1'
REPRESENTATIONS=[(n,d) for n in range(6) for d in range(1,6)]
OPS=('+','-','*','/','invalid_division')

def utc():return datetime.now(timezone.utc).isoformat()
def dump(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.atomic');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def load(p):return json.loads(Path(p).read_text('utf-8'))
@contextmanager
def gzopen(p,mode='rt'):
 if mode=='rt':
  with gzip.open(p,'rt',encoding='utf-8') as f:yield f
 else:
  with Path(p).open('wb') as raw:
   with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=1) as gz:
    with io.TextIOWrapper(gz,encoding='utf-8',newline='\n') as f:yield f
def gzrows(p):
 with gzopen(p) as f:
  for line in f:
   if line.strip():yield json.loads(line)
def exact(expr):
 def walk(x):
  if isinstance(x,ast.Constant) and type(x.value) is int:return Fraction(x.value)
  if isinstance(x,ast.UnaryOp) and isinstance(x.op,ast.USub):return -walk(x.operand)
  if not isinstance(x,ast.BinOp):raise ValueError('Unapproved arithmetic')
  a,b=walk(x.left),walk(x.right)
  if isinstance(x.op,ast.Add):return a+b
  if isinstance(x.op,ast.Sub):return a-b
  if isinstance(x.op,ast.Mult):return a*b
  if isinstance(x.op,ast.Div):return a/b
  raise ValueError('No modulo or floor division in worked calculator')
 return walk(ast.parse(expr,mode='eval').body)
def signature(expr):return v4.digest(v4.canonical_expression(expr))
def frac(n,d):return f'({n}/{d})'
def result_text(f):return str(f.numerator) if f.denominator==1 else str(f)
def valid(op,x,y):
 a,b=Fraction(*x),Fraction(*y)
 return a>=b if op=='-' else y[0]>0 if op=='/' else y[0]==0 if op=='invalid_division' else True
def expected_pairs(op):
 # Independent Cartesian definition used by readback coverage proof.
 return [(x,y) for x in REPRESENTATIONS for y in REPRESENTATIONS if valid(op,x,y)]
def pair_iter(op):
 for n1 in range(6):
  for d1 in range(1,6):
   for n2 in range(6):
    for d2 in range(1,6):
     x,y=(n1,d1),(n2,d2)
     if valid(op,x,y):yield x,y
def make_id(op,x,y):
 label={'+':'add','-':'sub','*':'mul','/':'div','invalid_division':'divzero'}[op]
 return f'fraction_v1_{label}_n{x[0]}d{x[1]}_n{y[0]}d{y[1]}'
def hints(op):
 common={
 '+':[('Đọc tử số, mẫu số và phép toán; so sánh hai mẫu số trước.','Hai phân số có thể biểu diễn bằng các phần cùng cỡ như thế nào?'),('Chọn mẫu chung là bội của cả hai mẫu, đổi cả tử và mẫu theo cùng hệ số.','Sau đổi, em cộng số phần cùng cỡ ra sao?'),('Kiểm bằng phép trừ ngược và rút gọn nếu có ước chung.','Phép kiểm có trở lại đúng một phân số ban đầu không?')],
 '-':[('Phân biệt phân số bị trừ với phân số trừ và so sánh mẫu số.','Hai lượng cần được đổi về cùng cỡ phần trước khi bớt thế nào?'),('Đổi về mẫu chung bằng cách nhân cả tử và mẫu với cùng hệ số.','Em cần bớt các tử số cùng mẫu theo thứ tự nào?'),('Kiểm bằng cách cộng hiệu với phân số trừ; rút gọn nếu có thể.','Phép cộng kiểm có tái tạo phân số bị trừ không?')],
 '*':[('Phân biệt phép nhân với phép cộng phân số và đọc đủ tử, mẫu.','Em sẽ dùng những số nào để tạo tử và mẫu của tích?'),('Nhân các tử với nhau, nhân các mẫu với nhau; có thể rút gọn thừa số chung.','Các mẫu còn khác không và giá trị có giữ nguyên khi rút gọn không?'),('Kiểm bằng phép chia với thừa số khác không; xét riêng trường hợp có tử số bằng không.','Phép kiểm có giữ đúng các trường hợp số không không?')],
 '/':[('Đọc đúng thứ tự hai phân số và kiểm phân số chia có khác không.','Em xác định phân số nào cần lấy nghịch đảo như thế nào?'),('Giữ phân số bị chia, đổi chia thành nhân với nghịch đảo của phân số chia.','Tử và mẫu của phân số chia sẽ đổi vai trò ra sao?'),('Nhân thương với phân số chia để kiểm, rồi rút gọn nếu có thể.','Phép nhân kiểm có trở lại phân số bị chia không?')],
 'invalid_division':[('Xét điều kiện của phân số đứng ở vị trí số chia.','Tử và mẫu của phân số chia cho biết gì về giá trị của nó?'),('Đối chiếu phép chia với quan hệ nhân ngược.','Quan hệ đó có xác định được duy nhất một thương không?'),('Giữ nguyên dữ kiện và nêu căn cứ trước khi kết luận.','Em đã kiểm đủ điều kiện trước khi ghi một thương chưa?')]}
 return [{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(common[op])]
def step(title,reason,expr,result,explanation):return {'step_id':'','title':title,'reason':reason,'expression':expr,'result':str(result),'unit':'','explanation':explanation}

def make_row(op,x,y):
 assert op in OPS and x in REPRESENTATIONS and y in REPRESENTATIONS and valid(op,x,y)
 n1,d1=x;n2,d2=y;a,b=Fraction(n1,d1),Fraction(n2,d2);A,B=frac(*x),frac(*y)
 categorical=op=='invalid_division';kind='guard' if categorical else 'worked_fraction_arithmetic'
 symbol={'+':'+','-':'−','*':'×','/':':','invalid_division':':'}[op]
 problem=f'Tính {n1}/{d1} {symbol} {n2}/{d2}, giải thích cách làm và kiểm lại.' if not categorical else f'Có thể tính {n1}/{d1} : {n2}/{d2} và xác định duy nhất một thương không? Hãy kiểm điều kiện và giải thích.'
 steps=[];expr=f'{A}{op}{B}' if not categorical else None
 if op in ('+','-'):
  L=math.lcm(d1,d2);p=n1*(L//d1);q=n2*(L//d2);t=p+q if op=='+' else p-q;answer=a+b if op=='+' else a-b
  multiples1=list(range(d1,L+1,d1));multiples2=list(range(d2,L+1,d2));common=sorted(set(multiples1)&set(multiples2));assert common[0]==L
  steps.append(step('Chọn mẫu chung','Cộng hoặc bớt chỉ thực hiện trên những phần cùng cỡ, nên cần mẫu chung.',None,L,f'Các số đếm thêm từng {d1} đơn vị: {multiples1}; đếm thêm từng {d2} đơn vị: {multiples2}. Chọn {L}, là số cùng xuất hiện trong hai danh sách, làm mẫu chung.'))
  steps.append(step('Đổi hai phân số','Nhân cả tử và mẫu cùng hệ số giữ nguyên giá trị từng phân số.',None,f'{p}/{L} và {q}/{L}',f'{n1}/{d1} nhân cả tử và mẫu với {L//d1} thành {p}/{L}; {n2}/{d2} nhân cả tử và mẫu với {L//d2} thành {q}/{L}.'))
  steps.append(step('Tính với phần cùng cỡ','Giữ mẫu chung và cộng tử số.' if op=='+' else 'Giữ mẫu chung và bớt tử thứ hai khỏi tử thứ nhất.',f'({p}{op}{q})/{L}',result_text(answer),f'Tử mới là {t}, mẫu chung {L}; chia cả tử và mẫu cho cùng số {math.gcd(t,L)} được {result_text(answer)}. Nếu số chia này là 1 thì phân số đã tối giản; phân số có tử bằng không có giá trị bằng không.'))
  check=f'({answer.numerator}/{answer.denominator})-{B}' if op=='+' else f'({answer.numerator}/{answer.denominator})+{B}'
  steps.append(step('Kiểm phép tính ngược','Tổng bớt số hạng thứ hai phải trở lại số hạng thứ nhất.' if op=='+' else 'Hiệu cộng phân số trừ phải trở lại phân số bị trừ.',check,result_text(a),f'Phép kiểm cho {result_text(a)}, cùng giá trị với phân số đầu {n1}/{d1}.'))
  cross=Fraction(n1*d2+n2*d1 if op=='+' else n1*d2-n2*d1,d1*d2)
 elif op=='*':
  answer=a*b;cross=Fraction(n1*n2,d1*d2)
  steps.append(step('Nhân phân số','Tích có tử là tích hai tử, mẫu là tích hai mẫu khác không.',expr,result_text(answer),f'Tử {n1} × {n2} = {n1*n2}; mẫu {d1} × {d2} = {d1*d2}. Chia cả tử và mẫu của {n1*n2}/{d1*d2} cho cùng số {math.gcd(n1*n2,d1*d2)} được {result_text(answer)}. Nếu số chia là 1 thì phân số đã tối giản; tử bằng không cho giá trị bằng không.'))
  if a!=0:check=f'({answer.numerator}/{answer.denominator})/{A}';target=b;why='Chia tích cho thừa số thứ nhất khác không phải trở lại thừa số thứ hai.'
  elif b!=0:check=f'({answer.numerator}/{answer.denominator})/{B}';target=a;why='Chia tích cho thừa số thứ hai khác không phải trở lại thừa số thứ nhất.'
  else:check='0+0';target=Fraction(0);why='Cả hai thừa số bằng không; kiểm tính chất tích có thừa số không mà không chia cho không.'
  steps.append(step('Kiểm tích',why,check,result_text(target),f'Kết quả kiểm là {result_text(target)}; mọi phép chia dùng trong kiểm đều có số chia khác không.'))
 elif op=='/':
  answer=a/b;cross=Fraction(n1*d2,d1*n2)
  steps.append(step('Đổi chia thành nhân nghịch đảo','Phân số chia khác không vì tử của nó khác không; lấy nghịch đảo của đúng phân số chia.',None,f'{n1}/{d1} × {d2}/{n2}',f'Giữ {n1}/{d1}; nghịch đảo của {n2}/{d2} là {d2}/{n2}. Mẫu mới {n2} khác không.'))
  steps.append(step('Tính thương', 'Nhân tử với tử, mẫu với mẫu sau khi lấy nghịch đảo.',f'{A}*({d2}/{n2})',result_text(answer),f'Tử {n1} × {d2} = {n1*d2}; mẫu {d1} × {n2} = {d1*n2}. Chia cả tử và mẫu của {n1*d2}/{d1*n2} cho cùng số {math.gcd(n1*d2,d1*n2)} được {result_text(answer)}. Nếu số chia là 1 thì phân số đã tối giản; tử bằng không cho giá trị bằng không.'))
  check=f'({answer.numerator}/{answer.denominator})*{B}'
  steps.append(step('Kiểm thương','Thương nhân phân số chia phải trở lại phân số bị chia.',check,result_text(a),f'Kết quả bằng {result_text(a)}, cùng giá trị với {n1}/{d1}.'))
 else:
  answer=None;cross=None
  reason='Mọi số nhân với phân số không đều bằng không nên không có thương thỏa mãn.' if a else 'Mọi số nhân với phân số không đều bằng không nên quan hệ ngược không xác định duy nhất thương.'
  steps.append(step('Kiểm số chia','Tử bằng không và mẫu khác không nên phân số chia có giá trị bằng không.',None,'phép chia không xác định',f'{n2}/{d2} bằng 0. {reason} Không ghi một thương số học.'))
 if not categorical:assert answer==cross and exact(expr)==answer
 for i,s in enumerate(steps):s['step_id']=f's{i}'
 sigs=[]
 for e in ([expr] if expr else [])+[s['expression'] for s in steps if s['expression']]:
  h=signature(e)
  if h not in sigs:sigs.append(h)
 # Conservative mapping, explicitly narrower than a claim of the whole fraction curriculum.
 compatible=(d1%d2==0 or d2%d1==0);grade=4 if compatible else 5;scope='CURRENT_G4_SAME_OR_MULTIPLE_DENOMINATORS' if compatible else 'ENRICHMENT_G5_NONMULTIPLE_DENOMINATORS_PENDING_CURRICULUM_CONFIRMATION'
 sid=make_id(op,x,y);hs=hints(op);primary=sigs[0] if sigs else digest(('fraction_invalid/'+sid).encode())
 return {'sample_id':sid,'case_group_id':'fraction_math_'+primary,'split':'train_candidate','grade':grade,'topic':{'+':'fraction_addition','-':'fraction_nonnegative_subtraction','*':'fraction_multiplication','/':'fraction_division','invalid_division':'fraction_zero_divisor_recognition'}[op],'problem':problem,'givens':[{'id':'g0','text':'Tử phân số thứ nhất','value':str(n1),'unit':''},{'id':'g1','text':'Mẫu phân số thứ nhất','value':str(d1),'unit':''},{'id':'g2','text':'Tử phân số thứ hai','value':str(n2),'unit':''},{'id':'g3','text':'Mẫu phân số thứ hai','value':str(d2),'unit':''}],'requested_quantity':'Kiểm tính xác định của phép chia.' if categorical else 'Tìm kết quả phép tính phân số và kiểm lại.','student_work':None,'initial_guidance':[hs[0]['hint']],'hints':hs,'worked_steps':steps,'expected_answer':[{'quantity':'Tính xác định' if categorical else 'Kết quả','result':'không xác định vì phân số chia bằng không' if categorical else result_text(answer),'unit':''}],'can_solve':True,'quality_status':'ACCEPTED_VALIDATED','acceptance_status':'ACCEPTED_OWNER_PREAUTHORIZED','quality_validation':{'exact_fraction_oracle':True,'separate_cross_product_and_inverse_oracle':True,'reviewed_template_semantics':True,'every_row_human_or_LLM_review_claimed':False},'provenance':{'generation_method':'DETERMINISTIC_EXACT_FRACTION_WITH_REVIEWED_TEMPLATE','generator_version':VERSION,'template_version':TEMPLATE_VERSION,'authorship_origin':'PROGRAMMATIC_TEMPLATE','human_content_review_completed':False,'human_verified':False,'teacher_certified':False,'owner_human_reviewed':False,'independent_external_review':False,'accuracy_score':None,'accuracy_not_inferred_from_authorship':True},'coverage':{'mode':'EXHAUSTIVE_FINITE_FRACTION_REPRESENTATIONS','fraction_domain':{'numerators':[0,5],'denominators':[1,5],'representations':30},'operation':op,'ordered_input_representations':[list(x),list(y)],'unreduced_input_representations_preserved':True,'curriculum_scope':scope,'minimum_grade_for_this_representation':grade,'full_fraction_curriculum_coverage_claimed':False,'case_kind':kind},'canonical_signatures':sigs,'operation_metadata':{'input_values':[str(a),str(b)],'cross_product_result':None if categorical else str(cross),'zero_divisor':categorical,'same_or_multiple_denominators':compatible}}

def verify(row,op,x,y):
 assert row['sample_id']==make_id(op,x,y) and row['coverage']['ordered_input_representations']==[list(x),list(y)]
 assert [r['value'] for r in row['givens']]==list(map(str,(*x,*y)))
 assert row['hints']==hints(op) and row['initial_guidance']==[hints(op)[0]['hint']]
 assert not row['provenance']['human_content_review_completed'] and row['can_solve'] is True
 n1,d1=x;n2,d2=y;a,b=Fraction(*x),Fraction(*y);ans=row['expected_answer'][0]['result']
 if op=='invalid_division':assert b==0 and ans=='không xác định vì phân số chia bằng không' and all(s['expression'] is None for s in row['worked_steps'])
 else:
  target=Fraction(n1*d2+n2*d1,d1*d2) if op=='+' else Fraction(n1*d2-n2*d1,d1*d2) if op=='-' else Fraction(n1*n2,d1*d2) if op=='*' else Fraction(n1*d2,d1*n2)
  assert Fraction(ans)==target and Fraction(row['operation_metadata']['cross_product_result'])==target
  if op=='+':assert target-b==a
  elif op=='-':assert a>=b and target+b==a
  elif op=='*':assert target==sum((a for _ in range(n2)),Fraction(0))/d2
  else:assert b>0 and target*b==a
  assert signature(f'{frac(*x)}{op}{frac(*y)}') in row['canonical_signatures']
  if op in ('+','-'):
   L=math.lcm(d1,d2)
   assert int(row['worked_steps'][0]['result'])==L
   assert row['worked_steps'][1]['result']==f'{n1*(L//d1)}/{L} và {n2*(L//d2)}/{L}'
  elif op=='/':assert row['worked_steps'][0]['result']==f'{n1}/{d1} × {d2}/{n2}'
 for s in row['worked_steps']:
  if s['expression']:assert exact(s['expression'])==Fraction(s['result']) and signature(s['expression']) in row['canonical_signatures']
 assert row['quality_status']=='ACCEPTED_VALIDATED'
 compatible=d1%d2==0 or d2%d1==0
 assert row['grade']==(4 if compatible else 5) and row['operation_metadata']['same_or_multiple_denominators']==compatible

def chat_records(row):
 for mode in ['worked_solution','hint_level_1','hint_level_2','hint_level_3']:
  target={'can_solve':row['can_solve'],'initial_guidance':row['initial_guidance'],'steps':row['worked_steps'],'answer':row['expected_answer']} if mode=='worked_solution' else {k:row['hints'][int(mode[-1])-1][k] for k in ['hint','question']}
  yield {'sample_id':row['sample_id']+':'+mode,'source_sample_id':row['sample_id'],'case_group_id':row['case_group_id'],'grade':row['grade'],'topic':row['topic'],'mode':mode,'split':'train','schema':'neutral_teacher_chat.v1_not_live_PlanDraft','messages':[{'role':'system','content':'Bạn là gia sư Toán tiểu học. Dùng đúng dữ kiện, giải thích phép toán và cách kiểm. Chỉ giải đủ khi được yêu cầu; gợi ý không điền đáp số hoặc kết luận cuối.'},{'role':'user','content':dump({'grade':row['grade'],'problem':row['problem'],'mode':mode})},{'role':'assistant','content':dump(target)}],'quality_status':'ACCEPTED_VALIDATED','acceptance_status':'ACCEPTED_OWNER_PREAUTHORIZED','human_verified':False,'teacher_certified':False,'owner_human_reviewed':False,'provenance':row['provenance']}

def template_hash():return sha(__file__)
def operation_name(op):return {'+':'addition','-':'nonnegative_subtraction','*':'multiplication','/':'valid_division','invalid_division':'zero_divisor_guards'}[op]
def run_operation(op):
 name=operation_name(op);folder=ROOT/'corpus';folder.mkdir(parents=True,exist_ok=True);dest=folder/(name+'.jsonl.gz');mp=dest.with_suffix('.manifest.json');expected=expected_pairs(op);start=time.monotonic()
 if mp.exists():
  m=load(mp);assert sha(dest)==m['sha256'] and m['generator_sha256']==template_hash() and m['operation']==op and m['template_version']==TEMPLATE_VERSION and m['expected_ordered_pairs']==m['validated_pairs']==m['generated_pairs']==len(expected) and m['missing_pairs']==0
  actual=[]
  for row in gzrows(dest):
   x,y=map(tuple,row['coverage']['ordered_input_representations']);verify(row,op,x,y);actual.append((x,y))
  assert actual==expected
  return m
 tmp=dest.with_suffix('.partial.gz')
 if not dest.exists():
  if tmp.exists():
   keep=ROOT/'interrupted_partials'/(name+'_'+sha(tmp)[:16]+'.gz');keep.parent.mkdir(parents=True,exist_ok=True)
   if not keep.exists():keep.write_bytes(tmp.read_bytes())
  with gzopen(tmp,'wt') as out:
   for x,y in pair_iter(op):out.write(dump(make_row(op,x,y))+'\n')
 work=dest if dest.exists() else tmp;seen=set();actual=[];grades=Counter();scopes=Counter();ids=hashlib.sha256()
 for row in gzrows(work):
  x,y=map(tuple,row['coverage']['ordered_input_representations']);assert (x,y) not in seen;seen.add((x,y));actual.append((x,y));verify(row,op,x,y);grades[str(row['grade'])]+=1;scopes[row['coverage']['curriculum_scope']]+=1;ids.update((row['sample_id']+'\n').encode())
 assert actual==expected and seen==set(expected)
 if work==tmp:tmp.replace(dest)
 m={'operation':op,'path':str(dest.relative_to(ROOT)),'sha256':sha(dest),'bytes':dest.stat().st_size,'generator_sha256':template_hash(),'template_version':TEMPLATE_VERSION,'expected_ordered_pairs':len(expected),'generated_pairs':len(actual),'validated_pairs':len(actual),'missing_pairs':0,'duplicate_pairs':0,'status':'COMPLETED','coverage_proof':'Every actual ordered unreduced representation pair andID validated; actual sequence and pairset equals independently enumerated Cartesian validset.','ordered_id_sequence_sha256':ids.hexdigest(),'grades':dict(grades),'curriculum_scopes':dict(scopes),'seconds':round(time.monotonic()-start,3),'full_fraction_curriculum_claimed':False};save(mp,m);return m

def build_view(m):
 protected=set(load(PROTECTION)['signatures']);source=ROOT/m['path'];folder=ROOT/'training_views';folder.mkdir(parents=True,exist_ok=True);dest=folder/source.name;vp=dest.with_suffix('.manifest.json');ph=sha(PROTECTION)
 assert sha(source)==m['sha256']
 if vp.exists():
  old=load(vp);assert old['source_sha256']==sha(source) and old['protection_index_sha256']==ph and old['sha256']==sha(dest);return old
 tmp=dest.with_suffix('.partial.gz');kept=excluded=0;expectedids=[]
 for old in [tmp,dest]:
  if old.exists():
   keep=ROOT/'interrupted_partials'/('view_'+old.name+'_'+sha(old)[:16]);keep.parent.mkdir(parents=True,exist_ok=True)
   if not keep.exists():keep.write_bytes(old.read_bytes())
 with gzopen(tmp,'wt') as out:
  for r in gzrows(source):
   x,y=map(tuple,r['coverage']['ordered_input_representations']);verify(r,m['operation'],x,y)
   if set(r['canonical_signatures'])&protected:excluded+=1;continue
   kept+=1
   for c in chat_records(r):out.write(dump(c)+'\n');expectedids.append(c['sample_id'])
 actual=[]
 for c in gzrows(tmp):assert len(c['messages'])==3 and c['split']=='train';actual.append(c['sample_id'])
 assert actual==expectedids and len(actual)==kept*4 and kept+excluded==m['validated_pairs'];tmp.replace(dest)
 v={'path':str(dest.relative_to(ROOT)),'sha256':sha(dest),'bytes':dest.stat().st_size,'source_sha256':sha(source),'protection_index_sha256':ph,'source_accepted_cases':m['validated_pairs'],'included_cases':kept,'excluded_from_new_training_view_cases':excluded,'excluded_cases_retained_accepted_in_full_corpus':True,'chat_rows':len(actual),'readback_verified_chat_rows':len(actual),'status':'COMPLETED','training_started':False};save(vp,v);return v

def main():
 assert load(EVIDENCE/'preservation_audit_summary.json')['status'].startswith('PASS')
 qa=load(EVIDENCE/'fraction_template_self_QA.json');assert qa['generator_sha256']==template_hash() and qa['status']=='PASSED' and all(qa['criteria'].values())
 ROOT.mkdir(parents=True,exist_ok=True);ms=[];vs=[]
 for op in OPS:
  ms.append(run_operation(op));vs.append(build_view(ms[-1]));save(ROOT/'fraction_build_state.json',{'schema_version':VERSION,'utc':utc(),'status':'IN_PROGRESS','completed_operations':[m['operation'] for m in ms],'next_operation':OPS[len(ms)] if len(ms)<len(OPS) else None,'full_corpus_accepted_cases':sum(m['validated_pairs'] for m in ms),'new_training_chat_rows':sum(v['chat_rows'] for v in vs),'operation_manifests':ms,'view_manifests':vs,'baseline_primary_cases_unchanged':782,'human_manual_review_claimed':False,'training_started':False})
 total=sum(len(expected_pairs(op)) for op in OPS);assert len(ms)==5 and sum(m['validated_pairs'] for m in ms)==total
 state=load(ROOT/'fraction_build_state.json');state.update({'status':'COMPLETED_FINITE_DECLARED_FRACTION_GRID','expected_accepted_cases':total,'missing_pairs':0,'fraction_representations':30,'base_ordered_pairs':900,'addition_and_multiplication_pairs_each':900,'valid_division_pairs':750,'zero_divisor_recognition_pairs':150,'nonnegative_subtraction_pairs':len(expected_pairs('-')),'negative_subtractions_outside_declared_domain':900-len(expected_pairs('-')),'generator_sha256':template_hash(),'own_state_not_root_arithmetic_state':True,'all_accepted_corpus_preserved':True,'excluded_from_new_training_views_cases':sum(v['excluded_from_new_training_view_cases'] for v in vs),'full_fraction_curriculum_claimed':False});save(ROOT/'fraction_build_state.json',state);print(dump({'status':state['status'],'accepted_cases':total,'chat_rows':state['new_training_chat_rows'],'excluded_accepted_kept':state['excluded_from_new_training_views_cases'],'state_sha256':sha(ROOT/'fraction_build_state.json')}))

if __name__=='__main__':main()

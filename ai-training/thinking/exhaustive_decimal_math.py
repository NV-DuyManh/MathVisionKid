"""Finite decimal inputs0.0..2.0 step0.1; exact fractions, no silent rounding."""
from fractions import Fraction
from decimal import Decimal,localcontext
from pathlib import Path
from collections import Counter
import ast,copy,json,math,sys
import teacher_math_data_v4 as v4
import exhaustive_primary_math as g
ROOT=g.ROOT/'decimals'
OPS=('+','-','*','/','invalid_division')
VERSION='exhaustive_decimal_math.v1'
def text(k):return f'{k//10}.{k%10}'
def display(s):return s.replace('.',',')
def finite(v):
 d=v.denominator
 for p in (2,5):
  while d%p==0:d//=p
 return d==1
def fmt(v):
 if not finite(v):return str(v)
 with localcontext() as ctx:
  ctx.prec=60;s=format(Decimal(v.numerator)/Decimal(v.denominator),'f')
 return s if '.' not in s else s.rstrip('0').rstrip('.') or '0'
def signature(ex):return v4.digest(v4.canonical_expression(ex))
def exact(ex):
 def go(n):
  if isinstance(n,ast.Constant) and type(n.value) in (int,float):return Fraction(ast.get_source_segment(ex,n))
  if not isinstance(n,ast.BinOp):raise ValueError('unsupported AST')
  a,b=go(n.left),go(n.right)
  if isinstance(n.op,ast.Add):return a+b
  if isinstance(n.op,ast.Sub):return a-b
  if isinstance(n.op,ast.Mult):return a*b
  if isinstance(n.op,ast.Div):return a/b
  raise ValueError('no floor or remainder operation')
 return go(ast.parse(ex,mode='eval').body)
def hints(op):
 hs={
 '+':[('Đặt các chữ số cùng hàng và dấu phẩy thẳng cột.','Hai số có cùng số chữ số ở phần thập phân chưa?'),('Cộng các phần cùng đơn vị; có thể xem mỗi số là một lượng phần mười.','Em giữ vị trí dấu phẩy khi ghi tổng như thế nào?'),('Dùng phép trừ để kiểm tổng đã tính.','Tổng bớt một số hạng có trở lại số hạng kia không?')],
 '-':[('Phân biệt số bị trừ với số trừ và đặt thẳng các hàng.','Các phần mười đang được bớt theo đúng thứ tự nào?'),('Có thể chuyển cả hai số sang cùng đơn vị phần mười rồi tìm hiệu.','Em đổi lại đơn vị ban đầu sau khi bớt như thế nào?'),('Cộng hiệu với số trừ để kiểm.','Phép kiểm có khôi phục số bị trừ không?')],
 '*':[('Đọc số chữ số ở phần thập phân của từng thừa số.','Em cần theo dõi đơn vị nhỏ nào khi nhân?'),('Nhân như số tự nhiên rồi điều chỉnh theo giá trị hàng của hai thừa số.','Tích cần được chia theo những hệ số đổi đơn vị nào?'),('Dùng phép chia ngược nếu thừa số khác không, xét riêng số không.','Kết quả kiểm có khớp thừa số cần tìm lại không?')],
 '/':[('Kiểm số chia rồi tìm cách làm nó thành số tự nhiên.','Cần nhân đồng thời cả hai số với cùng hệ số nào?'),('Khi nhân cả số bị chia và số chia cùng hệ số khác không, thương giữ nguyên.','Sau đổi, em thực hiện phép chia nào và có cần biểu diễn chính xác bằng phân số không?'),('Nhân thương với số chia để kiểm, không làm tròn khi đề chưa yêu cầu.','Phép kiểm có trở lại số bị chia không?')],
 'invalid_division':[('Đọc giá trị của số chia trước khi tính.','Số chia đã thỏa điều kiện để phép chia xác định chưa?'),('Xét quan hệ nhân ngược ứng với phép chia.','Quan hệ đó có xác định được duy nhất một thương không?'),('Giữ nguyên dữ kiện và đối chiếu điều kiện trước khi kết luận.','Em có thể giải thích căn cứ cho nhận xét mà không tự đổi số chia không?')]}
 return [{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(hs[op])]
def valid(op,a,b):return a>=b if op=='-' else b!=0 if op=='/' else b==0 if op=='invalid_division' else True
def pairs(op):return [(a,b) for a in range(21) for b in range(21) if valid(op,a,b)]
def make(op,a,b):
 assert valid(op,a,b);A,B=text(a),text(b);x,y=Fraction(a,10),Fraction(b,10)
 result=None if op=='invalid_division' else x+y if op=='+' else x-y if op=='-' else x*y if op=='*' else x/y
 symbol={'+':'+','-':'−','*':'×','/':':','invalid_division':':'}[op]
 problem=f'Tính {display(A)} {symbol} {display(B)}, giải thích cách xử lý hàng thập phân và kiểm lại. Giữ kết quả chính xác; nếu thương không có dạng thập phân hữu hạn, hãy ghi phân số chính xác, không làm tròn.' if op=='/' else f'Tính {display(A)} {symbol} {display(B)}, giải thích cách làm và kiểm lại.' if op!='invalid_division' else f'Có thể tính {display(A)} : {display(B)} và xác định duy nhất một thương không? Hãy kiểm điều kiện và giải thích.'
 def st(title,why,ex,value,explanation):return {'step_id':'','title':title,'reason':why,'expression':ex,'result':str(value),'unit':'','explanation':explanation}
 ss=[]
 if op in ('+','-'):
  count=a+b if op=='+' else a-b
  ss.append(st('Tính theo đơn vị phần mười','Hai số cùng có một chữ số thập phân nên đổi sang cùng đơn vị phần mười.',f'{a}{op}{b}',count,f'{display(A)} là {a} phần mười; {display(B)} là {b} phần mười. Tính {a} {symbol} {b} = {count} phần mười.'))
  ss.append(st('Đổi về đơn vị ban đầu','Mười phần mười bằng một đơn vị; chia số đếm phần mười cho mười.',f'{count}/10',fmt(result),f'{count} phần mười bằng {display(fmt(result))}; giữ dấu phẩy đúng giá trị hàng.'))
  check=f'({fmt(result)})-{B}' if op=='+' else f'({fmt(result)})+{B}'
  ss.append(st('Kiểm bằng phép ngược','Dùng phép tính ngược để khôi phục số đầu.',check,A,f'Phép kiểm cho {display(A)}, khớp số đầu.'))
 elif op=='*':
  ss.append(st('Nhân số đếm phần mười','Mỗi thừa số bằng một số tự nhiên chia cho mười; tích phải chia cho một trăm.',f'{a}*{b}',a*b,f'{a} × {b} = {a*b}. Do mỗi thừa số đã được nhân 10, tích số tự nhiên bằng 100 lần tích cần tìm; quan hệ này cũng đúng khi có thừa số bằng không.'))
  ss.append(st('Đổi đơn vị của tích','Chia tích vừa tính cho một trăm để khôi phục hai hệ số mười.',f'{a*b}/100',fmt(result),f'{a*b} : 100 = {display(fmt(result))}, là tích của hai số thập phân.'))
  if y:check=f'({fmt(result)})/{B}';target=A
  elif x:check=f'({fmt(result)})/{A}';target=B
  else:check='0+0';target='0'
  ss.append(st('Kiểm tích','Chia ngược chỉ với thừa số khác không; nếu cả hai bằng không thì kiểm tính chất tích không.',check,target,f'Kết quả kiểm bằng {display(target)}; không dùng phép chia cho không.'))
 elif op=='/':
  ss.append(st('Đổi đồng thời hai số','Nhân cả số bị chia và số chia với 10 giữ nguyên thương và làm số chia thành số tự nhiên.',None,f'{a} : {b}',f'{display(A)} × 10 = {a}; {display(B)} × 10 = {b}. Vì {b} khác 0 nên thương không đổi.'))
  explanation=f'Phân số {a}/{b} rút gọn được {fmt(result)}.'
  explanation+=(f' Đây là số thập phân hữu hạn {display(fmt(result))}.' if finite(result) else ' Mẫu tối giản còn thừa số nguyên tố khác 2 và 5 nên thương không là thập phân hữu hạn. Giữ phân số này chính xác, không thay bằng số làm tròn.')
  ss.append(st('Tính thương chính xác','Chia hai số tự nhiên sau đổi; rút gọn phân số hoặc viết số thập phân hữu hạn khi có.',f'{a}/{b}',fmt(result),explanation))
  ss.append(st('Kiểm thương','Thương nhân số chia phải bằng số bị chia.',f'({fmt(result)})*{B}',A,f'Phép kiểm cho {display(A)}, đúng số bị chia.'))
 else:
  reason='Không có số nào nhân với 0 được số bị chia khác 0.' if a else 'Mọi số nhân với 0 đều bằng 0, nên không xác định được duy nhất một thương.'
  ss.append(st('Kiểm số chia','Phép chia cần số chia khác không.',None,'phép chia không xác định',f'{display(B)} có giá trị bằng 0. {reason} Không ghi một thương số học.'))
 for i,s in enumerate(ss):s['step_id']=f's{i}'
 sigs=[]
 for ex in ([f'{A}{op}{B}'] if op!='invalid_division' else [])+[s['expression'] for s in ss if s['expression']]:
  h=signature(ex)
  if h not in sigs:sigs.append(h)
 sid=f"decimal_v1_{ {'+':'add','-':'sub','*':'mul','/':'div','invalid_division':'divzero'}[op]}_{a}_10_{b}_10"
 hs=hints(op);scope='ENRICHMENT_NONTERMINATING_DECIMAL_QUOTIENT_EXACT_FRACTION' if result is not None and not finite(result) else 'CURRENT_G5_DECIMAL_NUMERIC_REFERENCE'
 return {'sample_id':sid,'case_group_id':'math_'+(sigs[0] if sigs else g.digest(sid.encode())),'case_kind':'invalid_operation_recognition' if result is None else 'worked_decimal_arithmetic','grade':5,'split':'train_candidate','topic':'decimal_'+str(op),'problem':problem,'givens':[{'id':'g0','text':'Số thứ nhất','value':A,'unit':''},{'id':'g1','text':'Số thứ hai','value':B,'unit':''}],'requested_quantity':'Kết quả chính xác và cách kiểm' if result is not None else 'Kiểm tính xác định của phép chia','student_work':None,'initial_guidance':[hs[0]['hint']],'hints':hs,'worked_steps':ss,'expected_answer':[{'quantity':'Kết quả' if result is not None else 'Tính xác định','result':fmt(result) if result is not None else 'không xác định vì số chia bằng 0','unit':''}],'can_solve':True,'quality_status':'ACCEPTED_VALIDATED','acceptance_status':'ACCEPTED_OWNER_PREAUTHORIZED','provenance':{'generation_method':'DETERMINISTIC_DECIMAL_TEMPLATE_EXACT_FRACTION_ORACLE','version':VERSION,'human_verified':False,'teacher_certified':False,'owner_human_reviewed':False,'human_content_review_completed':False,'accuracy_score':None,'origin_is_not_low_accuracy_evidence':True},'coverage':{'mode':'EXHAUSTIVE','domain':'21inputrepresentations_k_over10_k0to20','operation':op,'ordered_input_indices':[a,b],'input_decimal_representations':[A,B],'curriculum_scope':scope,'not_full_decimal_curriculum':True},'canonical_signatures':sigs}
def verify(r,op,a,b):
 assert r['coverage']['ordered_input_indices']==[a,b] and [g['value'] for g in r['givens']]==[text(a),text(b)] and r['hints']==hints(op)
 x,y=Fraction(a,10),Fraction(b,10)
 if op=='invalid_division':assert b==0 and r['expected_answer'][0]['result']=='không xác định vì số chia bằng 0'
 else:
  z=Fraction(a+b,10) if op=='+' else Fraction(a-b,10) if op=='-' else Fraction(a*b,100) if op=='*' else Fraction(a,b)
  assert Fraction(r['expected_answer'][0]['result'])==z
  with localcontext() as ctx:
   ctx.prec=60;da,db=Decimal(text(a)),Decimal(text(b));dz=da+db if op=='+' else da-db if op=='-' else da*db if op=='*' else da/db
   assert abs(dz-Decimal(z.numerator)/Decimal(z.denominator))<=Decimal('1e-55')
  assert (z-y==x if op=='+' else z+y==x if op=='-' else (z/y==x if y else z==0) if op=='*' else z*y==x)
 for s in r['worked_steps']:
  if s['expression']:assert exact(s['expression'])==Fraction(s['result']) and signature(s['expression']) in r['canonical_signatures']
 assert r['initial_guidance']==[hints(op)[0]['hint']] and not r['provenance']['human_verified']
def show():
 for op,a,b in [('+',1,2),('-',20,19),('*',3,4),('*',0,0),('/',1,3),('/',10,4),('/',0,20),('invalid_division',0,0),('invalid_division',20,0)]:
  r=make(op,a,b);print(g.dumps([r['sample_id'],r['problem'],r['initial_guidance'],r['hints'],r['worked_steps'],r['expected_answer']]))
def run():
 qa=g.load(g.EVIDENCE/'decimal_template_self_QA.json');assert qa['generator_sha256']==g.filehash(__file__) and qa['status']=='PASSED'
 protected=set(g.load(g.ROOT/'protected_numeric_signatures.json')['signatures']);man=[];views=[];ids=set();counts={}
 for op in OPS:
  label={'+':'addition','-':'subtraction','*':'multiplication','/':'division','invalid_division':'division_zero'}[op];dest=ROOT/'corpus'/f'{label}.jsonl.gz';vp=ROOT/'training_views'/dest.name;dest.parent.mkdir(parents=True,exist_ok=True);vp.parent.mkdir(parents=True,exist_ok=True);expected=pairs(op)
  if not dest.exists():
   with g.gzopen(dest.with_suffix('.partial.gz'),'wt') as out:
    for a,b in expected:out.write(g.dumps(make(op,a,b))+'\n')
   dest.with_suffix('.partial.gz').replace(dest)
  actual=[];kept=excluded=0;chatcount=0
  with g.gzopen(vp.with_suffix('.partial.gz'),'wt') as out:
   for r in g.gzrows(dest):
    a,b=r['coverage']['ordered_input_indices'];verify(r,op,a,b);actual.append((a,b));assert r['sample_id'] not in ids;ids.add(r['sample_id'])
    if set(r['canonical_signatures'])&protected:excluded+=1;continue
    kept+=1
    for c in g.chat_records(r):out.write(g.dumps(c)+'\n');chatcount+=1
  assert actual==expected and len(set(actual))==len(expected)
  assert sum(1 for _ in g.gzrows(vp.with_suffix('.partial.gz')))==chatcount==kept*4
  vp.with_suffix('.partial.gz').replace(vp)
  m={'operation':op,'path':str(dest.relative_to(ROOT)),'sha256':g.filehash(dest),'bytes':dest.stat().st_size,'expected_pairs':len(expected),'validated_pairs':len(actual),'missing_pairs':0,'status':'COMPLETED'};g.save(dest.with_suffix('.manifest.json'),m);man.append(m)
  v={'path':str(vp.relative_to(ROOT)),'sha256':g.filehash(vp),'bytes':vp.stat().st_size,'source_sha256':m['sha256'],'included_cases':kept,'excluded_cases_preserved':excluded,'chat_rows':chatcount,'status':'COMPLETED'};g.save(vp.with_suffix('.manifest.json'),v);views.append(v);counts[op]=len(expected)
 assert counts=={'+':441,'-':231,'*':441,'/':420,'invalid_division':21} and len(ids)==1554
 state={'schema_version':VERSION,'status':'COMPLETED_DECLARED_DECIMAL_GRID','utc':g.utc(),'cases':1554,'operation_counts':counts,'input_representations':21,'missing_pairs':0,'source_manifests':man,'view_manifests':views,'chat_rows':sum(v['chat_rows'] for v in views),'excluded_cases_preserved':sum(v['excluded_cases_preserved'] for v in views),'generator_sha256':g.filehash(__file__),'nonterminating_results_exact_fraction_no_rounding':True,'not_full_decimal_curriculum':True,'training_started':False}
 g.save(ROOT/'decimal_build_state.json',state);print(g.dumps(state))
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='show':show()
 else:run()

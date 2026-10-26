"""Append-only exhaustive arithmetic corpus. No model calls, training or source rewriting.

Physical shells contain each ordered pair once; logical 0..N domains compose
shells. All cases survive training-view exclusions. Atomic immutable gzip shards
are independently reopened to verify the actual ordered pair coverage.
"""
from __future__ import annotations
import argparse,ast,gzip,hashlib,inspect,io,json,math,os,shutil,subprocess,time
from contextlib import contextmanager
from collections import Counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from fractions import Fraction
import exhaustive_curriculum_scope as curriculum_scope

HERE=Path(__file__).resolve().parent
ROOT=HERE/'data/exhaustive_math_v1'
EVIDENCE=HERE/'evidence/exhaustive_math_20261018'
VERSION='exhaustive_primary_math.v1'
TEMPLATE_VERSION='observable_arithmetic_teaching.v1'
PLACES=['đơn vị','chục','trăm','nghìn','chục nghìn','trăm nghìn','triệu']
def utc():return datetime.now(timezone.utc).isoformat()
def dumps(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def digest(x):return hashlib.sha256(x).hexdigest()
def filehash(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text('utf-8'))
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.atomic');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf-8')
 # Windows readers/scanners may briefly hold the old inode without delete
 # sharing. Retain the complete atomic file and retry; never fall back to an
 # in-place partial write or overwrite committed corpus shards.
 for attempt in range(40):
  try:t.replace(p);return
  except PermissionError:
   if attempt==39:raise
   time.sleep(min(0.005*(attempt+1),0.1))
@contextmanager
def gzopen(p,mode='rt'):
 if mode=='rt':
  with gzip.open(p,mode,encoding='utf-8',newline='\n') as f:yield f
 else:
  with open(p,'wb') as raw:
   with gzip.GzipFile(filename='',mode='wb',fileobj=raw,compresslevel=1,mtime=0) as binary:
    with io.TextIOWrapper(binary,encoding='utf-8',newline='\n') as f:yield f
def gzrows(p):
 with gzopen(p) as f:
  for l in f:yield json.loads(l)
def numeric_group(op,a,b):
 # Identical to the existing v4 bounded arithmetic signature for two constants.
 children=[('n',str(a)),('n',str(b))]
 if op in ('+','*'):children.sort(key=repr)
 return digest(repr((op,*children)).encode())
def expression_group(expression):
 def walk(n):
  if isinstance(n,ast.Constant) and type(n.value) is int:return ('n',str(n.value))
  if not isinstance(n,ast.BinOp):raise ValueError('unapproved expression')
  op={ast.Add:'+',ast.Sub:'-',ast.Mult:'*',ast.Div:'/',ast.Mod:'%'}[type(n.op)];children=[walk(n.left),walk(n.right)]
  if op in ('+','*'):
   parts=[]
   for c in children:parts.extend(c[1:]) if c[0]==op else parts.append(c)
   return (op,*sorted(parts,key=repr))
  return (op,*children)
 return digest(repr(walk(ast.parse(expression,mode='eval').body)).encode())
def exact_expression(expression):
 def walk(n):
  if isinstance(n,ast.Constant) and type(n.value) is int:return Fraction(n.value)
  if not isinstance(n,ast.BinOp):raise ValueError('unapproved expression')
  a,b=walk(n.left),walk(n.right)
  if isinstance(n.op,ast.Add):return a+b
  if isinstance(n.op,ast.Sub):return a-b
  if isinstance(n.op,ast.Mult):return a*b
  if isinstance(n.op,ast.Div):return a/b
  raise ValueError('unsupported worked calculator operation')
 return walk(ast.parse(expression,mode='eval').body)
def addition_columns(a,b):
 carry=0;answer=0;trace=[];place=1;i=0;carries=[]
 while place<=max(a,b) or carry or not trace:
  x=a//place%10;y=b//place%10;incoming=carry;total=x+y+incoming;digit=total%10;carry=total//10
  answer+=digit*place
  trace.append(f'Hàng {PLACES[i]}: {x} + {y}'+(f' + {incoming} (nhớ từ hàng trước)' if incoming else '')+f' = {total}; ghi {digit} ở hàng {PLACES[i]}'+(f', nhớ {carry} sang hàng kế tiếp.' if carry else ', không còn nhớ.'))
  if carry:carries.append(i)
  place*=10;i+=1
 return answer,trace,carries
def subtraction_columns(a,b):
 assert a>=b
 digits=[int(d) for d in reversed(str(a))];width=max(len(str(a)),len(str(b)));digits += [0]*(width-len(digits))
 answer=0;trace=[];borrows=[]
 for i in range(width):
  y=b//10**i%10;prefix=f'Hàng {PLACES[i]}'
  if digits[i]<y:
   j=i+1
   while digits[j]==0:j+=1
   donor=digits[j];digits[j]-=1
   updates=[f'hàng {PLACES[j]} từ {donor} còn {digits[j]}']
   for k in range(j-1,i,-1):digits[k]=9;updates.append(f'hàng {PLACES[k]} nhận 10 rồi chuyển 1 cho hàng liền thấp, còn 9')
   digits[i]+=10;updates.append(f'hàng {PLACES[i]} thành {digits[i]}')
   prefix+=' chưa đủ bớt; đổi nhóm từ hàng cao hơn gần nhất còn đơn vị để đổi: '+ '; '.join(updates)
   borrows.extend(range(i,j))
  digit=digits[i]-y;answer+=digit*10**i
  trace.append(prefix+f'; {digits[i]} − {y} = {digit}, ghi {digit}.')
 return answer,trace,borrows
def step(title,reason,expr,result,explanation,unit=''):
 return {'step_id':'s0','title':title,'reason':reason,'expression':expr,'result':str(result),'unit':unit,'explanation':explanation}
def hints(op):
 text={
 '+':[('Xác định hai số hạng và đặt các chữ số cùng hàng thẳng cột.','Em nên bắt đầu cộng từ hàng nào?'),('Cộng theo từng hàng; một nhóm đủ mười được đổi sang hàng kế tiếp.','Ở hàng đang xét, có phần nhớ từ hàng trước cần cộng cùng không?'),('Sau khi ghi các hàng, dùng phép trừ để kiểm tổng.','Lấy kết quả bớt một số hạng có trở lại số hạng kia không?')],
 '-':[('Xác định số bị trừ, số trừ và đặt các chữ số cùng hàng thẳng cột.','Em nên bắt đầu bớt từ hàng nào?'),('Nếu một hàng chưa đủ bớt, đổi nhóm từ hàng cao hơn và cập nhật hàng cho đi.','Số lượng ở hàng đang xét có đủ để bớt số đã cho không?'),('Sau khi tính, cộng hiệu với số trừ để kiểm số bị trừ.','Phép kiểm của em có khôi phục số ban đầu không?')],
 '*':[('Xác định số nhóm bằng nhau và lượng trong mỗi nhóm.','Có thể dùng phép nhân hoặc cộng lặp để biểu diễn tổng như thế nào?'),('Dựa vào bảng nhân hoặc tách một thừa số thành các phần dễ tính.','Các phần em chọn có gộp lại đúng thừa số ban đầu không?'),('Kiểm bằng cộng lặp; khi có thừa số khác không có thể kiểm thêm bằng chia.','Phép kiểm có dùng đủ các nhóm và xử lý đúng trường hợp có số không không?')],
 '/':[('Xác định số bị chia và số chia trước khi lập các nhóm đủ.','Số chia có khác không để phép chia có nghĩa không?'),('Tìm số nhóm đủ; phần còn lại cần nhỏ hơn lượng trong một nhóm.','Nếu còn lập thêm được một nhóm đủ, thương đã là thương cuối chưa?'),('Nhân thương với số chia rồi cộng phần dư để kiểm.','Phép kiểm có khôi phục số bị chia và phần dư có nhỏ hơn số chia không?')],
 'invalid_division':[('Kiểm điều kiện của số chia trước khi tính.','Số chia trong biểu thức đã đáp ứng điều kiện để phép chia xác định chưa?'),('Thử đối chiếu với quan hệ phép nhân ngược.','Quan hệ ngược có xác định được đúng một thương không?'),('Đối chiếu điều kiện của phép chia với quan hệ nhân trước khi kết luận.','Em có thể nêu căn cứ cho nhận xét mà không tự đổi số chia không?')]}
 return [{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(text[op])]

def make_row(op,a,b,shell):
 assert type(a) is int and type(b) is int and a>=0 and b>=0
 if op=='*':assert max(a,b)<=10,'Multi-digit multiplication template is not yet reviewed'
 kind='worked_arithmetic';unit='';expr=f'{a}{op}{b}';provenance={'generation_method':'DETERMINISTIC_EXACT_ARITHMETIC_WITH_REVIEWED_TEACHING_TEMPLATE','generator_version':VERSION,'template_version':TEMPLATE_VERSION,'acceptance_basis':'OWNER_AUTHORIZED_VALIDATION','authorship_origin':'PROGRAMMATIC_TEMPLATE','human_content_review_completed':False,'human_verified':False,'teacher_certified':False,'independent_external_review':False,'accuracy_score':None,'accuracy_score_reason':'No empirical accuracy estimate assigned; origin is not a low-quality label.'}
 if op=='+':
  result,trace,carries=addition_columns(a,b);assert result==a+b and result-b==a and result-a==b
  grade=1 if result<=20 or (result<=100 and not carries) else 2 if result<=1000 else 3
  subtype='addition_with_carry' if carries else 'addition_no_carry'
  problem=f'Tính {a} + {b}. Giải thích cách cộng theo hàng và kiểm lại kết quả.'
  steps=[step('Cộng hai số hạng','Hai số hạng cho biết hai lượng cần gộp; cộng các chữ số cùng hàng, bắt đầu từ hàng thấp.',expr,result,' '.join(trace)+f' Vậy {a} + {b} = {result}.')]
  steps.append(step('Kiểm bằng phép trừ','Bớt một số hạng khỏi tổng phải còn số hạng kia.',f'{result}-{b}',a,f'{result} − {b} = {a}; kiểm thêm {result} − {a} = {b}.'))
  answer=[{'quantity':'Tổng','result':str(result),'unit':''}];canonical=[numeric_group('+',a,b)];flags={'carry_positions':carries}
 elif op=='-':
  result,trace,borrows=subtraction_columns(a,b);assert result==a-b and result+b==a
  grade=1 if a<=100 and not borrows else 2 if a<=1000 else 3
  subtype='subtraction_with_borrow' if borrows else 'subtraction_no_borrow'
  problem=f'Tính {a} − {b}. Giải thích cách bớt theo hàng và kiểm lại kết quả.'
  steps=[step('Trừ theo từng hàng','Tìm phần còn lại khi bớt số trừ khỏi số bị trừ; giữ giá trị số bị trừ khi đổi nhóm.',expr,result,' '.join(trace)+f' Vậy {a} − {b} = {result}.')]
  steps.append(step('Kiểm bằng phép cộng','Hiệu cộng số trừ phải bằng số bị trừ.',f'{result}+{b}',a,f'{result} + {b} = {a}, đúng số bị trừ.'))
  answer=[{'quantity':'Hiệu','result':str(result),'unit':''}];canonical=[numeric_group('-',a,b)];flags={'borrow_positions':borrows}
 elif op=='*':
  repeated=sum(a for _ in range(b));result=a*b;assert result==repeated
  grade=2 if a in (2,5) and b<=10 else 3
  subtype='multiplication_table';problem=f'Tính {a} × {b}. Giải thích bằng các nhóm bằng nhau và kiểm lại.'
  why=f'Có thể xem phép tính là {b} nhóm, mỗi nhóm {a} đơn vị.'
  explanation=(f'Có {b} nhóm cùng chứa {a} đơn vị. Cộng lượng của các nhóm được {result}.' if b else 'Không có nhóm nào nên tổng lượng bằng không.')
  steps=[step('Tìm tích',why,expr,result,explanation+f' Vì vậy {a} × {b} = {result}.')]
  check=f'Cộng {a} lặp lại {b} lần được {result}.' if b else 'Không cộng nhóm nào được 0, phù hợp không có nhóm.'
  if a:check+=f' Kiểm thêm {result} : {a} = {b}.'
  elif b:check+=f' Kiểm thêm {result} : {b} = {a}.'
  steps.append(step('Kiểm bằng nhóm bằng nhau','Cộng đủ số nhóm là cách đối chiếu độc lập với phép nhân.',None,result,check))
  answer=[{'quantity':'Tích','result':str(result),'unit':''}];canonical=[numeric_group('*',a,b)];flags={}
 elif op=='/':
  assert b>0;q,r=divmod(a,b);assert b*q+r==a and 0<=r<b
  # Separate repeated-group oracle, bounded to <=1000 for the current tier.
  remaining=a;count=0
  while remaining>=b:remaining-=b;count+=1
  assert (count,remaining)==(q,r)
  grade=3;subtype='division_exact' if r==0 else 'division_remainder'
  problem=f'Chia {a} cho {b}. Tìm thương và số dư, giải thích vì sao không lập thêm được nhóm đủ, rồi kiểm lại.'
  steps=[step('Lập các nhóm đủ','Mỗi nhóm chứa đúng số chia đơn vị; thương đếm các nhóm đủ, phần còn lại là số dư.',None,q,f'Lập được {q} nhóm, mỗi nhóm {b} đơn vị, dùng {q*b} đơn vị và còn {r}. Phần còn {r} bé hơn {b} nên không lập thêm được nhóm đủ.')]
  steps.append(step('Kiểm số bị chia và số dư','Thương nhân số chia cộng số dư phải khôi phục số bị chia; số dư không âm và nhỏ hơn số chia.',f'{q}*{b}+{r}',a,f'{q} × {b} + {r} = {a}; 0 ≤ {r} < {b}. Vậy thương là {q}, số dư là {r}.'))
  answer=[{'quantity':'Thương','result':str(q),'unit':''},{'quantity':'Số dư','result':str(r),'unit':''}];canonical=[numeric_group('%',a,b)];flags={'quotient':q,'remainder':r,'modulo_oracle_metadata_only':f'{a}%{b}'}
  if r==0:canonical.append(numeric_group('/',a,b))
 else:
  assert op=='invalid_division' and b==0
  grade=3;subtype='division_by_zero_recognition';kind='invalid_operation_recognition';result=None
  problem=f'Có thể tính {a} : 0 và ghi một thương xác định không? Hãy kiểm điều kiện của phép chia và giải thích.'
  reason=(f'Mọi số nhân với 0 đều bằng 0 nên không có số nào nhân 0 được {a}.' if a else 'Mọi số nhân với 0 đều bằng 0 nên quan hệ nhân ngược không xác định được đúng một thương.')
  steps=[step('Kiểm điều kiện phép chia','Phép chia phải có số chia khác không.',None,'phép chia không xác định',reason+' Vì vậy không ghi một thương số học cho phép chia này.')]
  answer=[{'quantity':'Tính xác định của phép chia','result':'không xác định vì số chia bằng 0','unit':''}];canonical=[];flags={'invalid_division_not_numeric_answer':True}
 hs=hints(op)
 scope=curriculum_scope.classify(op,a,b,flags)
 if op in ('+','-'):assert scope['supplied_positions_match'] is True
 grade=scope['grade']
 for i,s in enumerate(steps):s['step_id']=f's{i}'
 for s in steps:
  if s['expression']:
   sig=expression_group(s['expression'])
   if sig not in canonical:canonical.append(sig)
 symbol={'+':'add','-':'sub','*':'mul','/':'div','invalid_division':'divzero'}[op]
 sid=f'exhaustive_v1_{symbol}_{a}_{b}'
 primarygroup=canonical[0] if canonical else digest(f'invalid/{a}/{b}'.encode())
 return {'sample_id':sid,'case_group_id':'math_'+primarygroup,'case_kind':kind,'split':'train_candidate','grade':grade,'topic':subtype,'problem':problem,'givens':[{'id':'g0','text':'Số thứ nhất','value':str(a),'unit':''},{'id':'g1','text':'Số thứ hai','value':str(b),'unit':''}],'requested_quantity':'; '.join(x['quantity'] for x in answer),'student_work':None,'initial_guidance':[hs[0]['hint']],'hints':hs,'worked_steps':steps,'expected_answer':answer,'can_solve':True,'quality_status':'ACCEPTED_VALIDATED','acceptance_status':'ACCEPTED_OWNER_PREAUTHORIZED','quality_validation':{'exact_integer_oracle':True,'independent_reconstruction_or_group_oracle':True,'reviewed_template_semantics':True,'every_row_human_or_LLM_review_claimed':False},'provenance':provenance,'curriculum_assignment':scope,'coverage':{'mode':'EXHAUSTIVE','physical_shell':shell,'ordered_input_pair':[a,b],'operation':op,'subtype':subtype,'semantic_curriculum_confirmation':'HASH_BOUND_CURRENT_REFERENCE_OR_EXPLICIT_ENRICHMENT','minimum_grade_for_this_representation':grade},'canonical_signatures':canonical,'operation_metadata':flags}

def chat_records(row):
 for mode in ('worked_solution','hint_level_1','hint_level_2','hint_level_3'):
  p={'grade':row['grade'],'problem':row['problem'],'mode':mode}
  if row.get('student_work'):p['student_work']=row['student_work']['text']
  if mode=='worked_solution':target={'can_solve':row['can_solve'],'initial_guidance':row['initial_guidance'],'steps':row['worked_steps'],'answer':row['expected_answer']}
  else:h=row['hints'][int(mode[-1])-1];target={'hint':h['hint'],'question':h['question']}
  yield {'sample_id':row['sample_id']+':'+mode,'case_group_id':row['case_group_id'],'grade':row['grade'],'topic':row['topic'],'mode':mode,'split':'train','schema':'neutral_teacher_chat.v1_not_live_PlanDraft','messages':[{'role':'system','content':'Bạn là gia sư Toán tiểu học. Trả lời bằng tiếng Việt theo yêu cầu. Chỉ đưa lời giải đầy đủ khi được yêu cầu; gợi ý không điền đáp số. Chỉ nhận xét lời làm thực sự được cung cấp.'},{'role':'user','content':dumps(p)},{'role':'assistant','content':dumps(target)}],'source_sample_id':row['sample_id'],'quality_status':'ACCEPTED_VALIDATED','acceptance_status':'ACCEPTED_OWNER_PREAUTHORIZED','human_verified':False,'teacher_certified':False,'provenance':row['provenance']}

def expected(op,n):
 if op=='+':return (n+1)**2
 if op=='-':return (n+1)*(n+2)//2
 if op=='*':return (n+1)**2
 if op=='/':return (n+1)*min(9,n)
 if op=='invalid_division':return n+1
 raise ValueError(op)
def shell_count(op,n,prev):return expected(op,n)-(expected(op,prev) if prev>=0 else 0)
def pairs(op,n,prev,a0=0,a1=None):
 for a in range(a0,min(n+1,a1 if a1 is not None else n+1)):
  bs=range(a+1) if op=='-' else range(1,min(9,n)+1) if op=='/' else (0,) if op=='invalid_division' else range(n+1)
  for b in bs:
   # Division shells extend dividend only; multiplication/addition use square shells.
   isold=(a<=prev and b<=min(9,prev)) if op=='/' else (a<=prev) if op=='invalid_division' else max(a,b)<=prev
   if not isold:yield a,b
def name(op,n,prev):return {'+':'addition','-':'subtraction','*':'multiplication','/':'division_by_1_9','invalid_division':'division_by_zero'}[op]+f'_shell_{prev+1}_{n}'
def read_protection_index():
 p=ROOT/'protected_numeric_signatures.json'
 assert p.exists(),'Generate source fingerprints-only protection index before training views'
 x=load(p);return set(x['signatures']),x
def write_shard(job):
 op,n,prev,a0,a1=job;domain=name(op,n,prev);folder=ROOT/'corpus'/domain;folder.mkdir(parents=True,exist_ok=True)
 dest=folder/f'a_{a0:06d}_{a1-1:06d}.jsonl.gz';mp=dest.with_suffix('.manifest.json')
 if mp.exists():
  m=load(mp);assert dest.exists() and filehash(dest)==m['sha256'] and m['template_version']==TEMPLATE_VERSION and m['template_sha256']==template_fingerprint() and (m['operation'],m['maximum'],m['previous_maximum'],m['a_start'],m['a_stop_exclusive'])==job;return m|{'reused':True}
 # An orphaned complete shard is recoverable by readback; a .partial file is
 # never a committed shard and is overwritten only inside this exact job path.
 tmp=dest.with_suffix('.partial.gz');start=time.monotonic();grades=Counter();topics=Counter();cnt=0
 working=dest if dest.exists() else tmp
 if not dest.exists():
  if tmp.exists():
   preserved=EVIDENCE/'interrupted_partial_shards'/(dom_safe(domain)+'_'+tmp.stem+'_'+filehash(tmp)[:16]+'.gz');preserved.parent.mkdir(parents=True,exist_ok=True)
   if not preserved.exists():shutil.copyfile(tmp,preserved)
  with gzopen(tmp,'wt') as f:
   for a,b in pairs(op,n,prev,a0,a1):
    row=make_row(op,a,b,domain);f.write(dumps(row)+'\n');cnt+=1
 # Validate the ACTUAL rows against an independently iterated expected sequence.
 gen=pairs(op,n,prev,a0,a1);validated=0;content=hashlib.sha256()
 for row in gzrows(working):
  a,b=next(gen);assert row['coverage']['ordered_input_pair']==[a,b]
  assert row['sample_id']==make_id(op,a,b)
  assert row['coverage']['operation']==op
  verify_answer(row,op,a,b);content.update((row['sample_id']+'\n').encode());validated+=1;grades[str(row['grade'])]+=1;topics[row['topic']]+=1
 assert next(gen,None) is None and (working==dest or validated==cnt)
 cnt=validated
 if working==tmp:tmp.replace(dest)
 m={'domain':domain,'operation':op,'maximum':n,'previous_maximum':prev,'a_start':a0,'a_stop_exclusive':a1,'rows':cnt,'validated_rows':validated,'actual_pair_sequence_sha256':content.hexdigest(),'pair_coverage_proof':'Every parsed ordered pair and deterministic ID compared in order to complete expected generator; exact row count and no missing/trailing pairs.','path':str(dest.relative_to(ROOT)),'sha256':filehash(dest),'bytes':dest.stat().st_size,'grades':dict(grades),'topics':dict(topics),'seconds':round(time.monotonic()-start,3),'quality_status':'ACCEPTED_VALIDATED','template_version':TEMPLATE_VERSION,'template_sha256':template_fingerprint(),'status':'COMPLETED','reused':False}
 save(mp,m);return m
def dom_safe(x):return ''.join(c if c.isalnum() or c in '_-' else '_' for c in x)
def make_id(op,a,b):
 symbol={'+':'add','-':'sub','*':'mul','/':'div','invalid_division':'divzero'}[op]
 return f'exhaustive_v1_{symbol}_{a}_{b}'
def verify_answer(row,op,a,b):
 assert row['sample_id']==make_id(op,a,b)
 assert [g['value'] for g in row['givens']]==[str(a),str(b)]
 assert row['coverage']['operation']==op and row['coverage']['ordered_input_pair']==[a,b]
 assert row['hints']==hints(op) and row['initial_guidance']==[hints(op)[0]['hint']]
 assert row['can_solve'] is True and row['provenance']['template_version']==TEMPLATE_VERSION
 scope=curriculum_scope.classify(op,a,b,row['operation_metadata'])
 assert row['curriculum_assignment']==scope and row['grade']==scope['grade']
 ans=row['expected_answer']
 if op=='+':assert int(ans[0]['result'])==a+b
 elif op=='-':assert a>=b and int(ans[0]['result'])==a-b
 elif op=='*':assert int(ans[0]['result'])==a*b
 elif op=='/':
  assert (int(ans[0]['result']),int(ans[1]['result']))==divmod(a,b)
  assert int(row['worked_steps'][0]['result'])==a//b and row['operation_metadata']['modulo_oracle_metadata_only']==f'{a}%{b}'
 else:assert b==0 and ans[0]['result']=='không xác định vì số chia bằng 0' and all(s['expression'] is None for s in row['worked_steps'])
 for s in row['worked_steps']:
  if s['expression']:assert exact_expression(s['expression'])==Fraction(s['result']) and expression_group(s['expression']) in row['canonical_signatures']
 if op!='invalid_division':assert numeric_group('%' if op=='/' else op,a,b) in row['canonical_signatures']
 assert len(row['hints'])==3 and [h['level'] for h in row['hints']]==[1,2,3]
 assert not row['provenance']['human_content_review_completed']
def template_fingerprint():
 return digest((''.join(inspect.getsource(f) for f in (make_row,hints,addition_columns,subtraction_columns,chat_records))+TEMPLATE_VERSION+filehash(curriculum_scope.__file__)).encode())

def update_state():
 completed=[load(p) for p in sorted((ROOT/'corpus').rglob('*.manifest.json'))];domains={}
 for m in completed:
  d=domains.setdefault(m['domain'],{'status':'IN_PROGRESS','expected_pairs':shell_count(m['operation'],m['maximum'],m['previous_maximum']),'generated_pairs':0,'validated_pairs':0,'shards':[],'operation':m['operation'],'maximum':m['maximum'],'previous_maximum':m['previous_maximum']})
  d['generated_pairs']+=m['rows'];d['validated_pairs']+=m['validated_rows'];d['shards'].append(m)
 for d in domains.values():
  intervals=sorted((m['a_start'],m['a_stop_exclusive']) for m in d['shards'])
  assert all(left[1]<=right[0] for left,right in zip(intervals,intervals[1:])),'overlapping shard partitions'
  d['missing_pairs']=d['expected_pairs']-d['validated_pairs'];assert d['missing_pairs']>=0
  if not d['missing_pairs']:d['status']='COMPLETED'
 for op in ('+','-','*','/','invalid_division'):
  shells=sorted((d['previous_maximum']+1,d['maximum']) for d in domains.values() if d['operation']==op)
  assert all(x[1]<y[0] for x,y in zip(shells,shells[1:])),'overlapping numeric shells'
 logical=[]
 for op in ('+','-','*','/','invalid_division'):
  for n in (10,20,100,1000,10000,100000):
   if op=='*' and n not in (10,100,1000,10000,100000):continue
   actual=sum(d['validated_pairs'] for d in domains.values() if d['operation']==op and d['maximum']<=n)
   total=expected(op,n)
   logical.append({'domain':name(op,n,-1),'coverage_mode':'EXHAUSTIVE','expected_pairs':total,'generated_pairs':actual,'validated_pairs':actual,'missing_pairs':total-actual,'status':'COMPLETED' if actual==total else 'IN_PROGRESS' if actual else 'NOT_STARTED','ordered_pairs':True,'maximum':n,'operation':op,'physical_shells':[k for k,d in domains.items() if d['operation']==op and d['maximum']<=n],'expected_corpus_bytes_estimate':total*3700,'expected_chat_bytes_estimate':total*4*2200,'arithmetic_bounds_not_full_curricular_certification':True})
 views=[load(p) for p in (ROOT/'training_views').rglob('*.manifest.json')] if (ROOT/'training_views').exists() else []
 grades=Counter();topics=Counter()
 for m in completed:grades.update(m['grades']);topics.update(m['topics'])
 state={'schema_version':VERSION,'updated_utc':utc(),'status':'IN_PROGRESS','baseline_primary_cases':782,'baseline_primary_chat_rows':3128,'new_generated_cases':sum(m['rows'] for m in completed),'new_validated_accepted_cases':sum(m['validated_rows'] for m in completed),'full_corpus_new_cases_preserved':sum(m['rows'] for m in completed),'new_materialized_chat_rows':sum(m['chat_rows'] for m in views),'protected_overlap_cases_preserved_outside_new_training_view':sum(m['excluded_from_this_training_view_cases'] for m in views),'by_grade':dict(grades),'by_topic':dict(topics),'physical_shells':domains,'logical_domains':logical,'generator_sha256':filehash(__file__),'training_started':False,'no_accuracy_penalty_based_on_origin':True,'existing_sources_deleted_or_reclassified':False,'remaining_domain_policy':'All ungenerated ranges remain NOT_STARTED or IN_PROGRESS with exact missing counts and capacity estimates. No completion claim for entire 0..100000 grid or infinite word problems.'}
 save(ROOT/'data_build_state.json',state);return state
def run(op,n,prev,workers=2,width=25):
 storage=HERE/'exhaustive_cloud_storage_policy.json'
 if storage.exists() and load(storage).get('cloud_only'):
  raise RuntimeError('Owner requires cloud-only data storage. Bulk local generation is disabled; resume only with bounded temporary shards, verified Drive publication and remote checkpoint.')
 assert load(EVIDENCE/'preservation_audit_summary.json')['status'].startswith('PASS')
 catalog=load(ROOT/'template_catalog.json');assert catalog['template_QA_status']=='ACTUAL_TEMPLATE_QA_PASSED' and catalog['template_sha256']==template_fingerprint()
 assert -1<=prev<n and n<=100000
 if op=='*':assert n<=10,'Larger multiplication requires reviewed multi-digit teaching template, retained NOT_STARTED in plan'
 dom=name(op,n,prev);jobs=[(op,n,prev,a,min(n+1,a+width)) for a in range(0,n+1,width)]
 capacity=ROOT/'capacity_and_resume_plan.json'
 if capacity.exists():
  c=load(capacity)
  for estimate in c['future_ranges']:
   if (estimate['operation'],estimate['maximum'],estimate['previous_maximum'])==(op,n,prev):
    required=math.ceil(1.2*(estimate['estimated_source_gzip_bytes']+estimate['estimated_view_gzip_bytes']))
    free=shutil.disk_usage(ROOT).free
    if free<required:
     save(ROOT/'capacity_block.json',{'utc':utc(),'domain':dom,'status':'NOT_STARTED_RESOURCE_LIMIT','free_bytes':free,'estimated_corpus_plus_views_with20percent_margin':required,'source_or_existing_cases_modified':False,'next_pair':[0,prev+1] if op=='+' else [prev+1,0],'reason':'Workspace volume cannot hold this complete logical domain. Do not begin and silently abandon it or discard committed source shards.'})
     raise OSError(f'Capacity preflight: full domain needs approximately {required} bytes; workspace has {free}. No new shard started.')
 plan=ROOT/'plans'/f'{dom}.json';spec={'operation':op,'maximum':n,'previous_maximum':prev,'width':width,'jobs':[list(j) for j in jobs],'template_sha256':template_fingerprint()}
 if plan.exists():assert load(plan)==spec,'Partition plan or template changed; do not duplicate committed shards'
 else:
  for other in (ROOT/'plans').glob('*.json') if (ROOT/'plans').exists() else []:
   old=load(other)
   if old['operation']==op:assert n<old['previous_maximum']+1 or prev+1>old['maximum'],'Overlapping physical domain already declared'
  save(plan,spec)
 # Prohibit two managers processing the same domain concurrently.
 lock=ROOT/'locks'/f'{dom}.lock';lock.parent.mkdir(parents=True,exist_ok=True)
 if lock.exists():
  pid=int(lock.read_text('utf-8'))
  if os.name=='nt':
   status=subprocess.run(['tasklist','/FI',f'PID eq {pid}','/FO','CSV','/NH'],capture_output=True,text=True,check=True)
   alive=f'"{pid}"' in status.stdout
  else:
   try:os.kill(pid,0);alive=True
   except ProcessLookupError:alive=False
  assert not alive,'Another manager owns this domain; no concurrent overwrite'
  history=EVIDENCE/'stale_locks';history.mkdir(parents=True,exist_ok=True);shutil.copyfile(lock,history/(lock.stem+'_'+str(time.time_ns())+'.lock'));lock.unlink()
 fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
 try:
  with ProcessPoolExecutor(max_workers=workers) as ex:
   pending={ex.submit(write_shard,j):j for j in jobs}
   for f in as_completed(pending):
    m=f.result();state=update_state();print(dumps({'committed':m['domain'],'a':m['a_start'],'rows':m['rows'],'seconds':m['seconds'],'new_corpus_total':state['new_generated_cases'],'reused':m['reused']}),flush=True)
  state=update_state();assert state['physical_shells'][dom]['status']=='COMPLETED';return state
 finally:lock.unlink()
def build_views():
 storage=HERE/'exhaustive_cloud_storage_policy.json'
 if storage.exists() and load(storage).get('cloud_only'):
  raise RuntimeError('Owner requires cloud-only data storage. Bulk local view materialization is disabled; use verified remote shards.')
 protected,pi=read_protection_index();ROOT.joinpath('training_views').mkdir(parents=True,exist_ok=True)
 for m in [load(p) for p in sorted((ROOT/'corpus').rglob('*.manifest.json'))]:
  source=ROOT/m['path'];dest=ROOT/'training_views'/m['domain']/source.name;vp=dest.with_suffix('.manifest.json');dest.parent.mkdir(parents=True,exist_ok=True)
  if vp.exists():
   old=load(vp);assert old['source_sha256']==m['sha256'] and old['protection_index_sha256']==filehash(ROOT/'protected_numeric_signatures.json') and filehash(dest)==old['sha256'];continue
  tmp=dest.with_suffix('.partial.gz');included=excluded=chatcount=0;readback=0;start=time.monotonic()
  with gzopen(tmp,'wt') as out:
   for row in gzrows(source):
    if set(row['canonical_signatures'])&protected:excluded+=1;continue
    included+=1
    for c in chat_records(row):out.write(dumps(c)+'\n');chatcount+=1
  for c in gzrows(tmp):
   assert c['split']=='train' and len(c['messages'])==3 and c['mode'] in ('worked_solution','hint_level_1','hint_level_2','hint_level_3');readback+=1
  assert readback==chatcount==4*included and included+excluded==m['rows'];tmp.replace(dest)
  save(vp,{'path':str(dest.relative_to(ROOT)),'source_sha256':m['sha256'],'protection_index_sha256':filehash(ROOT/'protected_numeric_signatures.json'),'sha256':filehash(dest),'bytes':dest.stat().st_size,'source_cases':m['rows'],'included_cases':included,'excluded_from_this_training_view_cases':excluded,'excluded_cases_retained_in_full_corpus':True,'chat_rows':chatcount,'readback_validated_rows':readback,'seconds':round(time.monotonic()-start,3),'status':'COMPLETED','model_training_started':False})
  state=update_state();print(dumps({'view':m['domain'],'a':m['a_start'],'chat_rows':chatcount,'excluded_kept':excluded,'total_chat_rows':state['new_materialized_chat_rows']}),flush=True)

def init():
 storage=HERE/'exhaustive_cloud_storage_policy.json'
 if storage.exists() and load(storage).get('cloud_only'):
  raise RuntimeError('Cloud-only corpus already published; do not initialize a replacement local corpus.')
 ROOT.mkdir(parents=True,exist_ok=True)
 policy={'schema_version':'exhaustive_owner_acceptance.v1','utc':utc(),'authorization':'Direct owner request and attached preserve+exhaustive generation instructions 2026-10-18','accept_new_after_exact_and_template_QA':True,'ask_per_batch':False,'previous_accepted_labels_preserved':True,'quality_status':'ACCEPTED_VALIDATED','accuracy_score':None,'origin_is_not_evidence_of_low_accuracy':True,'future_human_manual_review_not_implied':True,'original_provenance_and_existing_owner_signoffs_unchanged':True,'new_data_not_added_to_old_frozen_blueprint_quota':True,'known_protected_overlap_preserved_in_corpus_excluded_from_new_views':True,'sealed_concept_test_not_read':True}
 p=ROOT/'owner_acceptance_policy.json'
 if not p.exists():save(p,policy)
 tp=ROOT/'template_catalog.json'
 if not tp.exists():save(tp,{'version':TEMPLATE_VERSION,'hints':{k:hints(k) for k in ('+','-','*','/','invalid_division')},'observable_worked_steps_not_private_reasoning':True,'template_QA_status':'PENDING_ACTUAL_TEMPLATE_REVIEW','accuracy_not_inferred_from_authorship':True})
 print(dumps({'root':str(ROOT),'policy':str(p),'state':update_state()['new_generated_cases']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['init','run','views','state']);p.add_argument('--op',default='+');p.add_argument('--max',type=int,default=10);p.add_argument('--prev',type=int,default=-1);p.add_argument('--workers',type=int,default=2);p.add_argument('--width',type=int,default=25);a=p.parse_args()
 if a.action=='init':init()
 elif a.action=='run':run(a.op,a.max,a.prev,a.workers,a.width)
 elif a.action=='views':build_views()
 else:print(dumps(update_state()))

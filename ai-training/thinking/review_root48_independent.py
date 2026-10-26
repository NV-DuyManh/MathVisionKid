from pathlib import Path
import ast,json,hashlib,itertools,re
from fractions import Fraction as F
from collections import deque
root=Path('thinking/cloud_publication/sgk_page_audit_20261019');p=root/'root_numeric/draft_before_concrete_content_repairs.jsonl'
raw=p.read_bytes();lines=raw.splitlines();rows=[json.loads(l) for l in lines]
def sha(b):return hashlib.sha256(b).hexdigest()
def val(s):
 s=s.strip()
 def ev(n):
  if isinstance(n,ast.Constant) and type(n.value) in (int,float):return F(ast.get_source_segment(s,n))
  if isinstance(n,ast.UnaryOp):return -ev(n.operand) if isinstance(n.op,ast.USub) else ev(n.operand)
  if isinstance(n,ast.BinOp):
   a,b=ev(n.left),ev(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,ast.Div):return a/b
  raise ValueError(ast.dump(n))
 return ev(ast.parse(s,mode='eval').body)
results=[];nexpr=0
for i,r in enumerate(rows,1):
 e=r['oracle_evidence'];k=e['kind'];ok=True
 if k=='abacus':
  ds=[d for d in itertools.product(range(10),repeat=4) if sum(d)==e['total']]; vs=[sum(x*10**(3-j) for j,x in enumerate(d)) for d in ds]; actual=(min if e['want']=='nhỏ nhất' else max)(vs);ok=actual==e['value']
 elif k=='successor':ok=e['n']+1==e['answer']
 elif k=='bounded_natural':ok=max(range(10**e['digits']))==e['answer']
 elif k=='delete':
  pairs=[(j+1,int(e['text'][:j]+e['text'][j+1:])) for j in range(5) if (e['text'][:j]+e['text'][j+1:])[0]!='0'];target=(min if e['want']=='nhỏ nhất' else max)(v for j,v in pairs);ok=target==e['result'] and [j for j,v in pairs if v==target]==e['positions']
 elif k=='digit_inequality':ok=[d for d in range(10) if (int(e['template'].replace('A',str(d)))<e['bound'] if e['rel']=='<' else int(e['template'].replace('A',str(d)))>e['bound'])]==e['digits']
 elif k=='global_cards':ok=[[a,b] for a,b in itertools.permutations(e['cards'],2) if e['left0']*10+a<e['right0'] and e['left1']*10+b>e['right1']]==e['pairs']
 elif k=='columns':
  left,right=e['puzzle'].replace('−','-').split('=');actual=[]
  for a,b in itertools.product(range(10),repeat=2):
   lhs=left.replace('A',str(a)).replace('B',str(b));nums=re.findall(r'\d+',lhs)
   if any(len(n)>1 and n[0]=='0' for n in nums):continue
   if val(lhs)==val(right):actual.append([a,b])
  ok=actual==e['pairs']
 elif k=='swap':
  queue=deque([(e['start'],0)]);seen={e['start']};distance=None
  while queue:
   s,d=queue.popleft()
   if s==e['target']:distance=d;break
   for a,b in itertools.combinations(range(len(s)),2):
    x=list(s);x[a],x[b]=x[b],x[a];t=''.join(x)
    if t not in seen:seen.add(t);queue.append((t,d+1))
  x=list(e['start'])
  for a,b in e['route']:x[a-1],x[b-1]=x[b-1],x[a-1]
  ok=distance==e['minimum'] and ''.join(x)==e['target'] and len(e['route'])==distance
 elif k=='insert_plus':
  s=e['digits'];actual=[j for j in range(1,len(s)) if not (len(s[j:])>1 and s[j]=='0') and int(s[:j])+int(s[j:])==e['total']];ok=actual==e['cuts']
 elif k=='prefix':ok=int(str(e['prefix'])+str(e['n']))-e['n']==e['difference']==e['prefix']*10**e['digits']
 elif k=='round_place':ok=[q for q in e['places'] if ((2*e['n']+q)//(2*q))*q==e['out']]==e['valid']
 elif k=='unit_pairs':
  f=F(e['fraction']);actual=[]
  # Positive distinct denominators a<b imply f<2/a. This gives exhaustive finite enumeration.
  for a in range(1,int(2/f)+1):
   rem=f-F(1,a)
   if rem>0 and rem.numerator==1 and rem.denominator>a:actual.append([a,rem.denominator])
  ok=actual==e['pairs']
 elif k=='integrality':
  values=[e['count']*F(f) for f in e['fractions']];ok=values==[F(v) for v in e['values']] and [v.denominator==1 and 0<=v<=e['count'] for v in values]==e['possible']
 elif k=='parameter':
  values=[val(x) for x in e['expressions']];ok=values==[F(x) for x in e['values']] and [m for m,v in zip(e['domain'],values) if v==max(values)]==e['args']
 elif k=='structural_arithmetic':ok=val(e['expression'])==F(e['value'])
 elif k=='reverse_error':ok=e['x']*sum(map(int,str(e['multiplier'])))==e['wrong'] and e['x']*e['multiplier']==e['correct']
 elif k=='numeral_filter':
  if e['variant']=='thousands_and_parity':actual=[n for n in e['numbers'] if n//10000%10==2 and n//10%10==0 and n%2==0]
  elif e['variant']=='class_pattern':actual=[n for n in e['numbers'] if n//1000%1000==42 and n%10==5]
  else:actual=[n for n in e['numbers'] if n//1000%10==5 and n//100%10==0 and n%2==0]
  ok=actual==e['result']
 else:raise ValueError(k)
 assert ok,(i,k)
 for s in r['worked_steps']:
  if s['expression'] is not None:
   assert val(s['expression'])==F(s['result']),(i,s)
   nexpr+=1
 results.append({'row_number':i,'sample_id':r['sample_id'],'source_row_sha256':sha(lines[i-1]),'independent_structure_oracle':'PASS','numeric_steps':'PASS','full_actual_requested_fields_read':True,'human_review_claimed':False})
issues={
2:[('pedagogy','MINOR','Smallest abacus s1 uses generic decreasing-priority statement; explicitly state moving any ring to a higher column increases value.')],
25:[('pedagogy','MINOR','Initial/hint1 phrasing about moving right in place value is confusing; old digits retain their place values.')],
26:[('pedagogy','MINOR','Initial/hint1 phrasing about moving right in place value is confusing; old digits retain their place values.')],
27:[('pedagogy','MINOR','Initial/hint1 phrasing about moving right in place value is confusing; old digits retain their place values.')],
31:[('grade_fit','REPAIR','Replace reciprocal inequalities in a with concrete denominator bounds understandable in grade4; show all candidate checks.')],
32:[('grade_fit','REPAIR','Replace reciprocal inequalities in a with concrete denominator bounds; explicitly check both returned pairs, not only first.')],
33:[('grade_fit','REPAIR','Replace reciprocal inequalities in a with concrete denominator bounds and excluded equal-denominator boundary.')],
34:[('presentation','REPAIR','Expected answer is Python boolean list; use Vietnamese A/B possibility phrases.')],
35:[('presentation','REPAIR','Expected answer is Python boolean list; use Vietnamese A/B possibility phrases.')],
36:[('presentation','REPAIR','Expected answer is Python boolean list; use Vietnamese A/B possibility phrases.')],
40:[('check_completeness','REPAIR','Problem requests separate numerator/denominator check but steps do not calculate them explicitly.')],
41:[('check_completeness','REPAIR','Problem requests separate numerator/denominator check but steps do not calculate them explicitly.')],
42:[('check_completeness','REPAIR','Problem requests separate numerator/denominator check but steps do not calculate them explicitly.')],
43:[('check_completeness','REPAIR','Show concrete substitution in the supplied wrong algorithm and tens-place correct decomposition; currently claims check without displaying it.')],
44:[('check_completeness','REPAIR','Show concrete substitution in supplied wrong algorithm and tens-place correct decomposition.')],
45:[('check_completeness','REPAIR','Show concrete substitution in supplied wrong algorithm and tens-place correct decomposition.')],
46:[('check_completeness','REPAIR','Problem asks why each rejected card fails; generic not-all-conditions label insufficient. Specify failing digit/condition for each.')],
47:[('check_completeness','REPAIR','Problem asks why each rejected card fails; generic label insufficient. Also remove unrelated even-number explanation for this nonparity row.')],
48:[('check_completeness','REPAIR','Problem asks why each rejected card fails; generic label insufficient. Specify failing digit/condition for each.')]}
for item in results:
 ix=item['row_number'];item['issues']=[dict(criterion=a,severity=b,detail=c) for a,b,c in issues.get(ix,[])];item['seven_criteria']={'math_correctness':'PASS','givens_request_consistency':'PASS','units':'PASS','grade_fit':'REPAIR' if ix in (31,32,33) else 'PASS','pedagogic_reason_and_check':'REPAIR' if any(x['criterion'] in ('check_completeness','pedagogy') for x in item['issues']) else 'PASS','guidance_and_all_hints_no_final_answer_leak':'PASS','truthful_provenance_and_student_work':'PASS'};item['status']='REPAIR' if item['issues'] else 'PASS_FOR_REVIEWED_CONTENT'
review={'status':'DRAFT_REPAIR_REQUESTED_NOT_ACCEPTANCE','source_file':str(p),'source_file_sha256':sha(raw),'scope':'All48 actual problem,givens,requested_quantity,student_work,worked_steps incl every reason/explanation/result/unit,expected_answer,initial_guidance,all3 hints read. Independent exhaustive structure checks for each row and Fraction AST evaluation of every numeric worked expression. No textbook-source coverage proof added here.','math_oracle_pass_rows':48,'numeric_expression_count':nexpr,'all_rows_read':48,'human_review':False,'external_review':False,'diversity_limit':'Some within-family entries differ only numerals (successor04/05; inequality10/12; cards13/14/15; prefix25/27; reverseerror43/44/45). They are numeric variants of a representation, not independent subform coverage.','rows':results}
out=root/'root_numeric/root48_peer_review.json';out.write_text(json.dumps(review,ensure_ascii=False,indent=2),'utf-8');print(json.dumps({'path':str(out),'sha256':sha(out.read_bytes()),'rows':48,'numeric':nexpr,'repair_rows':len(issues),'math_failures':0}))


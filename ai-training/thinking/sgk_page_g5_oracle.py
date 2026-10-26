"""Independent givens-based oracle; no import of author builder or its answers."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal,localcontext
from datetime import datetime,timedelta
import ast,json,hashlib
P=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019/g5_append'
def sha(b):return hashlib.sha256(b).hexdigest()
def neg(v):return tuple(-x for x in v)
def foldable(cells):
 pts={tuple(v) for v in cells.values()}
 if len(pts)!=6:return False
 start=next(iter(pts)); frames={start:((1,0,0),(0,1,0),(0,0,1))};q=[start]
 for p in q:
  u,v,n=frames[p]
  choices=[((1,0),(neg(n),v,u)),((-1,0),(n,v,neg(u))),((0,1),(u,neg(n),v)),((0,-1),(u,n,neg(v)))]
  for (dx,dy),frame in choices:
   z=(p[0]+dx,p[1]+dy)
   if z not in pts:continue
   if z in frames:
    if frames[z]!=frame:return False
   else:frames[z]=frame;q.append(z)
 return len(frames)==6 and len({f[2] for f in frames.values()})==6
def ev(expr,cast):
 def go(n):
  if isinstance(n,ast.Expression):return go(n.body)
  if isinstance(n,ast.Constant):return cast(str(n.value))
  if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -go(n.operand)
  if isinstance(n,ast.BinOp):
   a,b=go(n.left),go(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,ast.Div):return a/b
  raise ValueError(ast.dump(n))
 return go(ast.parse(expr,mode='eval'))
rows=[];nsteps=0
for line in (P/'draft_cases.jsonl').read_bytes().splitlines():
 r=json.loads(line);o=r['oracle_evidence'];kind=o['kind'];out={}
 if kind.startswith('tariff'):
  def bill(n):
   # Per-unit marginal price enumeration, independent of author's block products.
   return sum(next(o['rates'][j] for j,cap in enumerate(o['caps']) if cap is None or unit<=cap) for unit in range(1,n+1))
  if kind=='tariff':assert bill(o['used'])==o['total'];out={'total':bill(o['used']),'unit_prices_enumerated':o['used']}
  else:
   candidates=[n for n in o['domain'] if bill(n)==o['bill']];assert candidates==[o['used']];out={'solutions':candidates}
 elif kind=='rotation':
  # Compare equal fractions of full tank capacity, not direct reused step formula.
  dims=list(map(Fraction,o['dims']));capacity=dims[0]*dims[1]*dims[2]
  oldheight=Fraction(o['oldheight']);oldmax=capacity/(Fraction(o['base'][0])*Fraction(o['base'][1]))
  fraction_full=oldheight/oldmax;newheight=fraction_full*Fraction(o['newmax'])
  assert newheight==Fraction(o['newheight']) and 0<newheight<=Fraction(o['newmax'])
  assert capacity*fraction_full==o['volume'];out={'fraction_full':str(fraction_full),'height':str(newheight),'capacity':str(capacity)}
 elif kind=='timezone':
  a,b,t=map(datetime.fromisoformat,(o['reference_a'],o['reference_b'],o['target_a']))
  offset=b-a;target=t+offset;assert target.isoformat(timespec='minutes')==o['target_b'];assert (t-a).total_seconds()==o['elapsed']*60
  out={'offset_seconds':offset.total_seconds(),'target_b':target.isoformat(timespec='minutes')}
 elif kind=='net_cut':
  valid=[];out={}
  for label in o['allowed']:
   result=foldable({k:v for k,v in o['cells'].items() if k!=label});out[label]=result
   if result:valid.append(label)
  assert valid==o['valid'];out['valid']=valid
 else:raise ValueError(kind)
 answers={}; numeric=[]
 for s in r['worked_steps']:
  if not s.get('expression'):continue
  exp=s['expression']
  for key,val in answers.items():exp=exp.replace('{'+key+'}','('+val+')')
  f=ev(exp,Fraction)
  with localcontext() as ctx:ctx.prec=80;d=ev(exp,Decimal);assert Fraction(d)==f
  assert f==Fraction(s['result']);answers[s['step_id']]=s['result'];numeric.append(s['step_id']);nsteps+=1
 rows.append(dict(sample_id=r['sample_id'],source_line_sha256=sha(line),oracle_status='PASS',method='INDEPENDENT_PER_UNIT_ENUMERATION_OR_FRAME_FOLD_OR_CAPACITY_FRACTION_OR_OFFSET_DATETIME',result=out,numeric_steps_fraction_decimal=numeric,semantic_proof_claim=False))
(P/'independent_oracles.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for x in rows),'utf-8')
print(json.dumps(dict(rows=len(rows),passed=len(rows),numeric_steps=nsteps,source_sha256=sha((P/'draft_cases.jsonl').read_bytes()),oracle_sha256=sha((P/'independent_oracles.jsonl').read_bytes()))))

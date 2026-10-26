"""A finite teaching supplement outside the newly exhaustive small rectangles."""
import json
from pathlib import Path
import exhaustive_cloud_resume as c
import exhaustive_multidigit_math as m

RUN=c.RUN
def build():
 c.configure_sources();reserved=c.protected()|set(c.read(RUN/'holdout_signatures.json')['signatures'])
 # Several long-division turns, internal/trailing quotient zero, exact/remainder,
 # digit zero in factors, carry and factors of ten, all in stated finite scope.
 pairs=[]
 for a,b in [(1563,43),(1564,43),(1562,43),(43043,43),(4300,43),(4301,43),(10005,49),(10001,97),(123456,123),(998001,999),(1002003,101),(700007,777),(999999,999),(123456,456),(120060,120),(100000,125),(12345,25),(1000001,999),(908070,302),(99999,11),(100100,100),(100000,999),(765432,321),(101001,100),(100800,105),(810081,81),(9999999,999),(704025,345)]:pairs.append(('/',a,b))
 for a,b in [(567,89),(999,999),(208,304),(1001,101),(999999,999),(709,10),(709,100),(709,1000),(1000,1000),(809,1),(0,999),(999,0),(12345,67),(87654,321),(50006,208),(105,908),(304,208),(89,567),(456789,9),(987654,100),(10001,101),(10001,1000),(120030,405),(6789,789),(3456,123),(90909,909)]:pairs.append(('*',a,b))
 for a,b in [(99999,1),(99999,99999),(506007,7098),(100000,99999),(1000000,10001),(100002,99999),(9000000,8999999),(909090,808080)]:
  for op in ('+','-'):
   if (op=='+' and a+b<=9999999) or (op=='-' and a>=b):pairs.append((op,a,b))
 # Existing large addition/subtraction domain0..1000 never repeated. Multiplication
 # old0..10 and small rectangle0..100 are likewise excluded by this fixed list.
 seen=set();rows=[];chat=[];numeric=0;excluded=[]
 for op,a,b in pairs:
  assert (op,a,b) not in seen;seen.add((op,a,b))
  assert max(a,b)>1000 if op in ('+','-') else max(a,b)>100
  r=m.make_row(op,a,b);proof=m.validate_row(r);numeric+=sum(s['expression'] is not None for s in r['worked_steps'])
  r['coverage']['mode']='FINITE_TEACHING_BOUNDARY_SUITE'
  r['coverage']['finite_suite']='multidigit_boundaries.v1'
  rows.append(r)
  reason='FIXED_REGRESSION' if not r['training_eligible'] else 'PROTECTED_OR_HELDOUT_NUMERIC' if set(r['canonical_signatures'])&reserved else None
  if reason:excluded.append({'sample_id':r['sample_id'],'reason':reason})
  else:chat.extend(m.chat_records(r))
 for name,values in [('boundary_cases.jsonl',rows),('boundary_chat.jsonl',chat)]:
  (RUN/name).write_text(''.join(c.dumps(r)+'\n' for r in values),'utf-8')
 c.save(RUN/'boundary_qa.json',{'cases':len(rows),'chat_rows':len(chat),'numeric_steps_validated':numeric,'excluded_from_candidate_view':excluded,'source_sha256':c.filehash(RUN/'boundary_cases.jsonl'),'status':'EXACT_ORACLES_PASSED_PENDING_ACTUAL_TEMPLATE_REVIEW','fixed_regression_present_in_source_only':True,'new_generated_cases':len(rows),'template_sha256':m.template_fingerprint()})
 print(c.dumps({'boundary_cases':len(rows),'candidate_chat_rows':len(chat),'excluded_cases':len(excluded)}))
if __name__=='__main__':build()

"""Reopen exact draft fields, additional prose arithmetic, links and mutations."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
import ast,copy,hashlib,importlib.util,json,operator
P=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def rows(n):return[(json.loads(b),sha(b))for b in(P/n).read_bytes().splitlines()if b]
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jl(n,x):(P/n).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'for r in x),encoding='utf-8')
def calc(e,typ):
 def walk(n):
  if isinstance(n,ast.Constant):return typ(ast.get_source_segment(e,n))
  if isinstance(n,ast.BinOp):return{ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}[type(n.op)](walk(n.left),walk(n.right))
  raise ValueError(e)
 return walk(ast.parse(e,mode='eval').body)
FACTS={
'board_cutlist_area_price':[('2*90*20','3600'),('3*60*20','3600'),('90*60','5400'),('3600+3600+5400','12600'),('226.8/180','1.26'),('2+3+1','6')],
'shelf_design_finite_budget':[('0.6*0.25','0.15'),('0.88+2*0.15','1.18'),('0.88+3*0.15','1.33'),('0.88+4*0.15','1.48'),('1.18*200','236'),('1.33*200','266'),('1.48*200','296'),('270-266','4')],
'half_third_vs_sixth_inventory':[('3*2','6'),('2*3','6'),('6+6','12'),('5*6','30'),('6*5','30'),('6*5/6','5')],
'scheme_piece_shortage_even_if_named_share':[('1/3+2/6','2/3'),('3*2/3','2'),('3-2','1'),('1/2+1/3','5/6'),('3*(1/2+1/3)','5/2')],
'grid_frame_known_side_cells':[('9*0.5','4.5'),('7*0.5','3.5'),('9*7','63'),('(9-2)*(7-2)','35'),('0.5*0.5','0.25'),('63*0.25','15.75'),('35*0.25','8.75'),('28*0.25','7'),('8.75+7','15.75')],
'grid_frame_unknown_height_from_border':[('24-2*9','6'),('6/2','3'),('3+2','5'),('9*0.5','4.5'),('5*0.5','2.5'),('2*9+2*(5-2)','24'),('9*5','45'),('45*0.25','11.25'),('(9-2)*(5-2)','21'),('21*0.25','5.25'),('6+5.25','11.25')],
'gridded_net_dimensions_no_target':[('6+3+6+3','18'),('6*0.5','3'),('3*0.5','1.5'),('4*0.5','2'),('6*3*4','72'),('0.5*0.5*0.5','0.125'),('72*0.125','9')],
'net_total_strip_not_edge':[('6+4+6+4','20'),('6*0.2','1.2'),('4*0.2','0.8'),('3*0.2','0.6'),('6*4*3','72'),('0.2*0.2*0.2','0.008'),('72*0.008','0.576'),('4*0.8*0.6','1.92')],
'tiling_mixed_orientation_construction':[('5*6','30'),('2*3','6'),('2*3','6'),('3*2','6'),('2+3','5')],
'tiling_no_rotation_area_not_sufficient':[('30/6','5')],
'nested_triangles_distinct_apex_heights':[('8*6/2','24'),('4*6/2','12'),('4*3/2','6'),('24-6','18'),('6+18','24')],
'nested_vertical_base_external_altitude_foot':[('6-3','3'),('3*4/2','6'),('3*5/2','7.5'),('8-4','4'),('4*6/2','12'),('6+6+12','24'),('8*6/2','24')]
}
spec=importlib.util.spec_from_file_location('independent_measure_readback',P/'independent_oracle.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
cases=rows('cases.jsonl');byid={r['sample_id']:(r,h)for r,h in cases};assert len(cases)==12
qa={r['sample_id']:r for r,h in rows('selfqa7.jsonl')};numeric=[];mutations=[]
for r,h in cases:
 assert qa[r['sample_id']]['source_row_sha256']==h and len(qa[r['sample_id']]['criteria'])==7 and all(v['passed']for v in qa[r['sample_id']]['criteria'])
 assert all(r[k]==v for k,v in qa[r['sample_id']]['actual_fields'].items())
 assert[r0['id']for r0 in r['givens']]==['g0','g1']and[s['step_id']for s in r['worked_steps']]==['s'+str(i)for i in range(len(r['worked_steps']))]
 if r['student_work']:
  assert r['student_work']['text']in r['problem']and all(z['excerpt']in r['student_work']['text']for z in r['student_work']['observations'])
 for expr,wanted in FACTS[r['topic']]:
  f=calc(expr,F)
  with localcontext()as c:
   c.prec=90;d=calc(expr,Decimal);assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-70')
  assert f==F(wanted)
  numeric.append(dict(sample_id=r['sample_id'],source_row_sha256=h,expression=expr,expected=wanted,fraction=str(f),decimal=str(d),scope='Actual arithmetic fact transcribed from actual worked prose; includes quoted arithmetic when explicitly correct',passed=True))
 model=copy.deepcopy(r['independent_model']);kind=model['kind'];mod.oracle(model)
 if kind in('board_bill','frame','frame_inverse'):model['expected_total'if'expected_total'in model else'expected_cost']='999'
 elif kind=='board_budget':model['expected_best']=4
 elif kind=='cut_compare':model['expected_feasible'][0]=False
 elif kind=='net':model['expected_volume']='999'
 elif kind=='tiling':model['expected_possible']=not model['expected_possible']
 elif kind=='nested':model['expected_areas'][0]='999'
 try:mod.oracle(model)
 except AssertionError:mutations.append(dict(sample_id=r['sample_id'],source_row_sha256=h,mutation='Change expected complete finite-model answer or convention',detected=True))
 else:raise AssertionError('Wrong answer was not rejected')
linkcount=0;modes={sid:set()for sid in byid}
for c,ch in rows('chat.jsonl'):
 r,h=byid[c['source_sample_id']];assert c['source_row_sha256']==h and c['acceptance_status']==r['acceptance_status']and c['quality_status']==r['quality_status']
 user=json.loads(c['messages'][1]['content']);expect=dict(grade=r['grade'],problem=r['problem'],mode=c['mode'])
 if r['student_work']:expect['student_work']=r['student_work']['text']
 assert user==expect
 target=json.loads(c['messages'][2]['content'])
 if c['mode']=='worked_solution':assert target==dict(can_solve=True,initial_guidance=r['initial_guidance'],steps=r['worked_steps'],answer=r['expected_answer'])
 else:
  hint=r['hints'][int(c['mode'][-1])-1];assert target==dict(hint=hint['hint'],question=hint['question'])
 modes[r['sample_id']].add(c['mode']);linkcount+=1
assert linkcount==48 and all(v=={'worked_solution','hint_level_1','hint_level_2','hint_level_3'}for v in modes.values())
jl('prose_numeric_fraction_decimal.jsonl',numeric);jl('adversarial_model_checks.jsonl',mutations)
summary=dict(status='AUTHOR_REOPEN_FULLFIELD_QA_PASS_ROOT_PEER_PENDING',cases=12,chats=48,source_cases_sha256=sha((P/'cases.jsonl').read_bytes()),source_chat_sha256=sha((P/'chat.jsonl').read_bytes()),additional_prose_arithmetic_facts=len(numeric),independent_models_rerun=12,wrong_model_answer_mutations_rejected=len(mutations),source_qa7_hashes=True,all_chat_source_prompt_target_links=True,technical_ids_canonical=True,original_author_draft_preserved='../g5_measurement_models (including its author_pre_polish)',parent_lineage='partition_repair_delta.json',training_started=False,drive_mutated=False)
write('validation_readback.json',summary)
manifest=json.loads((P/'manifest.json').read_text('utf-8'));manifest['additional_prose_arithmetic_facts']=len(numeric);manifest['wrong_model_answer_mutations_rejected']=len(mutations)
manifest['readback_files']=[dict(file=n,bytes=(P/n).stat().st_size,sha256=sha((P/n).read_bytes()))for n in['measure_readback.py','prose_numeric_fraction_decimal.jsonl','adversarial_model_checks.jsonl','validation_readback.json','author_polish_delta.jsonl']]
write('manifest.json',manifest);print(json.dumps(summary,ensure_ascii=False))

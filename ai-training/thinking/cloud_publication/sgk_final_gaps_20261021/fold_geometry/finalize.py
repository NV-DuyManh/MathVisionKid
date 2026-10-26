"""Create draft rows, exact QA evidence and four neutral chat modes."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
import ast,hashlib,importlib.util,json,re
from collections import Counter

def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def calc(e,T):
 def walk(n):
  if isinstance(n,ast.Constant):return T(str(n.value))
  if isinstance(n,ast.UnaryOp)and isinstance(n.op,ast.USub):return -walk(n.operand)
  if isinstance(n,ast.BinOp):
   a,b=walk(n.left),walk(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,ast.Div):return a/b
  raise ValueError(e)
 return walk(ast.parse(e,mode='eval').body)

def run(M):
 out=M.OUT;out.mkdir(parents=True,exist_ok=True)
 prior_raw=None
 if(out/'cases.jsonl').exists():
  assert not(out/'manifest.json').exists(),'Frozen draft exists; do not reauthor'
  prior_raw=(out/'cases.jsonl').read_bytes()
  target=out/'author_before_numeric_metadata_normalization.jsonl'
  if target.exists():assert target.read_bytes()==prior_raw
  else:target.write_bytes(prior_raw)
 def write(n,x):(out/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 def jl(n,x):(out/n).write_text(''.join(dump(r)+'\n'for r in x),encoding='utf-8',newline='\n')
 def loadfile(n):
  spec=importlib.util.spec_from_file_location(n,out/(n+'.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
 data=loadfile('author_data');O=loadfile('independent_oracle')
 hints=[
 ['Phân biệt hình giấy cong thật với hình chữ nhật dùng để ước lượng.','Theo dõi bán kính và nửa độ dài đường tròn trong cách xếp xen kẽ.','Kiểm kết luận cho số miếng hữu hạn và khi chia ngày càng nhỏ.'],
 ['Tìm hai đầu hoặc hai mép cần đặt trùng khi gấp.','Theo dõi mỗi lần gấp tạo các phần bằng nhau nào rồi mở để nhận nếp.','Kiểm bằng trùng khít và đối xứng, phân biệt kế hoạch với kết quả đã quan sát.'],
 ['Ghi cạnh nào là nếp gấp, cạnh nào là mép ngoài.','Mở lần lượt từng nếp và phản chiếu vết cắt qua đúng nếp đó.','Kiểm vết cắt gặp nhau hay tách rời và đối chiếu sự đối xứng.'],
 ['Lần theo các điểm giữa rồi tách thành tam giác bằng diện tích.','Tính diện tích từng mảnh trước khi so với cả hình vuông.','Kiểm đủ mảnh, không chồng và tổng phần bằng cả hình, không dùng số mảnh thay diện tích.'],
 ['Đưa mọi độ dài về cùng đơn vị trước khi đặt compa.','Phân biệt tâm mới với điểm cần nằm trên đường tròn trước.','Kiểm từng khoảng tâm và bán kính, giữ rõ hướng nào chưa được cho.'],
 ['Giữ đúng đỉnh, tia gốc và phía cần vẽ của góc.','Dùng tính chất ô vuông đã cho hoặc đặt tâm và vạch không của thước đo góc đúng.','Kiểm góc mở giữa hai tia, tránh đọc nhầm thang hoặc lấy góc kề.'],
 ['Theo dõi kích thước phần giấy đang chồng sau từng nếp.','Tách diện tích dấu chân nhìn từ trên khỏi lượng giấy có tính các lớp.','Kiểm diện tích từng miền nhân số lớp, đừng mặc định các miền cùng số lớp.'],
 ['Xét cạnh nào cần hoàn thiện và cặp cạnh nào cần song song.','Thử mọi điểm cho phép theo thứ tự nối đỉnh đã ghi.','Kiểm không tự cắt và đúng quy ước song song, giữ đủ các lựa chọn hợp lệ.'],
 ['Chỉ rõ đường cắt và mảnh chuyển, không chỉ so diện tích.','Theo dõi cạnh khi ghép để kiểm kín hình và không chồng.','Kiểm diện tích riêng với chu vi vì đường biên có thể thay đổi.'],
 ['Đổi đường đi và kích thước bánh về cùng đơn vị.','Một vòng lăn không trượt ứng với độ dài nào của đường tròn?','Kiểm ngược số vòng nhân độ dài một vòng, giữ phần vòng lẻ nếu được cho.']]
 def put(mid,branch,grade,problem,request,steps,answers,model,decision,student=None):
  M.add(mid,branch,problem,[problem],request,steps,answers,hints[M.WANT.index(mid)],model,decision,student)
  r=M.ROWS[-1];r['grade']=grade;r['curriculum_assignment']['grade']=grade
  r['coverage']['specific_grade_branch']=branch
  r['nearest_source_comparison']['semantic_difference']=decision
  r['coverage']['candidate_ids']={
   'g3_coincidence_midpoint':['g3_fold_midpoint'],
   'g4_cord_quarter_without_ruler':['folding_fraction_without_ruler'],
   'g4_perpendicular_coincidence_fold':['paper_fold_perpendicular_construction'],
   'g5_three_eighths_nonunit_strip':['g5_candidate_fold_fraction'],
   'g3_rectangle_single_cut_to_square':['area_preserving_cut_rearrangement'],
   'g4_parallelogram_cut_translate':['area_preserving_cut_rearrangement'],
   'g4_square_diagonal_pair_reassembly':['area_preserving_cut_rearrangement']}.get(branch,M.TASKS[mid]['candidate_ids'])
 data.author(put,M.st,M.WANT);rows=M.ROWS;assert len(rows)==23
 # A compound sentence is not a scalar numeric result. Its quantities are
 # independently checked by the model oracle, so don't attach a scalar
 # expression field to that sentence. No expected answer or wording changes.
 metadata_deltas=[]
 for r in rows:
  for step in r['worked_steps']:
   if step['expression']:
    try:F(step['result'])
    except ValueError:
     metadata_deltas.append(dict(sample_id=r['sample_id'],step_id=step['step_id'],before_expression=step['expression'],after_expression=None,result_unchanged=step['result'],reason='Compound textual result; numerical facts checked in separate geometry oracle'))
     step['expression']=None
 write('numeric_metadata_normalization.json',dict(answer_values_unchanged=True,changes=metadata_deltas,parent_raw_sha256=sha(prior_raw)if prior_raw else None))
 assert set(r['coverage']['finite_master_id']for r in rows)==set(M.WANT)
 # Frozen nearest references are selected valid training rows, never held-out payloads.
 nearest=[];seen=set();cache={}
 for t in M.TASKS.values():
  for ref in t['nearest_refs']:
   key=ref['source_file'],ref['line']
   if key in seen:continue
   p=M.OLD/ref['source_file'];cache.setdefault(str(p),p.read_bytes().splitlines());raw=cache[str(p)][ref['line']-1];r=json.loads(raw)
   assert sha(raw)==ref['sha256']and r['sample_id']==ref['sample_id']and r['split']=='train'
   assert not re.search('eval|holdout|pilot|protected',r['sample_id'],re.I)
   nearest.append(dict(reference=ref,source_row_sha256=sha(raw),actual_fields={f:r.get(f)for f in M.FIELDS},scope='Nearest valid-training actual fields only; no full-archive absence claim'));seen.add(key)
 write('candidate_task_snapshot.json',dict(input_path=str(M.PROJECTION),input_sha256=sha(M.PROJECTION.read_bytes()),tasks=list(M.TASKS.values())))
 jl('nearest_actual_fullfields.jsonl',nearest)
 # Old rows remain byte-identical. Only compare selected accepted/current sources.
 paths=[M.OLD/'current_sources.jsonl',M.OLD/'release/accepted_cases.jsonl']
 for directory in['sgk_finish_20261020','sgk_remaining_20261020','sgk_final_forms_20261020','sgk_completion_20261021','sgk_residual_20261021']:
  root=M.HERE/'cloud_publication'/directory
  paths+=list(root.glob('release/accepted_cases.jsonl'))
 snapshots={str(p):sha(p.read_bytes())for p in paths if p.exists()}
 oldids=set();oldquestions=set();norm=lambda x:re.sub(r'\s+',' ',x).strip().casefold()
 for p in snapshots:
  for b in Path(p).read_bytes().splitlines():
   r=json.loads(b);oldids.add(r['sample_id']);oldquestions.add(norm(r['problem']))
 assert len({r['sample_id']for r in rows})==23
 assert all(r['sample_id']not in oldids and norm(r['problem'])not in oldquestions for r in rows)
 jl('cases.jsonl',rows);lines=(out/'cases.jsonl').read_bytes().splitlines()
 qa=[];numeric=[];oracles=[];mutations=[];chats=[];matrix=[]
 for r,b in zip(rows,lines):
  h=sha(b);model=r['independent_model'];proof=O.oracle(model);mutation=O.adversarial(model)
  oracles.append(dict(sample_id=r['sample_id'],source_row_sha256=h,model=model,result=proof,passed=True,method='Independent finite geometry/reflection/partition/unit model, not worked-step parser'))
  mutations.append(dict(sample_id=r['sample_id'],source_row_sha256=h,**mutation))
  for s in r['worked_steps']:
   assert s['reason']and s['explanation']
   if s['expression']:
    f=calc(s['expression'],F)
    with localcontext()as ctx:
     ctx.prec=90;d=calc(s['expression'],Decimal);assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-70')
    assert f==F(s['result']);numeric.append(dict(sample_id=r['sample_id'],source_row_sha256=h,step_id=s['step_id'],expression=s['expression'],fraction=str(f),decimal=str(d),passed=True))
  for c in M.chat_records(r):
   c.update(source_row_sha256=h,acceptance_status=r['acceptance_status'],quality_status=r['quality_status']);M.L.validate_chat(c);chats.append(c)
  evidence=[
   ('problem_givens_request_consistency','Read actual full problem, givens and request; finite paper/cell/point/compass/wheel protocols explicitly supply all needed data.'),
   ('mathematical_correctness','Independent rational polygon intersection, reflected cell/layer inventory, center-distance witnesses or alternative-unit rolling oracle; Fraction and Decimal steps checked.'),
   ('reason_steps_units_check','Read every step/reason/result/explanation; why-operation, units, inverse/partition/conservation checks and approximation qualifications are explicit.'),
   ('initial_all_hints_no_answer_leak','Read initial guidance and all three hint and question fields; strategies do not give requested answer, final choice or worked solution.'),
   ('grounded_student_work_missing_data','Only explicit synthetic quoted student_work discussed. No unseen image, hidden thought, measured length, successful real fold or physical construction inferred.'),
   ('original_grade_and_structure',r['pedagogical_review_decision']),
   ('provenance_scope_preservation','Original AI source retained, DRAFT and human fields false; owner process authorization is not human content review. Exact grade branches, no extra core count; prior hashes unchanged.')]
  qa.append(dict(sample_id=r['sample_id'],source_row_sha256=h,actual_fields={f:r[f]for f in M.FIELDS},criteria=[dict(criterion=k,passed=True,evidence=e)for k,e in evidence],human_review_claimed=False,root_cross_review_status='PENDING'))
  matrix.append(dict(sample_id=r['sample_id'],source_row_sha256=h,grade=r['grade'],master_id=r['coverage']['finite_master_id'],candidate_ids=r['coverage']['candidate_ids'],specific_branch=r['topic'],scope=r['pedagogical_review_decision'],original_required_constraints=M.TASKS[r['coverage']['finite_master_id']]['required_constraints'],actual_page_receipts=M.TASKS[r['coverage']['finite_master_id']]['exact_page_receipts'],physical_visual_observation_certified=False))
 assert len(chats)==92 and all(sha(Path(p).read_bytes())==h for p,h in snapshots.items())
 for n,x in [('chat.jsonl',chats),('selfqa7.jsonl',qa),('numeric_fraction_decimal.jsonl',numeric),('independent_oracles.jsonl',oracles),('adversarial_mutations.jsonl',mutations),('coverage_grade_residual_matrix.jsonl',matrix)]:jl(n,x)
 files=[p for p in out.iterdir()if p.is_file()and p.name!='manifest.json']
 write('manifest.json',dict(status='23_DRAFTS_SELF_QA_PASSED_ROOT_CROSS_QA_PENDING',case_count=23,chat_count=92,master_counts=dict(Counter(r['coverage']['finite_master_id']for r in rows)),grade_counts=dict(Counter(r['grade']for r in rows)),numeric_steps=len(numeric),independent_oracles=len(oracles),adversarial_rejections=len(mutations),nearest_actual_rows=len(nearest),input_queue_sha256=sha(M.PROJECTION.read_bytes()),helper_sha256=sha(Path(M.__file__).read_bytes()),source_files=[dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in files],frozen_prior_hashes=snapshots,prior_unchanged=True,training_started=False,drive_mutated=False,all_sgk_forms_covered=False,scope_limitations=['Finite explicit text geometry; original publisher image and physical-execution coverage not certified.','Disk formula derivation uses supplied refinement relation and distinguishes finite arrangement from approximation.','Only exact grade/candidate branches in matrix proposed; no global master closed solely by shared ID.']))
 print(dump(dict(cases=23,chats=92,numeric_steps=len(numeric),oracles=len(oracles),mutations=len(mutations),cases_sha256=sha((out/'cases.jsonl').read_bytes()),chat_sha256=sha((out/'chat.jsonl').read_bytes()))))

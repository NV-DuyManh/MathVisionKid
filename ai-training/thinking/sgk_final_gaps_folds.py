"""Twelve original finite G5 measurement-model drafts, DATA ONLY."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
from collections import Counter
import ast,hashlib,importlib.util,json,re,sys,shutil
from exhaustive_primary_math import chat_records,expression_group
import exhaustive_colab_loader as L
HERE=Path(__file__).resolve().parent
OUT=HERE/'cloud_publication/sgk_final_gaps_20261021/fold_geometry'
OLD=HERE/'cloud_publication/sgk_page_audit_20261019'
PROJECTION=HERE/'cloud_publication/sgk_residual_20261021/reconciliation/next_uncovered_tasks.json'
WANT=['disk_sector_limit_area_argument','fold_coincidence_fraction_perpendicular','fold_cut_unfold_boundary','midpoint_tangram_piece_area','nested_circle_center_construction','prescribed_grid_angle_construction','repeated_fold_visible_area','rotated_trapezoid_completion','specified_area_preserving_dissection','wheel_turns_distance']
FIELDS=['problem','givens','requested_quantity','student_work','initial_guidance','hints','worked_steps','expected_answer']
def sha(b):return hashlib.sha256(b).hexdigest()
def jd(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def write(name,x): (OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jl(name,x): (OUT/name).write_text(''.join(jd(r)+'\n' for r in x),encoding='utf-8',newline='\n')
def find_tasks(v):
 if isinstance(v,dict):
  if v.get('master_id') in WANT and 'task_kind' in v:yield v
  for z in v.values():yield from find_tasks(z)
 elif isinstance(v,list):
  for z in v:yield from find_tasks(z)
TASKS={x['master_id']:x for x in find_tasks(json.loads(PROJECTION.read_text('utf-8')))}
assert len(TASKS)==10
ROWS=[]
def st(title,reason,result,explanation,expression=None,unit=''):return dict(title=title,reason=reason,result=str(result),explanation=explanation,expression=expression,unit=unit)
def add(master,branch,problem,givens,request,steps,answers,hh,model,decision,student=None):
 sid='sgk_final_gaps_folds_20261021_'+branch;t=TASKS[master]
 row=dict(sample_id=sid,case_group_id=sid+'_group',grade=5,topic=branch,split='train',case_kind='observable_student_error' if student else 'original_finite_measurement_model',problem=problem,givens=[dict(id='g'+str(i),text=x,value=None,unit='',role='explicit_original_given')for i,x in enumerate(givens)],requested_quantity=request,student_work=dict(text=student,observations=[dict(excerpt=student,claim_scope='Only explicit synthetic written work; no hidden cognition or unseen image inferred.')])if student else None,can_solve=True,worked_steps=[dict(step_id='s'+str(i),**x)for i,x in enumerate(steps)],expected_answer=[dict(quantity=q,result=str(v),unit=u)for q,v,u in answers],initial_guidance=[hh[0]],hints=[dict(level=i+1,hint=h,question=['Em cần giữ những điều kiện và đơn vị nào?','Em áp dụng quan hệ được cho ra sao?','Em kiểm đủ điều kiện và trường hợp biên thế nào?'][i])for i,h in enumerate(hh)],independent_model=model,pedagogical_review_decision=decision,source_role='AI_GENERATED',acceptance_status='DRAFT_AWAITING_ROOT_CONTENT_QA',quality_status='AUTHOR_SELF_QA_COMPLETE_PENDING_ROOT_QA',human_verified=False,teacher_certified=False,owner_human_reviewed=False,coverage=dict(mode='FINITE_SUPPLEMENTARY_APPEND_NOT_CORE',finite_master_id=master,branch=branch,candidate_ids=t['candidate_ids'],numbers_only_variant=False,new_core_slots_claimed=0,text_relation_only=True,visual_physical_coverage_claimed=False),curriculum_assignment=dict(grade=5,enrichment=True,source_reference='Inherited verified KNTT page receipt; original complete text model; no new image view or physical success claim.'),provenance=dict(authorship_origin='ORIGINAL_AI_TEACHER_AUTHORING',book_exercise_copied=False,human_content_review_completed=False,actual_physical_or_image_result_claimed=False,acceptance_basis='OWNER_PREAUTHORIZED_PROCESS_ROOT_QA_PENDING'),nearest_source_comparison=dict(mapping_file=str(PROJECTION.relative_to(HERE)),mapping_sha256=sha(PROJECTION.read_bytes()),actual_page_receipts=t['exact_page_receipts'],nearest_actual_valid_train_rows=t['nearest_refs'],semantic_difference=t['original_master_reasons']))
 row['canonical_signatures']=sorted({expression_group(s['expression'])for s in steps if s['expression']});ROWS.append(row)


if __name__=='__main__':
 spec=importlib.util.spec_from_file_location('folds_finalize',OUT/'finalize.py')
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 mod.run(sys.modules[__name__])

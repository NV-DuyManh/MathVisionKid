"""Additive finite text reconciliation of accepted RUN7 examples. No Drive/train."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import json,hashlib
HERE=Path(__file__).resolve().parent;PUB=HERE/'cloud_publication'
RUN=PUB/'sgk_final_gaps_20261021';PAR=PUB/'sgk_residual_20261021/reconciliation';OUT=RUN/'reconciliation'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text('utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
FIELDS=['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints']
BASIS={
'angle_ray_pair_enumeration':'G3 degree-free three-ray enumeration includes compound outer angle; duplicate point names on one ray merged. G4 prior exact relation retained.',
'balance_order_substitution_chain':'G4 explicit low-pan heavier with side changes and transitive order; G5 decimal-labelled pans include equal trailing-zero labels and wrong orientation repair. Prior G3 substitution retained.',
'bill_of_materials_area_cost':'G5 open integer design domain stated for all W,H,D,N; proposes one arbitrary valid design and repairs an over-budget design, with complete plank count and per-area cost. Does not claim unrestricted optimum, stock-sheet packing, safety or construction.',
'bounded_color_multiset_without_replacement':'G3 bounded two-token unordered color outcomes and G5 three-token bounded multisets. Actual G5 v2 printed126 source image re-viewed: exercise2 explicitly takes3 simultaneously from2red3blue; draw-count ambiguity is resolved. Prior G4 two-draw examples retained.',
'collinear_triple_complete_enumeration':'G3 complete endpoint-pair inventory, compound drawn segments and every collinear triple explicitly worked; broken-ink variant distinguishes geometric incidence from drawn boundary. Original unlocated alias locator remains unknown.',
'complementary_irregular_boundary_match':'G1 explicit concave cell boundary complement with wrong-shape distractor, then all permitted rotations with reflections forbidden; checks exact remaining cells/no overlap/no gap.',
'composite_shape_square_nonaligned_inventory':'G1 composite axis and tilted square inventory, missing-side contrast; exact declared boundaries and allowed endpoint list prevent imagined shapes. Finite modeled geometry only, not arbitrary images.',
'disk_sector_limit_area_argument':'G5 alternated sector rearrangement distinguishes finite curved boundary from limiting rectangle; derives half-circumference times radius and keeps finite substitute approximation error separate from preserved paper.',
'finite_inventory_collection_game':'G4 flower eligibility by equivalent fractions plus mutable ownership/removal, explicit shared five threshold, reciprocal-card matching with face-down reset/removal/per-player pair threshold, and ambiguous original-rule guard.',
'fixed_piece_assembly_feasibility':'G3 exact candidate triangular-piece selection with legal quarter-turn/node translations and impossible long-leg pieces; G4 equal-area but no-fit target counterexample; no actual physical execution certified.',
'fixed_piece_silhouette_placement':'G1 house silhouette uses all square/triangle pieces with exact roof boundary; G4 four triangles fill tilted square; G5 exact standard seven-piece tangram with all polygon vertices, legal transforms and no-gap/no-overlap checks.',
'fold_coincidence_fraction_perpendicular':'Separate G3 midpoint coincidence fold; G4 quarter-cord and perpendicular-through-point coincidence protocol; G5 three-eighths of nonunit strip. Model symmetry justifies fractions/perpendicularity; actual execution not claimed.',
'fold_cut_unfold_boundary':'G4 one-fold outer corner notch and two-fold central cut propagated through symmetry; connected-hole versus separate-notch distinction, correct multiplicity and remaining region.',
'geometric_edge_removal_relocation':'G1 removes exactly one explicitly named internal stick then recounts all triangles including outer; G4 exactly three sticks relocated from fixed inventory into two rhombi with complete legal donor/recipient proof.',
'gregorian_leap_year_convention':'G5 explicitly supplied Gregory4/100/400 rule used on2024/2100/2400 and complete-year interval2099..2101. Century exception scoped as enrichment; no claim publisher simplification teaches that full rule.',
'irregular_region_unit_area_count':'G1 staircase exact unit cells and partial diagonal half-cells with one-use regrouping; no enclosing rectangle counted and no double-counting.',
'midpoint_grid_multi_piece_dissection':'G4 six-piece midpoint construction with exact cut list: two squares/four triangles; all piece areas sum to source. Non-midpoint variant rejects same-area-by-appearance; no auxiliary locating diagonals counted as cuts.',
'midpoint_tangram_piece_area':'G5 standard midpoint tangram seven-piece cut inventory, each area/fraction derived, sums checked; compares unequal piece-count groups via area rather than count.',
'nested_circle_center_construction':'G5 successive centers located on the appropriate previous circle with mixed units and radius/diameter distinction; explicit nonuniqueness of unprescribed center distance.',
'nonaxis_composite_quadrilateral_enumeration':'G4 exact regular-hexagon/spoke edge graph enumerates all rhombi/parallelograms in three directions, excludes collinear degenerate vertices; missing-edge variant preserves edge completeness.',
'partial_product_column_reconstruction':'G3 one-digit multiplication only:1a4 times3 equals4b2, all four digit solutions and carry constraints; separate one-use physical-card multiplication21times4 with full finite enumeration.',
'placeclass_torn_strip_constraints':'G3 directed connector fragments, one-use orientation, leading/trailing endpoints and retained zero place tested; impossible reverse-connector variant rejects forced answer. Original G3 alias source-page locator still absent; G4 page cannot replace it.',
'prescribed_grid_angle_construction':'G4 particular nonright diagonal grid rays constructed through specified points; acute45 and obtuse135 with given square diagonal property, correct protractor zero-side/scale plan. No actual measurement attested.',
'repeated_fold_visible_area':'G5 uniform orthogonal half-folds versus off-center then half-fold: footprint dimensions, distinct local layer counts, area weighted by layers, conserved original paper.',
'repeated_value_identity_assignment':'G3 distinct-card strict ranking and partial-order all assignments, no invented middle rank; G4 room equality derives actual16/18 areas and exact inventory before person assignment. Prior G1 repeated-score evidence retained.',
'rotated_trapezoid_completion':'G5 vertical-base multiple completions and diagonal-base exclusive convention; tests actual parallel opposite sides, rejects parallelogram under explicit exactly-one-pair convention, keeps simple cyclic order.',
'seven_segment_glyph_inventory_relocation':'G1 exact segment alphabet four-stick digit and one-move equation; G4 fixed-slot one-move minimum with all candidates and leading-zero ban; digit-count change uses explicitly two moves and proves one-move impossible under separated-slot convention.',
'solid_visible_face_direction_binding':'G1 fixed-view front/top/right label binding and wrong-direction repair; G2 selects top faces then applies declared complete occlusion, excludes known-but-hidden face and other directions. Text table only, no image recognition.',
'specified_area_preserving_dissection':'Separate G3 one-cut8by2 rectangle to4by4 square; G4 parallelogram triangle translation to rectangle and square diagonal-pair reassembly. Legal cuts/transforms, no gap/overlap and area/perimeter distinction explicit. Prior G5 trapezoid evidence retained.',
'wheel_turns_distance':'G5 no-slip diameter-cm turns to metres with fractional turns; inverse kilometres plus dm radius to common units, diameter factor and round-trip check. Prior matched-unit cases retained.'
}
def main():
 cp=PAR/'candidate_adjudication.json';qp=PAR/'next_uncovered_tasks.json'
 ap=RUN/'release/accepted_cases.jsonl';rp=RUN/'release/cross_reviews.jsonl'
 pins={p.relative_to(PUB).as_posix():sha(p.read_bytes()) for p in [cp,qp,ap,rp,RUN/'root_evidence/content_review.json']}
 parent=read(cp);queue=read(qp)
 assert len(queue['global_master_tasks'])==30 and len(queue['external_g2_remaining_separate'])==55
 assert len(parent['candidates'])==204 and len(parent['occurrences'])==315
 accepted=[(json.loads(b),sha(b),i) for i,b in enumerate(ap.read_bytes().splitlines(),1)]
 reviews={r['sample_id']:r for r in map(json.loads,rp.read_text('utf8').splitlines())}
 assert len(accepted)==len(reviews)==71
 drafts={}
 for p in RUN.glob('**/cases.jsonl'):
  if p==ap:continue
  for i,b in enumerate(p.read_bytes().splitlines(),1):
   r=json.loads(b);drafts[(r['sample_id'],sha(b))]=(p,i,r)
 bound=[]
 for row,h,n in accepted:
  sid=row['sample_id'];review=reviews[sid];dh=row['provenance']['reviewed_draft_row_sha256']
  assert review['exported_row_sha256']==h and review['reviewed_draft_row_sha256']==dh
  assert len(review['criteria'])==7 and all(x['passed'] for x in review['criteria'])
  assert row['acceptance_status']=='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED' and row['split']=='train'
  assert not any(row.get(k) for k in ['human_verified','teacher_certified','owner_human_reviewed'])
  dp,dn,dr=drafts[(sid,dh)]
  assert all(dr[k]==row[k] for k in FIELDS)
  mid=row['coverage']['finite_master_id'];assert mid in BASIS
  bound.append(dict(sample_id=sid,master_id=mid,grade=row['grade'],branch=row['topic'],
   candidate_ids=row['coverage']['candidate_ids'],exported_row_sha256=h,reviewed_draft_row_sha256=dh,
   source_reference=dict(file=dp.relative_to(PUB).as_posix(),line=dn,sha256=dh),
   export_reference=dict(file=ap.relative_to(PUB).as_posix(),line=n,sha256=h),
   actual_math_fields={k:row[k] for k in FIELDS},root_qa7_pinned=True,
   publisher_image_recognition_or_physical_success_certified=False))
 bymaster={m:[x for x in bound if x['master_id']==m] for m in BASIS}
 assert all(bymaster.values())
 # Complete math branch, unresolved *source locator* is not another authoring request.
 residual={
 'collinear_triple_complete_enumeration':[dict(candidate_id='collinear_enumeration_and_segment_pairs',
  status='ORIGINAL_PAGE_LOCATOR_ONLY_PENDING',constraints=['All finite text mathematics is now demonstrated at G3, including endpoint-pair segment inventory; original alias has no exact source-page locator. Find/document the original locator, or explicitly record pending-source. Do not reauthor or relabel existing page evidence to simulate that locator.'])],
 'placeclass_torn_strip_constraints':[dict(candidate_id='tornplaceclass_strip_assembly',
  status='ORIGINAL_G3_PAGE_LOCATOR_ONLY_PENDING',constraints=['G3 directed-fragment/place-value adaptation is now demonstrated, including impossible connector and zero placeholder. Original G3 alias exact page locator is still absent; existing G4 pp43-44 are not an original G3 locator. Resolve/document source mapping only; no number-only duplicate required.'])]
 }
 closed=set(BASIS)-set(residual);assert len(closed)==28
 report=deepcopy(parent);report['schema']='finite_candidate_reconciliation.v4_accepted_run7'
 report['parent_adjudication_sha256']=sha(cp.read_bytes())
 candidate_decisions=[]
 for c in report['candidates']:
  mid=c['decision']['master_id']
  if mid not in BASIS:continue
  exact=[e for e in bymaster[mid] if c['candidate_id'] in e['candidate_ids']]
  if not exact:continue
  old=deepcopy(c['reconciliation'])
  c.setdefault('reconciliation_history',[]).append(dict(parent_sha256=sha(cp.read_bytes()),decision=old))
  rem=[x for x in residual.get(mid,[]) if x['candidate_id']==c['candidate_id']]
  status='TEXT_RELATION_COMPLETE_SOURCE_LOCATOR_PENDING' if rem else 'NEW_EXACT_FINITE_TEXT_BRANCH_DEMONSTRATED'
  update=dict(status=status,text_relation_demonstrated=True,remaining_constraints=deepcopy(rem),
   accepted_run7_examples=deepcopy(exact),semantic_basis=BASIS[mid],
   whole_master_closed=False,publisher_image_recognition_or_physical_success_certified=False,
   original_candidate_fields_and_locator_preserved=True)
  c['reconciliation'].update(update)
  candidate_decisions.append(dict(candidate_id=c['candidate_id'],master_id=mid,**update))
 for m in report['masters']:
  mid=m['master_id']
  if mid not in BASIS:continue
  m.setdefault('reconciliation_history',[]).append(dict(parent_sha256=sha(cp.read_bytes()),status=m['status'],remaining_candidate_branches=deepcopy(m['remaining_candidate_branches'])))
  m.update(status='FINITE_TEXT_COMPLETE_SOURCE_LOCATOR_PENDING' if mid in residual else 'FINITE_TEXT_RELATION_DEMONSTRATED',
    accepted_run7_examples=deepcopy(bymaster[mid]),remaining_candidate_branches=deepcopy(residual.get(mid,[])),
    text_mathematical_branch_complete=True,physical_or_image_assets_complete=False,semantic_basis=BASIS[mid])
 # Do not extend all other G2 aliases by master/name. One genuinely G2 source row only.
 g2id='g2v1:solid_visible_face_directions'
 g2e=[e for e in bound if e['grade']==2 and g2id in e['candidate_ids']]
 assert len(g2e)==1
 g2matches=[]
 for c in report['external_g2_candidates']:
  if c['candidate_id']!=g2id:continue
  c.setdefault('reconciliation_history',[]).append(dict(parent_sha256=sha(cp.read_bytes()),decision=deepcopy(c['reconciliation'])))
  c['reconciliation'].update(status='NEW_EXACT_G2_TEXT_RELATION_DEMONSTRATED',
    matched_new_examples=deepcopy(g2e),remaining_constraints=[],
    semantic_basis='Explicit grade2 fixed direction/occlusion model filters TOP and VISIBLE independently; full face table contains distractors and known hidden top face. Only finite original text relation is certified.',
    whole_g2_candidate_closed=False,physical_or_publisher_image_result_claimed=False)
  g2matches.append(dict(candidate_id=g2id,grade=2,accepted_examples=deepcopy(g2e),physical_or_image_claim=False))
 outq=deepcopy(queue);outq['schema']='finite_next_uncovered_tasks.v4_accepted_run7'
 outq['parent_queue_sha256']=sha(qp.read_bytes())
 tasks=[]
 for t in queue['global_master_tasks']:
  mid=t['master_id']
  if mid in closed:continue
  assert mid in residual
  new=deepcopy(t);new['prior_task']=deepcopy(t)
  new.update(required_constraints=deepcopy(residual[mid]),
    existing_relation_examples=[e['export_reference']|dict(sample_id=e['sample_id'],grade=e['grade'],reviewed_draft_row_sha256=e['reviewed_draft_row_sha256']) for e in bymaster[mid]],
    text_mathematical_branch_complete=True,task_kind='RESOLVE_OR_DOCUMENT_ORIGINAL_SOURCE_LOCATOR_ONLY_DO_NOT_REAUTHOR',
    run7_accepted_semantic_scope=BASIS[mid])
  tasks.append(new)
 outq['global_master_tasks']=tasks
 outq['external_g2_remaining_separate']=[t for t in queue['external_g2_remaining_separate'] if t['candidate_id']!=g2id]
 outq['external_g2_new_exact_text_binding']=g2matches
 outq['counts'].update(global_master_tasks=2,never_appended_missing_masters=0,partial_master_tasks=2,
   source_locator_only_tasks=2,global_text_math_authoring_tasks=0,
   external_g2_remaining_separate=54,external_g2_new_exact_text_candidates=1)
 outq['authoring_priority_guidance']='Do not reauthor the two global locator-only tasks. Address54 separate G2 candidate constraints with actual grade2 forms, plus explicit asset/physical limits. Shared masters, publisher-image recognition, and actual measurements are not certified by accepted text models.'
 report['run7_accepted_binding']=dict(status='ACCEPTED_HASH_BOUND_NOT_YET_REMOTE_BUNDLE_BOUND',
  source_sha256=sha(ap.read_bytes()),root_reviews_sha256=sha(rp.read_bytes()),
  all71_examples=bound,candidate_matches=candidate_decisions,external_g2_matches=g2matches,
  finite_text_tasks_discharged=sorted(closed),
  remaining_source_locator_only_masters=sorted(residual),
  actual_g5_three_draw_page_review=dict(file='sgk_final_gaps_20261021/numbers_reasoning/source_126.png',
   sha256=sha((RUN/'numbers_reasoning/source_126.png').read_bytes()),printed_page=126,grade=5,
   actual_image_viewed_by_reconciler=True,observed='Exercise2:2red3blue balls,3taken simultaneously; enumerate color possibilities.'))
 report['counts'].update(new_cases_evidence=parent['counts']['new_cases_evidence']+71,
   new_chat_links=parent['counts']['new_chat_links']+284,run7_accepted=71,
   remaining_global_master_tasks=2,never_appended_missing_masters=0,remaining_global_text_math_authoring_tasks=0,
   remaining_source_locator_only_tasks=2,external_g2_remaining_separate=54,
   master_status_counts=dict(Counter(x['status'] for x in report['masters'])),
   candidate_status_counts=dict(Counter(x['reconciliation']['status'] for x in report['candidates'])))
 report.update(all_sgk_forms_covered=False,authoring_performed=False,drive_mutated=False,training_performed=False,
   source_selection='Prior exact reconciliation plus71 accepted original finite models, source/export/draft hashes checked. No exhaustive corpus claim; all original204candidate fields,315occurrences,91G2records retained; only one explicit G2 text disposition updated.',
   limitations=parent['limitations']+[
    '28global finite text tasks discharged; two original source locators remain unresolved even though their mathematical branches are complete.',
    '54 separate G2 grade/constraint/asset branches remain; common global masters do not close these.',
    '10asset-only masters retained separately; text plans never attest physical execution or publisher image recognition.',
    'Acceptance of open-domain shelf examples is of one lawful original design, not stock packing, structural safety or global optimum.'])
 assert report['occurrences']==parent['occurrences'] and len(report['occurrences'])==315
 assert len(report['candidates'])==204 and len(report['masters'])==167 and len(report['external_g2_candidates'])==91
 assert outq['unresolved_asset_only_masters']==queue['unresolved_asset_only_masters'] and len(outq['unresolved_asset_only_masters'])==10
 for old,new in zip(parent['candidates'],report['candidates']):
  for k,v in old.items():
   if k not in ('reconciliation','reconciliation_history'):assert new[k]==v
 for old,new in zip(parent['external_g2_candidates'],report['external_g2_candidates']):
  if old['candidate_id']!=g2id:assert old==new
 OUT.mkdir(exist_ok=True)
 write(OUT/'candidate_adjudication.json',report)
 write(OUT/'next_uncovered_tasks.json',outq)
 write(OUT/'run7_accepted_binding.json',report['run7_accepted_binding'])
 after={p.relative_to(PUB).as_posix():sha(p.read_bytes()) for p in [cp,qp,ap,rp,RUN/'root_evidence/content_review.json']}
 assert after==pins
 result=dict(status='PASS',accepted_cases_bound=71,accepted_chat_links_declared=284,
   finite_text_global_tasks_discharged=28,remaining_global_master_tasks=2,
   remaining_global_text_math_authoring_tasks=0,remaining_source_locator_only_tasks=2,
   external_g2_new_exact_text_candidates=1,external_g2_remaining_separate=54,
   asset_only_masters_separate=10,original204_candidate_fields_preserved=True,
   original315_occurrences_preserved=True,external91_g2_records_preserved=True,
   untouched54_g2_pending_branches_preserved=True,all_sgk_forms_covered=False,
   training_started=False,inputs=pins,outputs={n:sha((OUT/n).read_bytes()) for n in ['candidate_adjudication.json','next_uncovered_tasks.json','run7_accepted_binding.json']})
 write(OUT/'validation.json',result)
 print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','outputs')}))
if __name__=='__main__':main()


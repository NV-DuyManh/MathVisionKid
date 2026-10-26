"""Plan pending G2 branches, no authoring/acceptance or sealed artifact changes."""
import hashlib,json
from collections import Counter
from copy import deepcopy
from pathlib import Path
HERE=Path(__file__).resolve().parent
PUB=HERE/'cloud_publication'
SOURCE=PUB/'sgk_final_gaps_20261021/reconciliation'
OUT=PUB/'colab_data_audit_20261021/g2_planning'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text('utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
# Every task joins only one finite_master_id. Different source-volume labels remain separate
# candidate records. Some masters need multiple relation branches; those are not duplicates.
T=[
('numerals_distinct_all','text_finite','number_constraints',
 ['g2v1:g2_card_numeral_formation'],
 ['Enumerate every two-digit numeral from a finite distinct physical-card stock containing zero; prohibit leading0, preserve one-use identity, report both extrema and their difference. No parity filter.'],
 'Do not reuse the even-only0,3,8 exemplar as closure.'),
('numerals_repeated_zero','text_finite','number_constraints',
 ['g2v1:multiset_numeral_generation','g2v2:digit_card_permutations_zero'],
 ['Repeated-valued cards are distinct resources; enumerate unique unrestricted numeral values with exact multiplicities and zero-place restrictions; compute extrema, and distinguish identical values from physical assignments.'],
 'Both labels name the same repeated-resource/zero branch; preserve both source locators but use the same original model.'),
('numerals_bounded_three_digit','text_finite','number_constraints',
 ['g2v2:digit_card_extrema'],
 ['Construct extremal three-digit numerals from supplied card pool while exceeding an explicit bound; exact card use, no leading zero and strict boundary tested jointly.'],
 'A bounded3digit extremum is not the unrestricted2digit inventory task.'),
('role_specific_equation_pools','text_finite','number_constraints',
 ['g2v1:role_specific_equation_matching'],
 ['Supply separate finite left-operand, right-operand and result lists; enumerate only equations satisfying the role-specific membership and original reuse rule.'],
 'One undifferentiated numeric pool cannot discharge roles.'),
('exact_one_pair_sort_repair','text_finite','number_constraints',
 ['g2v1:single_pair_sort_repair'],
 ['Exactly one selected pair may be swapped; enumerate every legal pair, test the required sorted order and explicitly include an impossible branch or uniqueness check.'],
 'Arbitrary multi-swap minimum is a different operation budget.'),
('vertex_sum_rule','original_asset_or_complete_annotation','number_constraints',
 ['g2v1:rule_inference_ambiguity'],
 ['Provide complete vertex/edge incidence and numeric examples in a common vertex-sum diagram; infer/check the stated candidate rule and show when a finite prefix cannot uniquely determine a rule.'],
 'Use original fully annotated diagram or text incidence. No invented publisher image and no generic sequence-only substitute.'),
('expression_truth_attribute_extrema','original_asset_or_complete_annotation','number_constraints',
 ['g2v1:conjunctive_attribute_expression_filter','g2v1:conjunctive_attribute_filter'],
 ['Evaluate each arithmetic statement/expression, conjoin its truth with a supplied color/shape annotation, then select extrema only among surviving objects. Test an attractive wrong-attribute extremum.'],
 'The two constraints require the same arithmetic-truth plus attribute conjunction; one exact original table can serve both labels.'),
('irregular_cube_support_layers','original_asset_or_complete_annotation','geometry_representation',
 ['g2v1:unit_cube_count_assembly'],
 ['Specify an irregular occupied-cell or column-height arrangement, viewing direction and support/no-floating convention; count visible and genuinely required hidden units, with ambiguity guard if hidden support is not determined.'],
 'Complete cuboid multiplication does not establish irregular visibility or hidden-support inference.'),
('mutable_game_inventory_ownership','text_finite','state_games',
 ['g2v1:finite_inventory_collection_state','g2v1:finite_inventory_game_state','g2v2:finite_token_game','g2v2:finite_board_ownership'],
 ['Subbranch1: collect a named card once, remove it permanently and track owner/remainingstock.',
  'Subbranch2: memory-pair match state; mismatch resets face state, match removes pair; all values supplied.',
  'Subbranch3: finite token availability restricts later placements; keep turn order and legal move budget.',
  'Subbranch4: board cell ownership plus explicit collinear winning lines; evaluate stop/win from supplied moves.'],
 'All four aliases inherited the same broad constraint paragraph. One packet coordinates four substantive branches; do not pretend one scalar board walk closes all four. Multiple small originals are expected within this packet.'),
('balance_down_pan_transitivity','original_asset_or_complete_annotation','measurement_relations',
 ['g2v1:balance_orientation_order','g2v2:balance_orientation_order'],
 ['Grade2 integer/symbolic stable-object pans; explicit low=heavy convention; object changes side across observations; chain inequalities and verify every pan.'],
 'Exact duplicate v1/v2 orientation constraints share one original grade2 model. G4 accepted examples stay references only.'),
('pan_group_substitution_chain','text_finite','measurement_relations',
 ['g2v1:balance_chain_substitution'],
 ['Replace a group by an explicitly equal-weight group through several balances, keeping item multiplicities; derive an unknown quantity or compare totals and substitute back into every original equality.'],
 'Keep pan-group equality distinct from a one-step balance or displacement-volume formula.'),
('boat_equal_watermark_substitution','original_asset_or_complete_annotation','measurement_relations',
 ['g2v2:substitution_equal_mark'],
 ['Supply equal baseline boat/load conditions and equal observed water marks as an explicit mass-equivalence rule; replace entire load groups with equal groups and preserve passenger/item identities.'],
 'Do not claim actual water marks were observed; use a labeled original table/model or an actual supplied record.'),
('bounded_repour_state_choices','text_finite','measurement_relations',
 ['g2v1:capacity_conservation_repour'],
 ['Give finite container capacities, initial amounts, allowed fill/empty/repour actions and target; enumerate legal state transitions with recipient capacity, amount conservation and no impossible overfill.'],
 'Single donor-minus-recipient arithmetic is not a multi-container plan.'),
('pointer_scale_direction_tare','original_asset_or_complete_annotation','measurement_relations',
 ['g2v1:instrument_scale_reading'],
 ['Circular pointer with explicit tick values, equal interval count, increasing direction, needle location and tare/gross condition; read and check actual intended quantity.'],
 'Fully annotate an original diagram or text tick table; existing linear vessel interpolation is related only. Physical pointer reading remains unverified without actual record.'),
('subset_fixed_cardinality_target','text_finite','number_constraints',
 ['g2v1:fixed_cardinality_subset_sum','g2v2:fixed_cardinality_subset_sum'],
 ['Finite named items/weights, exact selected cardinality2or3, target and boundary constraints; enumerate all lawful subsets and conserve item availability.'],
 'Two exact duplicate cardinality constraints share one finite original, not two number-only variants.'),
('subset_sum_extrema','text_finite','number_constraints',
 ['g2v1:finite_subset_sum_extrema'],
 ['Among subsets satisfying a stated cardinality/eligibility/budget domain, minimize or maximize selected total and enumerate tied optima; one feasible target does not prove optimality.'],
 'Different requested objective from fixed target/cardinality feasibility; retain a separate branch.'),
('seven_segment_single_move_maximum','original_asset_or_complete_annotation','geometry_representation',
 ['g2v1:seven_segment_relocation','g2v2:matchstick_numeral_extrema'],
 ['Define exact digit segment alphabet, fixed slots, one physical relocation, no added/lost sticks, leading-zero rule and required maximum. Enumerate all legal final values and establish global maximum under that exact budget.'],
 'Both labels require same single-move maximum; prior G4 minimum and two-move digit-count case do not close grade2maximum.'),
('skip_nodes_example_rule','text_finite','state_games',
 ['g2v1:jump_skip_nodes_interpretation'],
 ['Supply an unambiguous example distinguishing nodes jumped-over from landing; infer/confirm k-to-k+1 rule, preserve starting/landing count and finite board endpoint behavior.'],
 'Ordinary die counting cannot replace the jump-over convention.'),
('crossing_curved_connector_trace','original_asset_or_complete_annotation','geometry_representation',
 ['g2v1:trace_single_crossing_curve'],
 ['One continuous curved connector passes through a crossing; specify continuity/tangent/over-under annotations enough to follow without switching; return endpoint or traversal, with insufficient-evidence guard.'],
 'A named straight polyline or line/curve definition does not close crossing trace. Original actual curve asset or complete continuity annotation needed.'),
('all_drawn_segment_endpoint_pairs','text_finite','geometry_representation',
 ['g2v1:point_segment_edge_list'],
 ['Grade2 named endpoint inventory over explicit drawn intervals; include compound segments through intermediate points and exclude gaps, reverse names and nonexistent cross-lines.'],
 'New G3source now models this relation but no automatic grade2 binding.'),
('actual_measurement_record','actual_observation_required','physical_personal_records',
 ['g2v1:physical_measurement_guard','g2v2:physical_measurement'],
 ['Obtain actual learner ruler/scale reading or calibrated image with units, endpoint alignment, zero/offset and measurement record. A synthetic plan may support guard behavior only.'],
 'Both labels are duplicate actual-evidence requirements. Do not generate a measurement outcome as if it was performed.'),
('all_collinear_triples_grade2','text_finite','geometry_representation',
 ['g2v1:collinear_triples'],
 ['Complete explicit point incidence, including intermediate points; enumerate every unordered collinear triple without inferring unprovided alignments. Grade2 naming/presentation adapted explicitly.'],
 'Different finite_master_id from drawn-segment inventory; keep separate even when one original diagram may support both mathematical questions.'),
('composite_quadrilateral_inventory_grade2','original_asset_or_complete_annotation','geometry_representation',
 ['g2v1:composite_polygon_count','g2v2:composite_shape_count'],
 ['Grade2 finite quadrilateral/composite arrangement with explicit vertices and every drawn segment; include composite sides through collinear points, exclude degenerate corners and missing boundaries.'],
 'Duplicatev1/v2 shape-configuration constraints can share one exact original annotated arrangement. G3triangle-only enumeration does not close this.'),
('scaled_grid_route_lengths','text_finite','geometry_representation',
 ['g2v1:grid_path_length_comparison','g2v2:grid_path_length'],
 ['Specify grid spacing/scale, allowed route edges, whole versus partial steps and supplied lengths for any permitted diagonal; sum each finite route and compare totals/ ties. Do not require irrational diagonal computation at grade2.'],
 'Both require scaled-grid geometry; a single complete original grid-path model can bind both only after actual QA.'),
('fold_cut_unfold_grade2','original_asset_or_complete_annotation','geometry_representation',
 ['g2v1:fold_cut_spatial'],
 ['Grade2 explicit fold axis/coincident sides, exact cut location and affected layers; unfold to named regions/boundary and distinguish edge notches from interior holes.'],
 'Original annotated layout or complete small cell model; G4fold examples are related references only.'),
('triangular_piece_pair_feasibility_grade2','original_asset_or_complete_annotation','geometry_representation',
 ['g2v1:piece_tiling'],
 ['Supplied triangular-piece pool; choose allowed pair for exact target with stated rotations/reflections, dimensions and no-gap/no-overlap proof, including a distractor pair.'],
 'G2domino tiling and G3triangular selection are not automatic grade2 source closure.'),
('actual_solid_assembly_record','actual_observation_required','physical_personal_records',
 ['g2v2:physical_assembly'],
 ['Real/pictured solid piece inventory and actually assembled result with support/occlusion evidence; record what is observed and what remains indeterminate.'],
 'Same master as triangular plane fitting but different dimension/physical-evidence branch, so it cannot be merged into that text-feasibility task.'),
('cut_reassemble_square_grade2','original_asset_or_complete_annotation','geometry_representation',
 ['g2v1:dissection_reassembly_square'],
 ['Explicit grade2 original cut positions, piece shapes and legal translations/rotations producing target square; exact full cover/no-overlap proof.'],
 'Preexisting-piece domino placement is not a cut selection protocol.'),
('actual_segment_construction_record','actual_observation_required','physical_personal_records',
 ['g2v1:physical_construction_guidance'],
 ['Obtain real endpoint/scale/zero-alignment evidence of requested segment; assess only visible placement and measured length; otherwise ask for missing observation.'],
 'Current guidance can be accepted as guidance, but cannot be promoted to a completed real construction.'),
('calendar_grid_missing_cells_offsets','text_finite','time_context',
 ['g2v1:calendar_missing_cells'],
 ['Supply complete month/year or adequate last-date/leap convention, weekday anchor and weekly grid convention; restore missing cells, first-occurrence weekday and previous-week dates.'],
 'One end-of-month rollover does not cover all three requested grid/offset branches.'),
('personal_date_timetable_contract_guard','text_finite','time_context',
 ['g2v1:missing_personal_timetable_guard','g2v1:missing_current_date_guard'],
 ['Subbranch1: absent learner timetable -> request learner schedule/reference day, no invented class period.',
  'Subbranch2: absent current-date/location context -> ask needed learner date/year/timezone, no substitution from agent system date.'],
 'Exact duplicate broad constraint paragraph coordinates two input contracts; preserve both labels and require both small cases.'),
('continuous_clock_hand_motion','text_finite','time_context',
 ['g2v1:clock_hand_motion'],
 ['Specify continuous hour/minute hand motion across stated elapsed hours/quarter-hours; hour hand advances between numerals as minutes advance; verify rollover and start anchor.'],
 'Static clock-angle arithmetic does not model simultaneous hand movement.'),
('discover_equal_expression_classes','text_finite','number_constraints',
 ['g2v2:g2v2_expression_class_count'],
 ['Evaluate every supplied expression, discover complete equal-value equivalence classes and count distinct classes; not merely list members for already supplied target values.'],
 'Output is a partition/count, not matching two predefined totals.'),
('shape_recognition_filtered_maze','original_asset_or_complete_annotation','state_games',
 ['g2v2:shape_filtered_maze'],
 ['Each branch has exact shape/solid attributes, original recognizable asset or complete annotation; follow the supplied shape predicate and graph direction, returning lawful path/allpaths.'],
 'Text arithmetic predicate alone is different; do not infer unseen shapes.'),
('local_condition_labelled_maze','text_finite','state_games',
 ['g2v2:conditional_labelled_maze'],
 ['Node/edge labels condition moves locally; include larger-edge choice and any label-dependent transition policy, exact finite graph, ties and dead-end behavior.'],
 'One global graph predicate is not every local conditional policy.'),
('unit_capacity_bijection_inclusive','text_finite','measurement_relations',
 ['g2v2:capacity_assignment'],
 ['Convert supplied quantities to a common unit, assign one-to-one to finite container capacities with inclusive fits<=capacity, no reuse; test equality boundary and enumerate valid assignments.'],
 'Strict greater-than resource example fails inclusive boundary.'),
('aligned_endpoint_length_difference','text_finite','measurement_relations',
 ['g2v2:aligned_segment_difference'],
 ['Explicit common-reference endpoints/offsets for train/bridge or bars; derive missing length from aligned spans and check reconstructed endpoint positions.'],
 'Do not subtract arbitrary labelled lengths without shared alignment.'),
('actual_trajectory_observation','actual_observation_required','physical_personal_records',
 ['g2v2:trajectory_observation_guard'],
 ['Obtain actual supplied path/image or authoritative complete path annotation; classify only observed trajectory features, otherwise request clear trace.'],
 'Generic line-vs-curve and photo guard principles cannot certify the particular unobserved trajectory.'),
('actual_personal_survey_room_schedule','actual_observation_required','physical_personal_records',
 ['g2v2:physical_observation','g2v2:personal_survey'],
 ['Obtain learner actual room/timetable/preferences/respondent records; retain respondent identity, one-choice/counting contract and missing records; distinguish hypothetical teaching example from actual reported fact.'],
 'Both candidates require actual personal evidence; do not author survey answers and call them collected.'),
('grid_copy_coordinates_incidence','original_asset_or_complete_annotation','geometry_representation',
 ['g2v2:grid_copy'],
 ['Original lattice target has complete vertex coordinates/incidence/scale/orientation; reproduce every required segment/region on a second grid and verify correspondence.'],
 'Domino tiling or arbitrary collinearity statement is not copying the supplied silhouette.'),
('sequential_draw_stock_outcomes_grade2','text_finite','state_games',
 ['g2v2:two_draw_without_replacement'],
 ['Two sequential no-replacement draws update stock after first draw; enumerate possible color outcomes, combine order-insensitive observations where asked, and classify possible/certain/impossible events under exact multiplicity.'],
 'Simultaneous G3/G5 draws and numeral card use do not automatically satisfy grade2sequential-state semantics.')
]
def main():
 qp=SOURCE/'next_uncovered_tasks.json';ap=SOURCE/'candidate_adjudication.json'
 before={str(p.relative_to(PUB)):sha(p.read_bytes()) for p in [qp,ap]}
 q=read(qp);a=read(ap)
 pending=q['external_g2_remaining_separate'];assert len(pending)==54
 source={x['candidate_id']:x for x in pending};assert len(source)==54
 original={x['candidate_id']:x for x in a['external_g2_candidates']};assert len(original)==91
 tasks=[];assigned=[]
 for seq,(slug,kind,category,ids,branches,why) in enumerate(T,1):
  assert len(set(ids))==len(ids)
  records=[source[x] for x in ids]
  mids={x['finite_master_id'] for x in records};assert len(mids)==1
  crosses={x['crossgrade_master_id'] for x in records};assert len(crosses)==1
  for cid in ids:
   assert cid in original
   assert original[cid]['book_id'] in ['g2v1','g2v2']
  evidence=[]
  for cid in ids:
   c=original[cid]
   evidence.append(dict(candidate_id=cid,grade=2,book_id=c['book_id'],
    actual_required_constraints=deepcopy(source[cid]['constraints']),
    queue_record=deepcopy(source[cid]),
    original_candidate_record_sha256=sha(json.dumps(c,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()),
    actual_page_receipts=deepcopy(c.get('actual_page_receipts',[])),
    nearest_actual_valid_train_rows=deepcopy(c.get('nearest_actual_valid_train_rows',[])),
    prior_reconciliation=deepcopy(c['reconciliation'])))
  task=dict(task_id=f'g2_pending_{seq:02d}_{slug}',grade=2,finite_master_id=next(iter(mids)),
    crossgrade_master_id=next(iter(crosses)),candidate_ids=ids,category=category,
    preparation_kind=kind,status='PLANNED_NOT_AUTHORED_NOT_ACCEPTED',
    minimal_required_specific_branches=branches,grouping_semantic_basis=why,
    actual_candidate_evidence=evidence,
    authoring_scope='Original finite fully explicit text/annotation or actual evidence only; grade2 enrichment/range explicit; preserve all source/page IDs.',
    actual_asset_or_observation_requirement=(
     'Actual observation required to claim real performance. Synthetic tasks/guards may be supplementary but never certify these real outcomes.'
       if kind=='actual_observation_required' else
     'For text-relation coverage supply original asset or complete annotation; original publisher-image recognition remains unverified without actual task-specific image evidence.'
       if kind=='original_asset_or_complete_annotation' else
     'A fully explicit finite text model can demonstrate only the specified mathematical/input-contract relation; no actual physical or publisher-image claim.'),
    independent_acceptance_criteria=[
     'Root reads actual problem/givens/request/student_work, every step/reason/explanation/unit/answer, initial guidance and all three hints.',
     'Finite independent model and Fraction/Decimal where numeric; meaningful wrong-model/answer mutations.',
     'Record exact raw source/draft/export hashes and QA7; accepted previous forms remain untouched.',
     'Only explicit candidate-grade/constraint match may close a branch; same master/name or this plan never constitutes acceptance.'
    ],
    new_examples_created=0,pending_candidates_closed=0,human_review_claimed=False)
  tasks.append(task);assigned.extend(ids)
 assert len(tasks)==41 and len(assigned)==54 and set(assigned)==set(source)
 assert all(n==1 for n in Counter(assigned).values())
 # Count exact duplicated queue texts separately from consciously combined semantic constraints.
 exact=Counter((x['finite_master_id'],tuple(x['constraints'])) for x in pending)
 same_text_groups=[dict(finite_master_id=m,constraints=list(c),candidate_ids=[x['candidate_id'] for x in pending if x['finite_master_id']==m and tuple(x['constraints'])==c])
                   for (m,c),n in exact.items() if n>1]
 byslug={t['task_id'].split('_',3)[3]:t['task_id'] for t in tasks}
 cohorts=[
 dict(cohort_id='G2_A_small_numeric',task_ids=[byslug[x] for x in ['numerals_distinct_all','numerals_repeated_zero','numerals_bounded_three_digit']],
      purpose='Three different finite numeral branches; reuse one independent card-enumeration engine but keep substantive stock/output constraints. No number-only duplication.',
      maximum_initial_cases=6,scope='2 contrasting cases per task, then semantic QA; do not multiply numerical variants.'),
 dict(cohort_id='G2_B_small_selection',task_ids=[byslug[x] for x in ['role_specific_equation_pools','exact_one_pair_sort_repair','subset_fixed_cardinality_target']],
      purpose='Role pools, exact-one-swap repair, exact-cardinality feasibility are separate finite constraints.',
      maximum_initial_cases=6,scope='2 substantive contrasting originals per task, then independent QA.'),
 dict(cohort_id='G2_C_small_calendar_context',task_ids=[byslug[x] for x in ['calendar_grid_missing_cells_offsets','personal_date_timetable_contract_guard','continuous_clock_hand_motion']],
      purpose='Anchor-grid completion, truthful missing learner context, and continuous two-hand motion.',
      maximum_initial_cases=6,scope='Cover every listed subbranch with small originals; actual student data remain requested, never invented.')
 ]
 result=dict(schema='finite_g2_pending_preparation_plan.v1',status='PLAN_ONLY_NO_COVERAGE_DISCHARGED',
  source_queue_sha256=sha(qp.read_bytes()),source_adjudication_sha256=sha(ap.read_bytes()),
  counts=dict(pending_candidate_ids=54,unique_finite_master_ids=len({x['finite_master_id'] for x in pending}),
    specific_preparation_tasks=len(tasks),by_grade={'2':len(tasks)},by_category=dict(Counter(t['category'] for t in tasks)),
    by_preparation_kind=dict(Counter(t['preparation_kind'] for t in tasks)),
    actual_observation_required_tasks=sum(t['preparation_kind']=='actual_observation_required' for t in tasks),
    original_asset_or_complete_annotation_tasks=sum(t['preparation_kind']=='original_asset_or_complete_annotation' for t in tasks),
    next_three_cohorts=len(cohorts),new_cases=0,accepted_cases=0,pending_closed=0),
  grouping_policy='Group only compatible exact same finite_master_id and actual constraints; preserve every v1/v2 candidate ID/receipt. Split materially different branches even under one master. 41small packets are an inspected economical plan, not a mathematical proof of globally minimum examples. One packet may explicitly require several different branch cases.',
  exact_duplicate_constraint_groups=same_text_groups,tasks=tasks,next_three_small_cohorts=cohorts,
  original_frozen_sources_modified=False,drive_mutated=False,training_started=False,
  limitations=['No task is accepted or closed by planning;54pending dispositions remain authoritative.',
   'Grade2 branch/range and original page representation must be reviewed before exact closure; G1/G3/G4same-master examples are references only.',
   'Actual measurement, construction, assembly and personal records cannot be synthesized as performed facts.',
   'Publisher-image skill is separate from fully annotated original text relation.'])
 OUT.mkdir(parents=True,exist_ok=True)
 write(OUT/'queue.json',result)
 after={str(p.relative_to(PUB)):sha(p.read_bytes()) for p in [qp,ap]}
 assert before==after
 validation=dict(status='PASS',all54_candidate_ids_assigned_exactly_once=True,
  original_candidate_ids_count=54,assigned_candidate_ids_count=54,unique_assigned=54,
  task_count=len(tasks),unique_finite_master_ids=36,no_task_crosses_finite_master=True,
  all_tasks_grade2=True,actual_required_constraints_and_nearestrefs_preserved=True,
  original_source_hashes_before=before,original_source_hashes_after=after,
  original_frozen_sources_unchanged=before==after,new_cases_created=0,pending_closed=0,
  drive_mutated=False,training_started=False,queue_sha256=sha((OUT/'queue.json').read_bytes()),
  helper_sha256=sha(Path(__file__).read_bytes()))
 write(OUT/'validation.json',validation)
 print(json.dumps(dict(status='PASS',counts=result['counts'],queue_sha256=validation['queue_sha256'],
    validation_sha256=sha((OUT/'validation.json').read_bytes())),ensure_ascii=False))
if __name__=='__main__':main()


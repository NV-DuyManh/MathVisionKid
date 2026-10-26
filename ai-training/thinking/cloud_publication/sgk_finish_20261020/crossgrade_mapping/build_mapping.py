"""Finite semantic ledger; source payloads remain immutable. No training/publication."""
import json, pathlib, hashlib, re, collections

BASE=pathlib.Path(__file__).resolve().parent
RUN=BASE.parent.parent/'sgk_page_audit_20261019'
def read(p): return json.loads((RUN/p).read_text('utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x): (BASE/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
inventory=read('current_source_index.json')  # metadata index only
V=json.loads((BASE/'valid_training_inventory.json').read_text('utf-8'))
SEM=['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints','can_solve']
def topic(t): return [s for s,z in V.items() if z['row'].get('topic')==t]
def sid(s):
 if s in V:return s
 hits=[k for k in V if k.endswith(s)]
 if len(hits)!=1: raise ValueError((s,hits))
 return hits[0]
def refs_from(x):
 out=[]
 def walk(y):
  if isinstance(y,dict):
   if y.get('sample_id') in V: out.append(y['sample_id'])
   for v in y.values():walk(v)
  elif isinstance(y,list):
   for v in y:walk(v)
 walk(x);return list(dict.fromkeys(out))

records={};occ=[];receipt_files={}
def add(cid,origin,x):
 z=records.setdefault(cid,{'candidate_id':cid,'origins':[],'prior_adjudications':[],'nearest_ids':[],'page_receipts':[]})
 z['origins'].append(origin);z['prior_adjudications'].append(x);z['nearest_ids']+=refs_from(x)
 return z
files=['g1v1_audit/gaps.json','g1v2_audit/candidate_adjudication.json','g3_audit/candidate_adjudication.json','g3_spatial_append/adjudication.json','g4_audit/remaining_candidate_adjudication.json','g5_audit/candidate_adjudication.json']
for f in files:
 d=read(f);arr=d if isinstance(d,list) else next((d[k] for k in ['candidates','adjudications','selected_draft_forms'] if k in d),[])
 for x in arr:
  c=x.get('candidate_id',x.get('gap_id'));add(c,f,x)
for dr,key in [('g1v1_audit','new_gap_candidate_ids'),('g1v2_audit','new_gap_candidate_ids'),('g3_audit','gap_ids'),('g4_audit','gap_candidates'),('g5_audit','gap_ids')]:
 p=RUN/dr/'page_review.jsonl';receipt_files[str(p.relative_to(RUN))]=sha(p)
 for ln,l in enumerate(p.read_text('utf-8-sig').splitlines(),1):
  x=json.loads(l)
  for c in x.get(key,[]):
   z=records.get(c) or add(c,str(p.relative_to(RUN)),{})
   pr={k:x[k] for k in ['book_id','grade','volume','printed_page','publisher_page_url','public_image_url','image_url','official_url','source_image_sha256','image_sha256','sha256','exercise_types','exercise_types_read','evidence_level','review_basis','review','actual_visual_page_read'] if k in x}
   z['page_receipts'].append(pr);z['nearest_ids']+=refs_from(x)
   occ.append({'occurrence_id':f'{dr}:{ln}:{c}','candidate_id':c,'receipt_file':str(p.relative_to(RUN)),'receipt_line':ln,'page_receipt':pr})
g3=read('g3_spatial_append/adjudication.json')
for x in g3['cross_grade_merges']:
 c=x['canonical_form'];add(c,'g3_spatial_append/adjudication.json:cross_grade_merges',x)
 for pr in x['sources']:
  if pr['book_id'].startswith('g3'):
   records[c]['page_receipts'].append(pr);occ.append({'occurrence_id':f'g3_spatial_crossgrade:{c}:{pr["book_id"]}:{pr["printed_page"]}','candidate_id':c,'receipt_file':'g3_spatial_append/adjudication.json','page_receipt':pr})
# G3 adjudications retain exact observed locators, including historical candidate labels
# whose page_review gap_ids list was never populated. These are explicit occurrences too.
seen={(o['candidate_id'],o['page_receipt'].get('book_id'),o['page_receipt'].get('printed_page')) for o in occ}
for c,z in records.items():
 for a in z['prior_adjudications']:
  rr=a.get('actual_page_receipts',a.get('page_evidence',a.get('locators',[])))
  if isinstance(rr,dict):rr=[rr]
  if not rr and a.get('actual_page_receipt'):rr=[a['actual_page_receipt']]
  for p in rr:
   k=(c,p.get('book_id'),p.get('printed_page'))
   # Page-level original occurrences dominate repeated adjudication locators.
   if any(o['candidate_id']==c and o['page_receipt'].get('printed_page')==p.get('printed_page') for o in occ):continue
   if k not in seen:
    z['page_receipts'].append(p);occ.append({'occurrence_id':f'adjudication:{c}:{p.get("book_id",p.get("volume",""))}:{p.get("printed_page")}', 'candidate_id':c,'receipt_file':z['origins'][0],'page_receipt':p});seen.add(k)

C='COVERED_EXACT_ID_HASH';M='FINITE_CONFIRMED_MISSING_MASTER';A='ASSET_ONLY_LIMITATION';P='PENDING_ACTUAL_COMPARISON'
decisions={}
def setd(ids,master,status,reason,extra=(),owner='UNASSIGNED',asset=False,scope=None):
 if isinstance(ids,str):ids=[ids]
 ee=[]
 for x in extra:ee+=topic(x[6:]) if x.startswith('topic:') else [sid(x)]
 for c in ids:
  if c not in records:raise ValueError('unknown candidate '+c)
  decisions[c]={'master_id':master,'category':status,'semantic_comparison':reason,'support_ids':list(dict.fromkeys(ee)),'owner':owner,'asset_residual':asset,'comparison_scope':scope or 'Actual full fields of listed nearest valid training rows; missing means missing demonstrated subform within inspected nearest sources, not an exhaustive absence proof over all archives.'}

# Every accepted family is linked to its exact release rows. Old candidate words do
# not override the accepted source content, and merged labels do not imply closure.
for c in list(records):
 if c.startswith('G1V1_'):
  t=c[5:].lower()
  if topic(t):setd(c,t,C,'Accepted release explicitly works this observed relation, with task, constraints, answers and hints; exact release hashes retained.', ['topic:'+t],asset=any(w in t for w in ['shape','solid','cube']))
g4=read('g4_audit/remaining_candidate_adjudication.json')
for c,t in g4['numeric_already_handled'].items():setd(c,t,C,'The accepted release works the finite numeral/operation constraints; numeric constants alone do not create another type. Exact rows and hashes retained.',['topic:'+t])
g4new={'board_turn_privilege_transition':'board_turn_privilege','boat_shuttle_state_plan':'boat_shuttle','bar_model_to_story':'bar_model_to_story','regular_dial_angle':'regular_dial_angle','numeric_crossword_intersections':'numeric_crossword','directional_estimation_bound_proof':'directional_estimation_bound','geometric_sequence_local_extension':'geometric_sequence_local_extension','chart_causal_inference_guard':'chart_causal_guard','trial_log_race_state':'trial_log_race_state','closed_operation_cycle_consistency':'closed_operation_cycle'}
for c,t in g4new.items():setd(c,t,C,'Published exact source now demonstrates the added state/representation/output constraint that the prior adjudication marked missing. Reuse the accepted family; do not author a duplicate.',['topic:'+t])
for c,t in {'g3_composite_polygon_count':'composite_polygon_enumeration','g3_fixed_stick_rectangles':'fixed_stick_rectangle_inventory','g3_painted_cube_faces':'assembled_cube_painted_faces','g5_candidate_tiered_tariff':'tiered_tariff','g5_candidate_rotated_water':'rotated_water','g5_candidate_timezone_rollover':'timezone_given_table','g5_candidate_net_repair':'net_repair_cut_one'}.items():setd(c,t,C,'Published release now explicitly demonstrates this subform. Closure is text-described mathematical reasoning; visual recognition and physical execution remain outside this evidence.',['topic:'+t],asset=True)

setd(['G1V1_CURVED_CONNECTION_TRACING_ASSET'],'curved_connection_image',A,'The missing evidence is tracing an actually drawn crossing curve. Number reading/tens-ones is present; another text arithmetic row cannot establish pixel tracing.',['_bundled_sticks_tens_units_write_read'],asset=True)
setd('G1V1_DIGIT_STROKE_ASSET','handwriting_stroke_execution',A,'Reading numerals and operations is present; handwritten stroke formation needs a model/trace or observed physical result, not a new numerical task.',['_digit_cards_zero_and_tens_placeholder'],asset=True)
setd('G1V1_EMBEDDED_DIGIT_IMAGE_ASSET','embedded_digit_image',A,'Recognition of a numeral embedded in clutter is visual evidence absent from text-only numeral-reading examples.',['_digit_cards_zero_and_tens_placeholder'],asset=True)
setd(['G1V1_COMPLEMENTARY_BOUNDARY_MATCH'],'complementary_irregular_boundary_match',M,'Restoring two triangles from one declared cut does not choose irregular complementary convex/concave boundaries. Explicit piece boundaries/legal transforms required.',['_diagonal_cut_restore'],asset=True)
setd(['G1V1_COMPOSITE_SHAPE_COUNT'],'composite_shape_square_nonaligned_inventory',M,'Published triangle and axis-aligned rectangle enumeration establishes those subsets; it does not enumerate every G1 arbitrary composite/implicit-boundary shape. Keep original geometry and counting conventions.',['topic:composite_polygon_enumeration'],asset=True)
setd('G1V1_DICE_REGION_BOUNDARY_MATCH','all_boundary_labels_joint_match',M,'A region is eligible only if all boundary labels match supplied die outcomes; unary node filters and board position updates do not demonstrate this joint region constraint.',['topic:constrained_arithmetic_path'])
setd(['G1V1_MULTIPIECE_SILHOUETTE_ASSET','silhouette_piece_assembly','g5_candidate_tangram_assembly'],'fixed_piece_silhouette_placement',M,'A known diagonal restoration is not legal placement of a fixed multi-piece inventory into a silhouette. Need explicit piece shapes, target, rotations/reflections, no-gap/no-overlap proof.',['_diagonal_cut_restore'],asset=True)
setd('G1V1_REVERSE_SEQUENCE_COMPLETION','constant_step_sequence',C,'Declared subtraction of a constant step and inverse checking are already worked. Reversing traversal and repeated blanks changes constants/direction, not the recurrence relation.',['_round_tens_subtract','_forward_number_line_cross_tens_blank'])
setd('G1V1_SOLID_VISIBLE_FACE_DIRECTIONS','solid_visible_face_direction_binding',M,'Whole-solid classification does not bind each marked face to front/top/right in a specified viewpoint. Need explicit orientation/face inventory or actual image; do not infer hidden faces.',['_cube_all_faces'],asset=True)
setd('G1V1_STICK_SHARED_EDGE_CONSTRUCTION','shared_edge_stick_construction',M,'Diagonal-cut restoration does not construct two triangles under a five-stick inventory with one shared edge. Need finite edge model and inventory proof.',['_diagonal_cut_restore'],asset=True)
setd('G1V1_SUCCESSIVE_TWO_REMOVALS','successive_add_subtract_sequence',C,'The text corpus explicitly evaluates ordered add/subtract chains and verifies intermediate states. Repeating subtraction instead of alternating signs adds no distinct representation.',['_left_subtract_add','_left_add_subtract'])
setd('G1V1_UNIT_CUBE_COUNT_ASSEMBLY','unit_cube_layers_assembly',C,'Actual valid source counts unit cubes from layer/row/column structure and relates assembly to a larger cube. This closes mathematical text relation across grades; grade-1 wording and physical result are separate.',['_layers_unit_cubes','_metre_cube_layers'],asset=True)
setd('G1V1_ZERO_SUBTRACTION_EXPLICIT','generic_subtraction_boundary',C,'Subtracting zero or self is a boundary of the established subtraction operation; no new task family is justified by changing numbers only.',['_round_tens_subtract','_choose_subtract'])

# G1V2: finish actual relation comparisons, separating age presentation from math.
setd('G1V2_ATTRIBUTE_FILTERED_EXTREMA','attribute_filter_then_extremum',M,'Conjunctive numeral selection and independent sorting exist, but no listed row selects extrema from a color/shape-qualified subset; preserve filter before max/min, ties and empty subset.',['topic:conjunctive_numeral_filter','_sort_four'])
setd('G1V2_CALENDAR_ANCHOR_OFFSET','calendar_anchor_day_offset',M,'Actual calendar source generates only same-weekday +7 dates; lookup reads supplied pairs. Neither demonstrates offset by an arbitrary number of days to infer another weekday/date from one anchor.',['sgk_gap_20261019_g3_calendar_occurrences_fifth_weekday','_mini_calendar_lookup'])
setd('G1V2_CLOCK_READING_IMAGE_ASSET','clock_face_image_reading',A,'Explicit described hands and activity matching are worked; rotated/differently placed actual clock faces require visual evidence.',['_calendar_clock_activity'],asset=True)
setd('G1V2_COMMON_REFERENCE_LENGTH_COMPARISON','common_unit_length_image_alignment',A,'Equal-unit tiling with no gaps/overlaps, common endpoints and ruler-origin subtraction are explicitly worked. Differently oriented picture strips need the actual reference/alignment asset, not another length algorithm.',['_handspan_complete_units','_two_origins_same_length'],asset=True)
setd('G1V2_COMPOSITE_SHAPE_INVENTORY_ASSET','composite_component_image_inventory',A,'Naming each explicitly described component and counting discrete tokens are established. Segmentation of the pictured robot into visible components is absent visual evidence. This does not certify hidden/composite polygon enumeration.',['_four_shape_matching','_count14'],asset=True)
setd('G1V2_COMPOSITE_SQUARE_COUNT_ASSET','composite_square_only_enumeration',M,'The accepted 2x2 grid example enumerates all rectangles including squares, but does not work the square-only equal-side subset; retain one finite square-specific subform, not many number variants.',['topic:composite_polygon_enumeration'],asset=True)
setd('G1V2_CONSTANT_STEP_SEQUENCE','constant_step_sequence',C,'Actual source explicitly separates adjacent tick increments 1 and10; accepted inclusive step-two enumeration also preserves endpoints. A declared constant step2/5/10 changes a parameter, not mathematical structure.',['_ray_two_different_scales','sgk_gap_20261019_g4_parity_cards_inclusive_error'])
setd('G1V2_DIRECT_LENGTH_IMAGE_ASSET','actual_scale_measurement',A,'Known ruler endpoints and offset origins are worked. Measuring a printed object requires actual scale/resizing information and observed endpoints.',['_cm_read_write','_cm_offset_origin'],asset=True)
setd(['G1V2_DUPLICATE_SCORE_ASSIGNMENT','equal_area_elimination'],'repeated_value_identity_assignment',M,'Distinct-card sorting or one-use resource matching does not assign a repeated-value multiset to identities under equality/strict-order constraints. The G4 equal-area identity task shares this master.',['topic:resource_assignment_inequality','_trailing_zero_and_sort'])
setd('G1V2_ELAPSED_WHOLE_HOURS','elapsed_time_intervals',C,'Actual source computes same-day elapsed interval from explicit endpoints; whole hours remove minute conversion and are a simpler parameterization. Grade-specific wording is not a missing mathematical relation.',['cloud_pedagogy_v3_025'])
setd('G1V2_EQUAL_QUANTITY_BALANCE_REPRESENTATION','quantity_balance_equality',C,'Balance source equates a whole to sum of parts and explains why equality holds. Removing kg from abstract equal quantities preserves the relation; no claim of physical balance reading.',['_balance_equal_weights'],asset=True)
setd('G1V2_GATE_PAIR_SUM_PATH','pair_relation_stage_path',M,'Per-node predicates do not choose one gate at each stage under a relation jointly involving two labels. Need actual adjacency and relation between chosen pair.',['topic:constrained_arithmetic_path'])
setd(['G1V2_GRID_REGION_UNIT_COUNT_ASSET'],'irregular_region_unit_area_count',M,'Independent symbol counting and rectangular grid enumeration do not count full/partial equal-area cells of an irregular region. Explicit boundary, cell area, regrouping and no-overlap required.',['topic:composite_polygon_enumeration','_one_of_six_equal_area_parts:polish_v1'],asset=True)
setd('G1V2_LINKED_ARITHMETIC_NETWORK','successive_add_subtract_sequence',C,'Prior actual p97 receipt states a linear arrow chain. It is the same ordered intermediate-state update worked by old text rows; no branches/shared nodes are present to justify an invented new graph gap.',['_left_add_subtract'])
setd(['G1V2_MATCHSTICK_DIGIT_ASSET','G1V2_SINGLE_MATCH_EQUATION_REPAIR','seven_segment_single_move_minimum','seven_segment_relocation_with_digit_count_change'],'seven_segment_glyph_inventory_relocation',M,'Moving/counting segments changes glyph shapes, unlike swapping whole digit cards. Shared master must state segment alphabet, allowed positions, exact move budget, minimum convention and whether digit-count/layout changes are legal.',['topic:one_digit_swap_repair'],asset=True)
setd('G1V2_MISSING_DIGITS_COLUMN_SUBTRACTION','column_multi_blank',C,'Accepted exact subtraction source works coupled blanks with two exchanges, preserves other digits, lists all valid pairs and rechecks. Lower magnitude/grade is a presentation adaptation, not absent relation.',['sgk_page_20261019_g4_column_multi_blank_exchange'])
setd('G1V2_ORDERED_ITINERARY_DAY_MAPPING','ordered_itinerary_weekday_map',M,'Static queue and calendar lookup do not map successive itinerary stops to successive days from a stated start with one-stop-per-day rule. Keep finite order, start and weekday rollover.',['_mini_calendar_lookup','_queue_front_middle_back'])
setd(['G1V2_PLAUSIBLE_REFERENCE_ESTIMATION','plausible_measurement_unit','g5_candidate_area_magnitude','g5_candidate_volume_magnitude'],'plausible_measure_reference_options',C,'Actual source chooses between supplied magnitude/unit proposals from an explicit approximate reference and distinguishes estimate from measured fact. Length/area/volume conversions exist separately. Book-specific unstated world references remain contextual evidence limitations, not extra numeric methods.',['_estimate_with_reference_scale','_mixed_area_land','_volume_compare_mixed_units'],asset=True)
setd('G1V2_PREDICATE_PATH_ASSET','predicate_filtered_directed_path',C,'Actual accepted directed graph checks each allowed arrow and numeric predicate. The picture itself is an asset residual.',['topic:constrained_arithmetic_path'],asset=True)
setd(['G1V2_REMOVE_MATCHES_TRIANGLE_COUNT_ASSET','geometric_matchstick_relocation'],'geometric_edge_removal_relocation',M,'Published static triangle listing does not remove/move a fixed number of edges and recount all surviving target shapes while preserving inventory. Explicit edge set/move legality required.',['topic:composite_polygon_enumeration'],asset=True)
setd('G1V2_REPEATED_DIGIT_NUMBER_SELECTION','repeated_digit_symbol_predicate',M,'Place-value and fixed-position digit filters are worked; equality of two digit symbols over every supplied number is not explicitly demonstrated in listed rows. Keep one finite predicate example, not arithmetic-number expansion.',['topic:conjunctive_numeral_filter','_digit_cards_zero_and_tens_placeholder'])
setd('G1V2_ROLE_POOL_EQUATION_CONSTRUCTION','role_specific_equation_pool',M,'Accepted number-card equation synthesis uses a shared number inventory, not independently restricted first-operand, second-operand and result pools. Preserve role restrictions and reuse budget.',['topic:construct_equations_from_number_cards'])
setd(['G1V2_ROUTE_TOTAL_LENGTH_COMPARISON','g5_candidate_shortest_route'],'finite_route_total_optimization',M,'A single route sum and predicate-valid path do not compare totals over all connected routes and prove minimum. Explicit edge lengths/connectivity/direction and round-trip convention needed.',['topic:constrained_arithmetic_path','_scaled_field_fence'])
setd('G1V2_SCHEDULE_AFTER_ARRIVAL_SELECTION','arrival_schedule_eligibility',M,'Exact time-to-activity matching is present; event eligibility based on arrival before/at start adds an explicit strict/inclusive threshold over several events.',['_calendar_clock_activity'])
setd('G1V2_SORT_REPAIR_ONE_SWAP','minimum_pair_swaps',C,'Accepted pair-swap examples preserve physical cards, operate on positions and prove swap minimum; testing whether exactly one swap repairs the order is the same operation with budget1.',['topic:minimum_pair_swaps'])
setd('G1V2_TEMPORAL_STAGE_ORDER','biological_stage_image_context',A,'Recognizing botanical stages from unlabeled pictures is contextual/visual evidence, not a new numerical ordering operation. A stated ordered sequence is already worked.',['_queue_front_middle_back'],asset=True)
setd('G1V2_TIMETABLE_MULTI_CRITERIA_LOOKUP','timetable_day_hour_lookup',C,'Actual source selects by both weekday and hour; it does not rely on one matching key alone. Pictured table layout remains visual evidence.',['_calendar_clock_activity'],asset=True)
setd('G1V2_TRANSFER_COMPARISON','two_group_transfer_then_compare',M,'Sequential changes to one container do not update two group totals in opposite directions under a conserved transfer and then compare, including tie.',['_left_add_subtract'])
setd('G1V2_TWO_DIGIT_NUMBER_CARD_CONSTRUCTION','finite_digit_card_enumeration',C,'Actual source enumerates by last digit, chooses distinct remaining cards for tens, forbids leading0, checks all branches and deduplicates. Dropping the parity filter is a simpler finite card-enumeration instance; no new algorithm needed.',['sgk_gap_20261019_g4_parity_cards_two_digit_zero'])

# G3 and shared G4 geometry/constraint masters.
for c in ['g3_sum_pyramid','g3_expression_bin_filter_count','g3_conditional_board','g3_minimum_capacity','g3_digit_card_swap']:
 ts={'g3_sum_pyramid':'sum_pyramid','g3_expression_bin_filter_count':'expression_target_classification','g3_conditional_board':'conditional_board_game','g3_minimum_capacity':'minimum_capacity','g3_digit_card_swap':'one_digit_swap_repair'}
 setd(c,ts[c],C,'Actual prior full-field comparison demonstrates the same local rule/constraint. Larger operands alone are not a new representation.', ['topic:'+ts[c]])
setd('g3_product_pyramid','product_pyramid',M,'Adjacent product plus reverse missing-cell/dependency reasoning differs from existing sum pyramid. Parent is authoring one finite original family.',['topic:sum_pyramid'],owner='ROOT_AUTHORING')
setd('g3_two_jug_transfer','two_jug_state_transfer',M,'Marked-volume repeated measures do not track two ungraduated vessel states through fill/empty/pour and stop conditions.',['_balance_equal_weights'],owner='ROOT_AUTHORING')
setd('g3_operator_synthesis','finite_operator_synthesis',M,'Choosing supplied models/brackets does not synthesize all legal operators under a target or minimum objective.',['topic:expression_choice','topic:insert_single_plus'],owner='ROOT_AUTHORING')
setd('g3_missing_digit_column','partial_product_column_reconstruction',M,'Accepted multi-blank addition/subtraction works carry/exchange but does not reconstruct missing digits across multiplication partial products and their shifted total.',['topic:column_multi_blank','_misconception_tens_partial_unscaled'])
setd('g3_equal_area_heterogeneous_partition','equal_area_geometric_regrouping',M,'Stated equal-area pieces do not prove equality when triangles must be regrouped into same-size area units. Need exact partition/no-gap/no-overlap.',['_one_of_six_equal_area_parts:polish_v1'],asset=True)
setd('g3_inscribed_touching_circles','tangent_circle_alignment_lengths',M,'A radius/diameter definition does not derive route/rectangle dimensions through several tangent aligned circles. Need explicit tangency/order/collinearity.',['_circle_distance_membership_and_diameter'],asset=True)
setd('g3_bounded_measure_subset','bounded_inventory_target_sum',M,'Adding all present weights is not choosing a fixed-size/bounded inventory subset or distinct vessels to hit a target.',['_balance_equal_weights'])
setd(['g3_balance_relation_chain','balance_orientation_order','g5_candidate_balance_consistency'],'balance_order_substitution_chain',M,'Single balance equality is not pan-direction inequality, transitive ordering and repeated-object substitution. Text must fix pan convention and stable object identities.',['_balance_equal_weights'],asset=True)
setd('g3_factor_pair_search','bounded_factor_pair_enumeration',M,'An inverse with one known factor does not enumerate unknown factor pairs under lower bounds/completeness conventions.',['topic:expression_choice'])
setd('g3_route_running_quantity','running_operation_graph_target',M,'A predicate on labels does not compose edge operations along alternative paths to a target quantity. Preserve path connectivity and intermediate states.',['topic:constrained_arithmetic_path','topic:roman_routes'])
setd('g3_two_digit_reasoning_rank','repeated_value_identity_assignment',M,'Sorting labelled quantities is not assignment of quantities to identities from order constraints. Share finite identity-assignment master with G1/G4 and retain distinct/repeated inventories.',['_sort_four','topic:resource_assignment_inequality'])
setd(['g3_fold_midpoint','paper_fold_perpendicular_construction','folding_fraction_without_ruler','g5_candidate_fold_fraction'],'fold_coincidence_fraction_perpendicular',M,'Ruler marking and restoring cut pieces do not construct equal subdivisions/perpendiculars by coincidence/symmetry folds. Need explicit folding protocol and reasoning; physical execution is separate.',['_zero_origin_plan','_diagonal_cut_restore'],asset=True)
setd('g3_collinear_enumeration','collinear_triple_complete_enumeration',M,'Actual old source verifies two supplied triples; it does not list every eligible triple across a multi-line arrangement. A finite explicit incidence list can establish the math; actual image reading remains separate.',['_collinear_and_offline'],asset=True)
setd(['angle_count_ray_pairs'],'angle_ray_pair_enumeration',M,'Classifying a single given angle does not enumerate unordered ray pairs and compound/straight-angle conventions.',['_given_angle_measure_and_vertex'],asset=True)
setd(['gridangleconstruction','grid_angle_construction'],'prescribed_grid_angle_construction',M,'Existing right-angle and generic ruler/protractor plans do not specify a particular nonright grid ray or verify its prescribed angle. Original G4 locators resolve the prior missing locator.',['_given_angle_measure_and_vertex','_read_scale_starting_on_right'],asset=True)
setd(['tornplaceclass_strip_assembly','placeclass_strip_assembly'],'placeclass_torn_strip_constraints',M,'Place-value reading does not order torn strips using matching connectors. G4pp43-44 provide locators; need exact strip boundaries/labels and legal adjacency.',['_place_value_zero'],asset=True)
setd('physical_geometric_construction','observed_physical_geometric_result',A,'Actual valid sources already give ruler/eke/compass placement and checks while withholding unobserved product claims. Accurate drawing, kite/rod construction, track setup require observed asset/execution.',['_acute_altitude_plan','_circle_compass_plan'],asset=True)
for c,master,reason in [
 ('glyph_segment_relation_filter','glyph_parallel_perpendicular_filter','Shape names alone do not filter a glyph inventory by simultaneous parallel/perpendicular segment relations; explicit glyph edges needed.'),
 ('midpoint_grid_dissection','midpoint_grid_multi_piece_dissection','Ruler midpoint and two-triangle restoration do not specify multi-piece midpoint cuts and a complete coverage proof.'),
 ('hidden_vertex_parallelogram','missing_parallelogram_vertex','Known area/perimeter does not reconstruct the missing vertex from parallel opposite sides; multiple possible orientations must be retained.'),
 ('fixed_piece_assembly_feasibility','fixed_piece_assembly_feasibility','Guaranteed restore does not prove feasible/impossible arbitrary target under fixed-piece geometry and legal transforms.'),
 ('paper_fold_cut_symmetry','fold_cut_unfold_boundary','Restoring known pieces does not propagate a cut through folds to determine unfolded boundary/symmetry.'),
 ('layering_order_occlusion','occlusion_partial_layer_order','Fixed total queue order does not infer partial layer order from occlusion or report multiple consistent full orders.'),
 ('area_preserving_cut_rearrangement','specified_area_preserving_dissection','Citing cut-to-rectangle in a formula reason is not a fully specified partition/translation with no-overlap/no-gap and area-versus-perimeter distinction.'),
 ('two_dimensional_attribute_pattern','two_dimensional_feature_constraints','One-dimensional periodic pattern does not combine independent row/column attribute constraints in a matrix; underdetermined completions must be retained.')]:
 setd(c,master,M,reason,['_diagonal_cut_restore','topic:periodic_attribute_pattern'],asset=True)
setd('composite_polygon_count','nonaxis_composite_quadrilateral_enumeration',M,'Published G3 triangles and axis-aligned rectangles do not enumerate composite rhombi/parallelograms in different edge arrangements. Share enumeration method but preserve this finite geometric subform.',['topic:composite_polygon_enumeration'],asset=True)
setd('optical_illusion_measurement_guard','optical_illusion_measurement_asset',A,'Endpoint measurement and withholding unsupported claims are explicit. Assessing the particular illusion needs actual ruler/parallel evidence, not another guessed numerical answer.',['_cm_misconception_endmark','_guard_no_drawing_evidence'],asset=True)

# Remaining G4 explicit prior exact coverage and genuine pending merged relations.
for c,t in [('capacity_feasible_cargo','exact_capacity_bound'),('inclusive_arithmetic_progression_count','constant_step_sequence'),('instrument_scale_reading','equal_interval_instrument_reading'),('intervals_vs_posts_both_endpoints','inclusive_positions_intervals'),('expression_filtered_network_route','predicate_filtered_directed_path')]:
 setd(c,t,C,'Prior actual nearest full fields work this same relation and boundary convention. Specific image/physical asset remains separate. Reused exact references are retained per candidate.',asset=True)
for c,master,reason in [
 ('capacity_constrained_network_route','capacity_edge_filtered_path','Existing path has node predicates; capacity belongs to an edge and must be checked for every traversed bridge while preserving connectivity.'),
 ('jump_skip_nodes_interpretation','skip_intermediate_nodes_k_plus_one','Moving k spaces excludes start, whereas skipping k intermediate nodes lands after k+1 edges. Must state exact convention and work it.'),
 ('two_draw_color_multisets','bounded_color_multiset_without_replacement','One draw does not enumerate unordered pairs constrained by available multiplicities; ordered draws must not be counted twice.'),
 ('finite_inventory_collection_state','finite_inventory_collection_game','Position updates do not remove/own inventory, preserve token identity versus equal value, and apply win thresholds.'),
 ('ambiguous_game_inventory_guard','inventory_rule_termination_guard','Unknown response branch guard does not resolve conflicting eligible-inventory versus stopping-count rules; ask precise missing rule without silently repairing it.'),
 ('overlap_length_bar_alignment','overlap_shared_origin_lengths','Endpoint subtraction alone does not solve simultaneously shifted bars from shared overlap/endpoints; explicit common origin is required.'),
 ('equal_area_transfer_cancellation','equal_area_transfer_cancellation','Concrete equal triangle exchange/common-area cancellation needs a specified partition and invariance proof.'),
 ('missing_current_year_context','missing_calendar_reference_guard','Actual calendar guard explicitly refuses to substitute machine current date; reference year absence uses the same missing-context principle.'),
 ('matchstick_removal_game_terminal_state','edge_removal_game_terminal','Static shape enumeration does not simulate turns or quantify that no target composite shape remains at termination.')]:
 setd(c,master,C if c=='missing_current_year_context' else M,reason,['_guard_date_without_calendar'] if c=='missing_current_year_context' else (),asset=c in ['overlap_length_bar_alignment','equal_area_transfer_cancellation','matchstick_removal_game_terminal_state'])

# Cross-grade G3V2 receipts supplied after the original G3 candidate adjudication.
for c,master,reason in [
 ('composite_polygon_enumeration','composite_polygon_enumeration','The published nine spatial rows close triangles/axis-grid rectangles only; arbitrary nonaxis quadrilaterals remain under their separate missing master.'),
 ('collinear_enumeration_and_segment_pairs','collinear_triple_complete_enumeration','Exact old row verifies given triples, not all triples/segments from a finite incidence structure.'),
 ('two_draw_multiset_without_replacement','bounded_color_multiset_without_replacement','Finite unordered outcomes require multiplicity bounds and no double-counting.'),
 ('finite_inventory_collection_game','finite_inventory_collection_game','Collection ownership/removal/win threshold is not established by basic board position updates.'),
 ('non_overlapping_activity_interval_choice','nonoverlapping_schedule_interval_choice','Adding durations does not select a feasible set of nonoverlapping activities under endpoint-touch conventions.')]:
 setd(c,master,C if c=='composite_polygon_enumeration' else M,reason,['topic:composite_polygon_enumeration'] if c=='composite_polygon_enumeration' else (),asset=c=='composite_polygon_enumeration')

# G5 all 63 observed candidate IDs, including candidates never adjudicated before.
G5={
 'date_encoding':('date_digit_string_encoding',M,'Natural-number place-value reading does not encode a date by a specified concatenation convention with possible leading zeros.','_place_value_zero'),
 'even_sequence':('constant_step_sequence',C,'Consecutive even values have declared constant step2; accepted inclusive step-two enumeration works that relation.','sgk_gap_20261019_g4_parity_cards_inclusive_error'),
 'swap_optimization':('one_swap_parity_extremum',M,'Minimum swaps to sort a permutation does not maximize an odd numeral under exactly one digit swap; parity and one-swap objective must both hold.','topic:minimum_pair_swaps'),
 'multicolumn_constraint':('partial_product_column_reconstruction',M,'Published coupled blanks cover addition/subtraction; missing shifted partial products in multiplication are not worked.','topic:column_multi_blank'),
 'cancellation':('structural_product_cancel',C,'Accepted exact source cancels common product structure with nonzero denominator; changing factors/fractions preserves the cancellation relation.','topic:structural_product_cancel'),
 'fraction_interval':('strict_fraction_unknown_numerator_interval',M,'Known fraction comparison and decimal interval selection do not synthesize all numerator digits under two strict unlike-fraction bounds.','_open_interval_records'),
 'zoom_line':('equal_interval_numberline_refinement',C,'Actual partitioned-unit source computes fractional step, adds starting anchor and checks interval; labelled instrument interpolation uses arbitrary endpoint interval size. Decimal sub-tenth zoom changes scale.','sgk_kntt_g5_gap_20261019_008'),
 'unknown_fraction_operator':('finite_operator_synthesis',M,'A known fraction expression is not choice of plus/minus under equality; share finite operator-synthesis master and keep fraction operands.','topic:expression_choice'),
 'sharing_schemes':('compare_equal_sharing_cut_schemes',M,'Fraction amount/equal-share formulas do not compare feasibility and equality of two specific cutting/distribution schemes while tracking piece inventory.','topic:fraction_division_model'),
 'pack_unit_choices':('piece_pack_unit_role_choice',M,'Mixed-number conversion does not choose whether an unknown counts pieces or packs under equal sharing; quantities need role/unit disambiguation.','_whole_parts_to_fraction'),
 'rectangle_tiling':('mixed_orientation_rectangle_tiling',M,'Generic right-angle drawing does not tile a rectangle with fixed smaller rectangles under mixed orientations and no gaps/overlap.','_acute_altitude_plan'),
 'weighted_mean':('weighted_group_mean',C,'Actual old row reconstructs a4-day group total from mean and group size, adds a1-day group, divides by5 and explains why unweighted mean of two summaries is wrong. Bus groups use identical weighting relation.','_extend_mean_reconstruct_four_day_total'),
 'remainder_base':('successive_fraction_of_current_remainder',M,'Old fraction_of_remainder row removes one fraction of original then adds a known amount; another row explicitly uses original base. Neither applies a second fraction to the updated remainder.','cloud_pedagogy_v3_039'),
 'decimal_card_enumeration':('finite_decimal_digit_card_enumeration',M,'Integer digit-card enumeration exists, but fixed decimal-point slots, leading/trailing0, equal numerical values versus distinct card arrangements and decimal extrema need explicit treatment.','sgk_gap_20261019_g4_parity_cards_two_digit_zero'),
 'tile_boxes':('whole_package_area_procurement',M,'Ceiling transport capacity is present; tiled area to required tiles to whole boxes and budget is a specific multi-unit procurement chain with waste assumptions absent from nearest area/ceiling examples.','topic:minimum_capacity'),
 'materials_budget':('bill_of_materials_area_cost',M,'Simple rectangle/circle area is present; area of multiple counted boards plus per-area price and open design/budget constraints is not worked.','_lateral_and_closed_surface'),
 'grid_hole_dimensions':('grid_boundary_missing_dimensions',M,'Known-size area conversion does not infer rectangle dimensions from incomplete boundary unit cells; need exact outer grid-edge structure, cell scale and holes.','_square_metric_grid'),
 'three_masses':('three_unknown_pair_totals',M,'One missing addend and two-value sum/difference do not reconstruct three stable identities from pair sums/alltotal with consistency check.','_combine_then_remove'),
 'folded_visible_area':('repeated_fold_visible_area',M,'An area formula does not count folded layers or distinguish original from visible footprint after repeated folds. Need orientation/fold positions.','_diagonal_cut_restore'),
 'nested_altitudes':('nested_triangle_base_altitude_assignment',M,'A single given base/height and obtuse foot plan do not pair several nested triangle bases with their correct perpendicular heights.','_obtuse_external_foot'),
 'tangram_area':('midpoint_tangram_piece_area',M,'Generic fraction/triangle area does not derive tangram piece areas from square midpoint dissection and equal-area relations.','_triangle_area_imagined_pair_and_height'),
 'rotated_trapezoid':('rotated_trapezoid_completion',M,'Grid plan/classification has known vertices; selecting alternative completions in rotated orientations requires applying parallel-base constraints to incomplete figures.','exhaustive_structure_g5_grid_trapezoid_plan'),
 'trapezoid_derivation':('specified_area_preserving_dissection',M,'Worked trapezoid formula/reverse height does not provide the specific midpoint cut/rearrangement derivation with no-gap/no-overlap.','_reverse_trapezoid_height_then_remove_corner'),
 'circle_center_chain':('nested_circle_center_construction',M,'One compass circle plan does not locate subsequent centers on previous circles and construct nested/mixed-unit circle chains under their constraints.','_circle_compass_plan'),
 'circle_overlap':('circle_material_overlap_allowance',M,'Circumference without joining allowance is present; explicit material needed with specified overlap/free-end addition is not worked.','_diameter_edge_vs_disc_surface'),
 'semicircle_chain':('semicircle_chain_arc_length',M,'One circumference formula does not compare one semicircle arc with a chain of smaller semicircle arcs and explain diameter additivity.','_diameter_edge_vs_disc_surface'),
 'disk_derivation':('disk_sector_limit_area_argument',M,'Using radius-square formula is present, not the sector rearrangement/approximation argument relating limiting rectangle sides and area. Must distinguish finite approximation from exact disk.','_radius_area_explicit_pi'),
 'stadium':('stadium_composite_area',M,'Single disk/annulus area does not combine a rectangle and two matched semicircles while distinguishing fulldiameter from radius/rectangle dimensions.','_annular_border'),
 'semicircle_boundary':('semicircle_arc_plus_diameter_boundary',M,'Full-circle circumference and diameter definition are present; a semicircle full boundary explicitly needs half circumference plus diameter.','_diameter_edge_vs_disc_surface'),
 'triangle_parallel_apex':('triangle_parallel_apex_area_invariant',M,'Known base-height formula does not demonstrate an apex sliding on a parallel line preserves height/area.','_triangle_area_imagined_pair_and_height'),
 'triangle_base_ratio':('same_height_triangle_area_ratio',M,'Shared-height corner-removal example establishes a usable common altitude, but not proportional comparison/equal base subdivision of several triangle areas.','_reverse_trapezoid_height_then_remove_corner'),
 'decimal_symbol_choice':('decimal_symbol_open_interval_synthesis',M,'Selecting known decimal records within an open interval is present; inserting a legal symbol into a written digit string to satisfy both strict bounds has additional syntax/slot constraints.','_open_interval_records'),
 'decimal_whole_pieces':('whole_units_from_decimal_quotient',M,'Old decimal division examples divide exactly, and integer fullbag examples keep remainders. Floor to whole pieces from a nonintegral decimal quotient with leftover material is not worked.','_decimal_divisor_equal_scale'),
 'circle_feasibility':('circular_rim_capacity_feasibility',M,'Circle circumference and numeric capacity checking are present independently; comparing maximum stretch to required rim length with allowed overlap needs explicit elastic-bound interpretation.','_diameter_edge_vs_disc_surface'),
 'wheel_rotations':('wheel_turns_distance',M,'Circumference formula does not explicitly relate rolling turns to travelled distance under no-slip assumption and unit conversion.','_diameter_edge_vs_disc_surface'),
 'future_age_ratio':('future_age_invariant_difference_ratio',M,'Static difference-ratio source does not propagate both ages equally to a future ratio and use invariant difference.','_difference_ratio_book_piles'),
 'cashback_threshold':('conditional_cashback_threshold',M,'Uniform percentage discount lacks branch eligibility/minimum spend and cashback base/rules; preserve threshold inclusivity and distinguish gross/net amount.','_percentage_using_basic_keys_without_percent_key'),
 'equal_volume_surface':('fixed_volume_surface_arrangement_optimization',M,'Old source compares equal material volume in different arrays; published small assembly counts exposed faces. Neither enumerates arrangements and minimizes lateral/total area for fixed volume with explicit orientation.','_same_cube_volume_different_arrangements'),
 'joined_surface':('assembled_cube_painted_faces',C,'Accepted assembly row explicitly removes both sides of each glued face, includes bottom and counts all exposed small faces. Multiplying by each smallface area is established square area, same incidence relation.','topic:assembled_cube_painted_faces'),
 'displacement':('submerged_displacement_volume',C,'Prior actual nearest full-field adjudication establishes immersed object displacement versus water-level rise and overflow conditions; exact old references retained.'),
 'net_volume':('gridded_net_dimensions_to_volume',M,'Net validity/opposite faces and volume formulas are present; infer all dimensions from an actual gridded net with fold adjacency is not worked.','_cuboid_strip_and_matching_caps'),
 'clock_error':('slow_fast_clock_correction',M,'Elapsed duration arithmetic is present; correcting displayed time by an explicit accumulated fast/slow error needs signed error/reference rule.','_overnight_trip_elapsed_vs_active_time'),
 'piecewise_terrain':('piecewise_speed_travel_time_comparison',M,'Old uniform ride with a rest and total trial speed are present; different segment speeds and time sums require segment-specific distance/speed pairing and prohibit unweighted speed averaging.','_arrival_after_uniform_ride_and_one_rest'),
 'train_length':('finite_train_tunnel_bridge_crossing',M,'Point-motion remaining distance does not add the finite train length for tail clearance or invert bridge-crossing distance to infer train length.','original_tutor25_g5_04'),
 'interval_frequency':('interval_bin_boundary_frequency',M,'Exact-value frequency table is present; halfopen/closed numeric bins need boundary assignment once per observation, particularly values on shared endpoints.','_raw_lengths_frequency'),
 'frequency_weighted_mean':('frequency_table_weighted_mean',M,'Unequal group mean relation exists but raw ratings with frequency tables require weighting each value by frequency, total counts, and zero-frequency handling explicitly.','_extend_mean_reconstruct_four_day_total'),
 'pair_guarantee':('two_color_three_draw_pair_guarantee',M,'Observed frequency and possibility words do not prove a guaranteed equal-color pair among three selections from two colors. Need finite exhaustive argument/pigeonhole and inventory conditions.','_observed_frequency_not_fixed_next_block'),
 'overlap_length':('overlap_shared_origin_lengths',M,'Combining two nonoverlapping ropes is present; overlap joined length subtracts doubly counted overlap under fixed alignment, shared master with G1/G4 bars.','_combine_then_remove'),
 'compound_interest':('finite_reinvested_compound_percent',M,'Old interest task explicitly says no reinvestment and constant original principal. Reinvested year2 must apply percent to changed principal, not reuse simple-interest base.','_misconception_monthly_interest_vs_whole_period'),
 'painted_cubes':('large_cube_painted_face_classification',M,'Accepted2/3/4-cube assemblies count exposed faces. A fully n-by-n-by-n painted cube requires corner/edge/face-interior/interior classification, not covered by those small arrangement cases.','topic:assembled_cube_painted_faces'),
 'surface_volume_scaling':('edge_scale_square_cube_relation',M,'Old source distinguishes surface and volume dimensions but does not compare simultaneous edge scaling and derive area factor k² versus volume factor k³.','_cube_one_face_total_surface_vs_solid_volume'),
 'multidraw_outcomes':('bounded_color_multiset_without_replacement',M,'Singledraw outcome/frequency examples do not enumerate unordered color multisets with bounded supply; same missing G2/G3/G4 master.','_observed_frequency_not_fixed_next_block'),
}
for k,(master,status,reason,*extra) in G5.items():
 c='g5_candidate_'+k
 if c in decisions:continue
 setd(c,master,status,reason,extra,asset=k in ['rectangle_tiling','grid_hole_dimensions','folded_visible_area','nested_altitudes','tangram_area','rotated_trapezoid','trapezoid_derivation','circle_center_chain','disk_derivation','net_volume','painted_cubes'])
setd('g5_source_caveat_leap_year','gregorian_leap_year_convention',M,'Actual source describes a supplied February ending on29; it does not teach the Gregorian divisible-by4, century, divisible-by400 rule. The book simplification must be scoped; do not extend every4years through non400centuries.',['_february_calendar_boundary'])

# Deeper nearest-source reread found actual arbitrary weekday and month rollover
# offsets; the earlier lookup/+7-only comparison was too narrow.
setd('G1V2_CALENDAR_ANCHOR_OFFSET','calendar_anchor_day_offset',C,'Actual schedule source explicitly counts Monday to Saturday as5days and computes1+5=6. Month-boundary source counts four transitions without counting start. These demonstrate anchor-to-other-weekday/date offset; G1 wording adaptation is separate.',['sgk_gap_20261019_g3_calendar_occurrences_schedule','_calendar_month_boundary'])
setd('non_overlapping_activity_interval_choice','nonoverlapping_schedule_interval_choice',M,'Actual old duration source is explicitly continuous and only computes end-start; time-budget source explicitly states activities do not overlap. Neither selects a feasible set from potentially overlapping intervals or applies endpoint-touch rules. Finite observed G3V2p84 activity-choice subform remains missing.',['_elapsed_same_day','_activity_durations_sum_and_budget_remainder'])

# G2 is not re-adjudicated or authored here. These references identify the shared
# master and retain G2 branch-specific work; a covered related master must not
# silently close repeated-card, clock-motion or picture-specific G2 branches.
G2_ALIASES={
 'G1V1_CURVED_CONNECTION_TRACING_ASSET':'curved_connection_image',
 'G1V2_ATTRIBUTE_FILTERED_EXTREMA':'attribute_filter_then_extremum',
 'G1V2_CALENDAR_ANCHOR_OFFSET':'calendar_anchor_day_offset',
 'G1V2_ELAPSED_WHOLE_HOURS':'elapsed_time_intervals',
 'G1V2_PREDICATE_PATH_ASSET':'predicate_filtered_directed_path',
 'G1V2_ROLE_POOL_EQUATION_CONSTRUCTION':'role_specific_equation_pool',
 'G1V2_ROUTE_TOTAL_LENGTH_COMPARISON':'finite_route_total_optimization',
 'G1V2_SORT_REPAIR_ONE_SWAP':'minimum_pair_swaps',
 'G1V2_TWO_DIGIT_NUMBER_CARD_CONSTRUCTION':'finite_digit_card_enumeration',
 'G1_RESOURCE_ASSIGNMENT_CAPACITY_BRANCH':'resource_assignment_inequality',
 'G2_SOLID_TOP_FACE_VISIBILITY':'solid_visible_face_direction_binding',
 'G2_HIDDEN_UNIT_CUBE_ASSEMBLY':'unit_cube_layers_assembly',
 'G3_AREA_PRESERVING_CUT_REARRANGEMENT':'specified_area_preserving_dissection',
 'G3_BALANCE_RELATION_CHAIN':'balance_order_substitution_chain',
 'G3_BOUNDED_MEASURE_SUBSET':'bounded_inventory_target_sum',
 'G3_COLLINEAR_ALL_SEGMENT_ENUMERATION':'collinear_triple_complete_enumeration',
 'G3_COLLINEAR_ENUMERATION':'collinear_triple_complete_enumeration',
 'G3_COMPOSITE_POLYGON_ENUMERATION_ASSET':'composite_polygon_enumeration',
 'G3_FIXED_PIECE_ASSEMBLY_FEASIBILITY':'fixed_piece_assembly_feasibility',
 'G3_PAPER_FOLD_CUT_SYMMETRY':'fold_cut_unfold_boundary',
 'G3_PHYSICAL_GEOMETRIC_CONSTRUCTION':'observed_physical_geometric_result',
 'G3_SILHOUETTE_PIECE_GRID_REPRODUCTION':'fixed_piece_silhouette_placement',
 'G3_TWO_JUG_TRANSFER':'two_jug_state_transfer',
 'G4_BALANCE_ORIENTATION_ORDER':'balance_order_substitution_chain',
 'G4_COLUMN_MULTI_BLANK_RELATION':'column_multi_blank',
 'G4_DIGIT_INEQUALITY_RELATION':'digit_inequality',
 'G4_FINITE_INVENTORY_AND_OWNERSHIP_STATE':'finite_inventory_collection_game',
 'G4_INSTRUMENT_SCALE_READING_ASSET':'equal_interval_instrument_reading',
 'G4_INTERVALS_VS_POSTS_BOTH_ENDPOINTS':'inclusive_positions_intervals',
 'G4_JUMP_SKIP_NODES_INTERPRETATION':'skip_intermediate_nodes_k_plus_one',
 'G4_MISSING_PERSONAL_DATE_OR_TIMETABLE_CONTEXT':'missing_calendar_reference_guard',
 'G4_OVERLAP_LENGTH_BAR_ALIGNMENT':'overlap_shared_origin_lengths',
 'G4_SEVEN_SEGMENT_RELOCATION':'seven_segment_glyph_inventory_relocation',
 'G4_TWO_DRAW_COLOR_MULTISETS':'bounded_color_multiset_without_replacement',
}

def main():
 missing=set(records)-set(decisions)
 if missing: raise ValueError('unresolved decisions '+repr(sorted(missing)))
 # Restore substantive old nearest references, then add curated closer examples.
 for c,z in records.items():
  d=decisions[c];z['nearest_ids']=list(dict.fromkeys(d['support_ids']+z['nearest_ids']))
  # Exact coverage may rely on prior documented actual IDs but never empty refs.
  if d['category']==C and not z['nearest_ids']:raise ValueError('covered without source '+c)
  if not z['nearest_ids']:
   # Shared canonical masters inherit exact nearest rows, not a closure status.
   peers=[a for a in records if decisions[a]['master_id']==d['master_id']]
   z['nearest_ids']=list(dict.fromkeys(s for a in peers for s in (decisions[a]['support_ids']+records[a]['nearest_ids'])))
  if not z['nearest_ids']: d['category']=P;d['semantic_comparison']+=' No actual nearest source could be retained; comparison must be completed before authoring.'
 for c,z in records.items():
  d=decisions[c]
  z['decision']={k:v for k,v in d.items() if k!='support_ids'}
  z['nearest_refs']=[{k:V[s][k] for k in ['sample_id','source_file','line','sha256']} for s in z.pop('nearest_ids')]
  z['prior_statuses']=list(dict.fromkeys(str(a.get('status')) for a in z.pop('prior_adjudications') if a.get('status')))
  z['page_receipts']=list({json.dumps(p,sort_keys=True):p for p in z['page_receipts']}.values())
 for o in occ:o['master_id']=decisions[o['candidate_id']]['master_id'];o['category']=decisions[o['candidate_id']]['category']
 masters=collections.defaultdict(list)
 for c,z in records.items():masters[z['decision']['master_id']].append(c)
 queue=[]
 for m,cs in sorted(masters.items()):
  cats={decisions[c]['category'] for c in cs}
  category=P if P in cats else M if M in cats else A if A in cats else C
  ss=list(dict.fromkeys(r['sample_id'] for c in cs for r in records[c]['nearest_refs']))
  queue.append({'master_id':m,'category':category,'candidate_ids':cs,'candidate_occurrence_count':sum(o['candidate_id'] in cs for o in occ),'owner':next((decisions[c]['owner'] for c in cs if decisions[c]['owner']!='UNASSIGNED'),'UNASSIGNED'),'reasons':list(dict.fromkeys(decisions[c]['semantic_comparison'] for c in cs)),'nearest_refs':[{k:V[s][k] for k in ['sample_id','source_file','line','sha256']} for s in ss],'actual_page_receipts':list({json.dumps(p,sort_keys=True):p for c in cs for p in records[c]['page_receipts']}.values()),'physical_or_image_assets_complete':False,'next_action':'Reuse exact source/hash; retain original visual/physical limits.' if category==C else 'Acquire/describe observed asset; do not duplicate existing mathematical text.' if category==A else 'Author finite original subform from exact specification; independent oracle and cross-review required.' if category==M else 'Read actual nearest full fields before deciding/authoring.'})
 g2=read('g2v2_audit/g2_combined_candidate_adjudication.json')
 external=[]
 for x in g2['finite_master_resume_queue']:
  gm=x['finite_master_id']
  if gm in G2_ALIASES:
   external.append({'g2_master_id':gm,'crossgrade_master_id':G2_ALIASES[gm],'g2_original_candidate_refs':x['candidate_refs'],'prior_g2_status':x['status'],'scope':'Related master alias only. G2 branch-specific semantics/grade/assets are not automatically closed; no G2 adjudication/source/queue mutated.','g2_confirmed14_overlap':False})
 dump('external_g2_aliases.json',{'source_file':'g2v2_audit/g2_combined_candidate_adjudication.json','source_sha256':sha(RUN/'g2v2_audit/g2_combined_candidate_adjudication.json'),'aliases':external,'g2_confirmed14_owned_elsewhere':True,'unmatched_g2_masters_untouched':True})
 used=set(r['sample_id'] for z in records.values() for r in z['nearest_refs'])
 used.update(s for s,z in V.items() if z['source_file']=='release/accepted_cases.jsonl')
 with (BASE/'nearest_fullfields.jsonl').open('w',encoding='utf-8',newline='\n') as f:
  for s in sorted(used):
   x=V[s];r={k:x[k] for k in ['sample_id','source_file','line','sha256']};r['grade']=x['row']['grade'];r['split']=x['row'].get('split','train');r['semantic_field_values']={k:x['row'].get(k) for k in SEM};r['source_row']=x['row'];f.write(json.dumps(r,ensure_ascii=False)+'\n')
 published=[{'sample_id':s,'source_row_sha256':z['sha256'],'source_file':z['source_file'],'line':z['line'],'family':z['row']['topic'],'accepted_status':z['row'].get('acceptance_status'),'matched_candidate_ids':[c for c in records if s in [r['sample_id'] for r in records[c]['nearest_refs']] or decisions[c]['master_id']==z['row']['topic']],'numeric_variants_not_independent_forms':True} for s,z in V.items() if z['source_file']=='release/accepted_cases.jsonl']
 mapping={'scope':'Finite recorded KNTT G1/G3/G4/G5 candidates and G3 crossgrade append locators only. All ten books previously actually read; no claim all legal curriculum or all SGK series. G2 original occurrences remain owned by separate G2 task. No protected/eval/pilot payload inspection, authoring, training, app changes, Drive mutation or registry/context/state changes.','category_definition':{C:'Demonstrated mathematical text relation supported by exact valid training source ID and raw line hash; crossgrade wording fit and actual image/physical recognition are not certified.',M:'Genuine added finite constraint/representation demonstrated absent in the inspected nearest actual training fields; bounded comparison, not parser/keyword absence or universal archive absence.',A:'Underlying mathematical text relation present; missing evidence is actual visual/physical/contextual asset.',P:'Actual source comparison still required; never counted covered.'},'original_candidate_records':len(records),'original_occurrences':len(occ),'candidate_category_counts':dict(collections.Counter(z['decision']['category'] for z in records.values())),'master_category_counts':dict(collections.Counter(q['category'] for q in queue)),'published_accepted_rows':len(published),'published_accepted_families':len(set(x['family'] for x in published)),'candidates':list(records.values()),'occurrences':occ,'published110_mapping':published,'source_receipt_file_sha256':receipt_files,'protected_payloads_used':False,'authoring_performed':False}
 dump('mapping.json',mapping);dump('resume_queue.json',{'scope':mapping['scope'],'master_count':len(queue),'masters':queue,'priority_small_text_master_ids':['product_pyramid','two_jug_state_transfer','finite_operator_synthesis','bounded_factor_pair_enumeration','bounded_inventory_target_sum','balance_order_substitution_chain','calendar_anchor_day_offset','repeated_value_identity_assignment','two_group_transfer_then_compare','ordered_itinerary_weekday_map','arrival_schedule_eligibility','strict_fraction_unknown_numerator_interval','successive_fraction_of_current_remainder','three_unknown_pair_totals','future_age_invariant_difference_ratio','slow_fast_clock_correction','conditional_cashback_threshold','finite_reinvested_compound_percent','interval_bin_boundary_frequency','two_color_three_draw_pair_guarantee']})
 evidence={'hash_basis':'SHA256 exact UTF8 JSONL line excluding line terminator; full source files also hashed','source_file_sha256':{p:sha(RUN/p) for p in ['current_sources.jsonl','release/accepted_cases.jsonl']+files},'valid_old_training_rows':sum(z['source_file']=='current_sources.jsonl' for z in V.values()),'accepted_release_rows':len(published),'nearest_actual_fullfield_rows':len(used),'receipt_hashes':receipt_files,'checks':{'every_original_candidate_has_decision':set(records)==set(decisions),'all_occurrences_resolve':all(o['candidate_id'] in records for o in occ),'all_covered_have_exact_source_refs':all(z['nearest_refs'] for z in records.values() if z['decision']['category']==C),'all_nearest_train_only':all(V[s]['row'].get('split','train')=='train' and not re.search('holdout|eval|pilot|protected',s,re.I) for s in used),'all110_mapped_exactly_once':len(published)==110 and len(set(x['sample_id'] for x in published))==110,'published_families40':len(set(x['family'] for x in published))==40,'no_merge_implies_coverage':True,'source_files_immutable':True},'limits':['Nearest references are bounded actual semantic comparisons; no keyword/parser absence used as semantic proof.','Actual image/physical outcome certification remains false even when text relation is covered.','Grade-specific instructional fit remains an adaptation constraint, not automatic within-grade coverage.','No full curriculum/all-series assertion.']}
 dump('validation.json',evidence)
 dump('artifact_hashes.json',{p:sha(BASE/p) for p in ['mapping.json','resume_queue.json','nearest_fullfields.jsonl','external_g2_aliases.json','validation.json','build_mapping.py']})
 print(json.dumps({'candidate_count':len(records),'occurrences':len(occ),'masters':len(queue),'categories':mapping['master_category_counts'],'candidate_categories':mapping['candidate_category_counts'],'fullfields':len(used),'checks':evidence['checks']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()

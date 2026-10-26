"""Finite G2 candidate adjudication. Reads train-only source rows; does not author data."""
import json, hashlib, pathlib, collections, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUN = ROOT / 'thinking/cloud_publication/sgk_page_audit_20261019'
OUT = RUN / 'g2v2_audit'
def sha(b): return hashlib.sha256(b).hexdigest()
def dump(path, obj): path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf8')

# All these rows were actually read in full task fields in this review turn or its
# retained same-agent checkpoint. The receipt below preserves exact inspected bytes.
ALIASES = {
 'grid':'sgk_g12_20261019_hundred_grid_patch_01',
 'bins':'sgk_g12_20261019_expression_target_classification_02',
 'pyramid':'sgk_g12_20261019_sum_pyramid_02',
 'path':'sgk_g12_20261019_constrained_arithmetic_path_01',
 'bounds':'sgk_page_g1_20261019_two_sided_strict_bound_selection_01',
 'ordinal':'sgk_page_g1_20261019_ordinal_from_both_ends_02',
 'column':'sgk_page_20261019_g4_column_multi_blank_exchange',
 'digit':'sgk_page_20261019_g4_digit_inequality_strict_low',
 'pour':'primary_20261017_g2_mass_capacity_0016_pour_to_full_without_loss',
 'balance':'primary_20261017_g2_mass_capacity_0016_balance_equal_weights',
 'estimate':'primary_20261017_g2_compare_estimate_0010_estimate_from_ten_reference',
 'lengthestimate':'primary_20261017_g2_measurement_0021_estimate_with_reference_scale',
 'line':'primary_20261017_g2_geometry_0013_segment_line_curve',
 'collinear':'primary_20261017_g2_geometry_0013_collinear_and_offline',
 'polyline':'primary_20261017_g2_geometry_0013_trace_polyline_segments',
 'draw':'primary_20261017_g2_drawing_assembly_0015_draw_from_zero',
 'measureguard':'primary_20261017_g2_drawing_assembly_0015_guard_unmeasured_drawing',
 'ray':'primary_20261017_g2_numbers_ray_0009_ray_two_different_scales',
 'calendar':'primary_20261017_g2_time_calendar_0018_february_calendar_boundary',
 'surveyguard':'primary_20261017_g2_tally_0023_guard_incomplete_survey',
 'tiling':'primary_20261017_g2_drawing_assembly_0015_tile_grid_with_horizontal_piece',
 'calendar_guard':'primary_20261017_g2_time_calendar_0018_guard_february_year_or_calendar',
 'payment':'primary_20261017_g2_money_0020_select_exact_payment_cards',
 'survey':'primary_20261017_g2_tally_0023_survey_one_choice_per_child',
 'cards':'sgk_gap_20261019_g4_parity_cards_two_digit_zero',
 'measuringplan':'primary_20261018_g3_practice_experience_0093_capacity_activity_compare_measuring_plans',
 'weightguard':'primary_20261018_g2_practice_experience_0092_guard_real_bag_weight_missing_scale_evidence',
 'equations':'sgk_page_g1_20261019_construct_equations_from_number_cards_01',
 'filter':'primary_20261018_g4_data_sequences_0067_filter_threshold_then_descending_labels',
 'board1':'sgk_g12_20261019_conditional_board_game_01',
 'board2':'sgk_g12_20261019_conditional_board_game_02',
 'sort':'sgk_page_20261019_g4_minimum_pair_swaps_cycle',
 'composite':'sgk_page_spatial_20261019_composite_polygon_enumeration_01',
 'scale':'primary_20261017_g3_new_units_0040_graduated_vessel_equal_intervals',
 'interval':'cloud_pedagogy_v3_007',
 'inclusive':'sgk_gap_20261019_g4_parity_cards_inclusive_error',
 'cubes':'primary_20261018_finish_g5_cuboid_cube_volume_layers_unit_cubes',
 'ambiguous':'sgk_g4extra_20261019_geometric_sequence_local_extension_02',
 'cycle':'sgk_g4extra_20261019_closed_operation_cycle_01',
}
FIELDS = ['problem','givens','requested_quantity','student_work','initial_guidance','hints','worked_steps','expected_answer']
sources = {}
for rel in ['current_sources.jsonl','release/accepted_cases.jsonl','g4_remaining_append/cases.jsonl']:
    p=RUN/rel
    for n,raw in enumerate(p.read_bytes().splitlines(),1):
        r=json.loads(raw); sid=r.get('sample_id','')
        if r.get('split','train')!='train' or re.search(r'holdout|eval|pilot|protected',sid,re.I): continue
        if sid not in ALIASES.values(): continue
        entry={'sample_id':sid,'grade':r.get('grade'),'source_file':rel,'source_line_number':n,
               'source_row_sha256':sha(raw),'hash_basis':'Exact UTF-8 JSONL line bytes excluding line terminator',
               'split':r.get('split','train'),'task_fields':{k:r.get(k) for k in FIELDS},
               'review':'ACTUAL_FULL_TASK_FIELDS_READ_SEMANTICALLY',
               'reviewer':'finish_g2_mapping',
               'human_review_claimed':False,'external_review_claimed':False}
        if sid not in sources: sources[sid]=entry
        elif sources[sid]['source_row_sha256']!=entry['source_row_sha256']:
            # Final root release may apply authorized acceptance overlays. Keep the
            # inspected original bytes and record alternate locations distinctly.
            sources[sid].setdefault('other_locations',[]).append({k:entry[k] for k in ['source_file','source_line_number','source_row_sha256']})
assert set(ALIASES.values())==set(sources), sorted(set(ALIASES.values())-set(sources))

# status, finite master, actual nearest full-field source aliases, semantic result.
M={}
def add(labels,status,master,refs,why):
    for label in labels.split('|'):
        assert label not in M,label
        M[label]=(status,master,refs.split(),why)

add('g1_two_sided_strict_bound_selection','COVERED','G1_STRICT_TWO_SIDED_BOUNDS','bounds',
    'Existing original G1 task tests every finite card against both strict endpoints and excludes equality. This is the same finite selection relation at the G2 page; no visual reading claim.')
add('g2_card_numeral_formation','MERGED_PENDING','G1V2_TWO_DIGIT_NUMBER_CARD_CONSTRUCTION','cards',
    'Nearest accepted card task enumerates only even two-digit numbers from 0,3,8. The G2 pages request all numerals, leading-zero exclusion and extrema difference; parity-filtered enumeration does not demonstrate that entire representation. Merge the unrestricted/zero branch with the existing card-construction master.')
add('grouped_visual_count_estimation|visual_estimate_reference','COVERED','G2_REFERENCE_GROUP_ESTIMATION_TEXT','estimate lengthestimate',
    'Existing grade2 tasks distinguish about four reference groups from an exact count and use a stated reference length. The mathematical estimation-and-certainty relation is present; identifying groups/reference size from each new publisher image remains visual work.')
add('g12_hundred_grid_patch','COVERED','G12_HUNDRED_GRID_PATCH','grid',
    'The inspected original row uses a ten-column patch, horizontal +1 and vertical +10, solves two missing cells and cross-checks the far corner. Same patch dependency, not mere number-word similarity.')
add('g1_ordinal_from_both_ends','COVERED','G1_ORDINAL_BOTH_ENDS','ordinal',
    'The inspected G1 row converts third-from-start among seven to fifth-from-end and counts before/after. This covers the order relation in the depicted lane; locating people in an image is not certified.')
add('role_specific_equation_matching','MERGED_PENDING','G1V2_ROLE_POOL_EQUATION_CONSTRUCTION','equations',
    'The accepted row uses one undifferentiated pool 2,5,7. It does not restrict each operand/result role to a separate supplied list. Keep the existing role-pool master open instead of duplicating the ordinary equation family.')
add('single_pair_sort_repair','MERGED_PENDING','G1V2_SORT_REPAIR_ONE_SWAP','sort',
    'Nearest new G4 permutation row minimizes arbitrary pair swaps and requires three swaps. The G2 request permits exactly one selected pair and asks the repair itself; its one-swap feasibility branch remains in the existing G1 master, despite common swap vocabulary.')
add('g12_expression_target_classification','COVERED','G12_EXPRESSION_TARGET_CLASSIFICATION','bins',
    'The row evaluates P,Q,R,S, preserves expression identities when equal, partitions by target3/5 and checks every label occurs once. This explicitly covers equal-value matching and finite target membership/counting.')
add('column_multi_blank|column_multiple_blank','COVERED','G4_COLUMN_MULTI_BLANK_RELATION','column',
    'The inspected new G4 row 8A2−3B7=425 derives the borrow dependency and enumerates all admissible digit pairs (0,7),(1,8),(2,9), checking the original column. Multiple interdependent blanks are present. This is relation-level coverage; a G2-scaled presentation remains enrichment, not required duplication.')
add('rule_inference_ambiguity','MERGED_PENDING','G2_VERTEX_SUM_RULE_WITH_AMBIGUITY_GUARD','pyramid ambiguous',
    'The G4 new source explicitly shows two continuations compatible with a finite prefix and asks for the missing rule; the sum-pyramid row supplies a different adjacent-pair dependency. Neither exercises inferring/checking a common vertex-sum rule from the page diagrams. Preserve that representation as a finite pending branch; the general ambiguity guard is already present.')
add('g12_conditional_board_game|boardgame_rules','COVERED','G12_CONDITIONAL_BOARD_GAME','board1 board2',
    'Two actual grade2 rows apply step count excluding the current square, jump transition, arithmetic verification and either staying or rollback to the original square. Both success and failure branches exist. Extra-turn/skip-turn G4 state is separate, already handled in its own append.')
add('additive_pyramid_constraints','COVERED','G12_ADJACENT_SUM_PYRAMID','pyramid',
    'The inspected row reverses a missing lower cell from a known parent sum, then propagates the adjacent sum through two levels and checks the top. Same additive constraint graph; a missing rule must still be asked for, not guessed from shape.')
add('solid_visible_face_directions','ASSET_PENDING','G2_SOLID_TOP_FACE_VISIBILITY','line cubes',
    'The page explicitly selects top dice faces while disregarding other faces. Text line classification and complete cuboid layer counts do not test directional face visibility/occlusion. Needs original face-labelled asset or a fully explicit visible-face representation; do not infer image competence.')
add('conjunctive_attribute_expression_filter|conjunctive_attribute_filter','MERGED_PENDING','G1V2_ATTRIBUTE_FILTERED_EXTREMA','filter bins',
    'The actual nearest rows separately implement threshold/stable order and expression-value grouping. The page combines visual colour/shape or truth condition with arithmetic selection/extrema. Keep the conjunction branch in the existing attribute-filter master; two separate component rows are not semantic proof of the combined task.')
add('unit_cube_count_assembly','ASSET_PENDING','G2_HIDDEN_UNIT_CUBE_ASSEMBLY','cubes tiling',
    'The inspected G5 row counts all layers of a complete 7×4×3 cuboid; the G2 pictured irregular structures require hidden-support/layer inference from a particular arrangement. A whole cuboid formula does not close the irregular visibility task or the grade2 representation.')
add('finite_inventory_collection_state|finite_inventory_game_state|finite_token_game|finite_board_ownership','MERGED_PENDING','G4_FINITE_INVENTORY_AND_OWNERSHIP_STATE','board1 board2',
    'The existing board sources track position and rollback, not the mutable collection inventory or occupied/owned cells. Merge into the preexisting finite_inventory_collection_state / ambiguous_game_inventory_guard master with explicit G2 branches: remove collected card, memory-pair state, token availability, ownership and collinear win test. Those branches remain pending; G4 turn-privilege rows do not silently close them.')
add('balance_orientation_order','MERGED_PENDING','G4_BALANCE_ORIENTATION_ORDER','balance weightguard',
    'The inspected grade2 balance row gives equality against 5+5+2kg; the weight guard asks for evidence. Neither tests down-pan heavier/up-pan lighter followed by transitive ordering. Both G2 volume labels merge with the existing G4 balance-orientation master, not accepted equality coverage.')
add('balance_chain_substitution|substitution_equal_mark','MERGED_PENDING','G3_BALANCE_RELATION_CHAIN','balance pour',
    'An explicit equal-weight sum and one lossless water transfer are present, but replacing a group by an equivalent group through several balances or equal boat water marks is not exercised. Merge into the existing balance-relation-chain master. G5 submerged-object volume displacement is a different relation and is not used to certify a boat mass substitution task.')
add('capacity_conservation_repour','MERGED_PENDING','G3_TWO_JUG_TRANSFER','pour measuringplan',
    'A24L donor poured once into an empty9L recipient and a repeated measured-portion plan cover simple conservation. The page candidate spans exact repour choices and recipient capacity constraints. Keep the finite multi-container/state branch merged with two-jug transfer; simple subtraction is partial coverage, not a plan proof.')
add('instrument_scale_reading','ASSET_PENDING','G4_INSTRUMENT_SCALE_READING_ASSET','scale',
    'The inspected graduated vessel row subtracts labelled ticks, divides by equal intervals, adds the stated offset and reconstructs all ticks. Thus scale interpolation mathematics is present. Reading each circular pointer, direction and tare state from a publisher image remains an explicit asset/representation task; no visual pass is claimed.')
add('plausible_measurement_estimation','COVERED','G2_REFERENCE_ESTIMATION_CERTAINTY','estimate lengthestimate weightguard',
    'The actual grade2 rows use stated ten-unit/handspan references, distinguish estimate from exact and request a real scale record before choosing a heavier bag. This covers the reference-and-certainty principle; it cannot certify unobserved real measurements.')
add('fixed_cardinality_subset_sum','MERGED_PENDING','G3_BOUNDED_MEASURE_SUBSET','payment',
    'The grade2 payment row selects 500+200 to reach700 with each available card used once, but imposes no exact two/three-item constraint or complete feasible-subset enumeration. Fixed cardinality and bound branch remains merged with the existing bounded-measure-subset master.')
add('maze_route_label_sum','CONFIRMED_GAP','G2_ROUTE_COLLECTED_LABEL_SUM','path polyline',
    'The inspected graph filters admissible nodes and checks edges; the polyline row names edges. Neither accumulates only labels collected along a valid route or handles a shared node counted once. This is a concrete route-state/sum difference among inspected nearest rows, not an exhaustive archive-absence proof.')
add('seven_segment_relocation|matchstick_numeral_extrema','MERGED_PENDING','G4_SEVEN_SEGMENT_RELOCATION','digit sort',
    'Digit inequality and arbitrary pair swaps do not model which physical digit segments can be removed/added by a single match move, fixed digit slots or the resulting maximum. Merge with the existing seven_segment_single_move_minimum / seven_segment_relocation_with_digit_count_change master; segment assets remain required.')
add('jump_skip_nodes_interpretation','MERGED_PENDING','G4_JUMP_SKIP_NODES_INTERPRETATION','board1',
    'A normal die step count excludes the start but counts landings. The observed jump-over versus landing rule comes from a supplied example and is not the same transition. Preserve the existing G4 jump-skip master and its exact rule/asset requirement.')
add('relative_difference_reference_update','CONFIRMED_GAP','G2_RELATIVE_HEIGHT_REFERENCE_UPDATE','pour bounds',
    'Nearest lossless-transfer and bound selection tasks do not update a signed relative height when only one reference height changes. Requires keeping which water level is the reference and recomputing the relative difference; not inferred from subtraction keywords.')
add('equal_result_path','COVERED','G12_EQUAL_RESULT_PREDICATE_PATH','path bins',
    'The original typed graph explicitly filters arithmetic values independently of adjacency, and the grouping row preserves equal-value labels. Selecting a route using one equality predicate uses that same finite graph predicate relation. Publisher graph recognition and a route-specific total are separate pending tasks.')
add('shared_card_assignment','CONFIRMED_GAP','G2_SHARED_ARITHMETIC_CARD_ASSIGNMENT','equations cards',
    'The inspected equation row reuses the same full pool independently in each listed equality; the numeral row enumerates one number at a time. Neither consumes a shared finite card inventory across several arithmetic blanks simultaneously. G4 shared digit inequality assignment is only a partial analogue, not automatic closure.')
add('ordered_label_graph_route|graph_result_sequence','CONFIRMED_GAP','G2_GRAPH_PRESCRIBED_RESULT_SEQUENCE','path bins',
    'A single admissibility predicate per node does not encode the position-dependent next required label/result in a prescribed sequence. The graph task needs a route and sequence index together; combine both volume aliases as one finite master.')
add('local_max_branch_route','CONFIRMED_GAP','G2_LOCAL_BRANCH_COMPARISON_ROUTE','path filter',
    'Global filtering/order rows do not choose the locally larger labelled branch at each encountered fork. A valid answer must follow the given local decision rule and actual edges, not globally maximize the final label.')
add('two_sided_strict_bound_selection','COVERED','G1_STRICT_TWO_SIDED_BOUNDS','bounds bins',
    'The strict two-ended card filter checks both endpoints explicitly; the expression row computes value while keeping labels. A page asking selection by strict expression-value bounds uses those same explicit relations, with equality excluded. No whole-image result is certified.')
add('multiset_numeral_generation|digit_card_permutations_zero','MERGED_PENDING','G1V2_TWO_DIGIT_NUMBER_CARD_CONSTRUCTION','cards',
    'The nearest parity-card row has distinct 0,3,8 cards and filters even two-digit outputs. It does not cover repeated-valued cards as separate resources, unrestricted permutations or all extrema. Merge the zero and multiset branches with the existing numeral-construction master; retain per-card multiplicity in later originals.')
add('trace_single_crossing_curve','ASSET_PENDING','G1V1_CURVED_CONNECTION_TRACING_ASSET','line polyline',
    'The inspected rows distinguish line/curve and name a straight polyline. They do not follow one curved connector through a crossing without switching. Use the preexisting curved-connection asset master, with the G2 page locator retained.')
add('digit_inequality','COVERED','G4_DIGIT_INEQUALITY_RELATION','digit',
    'The actual G4 digit row enumerates every digit at the same place, retains strict order and tests the equality boundary. G2 missing-digit inequality is the same place-value relation at smaller place count. Compound independent blanks remain separate.')
add('point_segment_edge_list','ASSET_PENDING','G3_COLLINEAR_ALL_SEGMENT_ENUMERATION','polyline collinear composite',
    'A supplied A→B→C→D polyline row names successive segments, and the triangle row checks drawn complete sides. The page also asks all pairs on a line containing interior points. Naming only adjacent links is incomplete; original point/edge geometry and all-pair enumeration remain pending under the collinear master.')
add('physical_measurement_guard|physical_measurement','ASSET_PENDING','G2_PHYSICAL_MEASUREMENT_AND_RECORD','measureguard draw lengthestimate',
    'Existing rows explicitly ask for ruler readings/clear image before claiming actual length and give a valid zero-aligned construction plan. The page requires real scale, measurement or record; those actions cannot be certified by a text plan. Mathematical/guard component exists, actual observation/asset remains pending.')
add('line_curve_recognition','COVERED','G2_LINE_CURVE_TEXT_RELATION','line',
    'The grade2 row explicitly distinguishes bounded straight segment, indefinitely extended straight line and curved line. It supplies the defining relations rather than relying on names alone. Identifying those relations from a fresh image remains outside this text coverage.')
add('collinearity','COVERED','G2_SINGLE_COLLINEAR_TRIPLE','collinear',
    'The grade2 row uses the supplied fact L,M,N collinear, M between and P off-line to test a true and false triple. It covers a single explicit collinearity decision, not complete enumeration of many intersecting lines.')
add('collinear_triples','ASSET_PENDING','G3_COLLINEAR_ENUMERATION','collinear composite',
    'Nearest rows decide one supplied triple or exclude one collinear triple while listing triangles. They do not inventory every collinear triple in the page arrangement, including intermediate points. Merge the existing collinear-enumeration asset task; require explicit incidence or an original clear asset.')
add('composite_polygon_count|composite_shape_count','ASSET_PENDING','G3_COMPOSITE_POLYGON_ENUMERATION_ASSET','composite',
    'Accepted new grade3 source lists ABD,ADC,ABC with drawn-side and noncollinearity checks, so selected text composite enumeration is present. G2 pages include different quadrilateral inventories and collinear composite segments. Arbitrary pictured inventory is not closed by the one triangle configuration; retain asset and shape-configuration scope without reauthoring its accepted text exemplar.')
add('grid_path_length_comparison|grid_path_length','MERGED_PENDING','G1V2_ROUTE_TOTAL_LENGTH_COMPARISON','polyline ray',
    'Actual source names consecutive links and another distinguishes one-unit versus ten-unit tick spacing. Neither computes and compares entire grid routes including a diagonal/scale convention. Merge with the route-total master and retain needed grid scale/edge definitions; avoid treating a count of vertices as length.')
add('fold_cut_spatial','ASSET_PENDING','G3_PAPER_FOLD_CUT_SYMMETRY','tiling draw',
    'An explicit domino placement and straight segment construction do not show which sides/regions coincide after a fold or how a cut maps on unfolding. Merge existing fold-cut asset master, not ordinary area or shape vocabulary.')
add('piece_tiling','ASSET_PENDING','G3_FIXED_PIECE_ASSEMBLY_FEASIBILITY','tiling',
    'A valid grade2 two-by-three domino tiling explicitly checks coverage/no overlap/rotation. Page candidates ask different triangular pieces and selecting a supplied pair. That geometry/feasibility is not implied by one domino solution; keep new original piece assets/representations pending.')
add('dissection_reassembly_square','ASSET_PENDING','G3_AREA_PRESERVING_CUT_REARRANGEMENT','tiling',
    'Nearest domino source places preexisting pieces; it never selects cuts or proves a dissection reassembles a square. Merge the existing area-preserving cut-rearrangement task and require original cut/piece coordinates or asset.')
add('physical_construction_guidance','ASSET_PENDING','G3_PHYSICAL_GEOMETRIC_CONSTRUCTION','draw measureguard',
    'An explicit grade2 zero-aligned ruler plan and missing-measurement guard cover truthful guidance. They do not establish a student physically constructed the requested segment. Keep physical scale/endpoint evidence pending under the existing construction master.')
add('calendar_missing_cells','MERGED_PENDING','G1V2_CALENDAR_ANCHOR_OFFSET','calendar calendar_guard',
    'The inspected calendar row follows27Tue,28Wed,29Thu to next1MarchFri and guard asks for year/last date. The observed pages additionally restore missing cells, first occurrences and previous-week dates. Keep those complete calendar-grid/anchor offsets in the existing master instead of counting rollover as all calendar representations.')
add('missing_personal_timetable_guard|missing_current_date_guard','MERGED_PENDING','G4_MISSING_PERSONAL_DATE_OR_TIMETABLE_CONTEXT','calendar_guard surveyguard',
    'Actual guards refuse a machine-year substitution and ask for missing respondents. They establish truthful missing-data behaviour but do not explicitly cover the student\'s own timetable/current date input contract. Merge with existing missing_current_year_context and G1 timetable masters; do not supply the agent\'s calendar as the student\'s context.')
add('clock_hand_motion','MERGED_PENDING','G1V2_ELAPSED_WHOLE_HOURS','calendar draw',
    'Calendar advancement and ruler construction do not coordinate continuous hour/minute hand motion. Merge with the existing elapsed-time/clock-reading master while keeping hand-motion and any quarter-hour representation explicit. Static G4 dial-angle arithmetic does not close this motion task.')
add('two_path_operation_merge','CONFIRMED_GAP','G2_SHARED_NODE_TWO_PATH_OPERATION_CONSISTENCY','cycle pyramid',
    'The new G4 source propagates one directed cycle and compares its end with its own start; the pyramid adds two children. Neither requires two different operation paths to agree at one shared unknown node. Preserve the distinct convergence constraint; a common graph keyword is not coverage.')
add('finite_subset_sum_extrema','MERGED_PENDING','G3_BOUNDED_MEASURE_SUBSET','payment bounds',
    'Exact payment selects one feasible subset without fixed size or an optimality proof. The page needs extremal sum of selected finite numbers under its constraints. Add this objective branch to the bounded-subset master; do not substitute an arbitrary target-sum solution.')
add('g2v2_expression_class_count','MERGED_PENDING','G12_EXPRESSION_CLASS_COUNT_EXTENSION','bins',
    'Existing grouping source lists members of two already named target groups. The G2 page asks discovery/count of equal-value classes. Preserve that finite output/partition branch pending; do not infer number of distinct classes from a row that only reports label groups for supplied targets.')
add('triangular_layers_pattern|alternating_decreasing_stack','CONFIRMED_GAP','G2_CHANGING_LAYER_AND_SHAPE_PATTERN','cubes interval',
    'Complete equal cuboid layers and a constant-addition sequence do not encode growing triangular layers or alternating decreasing stack counts/types. Keep two explicit branches of one finite changing-layer/shape-pattern master; G4 doubling sequences are also a different recurrence.')
add('physical_assembly','ASSET_PENDING','G3_FIXED_PIECE_ASSEMBLY_FEASIBILITY','tiling cubes',
    'Text domino placement and cuboid layer calculation cannot attest a real or pictured assembly. Merge with existing assembly master, retaining solid inventory, support/occlusion and physical record requirements.')
add('shape_filtered_maze','ASSET_PENDING','G1V2_PREDICATE_PATH_ASSET','path line',
    'Directed typed predicate paths are represented, but the page predicate requires object/solid recognition from each pictured branch. Original shape-labelled asset or complete shape annotations are required; text arithmetic filtering is not visual shape recognition.')
add('conditional_labelled_maze','MERGED_PENDING','G2_LABELLED_MAZE_LOCAL_CONDITIONS','path filter',
    'The actual graph source uses one global predicate; the page pair includes label-conditioned movement and locally larger-edge choices. Merge as a branch of G2 local-branch route rather than claiming any labelled graph closes all conditional policies.')
add('digit_card_extrema','MERGED_PENDING','G1V2_TWO_DIGIT_NUMBER_CARD_CONSTRUCTION','cards digit',
    'The nearest rows enumerate even two-digit distinct-card numbers or select a missing digit by a single inequality. The page constructs extremal three-digit numerals from a finite pool while exceeding a given bound; global card-use and bound must be checked jointly. Merge with finite numeral construction, pending that joint branch.')
add('measurement_bound_language','CONFIRMED_GAP','G2_MEASURE_REPEAT_UPPER_LOWER_BOUND_LANGUAGE','lengthestimate scale',
    'An approximate handspan estimate and interpolation between labelled ticks do not derive exact/approximate length bounds from repeated ruler placement and a partial remainder. The page combines repeated known unit with boundary language; keep an explicit finite master. G4 positive product comparison is a different representation.')
add('equal_intervals_from_posts','COVERED','G4_INTERVALS_VS_POSTS_BOTH_ENDPOINTS','interval inclusive',
    'Actual rows distinguish n positions from n−1 steps and explicitly retain both endpoints of an evenly spaced enumeration. This covers equal intervening intervals along a stated straight sequence. Shared intersections or closed loops remain separate pending forms.')
add('scaled_grid_distance_threshold','CONFIRMED_GAP','G2_SCALED_GRID_DISTANCE_THRESHOLD','ray bounds polyline',
    'Nearest rows separately handle number-ray tick scale, strict scalar bounds and ordered segments. The page requires a collinear scaled-grid distance followed by a threshold test; no inspected row combines grid endpoints, interval count, scale and inequality. Preserve the explicit geometry/threshold branch.')
add('capacity_assignment','MERGED_PENDING','G1_RESOURCE_ASSIGNMENT_CAPACITY_BRANCH','pour cards',
    'Single-container filling and numeral enumeration do not assign a set of converted quantities one-to-one to finite containers. Merge into the existing resource-assignment family with an inclusive capacity branch and unit conversion, keeping global no-reuse constraints explicit. Strict greater-than resource variants do not close an equality-capacity boundary.')
add('aligned_segment_difference','MERGED_PENDING','G4_OVERLAP_LENGTH_BAR_ALIGNMENT','polyline draw',
    'A named polyline and a zero-start ruler plan do not extract a train/bridge length from offset aligned endpoints. Merge the existing overlap_length_bar_alignment master; require shared-reference endpoints rather than subtracting arbitrary labelled lengths.')
add('grid_commands','CONFIRMED_GAP','G2_ORTHOGONAL_COMMAND_EXECUTION_AND_LANDING_SUM','path polyline',
    'The inspected graph follows supplied edges and a predicate. The page executes cardinal move commands on a lattice and sums landing labels. It needs coordinate/state updates and unambiguous counted landings, absent from those nearest examples.')
add('overlapping_region_filter','CONFIRMED_GAP','G2_OVERLAPPING_REGION_MEMBERSHIP_EXTREMA','filter bins',
    'Nearest threshold ordering and disjoint expression groups do not represent intersection/overlap membership where one object can belong to several regions. Preserve region-membership set logic before selecting extrema/difference; do not reduce to disjoint tally.')
add('trajectory_observation_guard','ASSET_PENDING','G2_TRAJECTORY_PICTURE_OBSERVATION_GUARD','line measureguard',
    'Line-versus-curve definitions and missing-photo guard are present. Classifying a particular pictured trajectory still needs actual path evidence; no unseen trajectory is invented. Keep the page-specific original trajectory asset/annotation pending.')
add('resource_distribution_event','CONFIRMED_GAP','G2_FINITE_POSITIVE_RESOURCE_DISTRIBUTION','payment',
    'A once-only payment subset selects existing cards; distributing a fixed total across recipients with each recipient positive allows allocations and distinct constraints. The page event assertion must enumerate or bound those allocations. Keep a finite positive-distribution master, not factor-pair or ordinary division coverage.')
add('physical_observation|personal_survey','ASSET_PENDING','G2_PERSONAL_OBSERVATION_SURVEY_RECORD','survey surveyguard weightguard',
    'Grade2 sources give a full hypothetical survey with respondent codes, one choice each and no false claim of actual interviews, plus incomplete-record guards. The pages require the learner\'s actual room/timetable/preferences. Existing principles cover recording/guard logic; actual personal observations remain required and cannot be generated as facts.')
add('finite_animal_leg_constraint','CONFIRMED_GAP','G2_FINITE_ANIMAL_COUNT_LEG_CONSTRAINT','payment equations',
    'Nearest subset payment and three-card equalities do not jointly satisfy total animal count, total legs and at-least-one of each type. Finite case enumeration with both counts is a distinct represented relation; no claim of archive-wide absence.')
add('grid_copy','ASSET_PENDING','G3_SILHOUETTE_PIECE_GRID_REPRODUCTION','tiling collinear',
    'A finite domino tiling and explicit collinearity statement do not copy the given lattice silhouette while preserving coordinates/incidence. Merge the spatial silhouette/grid reproduction asset family, retaining actual G2 locator and a fully specified original grid requirement.')
add('shared_intersection_planting','CONFIRMED_GAP','G2_SHARED_INTERSECTION_POINT_COUNT','interval collinear',
    'A single straight sequence has n−1 gaps, and a single collinear triple is covered. Several rows sharing intersection points require deduplicating one point belonging to multiple rows; the single-line post relation is insufficient. Preserve a finite incidence/count master.')
add('two_draw_without_replacement','MERGED_PENDING','G4_TWO_DRAW_COLOR_MULTISETS','surveyguard cards',
    'Finite card use within one numeral and missing survey data are partial only. Two sequential draws require updating the available multiplicities and testing possible/certain/impossible unordered colour outcomes without replacement. Merge the existing two_draw_color_multisets master, pending that explicit state relation.')

records=[]
all_labels=set()
for book in ['g2v1','g2v2']:
    rel=book+'_audit/page_review.jsonl'; groups=collections.defaultdict(list)
    for raw in (RUN/rel).read_bytes().splitlines():
        r=json.loads(raw)
        for label in r.get('gap_candidates',r.get('gap_ids',[])):
            groups[label].append({'book_id':book,'printed_page':r['printed_page'],
                'image_url':r.get('image_url',r.get('official_url')),
                'image_sha256':r.get('image_sha256',r.get('sha256')),
                'exercise_types_read':r.get('exercise_types',[]),
                'actual_page_read':r.get('actual_visual_page_read',False) or r.get('review')=='ACTUAL_FULL_PAGE_IMAGE_VIEWED',
                'receipt_path':rel,'receipt_line_sha256':sha(raw)})
    for label,evidence in groups.items():
        all_labels.add(label)
        assert label in M,label
        status,master,refs,why=M[label]
        records.append({'candidate_id':book+':'+label,'book_id':book,'original_candidate_label':label,
            'status':status,'finite_master_id':master,'actual_page_receipts':evidence,
            'nearest_actual_valid_train_rows':[
                {k:sources[ALIASES[a]][k] for k in ['sample_id','grade','source_file','source_line_number','source_row_sha256','split','review']}
                for a in refs],
            'semantic_adjudication':why,
            'coverage_scope':'COVERED means the explicit mathematical/text relation only; it does not certify publisher-image recognition, physical success, all numerical variants or whole-curriculum coverage.',
            'no_exhaustive_archive_absence_claim':True,'authoring_performed':False,
            'human_or_external_review_claimed':False})
assert all_labels==set(M), {'unused': sorted(set(M)-all_labels),'missing':sorted(all_labels-set(M))}

cross_paths=['g1v1_audit/gaps.json','g1v2_audit/candidate_adjudication.json','g3_audit/candidate_adjudication.json',
 'g3_spatial_append/adjudication.json','g4_audit/remaining_candidate_adjudication.json','g5_audit/candidate_adjudication.json',
 'g4_remaining_append/peer_review.json','g4_remaining_append/cases.jsonl','release/accepted_cases.jsonl']
cross=[{'path':rel,'sha256':sha((RUN/rel).read_bytes()),
        'use':'Existing candidate dispositions and accepted or pending originals, kept intact; no inherited keyword pass treated as a new semantic review.'} for rel in cross_paths]

masters=[]
for master,rr in sorted(((m,[r for r in records if r['finite_master_id']==m]) for m in {r['finite_master_id'] for r in records})):
    statuses=sorted(set(r['status'] for r in rr))
    assert len(statuses)==1,(master,statuses)
    masters.append({'finite_master_id':master,'status':statuses[0],
        'candidate_refs':[r['candidate_id'] for r in rr],
        'books':sorted({r['book_id'] for r in rr}),
        'next_action':('No duplicate authoring; retain modality/grade limits.' if statuses[0]=='COVERED' else
                       'Original asset or explicit incidence/scale/physical record required; do not treat a text analogue as image/physical completion.' if statuses[0]=='ASSET_PENDING' else
                       'Resume the existing finite master and these exact G2 branches; no duplicate task or automatic acceptance from merge.' if statuses[0]=='MERGED_PENDING' else
                       'Author only this finite observed form after original design and QA; confirmed difference is relative to inspected nearest rows, not proof of archive-wide absence.')})

receipt={'reviewer':'finish_g2_mapping','purpose':'Finite candidate semantic mapping only; no training rows authored.',
 'source_files':[{ 'path':x,'sha256':sha((RUN/x).read_bytes())} for x in ['current_sources.jsonl','release/accepted_cases.jsonl','g4_remaining_append/cases.jsonl']],
 'source_hash_basis':'Exact UTF-8 JSONL line excluding line terminator; original registry hash is not substituted for the actual reviewed row hash.',
 'fields_read':FIELDS,'steps_review_includes':['every step','reason','explanation','expression','result','unit'],
 'guidance_review_includes':['all initial guidance','all three hint texts and questions'],
 'row_count':len(sources),'rows':list(sources.values()),
 'not_read_or_used':['sealed challenge/evaluation/pilot/holdout/protected content'],
 'human_review_claimed':False,'external_review_claimed':False,'training_performed':False,'drive_mutated':False}
dump(OUT/'nearest_full_field_review.json',receipt)
result={'scope':'Only the 91 preexisting (book,label) candidates from already visually read G2V1/G2V2 publisher page receipts. No re-reading sealed evaluation; no authoring; no Drive mutation; no training.',
 'reviewer':'finish_g2_mapping','candidate_count':len(records),'per_book_count':dict(collections.Counter(r['book_id'] for r in records)),
 'status_counts':dict(collections.Counter(r['status'] for r in records)),
 'finite_master_count':len(masters),'master_status_counts':dict(collections.Counter(x['status'] for x in masters)),
 'actual_nearest_full_field_row_count':len(sources),'cross_grade_evidence':cross,
 'nearest_receipt':{'path':'g2v2_audit/nearest_full_field_review.json','sha256':sha((OUT/'nearest_full_field_review.json').read_bytes())},
 'limitations':['COVERED is an explicit relation-level/text decision, not all images, physical tasks, all grade presentations or all textbook exercises.',
                'MERGED_PENDING is open work, not accepted data or complete coverage. Aliases are consolidated for finite resume without double authoring.',
                'CONFIRMED_GAP means a concrete relation/representation difference against actual inspected nearest rows; all 5784 archived rows were not semantically re-read.',
                'All original source and page receipts, frozen provenance, official reviews and G5 adjudication are unchanged.',
                'The G4remaining20 sources were considered as new forms. Two relevant rows were actually read in full fields and are recorded; that append is not presumed accepted solely because its files exist.'],
 'adjudications':records,'finite_master_resume_queue':masters,
 'authoring_performed':False,'training_performed':False,'drive_mutated':False}
dump(OUT/'g2_combined_candidate_adjudication.json',result)
print(json.dumps({k:result[k] for k in ['candidate_count','per_book_count','status_counts','finite_master_count','master_status_counts','actual_nearest_full_field_row_count']},ensure_ascii=False))
print('adjudication_sha256',sha((OUT/'g2_combined_candidate_adjudication.json').read_bytes()))
print('nearest_receipt_sha256',sha((OUT/'nearest_full_field_review.json').read_bytes()))

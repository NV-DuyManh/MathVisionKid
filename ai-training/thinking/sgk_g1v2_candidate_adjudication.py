"""G1V2 comparison evidence; deliberately does not generate or accept data."""
import hashlib,json
from pathlib import Path
RUN=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019'
# These nearest source rows were printed with all semantic fields and read in
# the replacement-agent turn. Searching a topic is not treated as a proof.
ALIASES={
 'calendar':'primary_20261016_g1_time_0007_mini_calendar_lookup',
 'clock':'primary_20261016_g1_time_0007_read_morning_hour',
 'schedule':'primary_20261016_g1_time_0007_match_schedule',
 'table':'primary_20261017_g1_activities_0008_calendar_clock_activity',
 'length':'primary_20261016_g1_measurement_0006_cm_compare_same_unit',
 'ruler':'primary_20261016_g1_measurement_0006_cm_read_write',
 'estimate':'primary_20261016_g1_measurement_0006_guard_unknown_reference',
 'chain':'primary_20261016_g1_operations_0003_left_add_subtract',
 'tens':'primary_20261018_old_g1_numbers_100_0096_bundled_sticks_tens_units_write_read',
 'sequence':'primary_20261018_old_g1_numbers_100_0096_forward_number_line_cross_tens_blank',
 'sort':'primary_20261016_g1_foundations_0002_sort_four',
 'column':'sgk_g12_20261019_blank_digit_column_constraints_02',
 'multi_column':'sgk_g12_20261019_blank_digit_column_constraints_04',
 'path':'sgk_g12_20261019_constrained_arithmetic_path_01',
 'swap':'sgk_g12_20261019_one_digit_swap_repair_01',
 'bins':'sgk_g12_20261019_expression_target_classification_02',
 'shape':'primary_20261016_g1_geometry_0004_four_shape_matching',
 'count':'primary_20261016_g1_foundations_0002_count14',
 'cut':'primary_20261016_g1_solids_assembly_0005_diagonal_cut_restore',
 'balance':'primary_20261017_g2_mass_capacity_0016_balance_equal_weights',
 'filter':'primary_20261018_g4_data_sequences_0067_filter_threshold_then_descending_labels',
 'elapsed':'primary_20261018_finish_g3_calendar_elapsed_same_day',
 'route':'primary_20261018_finish_g3_lengthunits_hm_sum_route',
 'queue':'primary_20261016_g1_geometry_0004_queue_front_middle_back',
}
# status, nearest aliases, semantic difference/coverage, next action
DECISIONS={
 'G1V1_CURVED_CONNECTION_TRACING_ASSET':('TEXT_SKILL_COVERED_ASSET_PENDING',['tens'],'Number words and tens/ones are covered. Following crossing curved connector lines is not exercised by a word-only bundled-stick example.','Merge with existing G1 spatial asset queue; do not claim line tracing from text.'),
 'G1V2_ATTRIBUTE_FILTERED_EXTREMA':('PARTIAL_COVERAGE_GRADE_REPRESENTATION_PENDING',['filter','sort'],'A labelled numeric filter followed by sorting is present in grade 4. G1 colour-filtered max/min needs an age-appropriate representation; a larger-grade filter is not full G1 coverage.','Cross-check root conjunctive numeral filter and original typed attribute cases before authoring.'),
 'G1V2_CALENDAR_ANCHOR_OFFSET':('PARTIAL_COVERAGE_RELATION_PENDING',['calendar'],'Existing G1 row reads an already complete date/weekday table. Inferring another date or weekday from a single anchor requires counting the offset and is not identical to lookup.','Queue bounded G1 anchor-and-offset cases; do not use current real-world date.'),
 'G1V2_CLOCK_READING_IMAGE_ASSET':('TEXT_SKILL_COVERED_ASSET_PENDING',['clock','schedule'],'Reading explicitly described hands and matching to an activity is covered. Image recognition, rotated faces and locating the highest clock are not validated by these text examples.','Retain clock semantics; queue original clock diagram metadata/assets and review.'),
 'G1V2_COMMON_REFERENCE_LENGTH_COMPARISON':('PARTIAL_COVERAGE_ASSET_PENDING',['length','ruler'],'Existing source compares supplied cm values. It does not teach counting equally spaced grid units or aligning differently oriented strips to a common reference.','Merge grid/length spatial queue; specify unit intervals and endpoints in original data.'),
 'G1V2_COMPOSITE_SHAPE_INVENTORY_ASSET':('PARTIAL_COVERAGE_ASSET_PENDING',['shape','count'],'Shape-name matching and independent-symbol counting exist separately. Counting each component of a composite robot by shape requires an explicit component inventory or image.','Merge composite shape inventory queue; avoid assuming hidden components.'),
 'G1V2_COMPOSITE_SQUARE_COUNT_ASSET':('PARTIAL_COVERAGE_ASSET_PENDING',['shape','count'],'A 2 by 2 subdivision includes a larger square as well as the unit squares. Independent-dot counting does not teach exhaustive composite-square enumeration.','Merge G3/G4 composite geometry candidate; original edge/grid description must state all boundaries.'),
 'G1V2_CONSTANT_STEP_SEQUENCE':('PARTIAL_COVERAGE_RELATION_PENDING',['sequence'],'Existing G1 sequence has a declared step of one. Declared steps of two, five or ten need explicit repeated-step examples and are not proven by sorting.','Check skip-count train rows across grades; add only an uncovered G1 representation.'),
 'G1V2_DIRECT_LENGTH_IMAGE_ASSET':('TEXT_SKILL_COVERED_PHYSICAL_SCALE_PENDING',['ruler','length'],'Reading known ruler endpoints is covered. Measuring a printed object in cm cannot be inferred from an arbitrarily resized page image.','Queue original calibrated assets or ask for actual ruler/measurement; no numeric length from screenshot pixels.'),
 'G1V2_DUPLICATE_SCORE_ASSIGNMENT':('PARTIAL_COVERAGE_RELATION_PENDING',['sort'],'Sorting distinct numbers does not assign a multiset with repeated scores to named people under a strict comparison. P89 requires preserving both equal high scores.','Candidate for bounded multiset constraint cases after comparison with root global-card assignment.'),
 'G1V2_ELAPSED_WHOLE_HOURS':('PARTIAL_COVERAGE_GRADE_PENDING',['elapsed','clock'],'Grade 3 elapsed minutes is covered. The G1 task should count whole-hour intervals between explicit same-day endpoints without importing minute arithmetic.','Queue G1 age-appropriate whole-hour elapsed cases; distinguish midnight/day ambiguity.'),
 'G1V2_EQUAL_QUANTITY_BALANCE_REPRESENTATION':('PARTIAL_COVERAGE_REPRESENTATION_PENDING',['balance','column'],'Mass equality on a balanced scale exists in grade 2. G1 equal abstract quantities on both sides are a different representation; no unit-free physical mass assumption.','Merge balance relation queue; represent each side explicitly and keep units appropriate.'),
 'G1V2_GATE_PAIR_SUM_PATH':('PARTIAL_COVERAGE_RELATION_PENDING',['path','bins'],'Existing path has a unary predicate at every node. P93 uses one gate from each of two stages and a relation between the two labels, so a per-node filter alone is insufficient.','Queue original finite two-layer graph and enumerate all legal gate pairs.'),
 'G1V2_GRID_REGION_UNIT_COUNT_ASSET':('PARTIAL_COVERAGE_ASSET_PENDING',['count','cut'],'Independent-dot count and restoring two triangles do not cover exhaustive unit-square count in a nonrectangular region.','Merge grid-region queue; define occupied cells explicitly.'),
 'G1V2_LINKED_ARITHMETIC_NETWORK':('PARTIAL_COVERAGE_REPRESENTATION_PENDING',['chain'],'A linear sequence of adding then removing is covered. Branches or shared intermediate nodes, if required, need their actual graph. P97 is a linear arrow representation of the same arithmetic.','Treat P97 linear chain as covered semantics with arrow representation; inspect P51 graph separately before claiming a missing relation.'),
 'G1V2_MATCHSTICK_DIGIT_ASSET':('PARTIAL_COVERAGE_ASSET_PENDING',['shape','count'],'General shape identification does not define a seven-segment numeral or count required segments for every allowed numeral.','Merge seven-segment digit queue with explicit segment sets; no inferred match lengths.'),
 'G1V2_MISSING_DIGITS_COLUMN_SUBTRACTION':('PARTIAL_COVERAGE_MULTI_BLANK_PENDING',['column','multi_column'],'Existing G1 rows cover a single missing digit and a nonunique multi-blank guard. P98 includes jointly determined blanks. Root grade 4 multi-blank batch is related but does not establish G1 instructional fit.','Cross-link root multi-blank accepted hashes and review a G1 no-borrow version before additional authoring.'),
 'G1V2_ORDERED_ITINERARY_DAY_MAPPING':('PARTIAL_COVERAGE_RELATION_PENDING',['calendar','queue'],'Weekday lookup and a fixed queue exist separately; mapping successive itinerary stops to successive weekdays needs an explicit start and one-stop-per-day rule.','Queue after checking ordinal/day mapping cases; preserve missing-rule guards.'),
 'G1V2_PLAUSIBLE_REFERENCE_ESTIMATION':('PARTIAL_COVERAGE_RELATION_PENDING',['estimate','ruler'],'Existing guard correctly avoids inventing a measurement for an unseen personal object. Selecting a plausible scale from supplied options is a different task and must not turn typical size into guaranteed personal measurement.','Use original explicit reference ranges/options, or keep as a guard; no universal exact desk/handspan dimensions.'),
 'G1V2_PREDICATE_PATH_ASSET':('TEXT_SKILL_COVERED_ASSET_PENDING',['path'],'An explicit directed graph with a numeric predicate is covered in accepted G1 source. The SGK picture itself is not a missing numeric method.','Keep source coverage and queue only original diagram representation if needed.'),
 'G1V2_REMOVE_MATCHES_TRIANGLE_COUNT_ASSET':('PARTIAL_COVERAGE_ASSET_PENDING',['cut','shape'],'Restoring two cut pieces is not deleting edges and recounting all triangles in a shared-edge arrangement.','Merge finite edge-deletion geometry queue; specify edge set and count larger triangles too.'),
 'G1V2_REPEATED_DIGIT_NUMBER_SELECTION':('PARTIAL_COVERAGE_RELATION_PENDING',['tens'],'Reading tens/ones does not itself select all numbers whose two digit symbols are equal. A finite predicate over an explicitly given list is needed.','Cross-check root conjunctive numeral filter and G1 card list cases before new rows.'),
 'G1V2_ROLE_POOL_EQUATION_CONSTRUCTION':('PARTIAL_COVERAGE_ROLE_CONSTRAINT_PENDING',['column','bins'],'Known-result column completion and sorting cards into value bins do not construct equations taking each operand/result from different supplied pools.','Cross-link G1 new number-card equations and root global assignment; add only uncovered role-pool constraint.'),
 'G1V2_ROUTE_TOTAL_LENGTH_COMPARISON':('PARTIAL_COVERAGE_RELATION_PENDING',['route','length'],'Adding one route and comparing two known lengths are covered separately. Choosing between different explicitly enumerated routes combines them and must retain edge connectivity.','Merge route comparison queue; check existing shortest-path exact rows first.'),
 'G1V2_SCHEDULE_AFTER_ARRIVAL_SELECTION':('PARTIAL_COVERAGE_RELATION_PENDING',['schedule'],'Matching exact start time to a clock is covered; filtering events by whether arrival is before start requires a strict/inclusive eligibility rule.','Queue original same-day whole-hour schedule with equality boundary explicit.'),
 'G1V2_SINGLE_MATCH_EQUATION_REPAIR':('PARTIAL_COVERAGE_ASSET_PENDING',['swap'],'Swapping entire digit cards preserves each digit shape. Moving one segment changes digit shapes and needs an allowed seven-segment alphabet; it is not the same operation.','Merge G2/G3/G4 single-match candidates with one explicit finite oracle and legal operator rule.'),
 'G1V2_SORT_REPAIR_ONE_SWAP':('PARTIAL_COVERAGE_OPERATION_CONSTRAINT_PENDING',['sort','swap'],'Sorting and repairing an equation via one digit swap are present separately. Repairing the order with exactly one positional swap is a constrained operation.','Cross-link root minimum-swap rows; review G1 no-cycle-language version rather than duplicate a family.'),
 'G1V2_TEMPORAL_STAGE_ORDER':('NON_NUMERIC_CONTEXTUAL_ORDER_PENDING',['queue'],'P89 lotus stages require botanical stage recognition from pictures. Fixed queue order only follows a stated order and does not establish biological world knowledge.','Do not manufacture a math gap or certainty from this page; use stated sequence relations for any original temporal-order task.'),
 'G1V2_TIMETABLE_MULTI_CRITERIA_LOOKUP':('TEXT_SKILL_COVERED_ASSET_PENDING',['table','calendar'],'Accepted G1 source matches both weekday and hour; calendar row reads paired data in either direction. These cover the core table lookup relation. A pictured timetable layout still needs representation evidence.','No extra semantic family for basic day/hour lookup; split elapsed-time and arrival-eligibility extensions into their own candidates.'),
 'G1V2_TRANSFER_COMPARISON':('PARTIAL_COVERAGE_RELATION_PENDING',['chain','length'],'Sequential changes to one container do not directly cover transfer changing two groups in opposite directions before comparison. P89 has a tie boundary.','Queue original two-group transfer with conservation and post-transfer comparison; compare with root G1 add-group strict cases first.'),
 'G1V2_TWO_DIGIT_NUMBER_CARD_CONSTRUCTION':('PARTIAL_COVERAGE_ENUMERATION_PENDING',['tens'],'Tens/ones composition from a specified quantity does not enumerate all ordered choices of two distinct physical cards, with zero forbidden in the tens position.','Merge G2 two-digit-card candidate; define card reuse and zero rule, independently enumerate all choices.'),
}

def main():
    sources={}
    for lineno,line in enumerate((RUN/'current_sources.jsonl').read_bytes().splitlines(),1):
        r=json.loads(line)
        if r.get('split')!='train':continue
        sources[r['sample_id']]=(r,line,lineno)
    reviewed=[]
    fields=['problem','givens','requested_quantity','student_work','initial_guidance','hints','worked_steps','expected_answer']
    for alias,sid in ALIASES.items():
        r,line,n=sources[sid]
        reviewed.append(dict(sample_id=sid,grade=r['grade'],split=r['split'],source_line_number=n,source_row_sha256=hashlib.sha256(line).hexdigest(),semantic_fields_read=fields,semantic_field_values={k:r.get(k) for k in fields}))
    pages=[json.loads(x) for x in (RUN/'g1v2_audit/page_review.jsonl').read_text(encoding='utf-8').splitlines()]
    cs={c for r in pages for c in r['new_gap_candidate_ids']}
    assert cs==set(DECISIONS),cs^set(DECISIONS)
    out=[]
    for cid,(status,aliases,reason,next_action) in DECISIONS.items():
        loc=[dict(printed_page=r['printed_page'],publisher_page_url=r['publisher_page_url'],source_image_sha256=r['source_image_sha256']) for r in pages if cid in r['new_gap_candidate_ids']]
        nearest=[dict(sample_id=ALIASES[a],source_row_sha256=hashlib.sha256(sources[ALIASES[a]][1]).hexdigest(),grade=sources[ALIASES[a]][0]['grade']) for a in aliases]
        out.append(dict(candidate_id=cid,status=status,locators=loc,nearest_train_rows=nearest,semantic_adjudication=reason,next_action=next_action,review_type='ACTUAL_FULL_SEMANTIC_FIELDS_COMPARISON',reviewer='replacement_agent_resume_g1_page_audit',new_training_rows_created=0,not_an_exhaustive_absence_proof=True))
    d=RUN/'g1v2_audit'
    (d/'nearest_full_field_review.json').write_text(json.dumps(dict(source_file_sha256=hashlib.sha256((RUN/'current_sources.jsonl').read_bytes()).hexdigest(),train_only=True,protected_eval_pilot_not_used=True,reviewed_rows=reviewed),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (d/'candidate_adjudication.json').write_text(json.dumps(dict(candidate_count=len(out),reviewed_nearest_train_row_count=len(reviewed),scope='All 31 G1V2 candidate labels; exact nearest rows read, not exhaustive absence over the archive. Parent batch cross-links still pending. Physical images front/back not fully audited.',candidates=out),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(candidates=len(out),nearest_rows=len(reviewed),new_cases=0,adjudication_sha256=hashlib.sha256((d/'candidate_adjudication.json').read_bytes()).hexdigest())))

if __name__=='__main__':main()

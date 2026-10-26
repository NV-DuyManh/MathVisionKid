"""Finite, non-mutating reconciliation. Writes only this directory; no authoring."""
import json, hashlib, collections, pathlib, copy

HERE = pathlib.Path(__file__).resolve().parent
BASE = HERE.parents[1]
OLD = BASE / 'sgk_page_audit_20261019'
R2 = BASE / 'sgk_finish_20261020'
R3 = BASE / 'sgk_remaining_20261020'
def sha(b): return hashlib.sha256(b).hexdigest()
def obj(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def rel(p): return p.relative_to(BASE).as_posix()
def loadrows(p):
    return [(json.loads(b), {'sample_id':json.loads(b)['sample_id'], 'source_file':rel(p), 'line':i, 'sha256':sha(b)}) for i,b in enumerate(p.read_bytes().splitlines(),1) if b]

MAPPATH=R2/'crossgrade_mapping/mapping.json'
QUEUEPATH=R2/'crossgrade_mapping/resume_queue.json'
mapping=obj(MAPPATH); queue=obj(QUEUEPATH)
aliases=obj(R2/'crossgrade_mapping/external_g2_aliases.json')
g2=obj(OLD/'g2v2_audit/g2_combined_candidate_adjudication.json')
assert len(mapping['candidates'])==204 and len(mapping['occurrences'])==315 and len(queue['masters'])==167
sourcefiles=[OLD/'current_sources.jsonl',OLD/'release/accepted_cases.jsonl',R2/'release/accepted_cases.jsonl',R3/'release/accepted_cases.jsonl']
loaded={rel(p):loadrows(p) for p in sourcefiles}
newrows=loaded[rel(sourcefiles[2])]+loaded[rel(sourcefiles[3])]
assert len(newrows)==130
newbyid={r['sample_id']:(r,ref) for r,ref in newrows}; assert len(newbyid)==130
normal={'two_jug_transfer':'two_jug_state_transfer','operator_synthesis':'finite_operator_synthesis'}
by_master=collections.defaultdict(list)
for r,ref in newrows:
    cv=r.get('coverage',{}); mid=cv.get('finite_master_id',cv.get('gap_type'))
    by_master[normal.get(mid,mid)].append((r,ref))

# Explicit mathematical comparison, written after reading actual task fields. These
# describe the relation demonstrated, not blanket coverage of every page exercise.
PROOF={
'attribute_filter_then_extremum':'Eligibility is the conjunction of declared colour/shape attributes, applied before comparing values. One task preserves both maximum ties; another retains an empty eligible subset instead of choosing an ineligible card.',
'repeated_value_identity_assignment':'Scores form one repeated-value multiset assigned once to named identities under equality and strict order; the second task retains two assignments when only the high identity is pinned. This differs from consuming arithmetic cards across equations.',
'pair_relation_stage_path':'Choose exactly one gate per layer, satisfy a joint two-label sum, and retain only declared connecting edges. A numerically correct disconnected pair is explicitly rejected.',
'ordered_itinerary_weekday_map':'A fixed stop order is paired one stop per consecutive day from a supplied weekday; one branch crosses the weekly boundary, the other works backward from the final stop. No current-date assumption.',
'repeated_digit_symbol_predicate':'Select from the supplied finite strings by equality of their two digit symbols, while excluding candidates that fail the exactly-two-digit requirement. This is symbol equality, not equal arithmetic value.',
'role_specific_equation_pool':'First operand, second operand and result each have their own finite pool. All eligible addition triples are enumerated; subtraction feedback rejects crossing roles even when a numerical equality could be made.',
'arrival_schedule_eligibility':'Each event is tested against the arrival/start relation; arrival exactly at start is allowed in one branch and rejected under a separately declared strict-before rule in the other.',
'two_group_transfer_then_compare':'One transfer subtracts from its donor and adds to its recipient, preserving the total before comparing both updated groups. The branches produce equality and a reversal of the original order.',
'finite_route_total_optimization':'All complete paths in the explicitly finite G1 graph are enumerated and their edge weights summed before selecting all minima. The error branch distinguishes a greedy first-edge choice and preserves tied optimal full paths. It contains no G5 round-trip-time calculation.',
'bounded_factor_pair_enumeration':'Enumerate every bounded factor pair and check its product, with an unordered convention in one task and distinct ordered roles/bounds in the other; known-factor division alone is insufficient.',
'bounded_inventory_target_sum':'Choose an exact number of physical inventory items to hit a target; items of equal value remain distinct available copies, and a nonexistent extra copy is rejected. This demonstrates target feasibility/completeness, not subset-sum optimization.',
'balance_order_substitution_chain':'A declared lower-pan/heavier convention is combined with stable object identities and equal-group substitution; the second branch cancels the same common object on both pans. No decimal-label consistency test or equal-water-mark boat experiment is present.',
'product_pyramid':'Each upper cell is the product of precisely its two adjacent lower cells, with the middle base reused. Forward fill and reverse missing-factor/error correction both preserve the same multiplication law through the apex.',
'two_jug_state_transfer':'Both vessel states are tracked under fill, empty, and maximal pour until a source empties or destination fills. A concrete reachable target and an exhaustive even-capacity impossibility branch are demonstrated without imagined measuring marks.',
'finite_operator_synthesis':'Every legal finite operator placement is evaluated using declared precedence and operator-use budget. The examples use integer operands; they do not demonstrate G5 unlike-fraction operator synthesis.',
'capacity_edge_filtered_path':'Capacity belongs to each traversed bridge edge; every edge must admit the load and still form a connected path. Unit conversion and a cut/no-valid-route branch are explicit; checking node labels is not substituted.',
'bounded_color_multiset_without_replacement':'Finite supply bounds permit or forbid repeated colours in an unordered two-draw outcome. A separate task distinguishes ordered draw sequences from their colour-multiset images, without double counting or replacement.',
'running_operation_graph_target':'Each edge transforms the running arithmetic state; connected path history and intermediate quantity determine whether the target is reached. A shared graph node is allowed different incoming state, unlike a predicate on its printed label.',
'skip_intermediate_nodes_k_plus_one':'The route is explicitly ordered, and skipping k interior nodes traverses k+1 edges. Zero-skipped and one-skipped moves are checked against the stated route rather than counting the starting node.',
'nonoverlapping_schedule_interval_choice':'Choose a feasible subset of potentially overlapping event intervals. One branch permits touching endpoints, another requires a positive gap; pairwise overlap is checked under that declared convention.',
'inventory_rule_termination_guard':'Eligible stock and the stop-count rule are independently required. Contradictory stock/stop data and missing eligibility data each produce a precise question for the missing/conflicting rule, never a fabricated winner.',
'placeclass_torn_strip_constraints':'Connector adjacency orders fixed three-digit strips into complete million/thousand/unit classes; leading zero positions survive concatenation. A decoy sharing connectors is eliminated only by simultaneous pinned digit positions.',
'partial_product_column_reconstruction':'Unknown digits/factors are constrained simultaneously by multiplication by the ones digit, multiplication by the tens value including the shifted zero, and the aligned sum. G5 examples explicitly distinguish x20 from x2; they are not addition blanks.',
'overlap_shared_origin_lengths':'Both bars have exact endpoints on one shared oriented axis. Intersections and unions are derived from those endpoints; opposite endpoint-reading direction does not make a length negative or alter the covered set.',
'angle_ray_pair_enumeration':'All unordered pairs of distinct rays are enumerated, including nonadjacent compound angles. The second task applies an explicit straight-angle exclusion and corrects an adjacent-pairs-only list. Direction values in degrees are G4 enrichment.',
'collinear_triple_complete_enumeration':'Every unordered triple from an explicitly finite point set is tested. Four points on one line yield all four triples; a second configuration includes a diagonal triple missed by a horizontal/vertical-only student list. Segment-pair inventory is not requested.',
'two_dimensional_feature_constraints':'Independent row and column constraints jointly assign different attributes to a cell; a second grid has two legal completions and explicitly retains non-uniqueness. No unstated pattern law is added.',
'strict_fraction_unknown_numerator_interval':'Test all numerator digits against both strict unlike-fraction bounds; the feedback branch excludes exact equality at an endpoint. The denominator and digit domain remain fixed.',
'successive_fraction_of_current_remainder':'The second fractional removal uses the amount remaining after the first removal, with an explicit wrong-original-base student error and an independent remainder check.',
'three_unknown_pair_totals':'Three stable identities are reconstructed from all three pair sums, using decimal quantities and checking each pair. A separately supplied inconsistent total is identified and only the authorized total is repaired.',
'future_age_invariant_difference_ratio':'Both ages advance by the same supplied future interval, preserving their difference while changing their ratio. Reverse current-age and find-wait-time branches use that invariant explicitly.',
'conditional_cashback_threshold':'Discounted spend is compared to an inclusive threshold before computing cashback on the declared base. An exact-threshold eligible case and a wrong-original-price eligibility error are both worked.',
'interval_bin_boundary_frequency':'Every observation, including a repeated shared-boundary value, belongs to exactly one interval under explicit open/closed endpoint conventions; one task repairs double counting at boundaries.',
'date_digit_string_encoding':'Date fields are encoded/decoded in a supplied fixed eight-character order with required leading zeros; zero positions are counted as characters, without guessing a date convention.',
'finite_reinvested_compound_percent':'Year two applies the rate to the reinvested updated balance, with explicit comparison to simple interest and an inverse-principal branch. Intermediate decimal money is exact.',
'two_color_three_draw_pair_guarantee':'Finite inventory and exhaustive colour counts establish a guaranteed same-colour pair among three draws, distinguished from a guarantee of a particular colour; the second branch derives a minimum draw count.',
'slow_fast_clock_correction':'Elapsed true time and elapsed displayed time have an explicit rate from a supplied reset instant. Forward slow-clock and inverse fast-clock branches preserve the sign and reference time.',
'finite_train_tunnel_bridge_crossing':'Tail clearance requires train length plus bridge length, with start/end conventions stated. Both forward clearance time and inverse train length are checked dimensionally.',
'piecewise_speed_travel_time_comparison':'Each segment has its own distance/speed pair and time; total times are compared before any total-distance/total-time average. The second branch includes a declared rest and rejects arithmetic averaging of speeds.',
'frequency_table_weighted_mean':'Frequency counts determine observation total and weighted score total, including known zero frequency. The feedback branch rejects averaging category labels or treating zero as missing.',
'one_swap_parity_extremum':'Every one-swap position pair is enumerated, preserving the odd-units and leading-zero constraints before maximizing the numeral. Equal-value cards are still distinct physical positions under the exact-one-swap convention.',
'whole_units_from_decimal_quotient':'Maximum whole pieces are the floor of a nonintegral exact decimal quotient, with a checked leftover; reserved material is removed before division in the error branch.',
'whole_package_area_procurement':'Usable tile area gives tile demand, declared spares/reusable stock changes the purchase demand, and whole boxes use ceiling with box cost. Equal-room pooled stock is distinguished from rounding boxes separately.',
'piece_pack_unit_role_choice':'Pieces and packs are explicit alternative units with a conversion factor and equal-sharing role. The second branch treats sealed packs as indivisible and proves the requested equal share impossible.',
'circular_rim_capacity_feasibility':'Required circumference plus the specified joining allowance is compared to maximum available stretch, including exact equality and a case where ignoring the join falsely suggests feasibility.',
'semicircle_arc_plus_diameter_boundary':'The requested whole semidisc boundary consists of half a circumference plus its diameter. A second branch diagnoses an arc-only answer while preserving the stated pi and linear unit.',
'semicircle_chain_arc_length':'Arc lengths are additive in the supplied diameters; a chain is compared to one large semicircle. Explicit extra straight connectors are added only in the second branch, never silently counted as arcs.',
'wheel_turns_distance':'No-slip travel is circumference times turns, including a fractional-turn branch without rounding. These actual new tasks use matching linear units; a mixed-unit conversion subbranch remains separately unworked.',
'stadium_composite_area':'The declared composite is a central rectangle and two matched semicircles. One task also counts only the exposed outside boundary; the other distinguishes the overall length from the central rectangle length.',
'circle_material_overlap_allowance':'A declared wrap count and one final joining allowance determine material use, and an inverse joined-wire task recovers diameter. The number of joins is fixed rather than assumed one per wrap.',
'fixed_volume_surface_arrangement_optimization':'All unordered integer dimension triples of volume 12 are enumerated. Closed six-face surface and open-top five-face material objectives each have explicit minima/ties. No lateral-only four-wall objective is optimized.'
}

# Residuals are substantive branches, grade-specific pending review, or missing
# locators. A related row is evidence of the shared relation, not a closure claim.
RESIDUAL={
'g3_two_digit_reasoning_rank':('GRADE_BRANCH_PENDING','G3 identity ranking with the distinct-inventory branch is not demonstrated by the repeated-score G1 tasks; retain exact rank/inventory constraints before adapting.'),
'equal_area_elimination':('GRADE_BRANCH_PENDING','G4 equal-area room identity/elimination still needs its explicit area-derived equality premises; G1 score equality is a shared relation only.'),
'balance_orientation_order':('GRADE_BRANCH_PENDING','Pan-direction/transitivity is demonstrated in G3 text, but the G4 page-grade presentation and actual image binding remain pending; do not author a number-only duplicate.'),
'g5_candidate_balance_consistency':('UNWORKED_CONSTRAINT_BRANCH','G5 requires checking numeric decimal mass labels against pan orientation. The new G3 symbolic substitution tasks do not jointly test that decimal consistency.'),
'g3_missing_digit_column':('GRADE_BRANCH_PENDING','G5 shifted two-digit-multiplier examples do not certify a G3-appropriate column-reconstruction branch. Retain the actual G3 task operation/range before adapting.'),
'tornplaceclass_strip_assembly':('LOCATOR_AND_GRADE_PENDING','The original G3-origin alias has no exact page locator; G4 pp43-44 establish the strip relation but cannot supply the missing original locator or G3 adaptation.'),
'collinear_enumeration_and_segment_pairs':('UNWORKED_CONSTRAINT_BRANCH','Complete collinear triples are demonstrated, but complete segment/endpoint-pair inventory and its incidence convention are not; the original alias also has no page locator.'),
'two_draw_multiset_without_replacement':('GRADE_BRANCH_PENDING','The exact two-draw bounded-multiset relation is demonstrated by G4 text. Retain G3 page-grade/presentation review separately; no new numerical variant is automatically required.'),
'g5_candidate_multidraw_outcomes':('DRAW_COUNT_AND_GRADE_PENDING','Bounded unordered two-draw multisets are demonstrated, but the G5 receipt does not fix its draw count in the preserved description. Verify that count and G5 branch before closure; no blanket multidraw coverage.'),
'g5_candidate_unknown_fraction_operator':('UNWORKED_CONSTRAINT_BRANCH','The G3 operator synthesis examples have integer operands. G5 plus/minus choices among fractions under equality remain unworked.'),
'g5_candidate_shortest_route':('UNWORKED_CONSTRAINT_BRANCH','The G1 finite-path comparison lacks the G5 shortest-network-route plus round-trip travel-time branch, including return-route and speed convention.'),
'g5_candidate_equal_volume_surface':('UNWORKED_CONSTRAINT_BRANCH','Closed total and open-top material minima are demonstrated, but the original candidate also requires orientation-sensitive lateral-only surface optimization; that objective remains unworked.'),
'g5_candidate_wheel_rotations':('UNIT_CONVERSION_BRANCH_PENDING','No-slip turns times circumference and fractional turns are demonstrated. The explicit mixed-unit conversion requested in the master reason is absent from these matching-unit examples.')
}

# Preserve all originals and validate exact cited nearest rows against the frozen
# source bytes; semantic decisions on untouched candidates are inherited, not
# represented as newly re-reviewed semantic proof.
evidence={}; validation=[]
def capture(r,ref,kind):
    key=(ref['source_file'],ref['line'],ref['sha256'])
    if key not in evidence:
        evidence[key]={'evidence_id':sha(('|'.join(map(str,key))).encode())[:24], 'reference':ref,'capture_kind':kind,'full_row':r,'semantic_review_scope':'Actual full task fields compared in this append' if kind=='NEW_ACCEPTED_FULLFIELDS' else 'Exact source bytes/hash validated; prior semantic adjudication retained unless explicitly discussed in candidate decision'}
    return evidence[key]['evidence_id']
def getold(ref):
    fn=rel(OLD/ref['source_file']); r,got=loaded[fn][ref['line']-1]
    assert got['sample_id']==ref['sample_id'] and got['sha256']==ref['sha256'],(ref,got)
    assert r.get('split')=='train' and r.get('source_role')!='EVAL'
    return r,got
for c in mapping['candidates']:
    for ref in c['nearest_refs']:
        r,got=getold(ref); capture(r,got,'NEAREST_OR_PREVIOUS_ACCEPTED_HASH_VALIDATED')
for a in g2['adjudications']:
    for ref in a['nearest_actual_valid_train_rows']:
        converted={'sample_id':ref['sample_id'],'source_file':ref['source_file'],'line':ref['source_line_number'],'sha256':ref['source_row_sha256']}
        r,got=getold(converted);capture(r,got,'NEAREST_OR_PREVIOUS_ACCEPTED_HASH_VALIDATED')
for r,ref in newrows: capture(r,ref,'NEW_ACCEPTED_FULLFIELDS')

# Exact original descriptions, not a keyword search. Identifier fields select
# the original candidate record or the page row listing that candidate. Each
# original JSON node has a canonical-object hash plus the whole-file byte hash;
# JSONL pages additionally retain the actual byte-line hash.
original_links=collections.defaultdict(list); origin_files={}
def walk_original(x,path,cid):
    if isinstance(x,dict):
        if any(x.get(k)==cid for k in ['candidate_id','gap_id','canonical_form']):yield path,x
        else:
            for k,v in x.items():
                if isinstance(v,(list,dict)):yield from walk_original(v,path+'/'+str(k),cid)
    elif isinstance(x,list):
        for i,v in enumerate(x):yield from walk_original(v,path+'/'+str(i),cid)
for c in mapping['candidates']:
    cid=c['candidate_id']
    for origin in c['origins']:
        filename=origin.split(':',1)[0].replace('\\','/');p=OLD/filename
        data=p.read_bytes();origin_files[rel(p)]=sha(data)
        if p.suffix=='.jsonl':
            nodes=[]
            for i,b in enumerate(data.splitlines(),1):
                x=json.loads(b)
                if cid in x.get('gap_candidates',[]) or cid in x.get('gap_ids',[]):nodes.append((str(i),x,sha(b)))
        else:nodes=[(j,x,None) for j,x in walk_original(json.loads(data), '$',cid)]
        for loc,x,linehash in nodes:
            h=sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
            key=(rel(p),loc,h)
            if key not in evidence:evidence[key]={'evidence_id':sha(('|'.join(key)).encode())[:24],'capture_kind':'ORIGINAL_CANDIDATE_DESCRIPTION_OR_PAGE_ANCHOR','reference':{'source_file':rel(p),'file_sha256':sha(data),'json_path_or_line':loc,'actual_jsonl_line_sha256':linehash,'canonical_object_sha256':h},'full_original_record':x,'semantic_review_scope':'Exact identifier-linked original definition/page receipt; no copied textbook question text or newly viewed-image claim.'}
            original_links[cid].append(evidence[key]['evidence_id'])

# All 36 canonical RUN3 rows must be exact mathematical derivatives of the
# selected reviewed 12+12+12 drafts; parent unpolished rows are not counted again.
MATHFIELDS=['problem','givens','requested_quantity','expected_answer','worked_steps','initial_guidance','hints','student_work','can_solve','grade','pedagogical_review_decision']
draft_checks=[]
for folder in ['g34_structure_polished','g5_applied_text','g5_geometry_text']:
    for r,ref in loadrows(R3/folder/'cases.jsonl'):
        ar,aref=newbyid[r['sample_id']]
        assert all(r.get(k)==ar.get(k) for k in MATHFIELDS),(r['sample_id'],'canonical math changed')
        draft_checks.append({'sample_id':r['sample_id'],'reviewed_source':ref,'canonical_accepted_source':aref,'mathematical_fields_equal':MATHFIELDS})

chatlinks=collections.defaultdict(list)
for p in [R2/'release/accepted_chat.jsonl',R3/'release/accepted_chat.jsonl']:
    for r,ref in loadrows(p):
        sid=r['source_sample_id']; assert sid in newbyid
        assert r['source_row_sha256']==newbyid[sid][1]['sha256']
        user=json.loads(next(m['content'] for m in r['messages'] if m['role']=='user'))
        assert user['problem']==newbyid[sid][0]['problem']
        chatlinks[sid].append({'chat_reference':ref,'mode':r['mode'],'source_row_sha256':r['source_row_sha256']})
assert len(chatlinks)==130 and all(len(v)==4 for v in chatlinks.values())
for e in evidence.values():
    if e['capture_kind']=='NEW_ACCEPTED_FULLFIELDS':e['chat_links']=chatlinks[e['full_row']['sample_id']]

def examples(mid):
    return [{'reference':ref,'grade':r['grade'],'branch':r['coverage'].get('branch',r['coverage'].get('gap_type')),'evidence_id':capture(r,ref,'NEW_ACCEPTED_FULLFIELDS')} for r,ref in by_master.get(mid,[])]
def grades(receipts):
    vals=[]
    for a in receipts:
        g=a.get('grade'); book=a.get('book_id','')
        if g is None and book.startswith('g') and len(book)>1 and book[1].isdigit():g=int(book[1])
        if g and int(g) not in vals:vals.append(int(g))
    return vals
cs=[]; decisionby={}
for original in mapping['candidates']:
    c=copy.deepcopy(original); cid=c['candidate_id'];d=c['decision'];mid=d['master_id']; ex=examples(mid)
    result={'prior_category':d['category'],'candidate_grades':grades(c['page_receipts']),'matched_new_examples':ex,'publisher_image_recognition_or_physical_success_certified':False,'whole_master_closed':False}
    if d['category']=='COVERED_EXACT_ID_HASH':
        result.update(status='PRIOR_EXACT_COVERAGE_RETAINED',text_relation_demonstrated=True,semantic_basis=d['semantic_comparison'],remaining_constraints=[])
    elif d['category']=='ASSET_ONLY_LIMITATION':
        result.update(status='PRIOR_ASSET_LIMITATION_RETAINED',text_relation_demonstrated=False,semantic_basis=d['semantic_comparison'],remaining_constraints=['Actual image/physical evidence limitation retained unchanged.'])
    elif not ex:
        result.update(status='FINITE_TASK_STILL_UNWORKED_IN_INSPECTED_APPEND',text_relation_demonstrated=False,semantic_basis=d['semantic_comparison'],remaining_constraints=[d['semantic_comparison']])
    else:
        assert mid in PROOF,mid
        result.update(status='NEW_TEXT_RELATION_DEMONSTRATED',text_relation_demonstrated=True,semantic_basis=PROOF[mid],remaining_constraints=[])
        if cid in RESIDUAL:
            status,reason=RESIDUAL[cid];result.update(status=status,remaining_constraints=[reason])
        if cid=='angle_count_ray_pairs':
            result.update(status='MIXED_GRADE_OCCURRENCE_PARTIAL',remaining_constraints=['G4 unordered-pair/compound/straight-convention text is demonstrated; the G3 p118 occurrence needs degree-free grade-appropriate presentation review.'])
        if not result['remaining_constraints']:result['candidate_text_branch_complete_within_finite_inventory']=True
    result['nearest_evidence_ids']=[capture(*getold(r),'NEAREST_OR_PREVIOUS_ACCEPTED_HASH_VALIDATED') for r in c['nearest_refs']]
    result['original_description_evidence_ids']=original_links[cid]
    result['explicit_same_grade_text_examples']=[e for e in ex if e['grade'] in result['candidate_grades']] if result['text_relation_demonstrated'] else []
    result['shared_relation_examples_are_not_grade_or_constraint_closure']=True
    c['reconciliation']=result;cs.append(c);decisionby[cid]=result

occ=[]
for original in mapping['occurrences']:
    o=copy.deepcopy(original);result=copy.deepcopy(decisionby[o['candidate_id']]);g=grades([o['page_receipt']])
    if o['candidate_id']=='angle_count_ray_pairs' and g==[4]:
        result.update(status='NEW_TEXT_RELATION_DEMONSTRATED',remaining_constraints=[],candidate_text_branch_complete_within_finite_inventory=True)
    result['explicit_same_grade_text_examples']=[e for e in result['matched_new_examples'] if e['grade'] in g] if result['text_relation_demonstrated'] else []
    result['occurrence_grade']=g; o['reconciliation']=result;occ.append(o)
assert [x['occurrence_id'] for x in occ]==[x['occurrence_id'] for x in mapping['occurrences']]
assert len({x['occurrence_id'] for x in occ})==315

# External G2 records remain a separately conserved inventory (91 candidates),
# never added to the 315 global occurrence denominator.
alias_by_g2={a['g2_master_id']:a for a in aliases['aliases']}
external=[]
for original in g2['adjudications']:
    a=copy.deepcopy(original);mid=a['finite_master_id'];alias=alias_by_g2.get(mid);target=alias['crossgrade_master_id'] if alias else mid; ex=examples(target)
    result={'prior_status':a['status'],'crossgrade_master_id':target,'matched_new_examples':ex,'whole_g2_candidate_closed':False,'physical_or_publisher_image_result_claimed':False}
    if mid in by_master and mid.startswith('G2_'):
        result.update(status='NEW_G2_TEXT_RELATION_ACCEPTED',semantic_basis='Two accepted original branches for this exact G2 finite master retain the audited page relation; actual full fields and canonical row hashes are attached. Image/physical subforms remain excluded.',remaining_constraints=[])
    elif ex:
        result.update(status='RELATED_NEW_RELATION_G2_BRANCH_PENDING',semantic_basis=PROOF[target],remaining_constraints=['Keep original G2 constraints and grade/asset binding; shared master ID is not semantic closure. '+a['semantic_adjudication']])
        cid=a['candidate_id']
        extra={
          'g2v1:conjunctive_attribute_expression_filter':'G1 attribute/value examples do not evaluate expression truth then combine that truth with a visual attribute before extrema.',
          'g2v1:conjunctive_attribute_filter':'G2 truth-and-colour/arithmetic conjunction remains outside G1 supplied-value attribute filtering.',
          'g2v1:grid_path_length_comparison':'G1 weighted finite graph comparison has no explicit grid/diagonal/scale geometry.',
          'g2v2:grid_path_length':'G1 weighted finite graph comparison has no explicit scaled-grid route-length model.',
          'g2v1:finite_subset_sum_extrema':'New target-sum/cardinality examples do not maximize or minimize the selected subset sum.',
          'g2v1:point_segment_edge_list':'New collinear triples do not enumerate every permitted segment or endpoint pair.',
          'g2v2:substitution_equal_mark':'Equal boat water-mark mass equivalence is absent from the new pan-balance substitution examples.'}
        if cid in extra:result['remaining_constraints']=[extra[cid]]
    else:result.update(status='PRIOR_G2_DISPOSITION_RETAINED',semantic_basis=a['semantic_adjudication'],remaining_constraints=[] if a['status']=='COVERED' else [a['semantic_adjudication']])
    a['reconciliation']=result;external.append(a)
assert len(external)==91

masterout=[];pending=[]
for master in queue['masters']:
    mid=master['master_id'];candidates=[c for c in cs if c['decision']['master_id']==mid]; occurrences=[o for o in occ if o['master_id']==mid]
    remain=[{'candidate_id':c['candidate_id'],'status':c['reconciliation']['status'],'constraints':c['reconciliation']['remaining_constraints']} for c in candidates if c['reconciliation']['remaining_constraints']]
    if master['category']=='COVERED_EXACT_ID_HASH': status='PRIOR_EXACT_COVERAGE_RETAINED'
    elif master['category']=='ASSET_ONLY_LIMITATION':status='ASSET_LIMITATION_RETAINED'
    elif not examples(mid): status='UNWORKED_FINITE_MASTER'
    elif remain:status='PARTIALLY_DEMONSTRATED_WITH_EXPLICIT_RESIDUALS'
    else:status='FINITE_TEXT_RELATION_DEMONSTRATED'
    rec={'master_id':mid,'prior_category':master['category'],'candidate_ids':master['candidate_ids'],'original_occurrence_count':master['candidate_occurrence_count'],'status':status,'matched_new_examples':examples(mid),'remaining_candidate_branches':remain,'physical_or_image_assets_complete':False}
    masterout.append(rec)
    if master['category']=='FINITE_CONFIRMED_MISSING_MASTER' and status!='FINITE_TEXT_RELATION_DEMONSTRATED':
        pending.append({'master_id':mid,'task_kind':'AUTHOR_FINITE_ORIGINAL_TEXT_OR_EXPLICIT_GEOMETRY_MODEL' if status=='UNWORKED_FINITE_MASTER' else 'REVIEW_OR_AUTHOR_ONLY_UNWORKED_BRANCH','candidate_ids':master['candidate_ids'],'finite_occurrence_count':master['candidate_occurrence_count'],'exact_page_receipts':master['actual_page_receipts'],'original_master_reasons':master['reasons'],'nearest_refs':master['nearest_refs'],'original_description_evidence_ids':{c['candidate_id']:original_links[c['candidate_id']] for c in candidates},'required_constraints':remain or master['reasons'],'existing_relation_examples':examples(mid),'image_or_physical_result_still_separate':True,'avoid_number_only_duplicate':True})

snapshots=[{'path':rel(p),'sha256':sha(p.read_bytes()),'row_count':len(loaded[rel(p)])} for p in sourcefiles]
for p in [MAPPATH,QUEUEPATH,R2/'crossgrade_mapping/external_g2_aliases.json',OLD/'g2v2_audit/g2_combined_candidate_adjudication.json']:
    snapshots.append({'path':rel(p),'sha256':sha(p.read_bytes())})
snapshots.extend({'path':p,'sha256':h} for p,h in sorted(origin_files.items()))
report={'schema':'finite_candidate_reconciliation.v1','scope':'Only 204 original global candidate records / 315 occurrences, external 91 G2 records, frozen nearest valid-training refs, old accepted110, RUN2 accepted94 and RUN3 accepted36. Not an exhaustive search or absence claim over archives or a six-million-row corpus.','authoring_performed':False,'training_performed':False,'drive_mutated':False,'old_or_shared_state_mutated':False,'all_sgk_forms_covered':False,'source_snapshots':snapshots,'source_selection':'Canonical accepted RUN3 36; polished12 replaces its parent12, never added twice. Canonical mathematical fields were checked against selected drafts.','counts':{'global_candidates':len(cs),'global_occurrences':len(occ),'global_masters':len(masterout),'external_g2_candidates_separate':len(external),'old_source_snapshot_rows':len(loaded[rel(sourcefiles[0])]),'actual_unique_nearest_or_prior_accepted_rows_hash_validated':sum(e['capture_kind']=='NEAREST_OR_PREVIOUS_ACCEPTED_HASH_VALIDATED' for e in evidence.values()),'old_accepted':110,'run2_accepted':94,'run3_accepted':36,'new_cases_evidence':130,'new_chat_links':sum(map(len,chatlinks.values())),'new_global_masters_with_examples':sum(bool(examples(m['master_id'])) for m in queue['masters']),'original_missing_masters':94,'remaining_global_master_tasks':len(pending),'never_appended_missing_masters':sum(x['status']=='UNWORKED_FINITE_MASTER' for x in masterout),'master_status_counts':dict(collections.Counter(x['status'] for x in masterout)),'candidate_status_counts':dict(collections.Counter(x['reconciliation']['status'] for x in cs))},'masters':masterout,'candidates':cs,'occurrences':occ,'external_g2_candidates':external,'external_g2_alias_definitions_preserved':aliases,'canonical_draft_math_equality_checks':draft_checks,'limitations':['A demonstrated text relation does not certify actual publisher-image recognition, measured physical results, every numeric variation, or whole-curriculum coverage.','Other-grade aliases and missing operation/optimization/unit conventions remain explicit residuals. Grade review does not automatically require authoring a duplicate.','Prior exact coverage is inherited with exact nearest hashes; it is not represented as a fresh independent semantic recertification of every old row.','Unmatched finite masters retain their exact original candidate/page/constraint descriptions; no archive-wide missingness inference is made.']}
write(HERE/'candidate_adjudication.json',report)
with (HERE/'fullfield_evidence.jsonl').open('w',encoding='utf-8',newline='\n') as f:
    for e in evidence.values():f.write(json.dumps(e,ensure_ascii=False,separators=(',',':'))+'\n')
nextreport={'schema':'finite_next_uncovered_tasks.v1','scope':report['scope'],'source_queue_sha256':sha(QUEUEPATH.read_bytes()),'global_master_tasks':pending,'unresolved_asset_only_masters':[m for m in masterout if m['status']=='ASSET_LIMITATION_RETAINED'],'external_g2_remaining_separate':[{'candidate_id':a['candidate_id'],'finite_master_id':a['finite_master_id'],'crossgrade_master_id':a['reconciliation']['crossgrade_master_id'],'status':a['reconciliation']['status'],'constraints':a['reconciliation']['remaining_constraints']} for a in external if a['reconciliation']['remaining_constraints']],'counts':{'global_master_tasks':len(pending),'never_appended_missing_masters':sum(x['status']=='UNWORKED_FINITE_MASTER' for x in masterout),'partial_master_tasks':sum(x['status']=='PARTIALLY_DEMONSTRATED_WITH_EXPLICIT_RESIDUALS' for x in masterout),'asset_only_masters_separate':10},'authoring_priority_guidance':'First choose an unworked substantive text/constraint branch; verify original grade/page anchors and preserve all remaining constraints. Do not author number-only examples to clear grade aliases. Asset/physical branches require an explicit new model or actual evidence, never an imagined image.'}
write(HERE/'next_uncovered_tasks.json',nextreport)
outputs=[HERE/'candidate_adjudication.json',HERE/'fullfield_evidence.jsonl',HERE/'next_uncovered_tasks.json']
write(HERE/'manifest.json',{'schema':'finite_reconciliation_manifest.v1','counts':report['counts'],'source_snapshots':snapshots,'outputs':[{'file':p.name,'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in outputs],'helper_sha256':sha(pathlib.Path(__file__).read_bytes()),'writes_confined_to':str(HERE)})
print(json.dumps({'counts':report['counts'],'outputs':obj(HERE/'manifest.json')['outputs'],'remaining_global_master_ids':[p['master_id'] for p in pending]},ensure_ascii=False,indent=2))

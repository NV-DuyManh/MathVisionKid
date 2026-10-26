"""Read-only draft projection: never accepts rows or mutates authoritative queues."""
from pathlib import Path
from copy import deepcopy
from collections import Counter, defaultdict
import hashlib, json

OUT = Path(__file__).resolve().parent
RUN = OUT.parent
PUB = RUN.parent
FIELDS = ['problem', 'givens', 'requested_quantity', 'student_work', 'worked_steps', 'expected_answer', 'initial_guidance', 'hints']
BATCHES = ['g5_measurement_models_corrected', 'inventory_edges', 'geometric_relations']

def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_text('utf-8'))
def canon(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
def write(name, x):
    (OUT / name).write_text(json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')

# Decisions follow actual problem/givens/solutions, rather than shared keywords.
BASIS = {
 'all_boundary_labels_joint_match': 'All three boundary labels must consume the supplied die-card multiset once each; arbitrary order is legal, missing values and wrong multiplicities are rejected. Grade 1 explicit text inventory, not image reading.',
 'shared_edge_stick_construction': 'Five distinct allowed edges form two equilateral triangles sharing AB; the alternative one-stick completion tests both allowed additions and the unchanged inventory. Grade 1 plan, no observed physical construction.',
 'composite_square_only_enumeration': 'Complete 2-by-2 grid square-only inventory includes four small squares and the outside square, excludes nonsquare row/column rectangles; deleting one internal edge changes the exact inventory. Grade 1 finite configuration, not every pictured composite.',
 'finite_inventory_collection_game': 'Grade 3 explicit circuit updates position, removes each named token once, retains identity despite equal values, records ownership and checks stopping threshold. Second branch distinguishes number of tokens from numerical score. It does not implement G4 equivalent-fraction eligibility or reciprocal-card memory.',
 'edge_removal_game_terminal': 'Grade 4 finite edge inventories enumerate all prescribed parallelogram targets after each legal turn, including outer composites; second branch fixes rhombus-only scope and immediate termination. This is dynamic terminal-state logic, not static counting alone.',
 'glyph_parallel_perpendicular_filter': 'Grade 4 explicitly listed finite glyph segments are filtered by both distinct supporting-line parallelism and actual intersecting perpendicular segments. Disjoint support lines and collinear segments are rejected under the stated convention.',
 'equal_area_geometric_regrouping': 'Grade 3 complementary half-cells regroup into equal area units, with complete atom allocation proving three equal regions; the second branch shows piece count alone does not establish area. No assumed equal-sized heterogeneous pieces.',
 'equal_area_transfer_cancellation': 'Grade 4 specified common-region cancellation and congruent triangle transfer prove equality; a separate overlap example distinguishes physical paper area from union area. Partition and no-overlap conditions are explicit.',
 'missing_parallelogram_vertex': 'Grade 4 explicit grid-step opposite-side relations locate a fourth vertex when order is fixed; without order, all three legal completions are retained and checked. Not a known-vertex area/perimeter exercise.',
 'occlusion_partial_layer_order': 'Grade 4 stated global layer inequalities yield all consistent full orders; a cyclic global claim has no such order. The uniform-layer model is explicit; no unseen local occlusion inference is certified.',
 'tangent_circle_alignment_lengths': 'Grade 3 equal aligned externally tangent circles give tight rectangle dimensions, radius/diameter and center span. Inverse branch distinguishes full-width diameters from center gaps. Other circle layouts are not inferred.',
 'specified_area_preserving_dissection': 'Grade 5 right-trapezoid midpoint partition and half-turn produce a specified rectangle with no gap/overlap and area-versus-perimeter checks. Translation counterexample computes exact overlap and uncovered area. This does not supply the G3 square or G4 parallelogram dissection branches.',
 'bill_of_materials_area_cost': 'Grade 5 counts each finished board once, converts area before price, and compares a finite permitted n=2,3,4 design menu under an inclusive budget. These mathematical relations are demonstrated; unrestricted open design and a physical stock-sheet cutting plan are not.',
 'compare_equal_sharing_cut_schemes': 'Grade 5 compares two exact cutting schemes by unique piece inventory, recipient allocation, conservation and equal share; a shortage branch rejects a named share whose pieces cannot be distributed to everyone.',
 'grid_boundary_missing_dimensions': 'Grade 5 border-cell model fixes unique corner counting and cell edge scale; an inverse border count recovers height and separates whole rectangle, white interior and border areas. The white interior remains part of the rectangle, not removed material.',
 'gridded_net_dimensions_to_volume': 'Grade 5 explicit side strip, caps and fold adjacency determine base edges and height before unit scaling and cuboid volume; missing strip widths are reconstructed and total strip width is rejected as one solid edge.',
 'mixed_orientation_rectangle_tiling': 'Grade 5 enumerated mixed-orientation placement tiles a 5-by-6 target with five 2-by-3 tiles without overlap/gaps; prohibiting rotation makes it impossible despite equal total area. No arbitrary tangram or silhouette branch is inferred.',
 'nested_triangle_base_altitude_assignment': 'Grade 5 several nested triangles use chosen bases and their own perpendicular heights, including a foot on an extension and a vertical base. Corrected DE partitions ABE into ADE and DBE; no oblique side is substituted for altitude.'
}
RESIDUAL = {
 'finite_inventory_collection_state': [
   'G4 p70 equivalent-fraction eligibility and the nine-flowers/five termination ambiguity require an explicit clarified rule; scalar G3 token values do not resolve it.',
   'G4 p94 reciprocal-card memory matching, face state, removal and win threshold are not implemented by these G3 circuit cases.',
   'Same-master G3 evidence does not certify G4 presentation or original image/physical execution.'
 ],
 'area_preserving_cut_rearrangement': [
   'G3 volume 2 p27 dissection/reassembly and G4 volume 1 pp112-113 parallelogram-to-rectangle / square-diagonal configurations remain separate exact branches.',
   'G5 trapezoid midpoint/half-turn examples do not certify G3/G4 grade adaptation or those different cut geometries.'
 ],
 'g5_candidate_materials_budget': [
   'Only the finite design menu n in {2,3,4} is worked. The inherited p61 receipt also names open-ended bookshelf design; accepting a constrained original design with a declared design domain, or explicitly narrowing that requirement, remains an owner/root scope decision.',
   'No stock-sheet packing, physical construction, safety/structural validation or unrestricted design optimum is claimed.'
 ]
}

def main():
    cp = RUN / 'reconciliation/candidate_adjudication.json'
    qp = RUN / 'reconciliation/next_uncovered_tasks.json'
    paths = [cp, qp]
    for name in BATCHES:
        paths += [RUN/name/f for f in ['cases.jsonl','chat.jsonl','manifest.json','selfqa7.jsonl']]
    # Include frozen RUN4 projection in the preservation proof, without changing it.
    paths.append(PUB/'sgk_final_forms_20261020/reconciliation_projection.json')
    before = {p.relative_to(PUB).as_posix():sha(p.read_bytes()) for p in paths}
    baseline, queue = read(cp), read(qp)
    assert len(baseline['candidates']) == 204 and len(baseline['occurrences']) == 315
    assert len(baseline['external_g2_candidates']) == 91 and len(baseline['masters']) == 167
    assert len(queue['global_master_tasks']) == 45
    cases, bymaster = [], defaultdict(list)
    allids = set()
    for name in BATCHES:
        casepath, chatpath = RUN/name/'cases.jsonl', RUN/name/'chat.jsonl'
        rows = [(json.loads(b),sha(b),i) for i,b in enumerate(casepath.read_bytes().splitlines(),1)]
        chats = [(json.loads(b),sha(b),i) for i,b in enumerate(chatpath.read_bytes().splitlines(),1)]
        assert len(rows) == 12 and len(chats) == 48
        for r,h,line in rows:
            assert r['sample_id'] not in allids
            allids.add(r['sample_id'])
            assert r['split'] == 'train' and r['acceptance_status'].startswith('DRAFT_')
            assert not r['human_verified'] and not r['teacher_certified']
            master = r['coverage']['finite_master_id']
            assert master in BASIS and not r['coverage']['visual_physical_coverage_claimed']
            linked = [(c,ch,cl) for c,ch,cl in chats if c['source_sample_id'] == r['sample_id']]
            assert len(linked) == 4 and len({c['mode'] for c,_,_ in linked}) == 4
            assert all(c['source_row_sha256']==h for c,_,_ in linked)
            entry = dict(reference=dict(source_file=str(casepath.relative_to(PUB)),line=line,sample_id=r['sample_id'],source_row_sha256=h),
                         grade=r['grade'],branch=r['topic'],master_id=master,
                         status='DRAFT_PENDING_EXPORT',source_acceptance_status=r['acceptance_status'],
                         source_file_sha256=sha(casepath.read_bytes()),chat_file_sha256=sha(chatpath.read_bytes()),
                         chat_links=[dict(line=cl,sample_id=c['sample_id'],mode=c['mode'],sha256=ch) for c,ch,cl in linked],
                         actual_fields={k:r[k] for k in FIELDS},
                         curriculum_assignment=deepcopy(r['curriculum_assignment']),
                         original_source_comparison=deepcopy(r['nearest_source_comparison']),
                         semantic_basis=BASIS[master],
                         publisher_image_recognition_or_physical_success_certified=False)
            cases.append(entry);bymaster[master].append(entry)
    assert len(cases)==36 and len(bymaster)==18 and all(len(v)==2 for v in bymaster.values())
    # The manual finite branch decisions above are checked against metadata, not derived from it.
    assert before['sgk_completion_20261021/g5_measurement_models_corrected/cases.jsonl']=='5566927920148c8f35ace48767d97ad46778e9de51adda59cd924fadc9272df2'
    candidate_overlay=[]
    for c in baseline['candidates']:
        master=c['decision']['master_id']; examples=bymaster.get(master,[])
        same=[e for e in examples if e['grade'] in c['reconciliation']['candidate_grades']]
        related=[e for e in examples if e not in same]
        residual=deepcopy(RESIDUAL.get(c['candidate_id'],[]))
        if not examples:status='BASELINE_UNCHANGED_NO_RUN5_DRAFT_MATCH'
        elif related and not same:status='RELATED_RELATION_ONLY_GRADE_AND_BRANCH_PENDING'
        elif residual:status='PARTIAL_FINITE_TEXT_BRANCH_PENDING_EXPORT'
        else:status='FINITE_SAME_GRADE_TEXT_BRANCH_PENDING_EXPORT'
        candidate_overlay.append(dict(candidate_id=c['candidate_id'],master_id=master,
             original_candidate_sha256=sha(canon(c)),prior_status=c['reconciliation']['status'],
             candidate_grades=c['reconciliation']['candidate_grades'],status=status,
             same_grade_draft_examples=[e['reference'] for e in same],
             related_grade_draft_examples=[e['reference'] for e in related],
             semantic_basis=BASIS.get(master,c['reconciliation']['semantic_basis']),
             original_remaining_constraints=deepcopy(c['reconciliation']['remaining_constraints']),
             remaining_after_hypothetical_export=residual if examples else deepcopy(c['reconciliation']['remaining_constraints']),
             original_page_receipts=deepcopy(c.get('page_receipts',[])),
             whole_master_closed=False,accepted_export_verified=False,
             publisher_image_recognition_or_physical_success_certified=False))
    co={x['candidate_id']:x for x in candidate_overlay}
    master_overlay=[];possible_text_satisfied=set();residual_tasks=[];untouched_tasks=[]
    for task in queue['global_master_tasks']:
        master=task['master_id'];examples=bymaster.get(master,[])
        candidates=[co[i] for i in task['candidate_ids']]
        remaining=[x for x in candidates if x['status']!='FINITE_SAME_GRADE_TEXT_BRANCH_PENDING_EXPORT']
        if examples and not remaining:
            status='FINITE_TEXT_TASK_POTENTIALLY_SATISFIED_AFTER_ACCEPTED_HASH_EXPORT'
            possible_text_satisfied.add(master)
        elif examples:status='PARTIAL_RUN5_DRAFT_WITH_EXPLICIT_RESIDUALS'
        else:status='NO_RUN5_DRAFT_MATCH_BASELINE_TASK_RETAINED'
        mo=dict(master_id=master,status=status,candidate_ids=task['candidate_ids'],
                draft_examples=[e['reference'] for e in examples],
                pending_candidate_branches=[dict(candidate_id=x['candidate_id'],grades=x['candidate_grades'],status=x['status'],constraints=x['remaining_after_hypothetical_export']) for x in remaining],
                original_task=deepcopy(task),whole_master_closed=False,accepted_export_verified=False)
        master_overlay.append(mo)
        if master not in possible_text_satisfied:residual_tasks.append(mo)
        if not examples:untouched_tasks.append(mo)
    # Every original occurrence is preserved verbatim; this is a separate overlay only.
    occurrence_overlay=[]
    for o in baseline['occurrences']:
        m=co[o['candidate_id']];grades=o['reconciliation'].get('occurrence_grade',[])
        applicable=[e['reference'] for e in bymaster.get(m['master_id'],[]) if e['grade'] in grades]
        occurrence_overlay.append(dict(occurrence_id=o['occurrence_id'],candidate_id=o['candidate_id'],
           master_id=o['master_id'],occurrence_grade=grades,
           original_occurrence_sha256=sha(canon(o)),candidate_projection_status=m['status'],
           same_grade_draft_examples=applicable,accepted_export_verified=False,
           occurrence_closed=False,publisher_image_recognition_or_physical_success_certified=False))
    counts=dict(draft_cases=36,draft_chat_rows=144,draft_masters=18,
        global_candidates_preserved=204,global_occurrences_preserved=315,global_masters_preserved=167,
        external_g2_candidates_preserved=91,authoritative_global_master_tasks_unchanged=45,
        authoritative_asset_only_masters_separate=10,untouched_global_master_tasks=len(untouched_tasks),
        candidate_projection_statuses=dict(Counter(x['status'] for x in candidate_overlay)),
        finite_text_master_tasks_potentially_satisfied_after_acceptance=len(possible_text_satisfied),
        partial_master_tasks_with_new_drafts=18-len(possible_text_satisfied),
        prospective_remaining_global_master_tasks=len(residual_tasks),
        accepted_or_exported_run5_cases_claimed=0,core_slots_added=0)
    projection=deepcopy(baseline)
    projection['schema']='finite_run5_draft_projection.v1_preserved_baseline'
    projection['run5_draft_projection']=dict(status='DRAFT_PENDING_EXPORT',counts=counts,
        input_hashes=before,candidate_overlay=candidate_overlay,occurrence_overlay=occurrence_overlay,
        outstanding_master_overlay=master_overlay,draft_actual_fields_file='draft_actual_fields.jsonl',
        all_sgk_forms_covered=False,baseline_authority_unchanged=True,
        applicability='Projection only; accepted source and exported row hashes must be rebound after root QA/export. No source draft or original candidate is changed.',
        limitations=['No original publisher image or physical performance certified by explicit text models.',
           'No automatic closure of other grade aliases, distinct geometry branches or any of 91 separate G2 candidates.',
           'Materials cost/budget demonstrates a finite menu; its open-design receipt is retained as an explicit scope residual.',
           'Not an assertion of complete SGK, entire 2006 curriculum or legal/current 2026 curriculum coverage.'])
    assert projection['candidates']==baseline['candidates']
    assert projection['masters']==baseline['masters']
    assert projection['occurrences']==baseline['occurrences']
    assert projection['external_g2_candidates']==baseline['external_g2_candidates']
    write('projection.json',projection)
    (OUT/'draft_actual_fields.jsonl').write_bytes(b''.join(canon(e)+b'\n' for e in cases))
    write('remaining_master_tasks.json',dict(status='PROSPECTIVE_PENDING_EXPORT_NOT_AUTHORITATIVE',counts=counts,
          authoritative_queue_preserved=queue,
          prospective_remaining_global_master_tasks=residual_tasks,
          untouched_global_master_ids=[x['master_id'] for x in untouched_tasks],
          potentially_satisfied_finite_text_task_ids=sorted(possible_text_satisfied),
          external_g2_remaining_separate=deepcopy(queue['external_g2_remaining_separate']),
          unresolved_asset_only_masters=deepcopy(queue['unresolved_asset_only_masters'])))
    after={p.relative_to(PUB).as_posix():sha(p.read_bytes()) for p in paths}
    assert before==after
    receipt=dict(status='PASS_PRESERVATION_AND_MAPPING',counts=counts,inputs_unchanged=before==after,
          original_candidates_verbatim_preserved=True,original_masters_verbatim_preserved=True,
          occurrences315_verbatim_preserved=True,external_g2_91_verbatim_preserved=True,
          all_36_raw_source_hashes_and_144_chat_links_bound=True,
          source_drafts_not_accepted_by_this_projection=True,authoritative_queue_not_changed=True,
          whole_sgk_coverage_claimed=False,drive_mutated=False,state_mutated=False,training_started=False,
          input_hashes=before,helper_sha256=sha(Path(__file__).read_bytes()),
          output_hashes={n:sha((OUT/n).read_bytes()) for n in ['projection.json','draft_actual_fields.jsonl','remaining_master_tasks.json']})
    write('validation.json',receipt)
    print(json.dumps(dict(status=receipt['status'],counts=counts,output_hashes=receipt['output_hashes']),ensure_ascii=False))

if __name__=='__main__':main()

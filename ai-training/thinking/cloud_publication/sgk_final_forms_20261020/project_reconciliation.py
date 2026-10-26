"""Prospective semantic mapping only; never accept drafts or mutate old queues."""
from pathlib import Path
from collections import Counter
import json,hashlib

RUN=Path(__file__).resolve().parent
BASE=RUN.parent/'sgk_remaining_20261020/reconciliation'
FIELDS=['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints']
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def read(p):return json.loads(p.read_text('utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')

NOTES={
'decimal_symbol_open_interval_synthesis':('g5_candidate_decimal_symbol_choice','Fixed digit order, exactly one legal internal decimal comma, every slot enumerated, both strict interval bounds tested; second branch separates equal-value arithmetic from excluded endpoints.'),
'finite_decimal_digit_card_enumeration':('g5_candidate_decimal_card_enumeration','Fixed X,YZ format, permitted zero integer and trailing zero, exhaustive distinct strings and extrema. Second branch separately counts physical repeated-glyph card identities, strings, and numeric values.'),
'edge_scale_square_cube_relation':('g5_candidate_surface_volume_scaling','Uniform scale on every cube edge explicitly compared against area and volume, using squared versus cubed factors; shrink branch directly corrects an observable linear-scaling claim.'),
'large_cube_painted_face_classification':('g5_candidate_painted_cubes','Explicit complete 3-by-3-by-3 grid classified by 3/2/1/0 painted faces; both all-six-face and unpainted-bottom five-face conventions distinguish corner/edge/face/interior positions and conserve totals.'),
'same_height_triangle_area_ratio':('g5_candidate_triangle_base_ratio','Shared apex and collinear split base yield proportional areas 3:5 from known total without inventing height. Counterexample with unequal specified heights establishes the missing equal-height premise.'),
'triangle_parallel_apex_area_invariant':('g5_candidate_triangle_parallel_apex','Fixed base and parallel apex locus preserve perpendicular distance including external altitude feet. Counterexample changes height along a nonparallel path rather than falsely applying invariance.'),
'finite_operator_synthesis':('g5_candidate_unknown_fraction_operator','Fixed fraction operands and ordered plus/minus-only syntax, complete finite sign choices under equality; unique solution and no-legal-sign observable-error branches. G3 integer branch remains inherited separately.'),
'finite_route_total_optimization':('g5_candidate_shortest_route','Complete finite explicit bidirectional graph paths, weighted total minimum, return route convention, speeds, minute conversion and per-km round-trip cost. Separate unique reversed-return and tied independent-return branches.'),
'fixed_volume_surface_arrangement_optimization':('g5_candidate_equal_volume_surface','Full finite positive-integer base/height inventory with height orientation retained. Four-lateral-wall objective differs from inherited closed-six and open-five-face objectives; height-constrained error branch checks incorrect rotational pruning.')}

ASSIGNMENTS=[
 ('next_g5_measurement_models',[
  ('bill_of_materials_area_cost',5,'Count each board component once, derive total area and per-area cost; include an explicit open design and finite budget constraint rather than another tile-pack purchase.'),
  ('compare_equal_sharing_cut_schemes',5,'Define two cutting/distribution schemes, original units and piece inventory; prove equal shares or expose one infeasible scheme without inventing permission to join or discard pieces.'),
  ('grid_boundary_missing_dimensions',5,'Supply exact complete outer grid edge structure, unit-cell scale and any holes. Infer missing dimensions then area; do not pretend to see an unspecified figure.'),
  ('gridded_net_dimensions_to_volume',5,'Supply six gridded face dimensions and fold adjacency, infer three consistent solid dimensions and volume. Distinguish dimension inference from already-covered net validity.'),
  ('mixed_orientation_rectangle_tiling',5,'Use a small exact rectangle and fixed rectangular-piece inventory with stated rotations. Prove a mixed-orientation exact cover and an obstruction branch, not area-divisibility alone.'),
  ('nested_triangle_base_altitude_assignment',5,'Specify nested triangles and distinct perpendicular height data; pair each selected base with its own altitude, including an external-foot branch. Do not reuse only the shared-height ratio.')]),
 ('next_finite_inventory_and_edges',[
  ('all_boundary_labels_joint_match',1,'Supply explicit named regions and every boundary label plus die outcomes. Region eligibility must satisfy all boundary conditions jointly; include a misleading partial match.'),
  ('shared_edge_stick_construction',1,'Give a finite exact edge arrangement with two triangles sharing one edge and five sticks; verify inventory and that shared edge is counted once. No imaginary drawing or physical completion claim.'),
  ('composite_square_only_enumeration',1,'Provide a small explicit grid and enumerate square-only equal-side subsets including the outer composite square; distinguish rectangles that fail equal-side condition.'),
  ('finite_inventory_collection_game',3,'Fully specify board transitions, token identities, remove-on-collection, owner inventory and winning threshold. Distinguish repeated equal values from the same token and simulate supplied moves.'),
  ('edge_removal_game_terminal',4,'Specify finite unit-edge geometry, turn sequence and removal legality. Re-enumerate every target shape after a move and prove termination under the declared no-target condition.'),
  ('glyph_parallel_perpendicular_filter',4,'Give exact straight segment endpoints for a small glyph inventory; filter simultaneous parallel/perpendicular relations with a stated incidence convention. No inference from an unstated font.')]),
 ('next_geometric_relation_models',[
  ('equal_area_geometric_regrouping',3,'Use an exact partition into half-unit triangles and rectangles, regroup to identical area units and prove no gaps or overlap. Keep learner explanation within grade-appropriate counting.'),
  ('equal_area_transfer_cancellation',4,'Specify equal transferred triangular pieces and common-region cancellation. Verify equality after transfer and separate area conservation from perimeter change.'),
  ('missing_parallelogram_vertex',4,'Supply three points or small grid directions and allowed vertex order. Reconstruct all permitted missing vertices by opposite-side parallel relations; preserve multiple orientations.'),
  ('occlusion_partial_layer_order',4,'Supply explicit front-of/behind observations between named layers, not an unseen image. Find every compatible total order or identify an inconsistent cycle; preserve unresolved ties.'),
  ('tangent_circle_alignment_lengths',3,'Give exact aligned circle centers, equal radii and external tangency along a line. Derive diameter-chain/rectangle lengths from that model, with no assumed actual compass result.'),
  ('specified_area_preserving_dissection',5,'Fully specify a finite cut partition and legal translations/rotations, target coverage and no-overlap/no-gap argument. Preserve distinct G3/G4/G5 aliases; demonstrate one chosen grade/branch only.')])]

def main():
    paths=[BASE/'next_uncovered_tasks.json',BASE/'candidate_adjudication.json']
    paths += [RUN/d/n for d in ['g5_exact_text','g5_residual_text'] for n in ['cases.jsonl','chat.jsonl']]
    frozen={str(p):sha(p.read_bytes()) for p in paths}
    queue=read(paths[0]);prior=read(paths[1]);tasks={r['master_id']:r for r in queue['global_master_tasks']}
    assert len(prior['candidates'])==204 and len(prior['occurrences'])==315 and len(prior['external_g2_candidates'])==91
    expected={'g5_exact_text':('b52c14e9a5c3020a7147201ee8a9dd14ca81c9131ff1b7a0a1dab6766a41da5a','e4491f20adcc4cafb48667a479b934e3f6a1e714ea413f3dbc72fabe8b176f13'),
    'g5_residual_text':('a28c0806e59669bbddff5da43591c5da5d78b317972496e7a6dd28f6da7e1002','cab230016ad010e15e267ddf098bf8480e0b32c052e47f62adc3383f97703a99')}
    examples={};actual=[];snapshots=[]
    for directory,(ch,hh) in expected.items():
        src=RUN/directory/'cases.jsonl';chat=RUN/directory/'chat.jsonl'
        assert sha(src.read_bytes())==ch and sha(chat.read_bytes())==hh
        snapshots += [dict(file=str(p.relative_to(RUN)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size) for p in [src,chat]]
        for line,b in enumerate(src.read_bytes().splitlines(),1):
            r=json.loads(b);assert r['grade']==5 and r['split']=='train'
            master=r.get('coverage',{}).get('finite_master_id') or r['curriculum_assignment']['master_id']
            assert master in NOTES and r['acceptance_status'].startswith('DRAFT')
            ref=dict(sample_id=r['sample_id'],file=str(src.relative_to(RUN)),line=line,source_row_sha256=sha(b),grade=5,acceptance_status=r['acceptance_status'],status='PENDING_ACCEPTANCE')
            examples.setdefault(master,[]).append(ref)
            actual.append(dict(reference=ref,actual_fields={k:r[k] for k in FIELDS},curriculum_assignment=r['curriculum_assignment'],semantic_projection_scope='Actual fields read for candidate matching; this projection does not independently accept or replace peer/root QA.'))
    assert len(actual)==18 and len(examples)==9 and all(len(v)==2 for v in examples.values())
    bycandidate={r['candidate_id']:r for r in prior['candidates']}
    projections=[]
    for master,(candidate,note) in NOTES.items():
        original=bycandidate[candidate];assert original['decision']['master_id']==master
        assert original['reconciliation']['candidate_grades']==[5]
        projections.append(dict(master_id=master,candidate_id=candidate,status='PENDING_ACCEPTANCE',prospective_text_relation_match=True,master_closed=False,original_candidate=original,original_candidate_sha256=sha(canonical(original).encode()),original_open_task=tasks[master],draft_examples=examples[master],semantic_basis=note,remaining_gates=['Exact-hash peer/root content QA and any repair must finish before acceptance.','Projection must be rebound to exported accepted row hashes; draft hashes are not exported hashes.','Original page instances and image/physical competency are not certified by text analogues.'],additional_authoring_for_same_relation_recommended=False))
    holds={p['candidate_id']:p for p in projections}
    conserved=[]
    for c in prior['candidates']:
        p=holds.get(c['candidate_id'])
        conserved.append(dict(candidate_id=c['candidate_id'],master_id=c['decision']['master_id'],original_candidate_sha256=sha(canonical(c).encode()),authoritative_status_unchanged=c['reconciliation']['status'],prospective_status='PENDING_ACCEPTANCE' if p else 'NO_RUN4_CHANGE',prospective_examples=p['draft_examples'] if p else []))
    occurrence_inventory=[dict(occurrence_id=o['occurrence_id'],candidate_id=o['candidate_id'],master_id=o['master_id'],original_occurrence_sha256=sha(canonical(o).encode()),original_status=o['reconciliation']['status'],prospective_status='PENDING_ACCEPTANCE' if o['candidate_id'] in holds else 'NO_RUN4_CHANGE') for o in prior['occurrences']]
    assignments=[];claimed=set()
    for aid,masters in ASSIGNMENTS:
        items=[]
        for master,grade,instruction in masters:
            assert master in tasks and master not in examples and master not in claimed
            claimed.add(master);task=tasks[master]
            items.append(dict(master_id=master,target_grade=grade,status='PROPOSED_NOT_STARTED',original_task=task,required_small_task=instruction,scope='Original explicit mathematical model/text only; grade-appropriate enrichment if needed, no unseen original image or physical success claim.',case_budget='At most two substantive distinct branches; do not generate number-only variants. Exact candidate/nearest read and independent oracle required.'))
        assert len(items)<=6
        assignments.append(dict(assignment_id=aid,status='PROPOSED_NOT_STARTED',masters=items,maximum_master_count=6,maximum_cases_if_two_each=12))
    result=dict(schema='finite_run4_semantic_projection.v1',status='PENDING_ACCEPTANCE',scope='Prospective mapping of 18 existing RUN4 drafts only. No authoring, acceptance, training, Drive, old queue or state changes.',input_snapshots=[dict(file=str(p),sha256=h) for p,h in [(p,frozen[str(p)]) for p in paths]],draft_source_snapshots=snapshots,counts=dict(original_global_candidates=204,original_global_occurrences=315,original_global_masters=167,external_g2_records_separate=91,authoritative_open_global_tasks_unchanged=54,authoritative_asset_only_masters_separate_unchanged=10,draft_cases_inspected=18,draft_chat_rows_inventory=72,prospective_same_grade_candidate_branches=9,prospective_master_relations=9,other_open_global_tasks_without_this_RUN4_evidence=45,next_disjoint_assignments=3,next_disjoint_masters=18),prospective_matches=projections,conserved_candidate_inventory=conserved,conserved_occurrence_inventory=occurrence_inventory,external_g2_preservation=dict(count=91,sha256=sha(canonical(prior['external_g2_candidates']).encode()),status='UNCHANGED_NO_G2_CLOSURE_FROM_G5_DRAFTS'),next_authoring_assignments=assignments,limitations=['Every prospective row remains DRAFT/PENDING_ACCEPTANCE. Original statuses are retained; 54 is the authoritative open-task count until accepted and adjudicated.','The nine relation matches do not prove every original page problem/asset, every number instance or every SGK series is covered.','Same-height ratio is a general relation, not a reason to generate another numbers-only equal-base example; any original median/equal-subdivision instance needs precise mapping review rather than blanket extra authoring.','All 315 occurrence identities remain in the projection; inherited page-image receipts are not newly visually reverified.','No independent external/human reviewer claim.'])
    out=RUN/'reconciliation_projection.json';write(out,result)
    evidence=RUN/'reconciliation_projection_actual_fields.jsonl';evidence.write_text(''.join(canonical(x)+'\n' for x in actual),encoding='utf-8',newline='\n')
    assert all(sha(p.read_bytes())==h for p,h in [(p,frozen[str(p)]) for p in paths])
    receipt=dict(status='PASS_PROJECTION_ONLY_NOT_ACCEPTANCE',input_bytes_unchanged=True,global_candidates_conserved=len(conserved),occurrences_conserved=len(occurrence_inventory),external_g2_unchanged=91,draft_cases_actual_fields_read=18,prospective_candidate_matches=9,next_assignments_disjoint=True,next_master_count=len(claimed),outputs=[dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in [out,evidence]],helper_sha256=sha(Path(__file__).read_bytes()),training_started=False,drive_mutated=False,old_state_mutated=False)
    write(RUN/'reconciliation_projection_receipt.json',receipt);print(json.dumps(receipt))
if __name__=='__main__':main()

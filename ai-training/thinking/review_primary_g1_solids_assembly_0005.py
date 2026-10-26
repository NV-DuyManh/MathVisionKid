"""Separate content pass, exact toy geometry checks and bounded research curation."""
import json
from fractions import Fraction as F
from collections import Counter
from itertools import permutations
from datetime import datetime,timezone
from primary_math_data_pipeline import (DEFAULT_ROOT,HERE,REVIEW_FIELDS,read_rows,write_rows,write_json,
    row_sha,sha,inspect_case,curate)


def main():
    path=DEFAULT_ROOT/'authored_batches/g1_solids_assembly_0005.jsonl'
    reviews=DEFAULT_ROOT/'reviews/g1_solids_assembly_0005_AI_review.jsonl'
    if reviews.exists():print('Already reviewed; do not repeat curation with an old expected count.');return
    evidence=HERE/'evidence/primary_math_teacher_20261016';rows=read_rows(path)
    assert len(rows)==10
    write_rows(evidence/'g1_solids_assembly_0005_before_content_edit.jsonl',rows)
    # The question asks for a construction method. The draft hint2 gave that
    # entire method, so retain only a local trial/check rather than the answer.
    rows[4]['hints'][1]={'level':2,
        'hint':'Thử đưa hai mép cùng nguồn gốc lại gần nhau và so độ dài trước khi đặt hẳn.',
        'question':'Để khớp trọn mép, hai đầu của mỗi mép cần thẳng hàng thế nào?'}
    rows[4]['hints'][2]={'level':3,
        'hint':'Sau một lần thử, kiểm xem giấy có che lên nhau hoặc để hở; nếu có, xoay một miếng và thử lại.',
        'question':'Lần thử của em có khớp mép ngoài ban đầu mà không che hoặc hở giấy không?'}

    def faces(d):
        a,b,c=d;return [(a,b),(a,b),(a,c),(a,c),(b,c),(b,c)]
    def cube(d):return all(a==b for a,b in faces(d))
    assert cube((1,1,1)) and not cube((1,1,2))
    assert sum(a==b for a,b in faces((1,1,2)))==2
    assert all(not cube(d) and sorted(d)==[1,2,3] for d in permutations((1,2,3)))
    two_cells={(0,0),(1,0)}
    assert len(two_cells)==2
    assert max(x for x,y in two_cells)-min(x for x,y in two_cells)+1==2
    assert max(y for x,y in two_cells)-min(y for x,y in two_cells)+1==1
    triangles=[[(F(0),F(0)),(F(1),F(0)),(F(1),F(1))],
               [(F(0),F(0)),(F(1),F(1)),(F(0),F(1))]]
    # Cancel the common diagonal. Verify a four-sided unit-square boundary.
    edges=Counter(tuple(sorted((poly[k],poly[(k+1)%3]))) for poly in triangles for k in range(3))
    boundary=[edge for edge,count in edges.items() if count==1]
    shared=[edge for edge,count in edges.items() if count==2]
    assert len(boundary)==4 and len(shared)==1
    assert all((x-u)**2+(y-v)**2==1 for ((x,y),(u,v)) in boundary)
    vertices={v for edge in boundary for v in edge}
    assert vertices=={(0,0),(1,0),(1,1),(0,1)}
    def area(poly):return abs(sum(x*poly[(k+1)%3][1]-y*poly[(k+1)%3][0] for k,(x,y) in enumerate(poly)))/2
    assert sum(map(area,triangles))==1
    target={(0,0),(1,0),(0,1),(1,1)}
    placed={(0,0),(1,0),(0,1)};remaining=target-placed
    assert remaining=={(1,1)} and placed.isdisjoint(remaining) and placed|remaining==target
    one_square={(0,0)};overlap=one_square|one_square
    assert overlap==one_square and len(overlap)==1
    counterexamples=[{'dimensions':[1,1,1],'front':[1,1],'cube':True},
                     {'dimensions':[1,1,2],'front':[1,1],'cube':False}]
    assert len({v['cube'] for v in counterexamples})==2
    oracles=[
        {'method':'complete_six_face_record','square_faces':sum(a==b for a,b in faces((1,1,1))),'cube':True},
        {'method':'contrasting_complete_face_records','A_dimensions':[1,1,1],'B_dimensions':[1,1,2],'B_square_faces':2,'B_non_square_faces':4},
        {'method':'all_six_axis_permutations_preserve_unequal_dimension_multiset','witness_dimensions':[1,2,3],'all_cube_tests':False},
        {'method':'exact_unit_cell_union','cells':[[0,0],[1,0]],'outer_width':2,'outer_height':1},
        {'method':'exact_rational_triangle_edge_cancellation','common_internal_edges':1,'outer_unit_edges':4,'triangle_areas':['1/2','1/2'],'union_area':'1'},
        {'method':'target_minus_occupied_cells','unfilled_cell':[1,1],'coordinate_convention':'x0=left,x1=right,y0=top,y1=bottom','complete_nonoverlapping_fill':True},
        {'method':'one_square_face_and_four_non_square_side_faces','witness_dimensions':[1,1,2],'cube':False},
        {'method':'coincident_unit_cell_union','stacked_squares':2,'distinct_outline_cells':1,'width':1,'height':1},
        {'method':'two_boxes_same_square_front_different_cube_status','counterexamples':counterexamples},
        {'method':'missing_target_parts_and_observed_arrangement','sufficient_evidence_available':False,'no_pass_fail_inference':True}
    ]
    notes=[
        'All six congruent square faces of a closed box model justify cube. Keeps solid versus face names distinct. Familiar dice comparison is a hypothetical model, no claim of inspecting a real die. Three hints give feature checks without naming cube.',
        'A satisfies all-square equal-face condition. B has exactly two square ends and four non-square rectangular sides, so elongated rectangular box, not cube. Contrast is about sufficient whole-object evidence, not object colour or orientation. Does not assert cubes cannot be rectangular prisms in inclusive geometry.',
        'Unequal length/width/height persist under reorientation without deformation. Axis-permutation witnesses check the relation independently. Visible reasoning explains invariance, not just repeats the initial label. No claim pupil physically performed or passed the activity.',
        'Two congruent squares joined on a complete common side with disjoint interiors and no gaps have a2-by1 rectangular outline. Explanation removes internal seam from outer boundary and checks long/short sides. Distinct from stacking and from four-cell completion; hints do not name final shape.',
        'Diagonal cut of a square creates matching triangles that reconstruct square when original cut edges meet with interiors opposite. Exact boundary cancellation and areas check a concrete witness. Found draft hint2 leaked the full requested placement method; replaced it with a local edge-alignment trial and hint3 with a check/retry prompt before acceptance. Final method only in worked output.',
        'Explicit2-by2 target, three occupied cells and one congruent remaining tile force lower-right. Set complement and nonoverlap checks agree. Transfer task requires tracking all positions and checking fill, not merely adding counts. Hints never name lower-right.',
        'Synthetic one-face sufficiency statement directly contradicted by non-square side faces. Feedback identifies incomplete evidence and correct whole-box label; no invented observation about a child viewing or rotating a real object. Hints ask omitted faces rather than announcing final label.',
        'Exactly coincident square boundaries cannot produce a longer outline. Teacher distinguishes stacking from edge joining and gives square outline; it does not falsely claim square is outside the general rectangle class. Only the explicitly written increased-length claim is criticized.',
        'Square front alone fits cube1x1x1 and box1x1x2. Unknown identity remains unresolved; requests other faces rather than hallucinating hidden surfaces. Guard not counted as core, no actual image received or used.',
        'Without target, supplied pieces or student arrangement there is no basis to mark the house assembly correct or wrong. Requests each necessary evidence source and rules; does not diagnose gaps, overlap or unused pieces as observed facts.'
    ]
    decisions=[];checks=[]
    for i,r in enumerate(rows):
        m=inspect_case(r);assert m['passed'],(r['sample_id'],m)
        assert all(s['expression'] is None for s in r['worked_steps'])
        assert r['provenance']['visual_or_physical_outcome_verified'] is False
        if i>=8:assert r['can_solve'] is False and not r['worked_steps'] and not r['expected_answer']
        decisions.append({'sample_id':r['sample_id'],'row_sha256':row_sha(r),
            'reviewer':'root_single_assistant_separate_content_review_pass',**{k:True for k in REVIEW_FIELDS},
            'human_verified':False,'teacher_certified':False,'independent_external_AI_reviewer':False,
            'review_method':'Read every visible case and hint after authoring; exact finite geometry witnesses are independent computations, not an external semantic reviewer.',
            'notes':notes[i],'oracle':oracles[i]})
        checks.append({'sample_id':r['sample_id'],'row_sha256':row_sha(r),'mechanical':m,'oracle':oracles[i]})
    write_rows(path,rows);write_rows(reviews,decisions)
    bp=json.loads((DEFAULT_ROOT/'curriculum_blueprint.json').read_text('utf-8'))
    frozen={p:sha((HERE.parent/p).read_bytes())==h for p,h in bp['existing_inputs']['source_fingerprints'].items()}
    assert all(frozen.values())
    state=curate(DEFAULT_ROOT)
    assert state['accepted_cases']==68 and state['chat_train_rows']==272 and state['remaining_core_cases']==446
    assert state['core_nodes_complete']==10 and state['decisions']=={'ACCEPTED_AI_RESEARCH':68}
    write_json(evidence/'g1_solids_assembly_0005_verification.json',{
        'created_utc':datetime.now(timezone.utc).isoformat(),'batch_sha256':sha(path.read_bytes()),
        'review_sha256':sha(reviews.read_bytes()),'checks':checks,'frozen_inputs_unchanged':frozen,
        'draft_hint_leak_repaired_before_acceptance':rows[4]['sample_id'],
        'all_steps_categorical':True,'oracle_is_universal_semantic_proof':False,
        'external_independent_semantic_review':False,'teacher_certified':False,'human_verified':False,
        'visual_or_physical_outcome_verified':False,'training_started':False,'sealed_concept_challenge_read':False,
        'result':{k:state[k] for k in ('accepted_cases','chat_train_rows','remaining_core_cases','core_nodes_complete','decisions')}})
    print(json.dumps({k:state[k] for k in ('accepted_cases','chat_train_rows','remaining_core_cases','core_nodes_complete','decisions')}))


if __name__=='__main__':main()

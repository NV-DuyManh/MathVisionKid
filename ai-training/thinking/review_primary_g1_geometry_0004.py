"""Hash-bound content review and explicit finite-relation checks, not teacher gold."""
import json
from fractions import Fraction as F
from datetime import datetime, timezone
from primary_math_data_pipeline import (DEFAULT_ROOT,HERE,REVIEW_FIELDS,read_rows,write_rows,write_json,
    row_sha,sha,inspect_case,curate)


def main():
    batch=DEFAULT_ROOT/'authored_batches/g1_geometry_0004.jsonl'
    reviews=DEFAULT_ROOT/'reviews/g1_geometry_0004_AI_review.jsonl'
    if reviews.exists(): print('Review exists; inspect current state rather than repeating.');return
    evidence=HERE/'evidence/primary_math_teacher_20261016'
    rows=read_rows(batch);assert len(rows)==10
    write_rows(evidence/'g1_geometry_0004_before_content_edit.jsonl',rows)
    rows[2]['hints'][0]['question']='Bạn ở giữa khác bạn đầu hàng và cuối hàng ở điểm nào?'
    rows[3]['hints'][1]['question']='Hình tam giác có bao nhiêu cạnh thẳng theo bài em đã học?'
    rows[7]['worked_steps'][1]['explanation']='Miếng có dạng hình tam giác vì có ba cạnh thẳng nối kín. Tên hình này khớp với toàn bộ mô tả của đề.'
    # Relational oracles use supplied finite arrangements, not language keywords.
    order=['cốc','sách','hộp'];i=order.index('sách')
    sides=[order[i-1],order[i+1]];assert sides==['cốc','hộp']
    heights={'gấu':2,'xe':1};assert heights['xe']<heights['gấu']
    queue=['An','Bình','Chi'];j=queue.index('Bình')
    queue_answer=[queue[len(queue)//2],queue[j-1],queue[j+1]];assert queue_answer==['Bình','An','Chi']
    # Exact, rational rigid rotation as a supplementary invariant witness.
    vertices=[(F(0),F(0)),(F(1),F(0)),(F(1),F(1)),(F(0),F(1))]
    rotated=[(F(3,5)*x-F(4,5)*y,F(4,5)*x+F(3,5)*y) for x,y in vertices]
    distances=lambda vs:[(x-u)**2+(y-v)**2 for k,(x,y) in enumerate(vs) for u,v in vs[k+1:]]
    assert distances(vertices)==distances(rotated)
    edges=lambda vs:[(vs[(k+1)%4][0]-x,vs[(k+1)%4][1]-y) for k,(x,y) in enumerate(vs)]
    rv=edges(rotated)
    assert all(x*x+y*y==1 for x,y in rv)
    assert all(rv[k][0]*rv[(k+1)%4][0]+rv[k][1]*rv[(k+1)%4][1]==0 for k in range(4))
    descriptors={'A':{'curved':True,'edges':None},'B':{'curved':False,'edges':4},'C':{'curved':False,'edges':3}}
    triangle=[k for k,v in descriptors.items() if v['edges']==3 and not v['curved']]
    assert triangle==['C']
    matching={'A':'tròn','B':'tam giác','C':'vuông','D':'chữ nhật'}
    assert len(matching)==len(set(matching.values()))==4
    assert ['bóng','vở','bút'].index('vở')<['bóng','vở','bút'].index('bút')
    # Both counterexamples fit the guard input but need different outputs.
    spatial_counterexamples=[{'page_order':['cốc','sách'],'relation':'trái'},
                             {'page_order':['sách','cốc'],'relation':'phải'}]
    colour_counterexamples=[{'colour':'đỏ','shape':s} for s in ['tròn','tam giác','vuông']]
    assert len({c['relation'] for c in spatial_counterexamples})==2
    assert len({c['shape'] for c in colour_counterexamples})==3
    oracles=[
        {'method':'index_neighbours_in_fixed_page_order','order':order,'answers':sides},
        {'method':'strict_vertical_order_with_reversed_reference','heights':heights,'answers':['ở dưới gấu','ở trên xe']},
        {'method':'queue_neighbours_with_common_facing_direction','queue_nearest_door_first':queue,'answers':queue_answer},
        {'method':'explicit_boundary_feature_selection','features':descriptors,'unique_triangle':triangle},
        {'method':'exact_rational_rigid_rotation_witness','all_pair_distances_preserved':True,'four_unit_edges_and_right_corners_preserved':True,'limits':'Witness supports the invariant; not an observed physical activity or exhaustive proof from this code.'},
        {'method':'four_explicit_feature_records_one_to_one_matching','matching':matching,'square_is_not_declared_disjoint_from_all_rectangles':True},
        {'method':'index_order_relative_to_given_anchor','page_order':['bóng','vở','bút'],'anchor':'bút','relation':'trái'},
        {'method':'explicit_closed_three_straight_edge_boundary','curved':False,'edge_count':3,'classification':'tam giác'},
        {'method':'construct_two_consistent_layouts_with_different_answers','counterexamples':spatial_counterexamples},
        {'method':'construct_three_same_colour_different_shape_cases','counterexamples':colour_counterexamples}
    ]
    notes=[
        'Reference and page direction explicitly fixed. Left neighbour cup and right neighbour box both correct; each answer grounds in the stated order. Three hints focus on reference, neighbours, then checking without naming cup/box. Text relation teaching only, no vision claim.',
        'Two explicit heights unambiguously give car below bear and bear above car. Reverse reference is a genuine contrast and does not assert objects move. Hints ask reference and relational consistency without supplying the relation words as answers.',
        'Common facing towards door fixes front/back rather than guessing an observer frame. Queue An–Binh–Chi yields middleBinh, frontAn, behindChi; all three relations and check shown. Rephrased first hint question for young learners. No invented reordering.',
        'C uniquely meets three straight closed sides; A curved and B four-sided cannot satisfy that definition. Grade-one recognition supported by familiar language, not formal angle measurement. Hint2 now asks a clear conceptual recall question, does not name the selected card.',
        'Initial square is explicit; hypothetical in-plane rotation without cutting/folding preserves shape. Visible explanation identifies unchanged edges/corners, not only number of sides. Does not say an observed child actually rotated successfully. Hints preserve invariant reasoning without stating the resulting name.',
        'Four fully described cards map one-to-one to familiar shape names. D explicitly has unequal long/short pairs and paper-like right corners; C has four equal sides and such corners. Does not teach the false general claim that squares are outside the rectangle class. Classification and reverse check shown; hints do not disclose pair labels.',
        'Synthetic right-of statement is contradicted by fixed page order; corrected left-of relation uses the same anchor. Feedback distinguishes reversing a statement from answering the asked relation. No claim that child used wrong hand, mis-saw an image or physically changed orientation.',
        'Synthetic circle label conflicts with three straight closed edges. Correction explains curved versus straight and the three-edge triangle; simplified final sentence to be child-facing. No invented image or colour observations. Hints leave the final shape name for pupil.',
        'Absent image and order allow both left/right layouts; a numeric or directional answer is not identifiable. Requests a clear image or fixed page order and anchor. Not a solved core, no made-up position. Each hint asks a specific missing item.',
        'Red alone admits circle, triangle and square. Requests boundary image/description then edges/corners when needed. No predicted label from colour; no fabricated measurements. Guard is separate from core recognition quota.'
    ]
    decisions=[];checks=[]
    for k,r in enumerate(rows):
        m=inspect_case(r);assert m['passed'],(r['sample_id'],m)
        assert all(s['expression'] is None for s in r['worked_steps'])
        if k>=8:assert not r['expected_answer'] and not r['worked_steps'] and r['can_solve'] is False
        decisions.append({'sample_id':r['sample_id'],'row_sha256':row_sha(r),
            'reviewer':'root_single_assistant_separate_content_review_pass',**{f:True for f in REVIEW_FIELDS},
            'human_verified':False,'teacher_certified':False,'independent_external_AI_reviewer':False,
            'review_method':'Full visible content read after authoring plus explicit finite relation/feature oracles; same assistant, not a second semantic reviewer.',
            'notes':notes[k],'oracle':oracles[k]})
        checks.append({'sample_id':r['sample_id'],'row_sha256':row_sha(r),'mechanical':m,'oracle':oracles[k]})
    write_rows(batch,rows);write_rows(reviews,decisions)
    bp=json.loads((DEFAULT_ROOT/'curriculum_blueprint.json').read_text('utf-8'))
    frozen={p:sha((HERE.parent/p).read_bytes())==h for p,h in bp['existing_inputs']['source_fingerprints'].items()}
    assert all(frozen.values())
    state=curate(DEFAULT_ROOT)
    assert state['accepted_cases']==58 and state['chat_train_rows']==232 and state['remaining_core_cases']==452
    assert state['core_nodes_complete']==8 and state['decisions']=={'ACCEPTED_AI_RESEARCH':58}
    write_json(evidence/'g1_geometry_0004_verification.json',{
        'created_utc':datetime.now(timezone.utc).isoformat(),'batch_sha256':sha(batch.read_bytes()),
        'review_sha256':sha(reviews.read_bytes()),'checks':checks,'frozen_inputs_unchanged':frozen,
        'all_steps_categorical':True,'arithmetic_gate_is_semantic_proof':False,
        'external_independent_semantic_review':False,'teacher_certified':False,'human_verified':False,
        'visual_or_physical_outcome_verified':False,'training_started':False,'sealed_concept_challenge_read':False,
        'result':{k:state[k] for k in ('accepted_cases','chat_train_rows','remaining_core_cases','core_nodes_complete','decisions')}})
    print(json.dumps({k:state[k] for k in ('accepted_cases','chat_train_rows','remaining_core_cases','core_nodes_complete','decisions')}))


if __name__=='__main__':main()

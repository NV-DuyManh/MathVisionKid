"""Independent predicates after root read all twelve network/guard tasks."""
from itertools import combinations,permutations
from sgk_finish_text_root_review import review

def independent(t):
    if t.startswith('capacity_'):
        load,branches=(5,{'A':[6,4],'B':[5,7]}) if t.endswith('edge') else (2500,{'P':[3000,2400],'Q':[2600,2000]})
        valid=[k for k,values in branches.items() if all(load<=v for v in values)];assert valid==(['B'] if load==5 else []);return dict(common_unit_load=load,branch_edge_limits=branches,valid=valid,all_edges_not_sum_of_limits=True)
    if t=='colors_unordered_limited':
        colors={'R1':'Đỏ','R2':'Đỏ','B1':'Xanh'};valid=sorted({tuple(sorted(colors[x] for x in pair)) for pair in combinations(colors,2)})
        assert len(valid)==2 and ('Xanh','Xanh') not in valid;return dict(all_color_multisets=valid,explicit_identity_pairs=list(combinations(colors,2)))
    if t=='colors_order_vs_multiset':
        colors=['Đ','X','V'];ordered=list(permutations(colors,2));unordered={frozenset(pair) for pair in ordered};assert len(ordered)==6 and len(unordered)==3;return dict(ordered=ordered,unordered=[sorted(v) for v in unordered],counts=[6,3])
    if t=='running_state_unique_path':
        a=[6,6+4,(6+4)*2];b=[6,6*2,6*2+4];assert a[-1]==20 and b[-1]==16;return dict(path_A_states=a,path_B_states=b,valid=['S','A','T'])
    if t=='running_state_shared_node':
        a=[12,12-4,(12-4)*3,(12-4)*3-2];b=[12,12+6,(12+6)//3,(12+6)//3-2]
        assert a==[12,8,24,22] and b==[12,18,6,4];return dict(A_states=a,B_states=b,valid=['S','B','M','T'],shared_vertex_not_fixed_value=True)
    if t=='skip_two_interior_nodes':
        route=list('ABCDE');start=0;k=2;landing=start+k+1;assert route[landing]=='D';return dict(skipped=route[start+1:landing],landing=route[landing],edges=landing-start)
    if t=='skip_zero_then_one_error':
        route=['P','Q','R','U','V'];position=0;landings=[];edges=0
        for k in (0,1):position+=k+1;edges+=k+1;landings.append(route[position])
        assert landings==['Q','U'] and edges==3;return dict(landings=landings,edges=edges)
    if t.startswith('interval_'):
        spans={'A':(480,540),'B':(540,600),'C':(510,570)} if t.endswith('allowed') else {'P':(480,540),'Q':(540,600),'R':(600,660)};touch=t.endswith('allowed');valid=[]
        for a,b in combinations(spans,2):
            left,right=sorted([spans[a],spans[b]])
            if (left[1]<=right[0] if touch else left[1]<right[0]):valid.append((a,b))
        assert valid==([('A','B')] if touch else [('P','R')]);return dict(spans_minutes=spans,valid=valid,touch_allowed=touch)
    if t=='guard_stock_stop_conflict':
        assignments=[n for n in range(4)];assert max(assignments)==3 and not any(n>=4 for n in assignments);return dict(max_single_player_inventory=3,victory_threshold=4,reachable_victory=False,stock_empty_termination_rule_supplied=False,actual_player_log_supplied=False,appropriate_response='Ask for clarification, no actual winner claim')
    if t=='guard_unknown_eligible_set':
        held={'A','B','C'};worlds=[{'A','B','C'},set('ABCDE')];outcomes=[held>=valid for valid in worlds];assert outcomes==[True,False];return dict(two_consistent_eligible_sets=[sorted(s) for s in worlds],all_eligible_collected=outcomes,real_eligible_set_known=False,actual_winner_determined=False)
    raise ValueError(t)

if __name__=='__main__':
    from pathlib import Path
    import json,hashlib
    path=Path(__file__).resolve().parent/'cloud_publication/sgk_finish_20261020/g34_network_text/cases.jsonl'
    rows=[json.loads(b) for b in path.read_bytes().splitlines()]
    guard=next(r for r in rows if r['topic']=='guard_unknown_eligible_set')
    assert guard['hints'][2]['hint']=='Đối chiếu phần luật cần hỏi với điều kiện dừng, không tự bổ sung quy tắc.'
    report=json.loads((path.parent/'hint_repair_delta.json').read_text('utf-8'))
    assert report['final_cases_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    review('g34_network_text',report['final_cases_sha256'],independent)

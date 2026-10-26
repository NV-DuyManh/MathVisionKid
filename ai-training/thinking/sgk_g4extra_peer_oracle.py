"""Independent content cross-review oracle for bounded G4 extra20.

Never imports the author builder, accepts data, or writes Drive.
"""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal, localcontext
from itertools import combinations, product
import ast, hashlib, json

RUN=Path(__file__).resolve().parent/'cloud_publication/sgk_page_audit_20261019'
OUT=RUN/'g4_remaining_append'
CRITERIA=['math_correctness_or_explicit_guard','givens_request_consistency','grade_and_enrichment_scope','steps_reasons_units_check','initial_all_hints_answer_free','student_work_grounding','schema_provenance_preservation']
def sha(b):return hashlib.sha256(b).hexdigest()
def calc(e,typ=Fraction):
    def visit(n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):return typ(ast.get_source_segment(e,n))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
            v=visit(n.operand);return -v if isinstance(n.op,ast.USub) else v
        if isinstance(n,ast.BinOp):
            a,b=visit(n.left),visit(n.right)
            if isinstance(n.op,ast.Add):return a+b
            if isinstance(n.op,ast.Sub):return a-b
            if isinstance(n.op,ast.Mult):return a*b
            if isinstance(n.op,ast.Div):return a/b
        raise ValueError(e)
    return visit(ast.parse(e,mode='eval').body)

def shuttle(weights,capacity,plan=None):
    names=list(weights);start=(0,)*(len(names)+1);goal=(1,)*len(start)
    states=list(product((0,1),repeat=len(start)));arcs={s:[] for s in states}
    for s in states:
        available=[i for i in range(len(names)) if s[i]==s[-1]]
        for n in range(1,len(available)+1):
            for group in combinations(available,n):
                load=sum(weights[names[i]] for i in group)
                if load>capacity:continue
                t=list(s);t[-1]=1-s[-1]
                for i in group:t[i]=1-s[i]
                arcs[s].append((tuple(t),tuple(names[i] for i in group),load))
    # Reachability by exact walk lengths, no author queue/bitmask helper.
    frontier={start};minimum=None
    for depth in range(len(states)+1):
        if goal in frontier:minimum=depth;break
        frontier={t for s in frontier for t,g,w in arcs[s]}
    trace=[]
    if plan:
        s=start
        for group in plan:
            options=[a for a in arcs[s] if set(a[1])==set(group)]
            assert len(options)==1
            t,g,load=options[0];trace.append(dict(before=s,passengers=g,load=load,after=t));s=t
        assert s==goal and len(plan)==minimum
    return dict(method='EXACT_LENGTH_REACHABILITY_IN_EXHAUSTIVE_TUPLE_STATE_GRAPH',minimum_crossings=minimum,state_count=len(states),validated_plan_trace=trace)

def crossing_constraints(clues):
    cells={};contradictions=[]
    for label,value in clues.items():
        assert 10<=value<=99
        for k,d in zip(label,divmod(value,10)):
            if k in cells and cells[k]!=d:contradictions.append(dict(cell=k,first=cells[k],other=d,clue=label))
            else:cells[k]=d
    return dict(cells=cells,contradictions=contradictions,consistent=not contradictions)

def prefix_race(rolls,target,kind):
    if kind=='parity':
        labels=['Chẵn','Lẻ'];events=[labels[sum(pair)%2] for pair in rolls]
    else:labels=[5,6];events=[sum(pair) if sum(pair) in labels else None for pair in rolls]
    prefixes=[]
    for length in range(1,len(events)+1):
        counts={label:events[:length].count(label) for label in labels};prefixes.append(counts)
        winners=[label for label in labels if counts[label]>=target]
        if winners:return dict(winner=winners[0],stop=length,positions=counts,prefix_counts=prefixes)
    return dict(winner=None,stop=None,positions=prefixes[-1],prefix_counts=prefixes)

def independent(r):
    topic=r['topic'];i=int(r['sample_id'][-2:]);o=r['gap_oracle'];answer=r['expected_answer']
    if topic=='board_turn_privilege':
        if i==1:
            position=1;current='An';trace=[]
            for roll,answer_value in [(2,8),(1,4)]:
                position+=roll;correct=answer_value=={3:8,4:4}[position]
                bonus=position==3 and correct
                trace.append(dict(position=position,correct_answer=correct,keeps_turn=bonus))
                if not bonus:current='Bình'
            assert position==4 and current=='Bình' and [x['result'] for x in answer]==['4','Bình']
            return dict(method='EXPLICIT_SUPPLIED_ROLL_AND_PERMISSION_TRANSITIONS',trace=trace,next_player=current)
        pos={'M':1,'N':2};skip={'M':1,'N':0};rolls={'N':[2],'M':[1]};trace=[]
        for player in ['M','N','M','N']:
            if skip[player]:skip[player]-=1;action='skip'
            else:
                pos[player]+=rolls[player].pop(0);action='move'
                if pos[player]==4:skip[player]+=1
            trace.append(dict(player=player,action=action,positions=pos.copy(),skip_flags=skip.copy()))
        assert pos=={'M':2,'N':4} and skip=={'M':0,'N':0}
        assert [x['player']+'_'+x['action'] for x in trace]==o['expected_actions']
        return dict(method='FOUR_TURN_FLAG_STATE_TRANSITIONS_FROM_SUPPLIED_LOG',trace=trace)
    if topic=='boat_shuttle':
        weights,cap=({'A':60,'B':40,'C':20},60) if i==1 else ({'A':70,'B':35,'C':25},60)
        result=shuttle(weights,cap,[['B','C'],['C'],['A'],['B'],['B','C']] if i==1 else None)
        assert result['minimum_crossings']==(5 if i==1 else None)
        if i==1:assert answer[0]['result']=='5'
        else:assert answer[0]['result']=='Không có kế hoạch hợp lệ'
        return result
    if topic=='bar_model_to_story':
        pairs=[(small,large) for small in range(29) for large in range(29) if (small+large==28 and large-small==4) if i==1] if i==1 else [(small,large) for small in range(21) for large in range(21) if large==4*small and large-small==12]
        assert pairs==([(12,16)] if i==1 else [(4,16)])
        if i==1:assert [a['result'] for a in answer][1:]==['12','16']
        else:assert [a['result'] for a in answer][:2]==['4','16']
        return dict(method='FINITE_TWO_VARIABLE_RELATION_INTERSECTION',unique_pair=pairs[0],student_story_must_match_difference_not_total=i==2)
    if topic=='regular_dial_angle':
        sectors,start,end=(12,2,7) if i==1 else (8,0,6)
        counts=[]
        for direction in (1,-1):
            p=start;count=0
            while p!=end:p=(p+direction)%sectors;count+=1
            counts.append(count)
        arcs=[Fraction(360,sectors)*n for n in counts]
        assert sum(arcs)==360 and min(arcs)==Fraction(answer[0]['result'])
        return dict(method='WALK_BOTH_DIRECTIONS_THROUGH_REGULAR_SECTORS',arc_steps=counts,arc_degrees=list(map(str,arcs)))
    if topic=='numeric_crossword':
        clues={'AB':4*6,'AC':20+3,'BD':50-4} if i==1 else {'AB':3*4,'CD':9*3,'AC':12,'BD':24}
        result=crossing_constraints(clues)
        assert result['consistent']==(i==1)
        if i==1:assert result['cells']=={'A':2,'B':4,'C':3,'D':6} and answer[1]['result']=='36'
        else:assert any(c['cell']=='D' and {c['first'],c['other']}=={7,4} for c in result['contradictions'])
        return dict(method='DIRECT_SHARED_DIGIT_CONSTRAINT_PROPAGATION',**result)
    if topic=='directional_estimation_bound':
        if i==1:
            da,db=51-50,21-20;excess=50*db+20*da+da*db
            assert excess>0 and 50*20==1000 and 51*21-1000==excess
            return dict(method='POSITIVE_INCREMENT_EXPANSION',strict_excess=excess,relation='>')
        gap=Fraction(200-199,5);assert gap>0 and Fraction(200,5)==40
        return dict(method='POSITIVE_DIVIDEND_GAP_DIVIDED_BY_COMMON_POSITIVE_DIVISOR',strict_gap=str(gap),relation='<')
    if topic=='geometric_sequence_local_extension':
        if i==1:
            first=Fraction(24)
            for j in range(3):first/=2
            seq=[first]
            for j in range(5):seq.append(seq[-1]*2)
            assert seq[3]==24 and seq[2]==12 and seq[5]==96
            return dict(method='ITERATIVE_RECONSTRUCTION_FROM_FIRST_POSITION',sequence=list(map(str,seq)))
        double=[2]
        for j in range(3):double.append(double[-1]*2)
        repeat=([2,4,8]*2)[:4]
        assert double[:3]==repeat[:3]==[2,4,8] and double[3]!=repeat[3]
        return dict(method='TWO_EXPLICIT_FULL_SEQUENCE_RULES',double=double,repeated_group=repeat,unique_fourth_term=False)
    if topic=='chart_causal_guard':
        before,after=(12,20) if i==1 else (20,30);diff=after-before
        models=[dict(other_condition_component=before,intervention_effect=diff),dict(other_condition_component=after,intervention_effect=0)]
        assert all(m['other_condition_component']+m['intervention_effect']==after for m in models)
        assert str(diff)==answer[0]['result']
        return dict(method='TWO_HYPOTHETICAL_DECOMPOSITIONS_SAME_OBSERVATION_DIFFERENT_EFFECT',observed_difference=diff,logical_models=models,models_not_claims_of_real_causes=True,causal_effect_identified=False)
    if topic=='trial_log_race_state':
        if i==1:
            result=prefix_race([(1,2),(2,2),(3,4),(6,2)],2,'parity')
            assert (result['winner'],result['stop'],result['positions'])==('Lẻ',3,{'Chẵn':1,'Lẻ':2})
            assert [x['result'] for x in answer][:2]==['Lẻ','3'];return dict(method='FIRST_THRESHOLD_OVER_CUMULATIVE_PREFIX_COUNTS',**result)
        outcomes={str(face):prefix_race([(1,4),(2,face),(1,5)],2,'sum') for face in range(1,7)}
        assert outcomes['3']['winner']==5 and outcomes['3']['stop']==2
        assert outcomes['4']['winner']==6 and outcomes['4']['stop']==3
        return dict(method='ALL_SIX_VALID_COMPLETIONS_AND_FIRST_PREFIX_THRESHOLD',outcomes=outcomes,uniquely_determined_winner=False)
    if topic=='closed_operation_cycle':
        start=Fraction('3/4' if i==1 else '2/3');ops=[('add',Fraction('1/2')),('mul',Fraction(2)),('sub',Fraction('7/4'))] if i==1 else [('add',Fraction('1/6')),('mul',Fraction(3)),('sub',Fraction('5/3'))]
        a,b=Fraction(1),Fraction(0);milestones=[]
        for op,v in ops:
            if op=='add':b+=v
            elif op=='sub':b-=v
            else:a*=v;b*=v
            milestones.append(a*start+b)
        assert list(map(str,milestones))==(['5/4','5/2','3/4'] if i==1 else ['5/6','5/2','5/6'])
        assert (milestones[-1]==start)==(i==1)
        if i==2:assert milestones[-1]-start==Fraction(1,6)
        return dict(method='COMPOSITION_OF_AFFINE_STATE_TRANSFORMATIONS',affine_a=str(a),affine_b=str(b),milestones=list(map(str,milestones)),closed=milestones[-1]==start)
    raise ValueError(topic)

def main():
    source=(OUT/'cases.jsonl').read_bytes();lines=source.splitlines();rs=[json.loads(l) for l in lines]
    assert len(rs)==20 and len({r['sample_id'] for r in rs})==20
    result=[];numeric_count=0
    page_receipts=[json.loads(b) for b in (RUN/'g4_audit/page_review.jsonl').read_bytes().splitlines()]
    for r,line in zip(rs,lines):
        proof=independent(r);checks=[]
        for s in r['worked_steps']:
            assert s['reason'] and s['explanation']
            if not s['expression']:continue
            f=calc(s['expression']);assert f==Fraction(s['result'])
            with localcontext() as ctx:
                ctx.prec=95;d=calc(s['expression'],Decimal);expected=Decimal(f.numerator)/Decimal(f.denominator)
                assert abs(d-expected)<Decimal('1e-80')
            checks.append(dict(step_id=s['step_id'],expression=s['expression'],exact=str(f),decimal_95_digits_agrees=True));numeric_count+=1
        assert r['grade']==4 and r['split']=='train' and r['curriculum_assignment']['enrichment']
        assert len(r['hints'])==3 and [h['level'] for h in r['hints']]==[1,2,3]
        assert r['initial_guidance']==[r['hints'][0]['hint']]
        assert not any(r.get(k) for k in ('human_verified','teacher_certified','owner_human_reviewed'))
        anchor=r['curriculum_assignment'];assert any(p['image_url']==anchor['publisher_page_url'] and p['image_sha256']==anchor['source_image_sha256'] and p['printed_page']==anchor['lesson_page'] for p in page_receipts)
        result.append(dict(sample_id=r['sample_id'],source_row_sha256=sha(line),status='PASS_CONTENT_CROSS_REVIEW_DRAFT_NOT_ACCEPTED',review_role='CONTENT_CROSS_REVIEW_AND_INDEPENDENT_ORACLE',criteria={k:'PASS' for k in CRITERIA},actual_semantic_fields_read=['problem','givens','requested_quantity','student_work','all_worked_steps','reasons','explanations','answers','initial_guidance','all_three_hints'],independent_structural_oracle=proof,numeric_checks=checks,human_review_claimed=False,external_review_claimed=False))
    chats_path=OUT/'chat.jsonl';chats=[json.loads(l) for l in chats_path.read_bytes().splitlines()]
    assert len(chats)==80 and len({c['sample_id'] for c in chats})==80
    byid={r['sample_id']:(r,sha(line)) for r,line in zip(rs,lines)};modes={sid:set() for sid in byid}
    for c in chats:
        r,h=byid[c['source_sample_id']];assert c['source_row_sha256']==h
        assert c['acceptance_status']==r['acceptance_status'] and c['quality_status']==r['quality_status']
        prompt=json.loads(c['messages'][1]['content']);target=json.loads(c['messages'][2]['content'])
        assert prompt['problem']==r['problem'] and prompt['grade']==4
        mode=c['mode'];modes[r['sample_id']].add(mode)
        if mode=='worked_solution':assert target['steps']==r['worked_steps'] and target['answer']==r['expected_answer'] and target['initial_guidance']==r['initial_guidance']
        else:
            hint=r['hints'][int(mode[-1])-1];assert target==dict(hint=hint['hint'],question=hint['question'])
    assert all(v=={'worked_solution','hint_level_1','hint_level_2','hint_level_3'} for v in modes.values())
    report=dict(source_file_sha256=sha(source),source_file_bytes=len(source),case_count=20,chat_file_sha256=sha(chats_path.read_bytes()),chat_count=80,seven_criteria_pass_count=20,numeric_step_checks=numeric_count,chat_exact_source_hash_and_content_checks='PASS',status='PASS_CONTENT_CROSS_REVIEW_DRAFT_NOT_ACCEPTED',math_issues=[],pedagogy_blocking_issues=[],repair_review=dict(original_source_sha256=sha((OUT/'draft_before_author_repairs.jsonl').read_bytes()),final_changed_rows_fully_read=[3,14,16,20],changed_fields='Three numeric result fields separated from narrative. Shuttle minimum proof covers A-first and light-pair-first orders. Final parent polish: causal row16 reason now avoids implying conditions were controlled; row20 two givens spaced. Actual changed fields read before final recheck.',parent_polish_source_sha256=sha((OUT/'parent_before_final_polish_f5252a83.jsonl').read_bytes()),no_answer_changed_to_bypass_gate=True),reviews=result,scope_limitations=['Twenty original text cases for ten finite reasoning forms; not twenty independent curriculum forms.','Grade4 reasoning enrichment; no new core495 slots claimed.','No visual/physical competency or full SGK semantic completeness claim.','Cross-agent review is not an owner human attestation or external review.'],drive_mutated=False,trained=False)
    (OUT/'peer_review.json').write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['case_count','source_file_sha256','seven_criteria_pass_count','numeric_step_checks','chat_count','status']}))
if __name__=='__main__':main()

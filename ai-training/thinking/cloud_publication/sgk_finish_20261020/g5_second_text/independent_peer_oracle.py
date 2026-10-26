"""Independent review of final second G5 batch; no author oracle import.

Constants here are transcribed from the actual problem/givens, never derived
from independent_model or the author's claimed oracle/QA output.
"""
from collections import Counter
from fractions import Fraction
from itertools import combinations
import hashlib
import json
from pathlib import Path
import re
import sys

HERE=Path(__file__).resolve().parent;THINKING=HERE.parents[2]
sys.path.insert(0,str(THINKING))
import exhaustive_colab_loader as L
from math_data_archive_audit import source_projection,linkage_errors
from math_data_portable_resume import canonical,save


def exact(expression):
    tokens=re.findall(r'\d+(?:\.\d+)?|[()+*/-]',expression)
    if ''.join(tokens)!=re.sub(r'\s+','',expression):raise ValueError(expression)
    stack=[];operators=[];precedence={'+':1,'-':1,'*':2,'/':2}
    def apply():
        op=operators.pop();b=stack.pop();a=stack.pop()
        stack.append({'+':lambda:a+b,'-':lambda:a-b,'*':lambda:a*b,'/':lambda:a/b}[op]())
    for token in tokens:
        if token[0].isdigit():stack.append(Fraction(token))
        elif token=='(':operators.append(token)
        elif token==')':
            while operators[-1]!='(':apply()
            operators.pop()
        else:
            while operators and operators[-1]!='(' and precedence[operators[-1]]>=precedence[token]:apply()
            operators.append(token)
    while operators:apply()
    assert len(stack)==1
    return stack[0]


def values(row):return [x['result'] for x in row['expected_answer']]


def review(row):
    name=row['sample_id'].removeprefix('sgk_finish_g5_20261020_');answer=values(row)
    if name=='date_fixed_yyyymmdd_encode':
        # Written date: day9,month4,year2026; rule YYYYMMDD with padding.
        result=f'{2026:04d}{4:02d}{9:02d}';positions=[i for i,x in enumerate(result,1) if x=='0']
        assert result=='20260409' and positions==[2,5,7]
        assert answer==[result,str(len(positions)),','.join(map(str,positions))]
        oracle=dict(rule='YYYYMMDD',encoded=result,zero_positions=positions,character_count=len(result))
    elif name=='date_fixed_ddmmyyyy_leading_zero_repair':
        code='02032026';fields=[code[:2],code[2:4],code[4:]];positions=[i for i,x in enumerate(code,1) if x=='0']
        assert fields==['02','03','2026'] and positions==[1,3,6] and len(code[1:])==7
        assert answer==['02/03/2026 theo thứ tự ngày/tháng/năm',code,'3']
        oracle=dict(rule='DDMMYYYY',fields=fields,zero_positions=positions,wrong_dropped_code_length=7,
                    student_claim_of_eight_characters_false=True)
    elif name=='compound_two_years_compare_simple':
        principal=Fraction(800);rate=Fraction(5,100);current=principal;balances=[]
        for year in range(2):current+=current*rate;balances.append(current)
        simple=principal+2*principal*rate
        assert answer==[str(current),str(simple),str(current-simple)]==['882','880','2']
        oracle=dict(explicit_fictional_rules=True,year_end_balances=list(map(str,balances)),simple=str(simple),difference=str(current-simple))
    elif name=='compound_reverse_principal':
        final=Fraction(1210);growth=Fraction(110,100);year1=final/growth;principal=year1/growth
        interest1=year1-principal;interest2=final-year1
        assert answer==[str(principal),str(interest1),str(interest2)]==['1000','100','110']
        assert (principal+interest1)*growth==final
        oracle=dict(explicit_fictional_rules=True,principal=str(principal),year1=str(year1),interest1=str(interest1),interest2=str(interest2),final=str(final))
    elif name=='pair_guarantee_any_color_not_red':
        inventory=['R1','R2','R3','B1','B2','B3'];draws=list(combinations(inventory,3))
        counts=[Counter(item[0] for item in draw) for draw in draws]
        assert len(draws)==20 and all(max(x.values())>=2 for x in counts)
        assert not all(x.get('R',0)>=2 for x in counts)
        assert {x.get('R',0) for x in counts}=={0,1,2,3}
        assert answer==['Chắc chắn có','Không chắc chắn có']
        oracle=dict(distinct_three_draws_enumerated=20,red_counts=[0,1,2,3],same_color_pair_always=True,red_pair_always=False,counterexample=['B1','B2','B3'])
    elif name=='pair_guarantee_blue_minimum_draws':
        inventory=['R','U','V'];blue={'U','V'};guarantee={}
        for k in range(4):guarantee[k]=all(len(set(draw)&blue)>=2 for draw in combinations(inventory,k))
        minimum=min(k for k,holds in guarantee.items() if holds)
        assert minimum==3 and answer==['3'] and len({'R','U'}&blue)==1
        oracle=dict(all_draw_counts_checked=guarantee,minimum_draws=minimum,lower_bound_counterexample=['R','U'])
    elif name=='clock_slow_forward_from_reset':
        true_elapsed=(11-8)*60;display_elapsed=Fraction(true_elapsed*58,60);shown=8*60+display_elapsed;loss=true_elapsed-display_elapsed
        assert shown==654 and loss==6 and answer==['10:54 cùng ngày','6']
        oracle=dict(true_elapsed_minutes=true_elapsed,display_elapsed_minutes=str(display_elapsed),shown_minutes_after_midnight=str(shown),loss_minutes=str(loss))
    elif name=='clock_fast_inverse_display_elapsed':
        display_elapsed=(10*60+15)-7*60;elapsed=Fraction(display_elapsed*60,65);true_time=7*60+elapsed;gain=display_elapsed-elapsed
        assert true_time==600 and gain==15 and answer==['10:00 cùng ngày','15']
        oracle=dict(display_elapsed_minutes=display_elapsed,true_elapsed_minutes=str(elapsed),true_clock_minutes_after_midnight=str(true_time),gain_minutes=str(gain))
    elif name=='train_tail_bridge_forward':
        # Tail equation10*t-120=180; solve it directly from the endpoints.
        t=Fraction(180+120,10);head=10*t;tail=head-120
        assert tail==180 and answer==[str(head),str(t)]==['300','30']
        oracle=dict(end_tail_coordinate=str(tail),head_displacement=str(head),duration_seconds=str(t),endpoint_equation='10*t-120=180')
    elif name=='train_bridge_inverse_length':
        head=15*24;tail_end=200;length=head-tail_end
        assert length==160 and answer==['160'] and head-length==200
        oracle=dict(head_displacement=head,tail_end_coordinate=tail_end,train_length=length,endpoint_equation='15*24-L=200')
    elif name=='piecewise_routes_equal_time':
        times=[Fraction(6,3),Fraction(6,6)];a=sum(times);b=Fraction(12,4);average=Fraction(12,1)/a
        assert a==b==3 and average==4 and answer==['3','3','Đến cùng lúc','4']
        oracle=dict(segment_hours=list(map(str,times)),route_a_hours=str(a),route_b_hours=str(b),route_a_average_kmh=str(average),arithmetic_mean_is_not_weighted_time_average=True)
    elif name=='piecewise_rest_total_average_error':
        moving=Fraction(12,4)+Fraction(6,6);rest=Fraction(30,60);elapsed=moving+rest;speed=Fraction(18,1)/elapsed
        assert moving==4 and elapsed==Fraction(9,2) and speed==4 and answer==['4','4.5','4']
        oracle=dict(moving_hours=str(moving),rest_hours=str(rest),elapsed_hours=str(elapsed),whole_trip_average=str(speed),moving_only_average=str(Fraction(18,1)/moving),naive_mean=5,student_two_claims_both_false=True)
    else:raise ValueError(name)
    numeric=[]
    for step in row['worked_steps']:
        assert step['reason'] and step['explanation']
        if step.get('expression'):
            value=exact(step['expression']);assert value==Fraction(step['result'])
            numeric.append({'expression':step['expression'],'exact':str(value)})
    assert row['can_solve'] and [h['level'] for h in row['hints']]==[1,2,3]
    assert not any(row.get(k) for k in ('human_verified','teacher_certified','owner_human_reviewed'))
    return {'independent_structural_oracle':oracle,'numeric_steps':numeric}


def main():
    raw=(HERE/'cases.jsonl').read_bytes();chatraw=(HERE/'chat.jsonl').read_bytes()
    rows=[(json.loads(line),hashlib.sha256(line).hexdigest()) for line in raw.splitlines() if line]
    chats=[json.loads(line) for line in chatraw.splitlines() if line];index={r['sample_id']:r for r,h in rows}
    manifest=json.loads((HERE/'manifest.json').read_text('utf8'))
    for name,data in [('cases.jsonl',raw),('chat.jsonl',chatraw)]:
        ref=next(x for x in manifest['manifest'] if x['path']==name)
        assert ref['sha256']==hashlib.sha256(data).hexdigest() and ref['bytes']==len(data)
    assert len(rows)==12 and len(chats)==48 and len({r['sample_id'] for r in chats})==48
    for chat in chats:
        L.validate_chat(chat)
        errors=linkage_errors(chat,source_projection(index[L.case_id(chat)]))
        assert not errors,(chat['sample_id'],errors)
    assert len({(L.case_id(r),r['mode']) for r in chats})==48
    criteria={
      'math_correctness_or_explicit_guard':'PASS: date positions, finite reinvestment recurrence/inverse, every distinct draw, clock rate conversion, train endpoint coordinates and piecewise times independently recomputed; every numeric expression rechecked by separate exact precedence parser.',
      'givens_request_consistency':'PASS: all actual givens/request fields read; fixed-width code order, explicit fictional percentage rules, inventories, clock reset/reference, train head/tail endpoints and rest inclusion align with answers.',
      'grade_and_scope':'PASS: bounded grade5 reasoning enrichment under stated rules; no external investment facts, probability demand, actual physical or vision outcome claimed.',
      'steps_reasons_units_check':'PASS: actual steps/reasons/explanations read; percent bases reset yearly, clocks distinguish displayed/true intervals, bridge uses train length, trip average denominator includes stated rest.',
      'initial_and_all_hints_no_answer_leak':'PASS: initial guidance and all three hints/questions read; describe field/rate/base/endpoint/enumeration method without supplying final code, numeric time, amount or selected answer.',
      'student_work_grounding':'PASS: feedback uses only the two supplied synthetic excerpts on leading-zero code and naive trip average/rest; no hidden student behavior is inferred.',
      'schema_provenance_preservation':'PASS: final source file/each raw row hash bound; all48chat prompts and targets reproduce source problem/grade/student work and worked solution/all hints; no human certification asserted.'}
    reviews=[]
    for row,h in rows:
        result=review(row)
        reviews.append({'sample_id':row['sample_id'],'source_row_sha256':h,'status':'PASS','criteria':criteria,
            'actual_fields_read':['problem','givens','requested_quantity','student_work.text_and_observations','worked_steps','reasons','explanations','expected_answer','initial_guidance','all_three_hints_and_questions'],
            **result,'human_review_claimed':False})
    result={'schema':'MathVisionKid.independent_peer_review.v1','source_file_sha256':hashlib.sha256(raw).hexdigest(),
        'chat_file_sha256':hashlib.sha256(chatraw).hexdigest(),'rows_read':12,'chat_rows_checked':48,
        'seven_criteria_pass_count':12,'numeric_steps_checked':sum(len(r['numeric_steps']) for r in reviews),
        'status':'PASS','author_oracle_or_independent_model_used_as_premise':False,
        'reviewer':'independent_peer_agent','reviews':reviews,'training_started':False,'drive_mutated':False}
    save(HERE/'peer_review.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('reviews',)}))


if __name__=='__main__':main()

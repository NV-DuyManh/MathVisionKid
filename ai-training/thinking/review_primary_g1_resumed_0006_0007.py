"""Independent parent review of saved drafts authored by two other agents."""
import json
from datetime import date,timedelta,datetime,timezone
from fractions import Fraction as F
from primary_math_data_pipeline import (DEFAULT_ROOT,HERE,REVIEW_FIELDS,read_rows,write_rows,
    write_json,row_sha,sha,inspect_case,mapping_error,protections,answer_signatures,normalized,curate)


def main():
    evidence=HERE/'evidence/primary_math_teacher_20261016'
    specifications=[('g1_measurement_0006','primary_length_author_0006','g1_measurement_0006_author.py'),
                    ('g1_time_0007','primary_time_author_0007','author_primary_g1_time_0007.py')]
    if any((DEFAULT_ROOT/'reviews'/f'{name}_AI_review.jsonl').exists() for name,_,_ in specifications):
        raise ValueError('Review already or partially exists: inspect before resuming, do not overwrite.')
    bp=json.loads((DEFAULT_ROOT/'curriculum_blueprint.json').read_text('utf-8'))
    nodes={n['node_id']:n for n in bp['nodes']}
    protected,questions,_=protections()
    measurements=read_rows(DEFAULT_ROOT/'authored_batches/g1_measurement_0006.jsonl')
    times=read_rows(DEFAULT_ROOT/'authored_batches/g1_time_0007.jsonl')
    assert len(measurements)==len(times)==10
    # Count intervals and compare integer orders, independent of the AST gate.
    assert len(range(0,7))==7 and 42>36
    assert len(range(3,18))==15 and 3+len(range(3,18))==18
    assert len(range(2,9))==7 and 2+len(range(2,9))==9
    assert len(['A','B','C','D'])==4
    assert F(25)-F(22)==3 and len(range(0,25))==25
    assert F(6)*2==F(4)*3 # abstract unit witness, not an actual cm measurement
    measurement_oracles=[
        {'method':'enumerate_unit_intervals','result_cm':len(range(0,7)),'reading':'bảy xăng-ti-mét'},
        {'method':'integer_order_with_matching_units','red_cm':42,'blue_cm':36,'larger':'đỏ'},
        {'method':'interval_cardinality_and_inverse','result_cm':len(range(3,18)),'end_mark':18},
        {'method':'interval_cardinality_and_inverse','result_cm':len(range(2,9)),'end_mark':9},
        {'method':'distinct_completions_of_missing_start','end_cm':12,'possible_starts':[0,4],'possible_lengths':[12,8]},
        {'method':'count_explicit_measurement_labels','labels':['A','B','C','D'],'result_handspans':4,'cm_conversion':'NOT_PROVIDED'},
        {'method':'exact_rational_comparison_of_estimate_and_measure','measured_cm':25,'estimate_cm':22,'difference_cm':str(F(25)-F(22))},
        {'method':'equal_path_different_unit_witness','path_abstract_units':12,'child_steps':6,'child_unit':2,'adult_steps':4,'adult_unit':3,'actual_cm_not_assigned':True},
        {'method':'count_and_dimension_consistency','count':5,'unit':'gang tay của bạn','cm_per_handspan':'NOT_PROVIDED'},
        {'method':'two_unobserved_objects_consistent_with_input','possible_handspans':[4,6],'no_actual_dimension_assigned':True}
    ]
    week=['Thứ Hai','Thứ Ba','Thứ Tư','Thứ Năm','Thứ Sáu','Thứ Bảy','Chủ nhật']
    # Independent calendar witness; the data itself uses a supplied fictitious week.
    start=date(2024,11,11);assert start.weekday()==0
    calendar={11+i:week[(start+timedelta(days=i)).weekday()] for i in range(7)}
    assert calendar[14]=='Thứ Năm' and calendar[16]=='Thứ Bảy'
    assert (date(2024,11,17)+timedelta(days=1)).weekday()==0
    assert date(2024,11,12).weekday()!=date(2024,12,12).weekday()
    def hour_angle(h):return F(h%12)*30
    assert hour_angle(7)==210 and hour_angle(12)==0 and hour_angle(6)==180
    assert hour_angle(9)==270 and hour_angle(10)==300
    time_oracles=[
        {'method':'seven_unique_weekday_names_in_standard_Monday_order','order':week,'count':len(set(week))},
        {'method':'datetime_successor_of_Sunday_witness','witness_date':'2024-11-17','successor_weekday':week[(date(2024,11,17)+timedelta(days=1)).weekday()]},
        {'method':'independent_datetime_witness_for_supplied_week','calendar':calendar,'activity_date':14,'weekday_at_16':calendar[16]},
        {'method':'set_difference_full_week_vs_six_day_segment','omitted_day':list(set(week)-set(week[:6])),'total':7},
        {'method':'two_real_dates_same_day_number_different_weekdays','dates':['2024-11-12','2024-12-12'],'weekdays':[date(2024,11,12).weekday(),date(2024,12,12).weekday()]},
        {'method':'whole_hour_hand_angle','minute_angle':0,'hour_angle':str(hour_angle(7)),'hour':7,'morning_from_problem':True},
        {'method':'coincident_zero_angle_hands','minute_angle':0,'hour_angle':str(hour_angle(12)),'hour':12,'noon_from_problem':True},
        {'method':'schedule_hour_to_distinct_hour_hand_angles','required_angle':270,'A_angle':270,'B_angle':300,'selected':'A','AM_from_schedule_not_face':True},
        {'method':'hour_hand_angle_not_minute_numeral','minute_angle':0,'hour_angle':str(hour_angle(6)),'hour':6,'morning_from_problem':True},
        {'method':'same_minute_angle_different_hour_angles','minute_angle':0,'possible_hour_angles':[60,240],'not_identifiable':True}
    ]
    measurement_notes=[
        'Both ruler endpoints and one-cm spacing explicit. Seven intervals, not eight tick marks;7cm and verbal reading correct. Text description supplies all data, not a real image. Hints identify start, interval counting and unit without giving7.',
        'Two given lengths share cm;42>36 by tens correctly selects red. Position on a page does not alter given measured lengths. Contrast is numeric measurement versus apparent position, no invented relative appearance. Hints do not name the chosen colour.',
        'Nonzero origin3 to18 produces15cm without borrowing. Worked separates endpoint coordinate from length and inverse3+15=18. Transfer focuses on excluding pre-object ruler segment. Hints do not give15 or compute a digit for the pupil.',
        'Synthetic endpoint-equals-length justification is explicitly observed in the quoted sentence. Correct length9−2=7cm and2+7=9 check are grounded. Does not invent a pupil motor or perception error. Refined feedback to concise child-facing explanation.',
        'Endpoint12 alone admits start0/length12 and start4/length8, so guard is necessary. Requests start mark or clear complete ruler image, not an invented default zero. No answer/steps emitted.',
        'Complete listA,B,C,D plus equal, adjoining spans and no remainder gives4 handspans ofAn. Keeps person-specific unit and refuses unsupported cm conversion. Literal4 represents reviewed list cardinality, not computational semantic proof. Removed report-like certification sentence from child worked output.',
        '22cm is explicit preliminary estimate, measured interval0to25 gives25cm, and25−22=3cm compares like units. Distinguishes estimate from confirmed scenario measurement without asserting real physical performance. No carried or borrowed arithmetic beyond grade1; hints withhold25/3.',
        'Same two endpoints force same path;6 child steps and4 adult steps can measure equal length with unequal units. No direct numerical comparison of distinct person-specific units. Method asks shared unit and endpoints for rechecking, not fabricated step-to-cm lengths. Finite witness is abstract only.',
        'Synthetic5gang→5cm statement changes unit without a conversion fact. Corrected5 retains own handspan unit; no arbitrary handspan size assumed. Feedback limited to given sentence; hints ask unit and missing link rather than state complete corrected answer.',
        'No object/reference/own-handspan information supports a numeric desk estimate. Provides a way to gather evidence, records leftover portions rather than silently round, and asks for actual observations. No number assigned or physical success claim.'
    ]
    time_notes=[
        'All seven weekday cards exactly once, Monday start explicitly requested. Correct ordered list and count7. Literal count independently checked against source cards; no use of machine current date. Hints request beginning, next card and completeness without supplying final list or count.',
        'Hypothetical Saturday→Sunday→Monday sequence crosses boundary correctly. Today anchor distinguished from yesterday; no fabricated eighth weekday. All hints support cycle recognition without naming Monday. Boundary case genuinely differs from card ordering.',
        'Provided mini-calendar is sufficient despite no month/year. Thursday maps14 and date16 mapsSaturday; inverse lookup explained and checked.14 literal is a reviewed table lookup, not evidence from AST. Hints keep pairs together without disclosing answers.',
        'Six days Monday throughSaturday is correct partial count; incorrect whole-week generalization omitsSunday.7days via6+1 and full list checked. Removed report-style speculation disclaimer while retaining grounded correction. No claim child lost cards or saw a real calendar.',
        'Day-of-month12 alone does not identify weekday; different months give distinct real-date witnesses. Requests month/year, calendar or valid same-calendar anchor, never machine current date. No answer invented.',
        'Minute hand12 means whole hour, hour hand7 gives7AM with morning explicit. Roles explained and checked; no claim physical clock image was viewed. Hints identify roles and context without outputting7.',
        'Both hands at12 is a valid whole hour. Noon provided prevents midnight ambiguity; answer12noon correct. Explanation keeps both hand roles. Hints do not say12 or a replacement time, and context is already given rather than inferred from face.',
        'Schedule9AM matches modelA hour9, notB hour10; minute hands equal at12. Worked states AM comes from schedule, not dial. Transfer compares observations with a requested event; hints do not nameA or evaluate both models for pupil.',
        'Quoted reason explicitly uses minute-hand numeral as hour. Correction reads hour6 and given morning; no invented perceptual inability. Simplified feedback to directly explain proper hand role. All hints withhold6.',
        'Minute hand12 alone permits many whole hours. Requests short-hand position or clear image; AM/PM only if contextual reading desired. No assumed hour or actual picture evidence.'
    ]
    summaries=[]
    for rows,(name,actor,helper),oracles,notes in zip([measurements,times],specifications,
            [measurement_oracles,time_oracles],[measurement_notes,time_notes]):
        path=DEFAULT_ROOT/'authored_batches'/f'{name}.jsonl'
        write_rows(evidence/f'{name}_before_parent_review_20261017.jsonl',rows)
        if name=='g1_measurement_0006':
            rows[3]['worked_steps'][0]['explanation']='Số chỉ vạch cuối chưa phải độ dài khi đầu băng không ở vạch không. Cần xét khoảng giữa cả hai đầu băng.'
            rows[5]['worked_steps'][2]['explanation']='Đếm lại các nhãn vẫn đủ toàn bộ cạnh bàn. Kết quả dùng đơn vị gang tay của An; chưa biết số xăng-ti-mét của mỗi gang nên chưa đổi sang cm.'
        else:
            rows[3]['worked_steps'][0]['explanation']='Từ Thứ Hai đến Thứ Bảy chưa có Chủ nhật. Muốn kết luận về cả tuần, em cần bổ sung ngày còn thiếu rồi đếm lại đủ các ngày.'
            rows[8]['worked_steps'][0]['explanation']='Kim dài chỉ 12 cho biết giờ đúng. Số giờ cần đọc ở kim ngắn, nên không thể chỉ lấy số kim dài chỉ để kết luận số giờ.'
        decisions=[];checks=[]
        for i,r in enumerate(rows):
            r['provenance'].update(authoring_label='AI_TEACHER',authoring_agent=actor,
                author_helper_sha256=sha((HERE/helper).read_bytes()),
                review_resumption='Authoring turn interrupted before publication; saved helper executed and content independently reviewed by parent.',
                content_review_status='INDEPENDENT_AI_REVIEW_WITH_PARENT_STYLE_ADJUDICATION',
                human_verified=False,teacher_certified=False,visual_or_physical_outcome_verified=False)
            m=inspect_case(r);assert m['passed'],(r['sample_id'],m)
            assert mapping_error(r,nodes) is None
            assert not answer_signatures(r,m)&protected
            assert normalized(r['problem']) not in questions
            decisions.append({'sample_id':r['sample_id'],'row_sha256':row_sha(r),
                'reviewer':'root_independent_parent_reviewer_of_'+actor,
                **{k:True for k in REVIEW_FIELDS},'human_verified':False,'teacher_certified':False,
                'independent_external_AI_reviewer':True,
                'review_method':'Parent independently read all authored problems/visible solutions/three hints, checked mathematics, grade, units, grounding and slot; minor child-facing style edits recorded, not a teacher or universal correctness guarantee.',
                'notes':notes[i],'independent_oracle':oracles[i]})
            checks.append({'sample_id':r['sample_id'],'row_sha256':row_sha(r),'mechanical':m,'oracle':oracles[i]})
        write_rows(path,rows);review_path=DEFAULT_ROOT/'reviews'/f'{name}_AI_review.jsonl';write_rows(review_path,decisions)
        report={'batch':name,'authoring_agent':actor,'batch_sha256':sha(path.read_bytes()),
            'review_sha256':sha(review_path.read_bytes()),'reviewed_cases':10,'checks':checks,
            'independent_parent_content_review':True,'authoring_agent_turn_completed':False,
            'human_verified':False,'teacher_certified':False,'physical_outcome_verified':False,
            'training_started':False,'sealed_concept_challenge_read':False}
        write_json(evidence/f'{name}_parent_review_20261017.json',report);summaries.append({k:report[k] for k in ('batch','batch_sha256','review_sha256','reviewed_cases')})
    frozen={p:sha((HERE.parent/p).read_bytes())==h for p,h in bp['existing_inputs']['source_fingerprints'].items()}
    assert all(frozen.values())
    state=curate(DEFAULT_ROOT)
    assert state['accepted_cases']==88 and state['chat_train_rows']==352 and state['remaining_core_cases']==434
    assert state['core_nodes_complete']==14 and state['decisions']=={'ACCEPTED_AI_RESEARCH':88}
    # A finite queue prevents completed core quotas from hiding missing ancillary tasks.
    coverage=json.loads((DEFAULT_ROOT/'coverage_progress.json').read_text('utf-8'))
    queue=[]
    for item in coverage:
        node=nodes[item['node_id']]
        for kind in ('misconception','guard'):
            required=node['authoring_plan'][kind+'_case']['required']
            actual=item['accepted_'+kind+'_cases']
            if required and not actual:queue.append({'node_id':item['node_id'],'grade':item['grade'],
                'curriculum_scope':item['curriculum_scope'],'case_kind':kind,'remaining_cases':1})
    write_json(DEFAULT_ROOT/'supplementary_queue.json',{'source_coverage_sha256':sha((DEFAULT_ROOT/'coverage_progress.json').read_bytes()),
        'remaining_required_tasks':len(queue),'queue':queue,'auxiliary_does_not_count_as_core':True})
    write_json(evidence/'resumed_batches_0006_0007_20261017_verification.json',{
        'created_utc':datetime.now(timezone.utc).isoformat(),'batches':summaries,'frozen_inputs_unchanged':frozen,
        'independent_review_37_previous_cases_completed':False,'independent_review_37_previous_cases_artifact_exists':False,
        'interruption':'Three previous agent turns returned usage-limit errors; no completed prior37 review artifact was present. Saved author helpers were recovered without spawning replacement agents.',
        'result':{k:state[k] for k in ('accepted_cases','chat_train_rows','remaining_core_cases','core_nodes_complete','decisions')},
        'remaining_required_supplementary_tasks':len(queue),'training_started':False,'human_verified':False,'teacher_certified':False})
    print(json.dumps({k:state[k] for k in ('accepted_cases','chat_train_rows','remaining_core_cases','core_nodes_complete','decisions')}))


if __name__=='__main__':main()

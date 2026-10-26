"""Eight original teaching cases for distinct outstanding grade-one slots."""
from datetime import datetime, timezone
from pathlib import Path
import json
from primary_math_data_pipeline import (DEFAULT_ROOT, HERE, REVIEW_FIELDS, answer_signatures,
    curate, inspect_case, mapping_error, normalized, protections, row_sha, sha, write_json, write_rows)
import teacher_math_data_v4 as v4


def teaching_step(title, reason, expression, result, unit, explanation):
    return dict(title=title, reason=reason, expression=expression, result=str(result), unit=unit, explanation=explanation)


def main():
    root = DEFAULT_ROOT; evidence = HERE/'evidence'/'primary_math_teacher_20261016'
    destination = root/'authored_batches'/'g1_foundations_0002.jsonl'
    review_path = root/'reviews'/'g1_foundations_0002_AI_review.jsonl'
    if destination.exists() or review_path.exists():
        if not (destination.exists() and review_path.exists()): raise ValueError('Partial batch; inspect before resuming')
        print(json.dumps({'already_authored': True})); return
    blueprint_path = root/'curriculum_blueprint.json'
    blueprint = json.loads(blueprint_path.read_text(encoding='utf-8'))
    nodes = {n['node_id']:n for n in blueprint['nodes']}
    cases=[]; oracles={}; review_notes={}

    def add(suffix, node_id, slot_name, problem, givens, steps, answers, initial, hints, canonical, oracle, note):
        node=nodes[node_id]; slot=next(s for s in node['authoring_plan']['core_cases'] if s['case_slot']==slot_name)
        sample_id='primary_20261016_g1_foundations_0002_'+suffix
        for i,s in enumerate(steps): s['step_id']='s'+str(i)
        row={'sample_id':sample_id,'split':'train','case_group_id':sample_id,'grade':1,'topic':canonical['family'],
             'problem':problem,'givens':givens,'requested_quantity':'; '.join(a['quantity'] for a in answers),
             'student_work':None,'initial_guidance':initial,
             'hints':[{'level':i+1,'hint':h[0],'question':h[1]} for i,h in enumerate(hints)],
             'worked_steps':steps,'expected_answer':answers,'canonical_case':canonical,
             'curriculum_assignment':{'node_id':node_id,'curriculum_scope':node['curriculum_scope'],'case_kind':'core',
                 **{k:slot[k] for k in ('case_slot','context_variant','method_variant')}},
             'provenance':{'authoring_method':'original_AI_teacher','human_verified':False,'teacher_certified':False,
                 'curriculum_node_id':node_id,'source_kind':'original_explicit_text_teacher_case',
                 'source_evidence':node['source_evidence'],'blueprint_sha256':sha(blueprint_path.read_bytes()),
                 'benchmark_status':'TRAINING_ONLY_NOT_GOLD','real_observation_claim':False},
             'quality_flags':{'app_plan_draft_compatible':False,'app_mapping_status':'NEUTRAL_TEACHER_SCHEMA_REQUIRES_ADAPTER',
                 'full_worked_solution_requires_explicit_request':True,'three_hint_levels_answer_free':True}}
        cases.append(row);oracles[sample_id]=oracle;review_notes[sample_id]=note

    marks=' '.join(['●']*14)
    add('count14','current_g1_natural_numbers_100','core_01',
        'Mỗi ký hiệu ● sau đây là một chấm: '+marks+'. Hãy đếm, viết số chấm bằng chữ số rồi đọc số đó.',
        [{'id':'g0','text':marks,'value':None,'unit':'chấm','role':'complete_explicit_symbol_list'}],
        [teaching_step('Đếm mỗi chấm đúng một lần','Gắn lần lượt một tên số với một chấm; số cuối cùng cho biết tổng số chấm.',
                       '14','14','chấm','Đánh dấu từ trái sang phải: một, hai, ba, bốn, năm, sáu, bảy, tám, chín, mười, mười một, mười hai, mười ba, mười bốn. Có 14 chấm.'),
         teaching_step('Viết và đọc số','Sau khi đếm, viết chữ số biểu thị lượng vừa đếm và đọc tên số.',None,'mười bốn','',
                       'Viết 14 và đọc là mười bốn. Đếm lại từ phải sang trái vẫn được 14 nếu mỗi chấm chỉ được tính một lần.')],
        [{'quantity':'Số chấm','result':'14','unit':'chấm'},{'quantity':'Cách đọc số','result':'mười bốn','unit':''}],
        ['Đề cho toàn bộ các chấm bằng ký hiệu, không cần đoán phần ngoài dòng.','Đánh dấu chấm đã đếm để tránh bỏ sót hoặc đếm lại.'],
        [('Bắt đầu ở một đầu dòng và dịch từng chấm.','Làm thế nào để biết chấm nào em đã đếm?'),
         ('Mỗi khi chuyển sang chấm chưa đếm, đọc số tiếp theo.','Tên số cuối cùng khi đếm cho em biết điều gì?'),
         ('Sau khi đếm xong, viết lượng đó bằng chữ số và đọc lại.','Nếu đếm lại theo chiều ngược, em cần giữ quy tắc nào?')],
        {'family':'explicit_symbol_count','operations':['14'],'numeric_values':[]},
        {'method':'count_actual_source_symbols','count':marks.count('●'),'reading':'mười bốn'},
        'Counted all fourteen provided symbols independently. Numeral14 and reading agree; no invented image or multiplication. Literal14 in the numeric field represents the counted cardinality, not an arithmetic proof of counting.')

    add('five_tens','current_g1_natural_numbers_100','core_03',
        'Có 5 bó que, mỗi bó có mười que, tức một chục que. Viết lượng que bằng số chục và bằng số que; giải thích hai cách viết.',
        [{'id':'g0','text':'5 bó que','value':'5','unit':'bó','role':'bundle_count'},
         {'id':'g1','text':'mỗi bó có mười que','value':'10','unit':'que/bó','role':'tens_bundle_size'}],
        [teaching_step('Đếm theo chục','Mỗi bó là một chục; đếm năm bó theo đơn vị chục.', '5','5','chục',
                       'Một chục, hai chục, ba chục, bốn chục, năm chục. Có năm chục que.'),
         teaching_step('Đổi cách biểu diễn cùng lượng','Mỗi chục gồm mười đơn vị, nên đếm tiếp từng chục bằng số đơn vị.',
                       '10+10+10+10+10','50','que','Đếm theo chục: 10, 20, 30, 40, 50. Năm chục que cũng là 50 que; lượng que không thay đổi.')],
        [{'quantity':'Lượng que tính theo chục','result':'5','unit':'chục'},{'quantity':'Lượng que tính theo đơn vị','result':'50','unit':'que'}],
        ['Giữ nguyên các que, chỉ đổi cách gọi đơn vị đếm.','Mỗi bó là một chục; có thể đếm các bó trước khi đếm từng que.'],
        [('Hãy nhìn các bó như các nhóm một chục.','Khi đếm bó, em đang đếm từng que hay từng chục?'),
         ('Đếm tiếp mỗi lần một chục thay vì mở các bó.','Một chục có bao nhiêu que theo đề?'),
         ('Viết cách đếm theo chục rồi đổi cùng lượng đó sang đơn vị que.','Vì sao hai cách viết khác đơn vị mà vẫn nói về cùng các que?')],
        {'family':'same_quantity_tens_and_units','operations':['10+10+10+10+10'],'numeric_values':['5','10']},
        {'method':'flatten_five_explicit_ten_item_bundles','tens':len([None]*5),'units':len([None for _ in range(5) for _ in range(10)])},
        'Five bundles give five tens and fifty units; repeated-addition/count-by-tens avoids teaching multiplication as a grade-one requirement. Hint never states the fifty-unit answer.')

    for suffix,a,b,slot_name,relation in [('different_tens',46,73,'core_01','different'),('same_tens',62,68,'core_02','same')]:
        larger=max(a,b)
        if relation=='different':
            explanation='46 có 4 chục, 73 có 7 chục. Bốn chục ít hơn bảy chục; không cần dùng hàng đơn vị để đổi kết luận. Số lớn hơn là 73.'
            reason='Hai số có hàng chục khác nhau; số có nhiều chục hơn lớn hơn.'
            hints=[('Xét hàng chục trước, chưa vội so hàng đơn vị.','Chữ số hàng chục nằm ở vị trí nào trong mỗi số?'),
                   ('Đọc số chục của từng thẻ.','Nếu số chục khác nhau, em cần so sánh hàng nào?'),
                   ('Dựa vào số chục để chọn số lớn hơn; hàng đơn vị chỉ xét khi hàng chục bằng nhau.','Vì sao một chữ số đơn vị lớn hơn chưa đủ quyết định cả số lớn hơn?')]
        else:
            explanation='62 và 68 đều có 6 chục. So hàng đơn vị: 2 ít hơn 8. Vì thế 62 bé hơn 68, nên chọn 68.'
            reason='Hai số có cùng số chục, nên dùng hàng đơn vị để phân biệt.'
            hints=[('Kiểm tra hai chữ số hàng chục trước.','Hai số có cùng số chục hay khác số chục?'),
                   ('Khi hàng chục bằng nhau, chuyển sang hàng đơn vị.','Em cần so sánh hai chữ số ở hàng nào tiếp theo?'),
                   ('Giữ nguyên số chục bằng nhau và chọn số có nhiều đơn vị hơn.','Lựa chọn của em có phù hợp với cách xếp hai số trên tia số không?')]
        add(suffix,'current_g1_compare_order_100',slot_name,
            f'Hai thẻ ghi số {a} và {b}. Thẻ nào ghi số lớn hơn? Giải thích bằng hàng chục và hàng đơn vị.',
            [{'id':'g0','text':str(a),'value':str(a),'unit':'','role':'first_number'},
             {'id':'g1','text':str(b),'value':str(b),'unit':'','role':'second_number'}],
            [teaching_step('So sánh theo giá trị các hàng',reason,str(larger),str(larger),'',explanation)],
            [{'quantity':'Số lớn hơn','result':str(larger),'unit':''}],
            ['Cả hai thẻ đều ghi số có hai chữ số.','So hàng chục trước; nếu bằng nhau mới so hàng đơn vị.'],hints,
            {'family':'compare_two_natural_numbers_'+relation,'operations':[str(larger)],'numeric_values':[str(a),str(b)]},
            {'method':'independent_integer_order_and_place_value_tuple','larger':max(a,b),
             'tuple_order_agrees':(divmod(a,10)<divmod(b,10))==(a<b)},
            'Read complete comparison rationale: tens dominate differing ones; equal tens require comparing ones. Numeric literal is a selected input value, not a falsely equated digit extraction.')

    values=[58,25,52,8]
    add('sort_four','current_g1_compare_order_100','core_03',
        'Xếp bốn số 58, 25, 52, 8 theo thứ tự từ bé đến lớn. Hãy kiểm tra từng cặp đứng cạnh nhau.',
        [{'id':f'g{i}','text':str(v),'value':str(v),'unit':'','role':'number_to_order'} for i,v in enumerate(values)],
        [teaching_step('Tìm số bé nhất','Số một chữ số bé hơn các số hai chữ số trong danh sách.', '8','8','',
                       'Số 8 có một chữ số; các số còn lại đều lớn hơn một chục. Đặt 8 trước.'),
         teaching_step('Xếp các số hai chữ số','So hàng chục; nếu bằng nhau thì so hàng đơn vị.',None,'25 < 52 < 58','',
                       '25 có 2 chục, đứng trước hai số có 5 chục. Giữa 52 và 58, cùng 5 chục nhưng 2 đơn vị ít hơn 8 đơn vị, nên 52 đứng trước 58.'),
         teaching_step('Viết thứ tự và kiểm lại','Đọc lại các cặp liền nhau để chắc rằng mỗi số đứng trước đều bé hơn số sau.',None,'8, 25, 52, 58','',
                       'Thứ tự là 8, 25, 52, 58. Kiểm tra: 8 < 25, 25 < 52 và 52 < 58.')],
        [{'quantity':'Dãy số từ bé đến lớn','result':'8, 25, 52, 58','unit':''}],
        ['Có đúng bốn số cần xếp; mỗi số chỉ xuất hiện một lần trong đáp án.','Chiều yêu cầu là từ bé đến lớn, nên xét số bé nhất trước.'],
        [('Phân biệt số có một chữ số với số có hai chữ số.','Số nào thuộc nhóm một chữ số trong danh sách?'),
         ('Trong nhóm hai chữ số, so hàng chục rồi mới so hàng đơn vị nếu cần.','Khi hai số có cùng số chục, em sẽ dùng hàng nào để xếp chúng?'),
         ('Sau khi xếp, đọc từng cặp liền nhau và giữ nguyên đủ bốn số của đề.','Có cặp nào đứng trước lại lớn hơn số đứng sau không?')],
        {'family':'order_four_natural_numbers','operations':[],'numeric_values':list(map(str,values))},
        {'method':'independent_sort_and_adjacent_inequalities','ordered':sorted(values),'strictly_increasing':all(a<b for a,b in zip(sorted(values),sorted(values)[1:]))},
        'All four values retained once; one-digit versus two-digit and tie-breaking within five tens both explained. Categorical order is reviewed directly; AST is not used as proof of ordering.')

    add('mental_within10','current_g1_mental_add_sub','core_01',
        'Lan có 6 hạt đậu và được cho thêm 3 hạt. Hãy nhẩm số hạt của Lan và nói cách đếm tiếp.',
        [{'id':'g0','text':'6 hạt đậu','value':'6','unit':'hạt','role':'initial_count'},
         {'id':'g1','text':'thêm 3 hạt','value':'3','unit':'hạt','role':'added_count'}],
        [teaching_step('Đếm tiếp phần được thêm','Thêm vào là gộp lượng mới với lượng đang có; không phải đếm lại từ đầu.',
                       '6+3','9','hạt','Giữ 6 trong đầu, đếm thêm ba lần: 7, 8, 9. Lan có 9 hạt; 6 + 3 = 9.')],
        [{'quantity':'Số hạt của Lan','result':'9','unit':'hạt'}],
        ['Số hạt đang có đã biết; em có thể bắt đầu từ số đó.','Mỗi hạt thêm ứng với một lần đếm tiếp.'],
        [('Giữ số đang có trong đầu thay vì đếm lại tất cả từ đầu.','Sau khi được cho thêm, số hạt tăng hay giảm?'),
         ('Đếm tiếp đúng số lần bằng số hạt được thêm.','Em làm cách nào để nhớ mình đã đếm thêm đủ số lần?'),
         ('Dừng sau khi đã đếm hết phần thêm và ghi đúng đơn vị.','Số cuối khi đếm tiếp cho em biết đại lượng nào?')],
        {'family':'mental_join_within10','operations':['6+3'],'numeric_values':['6','3']},
        {'method':'extend_concrete_six_item_list_by_three_items','count':len([None]*6+[None]*3)},
        'One-step count-on within ten, no carrying. Three actual increments reach nine; no subtraction or regrouping introduced. Hints withhold nine and the counted sequence.')

    for suffix,a,b,op,slot_name in [('round_tens_add',20,40,'+','core_02'),('round_tens_subtract',90,30,'-','core_03')]:
        result=a+b if op=='+' else a-b
        if op=='+':
            explanation='20 là 2 chục, 40 là 4 chục. Gộp được 6 chục, tức 60. Vậy 20 + 40 = 60.'
            reason='Cộng hai số tròn chục bằng cách cộng số chục, rồi gọi lại theo đơn vị.'
            hints=[('Hai số đều không có đơn vị rời.','Em có thể dùng chục làm đơn vị đếm được không?'),
                   ('Tách mỗi số thành số chục tương ứng.','Em đang gộp những lượng cùng đơn vị nào?'),
                   ('Gộp các chục rồi viết cùng lượng đó bằng số đơn vị.','Khi viết kết quả của các chục thành số, hàng đơn vị phải thế nào?')]
            action='cộng'
        else:
            explanation='90 là 9 chục, bớt 30 tức bớt 3 chục. Còn 6 chục, tức 60. Kiểm lại 60 + 30 = 90.'
            reason='Bớt các chục khỏi các chục cùng đơn vị; không bớt ba đơn vị khỏi chín chục.'
            hints=[('Cả số bị trừ và số trừ đều là số tròn chục.','Em có thể đếm theo chục thay cho từng đơn vị không?'),
                   ('Nêu số chục ban đầu và số chục cần bớt.','Hai lượng đang bớt có cùng đơn vị đếm chưa?'),
                   ('Bớt số chục rồi viết lại kết quả theo đơn vị; dùng cộng để kiểm tra.','Nếu cộng phần đã bớt vào phần còn lại, em phải lấy lại đại lượng nào?')]
            action='trừ'
        add(suffix,'current_g1_mental_add_sub',slot_name,
            f'Nhẩm {a} {action} {b}. Giải thích bằng cách đếm theo chục.',
            [{'id':'g0','text':str(a),'value':str(a),'unit':'','role':'first_number'},
             {'id':'g1','text':str(b),'value':str(b),'unit':'','role':'second_number'}],
            [teaching_step('Nhẩm bằng đơn vị chục',reason,f'{a}{op}{b}',str(result),'',explanation)],
            [{'quantity':'Kết quả phép tính','result':str(result),'unit':''}],
            ['Đề cho các số tròn chục, có thể đổi đơn vị đếm sang chục.','Giữ đúng dấu phép tính khi gộp hoặc bớt các chục.'],hints,
            {'family':'mental_round_tens_'+('add' if op=='+' else 'subtract'),'operations':[f'{a}{op}{b}'],'numeric_values':[str(a),str(b)]},
            {'method':'independent_operations_on_tens_then_reconstruction','tens_result':a//10+b//10 if op=='+' else a//10-b//10,'unit_result':result},
            'Tens-based mental method, values at most ninety and zero units throughout. No formal multiplication required; additive versus subtractive relation explained and the result withheld in all hints.')

    assert len(cases)==8
    blocked,questions,_=protections();_,_,_,seen_train=v4.v3_catalog()
    decisions=[];checks=[]
    for row in cases:
        mechanical=inspect_case(row); assert mechanical['passed'], (row['sample_id'],mechanical)
        signatures=answer_signatures(row,mechanical)
        assert not signatures & blocked, row['sample_id']
        assert normalized(row['problem']) not in questions
        assert mapping_error(row,nodes) is None
        overlap=signatures & seen_train.keys()
        row['provenance']['bounded_numeric_exposure']='PREVIOUS_TRAIN_CASE_MAY_RECUR_IN_FINITE_DOMAIN' if overlap else 'NO_DETECTED_PREVIOUS_TRAIN_SIGNATURE'
        row['provenance']['previous_train_source_ids']=sorted({i for sig in overlap for i in seen_train[sig]})
        decision={'sample_id':row['sample_id'],'row_sha256':row_sha(row),'reviewer':'root_single_assistant_separate_content_review_pass',
            **{field:True for field in REVIEW_FIELDS},'human_verified':False,'teacher_certified':False,
            'independent_external_AI_reviewer':False,'review_method':'Separate manual content/grade/unit/hint pass plus independent deterministic oracle; no claim of a second actor.',
            'notes':review_notes[row['sample_id']],'independent_arithmetic_oracle':oracles[row['sample_id']]}
        decisions.append(decision);checks.append({'sample_id':row['sample_id'],'mechanical':mechanical,'oracle':oracles[row['sample_id']],
            'protected_collision':False,'row_sha256':row_sha(row)})
    assert oracles[cases[0]['sample_id']]['count']==14
    assert oracles[cases[1]['sample_id']]['units']==50
    assert oracles[cases[4]['sample_id']]['ordered']==[8,25,52,58]
    assert oracles[cases[5]['sample_id']]['count']==9
    write_rows(destination,cases);write_rows(review_path,decisions)
    state=curate(root)
    write_json(evidence/'g1_foundations_0002_verification.json',{'created_utc':datetime.now(timezone.utc).isoformat(),
        'batch_sha256':sha(destination.read_bytes()),'review_sha256':sha(review_path.read_bytes()),'checks':checks,
        'no_external_AI_reviewer_claim':True,'training_started':False,'teacher_certified':False,
        'result':{k:state[k] for k in ('accepted_cases','chat_train_rows','remaining_core_cases','core_nodes_complete','decisions')}})
    print(json.dumps({k:state[k] for k in ('accepted_cases','chat_train_rows','remaining_core_cases','core_nodes_complete','decisions')}))


if __name__=='__main__':main()

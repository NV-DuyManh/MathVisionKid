"""Finite original grade-two drafts; never accept the author's own semantic review."""
import copy,json
from fractions import Fraction
from primary_math_data_pipeline import (HERE,DEFAULT_ROOT,read_rows,write_rows,write_json,sha,row_sha,
    inspect_case,mapping_error,protections,answer_signatures,normalized,curate)


def main():
    path=DEFAULT_ROOT/'authored_batches/g2_numbers_ray_0009.jsonl'
    if path.exists():print('Batch exists; resume review instead of generating it again.');return
    bp=DEFAULT_ROOT/'curriculum_blueprint.json';blueprint=json.loads(bp.read_text('utf-8'))
    nodes={n['node_id']:n for n in blueprint['nodes']}
    template=read_rows(DEFAULT_ROOT/'authored_batches/g1_geometry_0004.jsonl')[0]
    rows=[]
    def add(suffix,nodeid,slot,problem,givens,steps,answers,initial,hints,kind='core',student=None):
        r=copy.deepcopy(template);node=nodes[nodeid];sid='primary_20261017_g2_numbers_ray_0009_'+suffix
        r.update(sample_id=sid,case_group_id=sid,grade=2,topic=suffix,problem=problem,
            givens=[{'id':'g'+str(i),'text':t,'value':v,'unit':u,'role':role} for i,(t,v,u,role) in enumerate(givens)],
            requested_quantity='; '.join(q for q,v,u in answers) if answers else 'Thông tin để xác định số trên tia số',
            student_work=student,initial_guidance=initial,
            hints=[{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(hints)],
            worked_steps=[{'step_id':'s'+str(i),'title':t,'reason':why,'expression':expr,'result':str(v),'unit':u,'explanation':ex}
                for i,(t,why,expr,v,u,ex) in enumerate(steps)],
            expected_answer=[{'quantity':q,'result':str(v),'unit':u} for q,v,u in answers],can_solve=bool(answers),
            canonical_case={'family':suffix,'operations':[s[2] for s in steps if s[2] and '{s' not in s[2]],
                'numeric_values':[str(v) for t,v,u,role in givens if v is not None]})
        r['curriculum_assignment']={'node_id':nodeid,'curriculum_scope':node['curriculum_scope'],'case_kind':kind}
        if kind=='core':
            slotinfo=next(s for s in node['authoring_plan']['core_cases'] if s['case_slot']==slot)
            r['curriculum_assignment'].update({k:slotinfo[k] for k in ('case_slot','context_variant','method_variant')})
        r['provenance'].update(authoring_label='AI_TEACHER',authoring_agent='root',
            source_evidence=node['source_evidence'],blueprint_sha256=sha(bp.read_bytes()),
            source_kind='ORIGINAL_EXPLICIT_TEXT_TEACHER_CASE' if answers else 'ORIGINAL_MISSING_INFORMATION_GUARD',
            student_work_origin='EXPLICITLY_SYNTHETIC' if student else None,
            content_review_status='PENDING_INDEPENDENT_CONTENT_REVIEW',visual_or_physical_outcome_verified=False)
        rows.append(r)

    add('zero_tens_vs_zero_ones','current_g2_natural_numbers_1000','core_02',
        'Viết hai số: số A có 5 trăm, không có chục nào và 7 đơn vị; số B có 5 trăm, 7 chục và không có đơn vị rời. Đọc mỗi số và giải thích vì sao chữ số 0 phải ở hai vị trí khác nhau.',
        [('A có 5 trăm','500','','A_hundreds_value'),('A có 0 chục','0','','A_tens_value'),('A có 7 đơn vị','7','','A_ones_value'),
         ('B có 5 trăm','500','','B_hundreds_value'),('B có 7 chục','70','','B_tens_value'),('B có 0 đơn vị','0','','B_ones_value')],
        [('Viết số có hàng chục trống','Không có chục thì viết 0 ở hàng chục để giữ vị trí của hàng đơn vị.','500+0+7',507,'',
          'A có các chữ số hàng trăm, chục, đơn vị lần lượt là 5, 0, 7 nên viết 507. Đọc năm trăm linh bảy; cách đọc năm trăm lẻ bảy cũng biểu thị cùng số.'),
         ('Viết số có hàng đơn vị trống','Không có đơn vị rời thì 0 ở hàng đơn vị, còn 7 ở hàng chục.','500+70+0',570,'',
          'B viết 570, đọc năm trăm bảy mươi. Kiểm lại: 507 có 0 chục và 7 đơn vị; 570 có 7 chục và 0 đơn vị. Không bỏ chữ số 0 làm lệch hàng.')],
        [('Số A',507,''),('Số B',570,''),('Cách đọc số A','năm trăm linh bảy',''),('Cách đọc số B','năm trăm bảy mươi','')],
        ['Lập ba vị trí hàng trăm, hàng chục, hàng đơn vị cho từng số.','Chữ số không giữ chỗ cho hàng không có lượng, không được bỏ vị trí đó.'],
        [('Đọc riêng lượng của từng hàng trong mỗi mô tả.','Hàng nào của mỗi số được nói là không có lượng?'),
         ('Mỗi vị trí cần một chữ số, kể cả vị trí chưa có chục hoặc chưa có đơn vị.','Nếu bỏ vị trí trống, các chữ số còn lại có bị đổi hàng không?'),
         ('Tách lại mỗi số em viết thành giá trị ba hàng để đối chiếu với đề.','Số của em có giữ đúng vai trò từng hàng khi đọc lại không?')])

    add('adjacent_hundred_boundary','current_g2_natural_numbers_1000','core_03',
        'Dãy số thẻ tăng mỗi lần một đơn vị. Với thẻ 700, hãy ghi số liền trước và số liền sau, rồi kiểm rằng cả hai đều cách 700 đúng một đơn vị. Chú ý chỗ chuyển sang số tròn trăm.',
        [('Thẻ đang xét là 700','700','','anchor'),('Mỗi lần thay đổi một đơn vị','1','','adjacency_step')],
        [('Lùi một số để tìm số liền trước','Trong dãy tăng từng đơn vị, số ngay trước ít hơn số đang xét một đơn vị.','700-1',699,'',
          'Đếm lùi một số từ bảy trăm được sáu trăm chín mươi chín: số liền trước là 699.'),
         ('Tiến một số để tìm số liền sau','Số ngay sau nhiều hơn số đang xét một đơn vị.','700+1',701,'',
          'Đếm tiếp một số từ 700 được 701, đọc bảy trăm linh một hoặc bảy trăm lẻ một.'),
         ('Kiểm phía trước','Đi tiếp một đơn vị từ số liền trước phải về đúng thẻ mốc.','{s0}+1',700,'',
          '699 + 1 = 700, nên phía trước khớp.'),
         ('Kiểm phía sau','Đi lùi một đơn vị từ số liền sau phải về đúng thẻ mốc.','{s1}-1',700,'',
          '701 − 1 = 700. Dãy ba thẻ đúng là 699, 700, 701, mỗi cặp liền nhau hơn kém một đơn vị.')],
        [('Số liền trước 700',699,''),('Số liền sau 700',701,'')],
        ['Số liền trước và liền sau chỉ cách số đang xét đúng một đơn vị.','Đổi qua mốc tròn trăm vẫn phải giữ quy tắc này, không chỉ thay chữ số cuối tùy ý.'],
        [('Phân biệt hướng lùi với hướng tiến trong dãy số.','Số liền trước phải ít hơn hay nhiều hơn số mốc?'),
         ('Mỗi hướng chỉ thay đổi một đơn vị; qua mốc tròn trăm cần đọc lại toàn bộ số.','Em có đang giữ đúng một bước cho mỗi phía không?'),
         ('Dùng thao tác ngược từ từng số vừa tìm để quay lại mốc.','Cả hai phép kiểm của em có trở lại đúng số thẻ được cho không?')])

    wrong='4 trăm, 0 chục và 7 đơn vị viết là 47 vì không có chục thì bỏ vị trí đó.'
    add('misconception_omit_zero_place','current_g2_natural_numbers_1000',None,
        'Một bạn có câu viết giả định: '+wrong+' Hãy kiểm cách viết số theo hàng và sửa dựa đúng lượng mỗi hàng được nêu.',
        [('Bốn trăm','400','','hundreds_value'),('Không có chục','0','','tens_value'),('Bảy đơn vị','7','','ones_value')],
        [('Đối chiếu vị trí của chữ số','Số 47 có 4 ở hàng chục, không biểu thị 4 trăm như đề.',None,'cần giữ vị trí hàng chục','',
          'Không có chục thì vẫn cần chữ số 0 ở hàng chục. Bỏ vị trí ấy làm 4 chuyển sang hàng chục và đổi giá trị của số.'),
         ('Viết đủ các hàng và kiểm tổng giá trị','Giữ chữ số hàng trăm, hàng chục và hàng đơn vị đúng lượng được cho.','400+0+7',407,'',
          'Viết 4, 0, 7 theo ba hàng được số 407. Kiểm 400 + 0 + 7 = 407; đọc bốn trăm linh bảy hoặc bốn trăm lẻ bảy.')],
        [('Số cần viết đúng',407,'')],
        ['So hàng mà mỗi chữ số thực sự đứng trong lời viết với hàng đề yêu cầu.','Không có lượng ở một hàng không có nghĩa bỏ cả vị trí hàng đó.'],
        [('Cần phân biệt chữ số và giá trị của chữ số theo hàng.','Trong số bạn đã viết, chữ số đầu đang ở hàng nào?'),
         ('Giữ đủ ba vị trí rồi điền hàng chưa có lượng bằng chữ số thích hợp.','Đề có cho phép chuyển phần hàng trăm thành hàng chục không?'),
         ('Tách số đã sửa thành giá trị từng hàng để kiểm lại.','Phần hàng trăm và đơn vị của số em viết có khớp lượng đề cho chưa?')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':'không có chục thì bỏ vị trí đó','claim_scope':'Explicit omission of the tens position shifts the hundreds digit; no handwriting or hidden strategy inference.'}]})

    add('ray_single_unit_tick','current_g2_number_ray','core_01',
        'Một đoạn tia số tăng từ trái sang phải. Mỗi hai vạch liền nhau tăng đúng một đơn vị. Các vạch liền nhau của đoạn được mô tả là 202, 203, P, 205, 206 theo thứ tự trái sang phải. P là số nào? Kiểm với hai vạch hai bên.',
        [('Mỗi khoảng tăng 1','1','','tick_step'),('Vạch trước P là 203','203','','left_neighbour'),('Vạch sau P là 205','205','','right_neighbour')],
        [('Đi thêm một khoảng từ vạch đã biết','P liền bên phải 203 nên tăng đúng một đơn vị từ 203.','203+1',204,'',
          '203 + 1 = 204, nên P là 204.'),
         ('Kiểm vạch ở phía bên kia','Từ P đi tiếp một khoảng phải đến vạch 205 đã cho.','{s0}+1',205,'',
          '204 + 1 = 205, khớp vạch bên phải. Dãy là 202, 203, 204, 205, 206.')],
        [('Số tại vạch P',204,'')],
        ['Dùng chiều tăng và mức tăng giữa hai vạch mà đề đã nêu.','P là tên vị trí chưa biết số, không phải chữ số phải cộng vào phép tính.'],
        [('Tìm một vạch đã biết đứng liền vị trí cần tìm.','Mỗi lần đi sang vạch kế bên phải, số tăng bao nhiêu theo đề?'),
         ('Từ vạch ngay trước, đi đúng một khoảng thay vì đếm lại từ đầu tia số.','Em cần đi mấy khoảng từ vạch đã biết đến P?'),
         ('Sau khi tìm P, đi thêm một khoảng nữa để kiểm vạch đã biết bên phải.','Số nhận ở phép kiểm có khớp vạch bên kia chưa?')])

    add('ray_two_different_scales','current_g2_number_ray','core_02',
        'Có hai đoạn tia số giả định đều bắt đầu phần đang xét ở vạch ghi 60 và tăng sang phải. Đoạn A: các vạch liền nhau tăng 1 đơn vị. Đoạn B: các vạch liền nhau tăng 10 đơn vị. Ở mỗi đoạn, tính từ vạch 60 là vạch thứ nhất, hãy tìm số ở vạch thứ ba. Hai vạch thứ ba có ghi cùng số không? Giải thích.',
        [('Vạch thứ nhất của hai đoạn ghi 60','60','','common_first_tick'),('A tăng 1 mỗi khoảng','1','','A_tick_step'),
         ('B tăng 10 mỗi khoảng','10','','B_tick_step'),('Từ vạch thứ nhất đến thứ ba có hai khoảng','2','','interval_count')],
        [('Đếm khoảng ở đoạn A','Từ vạch thứ nhất tới thứ ba là hai khoảng, mỗi khoảng của A tăng một đơn vị.','60+1+1',62,'',
          'Đoạn A có các vạch 60, 61, 62 nên vạch thứ ba ghi 62.'),
         ('Dùng mức tăng của đoạn B','Vẫn hai khoảng nhưng mỗi khoảng B tăng mười đơn vị, không dùng mức tăng của A.','60+10+10',80,'',
          'Đoạn B có các vạch 60, 70, 80 nên vạch thứ ba ghi 80.'),
         ('Đối chiếu hai cách biểu diễn','Cùng thứ tự vạch chưa đủ để có cùng số khi mức tăng khác nhau.',None,'không cùng số','',
          '62 khác 80. Đếm số khoảng và mức tăng của mỗi đoạn mới xác định được số; không mặc định mọi đoạn đều tăng một đơn vị.')],
        [('Vạch thứ ba trên A',62,''),('Vạch thứ ba trên B',80,''),('Kết luận so hai số','không cùng số','')],
        ['Phân biệt số thứ tự vạch với giá trị số được ghi tại vạch.','Hai đoạn giống điểm bắt đầu nhưng khác mức tăng của mỗi khoảng.'],
        [('Từ một vạch đến vạch kế tiếp là một khoảng.','Từ vạch thứ nhất đến thứ ba có bao nhiêu khoảng?'),
         ('Đi cùng số khoảng nhưng dùng riêng mức tăng của mỗi đoạn.','Em có đang dùng nhầm mức tăng của đoạn này cho đoạn kia không?'),
         ('Ghi lại các vạch em đi qua trên từng đoạn rồi đối chiếu hai kết quả.','Nếu hai mức tăng khác nhau, điều gì cần được kiểm trước khi kết luận hai vị trí cùng số?')])

    add('ray_value_to_interval','current_g2_number_ray','core_03',
        'Một đoạn tia số tăng từ trái sang phải có các vạch mốc liền nhau ghi 710, 720, 730, 740, 750. Cần đặt điểm ghi số 736. Điểm ấy nằm giữa hai vạch mốc liền nhau nào? Chỉ nêu hai mốc kẹp điểm và kiểm bằng so sánh số; không cần đo vị trí chính xác trên ảnh.',
        [('Các mốc liền nhau: 710, 720, 730, 740, 750',None,'','ordered_reference_ticks'),('Số cần đặt là 736','736','','target_value')],
        [('Tìm hai mốc kẹp số đã cho','Mốc bên trái cần nhỏ hơn số cần đặt; mốc bên phải cần lớn hơn và là mốc liền sau mốc trái.',None,'giữa 730 và 740','',
          '730 bé hơn 736, còn 740 lớn hơn 736. Trong các mốc đã cho, 730 và 740 đứng liền nhau nên điểm 736 nằm giữa hai vạch ấy.'),
         ('Kiểm theo chiều tăng','Hai bất đẳng thức phải cùng đúng và không được bỏ qua một vạch mốc nằm giữa hai mốc chọn.',None,'730 < 736 < 740','',
          'Kiểm 730 < 736 < 740 và cặp 730, 740 là cặp vạch liền nhau. Không chọn 720 và 750 dù chúng cũng kẹp 736, vì chúng không liền nhau.')],
        [('Hai vạch mốc liền nhau kẹp điểm 736','giữa 730 và 740','')],
        ['Câu hỏi cho số cần đặt và yêu cầu tìm khoảng, ngược với việc đọc số từ một vạch.','Cần hai mốc liền nhau, không chỉ bất kỳ một số nhỏ hơn và một số lớn hơn.'],
        [('Đọc các mốc theo chiều tăng và so với số cần đặt.','Mốc nằm bên trái điểm cần nhỏ hơn hay lớn hơn số của điểm?'),
         ('Trong các mốc nhỏ hơn, xét mốc gần số cần đặt nhất rồi tìm mốc kế tiếp.','Hai mốc em chọn có đứng liền nhau trong danh sách không?'),
         ('Kiểm số cần đặt lớn hơn mốc trái và nhỏ hơn mốc phải, đồng thời giữ điều kiện liền nhau.','Cặp mốc của em đã thỏa cả hai phép so và điều kiện kề nhau chưa?')])

    wrong='R là 311 vì số liền sau 310 là 311.'
    add('misconception_tick_vs_successor','current_g2_number_ray',None,
        'Một đoạn tia số có các vạch liền nhau tăng đều 10 đơn vị, theo thứ tự là 300, 310, R, 330. Một bạn viết giả định: '+wrong+' Hãy nhận xét phần đúng và phần chưa đúng trong lý do, rồi tìm lại số tại R.',
        [('Vạch trước R là 310','310','','preceding_tick'),('Mỗi khoảng tăng 10','10','','tick_step'),('Vạch sau R là 330','330','','following_tick')],
        [('Phân biệt hai nghĩa của liền sau','Số tự nhiên liền sau 310 đúng là 311, nhưng vạch kế tiếp của đoạn đang xét cách 10 đơn vị chứ không phải một.',None,'đã dùng sai mức tăng của vạch','',
          'Câu nói về số tự nhiên liền sau là đúng, nhưng không phù hợp mức tăng mỗi khoảng đã cho của tia số này.'),
         ('Tính theo khoảng thật của đoạn','Đi từ 310 sang vạch R phải cộng đủ mức tăng một khoảng.','310+10',320,'',
          '310 + 10 = 320 nên R ghi 320.'),
         ('Kiểm vạch bên phải','Đi tiếp một khoảng cùng mức tăng phải khớp mốc kế.','{s1}+10',330,'',
          '320 + 10 = 330, đúng vạch đã cho. Dãy mốc là 300, 310, 320, 330.')],
        [('Số tại R',320,'')],
        ['Kiểm riêng câu về số tự nhiên liền sau và mức tăng của vạch trên đoạn này.','Không suy thêm lỗi ngoài câu viết giả định.'],
        [('Đề đã nói rõ quy tắc đi từ vạch này sang vạch kế.','Một khoảng của đoạn này tương ứng bao nhiêu đơn vị?'),
         ('Tìm xem lời bạn viết đã dùng mức tăng của số tự nhiên liên tiếp hay mức tăng của đoạn.','Hai quy tắc ấy ở đây có giống nhau không?'),
         ('Từ số ở vạch trước, dùng quy tắc đúng rồi kiểm tiếp với vạch sau.','Phép kiểm của em có khớp cả mức tăng và mốc phía bên kia không?')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':'vì số liền sau 310 là 311','claim_scope':'The stated natural-successor rule uses step1 instead of explicit tick step10; successor fact itself is correct.'}]})

    add('guard_unknown_tick_step','current_g2_number_ray',None,
        'Em mô tả một đoạn tia số tăng về bên phải có các vạch cách đều. Vạch A ghi 120, vạch B ngay bên phải chưa ghi số. Chưa biết mỗi khoảng tăng bao nhiêu và chưa có vạch khác kèm số hoặc ảnh rõ để xác định. Em hỏi B là số nào. Hãy hỏi thông tin còn thiếu thay vì mặc định mỗi khoảng tăng một.',
        [('Vạch A ghi 120','120','','known_tick'),('B ngay bên phải A, chưa biết giá trị mỗi khoảng',None,'','unknown_step')],[],[],
        ['Vị trí liền vạch chưa xác định số nếu chưa biết mức tăng mỗi khoảng.','Em cho biết mỗi khoảng ứng với bao nhiêu đơn vị, hoặc cung cấp thêm các vạch có số để xác định quy tắc.'],
        [('Cần biết quy tắc tăng số giữa hai vạch liên tiếp.','Mỗi khoảng trên đoạn này tăng bao nhiêu đơn vị?'),
         ('Nếu chưa có quy tắc bằng lời, các vạch khác có số có thể giúp xác định.','Em có thể chép thêm các vạch có số cùng thứ tự của chúng không?'),
         ('Chỉ sau khi biết mức tăng mới kiểm được số tại vạch kế.','Thông tin em bổ sung đã đủ xác định một mức tăng duy nhất chưa?')],kind='guard')

    assert len(rows)==8
    protected,questions,_=protections()
    existing=[r for f in (DEFAULT_ROOT/'authored_batches').glob('*.jsonl') for r in read_rows(f)]
    existing_questions={normalized(r['problem']) for r in existing}
    checks=[]
    for r in rows:
        m=inspect_case(r);assert m['passed'],(r['sample_id'],m)
        assert mapping_error(r,nodes) is None
        assert not answer_signatures(r,m)&protected,r['sample_id']
        assert normalized(r['problem']) not in questions|existing_questions
        checks.append({'sample_id':r['sample_id'],'row_sha256':row_sha(r),'mechanical':m,'mapping_pass':True})
    assert divmod(507,100)==(5,7) and divmod(570,100)==(5,70)
    assert list(range(699,702))==[699,700,701]
    assert Fraction(400)+Fraction(0)+Fraction(7)==407
    assert list(range(202,207))[2]==204
    assert list(range(60,63))[2]==62 and list(range(60,81,10))[2]==80
    ticks=[710,720,730,740,750];target=736
    brackets=[(a,b) for a,b in zip(ticks,ticks[1:]) if a<target<b];assert brackets==[(730,740)]
    assert list(range(300,331,10))[2]==320
    assert 120+1!=120+10
    frozen={p:sha((HERE.parent/p).read_bytes())==h for p,h in blueprint['existing_inputs']['source_fingerprints'].items()}
    assert all(frozen.values())
    write_rows(path,rows)
    write_json(HERE/'evidence/primary_math_teacher_20261016/g2_numbers_ray_0009_pre_review.json',{
        'batch_sha256':sha(path.read_bytes()),'authored_cases':8,'core_cases':5,'misconception_cases':2,'guard_cases':1,
        'checks':checks,'frozen_inputs_unchanged':frozen,
        'self_content_check':'Author checked visible reasoning, grade, units, pupil-work excerpts and all hints; independent semantic review is still required.',
        'independent_semantic_review_completed':False,'oracles':{
            'zero_place_values':[507,570],'adjacent_numbers':[699,700,701],'zero_place_correction':407,
            'single_tick':204,'different_scales':[62,80],'unique_adjacent_bracket':brackets,
            'step_not_successor':320,'missing_scale_completions':[121,130]},
        'arithmetic_oracle_is_semantic_proof':False,'human_verified':False,'teacher_certified':False,
        'training_started':False,'sealed_concept_challenge_read':False})
    state=curate(DEFAULT_ROOT)
    assert state['authored_cases']==104 and state['accepted_cases']==88
    assert state['decisions']=={'PENDING_AI_CONTENT_REVIEW':16,'ACCEPTED_AI_RESEARCH':88}
    print(json.dumps({k:state[k] for k in ('authored_cases','accepted_cases','chat_train_rows','remaining_core_cases','decisions')}))


if __name__=='__main__':main()

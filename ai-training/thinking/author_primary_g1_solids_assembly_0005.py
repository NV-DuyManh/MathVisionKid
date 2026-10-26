"""Original hypothetical solid/assembly cases, leaving content review pending."""
import copy,json
from primary_math_data_pipeline import (DEFAULT_ROOT,HERE,read_rows,write_rows,write_json,sha,
    inspect_case,mapping_error,protections,normalized)


def main():
    path=DEFAULT_ROOT/'authored_batches/g1_solids_assembly_0005.jsonl'
    if path.exists():print('Batch exists; continue from saved review/state.');return
    bp=DEFAULT_ROOT/'curriculum_blueprint.json'
    nodes={n['node_id']:n for n in json.loads(bp.read_text('utf-8'))['nodes']}
    template=read_rows(DEFAULT_ROOT/'authored_batches/g1_geometry_0004.jsonl')[0]
    rows=[]
    def add(suffix,nodeid,slot,problem,descriptions,steps,answers,initial,hints,kind='core',student=None):
        r=copy.deepcopy(template);node=nodes[nodeid]
        ident='primary_20261016_g1_solids_assembly_0005_'+suffix
        r.update(sample_id=ident,case_group_id=ident,topic=suffix,problem=problem,
            givens=[{'id':'g'+str(i),'text':t,'value':None,'unit':'','role':'explicit_hypothetical_description'} for i,t in enumerate(descriptions)],
            requested_quantity='; '.join(q for q,_ in answers) if answers else 'Thông tin còn thiếu để nhận dạng hoặc kiểm cách ghép',
            student_work=student,initial_guidance=initial,
            hints=[{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(hints)],
            worked_steps=[{'step_id':'s'+str(i),'title':t,'reason':why,'expression':None,'result':v,'unit':'','explanation':ex} for i,(t,why,v,ex) in enumerate(steps)],
            expected_answer=[{'quantity':q,'result':v,'unit':''} for q,v in answers],can_solve=bool(answers),
            canonical_case={'family':suffix,'operations':[],'numeric_values':[]})
        r['curriculum_assignment']={'node_id':nodeid,'curriculum_scope':node['curriculum_scope'],'case_kind':kind}
        if kind=='core':
            s=next(s for s in node['authoring_plan']['core_cases'] if s['case_slot']==slot)
            r['curriculum_assignment'].update({k:s[k] for k in ('case_slot','context_variant','method_variant')})
        r['provenance'].update(source_kind='ORIGINAL_EXPLICIT_HYPOTHETICAL_TEXT_DESCRIPTION' if answers else 'ORIGINAL_MISSING_INFORMATION_GUARD',
            source_evidence=node['source_evidence'],blueprint_sha256=sha(bp.read_bytes()),
            student_work_origin='EXPLICITLY_SYNTHETIC' if student else None)
        rows.append(r)

    add('cube_all_faces','current_g1_solid_shapes','core_01',
        'Giả sử một khối đồ chơi kín có dạng hộp như con xúc xắc: cả sáu mặt đều là các hình vuông bằng nhau. Hãy gọi tên khối và giải thích bằng đặc điểm các mặt được mô tả.',
        ['Khối kín dạng hộp như con xúc xắc.','Cả sáu mặt đều là hình vuông bằng nhau.'],
        [('Xét các mặt của cả khối','Cần dùng mô tả của cả khối, không chỉ hình dạng của một mặt.', 'sáu mặt vuông bằng nhau',
          'Đề cho biết mọi mặt của khối dạng hộp đều là các hình vuông bằng nhau.'),
         ('Gọi tên khối','Khối dạng hộp với sáu mặt vuông bằng nhau là khối lập phương.', 'khối lập phương',
          'Khối đồ chơi có dạng khối lập phương, giống mô hình con xúc xắc. Ta gọi tên khối, không chỉ gọi tên một mặt là hình vuông.')],
        [('Tên khối đồ chơi','khối lập phương')],
        ['Phân biệt tên một mặt phẳng với tên của cả khối.','Dùng đặc điểm của tất cả các mặt mà đề đã cho.'],
        [('Đề đang hỏi tên cả đồ vật có khối.','Em cần xét một mặt hay các mặt của cả khối?'),
         ('Đối chiếu kiểu mặt và sự bằng nhau của các mặt với mô hình đã học.','Các mặt trong mô tả giống nhau ở những điểm nào?'),
         ('Gọi tên khối rồi kiểm rằng tên đó phù hợp với toàn bộ các mặt.','Tên em chọn là tên của một hình phẳng hay của một khối?')])

    add('cube_elongated_box_contrast','current_g1_solid_shapes','core_02',
        'Hai mô hình hộp kín được mô tả: A có cả sáu mặt là hình vuông bằng nhau; B có hai mặt đầu là hình vuông bằng nhau, bốn mặt bên là hình chữ nhật dài, không phải hình vuông. Trong hai mô hình, mô hình nào là khối lập phương? Mô hình B có dạng khối gì?',
        ['A có sáu mặt vuông bằng nhau.','B có hai mặt đầu vuông, bốn mặt bên chữ nhật dài, không vuông.'],
        [('Đối chiếu điều kiện của khối lập phương','Cần mọi mặt đều là hình vuông bằng nhau, chứ không chỉ hai mặt đầu.', 'mô hình A',
          'A đáp ứng đủ mô tả các mặt của khối lập phương. B có mặt bên không vuông nên không đáp ứng điều kiện này.'),
         ('Gọi tên mô hình hộp còn lại','B là hộp kín có hai mặt đầu vuông và các mặt bên chữ nhật dài.', 'khối hộp chữ nhật',
          'B có dạng khối hộp chữ nhật kéo dài. Hai mặt đầu vuông không làm mọi mặt còn lại thành vuông.')],
        [('Mô hình là khối lập phương','mô hình A'),('Tên dạng khối của B','khối hộp chữ nhật')],
        ['Đọc riêng mô tả của từng mô hình.','Một vài mặt vuông chưa đủ để kết luận cả khối là lập phương.'],
        [('Tìm mô tả nói về toàn bộ các mặt.','Điều kiện của khối lập phương áp dụng cho bao nhiêu mặt của khối?'),
         ('Đối chiếu các mặt bên với các mặt đầu ở mỗi mô hình.','Có mô hình nào nêu rõ một số mặt không phải hình vuông không?'),
         ('Kiểm tên từng khối với toàn bộ mô tả, không bỏ qua mặt bên.','Lý do em chọn có xét hết các mặt được nêu chưa?')])

    add('box_reoriented','current_g1_solid_shapes','core_03',
        'Giả sử một hộp kín có dạng khối hộp chữ nhật, ba chiều dài, rộng, cao khác nhau. Ta đổi từ đặt ngang sang dựng đứng, không bóp méo hay cắt hộp. Sau thao tác, tên dạng khối có đổi thành khối lập phương không? Hãy gọi tên và kiểm theo hình dạng.',
        ['Hộp có dạng khối hộp chữ nhật, ba chiều khác nhau.','Chỉ đổi cách đặt, không làm biến dạng.'],
        [('Tách hướng đặt khỏi hình dạng','Dựng hộp chỉ đổi chiều nào hướng lên trên, không làm các chiều vốn khác nhau thành bằng nhau.', 'hướng đặt thay đổi',
          'Các mặt và độ dài các cạnh vẫn giữ như cũ; không có thao tác kéo ngắn hay kéo dài hộp.'),
         ('Giữ tên theo đặc điểm và kiểm lại','Tên khối phụ thuộc hình dạng chứ không phụ thuộc cách đặt ngang hoặc đứng.', 'khối hộp chữ nhật',
          'Hộp vẫn có dạng khối hộp chữ nhật. Các chiều vẫn khác nhau nên chỉ dựng đứng không biến hộp này thành khối lập phương.')],
        [('Tên dạng khối sau đổi cách đặt','khối hộp chữ nhật')],
        ['Theo dõi thao tác được cho phép và những đặc điểm giữ nguyên.','Không suy tên khối chỉ từ việc thấy hộp cao lên khi dựng đứng.'],
        [('Chỉ có cách đặt được đổi.','Thao tác này có làm cạnh hộp dài thêm hay ngắn đi không?'),
         ('Các chiều khác nhau vẫn là các chiều của chính hộp đó.','Đổi chiều hướng lên trên có làm các chiều trở nên bằng nhau không?'),
         ('Đọc tên khối theo các mặt và cạnh vẫn giữ, rồi đối chiếu với mô tả ban đầu.','Em đang kiểm hình dạng của hộp hay chỉ kiểm hướng đặt?')])

    add('two_squares_side_join','current_g1_assemble_shapes','core_01',
        'Giả sử có hai miếng hình vuông bằng nhau. Đặt một miếng bên trái, một miếng bên phải, hai miếng sát nhau theo trọn một cạnh; không chồng và không có khe hở. Đường bao ngoài của cả hai miếng tạo dạng hình gì? Giải thích cách ghép.',
        ['Hai hình vuông bằng nhau.','Ghép trái–phải sát trọn cạnh, không chồng, không khe.'],
        [('Ghép theo đúng cạnh chung','Hai cạnh bằng nhau phải áp sát trọn nhau, còn phần giấy nằm ở hai phía của cạnh chung.', 'hai miếng cạnh nhau',
          'Đặt hai hình vuông cạnh nhau từ trái sang phải. Cạnh chung nằm bên trong phần ghép.'),
         ('Xét đường bao ngoài','Sau khi ghép, phía trên và dưới dài hơn hai bên; các góc ngoài vẫn như góc tờ giấy.', 'hình chữ nhật',
          'Đường bao ngoài có dạng hình chữ nhật: hai cạnh dài chạy qua cả hai miếng, hai cạnh ngắn chỉ cao bằng một miếng. Kiểm không có phần giấy chồng hoặc khe hở.')],
        [('Dạng đường bao ngoài','hình chữ nhật')],
        ['Chỉ xét mép ngoài sau khi ghép, không nhầm cạnh chung bên trong với cạnh ngoài.','Giữ đúng điều kiện sát cả cạnh, không chồng và không để hở.'],
        [('Đặt hai miếng cạnh nhau theo chiều đề nêu.','Hai miếng cần áp sát nhau ở phần nào?'),
         ('Cạnh chung nằm giữa hai miếng nên không thuộc đường bao ngoài.','Mép trên của phần ghép chạy qua một hay cả hai miếng?'),
         ('Theo mép ngoài một vòng và đối chiếu với các hình đã học.','Các cạnh ngoài có đặc điểm gì để em gọi tên hình?')])

    add('diagonal_cut_restore','current_g1_assemble_shapes','core_02',
        'Giả sử một hình vuông được cắt đúng theo đoạn nối hai góc đối diện, tạo hai miếng tam giác. Còn đủ cả hai miếng, không làm rách hay cắt thêm. Muốn ghép lại hình vuông ban đầu, em đặt hai miếng như thế nào? Nêu cách kiểm mép ngoài.',
        ['Hình vuông bị cắt theo đoạn nối hai góc đối diện.','Còn đủ hai miếng tam giác, không thay đổi miếng.'],
        [('Tìm cạnh vừa cắt','Hai miếng có hai cạnh sinh ra từ cùng một đường cắt nên có thể ghép khớp.', 'ghép hai cạnh vừa cắt',
          'Đưa hai cạnh vừa cắt sát trọn nhau. Đặt phần giấy của hai miếng về hai phía của cạnh chung, không chồng một miếng lên miếng kia.'),
         ('Kiểm phần được khôi phục','Đường cắt nằm bên trong; các cạnh cũ của hình vuông tạo lại đường bao ngoài.', 'hình vuông ban đầu',
          'Ghép như vậy khôi phục hình vuông ban đầu. Kiểm bốn cạnh ngoài bằng nhau, các góc như trước, không có khe hở hay chồng giấy.')],
        [('Cách ghép','ghép hai cạnh vừa cắt, hai miếng nằm hai phía cạnh chung'),('Hình khôi phục','hình vuông ban đầu')],
        ['Đề cho biết hai miếng xuất phát từ cùng một hình vuông.','Cần tìm hai mép cùng được tạo ra khi cắt.'],
        [('Chú ý nguồn gốc của từng cạnh miếng.','Cạnh nào của hai miếng cùng sinh ra từ một đường cắt?'),
         ('Khi áp hai cạnh vừa cắt, để hai phần giấy nằm hai phía của đường chung.','Cách đặt của em có làm một miếng che lên miếng kia không?'),
         ('Kiểm mép ngoài và việc dùng đủ hai miếng, không sửa các miếng.','Mép ngoài đã khôi phục đầy đủ các cạnh và góc trước khi cắt chưa?')])

    add('fill_four_square_frame','current_g1_assemble_shapes','core_03',
        'Một khung hình vuông giả định được chia thành hai hàng và hai cột, tạo bốn ô vuông bằng nhau. Đã đặt các miếng vừa ô ở ô trên trái, trên phải và dưới trái. Còn một miếng vuông vừa ô, không được chồng lên miếng đã đặt. Cần đặt miếng cuối ở đâu để lấp kín khung? Kiểm đủ các ô.',
        ['Khung vuông hai hàng hai cột có bốn ô bằng nhau.','Đã lấp trên trái, trên phải, dưới trái.','Còn một miếng vuông vừa một ô, cấm chồng.'],
        [('Đối chiếu các ô đã được lấp','Miếng cuối cần vào ô còn trống, không vào ô đã có miếng.', 'ô dưới phải còn trống',
          'Hàng trên đã đủ hai ô. Hàng dưới đã có ô trái, còn ô phải chưa có miếng.'),
         ('Đặt miếng và kiểm toàn khung','Mỗi ô đúng một miếng sẽ lấp kín khung mà không chồng.', 'ô dưới phải',
          'Đặt miếng cuối vào ô dưới phải. Kiểm trên trái, trên phải, dưới trái, dưới phải đều có một miếng; không còn ô trống hoặc ô bị chồng.')],
        [('Ô cần đặt miếng cuối','ô dưới phải')],
        ['Dùng mô tả hai hàng và hai cột để liệt kê các ô.','Phân biệt ô đã lấp với ô chưa lấp trước khi đặt thêm.'],
        [('Đọc từng hàng thay vì đoán theo hình tưởng tượng.','Hàng nào đã được lấp đủ theo mô tả?'),
         ('Đối chiếu từng ô trong hàng còn lại với danh sách đã lấp.','Có ô nào chưa nằm trong danh sách các ô đã có miếng?'),
         ('Sau khi chọn ô, kiểm mỗi ô chỉ có một miếng và không còn ô trống.','Cách đặt của em có thỏa cả điều kiện đủ ô và không chồng không?')])

    wrong='Chỉ cần mặt trước vuông thì chắc chắn cả khối là khối lập phương.'
    add('misconception_one_face','current_g1_solid_shapes',None,
        'Giả sử một hộp kéo dài có mặt trước vuông, các mặt bên là hình chữ nhật dài không vuông. Một bạn phát biểu giả định: '+wrong+' Hãy nhận xét dựa vào mô tả và gọi tên dạng khối của hộp.',
        ['Mặt trước vuông; các mặt bên chữ nhật dài không vuông.'],
        [('Kiểm điều kiện cho cả khối','Một mặt vuông không đủ; khối lập phương cần tất cả sáu mặt vuông bằng nhau.', 'chưa đủ từ một mặt',
          'Phát biểu đã bỏ qua các mặt bên được mô tả là không vuông. Ta không thể dùng một mặt để kết luận thay cho cả khối.'),
         ('Gọi tên theo toàn bộ mô tả','Hộp kéo dài có các mặt bên chữ nhật không vuông phù hợp dạng khối hộp chữ nhật.', 'khối hộp chữ nhật',
          'Hộp này có dạng khối hộp chữ nhật. Muốn nhận dạng khối lập phương, cần đối chiếu cả các mặt, không chỉ mặt trước.')],
        [('Tên dạng khối của hộp','khối hộp chữ nhật')],
        ['Đối chiếu từ “chỉ cần” trong phát biểu với dữ kiện các mặt bên.','Chỉ góp ý điều thể hiện trong câu phát biểu giả định.'],
        [('Tên cả khối cần phù hợp với tất cả các mặt.','Phát biểu của bạn đã xét những mặt nào?'),
         ('Đề còn mô tả các mặt bên khác với mặt trước.','Các mặt bên có đáp ứng điều kiện của khối mà bạn chọn không?'),
         ('Dùng đủ mô tả mặt trước và mặt bên để gọi lại tên khối.','Tên em chọn đã khớp với cả hai loại mặt được nêu chưa?')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':wrong,'claim_scope':'Explicitly stated one-face sufficiency contradicts the provided non-square side faces; no unseen inspection claim.'}]})

    wrong='Hai hình vuông chồng trùng khít tạo thành một hình chữ nhật dài hơn.'
    add('misconception_overlap','current_g1_assemble_shapes',None,
        'Giả sử hai miếng vuông bằng nhau được đặt chồng trùng khít: mọi mép miếng trên trùng đúng mép miếng dưới. Một bạn viết giả định: '+wrong+' Hãy xét đường bao nhìn từ trên xuống và sửa lời giải thích.',
        ['Hai miếng vuông bằng nhau, đặt chồng trùng khít mọi mép.'],
        [('Theo đường bao được cho','Chồng trùng khít làm hai đường bao trùng nhau, không nối dài mép ngoài.', 'mép ngoài không dài thêm',
          'Lời viết “dài hơn” chưa phù hợp: không có phần miếng nào nhô ra ngoài đường bao vuông ban đầu.'),
         ('Gọi tên và phân biệt hai cách đặt','Chồng khít khác với đặt sát cạnh, không chồng.', 'hình vuông',
          'Đường bao nhìn từ trên vẫn là hình vuông. Muốn được đường bao chữ nhật dài hơn, cần chuyển hai miếng sang đặt cạnh nhau sát trọn cạnh, không chồng.')],
        [('Dạng đường bao khi chồng khít','hình vuông')],
        ['Giữ đúng dữ kiện mọi mép trùng khít.','Xét đường bao ngoài thay vì chỉ đếm số miếng.'],
        [('Đề không cho miếng nào nhô ra khỏi miếng kia.','Có mép ngoài nào được kéo dài thêm khi chồng khít không?'),
         ('So cách chồng khít với cách đặt sát cạnh để thấy chúng khác nhau.','Hai miếng trong đề đang nằm cạnh nhau hay trùng lên nhau?'),
         ('Lần theo mép ngoài rồi gọi tên theo hình dạng vẫn còn.','Lý do em dùng có xét mép ngoài thực sự được mô tả không?')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':wrong,'claim_scope':'The explicit claim of increased outline length contradicts coincident boundaries; no fabricated gap or hand movement.'}]})

    add('guard_one_visible_face','current_g1_solid_shapes',None,
        'Em chỉ kể rằng nhìn thấy một mặt trước hình vuông của một hộp kín, chưa có thông tin các mặt khác hoặc các chiều của hộp. Em hỏi có chắc đó là khối lập phương không. Hãy hỗ trợ mà không đoán phần bị khuất.',
        ['Chỉ biết một mặt trước vuông; chưa biết các mặt khác hoặc các chiều.'],[],[],
        ['Chỉ biết một mặt vuông thì chưa đủ kết luận cả khối là lập phương.','Em mô tả thêm các mặt khác, hoặc gửi ảnh từ những phía khác để cùng đối chiếu hình dạng.'],
        [('Một mặt vuông có thể thuộc những hộp có hình dạng khác nhau.','Em có thể mô tả hoặc gửi thêm các mặt bên của hộp không?'),
         ('Cần kiểm các mặt còn lại chứ không chỉ mặt trước.','Các mặt khác có đều là hình vuông bằng nhau không?'),
         ('Nếu chưa có thêm dữ kiện, cần giữ kết luận chưa xác định thay vì đoán.','Em đã có đủ thông tin để đối chiếu toàn bộ các mặt chưa?')],kind='guard')

    add('guard_unseen_assembly','current_g1_assemble_shapes',None,
        'Em nói đã ghép vài miếng thành hình ngôi nhà và hỏi mình làm đúng chưa, nhưng chưa gửi mẫu yêu cầu, hình các miếng hay cách em đã xếp. Hãy hướng dẫn em cung cấp bằng chứng để kiểm, chưa kết luận bài ghép đúng hoặc sai.',[],[],[],
        ['Mình chưa có mẫu cần ghép và cách em đã xếp nên chưa kiểm được.','Em gửi mẫu cùng ảnh các miếng và phần đã ghép, hoặc mô tả rõ hình dạng, vị trí và quy tắc ghép.'],
        [('Muốn so đúng sai, cần biết bài yêu cầu tạo hình nào và có những miếng nào.','Em có thể gửi mẫu yêu cầu cùng hình các miếng được cho không?'),
         ('Cần thêm cách em đã đặt các miếng để đối chiếu với mẫu.','Em có thể gửi ảnh phần đã ghép hoặc kể vị trí từng miếng không?'),
         ('Chỉ sau khi có mẫu, các miếng và cách xếp mới kiểm được đủ miếng, khớp mép và quy tắc.','Đề có quy định dùng đủ miếng và không chồng lên nhau không?')],kind='guard')

    assert len(rows)==10
    _,questions,_=protections()
    for r in rows:
        m=inspect_case(r);assert m['passed'],(r['sample_id'],m)
        assert mapping_error(r,nodes) is None
        assert normalized(r['problem']) not in questions
        assert r['provenance']['actual_image_asset_supplied'] is False
    write_rows(path,rows)
    write_json(HERE/'evidence/primary_math_teacher_20261016/g1_solids_assembly_0005_author_checks.json',
        {'batch_sha256':sha(path.read_bytes()),'authored':10,'content_review_status':'PENDING_SEPARATE_CONTENT_PASS',
         'text_only_hypothetical_cases':True,'physical_outcome_verified':False,'training_started':False,'skills_matched':'none'})
    print(json.dumps({'authored':10,'batch_sha256':sha(path.read_bytes()),'review_pending':True}))


if __name__=='__main__':main()

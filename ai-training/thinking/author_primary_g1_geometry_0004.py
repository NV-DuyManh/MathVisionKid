"""Text-grounded geometry cases; no claim of image or physical assessment."""
import json
from datetime import datetime, timezone
from primary_math_data_pipeline import (DEFAULT_ROOT, HERE, REVIEW_FIELDS, read_rows, write_rows, write_json,
    row_sha, sha, inspect_case, mapping_error, protections, normalized, curate)


def build():
    bp=DEFAULT_ROOT/'curriculum_blueprint.json'
    nodes={n['node_id']:n for n in json.loads(bp.read_text('utf-8'))['nodes']}
    rows=[]
    def add(suffix,nodeid,slot,problem,descriptions,steps,answers,initial,hints,kind='core',student=None):
        node=nodes[nodeid];ident='primary_20261016_g1_geometry_0004_'+suffix
        assignment={'node_id':nodeid,'curriculum_scope':node['curriculum_scope'],'case_kind':kind}
        if kind=='core':
            s=next(s for s in node['authoring_plan']['core_cases'] if s['case_slot']==slot)
            assignment.update({k:s[k] for k in ('case_slot','context_variant','method_variant')})
        rows.append({'sample_id':ident,'case_group_id':ident,'split':'train','grade':1,'topic':suffix,
            'problem':problem,'givens':[{'id':'g'+str(i),'text':d,'value':None,'unit':'','role':'explicit_description'} for i,d in enumerate(descriptions)],
            'requested_quantity':'; '.join(q for q,_ in answers) if answers else 'Thông tin hình dạng hoặc vị trí còn thiếu',
            'student_work':student,'initial_guidance':initial,
            'hints':[{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(hints)],
            'worked_steps':[{'step_id':'s'+str(i),'title':t,'reason':r,'expression':None,'result':v,'unit':'','explanation':x} for i,(t,r,v,x) in enumerate(steps)],
            'expected_answer':[{'quantity':q,'result':v,'unit':''} for q,v in answers],
            'can_solve':bool(answers),'canonical_case':{'family':suffix,'operations':[],'numeric_values':[]},
            'curriculum_assignment':assignment,
            'provenance':{'authoring_method':'original_AI_teacher','human_verified':False,'teacher_certified':False,
                'source_kind':'ORIGINAL_EXPLICIT_HYPOTHETICAL_TEXT_DESCRIPTION' if answers else 'ORIGINAL_MISSING_INFORMATION_GUARD',
                'source_evidence':node['source_evidence'],'blueprint_sha256':sha(bp.read_bytes()),
                'benchmark_status':'TRAINING_ONLY_NOT_GOLD','real_observation_claim':False,
                'visual_or_physical_outcome_verified':False,'actual_image_asset_supplied':False,
                'student_work_origin':'EXPLICITLY_SYNTHETIC' if student else None},
            'quality_flags':{'app_plan_draft_compatible':False,'app_mapping_status':'NEUTRAL_TEACHER_SCHEMA_REQUIRES_ADAPTER',
                'full_worked_solution_requires_explicit_request':True,'three_hint_levels_answer_free':True,
                'text_description_only_not_vision_training':True}})

    add('left_right_anchor','current_g1_spatial_orientation','core_01',
        'Theo chiều từ trái sang phải trên trang, ba đồ vật được xếp: cốc, sách, hộp. Đồ nào ở ngay bên trái sách và đồ nào ở ngay bên phải sách? Chỉ dùng thứ tự đã mô tả.',
        ['Từ trái sang phải trên trang: cốc, sách, hộp.'],
        [('Chọn sách làm mốc','Câu hỏi hỏi vị trí so với sách, nên xét hai đồ đứng cạnh sách.', 'sách',
          'Trong thứ tự cốc, sách, hộp, sách nằm giữa hai đồ còn lại.'),
         ('Tìm đồ cạnh trái','Chiều trái sang phải đã được đề cố định; đồ ngay trước sách trong dãy nằm bên trái sách.', 'cốc',
          'Cốc đứng ngay trước sách theo chiều trái sang phải, nên cốc ở ngay bên trái sách.'),
         ('Tìm đồ cạnh phải','Đồ ngay sau sách theo chiều đã cho nằm bên phải sách.', 'hộp',
          'Hộp đứng ngay sau sách, nên hộp ở ngay bên phải sách. Đọc lại cốc → sách → hộp để kiểm cả hai vị trí.')],
        [('Đồ ngay bên trái sách','cốc'),('Đồ ngay bên phải sách','hộp')],
        ['Đề đã quy định chiều từ trái sang phải trên trang.','Giữ sách làm mốc khi xét từng phía.'],
        [('Đọc dãy đúng theo chiều đề đã ghi.','Đồ vật nào được chọn làm mốc trong câu hỏi?'),
         ('Xét đồ đứng liền trước và đồ đứng liền sau mốc theo chiều đã cho.','Hai đồ cạnh mốc nằm ở những phía nào?'),
         ('Đối chiếu riêng mỗi phía với dãy ban đầu, không đổi mốc giữa chừng.','Em đã trả lời đủ cả hai phía so với cùng một mốc chưa?')])

    add('above_below_inverse','current_g1_spatial_orientation','core_02',
        'Kệ có hai tầng nằm ngang: gấu bông ở tầng cao, xe đồ chơi ở tầng thấp, thẳng dưới gấu. So với gấu thì xe ở đâu? So với xe thì gấu ở đâu?',
        ['Gấu bông ở tầng cao.','Xe đồ chơi ở tầng thấp, thẳng dưới gấu.'],
        [('Lấy gấu làm mốc','Đồ ở tầng thấp nằm dưới đồ ở tầng cao.', 'ở dưới gấu',
          'Xe ở tầng thấp còn gấu ở tầng cao, nên xe ở dưới gấu.'),
         ('Đổi mốc để đối chiếu','Khi nói lại cùng hai đồ vật với mốc đổi sang xe, hướng quan hệ cũng đổi theo.', 'ở trên xe',
          'Gấu ở tầng cao nên gấu ở trên xe. Xe dưới gấu và gấu trên xe cùng mô tả đúng một cách xếp.')],
        [('Vị trí của xe so với gấu','ở dưới gấu'),('Vị trí của gấu so với xe','ở trên xe')],
        ['Đọc rõ đồ vật nào ở tầng cao và đồ vật nào ở tầng thấp.','Mỗi câu dùng một đồ làm mốc khác nhau.'],
        [('Câu hỏi đầu lấy một đồ ở tầng cao làm mốc.','Em đang nói vị trí của đồ vật nào trong câu đầu?'),
         ('Sang câu thứ hai, đổi đồ làm mốc rồi nói lại quan hệ.','Đổi mốc có làm các đồ vật thật sự đổi chỗ không?'),
         ('Hai câu phải diễn tả cùng một cách xếp ở hai tầng.','Hai câu trả lời của em có khớp nhau khi đổi mốc không?')])

    add('queue_front_middle_back','current_g1_spatial_orientation','core_03',
        'Ba bạn xếp hàng, cùng quay mặt về cửa. Từ gần cửa nhất đến xa cửa nhất là An, Bình, Chi. Không ai đổi chỗ. Ai ở giữa hàng? Ai đứng ngay trước Bình và ai đứng ngay sau Bình?',
        ['Tất cả cùng quay mặt về cửa.','Từ gần cửa đến xa cửa: An, Bình, Chi.'],
        [('Xác định hai đầu và bạn ở giữa','Bạn ở giữa có một bạn ở phía gần cửa hơn và một bạn ở phía xa cửa hơn.', 'Bình',
          'Thứ tự từ cửa là An, Bình, Chi. Bình có An ở một phía và Chi ở phía còn lại, nên Bình ở giữa.'),
         ('Xét phía trước Bình','Các bạn đều hướng về cửa, nên người liền trước Bình ở phía gần cửa hơn.', 'An',
          'An đứng liền trước Bình theo hướng về cửa.'),
         ('Xét phía sau rồi kiểm lại','Người liền sau Bình ở phía xa cửa hơn.', 'Chi',
          'Chi đứng liền sau Bình. Đọc lại cửa → An → Bình → Chi: Bình ở giữa, An trước Bình, Chi sau Bình.')],
        [('Bạn ở giữa hàng','Bình'),('Bạn ngay trước Bình','An'),('Bạn ngay sau Bình','Chi')],
        ['Hướng nhìn chung về cửa quyết định phía trước của hàng.','Theo dõi thứ tự đã cho; không tự cho các bạn quay mặt hay đổi chỗ.'],
        [('Xác định đầu hàng gần cửa rồi đọc lần lượt về phía xa cửa.','Bạn ở giữa có bạn khác ở mấy phía dọc hàng?'),
         ('Xét hai người đứng liền cạnh bạn được hỏi, theo hướng cả hàng đang quay.','Phía trước của hàng là phía gần hay xa cửa?'),
         ('Kiểm lại ba quan hệ giữa, trước và sau trên cùng một thứ tự.','Nếu đọc từ cửa ra xa, thứ tự em dùng có giữ đúng mô tả không?')])

    add('triangle_by_boundary','current_g1_plane_shapes','core_01',
        'Có ba miếng phẳng, chỉ xét đường bao: miếng A tròn như miệng cốc; miếng B có bốn cạnh thẳng nối kín; miếng C có ba cạnh thẳng nối kín. Miếng nào có dạng hình tam giác? Giải thích từ mô tả.',
        ['A: đường bao tròn như miệng cốc.','B: bốn cạnh thẳng nối kín.','C: ba cạnh thẳng nối kín.'],
        [('Nêu dấu hiệu để chọn','Hình tam giác có ba cạnh thẳng nối kín.', 'ba cạnh thẳng nối kín',
          'Ta xét đường bao và số cạnh thẳng, không chọn theo tên chữ của miếng.'),
         ('Đối chiếu từng miếng','Miếng đúng phải có đủ dấu hiệu vừa nêu.', 'miếng C',
          'A có đường bao tròn; B có bốn cạnh. C có ba cạnh thẳng nối kín, nên miếng C có dạng hình tam giác.')],
        [('Miếng có dạng hình tam giác','miếng C')],
        ['Chỉ dùng mô tả về đường bao của từng miếng.','Đối chiếu dấu hiệu của hình cần tìm, không dựa vào màu hay kích thước.'],
        [('Xét đường bao của các miếng trước.','Hình cần tìm có đường bao cong hay gồm các cạnh thẳng?'),
         ('Với mỗi đường bao thẳng, đếm số cạnh nối kín.','Số cạnh của hình cần tìm là dấu hiệu nào em đã học?'),
         ('So lại toàn bộ dấu hiệu của miếng em chọn với hình tam giác.','Miếng đã chọn có vừa đúng số cạnh vừa kín đường bao không?')])

    add('square_rotated','current_g1_plane_shapes','core_02',
        'Giả sử một miếng giấy là hình vuông, có bốn cạnh bằng nhau và các góc như góc tờ giấy. Ta chỉ xoay nghiêng miếng đó trên bàn, không cắt hay gấp. Sau khi xoay, miếng còn là hình gì? Giải thích vì sao xoay không biến nó thành hình tam giác.',
        ['Ban đầu là hình vuông, bốn cạnh bằng nhau, các góc như góc tờ giấy.','Chỉ xoay trên bàn, không cắt hoặc gấp.'],
        [('Xét điều gì đã thay đổi','Chỉ xoay làm đổi hướng đặt; không làm mất cạnh hay đổi hình dạng miếng.', 'chỉ đổi hướng đặt',
          'Các cạnh và góc vẫn giữ nguyên; không có cạnh nào bị cắt bỏ hay thêm vào.'),
         ('Giữ tên hình theo đặc điểm','Tên hình phụ thuộc hình dạng, không phụ thuộc miếng nằm ngang hay nghiêng.', 'hình vuông',
          'Miếng vẫn là hình vuông. Nó vẫn có bốn cạnh như trước, nên việc xoay không biến nó thành hình tam giác.')],
        [('Tên hình sau khi chỉ xoay','hình vuông')],
        ['Phân biệt đổi hướng đặt với thay đổi hình dạng.','Đề chỉ cho xoay, không cho cắt hay gấp miếng giấy.'],
        [('Chú ý thao tác duy nhất mà đề cho phép.','Khi chỉ xoay, có cạnh nào bị mất đi không?'),
         ('Đối chiếu các cạnh và góc trước với sau thao tác.','Đặc điểm của miếng có thay đổi chỉ vì đặt nghiêng không?'),
         ('Dùng các đặc điểm vẫn giữ để gọi tên hình thay vì nhìn hướng đặt.','Em nên dựa vào hình dạng hay hướng đặt để gọi tên miếng?')])

    add('four_shape_matching','current_g1_plane_shapes','core_03',
        'Bốn thẻ được mô tả như sau: A có đường bao tròn như miệng cốc; B có ba cạnh thẳng nối kín; C có bốn cạnh bằng nhau, các góc như góc tờ giấy; D có bốn góc như góc tờ giấy, hai cạnh dài bằng nhau và hai cạnh ngắn bằng nhau. Ghép mỗi thẻ một lần với các tên quen thuộc: hình tròn, hình tam giác, hình vuông, hình chữ nhật có hai cạnh dài và hai cạnh ngắn.',
        ['A: đường bao tròn như miệng cốc.','B: ba cạnh thẳng nối kín.',
         'C: bốn cạnh bằng nhau, các góc như góc tờ giấy.','D: bốn góc như góc tờ giấy, hai cạnh dài bằng nhau và hai cạnh ngắn bằng nhau.'],
        [('Ghép đường bao tròn và ba cạnh','Hai mô tả này tách được theo đường bao cong hoặc ba cạnh nối kín.', 'A: hình tròn; B: hình tam giác',
          'A có đường bao tròn nên ghép hình tròn. B có ba cạnh thẳng nối kín nên ghép hình tam giác.'),
         ('Đối chiếu hai thẻ bốn cạnh','Trong hai thẻ còn lại, xem bốn cạnh đều bằng nhau hay có hai cạnh dài, hai cạnh ngắn.', 'C: hình vuông; D: hình chữ nhật có hai cạnh dài và hai cạnh ngắn',
          'C có bốn cạnh bằng nhau và các góc như góc tờ giấy nên ghép hình vuông. D có hai cạnh dài, hai cạnh ngắn và bốn góc như góc tờ giấy nên ghép tên hình chữ nhật được yêu cầu.'),
         ('Kiểm các cặp ghép','Mỗi thẻ phải được dùng đúng một lần và khớp mô tả của tên đã chọn.', 'A–tròn; B–tam giác; C–vuông; D–chữ nhật',
          'Đọc lại đủ A, B, C, D và đối chiếu từng đường bao. Không có thẻ nào bị bỏ sót hoặc dùng hai lần.')],
        [('Các cặp ghép','A–tròn; B–tam giác; C–vuông; D–chữ nhật')],
        ['Xét đường bao và đặc điểm cạnh, góc được nêu rõ bằng lời.','Danh sách yêu cầu mỗi thẻ và mỗi tên được dùng một lần.'],
        [('Tách các mô tả theo đường bao cong và đường bao gồm cạnh thẳng.','Em có thể phân biệt những nhóm đường bao nào trước?'),
         ('Trong nhóm cạnh thẳng, xét số cạnh rồi so đặc điểm các cạnh ở những thẻ còn lại.','Hai thẻ bốn cạnh được mô tả khác nhau ở điểm nào?'),
         ('Đọc ngược từ mỗi tên đã ghép về mô tả để kiểm đủ và đúng.','Có thẻ nào bị lặp hoặc chưa được ghép không?')])

    wrong='Vở ở bên phải bút.'
    add('misconception_changed_anchor','current_g1_spatial_orientation',None,
        'Theo chiều từ trái sang phải trên trang là: bóng, vở, bút. Hỏi vở ở phía nào so với bút. Một bạn trả lời giả định: '+wrong+' Hãy góp ý dựa trên thứ tự đã cho.',
        ['Từ trái sang phải trên trang: bóng, vở, bút.'],
        [('Giữ đúng đồ làm mốc','Câu hỏi lấy bút làm mốc, rồi xác định vở nằm về phía nào của bút.', 'bút là mốc',
          'Ta xét vị trí của vở so với bút, không đổi sang nói vị trí của bút so với vở.'),
         ('Sửa quan hệ trong câu trả lời','Vở xuất hiện trước bút khi đọc từ trái sang phải.', 'bên trái bút',
          'Vở ở bên trái bút, nên câu “Vở ở bên phải bút” chưa đúng. Nếu nói bút ở bên phải vở thì đúng, nhưng đó là câu đổi đồ làm mốc.')],
        [('Vị trí của vở so với bút','bên trái bút')],
        ['Xem câu hỏi chọn đồ vật nào làm mốc.','So câu trả lời được cho với đúng thứ tự trên trang.'],
        [('Giữ nguyên chiều đọc mà đề đã nêu.','Câu hỏi yêu cầu lấy đồ vật nào làm mốc?'),
         ('Tìm vở trong dãy rồi đối chiếu vị trí với đồ làm mốc.','Vở xuất hiện trước hay sau mốc khi đọc theo chiều đã cho?'),
         ('Thử đọc câu đã sửa và kiểm lại quan hệ với cùng một mốc.','Nếu đổi chỗ hai tên đồ vật trong câu, em cần kiểm lại điều gì?')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':wrong,'claim_scope':'The stated right-of relation contradicts the explicit page order; no inference about the pupil hands or actual view.'}]})

    wrong='Miếng này là hình tròn.'
    add('misconception_curve_vs_edges','current_g1_plane_shapes',None,
        'Một miếng phẳng có đường bao là ba đoạn thẳng nối kín, không có đoạn cong. Một bạn ghi câu trả lời giả định: '+wrong+' Hãy góp ý và gọi tên hình phù hợp với mô tả.',
        ['Đường bao có ba đoạn thẳng nối kín, không có đoạn cong.'],
        [('Đối chiếu đường bao','Hình tròn có đường bao cong tròn, khác với đường bao gồm các đoạn thẳng của miếng được mô tả.', 'không khớp tên hình tròn',
          'Câu trả lời hình tròn chưa phù hợp với mô tả không có đoạn cong. Ta cần dùng đặc điểm đường bao để gọi tên.'),
         ('Gọi tên theo các cạnh','Ba cạnh thẳng nối kín tạo đường bao hình tam giác.', 'hình tam giác',
          'Miếng có dạng hình tam giác. Ta sửa tên hình dựa trên ba cạnh đã cho, không dựa vào màu hoặc đoán hình em đã nhìn.')],
        [('Tên hình phù hợp','hình tam giác')],
        ['Đối chiếu lời bạn ghi với đặc điểm đường bao trong đề.','Chỉ dùng những đặc điểm đã được mô tả.'],
        [('Đề nói rõ đường bao không có đoạn cong.','Tên bạn chọn có phù hợp với loại đường bao đó không?'),
         ('Đếm các cạnh thẳng nối thành đường bao kín.','Em đã học hình nào có số cạnh như mô tả?'),
         ('Kiểm tên em chọn bằng cả loại cạnh và số cạnh.','Lý do em dùng có xuất phát từ chính mô tả của đề không?')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':wrong,'claim_scope':'Shape name conflicts with the explicitly described boundary; no claim of seeing a real drawing.'}]})

    add('guard_no_spatial_frame','current_g1_spatial_orientation',None,
        'Em hỏi cốc ở bên trái hay bên phải sách, nhưng chưa gửi ảnh và chưa mô tả cách xếp. Hãy giúp em cung cấp thông tin đủ để trả lời.',[],[],[],
        ['Mình chưa có ảnh hoặc mô tả vị trí của hai đồ vật.','Em gửi ảnh rõ, hoặc kể thứ tự từ trái sang phải trên trang có đánh dấu hướng; mình sẽ lấy sách làm mốc.'],
        [('Chưa có dữ kiện về cách xếp nên chưa chọn được phía.','Em có thể gửi ảnh rõ thấy cả cốc và sách không?'),
         ('Nếu chưa gửi ảnh, em có thể mô tả theo một chiều đã xác định.','Từ trái sang phải trên trang, hai đồ vật được xếp theo thứ tự nào?'),
         ('Cần thống nhất chiều đọc và giữ sách làm mốc trước khi gọi vị trí.','Mô tả của em đã nêu rõ chiều và thứ tự hai đồ vật chưa?')],kind='guard')

    add('guard_only_colour','current_g1_plane_shapes',None,
        'Em chỉ nói có một thẻ màu đỏ rồi hỏi thẻ đó là hình vuông, tròn hay tam giác. Chưa có ảnh và chưa mô tả đường bao. Hãy trả lời mà không đoán tên hình từ màu.',
        ['Thẻ có màu đỏ; chưa biết đường bao.'],[],[],
        ['Màu đỏ không xác định thẻ thuộc hình nào.','Em gửi ảnh hoặc mô tả đường bao cong hay thẳng và các cạnh của thẻ để mình cùng gọi tên.'],
        [('Nhiều hình khác nhau đều có thể tô cùng một màu.','Em có thể gửi ảnh nhìn rõ đường bao thẻ không?'),
         ('Nếu kể bằng lời, mô tả đường bao sẽ giúp phân biệt các hình.','Đường bao của thẻ cong tròn hay gồm các cạnh thẳng?'),
         ('Với đường bao thẳng, cần thêm số cạnh và đặc điểm của chúng.','Em có thể mô tả đủ các cạnh và góc của thẻ không?')],kind='guard')
    return rows,nodes


def main():
    path=DEFAULT_ROOT/'authored_batches/g1_geometry_0004.jsonl'
    if path.exists():print('Batch exists; resume review, do not create duplicates.');return
    rows,nodes=build();assert len(rows)==10
    _,questions,_=protections()
    for r in rows:
        m=inspect_case(r);assert m['passed'],(r['sample_id'],m)
        assert mapping_error(r,nodes) is None
        assert normalized(r['problem']) not in questions
    write_rows(path,rows)
    write_json(HERE/'evidence/primary_math_teacher_20261016/g1_geometry_0004_author_checks.json',
        {'batch_sha256':sha(path.read_bytes()),'authored':10,'content_review_status':'PENDING_SEPARATE_CONTENT_PASS',
         'all_steps_categorical':True,'actual_image_supplied':False,'training_started':False,'skills_matched':'none'})
    print(json.dumps({'authored':10,'batch_sha256':sha(path.read_bytes()),'review_pending':True}))


if __name__=='__main__':main()

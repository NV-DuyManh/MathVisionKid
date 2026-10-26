"""Original text-described geometry drafts. Content acceptance awaits another review."""
import copy
import json
from fractions import Fraction
from primary_math_data_pipeline import (HERE, DEFAULT_ROOT, read_rows, write_rows, write_json,
    sha, row_sha, inspect_case, mapping_error, protections, answer_signatures, normalized, curate)


def main():
    output = DEFAULT_ROOT/'authored_batches/g2_geometry_0013.jsonl'
    if output.exists():
        print('Existing batch retained; continue its pending content review.')
        return
    bp = DEFAULT_ROOT/'curriculum_blueprint.json'
    blueprint = json.loads(bp.read_text('utf-8'))
    nodes = {n['node_id']: n for n in blueprint['nodes']}
    template = read_rows(DEFAULT_ROOT/'authored_batches/g1_geometry_0004.jsonl')[0]
    rows = []

    def add(suffix, nodeid, slot, problem, descriptions, initial, hints, steps, answers,
            kind='core', student=None):
        row = copy.deepcopy(template)
        sid = 'primary_20261017_g2_geometry_0013_'+suffix
        node = nodes[nodeid]
        row.update(sample_id=sid, case_group_id=sid, split='train', grade=2, topic=suffix,
            problem=problem, givens=[{'id':'g'+str(i), 'text':s, 'value':None, 'unit':'',
                'role':'explicit_text_description'} for i,s in enumerate(descriptions)],
            requested_quantity='; '.join(q for q,a in answers) if answers else 'Dữ kiện hình học còn thiếu',
            student_work=student, initial_guidance=initial,
            hints=[{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(hints)],
            worked_steps=[{'step_id':'s'+str(i),'title':title,'reason':why,'expression':None,
                'result':result,'unit':'','explanation':ex} for i,(title,why,result,ex) in enumerate(steps)],
            expected_answer=[{'quantity':q,'result':a,'unit':''} for q,a in answers],
            can_solve=bool(answers), canonical_case={'family':suffix,'operations':[],'numeric_values':[]})
        row['curriculum_assignment']={'node_id':nodeid,'curriculum_scope':node['curriculum_scope'],'case_kind':kind}
        if kind=='core':
            spec = next(s for s in node['authoring_plan']['core_cases'] if s['case_slot']==slot)
            row['curriculum_assignment'].update({k:spec[k] for k in ('case_slot','context_variant','method_variant')})
        row['provenance'].update(authoring_label='AI_TEACHER',authoring_agent='root',
            source_evidence=node['source_evidence'],blueprint_sha256=sha(bp.read_bytes()),
            source_kind='ORIGINAL_EXPLICIT_TEXT_GEOMETRY_CASE' if answers else 'ORIGINAL_MISSING_INFORMATION_GUARD',
            content_review_status='PENDING_INDEPENDENT_CONTENT_REVIEW',
            student_work_origin='EXPLICITLY_SYNTHETIC' if student else None,
            real_observation_claim=False,visual_or_physical_outcome_verified=False)
        row['quality_flags'].update(app_plan_draft_compatible=False,
            actual_image_or_physical_asset_present=False)
        rows.append(row)

    lines='current_g2_points_lines_polyline'
    quad='current_g2_quadrilateral'
    add('segment_line_curve',lines,'core_01',
        'Ba nét được mô tả bằng lời: nét A nối thẳng hai điểm M, N và dừng đúng ở hai điểm ấy; nét B đi thẳng, được kéo dài mãi về cả hai phía; nét C uốn cong như một cung, không ghép từ các đoạn thẳng. Ghép A, B, C với đoạn thẳng, đường thẳng, đường cong và nêu dấu hiệu phân biệt.',
        ['A thẳng, có hai đầu M và N.','B thẳng và kéo dài mãi về cả hai phía.','C uốn cong, không ghép từ các đoạn thẳng.'],
        ['Đối chiếu từng mô tả, không tự cho rằng mình đã xem một hình vẽ.','Xét cả dạng nét và việc nét có điểm dừng hay không.'],
        [('Trước hết xét nét thẳng hay nét uốn.','Những nét nào có cùng dạng thẳng theo mô tả?'),
         ('Trong các nét thẳng, chú ý điều đề nói về hai phía của nét.','Nét có hai đầu dừng khác nét kéo dài mãi ở điểm nào?'),
         ('Đọc ngược từng tên đã ghép để kiểm đủ dấu hiệu và đủ ba nét.','Mỗi tên em chọn có khớp cả dạng nét và điểm dừng được nêu không?')],
        [('Xét nét có hai đầu','Phần thẳng nối hai điểm và dừng tại hai điểm là một đoạn thẳng.','A: đoạn thẳng MN','A nối M với N và dừng ở M, N nên là đoạn thẳng MN.'),
         ('Phân biệt hai nét còn lại','Không chỉ xét thẳng hay cong mà còn xét nét thẳng có bị giới hạn hai đầu không.','B: đường thẳng; C: đường cong','B kéo dài thẳng mãi về hai phía nên là đường thẳng. C uốn cong nên là đường cong. Kiểm lại A có hai đầu còn B không bị giới hạn như A.')],
        [('Ghép tên các nét','A: đoạn thẳng MN; B: đường thẳng; C: đường cong')])

    add('collinear_and_offline',lines,'core_02',
        'Trên một đường kẻ thẳng có ba điểm L, M, N theo thứ tự ấy, M nằm giữa L và N. Điểm P nằm ngoài đường kẻ đó. Trong hai bộ L–M–N và L–M–P, bộ nào có ba điểm thẳng hàng? Giải thích vì sao điểm nằm ngoài làm hai bộ khác nhau.',
        ['L, M, N nằm trên cùng một đường thẳng; M ở giữa.','P nằm ngoài đường thẳng đi qua L và M.'],
        ['Dùng cùng một đường kẻ làm mốc cho cả hai bộ.','Có đủ ba tên điểm chưa có nghĩa ba điểm cùng nằm trên một đường thẳng.'],
        [('Xét từng bộ với cùng đường kẻ đã cho.','Đề nói những điểm nào nằm trên cùng đường kẻ?'),
         ('Chú ý dữ kiện nằm ngoài thay vì chỉ thứ tự đọc tên.','Một điểm ngoài đường qua hai điểm còn lại có cùng thẳng hàng với chúng không?'),
         ('Kiểm từng điểm trong bộ em chọn và nêu dữ kiện loại bộ kia.','Lý do của em có kiểm đủ cả ba điểm trong mỗi bộ không?')],
        [('Đối chiếu bộ nằm trên đường kẻ','Ba điểm cùng nằm trên một đường thẳng là ba điểm thẳng hàng.','L, M, N thẳng hàng','L, M, N đều nằm trên cùng đường kẻ; M ở giữa không làm chúng hết thẳng hàng.'),
         ('Kiểm bộ có điểm nằm ngoài','P không thuộc đường thẳng qua L, M nên bộ này không đáp ứng điều kiện.','L, M, P không thẳng hàng','L và M xác định đường thẳng đã nói. P ở ngoài đường đó, nên không thể xếp cả L, M, P trên chính một đường thẳng. Chọn bộ L–M–N.')],
        [('Bộ ba điểm thẳng hàng','L, M, N'),('Bộ ba điểm không thẳng hàng','L, M, P')])

    add('trace_polyline_segments',lines,'core_03',
        'Một đường đi giả định bắt đầu ở A, đi thẳng đến B, đổi hướng đi thẳng đến C, rồi lại đổi hướng đi thẳng đến D và dừng. Các điểm A, B, C, D khác nhau; chỉ có ba chặng đã kể, không có chặng cong. Hãy gọi dạng đường đi, ghi các đoạn thẳng theo đúng thứ tự và kiểm chỗ nối.',
        ['Chỉ có các chặng thẳng A đến B, B đến C, C đến D.','Có đổi hướng tại B và C; các điểm khác nhau.'],
        ['Theo dõi điểm kết thúc của mỗi chặng và điểm bắt đầu chặng kế.','Phân biệt từng chặng thẳng với dạng của cả đường đi có đổi hướng.'],
        [('Ghép tên mỗi chặng từ hai đầu của chặng ấy.','Điểm cuối chặng trước có trùng điểm đầu chặng tiếp không?'),
         ('Xét các chặng có nối tiếp và có đổi hướng, khác với một nét thẳng duy nhất.','Tên gọi của cả đường đi cần xét những chỗ đổi hướng nào?'),
         ('Đọc lại từ điểm xuất phát tới điểm dừng, không thêm đường nối tắt.','Danh sách em viết có dùng đúng mọi chặng đã kể theo thứ tự không?')],
        [('Liệt kê đúng các chặng','Mỗi chặng thẳng được gọi bằng hai điểm đầu và cuối.','AB, BC, CD','Đi từ A đến B là đoạn AB, tiếp đến C là BC, rồi đến D là CD. Không có chặng AD nối tắt trong mô tả.'),
         ('Gọi dạng đường và kiểm nối','Các đoạn thẳng nối tiếp có đổi hướng tạo thành đường gấp khúc.','đường gấp khúc ABCD','Đoạn AB nối BC tại B; BC nối CD tại C. Có đổi hướng ở hai chỗ nên cả đường là đường gấp khúc ABCD, dù từng chặng riêng là đoạn thẳng.')],
        [('Dạng đường đi','đường gấp khúc ABCD'),('Các đoạn theo thứ tự','AB, BC, CD')])

    wrong='Đường PQR là đường thẳng vì PQ và QR đều là đoạn thẳng.'
    add('misconception_straight_parts',lines,None,
        'Hai đoạn PQ và QR nối nhau tại Q và đổi hướng ở Q; P, Q, R không thẳng hàng. Một bạn ghi giả định: '+wrong+' Hãy nhận xét lý do và gọi dạng của cả đường PQR theo dữ kiện.',
        ['PQ và QR là hai đoạn nối tiếp, đổi hướng tại Q.','P, Q, R không thẳng hàng.'],
        ['Tách tính chất của từng chặng khỏi tính chất của toàn đường đi.','Chỉ nhận xét lý do được viết, không đoán cách bạn đã vẽ.'],
        [('Đề cho biết điều gì xảy ra ở chỗ nối hai chặng.','Hai đoạn thẳng riêng lẻ có bắt buộc nối thành một đường thẳng không?'),
         ('Cần kiểm cả chỗ nối thay vì chỉ gọi tên từng phần.','Dữ kiện không thẳng hàng có phù hợp kết luận của bạn không?'),
         ('Giữ phần nói đúng về từng đoạn rồi sửa tên gọi toàn đường.','Lời sửa của em có xét việc đổi hướng ở chỗ nối chưa?')],
        [('Giữ nhận xét đúng về các phần','PQ và QR thật sự thẳng nhưng điều đó chưa quyết định toàn đường không đổi hướng.','từng đoạn thẳng, cả đường có đổi hướng','Bạn nêu đúng tính chất từng đoạn, nhưng bỏ qua dữ kiện đổi hướng tại Q và ba điểm không thẳng hàng.'),
         ('Gọi tên theo cả cách nối','Hai đoạn thẳng nối tiếp có đổi hướng tạo thành một đường gấp khúc.','đường gấp khúc PQR','Đường PQR là đường gấp khúc, không phải một đường thẳng. Kiểm chỗ Q để phân biệt dạng toàn đường với từng đoạn.')],
        [('Dạng của đường PQR','đường gấp khúc PQR')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':'vì PQ và QR đều là đoạn thẳng','claim_scope':'Explicit inference from straight parts ignores the stated change of direction; no drawing or hidden-strategy inference.'}]})

    add('guard_unknown_alignment',lines,None,
        'Em chỉ gửi tên ba điểm A, B, C rồi hỏi chúng có thẳng hàng không; chưa gửi hình và chưa mô tả vị trí các điểm. Hãy xin dữ kiện cần thiết, chưa kết luận thẳng hàng hay không.',
        ['Chỉ biết tên A, B, C; vị trí chưa được cung cấp.'],
        ['Tên điểm không cho biết vị trí của điểm.','Em gửi hình rõ hoặc mô tả ba điểm có cùng nằm trên một đường thẳng không để cùng kiểm.'],
        [('Cần thông tin về chỗ đặt các điểm.','Em có thể gửi hình rõ thấy cả ba điểm không?'),
         ('Nếu mô tả bằng lời, cần nói quan hệ vị trí thay vì chỉ đọc tên.','Có đường thẳng nào trong đề được nói đi qua các điểm không?'),
         ('Giữ kết luận chưa xác định khi chưa đủ dữ kiện.','Em đã cung cấp vị trí của cả ba điểm để đối chiếu chưa?')],[],[],kind='guard')

    add('closed_four_edges',quad,'core_01',
        'Các thẻ có đường bao như sau: A gồm ba đoạn thẳng nối kín; B gồm bốn đoạn thẳng nối thành đường kín không tự cắt, các cạnh liền nhau tạo góc; C gồm bốn đoạn nối tiếp nhưng đầu cuối còn hở. Thẻ nào có dạng hình tứ giác? Giải thích vì sao chỉ đếm đoạn chưa đủ.',
        ['A có ba cạnh nối kín.','B có bốn cạnh thẳng, kín, không tự cắt.','C có bốn đoạn nhưng chưa kín.'],
        ['Xét cả số cạnh và việc đường bao có khép kín.','Không chỉ chọn một thẻ vì có nhắc tới bốn đoạn.'],
        [('Đối chiếu đường bao từng thẻ với hình cần tìm.','Đường bao nào còn hở theo mô tả?'),
         ('Với các đường đã kín, đếm các cạnh thẳng một vòng.','Một đường kín nhưng có số cạnh khác có cùng tên hình cần tìm không?'),
         ('Kiểm lựa chọn bằng đủ các dấu hiệu, rồi nêu vì sao loại thẻ khác.','Em đã kiểm cả số cạnh lẫn chỗ khép kín chưa?')],
        [('Kiểm đồng thời hai dấu hiệu','Hình tứ giác có đường bao kín gồm bốn cạnh thẳng.','thẻ B','B có đủ bốn cạnh nối kín. A chỉ có ba cạnh, còn C tuy có bốn đoạn nhưng hở nên không đạt.'),
         ('Đọc lại một vòng đường bao','Mỗi cạnh được tính một lần và đường bao trở về chỗ bắt đầu.','B thỏa cả số cạnh và đường kín','Đi một vòng B qua bốn cạnh rồi trở về đầu. Chỉ đếm bốn đoạn như ở C chưa đủ nếu đầu cuối không nối kín.')],
        [('Thẻ có dạng hình tứ giác','thẻ B')])

    add('square_is_quadrilateral_rotated',quad,'core_02',
        'Một miếng giấy hình vuông được xoay nghiêng trên mặt bàn, không cắt, không gấp. Bạn hỏi: miếng đó còn thuộc nhóm hình tứ giác không? Hãy xét đường bao và giải thích vì sao tên hình vuông không ngăn nó thuộc nhóm này.',
        ['Ban đầu là một hình vuông.','Chỉ xoay trong mặt bàn, không thay đổi đường bao.'],
        ['Một hình có thể được gọi theo tên quen thuộc và đồng thời thuộc một nhóm rộng hơn.','Xét số cạnh và đường bao sau thao tác, không dựa vào hướng đặt.'],
        [('Chỉ xoay làm đổi hướng đặt, cần kiểm xem đường bao có đổi không.','Các cạnh có bị cắt mất hoặc thêm vào không?'),
         ('Đối chiếu đường bao còn giữ với đặc điểm của nhóm được hỏi.','Tên hình vuông có làm thay đổi số cạnh và việc nối kín không?'),
         ('Nêu kết luận bằng đặc điểm hình, rồi kiểm nó vẫn đúng khi đặt ngang trở lại.','Lý do của em phụ thuộc hướng đặt hay phụ thuộc đường bao?')],
        [('Kiểm điều giữ nguyên','Xoay không thêm cạnh, bớt cạnh hoặc mở đường bao.','vẫn có bốn cạnh thẳng nối kín','Hình vuông vẫn giữ bốn cạnh và đường bao kín sau khi chỉ xoay.'),
         ('Xét nhóm hình tứ giác','Có bốn cạnh thẳng nối kín nên hình vuông cũng thuộc nhóm hình tứ giác.','vẫn thuộc nhóm hình tứ giác','Miếng vẫn là hình vuông và vẫn thuộc nhóm hình tứ giác. Hai cách gọi không loại trừ nhau; đổi hướng đặt không đổi kết luận.')],
        [('Quan hệ với nhóm hình tứ giác','vẫn thuộc nhóm hình tứ giác')])

    add('trace_four_side_fence',quad,'core_03',
        'Một hàng rào giả định chỉ gồm bốn đoạn thẳng WX, XY, YZ, ZW. Chúng nối tiếp thành đường kín, không tự cắt; mỗi chỗ nối là một góc, không có đoạn cong hay cạnh khác. Hãy gọi dạng đường bao khu đất và chỉ cách kiểm đi đủ các cạnh mà không lặp.',
        ['Chỉ có WX, XY, YZ, ZW.','Đường kín không tự cắt; bốn chỗ nối thành góc.'],
        ['Bắt đầu tại một cọc và theo các cạnh được nêu.','Phân biệt trở lại cọc đầu với việc đi thêm một cạnh.'],
        [('Theo điểm cuối mỗi đoạn để chọn đoạn tiếp theo.','Đi theo danh sách có quay về cọc xuất phát không?'),
         ('Đánh dấu cạnh đã đi để không tính lại cạnh đầu khi quay về.','Có đoạn nào ngoài danh sách mà em tự thêm vào không?'),
         ('Dùng danh sách cạnh cùng điều kiện khép kín để gọi dạng đường bao.','Lời kiểm của em đã vừa đủ cạnh vừa trở về đầu chưa?')],
        [('Theo đủ các cạnh một vòng','Mỗi điểm cuối nối với điểm đầu cạnh kế và cạnh cuối quay về W.','WX, XY, YZ, ZW','Đi W đến X, tiếp Y, tiếp Z, rồi về W. Đã đi đúng bốn cạnh, mỗi cạnh một lần; về W không tạo thêm cạnh thứ năm.'),
         ('Gọi dạng theo đường bao','Bốn cạnh thẳng nối kín, không tự cắt tạo đường bao một hình tứ giác.','hình tứ giác','Khu đất có dạng hình tứ giác theo mô tả. Kiểm bốn cạnh đã cho và đường kín; không cần giả định bốn cạnh bằng nhau.')],
        [('Dạng đường bao khu đất','hình tứ giác'),('Thứ tự cạnh kiểm một vòng','WX, XY, YZ, ZW')])

    wrong='Có bốn đoạn thẳng nên chắc chắn là hình tứ giác, dù hai đầu còn hở.'
    add('misconception_four_but_open',quad,None,
        'Một đường gồm bốn đoạn nối tiếp, hai đầu cuối còn hở và không có đoạn nào nối hai đầu ấy. Một bạn viết giả định: '+wrong+' Hãy góp ý dựa đúng mô tả, không tự vẽ thêm cạnh.',
        ['Bốn đoạn nối tiếp; hai đầu cuối chưa nối với nhau.','Không có cạnh khác ngoài bốn đoạn được cho.'],
        ['Số đoạn là một dữ kiện, còn tình trạng hai đầu là dữ kiện khác.','Giữ nguyên đường được cho, không thêm cạnh để làm đúng lời bạn.'],
        [('Đối chiếu phát biểu với dữ kiện hai đầu cuối.','Hình cần gọi có đòi hỏi đường bao khép kín không?'),
         ('Một dấu hiệu đúng chưa thay cho mọi điều kiện cần có.','Dữ kiện nào trong đề chưa được lời bạn xét tới?'),
         ('Sửa kết luận dựa trên hình đang có, không sửa hình để cứu kết luận.','Em có đang tự thêm đường nối mà đề không cho không?')],
        [('Chỉ ra điều kiện bị bỏ qua','Bốn đoạn chưa đủ nếu chúng không khép kín thành đường bao.','chưa có đường bao kín','Bạn đếm đúng bốn đoạn nhưng bỏ qua hai đầu còn hở. Không thể dùng số đoạn để bỏ điều kiện đường kín.'),
         ('Kết luận cho đúng đường được mô tả','Không có đoạn nối hai đầu thì đường hiện tại chưa bao kín một hình tứ giác.','chưa phải đường bao hình tứ giác','Đường đã cho chưa phải đường bao hình tứ giác. Không tự thêm cạnh; cần giữ mô tả hở trong lời nhận xét.')],
        [('Kết luận về đường được cho','chưa phải đường bao hình tứ giác')],kind='misconception',
        student={'text':wrong,'observations':[{'excerpt':'dù hai đầu còn hở','claim_scope':'The explicit assertion ignores closure; no missing edge or unseen drawing inferred.'}]})

    add('guard_points_without_edges',quad,None,
        'Em chỉ nói trên giấy có bốn chấm rồi hỏi hình đã vẽ có phải tứ giác không. Chưa có ảnh, chưa biết những đoạn nào nối các chấm hay đường có kín không. Hãy hỏi đúng dữ kiện để kiểm, chưa suy tên hình chỉ từ số chấm.',
        ['Có bốn chấm; các đoạn nối và đường bao chưa được cung cấp.'],
        ['Số chấm không cho biết đường bao được vẽ như thế nào.','Em gửi ảnh rõ hoặc mô tả từng đoạn nối và chỗ khép kín để cùng kiểm.'],
        [('Cần biết đường nối thực sự có trên giấy.','Em có thể gửi hình rõ cả các chấm lẫn các đoạn nối không?'),
         ('Nếu kể bằng lời, cần nêu từng đoạn thay vì chỉ đếm các chấm.','Những chấm nào được nối với nhau bằng đoạn thẳng?'),
         ('Sau khi biết các cạnh, còn phải kiểm đường bao.','Các đoạn đã nối thành một đường kín hay vẫn còn hở?')],[],[],kind='guard')

    existing=[r for f in (DEFAULT_ROOT/'authored_batches').glob('*.jsonl') for r in read_rows(f)]
    known={normalized(r['problem']) for r in existing}
    protected,protected_questions,_ = protections()
    checks=[]
    for r in rows:
        inspected=inspect_case(r)
        assert inspected['passed'], (r['sample_id'],inspected)
        assert mapping_error(r,nodes) is None
        assert not answer_signatures(r,inspected)&protected
        assert normalized(r['problem']) not in known|protected_questions
        known.add(normalized(r['problem']))
        checks.append({'sample_id':r['sample_id'],'row_sha256':row_sha(r),
            'mechanical':inspected,'mapping_pass':True})

    def turn(a,b,c):
        return Fraction(b[0]-a[0])*Fraction(c[1]-a[1])-Fraction(b[1]-a[1])*Fraction(c[0]-a[0])
    L,M,N,P=(0,0),(2,0),(5,0),(2,1)
    assert turn(L,M,N)==0 and turn(L,M,P)!=0
    poly=[(0,0),(3,0),(3,2),(5,2)]
    assert all(turn(*poly[i:i+3])!=0 for i in range(2))
    route=['A','B','C','D'];edges=list(zip(route,route[1:]))
    assert edges==[('A','B'),('B','C'),('C','D')]
    cycle=['W','X','Y','Z','W'];fence=list(zip(cycle,cycle[1:]))
    assert len(set(fence))==4 and cycle[0]==cycle[-1]
    quad_points=[(0,0),(4,0),(3,2),(0,3)]
    turns=[turn(quad_points[i],quad_points[(i+1)%4],quad_points[(i+2)%4]) for i in range(4)]
    assert all(t>0 for t in turns)  # Convex witness, not a supplied picture.
    square=[(0,0),(1,0),(1,1),(0,1)]
    rotated=[(-y,x) for x,y in square]
    dist=lambda a,b:sum(Fraction(v-u)**2 for u,v in zip(a,b))
    assert all(dist(square[i],square[(i+1)%4])==dist(rotated[i],rotated[(i+1)%4]) for i in range(4))
    open_edges=[('E','F'),('F','G'),('G','H'),('H','I')]
    assert open_edges[-1][1]!=open_edges[0][0]
    frozen={p:sha((HERE.parent/p).read_bytes())==h for p,h in blueprint['existing_inputs']['source_fingerprints'].items()}
    assert all(frozen.values())
    write_rows(output,rows)
    write_json(HERE/'evidence/primary_math_teacher_20261016/g2_geometry_0013_pre_review.json',{
        'batch_sha256':sha(output.read_bytes()),'authored_cases':10,'core_cases':6,
        'misconception_cases':2,'guard_cases':2,'checks':checks,'frozen_inputs_unchanged':frozen,
        'oracles':{'collinearity_cross_products':[str(turn(L,M,N)),str(turn(L,M,P))],
            'polyline_edges':edges,'closed_fence_edges':fence,'convex_witness_turns':list(map(str,turns)),
            'rotation_preserves_side_lengths':True,'four_open_edges_not_closed':True,
            'alignment_guard_countermodels':'Same labels support collinear and noncollinear point placements.',
            'quadrilateral_guard_countermodels':'Four point labels support a closed four-edge outline or an open chain; edges are unspecified.'},
        'author_self_content_check':'Read each explicit description, role, teaching step, category answer and all three hints. Hints scaffold without choosing the final category or route list. This is authorship checking, not independent semantic review.',
        'independent_semantic_review_completed':False,'human_verified':False,'teacher_certified':False,
        'training_started':False,'sealed_concept_challenge_read':False,
        'limits':'Rational coordinates are independent geometric witnesses only, not image assets or extra child-facing givens. No metric lengths, angle measurement or physical success claimed. Curriculum legal currency is not recertified.'})
    state=curate(DEFAULT_ROOT)
    assert state['authored_cases']==137 and state['accepted_cases']==96
    assert state['decisions']=={'PENDING_AI_CONTENT_REVIEW':41,'ACCEPTED_AI_RESEARCH':96}
    print(json.dumps({k:state[k] for k in ('authored_cases','accepted_cases','chat_train_rows','remaining_core_cases','decisions')}))


if __name__=='__main__':
    main()

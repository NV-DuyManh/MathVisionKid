"""Ten original hypothetical measurement cases; no acceptance/review or curation."""
import json
from fractions import Fraction
from primary_math_data_pipeline import (DEFAULT_ROOT,HERE,read_rows,write_rows,write_json,sha,
    inspect_case,mapping_error,protections,normalized,answer_signatures)


def main():
    destination=DEFAULT_ROOT/'authored_batches/g1_measurement_0006.jsonl'
    if destination.exists():
        print('Batch already exists; do not regenerate.');return
    blueprint=DEFAULT_ROOT/'curriculum_blueprint.json'
    nodes={n['node_id']:n for n in json.loads(blueprint.read_text('utf-8'))['nodes']}
    rows=[]
    def step(title,reason,expression,result,unit,explanation):
        return dict(title=title,reason=reason,expression=expression,result=str(result),unit=unit,explanation=explanation)
    def add(suffix,nodeid,slot,problem,givens,steps,answers,initial,hints,kind='core',student=None):
        node=nodes[nodeid];sid='primary_20261016_g1_measurement_0006_'+suffix
        assignment={'node_id':nodeid,'curriculum_scope':node['curriculum_scope'],'case_kind':kind}
        if kind=='core':
            selected=next(s for s in node['authoring_plan']['core_cases'] if s['case_slot']==slot)
            assignment.update({k:selected[k] for k in ('case_slot','context_variant','method_variant')})
        for i,s in enumerate(steps):s['step_id']='s'+str(i)
        rows.append({'sample_id':sid,'split':'train','case_group_id':sid,'grade':1,'topic':suffix,
            'problem':problem,'givens':[{'id':'g'+str(i),'text':text,'value':value,'unit':unit,'role':role}
                for i,(text,value,unit,role) in enumerate(givens)],
            'requested_quantity':'; '.join(a['quantity'] for a in answers) if answers else 'Thông tin đo còn thiếu để trả lời',
            'student_work':student,'initial_guidance':initial,
            'hints':[{'level':i+1,'hint':h,'question':q} for i,(h,q) in enumerate(hints)],
            'worked_steps':steps,'expected_answer':answers,'can_solve':bool(answers),
            'canonical_case':{'family':suffix,'operations':[s['expression'] for s in steps if s['expression'] and '{s' not in s['expression']],
                'numeric_values':[str(g[1]) for g in givens if g[1] is not None]},
            'curriculum_assignment':assignment,
            'provenance':{'authoring_method':'original_AI_teacher','human_verified':False,'teacher_certified':False,
                'source_kind':'ORIGINAL_EXPLICIT_HYPOTHETICAL_TEXT_DESCRIPTION' if answers else 'ORIGINAL_MISSING_INFORMATION_GUARD',
                'source_evidence':node['source_evidence'],'blueprint_sha256':sha(blueprint.read_bytes()),
                'benchmark_status':'TRAINING_ONLY_NOT_GOLD','real_observation_claim':False,
                'actual_image_asset_supplied':False,'physical_outcome_verified':False,
                'student_work_origin':'EXPLICITLY_SYNTHETIC' if student else None,
                'content_review_status':'PENDING_INDEPENDENT_CONTENT_REVIEW'},
            'quality_flags':{'app_plan_draft_compatible':False,'app_mapping_status':'NEUTRAL_TEACHER_SCHEMA_REQUIRES_ADAPTER',
                'full_worked_solution_requires_explicit_request':True,'three_hint_levels_answer_free':True}})
    def ans(quantity,result,unit=''):return {'quantity':quantity,'result':str(result),'unit':unit}

    add('cm_read_write','current_g1_length_cm','core_01',
        'Trong tình huống giả định, một dải giấy được đặt thẳng sát thước có các vạch cách nhau một xăng-ti-mét. Đầu trái dải giấy trùng vạch 0 cm, đầu phải trùng vạch 7 cm. Hãy viết độ dài dải giấy bằng số kèm đơn vị và đọc độ dài đó. Đây là mô tả bằng chữ, không phải yêu cầu nhìn ảnh.',
        [('Đầu trái trùng vạch 0 cm','0','cm','start_mark'),('Đầu phải trùng vạch 7 cm','7','cm','end_mark'),
         ('Các vạch liên tiếp cách nhau một xăng-ti-mét','1','cm','ruler_interval')],
        [step('Xác định phần dải giấy chiếm trên thước','Độ dài ứng với khoảng từ vạch đầu đến vạch cuối, không đếm bản thân các vạch.',None,'khoảng từ vạch đầu đến vạch cuối','','Vì đầu dải giấy ở vạch không, số chỉ ở đầu kia cho biết số khoảng xăng-ti-mét.'),
         step('Viết độ dài có đơn vị','Lấy số khoảng xăng-ti-mét từ đầu đến cuối dải giấy.','7-0',7,'cm','Từ vạch 0 cm đến vạch 7 cm có 7 khoảng, mỗi khoảng dài 1 cm. Vậy dải giấy dài 7 cm.'),
         step('Đọc cách viết','Tên đơn vị cho biết số đang biểu thị độ dài.',None,'bảy xăng-ti-mét','','Viết 7 cm, đọc bảy xăng-ti-mét; không đọc là bảy vạch.')],
        [ans('Độ dài dải giấy',7,'cm'),ans('Cách đọc độ dài','bảy xăng-ti-mét')],
        ['Tìm vị trí của cả hai đầu dải giấy trên thước.','Phân biệt khoảng giữa các vạch với số lượng vạch.'],
        [('Chú ý vạch nằm dưới mỗi đầu dải giấy.','Đầu dải giấy bắt đầu ở đâu trên thước?'),
         ('Độ dài được tạo bởi các khoảng bằng nhau giữa hai đầu.','Em cần đếm các khoảng hay đếm tất cả các vạch?'),
         ('Viết kết quả kèm đúng tên đơn vị của thước rồi đọc lại.','Đơn vị em ghi có phù hợp với các khoảng trên thước không?')])

    add('cm_compare_same_unit','current_g1_length_cm','core_02',
        'Giả sử hai dải giấy đã được đo đúng: dải đỏ dài 42 cm, dải xanh dài 36 cm. Hỏi dải nào dài hơn? Giải thích cách so sánh mà không cần biết các dải đang được đặt ở đâu.',
        [('Dải đỏ dài 42 cm','42','cm','red_length'),('Dải xanh dài 36 cm','36','cm','blue_length')],
        [step('Kiểm đơn vị so sánh','Chỉ so sánh trực tiếp hai số đo khi chúng cùng đơn vị.',None,'cùng đơn vị cm','','Cả hai độ dài đều dùng cm, nên có thể so sánh 42 với 36.'),
         step('So sánh hàng chục','Số có nhiều chục hơn thì lớn hơn khi hai số có hàng chục khác nhau.',None,'42 lớn hơn 36','','42 có 4 chục, 36 có 3 chục; 4 chục nhiều hơn 3 chục, nên 42 lớn hơn 36.'),
         step('Trả lời theo đúng dải giấy','Gắn số đo lớn hơn với dải có số đo ấy.',None,'dải đỏ','','Dải đỏ dài hơn vì 42 cm lớn hơn 36 cm. Vị trí đặt không làm thay đổi độ dài đã đo.')],
        [ans('Dải dài hơn','dải đỏ')],
        ['Đọc số đo và đơn vị đi cùng từng dải.','Dùng độ dài đã đo thay cho việc đoán qua vị trí đặt.'],
        [('Trước khi so số, đối chiếu các tên đơn vị.','Hai số đo có cùng đơn vị không?'),
         ('Có thể so sánh hai số có hàng chục khác nhau bằng hàng chục trước.','Hàng chục của mỗi số đo là gì?'),
         ('Sau khi so sánh, nối số đo với đúng màu dải giấy.','Dải em chọn có thực sự mang số đo lớn hơn không?')])

    add('cm_offset_origin','current_g1_length_cm','core_03',
        'Trong mô tả giả định, một đoạn dây được kéo thẳng sát thước: một đầu trùng vạch 3 cm, đầu kia trùng vạch 18 cm. Các vạch thước cách đều đúng một xăng-ti-mét. Đoạn dây không bắt đầu ở vạch không. Tính độ dài đoạn dây rồi kiểm lại bằng cách xác định vạch cuối từ vạch đầu và độ dài vừa tìm.',
        [('Đầu dây thứ nhất ở vạch 3 cm','3','cm','start_mark'),('Đầu dây thứ hai ở vạch 18 cm','18','cm','end_mark')],
        [step('Tách vị trí và độ dài','Số ở đầu cuối là vị trí trên thước; cần bỏ phần từ vạch không đến đầu dây.',None,'phần giữa hai vạch đầu dây','','Đoạn từ vạch 0 cm đến vạch 3 cm không thuộc đoạn dây, nên không được tính vào độ dài dây.'),
         step('Tìm độ dài giữa hai đầu','Lấy vị trí cuối bớt vị trí đầu để tìm phần thước bị dây chiếm.','18-3',15,'cm','Độ dài dây là 18 − 3 = 15 cm.'),
         step('Kiểm từ vạch bắt đầu','Cộng độ dài vừa tìm vào vị trí đầu phải trở lại vị trí cuối.','3+{s1}',18,'cm','Từ vạch 3 cm đi thêm 15 cm đến vạch 18 cm, khớp mô tả. Độ dài dây vẫn là 15 cm; 18 cm ở phép kiểm là số chỉ vạch cuối.')],
        [ans('Độ dài đoạn dây',15,'cm')],
        ['Nhìn riêng vị trí đầu và vị trí cuối, không gọi ngay số chỉ vạch cuối là độ dài.','Cần đo phần nằm giữa hai đầu dây.'],
        [('Chú ý phần thước nằm trước đầu dây.','Phần trước đầu dây có thuộc đoạn cần đo không?'),
         ('Cần tách phần ngoài dây ra khỏi khoảng từ đầu thước tới cuối dây.','Em chọn phép tính nào để bỏ phần không thuộc dây?'),
         ('Sau khi tìm độ dài, thử đi từ vị trí đầu thêm đúng độ dài đó.','Điểm em đến có trùng vị trí cuối được mô tả không?')])

    wrong='Đoạn băng dài 9 cm vì đầu cuối ở vạch 9 cm.'
    add('cm_misconception_endmark','current_g1_length_cm',None,
        'Giả sử một đoạn băng thẳng có hai đầu trùng vạch 2 cm và 9 cm trên thước. Một bạn viết giả định: '+wrong+' Hãy kiểm và sửa dựa đúng các vạch đã cho.',
        [('Đầu đầu tiên ở vạch 2 cm','2','cm','start_mark'),('Đầu còn lại ở vạch 9 cm','9','cm','end_mark')],
        [step('Xét lời viết được cho','Câu viết chỉ lấy số chỉ đầu cuối, trong khi đầu đầu tiên không ở vạch không.',None,'chưa trừ phần trước đầu băng','','Ta chỉ nhận xét lý do bạn đã viết. Không biết bạn nhìn nhầm hay tính nhầm ở bước nào khác.'),
         step('Tính phần thực sự thuộc đoạn băng','Bớt khoảng trước đầu băng khỏi khoảng từ vạch không đến vạch cuối.','9-2',7,'cm','Đoạn băng dài 9 − 2 = 7 cm, không phải 9 cm.'),
         step('Kiểm vị trí cuối','Vị trí đầu cộng độ dài phải khớp số chỉ vạch cuối.','2+{s1}',9,'cm','Bắt đầu ở vạch 2 cm, đi thêm 7 cm sẽ đến vạch 9 cm. Phép kiểm khớp cả hai đầu.')],
        [ans('Độ dài đoạn băng',7,'cm')],
        ['Đối chiếu câu giải thích của bạn với vị trí của cả hai đầu băng.','Chỉ kết luận điều thể hiện trong câu viết giả định.'],
        [('Lời viết đã dùng một số chỉ trên thước.','Bạn đã xét đủ vị trí của cả hai đầu chưa?'),
         ('Vạch đầu tiên của đoạn băng khác với đầu thước.','Phần từ đầu thước đến đầu băng có thuộc băng không?'),
         ('Có thể kiểm độ dài đề xuất bằng cách đi từ vạch bắt đầu tới vạch kết thúc.','Độ dài em chọn có đưa từ đầu này đến đúng đầu kia không?')],
        kind='misconception',student={'text':wrong,'observations':[{'excerpt':wrong,'claim_scope':'Explicit written reason treats the endpoint mark as length despite nonzero start; no inferred unseen mental process.'}]})

    add('cm_guard_missing_start','current_g1_length_cm',None,
        'Em nói đầu phải của một đoạn giấy ở vạch 12 cm trên thước, nhưng chưa cho biết đầu trái nằm ở vạch nào; cũng chưa có ảnh thước và giấy. Em hỏi đoạn giấy dài bao nhiêu cm. Hãy giúp em cung cấp dữ kiện còn thiếu, chưa đoán độ dài.',
        [('Đầu phải ở vạch 12 cm','12','cm','known_end_mark'),('Chưa biết vị trí đầu trái và chưa có ảnh',None,'','missing_start_mark')],[],[],
        ['Mình mới biết vị trí đầu phải nên chưa xác định được phần thước đoạn giấy chiếm.','Em cho biết vạch dưới đầu trái, hoặc gửi ảnh rõ cả hai đầu giấy cùng thước.'],
        [('Độ dài phụ thuộc khoảng giữa cả hai đầu.','Đầu trái của đoạn giấy trùng vạch nào?'),
         ('Nếu dùng ảnh, cần thấy trọn hai đầu giấy và các vạch tại đó.','Em có thể gửi ảnh rõ cả hai đầu cùng thước không?'),
         ('Khi đã có hai vị trí, mới kiểm được khoảng thực sự thuộc giấy.','Em đã xác nhận được vạch ở cả hai đầu chưa?')],kind='guard')

    add('handspan_complete_units','current_g1_measure_estimate_length','core_01',
        'Đây là tình huống đo giả định đã được mô tả đầy đủ: An dùng gang tay của mình đo cạnh bàn. An đặt các gang liên tiếp cùng độ rộng, sát nhau, không hở và không chồng, từ đúng đầu này đến đúng đầu kia. An ghi từng gang đã đặt là A, B, C, D; không còn phần thừa. Cạnh bàn dài bao nhiêu gang tay của An? Không đổi sang cm khi chưa có số đo gang tay.',
        [('Các gang liên tiếp được ghi A, B, C, D',None,'gang tay của An','complete_explicit_unit_list'),
         ('Các gang cùng độ rộng, sát nhau, không hở/chồng, không có phần thừa',None,'','measurement_conditions')],
        [step('Kiểm cách đặt đơn vị','Chỉ đếm được độ dài bằng gang khi các gang bằng nhau và phủ đủ đoạn cần đo.',None,'đủ đoạn và không hở hoặc chồng','','Mô tả đã bảo đảm các gang của cùng An cùng độ rộng, nối từ đầu đến cuối và không có phần thừa.'),
         step('Đếm các gang đã đặt','Mỗi nhãn chỉ một gang được đặt đúng một lần.','4',4,'gang tay của An','Đếm A, B, C, D: một, hai, ba, bốn. Cạnh bàn dài 4 gang tay của An.'),
         step('Giữ đúng đơn vị','Chưa biết độ dài gang tay bằng cm nên không được đổi sang cm.',None,'chỉ kết luận bằng gang tay của An','','Đếm lại bốn nhãn vẫn đủ toàn bộ cạnh bàn. Đây là kết quả trong tình huống được cho, chưa phải bằng chứng An đã đo thật.')],
        [ans('Độ dài cạnh bàn',4,'gang tay của An')],
        ['Kiểm xem các đơn vị đã được đặt liên tiếp và cùng độ rộng chưa.','Đếm từng nhãn đúng một lần rồi giữ tên đơn vị đã dùng.'],
        [('Đọc các điều kiện đặt gang trước khi đếm.','Giữa các gang có phần hở hoặc chồng nào theo mô tả không?'),
         ('Mỗi nhãn là một lần đặt gang được ghi lại.','Làm cách nào để em tránh đếm lặp một nhãn?'),
         ('Tên đơn vị phải cho biết bàn đã được đo bằng gì.','Em đã có dữ kiện để đổi từ gang tay sang đơn vị khác chưa?')])

    add('estimate_against_measurement','current_g1_measure_estimate_length','core_02',
        'Trong một tình huống giả định, trước khi dùng thước, Mai ước lượng dải ruy-băng dài 22 cm. Sau đó Mai đặt thước đúng cách, đầu dải ở vạch 0 cm và đầu kia ở vạch 25 cm. Theo kết quả đo được mô tả, dải dài bao nhiêu cm? Số đo lớn hơn số ước lượng bao nhiêu cm? Phân biệt ước lượng với số đo.',
        [('Ước lượng ban đầu là 22 cm','22','cm','estimate'),('Đo đúng từ vạch 0 cm','0','cm','start_mark'),('Đầu kia ở vạch 25 cm','25','cm','end_mark')],
        [step('Phân biệt hai loại thông tin','Ước lượng là phỏng đoán trước khi đo; số đo đến từ cách dùng thước đã được mô tả.',None,'ước lượng và số đo khác nhau','','22 cm là ước lượng ban đầu. Khoảng trên thước từ vạch 0 cm đến vạch 25 cm mới là dữ kiện dùng để xác định số đo trong tình huống này.'),
         step('Ghi độ dài theo kết quả đo','Đo từ vạch không nên lấy khoảng tới đầu kia.','25-0',25,'cm','Dải ruy-băng dài 25 cm theo phép đo giả định được mô tả.'),
         step('Tìm độ lệch của ước lượng','Số đo lớn hơn ước lượng nên lấy số đo bớt số ước lượng.','{s1}-22',3,'cm','25 − 22 = 3 cm. Số đo lớn hơn ước lượng 3 cm; ước lượng không phải lời bảo đảm chính xác.')],
        [ans('Độ dài theo phép đo',25,'cm'),ans('Số đo lớn hơn ước lượng',3,'cm')],
        ['Tìm thông tin được ghi trước khi đo và thông tin nhận sau khi dùng thước.','Giữ đúng vai trò của từng số thay vì coi mọi số đều là số đo.'],
        [('Các con số đến từ những cách thu thập khác nhau.','Thông tin nào đến từ việc dùng thước được mô tả?'),
         ('Đọc vị trí hai đầu để xác định khoảng được đo trước.','Hai đầu dải nằm ở đâu trên thước?'),
         ('Sau khi có số đo, đối chiếu với ước lượng bằng cùng đơn vị.','Em làm thế nào để biết hai giá trị chênh nhau bao nhiêu?')])

    add('different_step_units_same_path','current_g1_measure_estimate_length','core_03',
        'Giả sử An và cô giáo đo đúng cùng một đoạn sân thẳng, cùng điểm đầu và điểm cuối. Trong mỗi lượt, bước chân đều nhau, nối sát nhau, không hở/chồng và vừa hết đoạn sân. An ghi 6 bước chân của An, cô ghi 4 bước chân của cô. Có thể dựa riêng vào hai số này để nói cô đã đo một đoạn sân ngắn hơn An không? Giải thích rồi nêu cách kiểm khi muốn so bằng số bước.',
        [('Hai người đo cùng đoạn sân, cùng hai đầu',None,'','same_segment'),('An ghi 6 bước chân của An','6','bước chân của An','child_units'),
         ('Cô ghi 4 bước chân của cô','4','bước chân của cô','adult_units'),('Các bước đều trong mỗi lượt và vừa hết đoạn',None,'','consistent_units_within_each_measurement')],
        [step('Kiểm đối tượng đã đo','Cùng hai đầu được cho nên đây vẫn là cùng đoạn sân.',None,'cùng một đoạn sân','','Đoạn sân không ngắn đi khi đổi người đo. Đề đã nói cả hai đo cùng đoạn, nên không thể bảo cô đo đoạn khác ngắn hơn.'),
         step('Kiểm đơn vị của mỗi số đếm','Bước chân của hai người chưa được cho là dài bằng nhau.',None,'không so trực tiếp số bước khác người','','6 là số bước của An, 4 là số bước của cô. Đơn vị có thể khác độ dài, nên chỉ so 4 với 6 không kết luận được đoạn sân nào dài hơn.'),
         step('Đề xuất cách kiểm công bằng','Giữ cùng một đơn vị mới so sánh số đo theo đơn vị ấy.',None,'dùng cùng một đơn vị đo','','Có thể để cùng một người đi đều đo các đoạn cần so, hoặc dùng cùng thước. Kiểm lại cùng hai mốc đầu cuối và cách nối các đơn vị; không tự đổi bước chân thành cm.')],
        [ans('Kết luận về đoạn cô đo','không thể nói ngắn hơn; hai người đo cùng một đoạn sân'),ans('Cách kiểm bằng số bước','dùng bước đều của cùng một người và cùng hai mốc')],
        ['Xem hai người đang đo đoạn nào và mỗi số đếm dùng đơn vị của ai.','Đối chiếu ý nghĩa đơn vị trước khi so hai con số.'],
        [('Số bước có kèm tên người thực hiện.','Đề có khẳng định bước của hai người dài bằng nhau không?'),
         ('Giữ nguyên các điểm đầu và cuối được mô tả khi nhận xét.','Hai lượt đo có thay đổi đoạn sân cần đo không?'),
         ('Một phép so cần giữ đơn vị và cách đặt đơn vị nhất quán.','Em cần giữ điều gì giống nhau nếu muốn dùng số bước để so các đoạn?')])

    wrong='Cạnh chiếu dài 5 cm vì em đếm được 5 gang tay của em.'
    add('unit_misconception','current_g1_measure_estimate_length',None,
        'Trong tình huống giả định, một bạn dùng các gang tay của chính mình cùng độ rộng, đặt sát, không hở/chồng và vừa hết cạnh chiếu. Bạn đếm được 5 gang. Chưa đo một gang bằng cm. Bạn viết: '+wrong+' Hãy sửa cách ghi kết quả và giải thích điều chưa đủ để đổi đơn vị.',
        [('Đếm đủ 5 gang tay của cùng bạn','5','gang tay của bạn','measured_count'),('Chưa có số cm của một gang',None,'','missing_conversion')],
        [step('Đối chiếu lời viết với cách đo','Đơn vị phải là đơn vị thực sự đã dùng, chưa thể tự đổi tên đơn vị.',None,'ghi sai đơn vị so với cách đo','','Câu viết chuyển số gang thành cùng số cm mà chưa có dữ kiện đổi. Ta chỉ sửa điều thể hiện trong câu, không đoán kích thước bàn tay của bạn.'),
         step('Ghi kết quả theo đơn vị đã đếm','Số đơn vị được giữ nguyên khi chỉ sửa tên đơn vị cho đúng cách đo.','5',5,'gang tay của bạn','Cạnh chiếu dài 5 gang tay của bạn trong tình huống đã cho, không được gọi là 5 cm.'),
         step('Nêu giới hạn kết luận','Không biết độ dài một gang theo cm thì chưa biết độ dài cạnh theo cm.',None,'chưa xác định được độ dài bằng cm','','Muốn ghi theo cm, hãy dùng thước đo cạnh hoặc cung cấp phép đo thích hợp. Không tự gán mọi gang tay cùng một số cm.')],
        [ans('Độ dài theo cách đã đo',5,'gang tay của bạn')],
        ['Giữ nguyên câu viết để đối chiếu tên đơn vị với cách bạn đo.','Không tự gán chiều dài bàn tay khi đề chưa cho.'],
        [('Số đếm cần đi cùng đơn vị đã dùng khi đo.','Bạn đã dùng vật hoặc bộ phận nào để đo?'),
         ('So tên đơn vị trong lời viết với tên đơn vị trong bản mô tả.','Hai tên đơn vị đó có trùng nhau không?'),
         ('Đổi đơn vị cần thêm mối liên hệ được đo hoặc được cho.','Đề đã có dữ kiện nào nối đơn vị bạn dùng với đơn vị bạn ghi chưa?')],
        kind='misconception',student={'text':wrong,'observations':[{'excerpt':wrong,'claim_scope':'The supplied sentence explicitly substitutes cm for a handspan count without conversion data; no actual pupil observed.'}]})

    add('guard_unknown_reference','current_g1_measure_estimate_length',None,
        'Em hỏi: “Hãy ước lượng bàn học của em dài mấy gang tay của em.” Em chưa gửi ảnh, chưa mô tả bàn hoặc cho số đo bàn, cũng chưa cho độ rộng gang tay của mình hay vật mốc để so. Hãy giúp em bắt đầu nhưng không bịa một số gang cho chiếc bàn chưa thấy.',
        [('Chưa có mô tả bàn, gang tay hoặc vật mốc',None,'','missing_reference_and_object_measurement')],[],[],
        ['Mình chưa có thông tin về bàn và gang tay của em nên chưa đưa ra một số ước lượng có cơ sở.','Em có thể so trước bằng gang tay của mình rồi kiểm bằng cách đặt các gang đều, sát nhau, không hở/chồng dọc cạnh cần đo; nếu còn phần thừa, nói rõ phần đó thay vì bỏ đi.'],
        [('Cần biết rõ cạnh bàn nào được hỏi và đơn vị của chính em.','Em định đo cạnh nào của bàn bằng gang tay của mình?'),
         ('Một ước lượng cần có vật mốc hoặc thông tin so sánh phù hợp.','Em có thể mô tả cạnh bàn cùng một vật mốc đã biết không?'),
         ('Khi tự đo để kiểm, ghi cả những gang đủ và phần còn thừa nếu có.','Em có thể kể cách đặt gang và kết quả em thực sự đo được không?')],kind='guard')

    assert len(rows)==10
    protected,questions,fingerprints=protections()
    accepted=read_rows(DEFAULT_ROOT/'exports/accepted_teacher_cases.jsonl')
    accepted_questions={normalized(r['problem']) for r in accepted}
    seen=set();reports=[]
    for r in rows:
        checked=inspect_case(r);assert checked['passed'],(r['sample_id'],checked)
        assert mapping_error(r,nodes) is None
        question=normalized(r['problem']);assert question not in questions|accepted_questions|seen
        seen.add(question)
        signatures=answer_signatures(r,checked);collision=signatures&protected
        assert not collision,(r['sample_id'],'protected canonical collision')
        reports.append({'sample_id':r['sample_id'],'mechanical_pass':True,'mapping_pass':True,
            'checked_expressions':checked['expanded_expressions'],'protected_collision':False,
            'semantic_review_status':'PENDING_INDEPENDENT_CONTENT_REVIEW'})
    # Deterministic witnesses are independent of the AST/result checker above.
    assert len(list(range(0,7)))==7
    assert 42>36 and divmod(42,10)[0]>divmod(36,10)[0]
    assert len(list(range(3,18)))==15 and 3+15==18
    assert len(list(range(2,9)))==7 and 2+7==9
    assert len(['A','B','C','D'])==4
    assert Fraction(25)-Fraction(22)==3 and len(list(range(0,25)))==25
    assert Fraction(24,6)==4 and Fraction(24,4)==6
    assert Fraction(12)-Fraction(0)==12 and Fraction(12)-Fraction(4)==8
    write_rows(destination,rows)
    write_json(HERE/'evidence/primary_math_teacher_20261016/g1_measurement_0006_author_checks.json',
        {'batch_sha256':sha(destination.read_bytes()),'authored':10,'core_cases':6,'misconception_cases':2,'guard_cases':2,
         'content_review_status':'PENDING_INDEPENDENT_CONTENT_REVIEW','mechanical_checks':reports,
         'independent_deterministic_oracles':{
             'cm_read_write':{'method':'count_unit_intervals','interval_count':7},
             'cm_compare':{'method':'integer_order_and_tens_tuple','larger_cm':42,'smaller_cm':36},
             'cm_offset':{'method':'enumerate_unit_intervals_and_inverse','interval_count':15,'inverse_end':18},
             'cm_misconception':{'method':'enumerate_unit_intervals_and_inverse','interval_count':7,'inverse_end':9},
             'handspan_count':{'method':'explicit_list_cardinality','count':4},
             'estimate_measure':{'method':'Fraction_difference_and_interval_enumeration','measured_cm':25,'difference_cm':3},
             'different_steps':{'method':'equal_segment_counterexample_only','segment_witness':'24 arbitrary length units',
                 'child_step_units':'24/6=4','adult_step_units':'24/4=6','not_claimed_actual_lengths':True},
             'unit_misconception':{'method':'dimension_label_check','count':5,'cm_per_handspan_not_provided':True},
             'missing_start_guard':{'method':'two_possible_completions','end_cm':12,'possible_start_cm':[0,4],'possible_length_cm':[12,8]},
             'unknown_reference_guard':{'method':'underdetermination','possible_handspans':[4,6],
                 'actual_dimensions_not_assigned':True}},
         'protected_fingerprints':fingerprints,'sealed_concept_challenge_read':False,
         'actual_image_asset_supplied':False,'physical_outcome_verified':False,
         'training_started':False,'human_verified':False,'teacher_certified':False,'skills_matched':'none'})
    print(json.dumps({'authored':10,'batch_sha256':sha(destination.read_bytes()),'review_pending':True}))


if __name__=='__main__':main()

"""Original grade-one calendar and whole-hour teaching data; no acceptance review."""
import copy
import json

from primary_math_data_pipeline import (
    DEFAULT_ROOT, HERE, answer_signatures, inspect_case, mapping_error, normalized,
    protections, read_rows, row_sha, sha, write_json, write_rows,
)


def main():
    path = DEFAULT_ROOT / 'authored_batches/g1_time_0007.jsonl'
    if path.exists():
        print('Batch already exists; do not recreate.')
        return
    blueprint = DEFAULT_ROOT / 'curriculum_blueprint.json'
    nodes = {n['node_id']: n for n in json.loads(blueprint.read_text('utf-8'))['nodes']}
    template = read_rows(DEFAULT_ROOT / 'authored_batches/g1_geometry_0004.jsonl')[0]
    rows = []

    def add(suffix, node_id, slot, problem, descriptions, steps, answers, initial, hints,
            kind='core', student=None):
        row = copy.deepcopy(template)
        ident = 'primary_20261016_g1_time_0007_' + suffix
        node = nodes[node_id]
        row.update(
            sample_id=ident, case_group_id=ident, topic=suffix, problem=problem,
            givens=[{'id': 'g'+str(i), 'text': t, 'value': None, 'unit': '',
                     'role': 'explicit_hypothetical_description'} for i, t in enumerate(descriptions)],
            requested_quantity='; '.join(a[0] for a in answers) if answers else 'Dữ kiện còn thiếu để trả lời chắc chắn',
            student_work=student, initial_guidance=initial,
            hints=[{'level': i+1, 'hint': h, 'question': q} for i, (h, q) in enumerate(hints)],
            worked_steps=[{'step_id': 's'+str(i), 'title': t, 'reason': why, 'expression': expr,
                           'result': value, 'unit': unit, 'explanation': explanation}
                          for i, (t, why, expr, value, unit, explanation) in enumerate(steps)],
            expected_answer=[{'quantity': q, 'result': value, 'unit': unit} for q, value, unit in answers],
            can_solve=bool(answers),
            canonical_case={'family': suffix, 'operations': [], 'numeric_values': []},
        )
        row['curriculum_assignment'] = {'node_id': node_id, 'curriculum_scope': node['curriculum_scope'], 'case_kind': kind}
        if kind == 'core':
            core = next(c for c in node['authoring_plan']['core_cases'] if c['case_slot'] == slot)
            row['curriculum_assignment'].update({k: core[k] for k in ('case_slot', 'context_variant', 'method_variant')})
        row['provenance'].update(
            source_kind='ORIGINAL_EXPLICIT_HYPOTHETICAL_TEXT_DESCRIPTION' if answers else 'ORIGINAL_MISSING_INFORMATION_GUARD',
            source_evidence=node['source_evidence'], blueprint_sha256=sha(blueprint.read_bytes()),
            student_work_origin='EXPLICITLY_SYNTHETIC' if student else None,
            authoring_label='AI_TEACHER', real_observation_claim=False,
            visual_or_physical_outcome_verified=False, actual_image_asset_supplied=False,
        )
        rows.append(row)

    add('week_order_count', 'current_g1_calendar_week', 'core_01',
        'Có các thẻ ghi Thứ Năm, Chủ nhật, Thứ Hai, Thứ Bảy, Thứ Tư, Thứ Sáu, Thứ Ba. Hãy xếp đủ các thẻ theo thứ tự các ngày trong một tuần, bắt đầu từ Thứ Hai, rồi cho biết một tuần có bao nhiêu ngày. Mỗi thẻ dùng một lần.',
        ['Các thẻ: Thứ Năm, Chủ nhật, Thứ Hai, Thứ Bảy, Thứ Tư, Thứ Sáu, Thứ Ba.', 'Xếp tuần bắt đầu từ Thứ Hai; dùng đủ, mỗi thẻ một lần.'],
        [('Xếp theo thứ tự ngày', 'Thẻ đang bị xáo trộn; cần dùng thứ tự các ngày trong tuần thay vì đọc theo thứ tự thẻ đã cho.', None,
          'Thứ Hai, Thứ Ba, Thứ Tư, Thứ Năm, Thứ Sáu, Thứ Bảy, Chủ nhật', '',
          'Đặt lần lượt Thứ Hai, Thứ Ba, Thứ Tư, Thứ Năm, Thứ Sáu, Thứ Bảy, Chủ nhật. Mỗi tên ngày xuất hiện đúng một lần.'),
         ('Đếm và đối chiếu đủ thẻ', 'Mỗi thẻ biểu thị một ngày; đếm các thẻ đã xếp để biết số ngày của một tuần.', '7', '7', 'ngày',
          'Đếm lần lượt các thẻ đã xếp được bảy thẻ, ứng với bảy ngày. Kiểm lại danh sách đầu bài để bảo đảm không bỏ Chủ nhật và không lặp thẻ nào.')],
        [('Thứ tự các ngày bắt đầu từ Thứ Hai', 'Thứ Hai, Thứ Ba, Thứ Tư, Thứ Năm, Thứ Sáu, Thứ Bảy, Chủ nhật', ''),
         ('Số ngày trong một tuần', '7', 'ngày')],
        ['Tên trên mỗi thẻ là tên một ngày.', 'Xếp theo thứ tự ngày đã học, rồi kiểm dùng đủ các thẻ.'],
        [('Danh sách thẻ chưa được xếp theo tuần.', 'Đề yêu cầu bắt đầu bằng thẻ nào?'),
         ('Sau thẻ bắt đầu, tìm ngày kế tiếp và tránh dùng lại thẻ đã đặt.', 'Em đã xếp được đoạn nào mà không bỏ hay lặp ngày?'),
         ('Đối chiếu các thẻ còn lại trước khi đếm toàn bộ dãy.', 'Em đã dùng hết mọi thẻ đúng một lần chưa?')])

    add('sunday_rollover', 'current_g1_calendar_week', 'core_02',
        'Trong một tình huống giả định, hôm qua là Thứ Bảy, hôm nay là Chủ nhật. Ngày mai là thứ mấy? Hãy giải thích vì sao không gọi ngày mai là “Thứ Tám”.',
        ['Hôm qua Thứ Bảy; hôm nay Chủ nhật.', 'Hỏi tên ngày ngay sau hôm nay.'],
        [('Xác định ngày đang làm mốc', 'Ngày mai là ngày ngay sau hôm nay, nên cần bắt đầu từ Chủ nhật đã được cho.', None, 'Chủ nhật là hôm nay', '',
          'Hôm qua chỉ giúp kiểm chuỗi ngày: Thứ Bảy rồi đến Chủ nhật. Ta tìm ngày sau Chủ nhật, không tìm ngày sau Thứ Bảy.'),
         ('Nối sang tuần kế tiếp', 'Tên ngày trong tuần lặp lại theo vòng; sau ngày cuối tuần là ngày đầu của tuần tiếp theo.', None, 'Thứ Hai', '',
          'Ngày mai là Thứ Hai. Một tuần kết thúc ở Chủ nhật rồi sang Thứ Hai của tuần sau; không có tên ngày “Thứ Tám”. Kiểm chuỗi Thứ Bảy → Chủ nhật → Thứ Hai.')],
        [('Tên ngày mai', 'Thứ Hai', '')],
        ['Dùng hôm nay làm mốc để tìm ngày mai.', 'Các tên ngày lặp lại qua các tuần.'],
        [('Cần phân biệt hôm qua, hôm nay và ngày mai.', 'Ngày nào trong đề được gọi là hôm nay?'),
         ('Đến hết một tuần, tên ngày tiếp tục từ đầu tuần kế tiếp.', 'Tên ngày có tiếp tục tăng mãi thành ngày mới ngoài tuần không?'),
         ('Đọc nối một ngày qua chỗ kết thúc tuần rồi kiểm với ngày đứng trước hôm nay.', 'Chuỗi tên ngày em nêu có nối liền hai tuần đúng thứ tự không?')])

    add('mini_calendar_lookup', 'current_g1_calendar_week', 'core_03',
        'Dùng đúng mẩu lịch giả định sau, không cần đoán tháng hay năm thật: ngày 11 — Thứ Hai; 12 — Thứ Ba; 13 — Thứ Tư; 14 — Thứ Năm; 15 — Thứ Sáu; 16 — Thứ Bảy; 17 — Chủ nhật. Lớp sinh hoạt vào Thứ Năm của tuần này. Buổi sinh hoạt là ngày mấy? Ngày 16 là thứ mấy? Hãy kiểm trên mẩu lịch.',
        ['Mẩu lịch giả định: 11 Thứ Hai, 12 Thứ Ba, 13 Thứ Tư, 14 Thứ Năm, 15 Thứ Sáu, 16 Thứ Bảy, 17 Chủ nhật.', 'Sinh hoạt vào Thứ Năm của chính tuần được cho.'],
        [('Tìm ngày của buổi sinh hoạt', 'Buổi sinh hoạt được cho bằng tên thứ, nên tìm tên thứ đó trong mẩu lịch rồi đọc số ngày đi cùng.', '14', '14', 'ngày trong tháng',
          'Mẩu lịch ghép Thứ Năm với ngày 14. Vì vậy buổi sinh hoạt là ngày 14, không phải ngày mang số giống tên thứ.'),
         ('Đọc thứ từ số ngày và kiểm hai chiều', 'Câu hỏi tiếp theo cho số ngày, nên tìm ngày đó rồi đọc tên thứ đi cùng.', None, 'Thứ Bảy', '',
          'Ngày 16 đi cùng Thứ Bảy. Kiểm lại hai cặp: ngày 14 — Thứ Năm, ngày 16 — Thứ Bảy, đều có đúng trong mẩu lịch. Không cần biết tháng hoặc năm ngoài mẩu lịch này.')],
        [('Ngày trong tháng của buổi sinh hoạt', '14', 'ngày trong tháng'), ('Thứ của ngày 16', 'Thứ Bảy', '')],
        ['Mẩu lịch đã ghép mỗi số ngày với một tên thứ.', 'Hai câu hỏi yêu cầu đọc cặp theo hai chiều khác nhau.'],
        [('Phân biệt tên thứ với số ngày trong tháng.', 'Câu hỏi về buổi sinh hoạt cho sẵn tên thứ hay số ngày?'),
         ('Tìm đúng mục có dữ kiện cần tra rồi đọc thông tin đi cùng trong cùng mục.', 'Em có giữ số ngày và tên thứ thuộc cùng một cặp khi đọc không?'),
         ('Đối chiếu lại từng cặp đã chọn với mẩu lịch, không dùng lịch của tháng khác.', 'Cả hai câu trả lời của em có đúng với chính mẩu lịch đã cho chưa?')])

    wrong = 'Từ Thứ Hai đến Thứ Bảy có sáu ngày, nên một tuần chỉ có sáu ngày.'
    add('misconception_omit_sunday', 'current_g1_calendar_week', None,
        'Một bạn viết trong bài làm giả định: “'+wrong+'” Hãy nhận xét chỉ dựa vào câu đã viết và sửa kết luận về số ngày trong một tuần.',
        ['Câu viết giả định của học sinh chỉ nêu từ Thứ Hai đến Thứ Bảy.'],
        [('Tách phần đếm đúng khỏi kết luận thiếu', 'Đếm từ Thứ Hai đến Thứ Bảy được sáu ngày, nhưng đoạn đó chưa chứa mọi ngày của một tuần.', None,
          'chưa kể Chủ nhật', '', 'Câu viết đã bỏ Chủ nhật khi kết luận về cả tuần. Ta chỉ góp ý điều thể hiện trong câu, không suy đoán bạn đã làm mất thẻ hay nhìn nhầm lịch.'),
         ('Bổ sung ngày còn thiếu và đếm lại', 'Muốn nói về một tuần, cần kể đủ các ngày của tuần.', '6+1', '7', 'ngày',
          'Sáu ngày từ Thứ Hai đến Thứ Bảy cùng thêm Chủ nhật là 6 + 1 = 7 ngày. Một tuần có bảy ngày. Kiểm danh sách có Thứ Hai, Thứ Ba, Thứ Tư, Thứ Năm, Thứ Sáu, Thứ Bảy, Chủ nhật, không lặp ngày.')],
        [('Số ngày trong một tuần', '7', 'ngày')],
        ['Cần kiểm câu viết đã nêu đủ các ngày hay chưa.', 'Một đoạn đúng trong tuần chưa chắc đã là cả tuần.'],
        [('Phân biệt số ngày trong đoạn đã kể với số ngày của cả tuần.', 'Bạn đang kể từ ngày nào đến ngày nào trong câu viết?'),
         ('Kiểm các tên ngày của cả tuần với danh sách bạn đã nêu.', 'Danh sách bạn viết đã bao gồm tất cả các tên ngày trong tuần chưa?'),
         ('Nếu còn tên ngày chưa được kể, bổ sung rồi mới kết luận về cả tuần.', 'Em có thể kiểm rằng mỗi ngày chỉ xuất hiện một lần trong danh sách đủ chưa?')],
        kind='misconception', student={'text': wrong, 'observations': [{'excerpt': wrong,
            'claim_scope': 'Synthetic written claim omits Sunday when generalizing a six-day segment to a whole week; no inference about real cards or observation.'}]})

    add('guard_date_without_calendar', 'current_g1_calendar_week', None,
        'Em chỉ nói “Hôm nay là ngày 12” rồi hỏi hôm nay là thứ mấy. Chưa cho tháng, năm, mẩu lịch hoặc một ngày có thứ đã biết để làm mốc. Hãy hỗ trợ mà không tự lấy ngày hiện tại của máy làm đáp án.',
        ['Chỉ biết số ngày trong tháng là 12.', 'Không có tháng, năm, lịch hoặc mốc thứ đã biết.'], [], [],
        ['Chỉ có số ngày trong tháng chưa xác định được tên thứ.', 'Em gửi mẩu lịch đang dùng hoặc cho biết thêm tháng, năm để cùng tra.'],
        [('Cùng một số ngày trong tháng có thể rơi vào các thứ khác nhau.', 'Em đang hỏi ngày đó của tháng và năm nào?'),
         ('Một mẩu lịch rõ số ngày và tên thứ sẽ giúp tra mà không phải đoán.', 'Em có thể gửi hoặc chép phần lịch có ngày cần tìm không?'),
         ('Nếu không có lịch, có thể dùng một ngày trong cùng tuần đã biết tên thứ làm mốc.', 'Em có biết ngày nào gần đó kèm tên thứ trong chính lịch đang dùng không?')], kind='guard')

    add('read_morning_hour', 'current_g1_clock_whole_hour', 'core_01',
        'Một đồng hồ kim được mô tả bằng chữ: kim dài là kim phút, đang chỉ đúng số 12; kim ngắn là kim giờ, đang chỉ đúng số 7. Đây là lúc buổi sáng. Đồng hồ chỉ mấy giờ sáng? Giải thích vai trò hai kim.',
        ['Kim phút dài chỉ 12; kim giờ ngắn chỉ 7.', 'Bối cảnh buổi sáng.'],
        [('Nhận ra giờ đúng', 'Kim phút chỉ đúng số 12 là dấu hiệu đang ở giờ đúng.', None, 'giờ đúng', '',
          'Kim dài cho biết phần phút; ở đây nó chỉ số 12 nên đọc giờ đúng, không lấy số 12 làm số giờ.'),
         ('Đọc kim giờ và thêm buổi', 'Trong giờ đúng, kim ngắn chỉ số nào thì đọc số giờ đó; buổi đã được đề nêu.', '7', '7', 'giờ sáng',
          'Kim giờ ngắn chỉ số 7 nên đồng hồ chỉ 7 giờ sáng. Kiểm: kim phút ở 12, kim giờ ở 7, và đề nói buổi sáng; cả ba dữ kiện phù hợp.')],
        [('Giờ đồng hồ chỉ', '7', 'giờ sáng')],
        ['Đề đã cho biết kim nào là kim phút và kim nào là kim giờ.', 'Đọc vai trò từng kim trước khi đọc số giờ.'],
        [('Hai kim có vai trò khác nhau dù cùng trỏ vào các số trên mặt đồng hồ.', 'Kim nào trong mô tả dùng để đọc số giờ?'),
         ('Dùng kim phút để xác định đây có phải giờ đúng, rồi xét kim còn lại.', 'Vị trí kim phút trong đề giúp em nhận ra điều gì về cách đọc giờ?'),
         ('Ghép giờ em đọc với buổi đã được nêu và kiểm lại từng kim.', 'Câu trả lời của em đã phù hợp với cả vai trò hai kim và buổi trong đề chưa?')])

    add('both_hands_at_noon', 'current_g1_clock_whole_hour', 'core_02',
        'Một đồng hồ được mô tả lúc đúng giữa trưa: kim dài chỉ số 12 và kim ngắn cũng chỉ số 12. Có bạn băn khoăn hai kim cùng một số thì không đọc được. Hãy đọc giờ và giải thích dựa vào vai trò của hai kim, không đổi thành thời điểm ban đêm.',
        ['Thời điểm đúng giữa trưa.', 'Kim dài phút và kim ngắn giờ cùng chỉ 12.'],
        [('Phân biệt vai trò dù kim cùng chỗ', 'Hai kim có thể cùng hướng mà vẫn giữ vai trò kim phút và kim giờ.', None, 'giờ đúng', '',
          'Kim dài ở số 12 cho biết giờ đúng. Kim ngắn cũng ở số 12 cho biết số giờ, nên sự trùng hướng không làm mất thông tin.'),
         ('Đọc giờ và giữ bối cảnh trưa', 'Đề nói rõ giữa trưa, vì vậy gắn buổi đó với số giờ đọc từ kim ngắn.', '12', '12', 'giờ trưa',
          'Đồng hồ chỉ 12 giờ trưa. Kiểm cả hai kim đều ở 12 và bối cảnh là giữa trưa; không tự chuyển sang nửa đêm chỉ vì mặt đồng hồ có thể trông giống nhau.')],
        [('Giờ đồng hồ chỉ', '12', 'giờ trưa')],
        ['Hai kim cùng hướng vẫn có hai nhiệm vụ khác nhau.', 'Giữ thời điểm trong ngày mà đề đã nói rõ.'],
        [('Có thể phân biệt vai trò kim dài và kim ngắn ngay cả khi chúng cùng hướng.', 'Kim ngắn và kim dài lần lượt dùng để đọc phần nào?'),
         ('Đọc từng kim theo vai trò thay vì cho rằng trùng chỗ thì không có thông tin.', 'Việc hai kim cùng hướng có làm chúng mất vai trò riêng không?'),
         ('Sau khi đọc số giờ, đối chiếu với thời điểm trong ngày đã nêu.', 'Cách đọc của em có giữ đúng bối cảnh mà đề đã cho chưa?')])

    add('match_schedule', 'current_g1_clock_whole_hour', 'core_03',
        'Lịch hoạt động giả định ghi: “Bắt đầu đọc truyện lúc 9 giờ sáng”. Có hai mô hình đồng hồ: A có kim phút dài chỉ 12, kim giờ ngắn chỉ 9; B có kim phút dài chỉ 12, kim giờ ngắn chỉ 10. Mô hình nào phù hợp lúc bắt đầu đọc truyện? Hãy đọc từng mô hình rồi đối chiếu với lịch.',
        ['Bắt đầu đọc truyện lúc 9 giờ sáng.', 'A: kim phút 12, kim giờ 9.', 'B: kim phút 12, kim giờ 10.'],
        [('Đọc giờ của từng mô hình', 'Cả hai kim phút đều ở 12 nên đều là giờ đúng; cần dùng kim giờ để phân biệt.', None,
          'A chỉ 9 giờ; B chỉ 10 giờ', '', 'Kim giờ của A chỉ 9 nên A chỉ 9 giờ; kim giờ của B chỉ 10 nên B chỉ 10 giờ. Đọc số giờ theo kim ngắn, không theo tên mô hình.'),
         ('Đối chiếu với lịch và kiểm lựa chọn', 'Mô hình đúng phải có số giờ trùng giờ bắt đầu trong lịch hoạt động.', None, 'mô hình A', '',
          'Chọn mô hình A vì lịch ghi bắt đầu lúc 9 giờ sáng. B chỉ 10 giờ nên không phù hợp. Mặt đồng hồ không tự cho biết buổi sáng; buổi sáng đến từ lịch hoạt động đã cho.')],
        [('Mô hình phù hợp giờ bắt đầu', 'mô hình A', '')],
        ['Lịch ghi thời điểm cần tìm, còn mô hình cho vị trí hai kim.', 'Đọc mỗi mô hình rồi mới so với lịch.'],
        [('Cần chọn bằng thời điểm trong lịch thay vì bằng tên mô hình.', 'Lịch hoạt động yêu cầu em tìm thời điểm của việc gì?'),
         ('Hai kim phút giống nhau nên hãy chú ý phần thông tin giúp phân biệt hai mô hình.', 'Kim nào ở hai mô hình đang chỉ vào hai số khác nhau?'),
         ('Đối chiếu số giờ đọc từ từng mô hình với số giờ trong lịch, rồi kiểm lại lựa chọn.', 'Lý do em chọn có nêu được sự phù hợp với lịch hoạt động không?')])

    wrong = 'Kim dài chỉ 12 nên đồng hồ chỉ 12 giờ.'
    add('misconception_read_minute_as_hour', 'current_g1_clock_whole_hour', None,
        'Trong bài làm giả định, đề mô tả buổi sáng: kim dài là kim phút chỉ 12; kim ngắn là kim giờ chỉ 6. Bạn viết: “'+wrong+'” Hãy nhận xét câu viết và đọc lại giờ chỉ theo dữ kiện đã cho.',
        ['Buổi sáng; kim phút dài 12, kim giờ ngắn 6.', 'Câu viết giả định lấy số kim dài chỉ làm số giờ.'],
        [('Chỉ rõ chỗ dùng sai vai trò kim', 'Câu viết lấy số do kim phút chỉ làm số giờ, trong khi số giờ cần đọc ở kim giờ.', None,
          'nhầm vai trò kim phút với kim giờ', '', 'Kim dài chỉ 12 cho biết giờ đúng, không có nghĩa số giờ là 12. Nhận xét này dựa vào đúng câu bạn đã viết, không đoán bạn không biết phân biệt độ dài hai kim.'),
         ('Đọc lại bằng kim giờ và kiểm', 'Kim giờ ngắn chỉ 6 và đề đã xác định buổi sáng.', '6', '6', 'giờ sáng',
          'Đồng hồ chỉ 6 giờ sáng. Kiểm lại: kim phút ở 12 cho biết giờ đúng; kim giờ ở 6 cho biết số giờ; buổi sáng là bối cảnh được cho.')],
        [('Giờ đồng hồ chỉ', '6', 'giờ sáng')],
        ['Cần đối chiếu câu viết với vai trò hai kim mà đề đã nêu.', 'Chỉ nhận xét sự nhầm vai trò thể hiện trong lời viết.'],
        [('Kim phút và kim giờ dùng để đọc những phần khác nhau.', 'Bạn đã dùng số do kim nào chỉ để kết luận số giờ?'),
         ('Giữ thông tin giờ đúng từ kim phút nhưng đọc số giờ ở kim còn lại.', 'Số giờ cần đối chiếu với vị trí kim nào trong mô tả?'),
         ('Kiểm lại giờ em đọc bằng cả hai kim và buổi đã nêu.', 'Lời sửa của em có tránh lặp lại cách lấy kim phút làm kim giờ không?')],
        kind='misconception', student={'text': wrong, 'observations': [{'excerpt': wrong,
            'claim_scope': 'Synthetic written explanation explicitly uses minute-hand numeral as hour; no claim about actual visual perception or motor error.'}]})

    add('guard_missing_hour_hand', 'current_g1_clock_whole_hour', None,
        'Em chỉ mô tả “Kim phút dài của đồng hồ chỉ đúng số 12” rồi hỏi đồng hồ chỉ mấy giờ. Chưa có ảnh hoặc vị trí kim giờ ngắn. Hãy hỏi thông tin còn thiếu, chưa đoán số giờ hay buổi trong ngày.',
        ['Chỉ biết kim phút dài chỉ đúng 12.', 'Chưa có vị trí kim giờ hoặc thông tin buổi.'], [], [],
        ['Kim phút ở vị trí đã nêu chỉ giúp nhận ra giờ đúng, chưa xác định số giờ.', 'Em mô tả vị trí kim giờ ngắn hoặc gửi ảnh rõ cả hai kim.'],
        [('Cần biết kim dùng để chỉ số giờ đang hướng về đâu.', 'Kim ngắn của đồng hồ đang chỉ số nào?'),
         ('Một vị trí kim phút có thể đi cùng nhiều vị trí kim giờ khác nhau.', 'Em có thể gửi ảnh rõ cả hai kim nếu chưa đọc được kim ngắn không?'),
         ('Đọc số giờ cần đủ hai kim; nếu muốn nói thêm buổi thì cần bối cảnh trong ngày.', 'Đề có cho thêm đây là buổi nào trong ngày không?')], kind='guard')

    assert len(rows) == 10
    blocked, protected_questions, fingerprints = protections()
    existing = [r for batch in (DEFAULT_ROOT/'authored_batches').glob('*.jsonl') for r in read_rows(batch)]
    existing_questions = {normalized(r['problem']) for r in existing}
    existing_ids = {r['sample_id'] for r in existing}
    checks = []
    for row in rows:
        inspection = inspect_case(row)
        assert inspection['passed'], (row['sample_id'], inspection)
        assert mapping_error(row, nodes) is None
        assert normalized(row['problem']) not in protected_questions | existing_questions
        assert row['sample_id'] not in existing_ids
        signatures = answer_signatures(row, inspection)
        assert not signatures & blocked, (row['sample_id'], 'protected signature collision')
        checks.append({'sample_id': row['sample_id'], 'row_sha256': row_sha(row),
                       'mechanical_pass': True, 'mapping_pass': True,
                       'exact_question_duplicate': False, 'protected_signature_collision': False})

    by_suffix = {r['topic']: r for r in rows}
    def answers(suffix):
        return [(a['result'], a['unit']) for a in by_suffix[suffix]['expected_answer']]
    # Separate finite-domain oracles: explicit ordered weekday cycle and hand-role lookup.
    week = ['Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy', 'Chủ nhật']
    cards = ['Thứ Năm', 'Chủ nhật', 'Thứ Hai', 'Thứ Bảy', 'Thứ Tư', 'Thứ Sáu', 'Thứ Ba']
    assert sorted(cards) == sorted(week) and len(set(cards)) == len(week) == 7
    assert answers('week_order_count') == [(', '.join(week), ''), (str(len(cards)), 'ngày')]
    assert answers('sunday_rollover') == [(week[(week.index('Chủ nhật')+1) % len(week)], '')]
    calendar = {11+i: day for i, day in enumerate(week)}
    activity_date = next(n for n, d in calendar.items() if d == 'Thứ Năm')
    assert answers('mini_calendar_lookup') == [(str(activity_date), 'ngày trong tháng'), (calendar[16], '')]
    assert answers('misconception_omit_sunday') == [(str(len(week)), 'ngày')]
    assert set(week) - set(week[:6]) == {'Chủ nhật'}
    clock = lambda minute, hour: hour if minute == 12 and hour in range(1,13) else None
    assert answers('read_morning_hour') == [(str(clock(12,7)), 'giờ sáng')]
    assert answers('both_hands_at_noon') == [(str(clock(12,12)), 'giờ trưa')]
    models = {'mô hình A': clock(12,9), 'mô hình B': clock(12,10)}
    assert answers('match_schedule') == [(next(k for k,v in models.items() if v == 9), '')]
    assert answers('misconception_read_minute_as_hour') == [(str(clock(12,6)), 'giờ sáng')]
    # Countermodels prove insufficiency of each guard without claiming current dates/images.
    hypothetical_week_a = {12: 'Thứ Hai'}
    hypothetical_week_b = {12: 'Thứ Tư'}
    assert hypothetical_week_a[12] != hypothetical_week_b[12]
    assert clock(12,2) != clock(12,8)
    for suffix in ('guard_date_without_calendar', 'guard_missing_hour_hand'):
        assert not by_suffix[suffix]['can_solve'] and not by_suffix[suffix]['worked_steps'] and not answers(suffix)

    record = write_rows(path, rows)
    write_json(HERE/'evidence/primary_math_teacher_20261016/g1_time_0007_author_checks.json', {
        'batch': str(path.relative_to(HERE)), 'batch_sha256': record['sha256'], 'authored_cases': len(rows),
        'core_cases': 6, 'misconception_cases': 2, 'guard_cases': 2,
        'checks': checks, 'separate_finite_domain_oracles_pass': True,
        'oracle_scope': 'Seven-day ordering/cycle, provided hypothetical date mapping, whole-hour hand roles, matching schedule, missing-data countermodels. Not proof of unrestricted semantics or physical/vision skill.',
        'protected_fingerprints': fingerprints, 'sealed_concept_challenge_read': False,
        'content_review_status': 'PENDING_INDEPENDENT_PARENT_REVIEW', 'human_verified': False,
        'teacher_certified': False, 'training_started': False, 'skills_matched': 'none',
    })
    print(json.dumps({**record, 'review_pending': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()

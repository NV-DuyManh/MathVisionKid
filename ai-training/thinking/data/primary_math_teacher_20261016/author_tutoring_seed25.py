"""Original, training-only teaching examples; no training or remote API calls.

This authoring source is evidence, not a model-quality benchmark. Calculation
claims are independently recomputed below with exact fractions and divmod.
"""
from __future__ import annotations

import ast
import hashlib
import json
import operator
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ROWS = []


def given(key, text, value, unit, role):
    return dict(id=key, text=text, value=value, unit=unit, role=role)


def step(title, reason, expression, result, unit, explanation):
    return dict(title=title, reason=reason, expression=expression,
                result=result, unit=unit, explanation=explanation)


def add(grade, family, problem, givens, requested, initial, hints, steps,
        answers, *, work="", observation="", capabilities=()):
    case_id = f"original_tutor25_g{grade}_{sum(r['grade'] == grade for r in ROWS)+1:02d}"
    for index, item in enumerate(steps):
        item["step_id"] = f"s{index}"
    ROWS.append(dict(
        sample_id=case_id, split="train", case_group_id=case_id,
        grade=grade, topic=family, problem=problem, givens=givens,
        requested_quantity=requested,
        student_work=dict(text=work, observations=[dict(excerpt=work, claim_scope=observation)]) if work else None,
        initial_guidance=initial,
        hints=[dict(level=i+1, hint=pair[0], question=pair[1]) for i, pair in enumerate(hints)],
        worked_steps=steps,
        expected_answer=[dict(quantity=q, result=v, unit=u) for q, v, u in answers],
        canonical_case=dict(family=family,
                            operations=[s["expression"] for s in steps],
                            numeric_values=[g["value"] for g in givens]),
        provenance=dict(authoring_method="original_AI_teacher", human_verified=False,
                        source_kind="original_problem_and_teacher_explanation",
                        curriculum_node_id=None,
                        curriculum_mapping_status="PENDING_PEER_MAPPING",
                        copied_from_pupil_work=False,
                        benchmark_status="TRAINING_ONLY_NOT_GOLD",
                        sealed_development_data_read=False),
        quality_flags=dict(three_hint_levels_answer_free=True,
                           full_worked_solution_requires_explicit_request=True,
                           source_work_observation_only=bool(work),
                           requires_capabilities=list(capabilities),
                           app_plan_draft_compatible=False,
                           app_mapping_status="NEUTRAL_SCHEMA_REQUIRES_EXPLICIT_ADAPTER_AND_REVIEW"),
    ))


# Grade 1: concrete quantities, composing numbers, comparison, and place value.
add(1, "add_no_carry_within_100", "Mai có 83 nhãn vở, được cô cho thêm 6 nhãn vở. Mai có tất cả bao nhiêu nhãn vở?",
    [given("g0", "có 83 nhãn vở", "83", "nhãn vở", "initial_count"), given("g1", "cho thêm 6 nhãn vở", "6", "nhãn vở", "added_count")],
    "Số nhãn vở sau khi được cho thêm.",
    ["Nhãn vở được cho thêm nhập chung với nhãn vở Mai đang có.", "Em cần tìm số nhãn vở của cả phần đang có và phần được cho thêm."],
    [("Em hãy nghĩ đến việc gộp phần đang có với phần được cho thêm.", "Nhãn vở của Mai tăng lên hay giảm đi?"),
     ("Hãy dùng phép cộng để gộp các nhãn vở cùng loại.", "Em sẽ bắt đầu đếm từ phần nào?"),
     ("Giữ số nhãn vở đang có, rồi đếm tiếp theo từng nhãn vở được thêm vào.", "Sau khi đếm tiếp hết phần thêm, em sẽ ghi đơn vị gì?")],
    [step("Gộp các nhãn vở", "Được cho thêm làm số nhãn vở tăng; gộp các phần cùng đơn vị bằng phép cộng.", "83+6", "89", "nhãn vở", "83 gồm 8 chục và 3 đơn vị. Thêm 6 đơn vị vào 3 đơn vị được 9 đơn vị; phần 8 chục giữ nguyên. Viết: Mai có tất cả là: 83 + 6 = 89 (nhãn vở).")],
    [("Số nhãn vở của Mai", "89", "nhãn vở")])

add(1, "subtract_known_part", "Trong khay có 17 chiếc cúc, gồm 6 chiếc màu đỏ và các chiếc màu xanh. Có bao nhiêu chiếc cúc màu xanh?",
    [given("g0", "có 17 chiếc cúc", "17", "chiếc cúc", "whole"), given("g1", "6 chiếc màu đỏ", "6", "chiếc cúc", "known_part")],
    "Phần cúc màu xanh còn lại trong tổng số cúc.",
    ["Tất cả cúc trong khay được chia theo màu đỏ và xanh.", "Khi bỏ phần đã biết màu đỏ ra khỏi tổng số, phần còn lại là cúc màu xanh."],
    [("Em hãy phân biệt tổng số cúc với phần cúc đã biết màu.", "Số cúc cần tìm là cả khay hay phần còn lại?"),
     ("Muốn tìm phần chưa biết, hãy bớt phần màu đỏ khỏi cả khay.", "Phép tính nào diễn tả việc bớt phần đã biết?"),
     ("Bắt đầu từ tổng số cúc, đếm lùi theo số cúc màu đỏ.", "Khi đếm lùi xong, phần nào được giữ lại?")],
    [step("Tìm phần màu xanh", "Tổng đã gồm cả cúc đỏ và cúc xanh; bớt phần đỏ thì còn đúng phần xanh.", "17-6", "11", "chiếc cúc", "Từ 17 bớt 6: bớt 7 xuống 10 rồi bù lại 1 được 11; cũng có thể đếm lùi 6 lần. Viết: Số cúc màu xanh là: 17 − 6 = 11 (chiếc cúc).")],
    [("Số cúc màu xanh", "11", "chiếc cúc")])

add(1, "compare_difference", "Nam có 18 viên bi, Bình có 5 viên bi. Nam có nhiều hơn Bình bao nhiêu viên bi?",
    [given("g0", "Nam có 18 viên bi", "18", "viên bi", "larger_count"), given("g1", "Bình có 5 viên bi", "5", "viên bi", "smaller_count")],
    "Phần bi của Nam nhiều hơn số bi của Bình.",
    ["Ghép bi của Nam với bi của Bình theo từng cặp bằng nhau.", "Phần bi của Nam không ghép được là phần nhiều hơn cần tìm."],
    [("Hãy hình dung ghép các viên bi của các bạn theo từng cặp.", "Phần không ghép được thuộc về bạn nào?"),
     ("Bớt phần bằng số bi của Bình khỏi số bi của Nam.", "Vì sao lấy số lớn bớt số nhỏ trong bài này?"),
     ("Em có thể đếm tiếp từ số bi của Bình đến số bi của Nam.", "Số lượt đếm tiếp cho biết điều gì?")],
    [step("Tìm phần nhiều hơn", "Chỉ hỏi phần chênh lệch nên lấy số bi lớn hơn trừ số bi nhỏ hơn, không gộp số bi của các bạn.", "18-5", "13", "viên bi", "18 gồm 1 chục và 8 đơn vị. Bớt 5 đơn vị thì còn 3 đơn vị cùng 1 chục, tức 13. Viết: Nam có nhiều hơn Bình là: 18 − 5 = 13 (viên bi).")],
    [("Số bi Nam nhiều hơn Bình", "13", "viên bi")])

add(1, "add_whole_tens_to_two_digit", "Tính 24 + 30. Bạn An viết: 24 + 30 = 27. Em hãy tính lại và giải thích cách đặt các hàng.",
    [given("g0", "24", "24", "", "first_addend"), given("g1", "30", "30", "", "second_addend")],
    "Tổng của các số và cách xếp hàng chục, hàng đơn vị.",
    ["Chữ số của các số cần được xếp theo cùng hàng trước khi cộng.", "Hãy nhìn xem phần thêm vào là các chục hay các đơn vị."],
    [("Em hãy đọc giá trị của chữ số khác không trong số được thêm vào.", "Chữ số đó đang ở hàng nào?"),
     ("Đặt hàng đơn vị thẳng hàng đơn vị, hàng chục thẳng hàng chục.", "Em sẽ cộng từ hàng nào trước?"),
     ("Phần đơn vị được cộng với phần đơn vị; các chục được cộng với các chục.", "Em kiểm tra lại cách viết hàng chục trong bài của bạn thế nào?")],
    [step("Cộng theo đúng hàng", "30 là các chục nên phải cộng vào hàng chục của 24; không xem 30 như 3 đơn vị.", "24+30", "54", "", "Đặt 24 trên 30 cho thẳng hàng. Hàng đơn vị: 4 + 0 = 4. Hàng chục: 2 + 3 = 5. Vì vậy 24 + 30 = 54. Dòng bạn viết có kết quả 27 khác tổng đã tính; chỉ từ dòng đó chưa kết luận bạn đã nghĩ như thế nào.")],
    [("Tổng", "54", "")], work="24 + 30 = 27", observation="Dòng viết thể hiện đáp số 27; không thấy đặt tính hoặc diễn biến tư duy, nên không khẳng định bạn đã bỏ quên hàng chục.")

add(1, "compose_tens_and_ones", "Có 30 que tính đã bó thành các bó chục và 6 que tính rời. Có tất cả bao nhiêu que tính? Giải thích theo các chục và đơn vị.",
    [given("g0", "30 que tính đã bó thành các bó chục", "30", "que tính", "whole_tens_value"), given("g1", "6 que tính rời", "6", "que tính", "ones_value")],
    "Tổng số que tính từ các chục và đơn vị rời.",
    ["Các chục là những bó có cùng số đơn vị; các đơn vị lẻ nằm ngoài các bó.", "Em cần ghép giá trị của phần chục với phần đơn vị lẻ."],
    [("Hãy phân biệt số bó chục với số đơn vị lẻ.", "Chữ số chỉ các bó chục phải đặt ở hàng nào?"),
     ("Viết chữ số chỉ các chục ở bên trái chữ số chỉ các đơn vị.", "Mỗi chữ số trong số em viết nói về phần nào?"),
     ("Em có thể vẽ các bó chục rồi vẽ thêm các đơn vị lẻ để kiểm tra số vừa ghép.", "Cách vẽ có giữ đúng các chục và các đơn vị trong đề không?")],
    [step("Ghép phần chục và phần lẻ", "Các bó chục và que rời cùng tạo thành toàn bộ số que tính, nên gộp các phần lại.", "30+6", "36", "que tính", "30 que tính là 3 bó chục. Ghép thêm 6 que rời được 3 chục và 6 đơn vị, viết là 36. Có tất cả: 30 + 6 = 36 (que tính). Trong số 36, chữ số 3 chỉ các chục và chữ số 6 chỉ các đơn vị.")],
    [("Tổng số que tính", "36", "que tính")])

# Grade 2: carrying, borrowing, equal groups, and relations between quantities.
add(2, "two_digit_add_with_carry", "Tủ sách có 38 quyển truyện. Cô bổ sung 27 quyển truyện. Tủ sách có tất cả bao nhiêu quyển truyện?",
    [given("g0", "38 quyển truyện", "38", "quyển truyện", "initial_count"), given("g1", "bổ sung 27 quyển", "27", "quyển truyện", "added_count")],
    "Số truyện sau khi bổ sung.", ["Số truyện được bổ sung làm số truyện của tủ tăng lên.", "Khi đặt tính, chú ý đổi đủ các đơn vị thành chục."],
    [("Truyện đang có và truyện bổ sung đều thuộc về tủ sách sau cùng.", "Em cần gộp hay bớt số truyện?"), ("Hãy đặt các chữ số cùng hàng thẳng cột rồi cộng hàng đơn vị trước.", "Khi hàng đơn vị đủ chục, em sẽ làm gì?"), ("Ghi phần đơn vị của tổng ở cột đơn vị và nhớ phần chục sang cột chục.", "Em đã cộng phần nhớ vào hàng chục chưa?")],
    [step("Gộp số truyện", "Tìm tất cả truyện sau khi thêm bằng phép cộng cùng đơn vị.", "38+27", "65", "quyển truyện", "Đặt 38 trên 27. 8 + 7 = 15, viết 5 ở hàng đơn vị và nhớ 1 chục. 3 + 2 + 1 = 6 chục. Tủ có tất cả: 38 + 27 = 65 (quyển truyện).")], [("Số truyện của tủ", "65", "quyển truyện")])

add(2, "two_digit_subtract_with_borrow", "Trong hộp có 45 chiếc kẹp. Cô lấy ra 18 chiếc. Hộp còn lại bao nhiêu chiếc kẹp? Bạn viết 45 − 18 = 33.",
    [given("g0", "45 chiếc kẹp", "45", "chiếc kẹp", "initial_count"), given("g1", "lấy ra 18 chiếc", "18", "chiếc kẹp", "removed_count")],
    "Số kẹp còn trong hộp.", ["Kẹp bị lấy ra không còn thuộc phần trong hộp.", "Trừ theo cùng hàng; nếu phần đơn vị chưa đủ để bớt, đổi từ hàng chục."],
    [("Em hãy tách phần ban đầu và phần đã lấy ra.", "Muốn tìm phần còn lại, em dùng phép tính nào?"), ("Đặt cùng hàng thẳng cột và xem hàng đơn vị có đủ để trừ không.", "Em cần đổi từ hàng nào khi phần đơn vị chưa đủ?"), ("Sau khi đổi chục thành đơn vị, nhớ giảm phần chục trước khi trừ hàng chục.", "Em sẽ kiểm tra lại phép trừ bằng phép cộng thế nào?")],
    [step("Bớt số kẹp đã lấy", "Kẹp bị lấy ra là phần cần bớt khỏi số ban đầu.", "45-18", "27", "chiếc kẹp", "5 đơn vị chưa bớt được 8 đơn vị trong các số tự nhiên, đổi 1 chục thành 10 đơn vị: 15 − 8 = 7; phần chục còn 3, nên 3 − 1 = 2. Còn 27 chiếc. Kiểm tra 27 + 18 = 45. Dòng 33 là kết quả sai nhưng không cho biết cụ thể thao tác sai nào đã xảy ra.")], [("Số kẹp còn lại", "27", "chiếc kẹp")], work="45 − 18 = 33", observation="Chỉ có dòng phép tính và đáp số; chưa có bằng chứng rằng bạn trừ chữ số nhỏ khỏi chữ số lớn.")

add(2, "equal_groups_table_five", "Có 4 hộp bút, mỗi hộp 5 chiếc. Có tất cả bao nhiêu chiếc bút trong các hộp?",
    [given("g0", "4 hộp", "4", "hộp", "group_count"), given("g1", "mỗi hộp 5 chiếc", "5", "chiếc bút/hộp", "per_group")],
    "Tổng số bút trong các hộp bằng nhau.", ["Các hộp có lượng bút bằng nhau.", "Gộp lượng bút của các hộp để tìm toàn bộ bút, phân biệt số hộp với số bút."],
    [("Em hãy xác định số nhóm và lượng bút trong từng nhóm.", "Thông tin nào nói về số hộp?"), ("Các hộp bằng nhau có thể gộp nhanh bằng phép nhân.", "Thông tin nào chỉ số hộp, thông tin nào chỉ bút trong mỗi hộp?"), ("Lấy lượng bút mỗi hộp theo đủ các hộp đã cho; có thể đếm thêm theo lượng mỗi hộp.", "Khi gộp đủ các hộp, em sẽ ghi đơn vị gì?")],
    [step("Tìm bút trong các hộp", "Biết số hộp và lượng bút bằng nhau trong mỗi hộp nên dùng phép nhân để gộp các nhóm.", "5*4", "20", "chiếc bút", "Mỗi hộp có 5 chiếc; đếm thêm 5 theo 4 hộp: 5, 10, 15, 20. Số bút trong các hộp là: 5 × 4 = 20 (chiếc bút).")], [("Tổng số bút", "20", "chiếc bút")])

add(2, "whole_known_part", "Câu lạc bộ có 63 bạn, trong đó có 22 bạn nữ, còn lại là bạn nam. Câu lạc bộ có bao nhiêu bạn nam?",
    [given("g0", "63 bạn", "63", "bạn", "whole_count"), given("g1", "22 bạn nữ", "22", "bạn", "female_count")],
    "Số bạn nam trong câu lạc bộ.", ["Tổng số bạn gồm bạn nữ và bạn nam; chưa biết riêng số bạn nam.", "Bớt phần nữ đã biết khỏi tổng sẽ còn phần bạn nam."],
    [("Em đã biết riêng số bạn nam chưa? Hãy xem tổng được chia thành những phần nào.", "Đại lượng cần tìm là tổng hay phần còn lại?"), ("Bớt phần bạn nữ khỏi tổng để biết phần bạn nam.", "Vì sao không gộp thêm số bạn nữ vào tổng?"), ("Đặt các chữ số cùng hàng thẳng cột rồi bớt phần đã biết khỏi tổng.", "Em kiểm tra kết quả bằng cách gộp lại các phần thế nào?")],
    [step("Tìm số bạn nam", "Tổng đã gồm bạn nữ và bạn nam; lấy tổng bớt nữ được nam.", "63-22", "41", "bạn", "Số bạn nam là: 63 − 22 = 41 (bạn). Kiểm tra 41 + 22 = 63, đúng bằng tổng số bạn trong câu lạc bộ.")], [("Số bạn nam", "41", "bạn")])

add(2, "compose_hundreds_tens_ones", "Viết số gồm 3 trăm, 4 chục và 6 đơn vị. Giải thích vị trí của các chữ số.",
    [given("g0", "3 trăm", "300", "đơn vị", "hundreds_value"), given("g1", "4 chục", "40", "đơn vị", "tens_value"), given("g2", "6 đơn vị", "6", "đơn vị", "ones_value")],
    "Số cần viết từ các phần hàng trăm, hàng chục và hàng đơn vị.", ["Mỗi chữ số mang giá trị theo hàng mà nó đứng.", "Đặt chữ số biểu thị phần trăm, phần chục và phần đơn vị đúng cột."],
    [("Hãy đặt các chữ số vào hàng trăm, hàng chục và hàng đơn vị đúng phần đề cho.", "Chữ số ở hàng chục đại diện cho các bó gì?"), ("Ghép các phần theo hàng; không cộng các chữ số như thể chúng đều là đơn vị.", "Phần hàng trăm khác phần hàng chục thế nào?"), ("Em có thể tách số đã viết thành phần trăm, phần chục và phần đơn vị để kiểm tra.", "Khi nói giá trị hàng chục, em cần nêu số bó hay số đơn vị của các bó đó?")],
    [step("Ghép số theo hàng", "Ghép phần trăm, chục và đơn vị theo đúng hàng để viết số hoàn chỉnh.", "300+40+6", "346", "", "3 trăm là 300, 4 chục là 40. Viết 3 ở hàng trăm, 4 ở hàng chục và 6 ở hàng đơn vị, được số 346. Ta có thể tách số ấy thành 300 + 40 + 6 = 346 để kiểm tra các hàng.")], [("Số cần viết", "346", "")], capabilities=("place_value_source_role_resolution",))

# Grade 3: actual remainder, several quantities, duration, and rectangles.
add(3, "euclidean_division_remainder", "Có 52 quả cam, xếp vào các túi, mỗi túi đầy chứa 6 quả. Xếp được nhiều nhất bao nhiêu túi đầy và còn dư bao nhiêu quả cam?",
    [given("g0", "52 quả cam", "52", "quả cam", "whole_count"), given("g1", "mỗi túi đầy chứa 6 quả", "6", "quả cam/túi", "capacity")],
    "Số túi đầy nhiều nhất và số cam chưa đủ đầy túi.", ["Túi đầy phải có đúng lượng cam đã quy định; phần còn lại có thể chưa đủ đầy túi.", "Sau khi tìm túi đầy, luôn kiểm tra phần dư nhỏ hơn sức chứa của túi."],
    [("Hãy tìm số nhóm đủ lượng trước, đừng xem phần cam còn lại là túi đầy.", "Đề đang hỏi túi đầy hay tất cả túi có thể dùng?"), ("Dùng phép chia có dư để tìm các túi đủ lượng và phần còn lại.", "Điều kiện nào giúp nhận ra số dư hợp lệ?"), ("Tìm bội của sức chứa gần tổng số cam nhất mà không vượt tổng, rồi bớt phần đã xếp.", "Nếu phần dư còn đủ đầy túi thì số túi vừa tìm đã nhiều nhất chưa?")],
    [step("Tìm số túi đầy", "Chỉ đếm những nhóm chứa đủ 6 quả; thương nguyên của phép chia là số túi đầy nhiều nhất.", "52//6", "8", "túi đầy", "6 × 8 = 48 còn 6 × 9 = 54 vượt 52, nên xếp nhiều nhất 8 túi đầy."), step("Tìm cam trong túi đầy", "Tính lượng đã xếp từ số túi đầy và sức chứa để tách phần đã xếp khỏi tổng.", "{s0}*6", "48", "quả cam", "Số cam đã xếp vào các túi đầy là: 8 × 6 = 48 (quả)."), step("Tìm phần còn dư", "Lấy tổng bớt số đã xếp được phần cam còn lại, và phải kiểm phần này chưa đủ đầy túi.", "52-{s1}", "4", "quả cam", "Còn dư: 52 − 48 = 4 (quả). Kiểm tra 52 = 6 × 8 + 4 và 0 ≤ 4 < 6. Có 8 túi đầy, dư 4 quả; không viết 52 ÷ 6 = 8 như phép chia hết.")], [("Số túi đầy nhiều nhất", "8", "túi đầy"), ("Số cam còn dư", "4", "quả cam")], capabilities=("euclidean_division_not_supported_by_current_app_ast",))

add(3, "three_digit_single_borrow", "Kho có 364 kg gạo, đã chuyển đi 128 kg. Kho còn bao nhiêu ki-lô-gam gạo? Bài làm có dòng 364 − 128 = 244.",
    [given("g0", "364 kg gạo", "364", "kg", "initial_mass"), given("g1", "chuyển đi 128 kg", "128", "kg", "removed_mass")],
    "Khối lượng gạo còn trong kho.", ["Phần gạo chuyển đi phải được bớt khỏi khối lượng ban đầu.", "Khi đổi từ hàng cao sang hàng thấp, phải sửa lại lượng của hàng đã cho đổi."],
    [("Xác định phần gạo còn trong kho khác với phần đã chuyển đi.", "Em sẽ dùng phép tính nào để tách phần chuyển đi?"), ("Đặt các hàng thẳng cột rồi xem cột đơn vị có đủ để trừ chưa.", "Khi đổi chục, chữ số ở hàng chục thay đổi ra sao?"), ("Sau khi đổi, dùng số chục còn lại để trừ hàng chục rồi tiếp tục hàng trăm.", "Em có thể cộng phần còn lại với phần chuyển đi để kiểm tra không?")],
    [step("Trừ khối lượng đã chuyển", "Phần còn lại là tổng ban đầu bớt phần chuyển đi cùng đơn vị ki-lô-gam.", "364-128", "236", "kg", "Đơn vị: đổi 1 chục thành 10 đơn vị, 14 − 8 = 6; phần chục còn 5. Chục: 5 − 2 = 3. Trăm: 3 − 1 = 2. Còn 236 kg; kiểm 236 + 128 = 364. Dòng 244 không đúng nhưng không đủ bằng chứng để kết luận thao tác sai cụ thể.")], [("Khối lượng gạo còn lại", "236", "kg")], work="364 − 128 = 244", observation="Chỉ quan sát được đáp số 244 khác kết quả đúng; chưa thấy cách đổi chục hoặc đặt tính của học sinh.")

add(3, "multiply_then_subtract", "Có 4 giá sách, mỗi giá có 27 quyển. Thư viện cho mượn 36 quyển từ số sách đó. Trên các giá còn tất cả bao nhiêu quyển?",
    [given("g0", "4 giá sách", "4", "giá", "group_count"), given("g1", "mỗi giá có 27 quyển", "27", "quyển/giá", "per_group"), given("g2", "cho mượn 36 quyển", "36", "quyển", "removed_count")],
    "Số sách còn trên các giá sau khi cho mượn.", ["Trước khi cho mượn, mỗi giá có lượng sách bằng nhau.", "Phải biết tổng sách ban đầu rồi mới bớt phần đã cho mượn."],
    [("Thông tin về từng giá chưa phải tổng sách của thư viện trong bài.", "Em cần gộp các giá bằng nhau bằng cách nào?"), ("Tìm tổng sách trên các giá trước, giữ nguyên đơn vị quyển.", "Phần cho mượn sẽ được gộp hay được bớt sau đó?"), ("Sau khi tìm tổng, bớt đúng số quyển đã cho mượn khỏi tổng ấy.", "Vì sao không trừ số cho mượn khỏi số sách trên mỗi giá?")],
    [step("Tìm tổng sách ban đầu", "Gộp các giá có lượng bằng nhau bằng phép nhân số giá với số quyển mỗi giá.", "4*27", "108", "quyển", "27 × 4: 7 × 4 = 28, viết 8 nhớ 2 chục; 2 × 4 + 2 = 10 chục. Ban đầu có 4 × 27 = 108 (quyển)."), step("Bớt số cho mượn", "36 quyển được lấy từ toàn bộ 108 quyển nên trừ khỏi tổng vừa tìm.", "{s0}-36", "72", "quyển", "Sách còn lại là: 108 − 36 = 72 (quyển). Phép kiểm 72 + 36 = 108 khôi phục tổng ban đầu.")], [("Số sách còn lại", "72", "quyển")])

add(3, "duration_convert_minutes", "Buổi sinh hoạt kéo dài 92 phút. Viết thời gian đó thành giờ và phút, với số phút còn lại ít hơn 60.",
    [given("g0", "92 phút", "92", "phút", "duration"), given("g1", "số phút còn lại ít hơn 60", "60", "phút/giờ", "conversion_base")],
    "Thời lượng theo giờ tròn và số phút còn lại.", ["Tách thời lượng thành các giờ đủ và phần phút chưa đủ giờ.", "Các phút còn lại phải nhỏ hơn số phút tạo thành giờ."],
    [("Hãy dùng mối quan hệ giữa giờ và phút để chia thời lượng thành các phần.", "Phần nào là giờ đủ và phần nào là phút còn lại?"), ("Tìm số giờ tròn có thể lấy ra mà không vượt thời lượng.", "Em cần làm gì với phần phút đã tạo thành giờ?"), ("Bớt số phút của các giờ tròn khỏi tổng thời lượng để tìm phút còn lại.", "Phần phút em tìm có còn tạo thành thêm giờ đủ không?")],
    [step("Tìm số giờ đủ", "Mỗi giờ gồm 60 phút; số giờ đủ là thương nguyên của thời lượng khi chia cho 60.", "92//60", "1", "giờ", "92 phút gồm 1 giờ đủ vì 60 × 1 = 60 và 60 × 2 = 120 vượt 92."), step("Tìm phút còn lại", "Bớt số phút đã đổi thành giờ khỏi tổng để giữ nguyên toàn bộ thời lượng.", "92-{s0}*60", "32", "phút", "Còn 92 − 1 × 60 = 32 phút. Vậy 92 phút = 1 giờ 32 phút; phần phút 32 nhỏ hơn 60.")], [("Phần giờ", "1", "giờ"), ("Phần phút còn lại", "32", "phút")], capabilities=("euclidean_division_not_supported_by_current_app_ast",))

add(3, "rectangle_perimeter_and_area", "Hình chữ nhật có chiều dài 18 cm, chiều rộng 7 cm. Tính chu vi và diện tích của hình.",
    [given("g0", "chiều dài 18 cm", "18", "cm", "length"), given("g1", "chiều rộng 7 cm", "7", "cm", "width")],
    "Độ dài đường bao và phần mặt hình được phủ.", ["Chu vi đo độ dài đường bao, còn diện tích đo phần mặt hình.", "Các đại lượng cần tìm khác nhau nên công thức và đơn vị cũng khác nhau."],
    [("Hãy xác định lúc nào em đang đi quanh hình và lúc nào đang phủ kín mặt hình.", "Bài đang yêu cầu những đại lượng khác nhau nào?"), ("Chu vi cần gộp các cạnh; diện tích hình chữ nhật cần gộp các ô vuông theo hàng.", "Chiều dài và chiều rộng đóng vai trò gì trong từng cách tính?"), ("Với chu vi, gộp chiều dài và chiều rộng rồi tính đủ các cặp cạnh; với diện tích, nhân các kích thước.", "Đơn vị của phần mặt hình khác đơn vị độ dài thế nào?")],
    [step("Tìm chu vi", "Hình chữ nhật có các cặp cạnh đối bằng nhau; đường bao gồm cả chiều dài và chiều rộng lặp lại.", "(18+7)*2", "50", "cm", "Tổng chiều dài và chiều rộng là 25 cm; đường bao gồm 2 lần tổng đó. Chu vi là: (18 + 7) × 2 = 50 (cm)."), step("Tìm diện tích", "Các ô vuông đơn vị xếp theo chiều dài và chiều rộng tạo mặt hình; nhân số ô theo các chiều.", "18*7", "126", "cm²", "Diện tích là: 18 × 7 = 126 (cm²). Chu vi 50 cm và diện tích 126 cm² là các kết quả khác đơn vị, không hoán đổi cho nhau.")], [("Chu vi", "50", "cm"), ("Diện tích", "126", "cm²")])

# Grade 4: equal-part meanings, exact fractions, total/difference, and averages.
add(4, "sum_difference", "Hai ngăn có tất cả 156 quyển sách. Ngăn trên nhiều hơn ngăn dưới 28 quyển. Mỗi ngăn có bao nhiêu quyển?",
    [given("g0", "tất cả 156 quyển", "156", "quyển", "sum"), given("g1", "ngăn trên nhiều hơn ngăn dưới 28 quyển", "28", "quyển", "difference")],
    "Số sách của từng ngăn.", ["Tổng gồm số sách ở ngăn dưới, phần bằng ngăn dưới ở ngăn trên và phần hơn.", "Bớt phần hơn khỏi tổng sẽ làm các phần còn lại bằng nhau."],
    [("Hãy vẽ các đoạn biểu diễn số sách để nhìn phần bằng nhau và phần chênh lệch.", "Ngăn nào có phần dài hơn trên sơ đồ?"), ("Bớt phần hơn khỏi tổng để các ngăn có thể được biểu diễn bằng các phần bằng nhau.", "Phần còn lại gồm những phần bằng số sách của ngăn nào?"), ("Chia phần tổng đã bỏ chênh lệch thành các phần bằng nhau, rồi khôi phục phần hơn cho ngăn trên.", "Kết quả em tìm cho ngăn dưới sẽ giúp tìm ngăn trên ra sao?")],
    [step("Bỏ phần hơn khỏi tổng", "Bớt phần hơn của ngăn trên khiến tổng còn lại gồm 2 phần cùng bằng số sách ngăn dưới.", "156-28", "128", "quyển", "Tổng sau khi bỏ phần hơn là: 156 − 28 = 128 (quyển)."), step("Tìm ngăn dưới", "128 quyển gồm 2 phần bằng nhau, mỗi phần tương ứng số sách ngăn dưới.", "{s0}/2", "64", "quyển", "Ngăn dưới có: 128 ÷ 2 = 64 (quyển)."), step("Tìm ngăn trên", "Ngăn trên hơn ngăn dưới đúng 28 quyển nên gộp phần bằng ngăn dưới với phần hơn.", "{s1}+28", "92", "quyển", "Ngăn trên có: 64 + 28 = 92 (quyển). Kiểm tra 92 + 64 = 156 và 92 − 64 = 28.")], [("Ngăn dưới", "64", "quyển"), ("Ngăn trên", "92", "quyển")])

add(4, "subtract_divisible_denominator_fractions", "Bình có 3/4 lít nước. Bình rót ra 1/8 lít nước. Bình còn bao nhiêu lít nước?",
    [given("g0", "3/4 lít nước", "3/4", "lít", "initial_volume"), given("g1", "rót ra 1/8 lít", "1/8", "lít", "removed_volume")],
    "Lượng nước còn lại.", ["Nước rót ra phải được bớt khỏi lượng có trong bình.", "Các phần tư và phần tám có kích thước khác nhau, cần viết về các phần cùng cỡ trước khi trừ."],
    [("Các phân số đều nói về cùng đơn vị lít, nhưng phần chia nhỏ có cùng cỡ chưa?", "Vì sao chưa thể trừ trực tiếp các tử số?"), ("Hãy chia lại các phần để lượng nước không đổi nhưng các phần nhỏ có cùng cỡ.", "Em cần làm gì với cả tử số và mẫu số khi đổi cách chia?"), ("Khi các mẫu số bằng nhau, bớt số phần đã rót và giữ cỡ phần chung.", "Sau khi trừ, em sẽ ghi đơn vị nước như thế nào?")],
    [step("Tìm lượng nước còn", "Dùng phép trừ vì nước bị rót ra; quy về cùng cỡ phần để so sánh và bớt các phần chính xác.", "3/4-1/8", "5/8", "lít", "Chia đôi mỗi phần tư thành các phần tám không làm đổi lượng: 3/4 = 6/8. Bớt 1 phần tám khỏi 6 phần tám còn 5 phần tám, nên nước còn 6/8 − 1/8 = 5/8 (lít). Không trừ các mẫu số vì mẫu biểu thị cỡ phần.")], [("Lượng nước còn", "5/8", "lít")])

add(4, "divide_exact_fractions", "Tính 3/4 : 2/3 và giải thích phép chia bằng các phần bằng nhau.",
    [given("g0", "3/4", "3/4", "", "dividend"), given("g1", "2/3", "2/3", "", "divisor")],
    "Thương chính xác của các phân số.", ["Chia cho phân số cần giữ nguyên ý nghĩa của các phần bằng nhau.", "Có thể tìm lượng ứng với phần nhỏ trước, rồi gộp đủ số phần của cả đơn vị."],
    [("Hãy xem số chia biểu thị phần nào của đơn vị, thay vì chỉ đọc quy tắc đổi dấu.", "Số chia gồm các phần bằng nhau ra sao?"), ("Muốn biết giá trị ứng với cả đơn vị, trước hết tìm giá trị ứng với phần nhỏ của số chia.", "Em sẽ chia số bị chia theo tử số của số chia như thế nào?"), ("Sau khi tìm lượng ứng với phần nhỏ, gộp đủ số phần theo mẫu số của số chia.", "Vì sao cách chia rồi nhân này giữ đúng quan hệ của phép chia?")],
    [step("Tính thương phân số", "Nếu 2/3 của lượng cần tìm là 3/4, chia 3/4 thành 2 phần bằng nhau được giá trị 1/3, rồi gộp 3 phần được cả lượng.", "(3/4)/(2/3)", "9/8", "", "Giá trị ứng với 1/3 là 3/4 ÷ 2 = 3/8. Gộp 3 phần: 3/8 × 3 = 9/8. Do đó 3/4 : 2/3 = 9/8; kiểm tra 9/8 × 2/3 = 3/4. Không làm tròn thành số thập phân.")], [("Thương", "9/8", "")])

add(4, "whole_from_fraction", "Một lớp có 36 học sinh tham gia câu lạc bộ, bằng 3/4 số học sinh của khối. Khối đó có bao nhiêu học sinh?",
    [given("g0", "36 học sinh", "36", "học sinh", "known_part_count"), given("g1", "bằng 3/4 số học sinh của khối", "3/4", "phần", "part_share")],
    "Toàn bộ số học sinh của khối.", ["Số học sinh đã biết chỉ là các phần của cả khối, không phải toàn bộ.", "Tìm số học sinh trong các phần bằng nhau trước rồi gộp đủ các phần của khối."],
    [("Hãy vẽ đoạn thẳng chia đều theo phân số; đánh dấu phần đã biết số học sinh.", "Số học sinh đã biết ứng với phần nào của cả khối?"), ("Chia số học sinh đã biết theo số phần mà nó đại diện.", "Sau khi biết lượng trong từng phần, em cần gộp đủ bao nhiêu phần của cả khối theo mẫu số?"), ("Tìm lượng trong phần nhỏ rồi gộp đủ các phần tạo nên cả khối.", "Vì sao không nhân ngay số học sinh đã biết với chính phân số đã cho?")],
    [step("Tìm học sinh trong mỗi phần", "36 học sinh ứng với 3 phần bằng nhau, nên chia cho 3 để tìm 1 phần; đây là số học sinh chứ không phải phân số của khối.", "36/3", "12", "học sinh", "Mỗi phần có: 36 ÷ 3 = 12 (học sinh)."), step("Tìm cả khối", "Cả khối gồm 4 phần bằng nhau, nên gộp 4 phần có số học sinh vừa tìm.", "{s0}*4", "48", "học sinh", "Khối có: 12 × 4 = 48 (học sinh). Kiểm tra 48 × 3/4 = 36. Phân số 3/4 không mang đơn vị học sinh; đáp số đếm người là 48 học sinh.")], [("Số học sinh cả khối", "48", "học sinh")])

add(4, "mean_equal_share", "Ba tổ trồng lần lượt 58 cây, 64 cây và 73 cây. Trung bình mỗi tổ trồng bao nhiêu cây?",
    [given("g0", "Ba tổ", "3", "tổ", "group_count"), given("g1", "58 cây", "58", "cây", "first_count"), given("g2", "64 cây", "64", "cây", "second_count"), given("g3", "73 cây", "73", "cây", "third_count")],
    "Số cây trung bình mỗi tổ.", ["Trung bình có thể hình dung là gộp cây rồi chia đều lại cho các tổ.", "Không chọn riêng số cây của tổ ở giữa để làm trung bình."],
    [("Hãy hình dung các tổ góp chung số cây đã trồng.", "Muốn chia đều lại, em cần biết lượng nào trước?"), ("Gộp đủ số cây của các tổ rồi mới chia theo số tổ.", "Tại sao chia theo số tổ thay vì theo số cây của tổ nào đó?"), ("Sau khi tính tổng, chia đều tổng ấy cho các tổ và kiểm tra bằng cách nhân trở lại.", "Số trung bình có nhất thiết bằng số cây đã trồng của tổ nào không?")],
    [step("Tìm tổng số cây", "Gộp toàn bộ cây trước khi xét việc chia đều giữa các tổ.", "58+64+73", "195", "cây", "Tổng số cây là: 58 + 64 + 73 = 195 (cây)."), step("Tìm trung bình", "Chia tổng số cây cho 3 tổ để biết lượng mỗi tổ sẽ có nếu chia đều.", "{s0}/3", "65", "cây", "Trung bình mỗi tổ trồng: 195 ÷ 3 = 65 (cây). Kiểm tra 65 × 3 = 195; 65 không phải số của tổ ở giữa và vẫn là trung bình đúng.")], [("Số cây trung bình mỗi tổ", "65", "cây")])

# Grade 5: decimals, percentages, ratio, motion, and area.
add(5, "decimal_add_subtract", "Can có 4,75 lít dầu. Người bán đổ thêm 2,8 lít rồi bán đi 1,65 lít. Can còn bao nhiêu lít dầu?",
    [given("g0", "4,75 lít", "4.75", "lít", "initial_volume"), given("g1", "thêm 2,8 lít", "2.8", "lít", "added_volume"), given("g2", "bán đi 1,65 lít", "1.65", "lít", "removed_volume")],
    "Lượng dầu sau cả việc thêm vào và bán đi.", ["Các thay đổi xảy ra theo thứ tự thêm dầu rồi bán dầu.", "Các chữ số cùng hàng thập phân phải được đặt thẳng nhau; có thể thêm chữ số không ở tận cùng phần thập phân."],
    [("Em cần theo dõi dầu trong can thay đổi theo các sự việc trong đề.", "Sự việc nào làm tăng và sự việc nào làm giảm lượng dầu?"), ("Gộp lượng dầu thêm trước rồi mới bớt lượng đã bán.", "Để đặt tính đúng, em cần xếp các dấu phẩy như thế nào?"), ("Viết các phần thập phân với đủ hàng, thực hiện phép tính rồi giữ đơn vị lít.", "Em sẽ kiểm tra dấu phẩy và thứ tự thay đổi ra sao?")],
    [step("Tìm dầu sau khi thêm", "Đổ thêm làm tăng dầu nên cộng các lượng cùng đơn vị lít.", "4.75+2.8", "7.55", "lít", "Viết 2,8 = 2,80, đặt các dấu phẩy thẳng cột. 4,75 + 2,80 = 7,55 (lít)."), step("Bớt dầu đã bán", "Lượng bán đi được lấy từ dầu sau khi thêm nên bớt khỏi kết quả trước.", "{s0}-1.65", "5.9", "lít", "7,55 − 1,65 = 5,90 (lít), viết gọn 5,9 lít. Can còn 5,9 lít dầu; không cộng lượng đã bán.")], [("Lượng dầu còn lại", "5.9", "lít")])

add(5, "percentage_part_and_remainder", "Vườn có 250 cây, trong đó 40% là cây cam, còn lại là cây bưởi. Có bao nhiêu cây bưởi?",
    [given("g0", "250 cây", "250", "cây", "whole_count"), given("g1", "40% là cây cam", "40", "%", "orange_percent")],
    "Số cây bưởi thuộc phần còn lại của vườn.", ["Tất cả cây gồm cam và bưởi; tỉ số phần trăm cho biết phần cam của toàn vườn.", "Tìm phần cam rồi bớt khỏi toàn bộ cây, hoặc tìm phần trăm còn lại trước."],
    [("Tỉ số phần trăm trong đề đang nói về loại cây nào?", "Đề muốn tìm phần đã cho phần trăm hay phần còn lại?"), ("Có thể tìm số cây cam từ toàn bộ số cây rồi bớt khỏi vườn.", "Vì sao không lấy tỉ số phần trăm làm số cây?"), ("Hãy biểu diễn phần trăm thành các phần của toàn bộ, tìm số cây tương ứng rồi xác định phần bưởi.", "Đơn vị của đáp số là phần trăm hay cây?")],
    [step("Tìm số cây cam", "40% nghĩa là 40 trong 100 phần bằng nhau của toàn bộ, nên lấy toàn vườn nhân 40 rồi chia 100.", "250*40/100", "100", "cây", "Số cây cam là: 250 × 40 : 100 = 100 (cây)."), step("Tìm cây bưởi", "Vườn chỉ có cam và bưởi, nên bớt cây cam khỏi tổng được cây bưởi.", "250-{s0}", "150", "cây", "Số cây bưởi là: 250 − 100 = 150 (cây). Kiểm tra 100 + 150 = 250. Đáp số là 150 cây, không phải 150%.")], [("Số cây bưởi", "150", "cây")])

add(5, "sum_ratio", "Hai thùng chứa tất cả 96 lít nước. Lượng nước thùng thứ nhất bằng 3/5 lượng nước thùng thứ hai. Mỗi thùng có bao nhiêu lít nước?",
    [given("g0", "tất cả 96 lít", "96", "lít", "sum"), given("g1", "thứ nhất bằng 3/5 thứ hai", "3/5", "", "first_to_second_ratio")],
    "Lượng nước riêng của từng thùng.", ["Tỉ số so sánh thùng thứ nhất với thùng thứ hai, không phải với tổng nước.", "Vẽ các phần bằng nhau theo tỉ số rồi dùng tổng để tìm lượng trong từng phần."],
    [("Hãy xác định đúng thứ tự các thùng trong tỉ số.", "Các phần của tổng được tạo từ phần của những thùng nào?"), ("Cộng số phần của các thùng để biết tổng có bao nhiêu phần bằng nhau.", "Vì sao không lấy tổng nhân ngay với tỉ số giữa các thùng?"), ("Chia tổng theo tổng số phần, rồi gộp số phần ứng với từng thùng.", "Khi cộng lượng của các thùng vừa tìm, em phải thu lại lượng nào?")],
    [step("Tìm tổng số phần", "Thùng thứ nhất tương ứng 3 phần, thùng thứ hai 5 phần bằng nhau; tổng gồm tất cả các phần ấy.", "3+5", "8", "phần", "Tổng số phần bằng nhau là: 3 + 5 = 8 (phần)."), step("Tìm lượng trong mỗi phần", "96 lít trải đều trên 8 phần nên chia tổng theo tổng phần.", "96/{s0}", "12", "lít", "Mỗi phần có: 96 ÷ 8 = 12 (lít)."), step("Tìm thùng thứ nhất", "Thùng thứ nhất có 3 phần nên gộp 3 lượng mỗi phần.", "{s1}*3", "36", "lít", "Thùng thứ nhất có: 12 × 3 = 36 (lít)."), step("Tìm thùng thứ hai", "Thùng thứ hai có 5 phần nên gộp 5 lượng mỗi phần; không dùng 3/5 của tổng.", "{s1}*5", "60", "lít", "Thùng thứ hai có: 12 × 5 = 60 (lít). Kiểm tra 36 + 60 = 96 và 36/60 = 3/5.")], [("Thùng thứ nhất", "36", "lít"), ("Thùng thứ hai", "60", "lít")])

add(5, "motion_distance_remaining", "Một ô tô cần đi quãng đường 135 km. Xe đi đều với vận tốc 54 km/giờ trong 1,5 giờ rồi nghỉ. Xe còn phải đi bao nhiêu ki-lô-mét?",
    [given("g0", "quãng đường 135 km", "135", "km", "total_distance"), given("g1", "54 km/giờ", "54", "km/giờ", "constant_speed"), given("g2", "1,5 giờ", "1.5", "giờ", "elapsed_duration")],
    "Quãng đường chưa đi sau thời gian đã cho.", ["Vận tốc cho biết quãng đường đi được theo mỗi giờ khi xe chạy đều.", "Tìm quãng đường đã đi rồi tách khỏi toàn bộ hành trình."],
    [("Phân biệt quãng đường cả hành trình với quãng đường xe đã thực sự đi.", "Thông tin nào giúp tìm quãng đường đã đi?"), ("Khi vận tốc và thời gian dùng đơn vị phù hợp, nhân chúng để tìm quãng đường đã đi.", "Sau khi tìm phần đã đi, em dùng quan hệ nào để tìm phần còn lại?"), ("Tính phần đã đi trước, rồi bớt phần đó khỏi quãng đường cần đi.", "Em kiểm tra phần còn lại có cùng đơn vị với cả hành trình chưa?")],
    [step("Tìm quãng đường đã đi", "Chạy đều nghĩa là quãng đường tăng theo thời gian; vận tốc km/giờ nhân thời gian giờ được km.", "54*1.5", "81", "km", "1,5 giờ gồm 1 giờ và nửa giờ: đi 54 km rồi thêm 27 km, tổng 81 km. Quãng đường đã đi: 54 × 1,5 = 81 (km)."), step("Tìm quãng đường còn lại", "Hành trình gồm phần đã đi và chưa đi; bớt phần đã đi khỏi tổng.", "135-{s0}", "54", "km", "Quãng đường còn phải đi là: 135 − 81 = 54 (km). Con số 54 ở đáp số là quãng đường, khác đại lượng vận tốc 54 km/giờ trong đề.")], [("Quãng đường còn lại", "54", "km")])

add(5, "trapezoid_area", "Một mảnh đất hình thang có hai đáy dài 18 m và 12 m, chiều cao 7 m. Tính diện tích mảnh đất.",
    [given("g0", "đáy dài 18 m", "18", "m", "first_base"), given("g1", "đáy dài 12 m", "12", "m", "second_base"), given("g2", "chiều cao 7 m", "7", "m", "height")],
    "Diện tích mặt đất hình thang.", ["Chiều cao vuông góc với các đáy; không thay bằng cạnh bên.", "Có thể hình dung ghép các hình thang bằng nhau để hiểu vì sao diện tích liên quan tổng các đáy."],
    [("Hãy nhận ra các đáy song song và chiều cao của hình thang.", "Đề đã cho đúng chiều cao hay chỉ cho cạnh bên?"), ("Ghép các hình thang bằng nhau tạo hình bình hành có đáy bằng tổng các đáy của hình thang.", "Diện tích hình thang chiếm phần nào của hình ghép?"), ("Tính tổng các đáy, nhân chiều cao rồi chia theo số hình bằng nhau đã ghép.", "Đơn vị diện tích của đáp số cần được viết thế nào?")],
    [step("Tìm tổng các đáy", "Khi ghép 2 hình thang bằng nhau, đáy hình bình hành bằng tổng các đáy hình thang.", "18+12", "30", "m", "Tổng độ dài các đáy là: 18 + 12 = 30 (m)."), step("Tìm diện tích", "Hình bình hành ghép có diện tích tổng đáy nhân cao và gồm 2 hình thang bằng nhau; chia 2 để tìm diện tích mảnh đất.", "{s0}*7/2", "105", "m²", "Diện tích mảnh đất là: 30 × 7 : 2 = 105 (m²). Chiều cao phải vuông góc với các đáy; đơn vị m² vì đang đo mặt đất.")], [("Diện tích mảnh đất", "105", "m²")])


def exact_value(expression, previous):
    expression = re.sub(r"\{s(\d+)\}", lambda m: f"({previous[int(m[1])]})", expression)
    tree = ast.parse(expression, mode="eval")
    allowed = {ast.Add: operator.add, ast.Sub: operator.sub,
               ast.Mult: operator.mul, ast.Div: operator.truediv,
               ast.FloorDiv: operator.floordiv}
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return Fraction(ast.get_source_segment(expression, node))
        if isinstance(node, ast.BinOp) and type(node.op) in allowed:
            left, right = visit(node.left), visit(node.right)
            return Fraction(allowed[type(node.op)](left, right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -visit(node.operand)
        raise ValueError(f"Unsupported arithmetic in {expression}")
    return visit(tree.body), expression


def write_outputs():
    assert len(ROWS) == 25 and Counter(row["grade"] for row in ROWS) == {i: 5 for i in range(1, 6)}
    arithmetic = []
    for row in ROWS:
        assert row["split"] == "train" and not row["provenance"]["human_verified"]
        assert [h["level"] for h in row["hints"]] == [1, 2, 3]
        # Stronger than a numeric substring blacklist: the hint never supplies a
        # computed value or formula at all. Semantic usefulness needs peer review.
        for hint in row["hints"]:
            assert not re.search(r"\d|[=+*/{}]", hint["hint"] + hint["question"])
            assert hint["question"].count("?") == 1
        previous = []
        for i, item in enumerate(row["worked_steps"]):
            refs = [int(v) for v in re.findall(r"\{s(\d+)\}", item["expression"])]
            assert all(v < i for v in refs)
            actual, resolved = exact_value(item["expression"], previous)
            assert actual == Fraction(item["result"]), (row["sample_id"], item, actual)
            previous.append(str(actual))
            arithmetic.append(dict(sample_id=row["sample_id"], step_id=item["step_id"],
                                   expression=resolved, declared=item["result"], exact_actual=str(actual), passed=True))
        for answer in row["expected_answer"]:
            assert any(Fraction(answer["result"]) == Fraction(s["result"]) and answer["unit"] == s["unit"]
                       for s in row["worked_steps"])
    # Independent domain identities, not merely replaying the declared formulas.
    quotient, remainder = divmod(52, 6)
    assert (quotient, remainder) == (8, 4) and 52 == 6*quotient+remainder and 0 <= remainder < 6
    hours, minutes = divmod(92, 60)
    assert (hours, minutes) == (1, 32) and 92 == 60*hours+minutes and 0 <= minutes < 60
    assert 64+92 == 156 and 92-64 == 28
    assert Fraction(36,60) == Fraction(3,5) and 36+60 == 96
    assert Fraction(9,8)*Fraction(2,3) == Fraction(3,4)
    assert Fraction("5.9") + Fraction("1.65") - Fraction("2.8") == Fraction("4.75")
    output = HERE / "tutoring_seed25.jsonl"
    payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in ROWS).encode("utf-8")
    output.write_bytes(payload)
    checks = dict(
        dataset=output.name, samples=len(ROWS), grades=dict(Counter(str(r["grade"]) for r in ROWS)),
        sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload),
        exact_arithmetic_checks=arithmetic,
        independent_identity_checks=["divmod_52_6_and_recomposition", "divmod_92_60_and_recomposition",
                                     "sum_difference_recomposition", "sum_ratio_recomposition",
                                     "fraction_division_inverse", "decimal_reverse_flow"],
        observed_student_work_cases=sum(bool(r["student_work"]) for r in ROWS),
        distinct_problem_strings=len({r["problem"] for r in ROWS}),
        all_train_only=True, arithmetic_checks_passed=True,
        hint_character_checks_passed=True,
        semantic_peer_review_status="PENDING", curriculum_mapping_status="PENDING_PEER_MAPPING",
        sealed_validation_overlap_status="NOT_CHECKED_HERE_ROOT_CURATOR_MUST_DEDUP",
        all_primary_curriculum_covered=False, human_verified=False,
        caveats=["25 original seed cases are not a complete curriculum.",
                 "Exact calculations do not certify semantic faithfulness or pedagogy.",
                 "Current app calculator does not support //; those examples require a new explicit bounded contract.",
                 "Place-value rows need source-role resolution instead of arbitrary operands in current app formulas.",
                 "Canonical neutral rows are not directly valid app PlanDraft JSON."],
    )
    (HERE / "tutoring_seed25_checks.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: checks[k] for k in ("samples", "grades", "sha256", "bytes", "observed_student_work_cases", "arithmetic_checks_passed")}, ensure_ascii=False))


def audit_protected_cases():
    """Bounded no-overlap proof for known numeric development cases, not gold."""
    sys.path.insert(0, str(ROOT / "ai-training" / "thinking"))
    import teacher_math_data_v4 as previous
    protected, _, old_hashes, _ = previous.v3_catalog()
    pilot_cases, _, pilot_hashes = previous.supplemental_pilot_exclusions()
    protected |= pilot_cases
    fresh = HERE.parent / "teacher_math_v4" / "generated" / "val.jsonl"
    for line in fresh.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("topic") in previous.LOOKUP and row.get("parameters"):
            protected.add(previous.case_signature(previous.LOOKUP[row["topic"]],
                          {key: Fraction(value) for key, value in row["parameters"].items()}))
    collisions = []
    unsupported = []
    checked = 0
    for row in ROWS:
        expanded = []
        for index, item in enumerate(row["worked_steps"]):
            expression = re.sub(r"\{s(\d+)\}", lambda m: "(" + expanded[int(m[1])] + ")", item["expression"])
            expanded.append(expression)
            try:
                signature = previous.digest(previous.canonical_expression(expression))
            except (KeyError, ValueError, SyntaxError):
                unsupported.append(dict(sample_id=row["sample_id"], step_id=item["step_id"],
                                        expression=expression, reason="EUCLIDEAN_DIVISION_NOT_IN_PREVIOUS_CANONICAL_AST"))
                continue
            checked += 1
            if signature in protected:
                collisions.append(dict(sample_id=row["sample_id"], step_id=item["step_id"],
                                       expression=expression, signature=signature))
    evidence = dict(dataset="tutoring_seed25.jsonl", dataset_sha256=hashlib.sha256((HERE / "tutoring_seed25.jsonl").read_bytes()).hexdigest(),
                    excluded_numeric_case_count=len(protected), old_numeric_dataset_hashes=old_hashes,
                    pilot_hashes=pilot_hashes, fresh_val_sha256=hashlib.sha256(fresh.read_bytes()).hexdigest(),
                    checked_expanded_steps=checked, collisions=collisions, unsupported_canonical_steps=unsupported,
                    status="NO_COLLISION_IN_SUPPORTED_CANONICAL_EXPRESSIONS" if not collisions else "REQUIRES_REAUTHORING",
                    equivalence_limit="Previous bounded associative/commutative +/* and ordered -/division. No universal semantic equivalence, no concept challenge content read.",
                    unsupported_policy="CAPABILITY_PENDING_RESEARCH_ONLY_DO_NOT_AUTOEXPORT_TO_APP")
    (HERE / "tutoring_seed25_protected_case_check.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert not collisions, "Known development operation reused in seed."
    print(json.dumps({"protected_case_count": len(protected), "checked_expanded_steps": checked,
                      "collisions": len(collisions), "unsupported_steps": len(unsupported)}))


if __name__ == "__main__":
    write_outputs()
    audit_protected_cases()

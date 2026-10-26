"""New original Vietnamese teacher examples, with bounded mathematical contracts.

V3 is imported read-only for its exact AST interpreter and topic formulas. No
V3 row is replayed or relabelled. Exclusions are mathematical case signatures,
not failed validation examples inserted into training. AI authored != certified.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from dataclasses import replace
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import re

import teacher_math_data_v3 as previous

VERSION = "mvk_teacher_math_v4_original_teacher_20261013"
SEED = 20261014
SYSTEM = previous.SYSTEM + (
    " Mỗi lời giải phải nói rõ dữ kiện dùng để tìm đại lượng nào; không coi số dư "
    "là thương. Giải thích đúng từng cột nhớ hoặc đổi hàng khi đặt tính, không suy "
    "đoán dấu nhớ chưa nhìn thấy. Với hint, chỉ hỏi một bước đầu hữu ích: không "
    "đưa toàn bộ cách giải, không tính ra số mới, không nói đáp số."
)
evaluate_expression = previous.evaluate_expression
number = previous.number
expression_number = previous.expression_number
digest = previous.digest
Topic = previous.Topic
PLACES = previous.PLACES
SPLITS = ("train", "val")

# These are fresh complete questions, not prefixes on held-out V3 questions.
# Each tuple supplies two train wordings and a reserved new-val wording.
WORDINGS = {
 "add_join": ("Hà đang giữ {a} viên sỏi; mẹ cho Hà thêm {b} viên sỏi. Bây giờ Hà giữ mấy viên?", "Trong rổ có {a} quả táo và vừa xếp vào rổ {b} quả nữa. Đếm tất cả số quả táo trong rổ.", "Quân mang {a} chiếc bút, được bạn tặng {b} chiếc. Sau khi nhận, Quân có mấy chiếc bút?"),
 "sub_remaining": ("Cô có {a} nhãn vở và đã phát {b} nhãn vở. Cô còn giữ mấy nhãn?", "Một đĩa có {a} quả; đã ăn {b} quả từ đĩa đó. Số quả chưa ăn là bao nhiêu?", "Hùng giữ {a} viên bi rồi tặng {b} viên. Hãy tìm số viên bi vẫn ở chỗ Hùng."),
 "missing_addend": ("Hộp có {a} chiếc bút, sau khi bỏ thêm bút thì hộp có {b} chiếc. Đã bỏ thêm mấy chiếc?", "Hà đã vẽ {a} ngôi sao và muốn đủ {b} ngôi sao. Hà phải vẽ thêm mấy ngôi sao?", "Bình đã nhặt {a} viên sỏi; cần nhặt thêm để đạt {b} viên. Cần nhặt thêm bao nhiêu?"),
 "compare_difference": ("Tổ Một có {a} nhãn vở, tổ Hai có {b} nhãn. Tổ Một hơn tổ Hai mấy nhãn?", "Mai đọc được {a} trang còn Hà đọc {b} trang. Số trang Mai đọc nhiều hơn là bao nhiêu?", "Túi thứ nhất chứa {a} viên bi và túi thứ hai chứa {b} viên. Túi thứ nhất có nhiều hơn mấy viên?"),
 "tens_place_value": ("Với số {a}, hãy tính riêng giá trị của chữ số ở hàng chục.", "Hàng chục đóng góp bao nhiêu đơn vị vào số {a}?", "Phân tích số {a}: phần ứng với chữ số hàng chục bằng bao nhiêu đơn vị?"),
 "equal_groups": ("Mỗi hộp đựng {b} viên bi, có {a} hộp đều như vậy. Hãy đếm tổng số viên bi.", "Có {a} đĩa, mỗi đĩa xếp {b} cái bánh. Tất cả các đĩa chứa mấy cái bánh?", "{a} bạn mỗi bạn được {b} chiếc bút. Cô đã phát tất cả mấy chiếc bút?"),
 "share_exact": ("{a} viên bi được chia hết và đều cho {b} bạn. Một bạn có bao nhiêu viên?", "Xếp {a} cái bánh đều vào {b} đĩa, không thừa bánh. Mỗi đĩa có mấy cái?", "Phân phối đều {a} quyển vở cho {b} bạn và không còn quyển nào. Số vở mỗi bạn là bao nhiêu?"),
 "missing_factor": ("Thừa số chưa biết nhân với {b} cho tích {a}. Thừa số chưa biết là số nào?", "Phép nhân có một thừa số {b} và tích {a}. Hãy tìm thừa số còn thiếu.", "Có phép nhân: một số nhân {b} được {a}. Hỏi số ấy bằng bao nhiêu?"),
 "multistep_add_sub": ("Cửa hàng có {a} quyển vở, nhận thêm {b} quyển và bán đi {c} quyển. Sau cả hai việc còn bao nhiêu?", "Thư viện ban đầu có {a} sách, bổ sung {b} sách rồi cho mượn {c} sách. Tìm số sách còn trong thư viện.", "Đội có {a} chiếc bút, được nhận thêm {b} chiếc rồi phát {c} chiếc. Tính số chiếc bút chưa phát."),
 "groups_after_sale": ("{a} túi mỗi túi đựng {b} viên kẹo. Lấy từ tổng số đó {c} viên; còn mấy viên?", "Kho có {a} hộp, mỗi hộp chứa {b} chiếc bút; phát {c} chiếc. Số bút còn lại là bao nhiêu?", "Chuẩn bị {a} đĩa, mỗi đĩa có {b} bánh, sau đó ăn {c} bánh. Hỏi còn mấy bánh?"),
 "money_change": ("Bút giá {a} đồng; người mua đưa {b} đồng. Cửa hàng cần trả lại bao nhiêu đồng?", "Hà mang {b} đồng, mua một món đồ giá {a} đồng. Số tiền Hà còn lại là bao nhiêu?", "Mua đồ hết {a} đồng và thanh toán bằng {b} đồng. Hỏi số tiền nhận lại."),
 "elapsed_minutes": ("Trong cùng một giờ, một tiết đọc bắt đầu tại phút {a}, kết thúc tại phút {b}. Tiết đó dài bao nhiêu phút?", "Hai mốc phút trong cùng giờ là {a} và {b}, mốc đầu là lúc bắt đầu. Tính khoảng thời gian đến mốc sau.", "Một việc bắt đầu ở phút {a} và xong ở phút {b} trong cùng giờ. Thời gian làm việc là mấy phút?"),
 "division_remainder": ("Từ {a} viên kẹo, đóng các túi có đủ {b} viên. Đóng tối đa số túi đủ; có mấy viên không đóng được vào túi đủ?", "Xếp {a} chiếc bút thành hộp đầy, mỗi hộp {b} chiếc. Khi đã xếp nhiều hộp đầy nhất, còn lẻ mấy chiếc?", "Chia {a} viên bi thành từng nhóm đủ {b} viên. Hỏi phần dư sau khi lập nhiều nhóm đủ nhất."),
 "order_operations": ("Tính biểu thức {a} + {b} × {c}, không thêm ngoặc.", "Một số hạng bằng {a}, số hạng còn lại là tích {b} với {c}. Tính tổng hai số hạng.", "Hãy tính giá trị {a} cộng {b} nhân {c} theo quy tắc thứ tự phép tính."),
 "length_m_to_cm": ("Đổi chiều dài {a} mét ra xăng-ti-mét.", "Một sợi dây đo được {a} m. Viết lại số đo của chính sợi dây bằng cm.", "Số đo {a} m được biểu diễn bằng bao nhiêu cm?"),
 "hours_minutes": ("Một buổi gồm {a} giờ học và thêm {b} phút nghỉ. Tính tổng thời gian học cộng thời gian nghỉ bằng phút.", "Hai khoảng thời gian nối tiếp là {a} giờ và {b} phút. Cộng cả hai khoảng được mấy phút?", "Chuyến sinh hoạt có {a} giờ hoạt động cộng {b} phút giải lao. Hỏi tổng số phút của toàn buổi."),
 "hours_minutes_active": ("Buổi sinh hoạt kéo dài tổng cộng {a} giờ; trong đó nghỉ {b} phút. Riêng thời gian hoạt động là mấy phút?", "Toàn bộ chuyến đi dài {a} giờ, bao gồm {b} phút dừng nghỉ. Tính số phút đang di chuyển.", "Một buổi học và nghỉ có tổng {a} giờ; phần nghỉ là {b} phút. Có bao nhiêu phút học?"),
 "mass_kg_to_g": ("Khối lượng {a} ki-lô-gam viết theo gam là bao nhiêu?", "Bao hàng cân nặng {a} kg. Hãy ghi khối lượng bao đó bằng g.", "Từ số đo {a} kg, đổi sang đơn vị gam cho cùng một vật."),
 "rectangle_perimeter": ("Một tấm bìa chữ nhật dài {a} cm, rộng {b} cm. Tính độ dài viền toàn bộ tấm bìa.", "Khu đất chữ nhật có các cạnh kề {a} cm và {b} cm. Tổng độ dài bốn cạnh bằng bao nhiêu cm?", "Cần dây để viền hình chữ nhật dài {a} cm rộng {b} cm. Cần mấy cm dây?"),
 "square_perimeter": ("Bốn cạnh một hình vuông đều bằng {a} cm. Cộng độ dài bốn cạnh được mấy cm?", "Mảnh giấy vuông có cạnh {a} cm. Cần viền quanh bằng bao nhiêu cm dây?", "Với hình vuông cạnh {a} cm, hãy tính chu vi đường bao."),
 "rectangle_area": ("Tấm bìa chữ nhật dài {a} cm và rộng {b} cm. Hỏi diện tích tấm bìa theo cm².", "Một hình chữ nhật có {a} cm chiều dài, {b} cm chiều rộng. Bề mặt rộng bao nhiêu cm²?", "Mỗi hàng có {a} ô vuông 1 cm², ghép {b} hàng thành chữ nhật. Tổng diện tích là bao nhiêu cm²?"),
 "square_area": ("Mảnh bìa vuông cạnh {a} cm có bề mặt rộng bao nhiêu cm²?", "Mỗi hàng có {a} ô vuông 1 cm², có {a} hàng tạo thành hình vuông. Tính diện tích.", "Hãy tính diện tích một hình vuông có cạnh dài {a} cm."),
 "table_total": ("Bảng thống kê số sách ba tổ: tổ Một {a}, tổ Hai {b}, tổ Ba {c}. Cộng số sách của ba tổ.", "Số cây ba lớp trồng lần lượt là {a}, {b}, {c}. Tính tổng số cây được ghi.", "Bảng số bút ở ba ngăn ghi {a}, {b}, {c}. Trong cả ba ngăn có mấy chiếc bút?"),
 "sum_difference_large": ("Tổng hai số bằng {a}, hiệu số lớn trừ số bé bằng {b}. Hãy tìm riêng số lớn.", "Hai số có tổng {a}, số lớn hơn số bé {b}. Giá trị số lớn là bao nhiêu?", "Cho tổng {a} và hiệu {b} của hai số. Số lớn trong hai số là số nào?"),
 "sum_difference_small": ("Tổng hai số bằng {a}, hiệu số lớn trừ số bé bằng {b}. Hãy tìm riêng số bé.", "Hai số có tổng {a}, số lớn hơn số bé {b}. Giá trị số bé là bao nhiêu?", "Cho tổng {a} và hiệu {b} của hai số. Số bé trong hai số là số nào?"),
 "fraction_add": ("Cộng hai phân số {a} và {b}, viết kết quả tối giản.", "Thực hiện phép cộng phân số: {a} + {b}.", "Hãy cộng phân số thứ nhất {a} với phân số thứ hai {b}, rồi rút gọn."),
 "fraction_subtract": ("Trừ phân số {b} khỏi phân số {a}, viết kết quả tối giản.", "Thực hiện phép trừ phân số: {a} - {b}.", "Hãy lấy phân số {a} bớt phân số {b}, rồi rút gọn."),
 "fraction_multiply": ("Nhân hai phân số {a} và {b}, viết kết quả tối giản.", "Thực hiện phép nhân phân số: {a} × {b}.", "Hãy nhân phân số thứ nhất {a} với phân số thứ hai {b}, rồi rút gọn."),
 "fraction_divide": ("Lấy phân số {a} chia cho phân số khác không {b}; viết kết quả tối giản.", "Thực hiện phép chia phân số: {a} : {b}.", "Hãy chia phân số bị chia {a} cho phân số chia {b}, rồi rút gọn."),
 "average_three": ("Ba giá trị {a}, {b}, {c} có trung bình cộng bằng bao nhiêu?", "Số sách ba bạn đọc là {a}, {b}, {c}. Nếu chia đều tổng ấy, mỗi bạn tương ứng mấy quyển?", "Tính trung bình cộng của bộ ba số {a}, {b}, {c}."),
 "fraction_of_quantity": ("Số bút là {a}; chọn phân số {b} của số bút đó. Đã chọn mấy chiếc?", "Có {a} viên bi, lấy phần {b} tổng số viên. Tính số viên bi được lấy.", "Trong {a} quyển vở, số phát đi bằng phân số {b} tổng số. Phát bao nhiêu quyển?"),
 "parallelogram_area": ("Hình bình hành có đáy {a} cm và chiều cao vuông góc tương ứng {b} cm. Tính diện tích theo cm².", "Cặp đáy và đường cao của hình bình hành dài {a} cm, {b} cm. Diện tích là bao nhiêu?", "Tính diện tích hình bình hành từ đáy {a} cm và đường cao tương ứng {b} cm."),
 "ratio_share": ("Hai nhóm chia {a} quyển vở theo số phần bằng nhau: nhóm đầu {b} phần, nhóm sau {c} phần. Nhóm đầu nhận mấy quyển?", "Tổng số bút hai nhóm là {a}, tỉ số nhóm đầu:nhóm sau là {b}:{c}. Tìm số bút nhóm đầu.", "Chia {a} đồ vật cho hai nhóm theo tỉ số {b}:{c}. Nhóm ứng với {b} phần nhận mấy đồ vật?"),
 "multiples_missing": ("Dãy tăng đúng {a} đơn vị sau mỗi bước, bắt đầu bằng {a}, {b}. Tìm số thứ ba.", "Quy luật là cộng thêm {a} mỗi lần; hai số đầu {a} và {b}. Số tiếp theo là số nào?", "Dãy số có hiệu giữa hai số liền nhau bằng {a}, đã ghi {a}, {b}. Hãy ghi số thứ ba."),
 "arithmetic_sequence": ("Dãy bắt đầu {a}, {b} và mỗi bước đều tăng đúng {c}. Số đứng sau {b} là bao nhiêu?", "Có dãy tăng đều với số đầu {a}, số thứ hai {b}, mức tăng mỗi lần {c}. Tìm số thứ ba.", "Hai số đầu là {a} và {b}; quy luật là thêm {c} sau mỗi bước. Tìm số kế tiếp."),
 "decimal_add": ("Cộng số thập phân {a} với số thập phân {b}.", "Thực hiện cộng hai số có dấu phẩy: {a} + {b}.", "Hai số thập phân cần cộng là {a} và {b}. Tính tổng."),
 "decimal_subtract": ("Lấy số thập phân {a} trừ số thập phân {b}.", "Thực hiện trừ hai số có dấu phẩy: {a} - {b}.", "Từ số thập phân {a}, bớt đi {b}. Còn bao nhiêu?"),
 "decimal_multiply": ("Nhân số thập phân {a} với số thập phân {b}.", "Thực hiện nhân hai số có dấu phẩy: {a} × {b}.", "Hai số thập phân cần nhân là {a} và {b}. Tính tích."),
 "decimal_divide": ("Lấy số thập phân {a} chia cho số thập phân khác không {b}.", "Thực hiện chia hai số có dấu phẩy: {a} : {b}.", "Số bị chia là {a}, số chia là {b}. Hãy tìm thương thập phân."),
 "percent_part": ("Tổng số bút là {a}, phần chọn chiếm {b}%. Hỏi đã chọn mấy chiếc bút?", "Một kho có {a} viên bi; lấy ra {b}% tổng số. Tìm số viên bi lấy ra.", "Trong {a} quyển vở, phần phát bằng {b}% tổng số vở. Phát mấy quyển?"),
 "percent_whole": ("Phần {b}% của cả lượng là {a}. Hãy tìm giá trị toàn bộ lượng ấy.", "Có {a} tương ứng {b}% một tổng chưa biết. Hỏi tổng đó bằng bao nhiêu?", "Một phần chiếm {b}% toàn bộ và có giá trị {a}. Tìm giá trị của 100% toàn bộ."),
 "percent_ratio": ("Có {a} sản phẩm tốt trong tất cả {b} sản phẩm. Sản phẩm tốt chiếm mấy phần trăm tổng số?", "Phần được chọn bằng {a}, toàn bộ bằng {b}. Tính tỉ lệ phần trăm phần được chọn.", "Tổng {b} bạn, trong đó {a} bạn tham gia. Số tham gia chiếm mấy phần trăm?"),
 "triangle_area": ("Một tam giác có đáy {a} cm, chiều cao vuông góc với đáy ấy {b} cm. Diện tích theo cm² là bao nhiêu?", "Đáy tam giác dài {a} cm, đường cao của đáy đó dài {b} cm. Hãy tính diện tích.", "Hãy tính diện tích tam giác có đáy {a} cm và đường cao tương ứng {b} cm."),
 "trapezoid_area": ("Hai đáy song song hình thang dài {a} cm, {b} cm; khoảng cách vuông góc giữa đáy {c} cm. Tính diện tích.", "Một hình thang có đáy lớn {a} cm, đáy bé {b} cm, đường cao {c} cm. Diện tích là bao nhiêu cm²?", "Cho hình thang: hai đáy {a} cm và {b} cm, chiều cao {c} cm. Tính diện tích theo cm²."),
 "circle_area": ("Hình tròn có bán kính {a} cm; dùng pi bằng 3,14. Hỏi diện tích theo cm².", "Một mặt tròn có bán kính {a} cm. Tính diện tích với giá trị gần đúng pi=3,14.", "Từ bán kính {a} cm, hãy tính diện tích hình tròn theo pi=3,14."),
 "circle_perimeter": ("Đường tròn có bán kính {a} cm; dùng pi bằng 3,14. Hỏi chu vi theo cm.", "Một mặt tròn có bán kính {a} cm. Tính đường bao với giá trị gần đúng pi=3,14.", "Từ bán kính {a} cm, hãy tính chu vi đường tròn theo pi=3,14."),
 "box_volume": ("Hộp chữ nhật có các kích thước dài {a} cm, rộng {b} cm, cao {c} cm. Hỏi thể tích theo cm³.", "Đáy một hộp chữ nhật dài {a} cm, rộng {b} cm; hộp cao {c} cm. Thể tích bằng bao nhiêu?", "Hãy tính thể tích hình hộp chữ nhật từ dài {a} cm, rộng {b} cm, cao {c} cm."),
 "cube_surface": ("Một khối lập phương cạnh {a} cm. Tính tổng diện tích cả sáu mặt theo cm².", "Hộp lập phương kín có cạnh {a} cm. Hỏi diện tích cần dán phủ toàn bộ các mặt.", "Từ cạnh {a} cm của hình lập phương, tính diện tích toàn phần."),
 "distance_from_speed_time": ("Trong {b} giờ, xe đi đều {a} km/giờ và không dừng nghỉ. Hỏi đã đi mấy km?", "Một chuyển động đều có vận tốc {a} km/giờ, kéo dài {b} giờ. Tìm quãng đường.", "Xe giữ vận tốc {a} km/giờ và chạy liên tục {b} giờ. Quãng đường bằng bao nhiêu km?"),
 "speed_from_distance_time": ("Xe chạy đều {a} km hết {b} giờ, không nghỉ. Mỗi giờ đi được mấy km?", "Một hành trình dài {a} km được chạy trong {b} giờ. Tìm vận tốc trung bình theo km/giờ.", "Từ quãng đường {a} km và thời gian {b} giờ, tính vận tốc trung bình."),
 "time_from_distance_speed": ("Xe phải đi {a} km với vận tốc đều {b} km/giờ, không dừng nghỉ. Hỏi thời gian theo giờ.", "Đi một quãng {a} km với {b} km trong mỗi giờ, không nghỉ. Mất mấy giờ?", "Từ quãng đường {a} km và vận tốc không đổi {b} km/giờ, tìm thời gian đi."),
 "area_unit_conversion": ("Diện tích đo được {a} m². Đổi cùng diện tích đó sang cm².", "Hãy chuyển số đo diện tích {a} mét vuông thành xăng-ti-mét vuông.", "Một vùng rộng {a} m², số đo của vùng ấy theo cm² là bao nhiêu?"),
 "volume_unit_conversion": ("Thể tích đo được {a} dm³. Đổi cùng thể tích đó sang cm³.", "Hãy chuyển số đo thể tích {a} đề-xi-mét khối thành xăng-ti-mét khối.", "Một khối có thể tích {a} dm³, số đo của khối ấy theo cm³ là bao nhiêu?"),
 "proportional_direct": ("Mỗi quyển vở có cùng giá; {a} quyển hết {b} đồng. Mua {c} quyển sẽ hết mấy đồng?", "{a} chiếc bút cùng giá có giá tổng {b} đồng. Giá mỗi chiếc giữ nguyên, hỏi tiền {c} chiếc.", "Với cùng đơn giá, {a} sản phẩm hết {b} đồng. Tính tiền mua {c} sản phẩm."),
 "proportional_inverse": ("Cùng một việc, {a} người cùng năng suất làm hết {b} ngày. {c} người có cùng năng suất ấy cần mấy ngày?", "Công việc và năng suất từng người không đổi: {a} người cần {b} ngày. Hỏi số ngày nếu dùng {c} người.", "Giữ lượng công việc và năng suất mỗi người, đổi từ {a} người làm {b} ngày sang {c} người. Cần bao nhiêu ngày?"),
 "probability_count": ("Có {a} thẻ đỏ và {b} thẻ xanh cùng kích thước. Trộn kỹ rồi chọn đều một thẻ. Phân số các trường hợp lấy đỏ là bao nhiêu?", "Mọi viên bi đều có cơ hội được chọn như nhau; {a} viên đỏ, {b} viên xanh. Phân số khả năng chọn đỏ là gì?", "Chọn ngẫu nhiên đều một trong {a} vật đỏ và {b} vật xanh cùng loại. Tỉ số khả năng chọn đỏ bằng bao nhiêu?"),
 "empirical_frequency": ("Thực hiện {b} lần thử, thấy đỏ {a} lần. Tính tỉ số quan sát đỏ so với tổng số lần thử.", "Bảng thực nghiệm ghi sự kiện xảy ra {a} lần trên {b} lần thử. Hãy viết tần suất quan sát bằng phân số.", "Kết quả đã quan sát: {a} lần thành công trong {b} lần thử. Tỉ số số lần thành công là bao nhiêu?"),
 "vertical_add": ("Hãy cộng {a} với {b} bằng đặt tính thẳng hàng và giải thích từng cột.", "Hai số tự nhiên {a}, {b} cần được cộng theo cột từ phải sang trái. Tính và giải thích cách nhớ.", "Đặt hai số {a} và {b} đúng hàng, thực hiện phép cộng và nói cách làm từng cột."),
 "vertical_subtract": ("Hãy đặt tính {a} trừ {b}, giải thích từng cột và cách đổi hàng nếu cần.", "Thực hiện phép trừ số tự nhiên {a} bớt {b} theo cột, nêu các lần đổi từ hàng bên trái.", "Đặt số bị trừ {a} và số trừ {b} thẳng hàng, tính hiệu và nói từng cột."),
}

HINTS = {t.name:t.hint for t in previous.TOPICS}
HINTS.update({
 "missing_addend":"Em dùng số đã có và số muốn đủ thế nào để tìm phần cần thêm?",
 "missing_factor":"Em cần dùng tích và thừa số đã biết thế nào để tìm thừa số chưa biết?",
 "table_total":"Để tìm tổng trong bảng này, em cần cộng số của những nhóm nào?",
 "groups_after_sale":"Trước khi xét phần đã lấy ra, em có thể tìm tổng số đồ vật bằng số nhóm và số mỗi nhóm thế nào?",
 "hours_minutes":"Đề yêu cầu cộng thời gian hoạt động với thời gian nghỉ; em cần đưa hai khoảng về cùng đơn vị nào?",
 "hours_minutes_active":"Thời gian nghỉ đã nằm trong tổng thời gian; em cần tìm phần hoạt động từ tổng và phần nghỉ thế nào?",
 "multiples_missing":"Đề đã cho mức tăng cố định; từ số thứ hai em thêm đúng lượng nào để tìm số thứ ba?",
 "arithmetic_sequence":"Đề quy định mỗi bước tăng cùng một lượng; từ số thứ hai em cần làm gì với lượng tăng đó?",
 "division_remainder":"Em có thể tìm số nhóm đủ rồi so với tổng ban đầu để xác định phần chưa đủ một nhóm như thế nào?",
 "fraction_divide":"Em cần đổi số chia thành phân số nghịch đảo như thế nào trước khi nhân?",
 "distance_from_speed_time":"Vận tốc đã không đổi; em dùng quãng đường đi trong mỗi giờ và số giờ thế nào?",
 "vertical_add":"Em sẽ cộng hàng nào trước và xử lý tổng của cột thế nào khi đủ một chục?",
 "vertical_subtract":"Em bắt đầu ở hàng nào, và khi chữ số trên chưa đủ để trừ em đổi từ hàng bên trái ra sao?",
})
UNIT_VARIANTS = {
 "add_join":("viên","quả","chiếc"), "sub_remaining":("nhãn","quả","viên"),
 "missing_addend":("chiếc","ngôi sao","viên"), "compare_difference":("nhãn","trang","viên"),
 "equal_groups":("viên","cái","chiếc"), "share_exact":("viên","cái","quyển"),
 "multistep_add_sub":("quyển","sách","chiếc"), "groups_after_sale":("viên","chiếc","bánh"),
 "table_total":("sách","cây","chiếc"), "average_three":("","quyển",""),
 "fraction_of_quantity":("chiếc","viên","quyển"), "ratio_share":("quyển","bút","đồ vật"),
 "percent_part":("chiếc","viên","quyển"), "division_remainder":("viên","chiếc","viên"),
}
FACT_ROLES = {
 "add_join":{"a":"initial_quantity","b":"added_quantity"},
 "sub_remaining":{"a":"initial_quantity","b":"removed_quantity"},
 "missing_addend":{"a":"initial_quantity","b":"desired_total"},
 "compare_difference":{"a":"larger_quantity","b":"smaller_quantity"},
 "tens_place_value":{"a":"observed_two_digit_number"},
 "equal_groups":{"a":"number_of_equal_groups","b":"quantity_per_group"},
 "share_exact":{"a":"total_quantity","b":"number_of_equal_groups"},
 "missing_factor":{"a":"known_product","b":"known_factor"},
 "multistep_add_sub":{"a":"initial_quantity","b":"added_quantity","c":"removed_quantity"},
 "groups_after_sale":{"a":"number_of_groups","b":"quantity_per_group","c":"removed_from_total"},
 "money_change":{"a":"item_price","b":"money_paid"},
 "elapsed_minutes":{"a":"start_minute_same_hour","b":"end_minute_same_hour"},
 "division_remainder":{"a":"total_objects","b":"objects_per_full_group"},
 "order_operations":{"a":"standalone_addend","b":"first_factor","c":"second_factor"},
 "hours_minutes":{"a":"whole_hours_first_interval","b":"additional_minutes_second_interval"},
 "hours_minutes_active":{"a":"total_hours_including_rest","b":"rest_minutes_inside_total"},
 "sum_difference_large":{"a":"sum_of_two_numbers","b":"large_minus_small"},
 "sum_difference_small":{"a":"sum_of_two_numbers","b":"large_minus_small"},
 "fraction_add":{"a":"first_fraction","b":"second_fraction"},
 "fraction_subtract":{"a":"minuend_fraction","b":"subtrahend_fraction"},
 "fraction_multiply":{"a":"first_fraction_factor","b":"second_fraction_factor"},
 "fraction_divide":{"a":"dividend_fraction","b":"nonzero_divisor_fraction"},
 "fraction_of_quantity":{"a":"whole_quantity","b":"fraction_of_whole"},
 "ratio_share":{"a":"whole_quantity","b":"first_group_equal_parts","c":"second_group_equal_parts"},
 "multiples_missing":{"a":"explicit_constant_increase","b":"second_term"},
 "arithmetic_sequence":{"a":"first_term","b":"second_term","c":"explicit_constant_increase"},
 "percent_part":{"a":"whole_quantity","b":"percent_number"},
 "percent_whole":{"a":"known_part_quantity","b":"percent_number_of_known_part"},
 "percent_ratio":{"a":"selected_part","b":"whole_quantity"},
 "triangle_area":{"a":"base_length_cm","b":"corresponding_perpendicular_height_cm"},
 "trapezoid_area":{"a":"first_parallel_base_cm","b":"second_parallel_base_cm","c":"perpendicular_height_cm"},
 "box_volume":{"a":"base_length_cm","b":"base_width_cm","c":"perpendicular_height_cm"},
 "distance_from_speed_time":{"a":"constant_speed_km_per_hour","b":"travel_time_hours"},
 "speed_from_distance_time":{"a":"distance_km","b":"travel_time_hours"},
 "time_from_distance_speed":{"a":"distance_km","b":"constant_speed_km_per_hour"},
 "proportional_direct":{"a":"known_item_count","b":"known_total_price","c":"requested_item_count"},
 "proportional_inverse":{"a":"original_worker_count","b":"original_days","c":"new_worker_count_same_productivity"},
 "probability_count":{"a":"red_equal_likelihood_objects","b":"blue_equal_likelihood_objects"},
 "empirical_frequency":{"a":"observed_event_count","b":"total_trial_count"},
 "vertical_add":{"a":"first_addend","b":"second_addend"},
 "vertical_subtract":{"a":"minuend","b":"subtrahend"},
}
TOPICS = [replace(t,templates=WORDINGS[t.name],hint=HINTS[t.name]) for t in previous.TOPICS]
TOPICS += [Topic("hours_minutes_active",5,WORDINGS["hours_minutes_active"],HINTS["hours_minutes_active"],"phút"),
           Topic("arithmetic_sequence",4,WORDINGS["arithmetic_sequence"],HINTS["arithmetic_sequence"])]
LOOKUP = {t.name:t for t in TOPICS}

def independent_answer(name, values):
    if name=="hours_minutes_active":return Fraction(60)*values["a"]-values["b"]
    if name=="arithmetic_sequence":return values["b"]+values["c"]
    return previous.independent_answer(name,values)

def column_trace(a:int,b:int,symbol:str):
    """Audit-only states; no target row may claim unseen student carry marks."""
    width=max(len(str(a)),len(str(b)))
    digits=list(map(int,str(a).zfill(width)[::-1]));other=list(map(int,str(b).zfill(width)[::-1]))
    records=[];carry=0
    for i in range(width):
        before=digits[:];incoming=carry;donor=None
        if symbol=="+":
            total=digits[i]+other[i]+carry;written=total%10;carry=total//10
        else:
            if digits[i]<other[i]:
                donor=i+1
                while donor<width and digits[donor]==0:donor+=1
                if donor==width:raise ValueError("NEGATIVE_SUBTRACTION")
                digits[donor]-=1
                for j in range(donor-1,i,-1):digits[j]=9
                digits[i]+=10
            total=digits[i]-other[i];written=total;carry=0
        records.append({"column":i,"place":PLACES[i],"left_before":before[i],"left_after":digits[i],
          "right":other[i],"incoming_carry":incoming,"outgoing_carry":carry,"donor_column":donor,
          "digits_before":before,"digits_after":digits[:],"total":total,"written":written})
    if symbol=="+" and carry:records.append({"column":width,"place":PLACES[width],"carry_only":carry,"written":carry,"total":carry})
    reconstructed=sum(s["written"]*10**s["column"] for s in records)
    if reconstructed!=(a+b if symbol=="+" else a-b):raise ValueError("COLUMN_INVERSE_RECONSTRUCTION")
    return records

def column_steps(a,b,symbol):
    rows=[]
    for s in column_trace(a,b,symbol):
        if "carry_only" in s:
            rows.append((f"Phần nhớ còn lại ở hàng {s['place']}; viết {s['written']}.",str(s["written"]),""));continue
        if symbol=="+":
            expr=f"{s['left_before']}+{s['right']}"+(f"+{s['incoming_carry']}" if s["incoming_carry"] else "")
            explanation=f"Hàng {s['place']}: "
            if s["incoming_carry"]:explanation+=f"cộng thêm {s['incoming_carry']} nhớ từ hàng bên phải. "
            explanation+=f"Tổng cột là {s['total']}; viết {s['written']}. "
            explanation+=f"Nhớ {s['outgoing_carry']} sang hàng {PLACES[s['column']+1]}." if s["outgoing_carry"] else "Không có phần nhớ mới."
        else:
            expr=f"{s['left_after']}-{s['right']}";explanation=f"Hàng {s['place']}: "
            donor=s["donor_column"]
            if donor is not None:
                original=s["digits_before"][donor];changed=s["digits_after"][donor]
                explanation+=f"đổi 1 {PLACES[donor]} thành 10 đơn vị hàng kế bên; chữ số hàng {PLACES[donor]} giảm từ {original} còn {changed}. "
                if donor>s["column"]+1:explanation+="Đổi tiếp qua các hàng 0; mỗi hàng trung gian còn 9 sau khi chuyển 1 sang bên phải. "
                explanation+=f"Ở hàng đang trừ, {s['left_before']} thành {s['left_after']}. "
            elif s["left_before"]!=int(str(a).zfill(max(len(str(a)),len(str(b))))[::-1][s["column"]]):
                explanation+="Dùng chữ số đã giảm sau lần đổi ở cột trước. "
            explanation+=f"Trừ {s['right']} được {s['written']}; viết {s['written']}."
        rows.append((explanation,expr,""))
    whole=len(rows)
    rows += [("Ghép các chữ số kết quả đúng giá trị hàng; bỏ số 0 thừa ở đầu.","a"+symbol+"b",""),
             ("Đối chiếu bằng phép tính ngược để kiểm tra kết quả vừa tìm.",f"r{whole}-b" if symbol=="+" else f"r{whole}+b","")]
    return rows

def steps_recipe(t,values):
    n=t.name;u=t.unit;a=values.get("a");b=values.get("b")
    if n.startswith("vertical_"):return column_steps(int(a),int(b),"+" if n=="vertical_add" else "-")
    if n=="tens_place_value":
        tens,ones=divmod(int(a),10)
        return [(f"Số {int(a)} gồm {tens} chục và {ones} đơn vị; bớt riêng {ones} đơn vị để giữ giá trị của phần chục, không lấy chữ số hàng chục làm đáp số.",f"a-{ones}",u)]
    if n=="hours_minutes_active":return [("Đổi tổng thời gian, vốn đã gồm thời gian nghỉ, sang phút.","a*60","phút"),("Lấy tổng phút trừ phút nghỉ để tìm riêng phút hoạt động.","r0-b","phút")]
    if n=="arithmetic_sequence":return [("Quy luật đề cho là tăng đều, nên cộng mức tăng với số thứ hai; không nhân đôi số thứ hai.","b+c",u)]
    if n=="division_remainder":
        quotient,remainder=divmod(int(a),int(b))
        return [("Tìm số đồ vật đã nằm trong các nhóm đủ bằng số nhóm đủ nhân số mỗi nhóm; đây chưa phải số dư.",f"{quotient}*b",u),("Lấy tổng ban đầu trừ lượng trong nhóm đủ để tìm số dư, nhỏ hơn số mỗi nhóm.","a-r0",u)]
    if n.startswith("fraction_") and n!="fraction_of_quantity":
        x,y=Fraction(a),Fraction(b);op={"fraction_add":"+","fraction_subtract":"-","fraction_multiply":"*","fraction_divide":"/"}[n]
        if op in ("+","-"):
            common=x.denominator*y.denominator//previous.gcd(x.denominator,y.denominator)
            lhs=x.numerator*(common//x.denominator);rhs=y.numerator*(common//y.denominator)
            numerator=lhs+rhs if op=="+" else lhs-rhs
            divisor=previous.gcd(abs(numerator),common)
            return [(f"Quy đồng về mẫu {common}: các tử tương ứng là {lhs} và {rhs}. {'Cộng' if op=='+' else 'Trừ'} các tử được {numerator}, giữ mẫu {common}; chia cả tử và mẫu cho ước chung lớn nhất {divisor} để viết kết quả tối giản.",f"({lhs}{op}{rhs})/{common}",u)]
        if op=="*":
            return [(f"Nhân tử {x.numerator} với tử {y.numerator}, mẫu {x.denominator} với mẫu {y.denominator}; sau đó rút gọn.",f"({x.numerator}*{y.numerator})/({x.denominator}*{y.denominator})",u)]
        return [(f"Đảo số chia {y.numerator}/{y.denominator} thành {y.denominator}/{y.numerator}; số chia khác 0.",f"{y.denominator}/{y.numerator}",u),
                ("Nhân phân số bị chia với phân số nghịch đảo vừa tìm, rồi rút gọn tử và mẫu.","a*r0",u)]
    if n=="percent_part":return [("Phần trăm là số phần trong một trăm phần bằng nhau; đổi tỉ lệ phần trăm thành phân số.","b/100",""),("Nhân tổng số lượng với tỉ lệ vừa đổi để tìm số lượng được chọn.","a*r0",u)]
    if n=="percent_whole":return [("Từ lượng của số phần trăm đã biết, chia cho số phần trăm để tìm lượng ứng với một phần trăm.","a/b",u),("Toàn bộ ứng với một trăm phần trăm, nhân lượng của một phần trăm với một trăm.","r0*100",u)]
    if n=="percent_ratio":return [("Chia giá trị phần được chọn cho toàn bộ để tìm tỉ số; đây chưa phải số phần trăm.","a/b",""),("Nhân tỉ số với một trăm để viết số phần trăm; đơn vị kết quả là phần trăm.","r0*100","%")]
    if n=="triangle_area":return [("Nhân đáy với chiều cao tương ứng để tìm diện tích hình chữ nhật có cùng đáy và chiều cao.","a*b","cm²"),("Diện tích tam giác bằng nửa diện tích hình chữ nhật tương ứng nên chia hai.","r0/2","cm²")]
    if n=="trapezoid_area":return [("Cộng độ dài hai đáy để tìm tổng hai đáy.","a+b","cm"),("Nhân tổng hai đáy với chiều cao tương ứng.","r0*c","cm²"),("Chia tích vừa tìm cho hai để được diện tích hình thang.","r1/2","cm²")]
    if n=="proportional_direct":return [("Lấy giá tiền đã biết chia số món để tìm đơn giá.","b/a","đồng/món"),("Đơn giá không đổi: nhân đơn giá với số món cần mua để tìm tổng tiền.","r0*c","đồng")]
    return previous.steps_recipe(t,values)

def make_values(t,rng):
    n=t.name;grade=t.grade
    if n.startswith("vertical_"):
        bound={1:99,2:999,3:99999,4:999999,5:999999}[grade]
        if grade==1:
            p=replace(LOOKUP["add_join" if n=="vertical_add" else "sub_remaining"],grade=1)
            return previous.make_values(p,rng)
        if n=="vertical_subtract" and rng.random()<.45:
            exponent=rng.randint(2,{2:2,3:4,4:5,5:5}[grade]);a=rng.randint(1,8)*10**exponent
            b=rng.randint(1,a-1)
        else:a,b=rng.randint(0,bound),rng.randint(0,bound)
        if n=="vertical_subtract" and a<b:a,b=b,a
        if n=="vertical_add" and a+b>bound:return make_values(t,rng)
        return {"a":Fraction(a),"b":Fraction(b)}
    if n=="hours_minutes_active":return {"a":Fraction(rng.randint(1,15)),"b":Fraction(rng.randint(1,59))}
    if n=="arithmetic_sequence":
        a,c=rng.randint(1,2000),rng.randint(1,200)
        return {"a":Fraction(a),"b":Fraction(a+c),"c":Fraction(c)}
    v=previous.make_values(t,rng)
    if n=="mass_kg_to_g":v={"a":Fraction(rng.randint(1,99))}
    if n=="square_area":v={"a":Fraction(rng.randint(1,9))}
    if n=="rectangle_area":v={"a":Fraction(rng.randint(1,999)),"b":Fraction(rng.randint(1,9))}
    if n=="rectangle_perimeter":v={"a":Fraction(rng.randint(2,2000)),"b":Fraction(rng.randint(1,1999))}
    if n in ("rectangle_area","rectangle_perimeter") and v["a"]<v["b"]:v["a"],v["b"]=v["b"],v["a"]
    if n=="square_perimeter":v={"a":Fraction(rng.randint(1,2000))}
    if n=="tens_place_value":v={"a":Fraction(rng.randint(10,99))}
    if n=="fraction_of_quantity":
        d=rng.randint(2,20);v={"a":Fraction(d*rng.randint(1,1000)),"b":Fraction(rng.randint(1,d-1),d)}
    if n=="multiples_missing":v={"a":Fraction(rng.randint(1,2000))};v["b"]=2*v["a"]
    if n in ("fraction_add","fraction_subtract","fraction_multiply","fraction_divide"):
        # Larger independent parameter space still satisfies current g4 denominator relation.
        d=rng.randint(2,24);e=d*rng.randint(1,4) if n in ("fraction_add","fraction_subtract") else rng.randint(2,24)
        x,y=Fraction(rng.randint(1,47),d),Fraction(rng.randint(1,47),e)
        if n in ("fraction_add","fraction_subtract") and max(x.denominator,y.denominator)%min(x.denominator,y.denominator):return make_values(t,rng)
        if n=="fraction_subtract" and x<y:x,y=y,x
        v={"a":x,"b":y}
    if n=="money_change":v={"a":Fraction(rng.randint(1,70)*10)};v["b"]=v["a"]+10*rng.randint(1,int((990-v["a"])/10))
    return v

def display(value,t,key):
    if t.name.startswith("fraction_") and (t.name!="fraction_of_quantity" or key=="b"):
        value=Fraction(value);return f"{value.numerator}/{value.denominator}"
    return number(value,t.style)

def render_question(t,variant,values):
    text=t.templates[variant];parts=[];facts=[];cursor=0;offset=0
    for match in re.finditer(r"\{([abc])\}",text):
        literal=text[cursor:match.start()];parts.append(literal);offset+=len(literal)
        key=match[1];quote=display(values[key],t,key)
        facts.append({"id":f"f{len(facts)}","role":FACT_ROLES.get(t.name,{}).get(key,key),"parameter":key,"value":str(values[key]),"quote":quote,"span":[offset,offset+len(quote)]})
        parts.append(quote);offset+=len(quote);cursor=match.end()
    parts.append(text[cursor:]);return "".join(parts),facts

def build_target(t,values,mode,observed=None):
    oracle=independent_answer(t.name,values)
    if mode=="hint":
        hint=t.hint
        if observed is not None:
            place=previous.result_mismatch_place(int(oracle),observed)
            hint=f"Ở hàng {place}, em đối chiếu chữ số kết quả đã ghi với phép tính tại cột này như thế nào?"
        return {"status":"solve","steps":[],"answer":None,"unit":None,"hint":hint}
    env=dict(values);steps=[]
    for index,(explanation,recipe,unit) in enumerate(steps_recipe(t,values)):
        expression=re.sub(r"\b(?:[abc]|r[0-9]+)\b",lambda m:expression_number(env[m[0]],t.style),recipe)
        result=evaluate_expression(expression);env[f"r{index}"]=result
        steps.append({"explanation":explanation,"expression":expression,"result":number(result,t.style),"unit":unit})
    final_index=len(steps)-2 if t.name.startswith("vertical_") else len(steps)-1
    if env[f"r{final_index}"]!=oracle:raise ValueError("INDEPENDENT_ORACLE_MISMATCH")
    if observed is not None:
        place=previous.result_mismatch_place(int(oracle),observed)
        steps[0]["explanation"]=f"Học sinh ghi {observed}; giữ nguyên để đối chiếu. Chữ số kết quả hàng {place} chưa khớp, nhưng chưa có dấu nhớ hoặc đổi hàng để kết luận lỗi thao tác nào. "+steps[0]["explanation"]
    return {"status":"solve","steps":steps,"answer":number(oracle,t.style),"unit":t.unit,"hint":None}

def canonical_expression(expression):
    """Bounded equivalence: associative/commutative +/*, ordered -/÷/%; no cancellation."""
    def walk(node):
        if isinstance(node,ast.Constant):return ("n",str(Fraction(ast.get_source_segment(expression,node))))
        if isinstance(node,ast.UnaryOp):return ("neg",walk(node.operand))
        if not isinstance(node,ast.BinOp):raise ValueError("INVALID_CASE_AST")
        op={ast.Add:"+",ast.Sub:"-",ast.Mult:"*",ast.Div:"/",ast.Mod:"%"}[type(node.op)]
        children=[walk(node.left),walk(node.right)]
        if op in ("+","*"):
            flattened=[]
            for child in children:flattened.extend(child[1:]) if child[0]==op else flattened.append(child)
            return tuple([op]+sorted(flattened,key=repr))
        return (op,*children)
    return repr(walk(ast.parse(expression,mode="eval").body))

def symbolic_answer_expression(t,values):
    recipes=previous.steps_recipe(t,values) if t.name in {x.name for x in previous.TOPICS} else steps_recipe(t,values)
    env={k:expression_number(v,t.style) for k,v in values.items()}
    for index,(_,recipe,_) in enumerate(recipes):
        env[f"r{index}"]=re.sub(r"\b(?:[abc]|r[0-9]+)\b",lambda m:"("+env[m[0]]+")",recipe)
    index=len(recipes)-2 if t.name.startswith("vertical_") else len(recipes)-1
    return env[f"r{index}"]

def case_signature(t,values):return digest(canonical_expression(symbolic_answer_expression(t,values)))

def v3_catalog(root=None):
    root=Path(root or Path(__file__).parent/"data"/"teacher_math_v3"/"generated")
    signatures=set();questions=set();fingerprints={};train_cases={}
    lookup={t.name:t for t in previous.TOPICS}
    for split in ("train","val","challenge"):
        path=root/(split+".jsonl");raw=path.read_bytes();fingerprints[split]=hashlib.sha256(raw).hexdigest()
        for line in raw.decode("utf-8").splitlines():
            row=json.loads(line);questions.add(row["problem"])
            if row["topic"] in lookup:
                signature=case_signature(lookup[row["topic"]],{k:Fraction(v) for k,v in row["parameters"].items()})
                if split=="train":train_cases.setdefault(signature,[]).append(row["sample_id"])
                else:signatures.add(signature)
    return signatures,questions,fingerprints,train_cases

def v3_exclusions(root=None):return v3_catalog(root)[:3]

def supplemental_pilot_exclusions(paths=None):
    """Preserve selection pilots as development evidence, never training prompts."""
    default=[Path(__file__).parent/"data"/"teacher_math_v3"/"independent_anchor.jsonl",
             Path(__file__).parent/"data"/"teacher_math_v4"/"base_choice_pilot30.jsonl"]
    cases=set();questions=set();fingerprints={}
    for path in paths or default:
        if not path.exists():continue
        raw=path.read_bytes();fingerprints[str(path.name)]=hashlib.sha256(raw).hexdigest()
        for line in raw.decode("utf-8").splitlines():
            r=json.loads(line);questions.add(r["problem"])
            if r.get("target",{}).get("status")!="solve":continue
            if r.get("topic") in LOOKUP and r.get("parameters"):
                cases.add(case_signature(LOOKUP[r["topic"]],{k:Fraction(v) for k,v in r["parameters"].items()}))
            if r.get("operation_formula") and r.get("parameters"):
                values={k:Fraction(v) for k,v in r["parameters"].items()}
                expression=re.sub(r"\b[a-z]\b",lambda m:expression_number(values[m[0]],"fraction"),r["operation_formula"])
                cases.add(digest(canonical_expression(expression)))
            # Conservative linkage of published numeric results to previous expressions.
            # This excludes both literal expressions and expressions with prior-result
            # substitutions; it is bounded and may overexclude, never adds a train row.
            linked={}
            for step in r["target"]["steps"]:
                expression=step["expression"]
                if not expression:continue
                try:cases.add(digest(canonical_expression(expression)))
                except (ValueError,SyntaxError,KeyError):continue
                expanded=re.sub(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])",lambda m:"("+linked[m[0]]+")" if m[0] in linked else m[0],expression)
                cases.add(digest(canonical_expression(expanded)))
                result=step["result"].replace(",",".")
                if re.fullmatch(r"\d+(?:\.\d+)?",result):linked[result]=expanded
    return cases,questions,fingerprints

def make_row(t,split,variant,values,mode,observed=None):
    if t.name in UNIT_VARIANTS:t=replace(t,unit=UNIT_VARIANTS[t.name][variant])
    problem,facts=render_question(t,variant,values)
    if observed is not None:problem+=f" Học sinh đã ghi đáp số {observed}; không có ảnh dấu nhớ hay các bước trung gian. Hãy kiểm tra kết quả quan sát được."
    group=case_signature(t,values)
    status="LEGACY_OR_ENRICHMENT_RESEARCH_EXTENSION" if t.name in previous.LEGACY_OR_ENRICHMENT else "CURRENT_SKILL_BOUNDED_ENGINEERING_EXAMPLE"
    if t.name=="probability_count":status="UNVERIFIED_ENRICHMENT_NOT_A_CURRENT_CURRICULUM_CLAIM"
    if t.name=="missing_addend":status="ENGINEERED_INFORMAL_MISSING_PART_NOT_FORMAL_EQUATION_REQUIREMENT"
    if t.name.startswith("vertical_") and t.grade==5:status="CAPSTONE_HARD_COLUMN_RESEARCH_EXTENSION_NOT_G5_NEW_CURRICULUM_OUTCOME"
    row={"sample_id":digest(VERSION+"|"+str(t.grade)+"|"+problem+"|"+mode)[:24],"split":split,"grade":t.grade,"problem":problem,"mode":mode,"topic":t.name,"template_variant":variant,
      "facts":facts,"parameters":{k:str(v) for k,v in values.items()},"numeric_case_group":group,"split_group_id":group,
      "wording_family":digest(re.sub(r"\d+(?:[.,/]\d+)?","#",problem)),"target":build_target(t,values,mode,observed),
      "oracle_answer":str(independent_answer(t.name,values)),"expected_answer":str(independent_answer(t.name,values)),"observed_work_verbatim":observed,
      "human_verified":False,"semantic_correctness_verified":False,"teacher_certified":False,"dataset_version":VERSION,
      "source":"AI_TEACHER_AUTHORED_NEW_ORIGINAL_V4","teacher":"Codex authored visible teaching examples; no transferred intelligence or model weights",
      "arithmetic_verification":"EXACT_AST_SEPARATE_TOPIC_FORMULA_COLUMN_TRACE_AND_INVERSE","semantic_verification":"BOUNDED_TEMPLATE_AND_FACT_ROLE_REVIEW_NOT_HUMAN_CERTIFIED",
      "curriculum_assignment":"BOUNDS_FROM_CACHED_2018_MAPPING_OR_EXPLICIT_EXTENSION","curriculum_status":status,
      "capstone_extension":t.name.startswith("vertical_"),"license":"project-authored synthetic examples; no textbook passages copied",
      "fact_roles":{k:FACT_ROLES.get(t.name,{}).get(k,"quantity_"+k) for k in values},
      "column_trace":column_trace(int(values["a"]),int(values["b"]),"+" if t.name=="vertical_add" else "-") if t.name.startswith("vertical_") else None}
    return row

GUARD_WORDINGS={
 "missing_quantity":("Hà được thêm {a} viên bi, nhưng chưa biết trước đó có mấy viên. Hỏi tổng số bi sau khi nhận.","Nhập thêm {a} quyển sách vào số sách ban đầu chưa ghi. Tính tổng sách.","Đã thêm {a} chiếc bút, số bút có sẵn không được cung cấp. Có tất cả mấy chiếc?"),
 "missing_divisor":("Chia đều {a} viên kẹo cho các bạn; đề chưa ghi số bạn. Một bạn nhận mấy viên?","{a} chiếc bút cần chia đều vào các hộp, chưa biết số hộp. Tìm số bút mỗi hộp.","Có {a} quyển vở chia đều cho các nhóm nhưng thiếu số nhóm. Mỗi nhóm nhận bao nhiêu?"),
 "ambiguous_referent":("Hà có {a} viên bi, Bình có số khác chưa ghi; một bạn cho đi số bi chưa ghi. Hỏi còn bao nhiêu.","Mai có {a} quyển vở, bạn khác có thêm một lượng chưa biết; chưa rõ ai phát bao nhiêu. Tìm số còn lại.","Một giỏ chứa {a} quả, giỏ khác chưa rõ; chuyển một số quả chưa ghi giữa các giỏ. Hỏi số quả trong giỏ được hỏi."),
 "unavailable_picture":("Đề nói xem hình tô màu nhưng hình chưa được gửi; chỉ có một nhãn {a} cm. Tính diện tích tô màu.","Hãy tìm tổng từ bảng ở ảnh chưa đính kèm; chỉ đọc được một giá trị {a}.","Cần tính theo sơ đồ chưa có; chỉ biết một cạnh mang số {a} cm. Tìm kết quả."),
 "zero_division":("Hãy tìm giá trị {a} chia cho 0.","Số bị chia là {a}, số chia 0. Tính thương.","Bài toán ghi phép chia {a} : 0; hãy xử lý phép tính này."),
 "non_math":("Hãy viết phần mềm có {a} nút bấm.","Tạo mã máy tính hiển thị {a} dòng.","Viết đoạn quảng cáo cho {a} món hàng."),
}
GUARD_HINTS={
 "missing_quantity":("Trước khi được thêm bi, Hà có bao nhiêu viên bi?","Ban đầu kho có bao nhiêu quyển sách?","Số bút có sẵn là bao nhiêu chiếc?"),
 "missing_divisor":("Có bao nhiêu bạn nhận kẹo chia đều?","Có bao nhiêu hộp nhận bút chia đều?","Có bao nhiêu nhóm được chia vở?"),
 "ambiguous_referent":("Em cần nêu số bi ban đầu của từng bạn, ai cho bao nhiêu và đang hỏi số bi của ai?","Em cần nêu số vở của từng bạn, ai phát bao nhiêu và hỏi số vở còn lại của ai?","Em cần nêu số quả ban đầu ở mỗi giỏ, lượng chuyển và giỏ đang cần tìm?"),
 "unavailable_picture":("Em có thể gửi hình tô màu và các kích thước đủ đọc rõ không?","Em có thể gửi đầy đủ bảng hoặc chép các hàng cần cộng không?","Em có thể cung cấp sơ đồ và các dữ kiện còn thiếu không?"),
 "zero_division":("Phép chia cho 0 không xác định; em kiểm tra lại số chia trong đề được không?",)*3,
 "non_math":("Em có thể gửi một bài toán tiểu học cần được hướng dẫn không?",)*3,
}
def guard_row(kind,split,variant,value,grade,mode):
    problem=GUARD_WORDINGS[kind][variant].format(a=value);group=digest(kind+"|"+str(value))
    return {"sample_id":digest(VERSION+"|"+str(grade)+"|"+problem+"|"+mode)[:24],"split":split,"grade":grade,"problem":problem,"mode":mode,"topic":kind,"template_variant":variant,"facts":[],"parameters":{"a":str(value)},"numeric_case_group":group,"split_group_id":group,"wording_family":digest(re.sub(r"\d+","#",problem)),
      "target":{"status":"unsupported" if kind in ("zero_division","non_math") else "clarify","steps":[],"answer":None,"unit":None,"hint":GUARD_HINTS[kind][variant]},"oracle_answer":None,"expected_answer":None,"observed_work_verbatim":None,"human_verified":False,"semantic_correctness_verified":False,"teacher_certified":False,"source":"AI_TEACHER_AUTHORED_NEW_ORIGINAL_V4_GUARDS","dataset_version":VERSION,"arithmetic_verification":"NO_GUARD_ANSWER","semantic_verification":"EXPLICIT_MISSING_FACT_REQUEST","curriculum_assignment":"ENGINEERED_GRADE_NOT_A_CURRICULUM_OUTCOME","column_trace":None}

def prompt(row):return json.dumps({k:row[k] for k in ("grade","problem","mode")},ensure_ascii=False,separators=(",",":"))

def grade_bounds(row):
    values={k:Fraction(v) for k,v in row["parameters"].items()};n=row["topic"];g=row["grade"]
    if row["target"]["status"]!="solve":return True
    if n.startswith("vertical_") and g<=4:
        trace=column_trace(int(values["a"]),int(values["b"]),"+" if n=="vertical_add" else "-")
        events=[]
        for state in trace:
            if state.get("outgoing_carry"):events.append(state["column"])
            if state.get("donor_column") is not None:events.extend(range(state["column"],state["donor_column"]))
        limit={1:0,2:1,3:2,4:3}[g]
        if len(events)>limit:raise ValueError("GRADE_CARRY_EVENT_LIMIT")
        if g in (3,4) and any(b-a==1 for a,b in zip(sorted(events),sorted(events)[1:])):raise ValueError("GRADE_CONSECUTIVE_REGROUPING")
    if g==1:
        if any(v.denominator!=1 or not 0<=v<=99 for v in values.values()):raise ValueError("G1_NUMBER_BOUNDS")
        if n in ("add_join","vertical_add"):
            a,b=map(int,(values["a"],values["b"]))
            if a+b>99 or a%10+b%10>=10:raise ValueError("G1_CARRY")
        if n in ("sub_remaining","compare_difference","vertical_subtract"):
            a,b=map(int,(values["a"],values["b"]))
            if a<b or a%10<b%10 or a//10<b//10:raise ValueError("G1_BORROW")
        if n=="missing_addend" and (values["b"]<values["a"] or int(values["b"])%10<int(values["a"])%10):raise ValueError("G1_MISSING_PART_BORROW")
    if g==2:
        if any(v.denominator!=1 or not 0<=v<=999 for v in values.values()):raise ValueError("G2_NUMBER_BOUNDS")
        if n in ("share_exact","missing_factor") and values["b"] not in (2,5):raise ValueError("G2_TABLE")
        if n=="equal_groups" and values["b"] not in (2,5):raise ValueError("G2_TABLE")
    if g==3:
        if any(abs(v)>100000 for v in values.values()) or abs(Fraction(row["oracle_answer"]))>100000:raise ValueError("G3_NUMBER_BOUNDS")
        if n=="rectangle_area" and min(values["a"],values["b"])>9:raise ValueError("G3_TWO_DIGIT_MULTIPLIERS")
        if n=="square_area" and values["a"]>9:raise ValueError("G3_SQUARE_MULTIPLIER")
    if n in ("fraction_add","fraction_subtract"):
        a,b=values["a"],values["b"]
        if max(a.denominator,b.denominator)%min(a.denominator,b.denominator):raise ValueError("G4_DENOMINATOR_CONTRACT")
    if g<=4 and not n.startswith("vertical_"):
        worked=row["target"] if row["mode"]=="worked_solution" else build_target(replace(LOOKUP[n],grade=g),values,"worked_solution")
        for step in worked["steps"]:
            for node in ast.walk(ast.parse(step["expression"],mode="eval")):
                if not isinstance(node,ast.BinOp) or not isinstance(node.op,(ast.Add,ast.Sub)):continue
                left=evaluate_expression(ast.unparse(node.left));right=evaluate_expression(ast.unparse(node.right))
                if left.denominator!=1 or right.denominator!=1 or left<0 or right<0 or (isinstance(node.op,ast.Sub) and left<right):continue
                trace=column_trace(int(left),int(right),"+" if isinstance(node.op,ast.Add) else "-")
                events=[]
                for state in trace:
                    if state.get("outgoing_carry"):events.append(state["column"])
                    if state.get("donor_column") is not None:events.extend(range(state["column"],state["donor_column"]))
                if len(events)>{1:0,2:1,3:2,4:3}[g]:raise ValueError("GRADE_WORD_STEP_CARRY_LIMIT")
                if g in (3,4) and any(b-a==1 for a,b in zip(sorted(events),sorted(events)[1:])):raise ValueError("GRADE_WORD_STEP_CONSECUTIVE_CARRY")
    return True

def validate_training_row(row):
    if row.get("human_verified") or row.get("semantic_correctness_verified") or row.get("teacher_certified"):raise ValueError("FALSE_CERTIFICATION")
    target=row["target"]
    if set(target)!={"status","steps","answer","unit","hint"}:raise ValueError("TARGET_SCHEMA")
    if target["status"] not in ("solve","clarify","unsupported"):raise ValueError("STATUS")
    if target["status"]=="solve":
        values={k:Fraction(v) for k,v in row["parameters"].items()}
        if independent_answer(row["topic"],values)!=Fraction(row["oracle_answer"]):raise ValueError("ROW_ORACLE")
    if len(target["steps"])>12:raise ValueError("STEP_LIMIT")
    if target["status"]!="solve" or row["mode"]=="hint":
        if target["steps"] or target["answer"] is not None or target["unit"] is not None:raise ValueError("HINT_ANSWER_LEAK")
        if not isinstance(target["hint"],str) or target["hint"].count("?")!=1:raise ValueError("ONE_HINT_QUESTION_REQUIRED")
        if "=" in target["hint"] or set(re.findall(r"\d+",target["hint"]))-set(re.findall(r"\d+",row["problem"])):raise ValueError("HINT_NUMERIC_DISCLOSURE")
        if target["status"]=="solve":
            t=replace(LOOKUP[row["topic"]],grade=row["grade"])
            if build_target(t,values,"hint",row.get("observed_work_verbatim"))!=target:raise ValueError("HINT_RECIPE_RECONSTRUCTION")
    else:
        values={k:Fraction(v) for k,v in row["parameters"].items()};oracle=independent_answer(row["topic"],values)
        if oracle!=Fraction(row["oracle_answer"]) or oracle!=Fraction(target["answer"].replace(",",".")):raise ValueError("ANSWER_ORACLE")
        if target["hint"] is not None or not target["steps"]:raise ValueError("WORKED_CONTRACT")
        for step in target["steps"]:
            if set(step)!={"explanation","expression","result","unit"}:raise ValueError("STEP_FIELDS")
            if evaluate_expression(step["expression"])!=Fraction(step["result"].replace(",",".")):raise ValueError("STEP_ARITHMETIC")
        t=replace(LOOKUP[row["topic"]],grade=row["grade"],unit=target["unit"])
        expected=build_target(t,values,"worked_solution",row.get("observed_work_verbatim"))
        if expected!=target:raise ValueError("TARGET_RECIPE_RECONSTRUCTION")
        if row["topic"].startswith("vertical_"):
            a,b=map(int,(values["a"],values["b"]));symbol="+" if row["topic"]=="vertical_add" else "-"
            if column_trace(a,b,symbol)!=row["column_trace"]:raise ValueError("COLUMN_STATE_TRACE")
            answer=int(Fraction(target["answer"]))
            if (answer-b if symbol=="+" else answer+b)!=a:raise ValueError("COLUMN_INVERSE")
    for fact in row["facts"]:
        start,end=fact["span"]
        if row["problem"][start:end]!=fact["quote"] or Fraction(fact["quote"].replace(",","."))!=Fraction(fact["value"]):raise ValueError("FACT_SPAN")
        if fact.get("role")!=FACT_ROLES.get(row["topic"],{}).get(fact["parameter"],fact["parameter"]):raise ValueError("FACT_ROLE")
    grade_bounds(row)
    return True

def validate(rows,excluded_cases=(),excluded_questions=()):
    ids=set();groups={};phrases={s:set() for s in SPLITS};old=set(excluded_cases);questions=set(excluded_questions)
    _,_,v3_hashes,old_train=v3_catalog()
    for row in rows:
        validate_training_row(row)
        if row["sample_id"] in ids:raise ValueError("DUPLICATE_SAMPLE_ID")
        ids.add(row["sample_id"])
        if row["numeric_case_group"] in old or row["problem"] in questions:raise ValueError("V3_EXCLUSION_COLLISION")
        if groups.setdefault(row["split_group_id"],row["split"])!=row["split"]:raise ValueError("V4_GROUP_SPLIT_LEAK")
        if row.get("case_origin")=="CORRECTED_REPLAY_OF_V3_TRAIN_CASE":
            evidence=row.get("replay_provenance") or {}
            if row["split"]!="train" or row["numeric_case_group"] not in old_train or evidence.get("source_sample_ids")!=old_train[row["numeric_case_group"]] or evidence.get("sha256")!=v3_hashes["train"]:raise ValueError("REPLAY_PROVENANCE")
        if row["split"]=="val" and row["target"]["status"]=="solve" and row["numeric_case_group"] in old_train:raise ValueError("FRESH_VAL_OLD_TRAIN_LEAK")
        phrases[row["split"]].add(row["wording_family"])
    if phrases["train"]&phrases["val"]:raise ValueError("V4_WORDING_SPLIT_LEAK")
    return True

def build(seed=SEED,cases_per_grade=650,val_cases_per_grade=40,guard_cases_per_grade_kind=10):
    rng=random.Random(seed);excluded,old_questions,fingerprints,train_cases=v3_catalog()
    pilot_cases,pilot_questions,pilot_fingerprints=supplemental_pilot_exclusions()
    excluded|=pilot_cases;old_questions|=pilot_questions
    seen=set(excluded);seen_questions=set(old_questions);rows=[];rejected=Counter()
    topic_grade={g:[t for t in TOPICS if t.grade==g and not t.name.startswith("vertical_")] for g in range(1,6)}
    core_shares={1:.40,2:.75,3:.40,4:.25,5:.15}
    for split in SPLITS:
        # Fresh validation excludes every old V3 training case, even if not replayed.
        if split=="val":seen.update(train_cases)
        count=cases_per_grade if split=="train" else val_cases_per_grade
        for grade in range(1,6):
            accepted=0;attempts=0;topic_hits=Counter()
            while accepted<count:
                attempts+=1
                if attempts>250000:raise ValueError(f"CASE_SPACE_EXHAUSTED_G{grade}_{split}")
                use_core=accepted<int(count*core_shares[grade])
                if use_core:t=replace(LOOKUP["vertical_add" if accepted%2==0 else "vertical_subtract"],grade=grade)
                else:
                    # Cycle all noncore grade topics; if a small table domain is exhausted, choose another topic.
                    candidates=topic_grade[grade];t=candidates[(accepted+attempts//100)%len(candidates)]
                values=make_values(t,rng);variant=accepted%2 if split=="train" else 2
                observed=None
                if use_core and accepted%5==0:
                    answer=int(independent_answer(t.name,values));place=rng.randint(0,max(0,len(str(answer))-1))
                    observed=str(answer+10**place)
                row=make_row(t,split,variant,values,"worked_solution",observed)
                try:grade_bounds(row)
                except ValueError as error:rejected[str(error)]+=1;continue
                if row["numeric_case_group"] in seen or row["problem"] in seen_questions:
                    rejected["case_or_wording_collision"]+=1;continue
                seen.add(row["numeric_case_group"]);seen_questions.add(row["problem"])
                hint=make_row(t,split,variant,values,"hint",observed)
                for accepted_row in (row,hint):
                    accepted_row["case_origin"]="CORRECTED_REPLAY_OF_V3_TRAIN_CASE" if row["numeric_case_group"] in train_cases else "NEW_MATHEMATICAL_CASE"
                    accepted_row["replay_provenance"]={"dataset":"teacher_math_v3","split":"train","sha256":fingerprints["train"],"source_sample_ids":train_cases[row["numeric_case_group"]],"policy":"Original V3 bytes preserved; newly authored V4 wording, grade and target corrections."} if row["numeric_case_group"] in train_cases else None
                rows += [row,hint]
                topic_hits[t.name]+=1;accepted+=1
            for kind in GUARD_WORDINGS:
                guard_count=guard_cases_per_grade_kind if split=="train" else 1
                for index in range(guard_count):
                    variant=index%2 if split=="train" else 2
                    while True:
                        row=guard_row(kind,split,variant,rng.randint(1,99999),grade,"worked_solution")
                        if row["numeric_case_group"] not in seen and row["problem"] not in seen_questions:break
                    seen.add(row["numeric_case_group"]);seen_questions.add(row["problem"])
                    hint=guard_row(kind,split,variant,int(row["parameters"]["a"]),grade,"hint")
                    for accepted_row in (row,hint):accepted_row["case_origin"]="NEW_GUARD_TEMPLATE";accepted_row["replay_provenance"]=None
                    rows += [row,hint]
    validate(rows,excluded,old_questions)
    return rows,{"v3_and_pilot_excluded_case_count":len(excluded),"v3_fingerprints":fingerprints,"pilot_fingerprints":pilot_fingerprints,"rejected_candidates":dict(rejected),"bounded_equivalence":"Associative/commutative +/*; ordered -/division/remainder. Conservative published pilot result-expression linkage. No algebraic cancellation or universal semantic equivalence claim.","training_replay_policy":"V3 train mathematical cases allowed with CORRECTED_REPLAY provenance; V3 val/challenge and selection pilots always excluded. Freshval additionally excludes all V3train cases."}

def export(output=None,**kwargs):
    output=Path(output or Path(__file__).parent/"data"/"teacher_math_v4"/"generated");output.mkdir(parents=True,exist_ok=True)
    rows,audit=build(**kwargs);hashes={}
    for split in SPLITS:
        content="".join(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n" for r in rows if r["split"]==split)
        (output/(split+".jsonl")).write_text(content,encoding="utf-8",newline="\n");hashes[split]=digest(content)
    report={"version":VERSION,"seed":kwargs.get("seed",SEED),"status":"GENERATED_EXACT_CONTRACT_AI_RESEARCH_DATA_NOT_TRAINED","splits":dict(Counter(r["split"] for r in rows)),"fingerprints":hashes,
      "grades":{s:dict(Counter(r["grade"] for r in rows if r["split"]==s)) for s in SPLITS},"modes":{s:dict(Counter(r["mode"] for r in rows if r["split"]==s)) for s in SPLITS},
      "statuses":{s:dict(Counter(r["target"]["status"] for r in rows if r["split"]==s)) for s in SPLITS},"topics":{s:dict(Counter(r["topic"] for r in rows if r["split"]==s)) for s in SPLITS},
      "wrong_observed_work":dict(Counter(r["split"] for r in rows if r["observed_work_verbatim"] is not None)),"column_cases":dict(Counter(r["split"] for r in rows if r["topic"].startswith("vertical_"))),
      "case_origins":{s:dict(Counter(r["case_origin"] for r in rows if r["split"]==s)) for s in SPLITS},
      "topic_coverage_gaps":{s:[t.name for t in TOPICS if not any(r["topic"]==t.name and r["split"]==s for r in rows)] for s in SPLITS},
      "curriculum_scope_counts":{s:dict(Counter(r.get("curriculum_status","GUARD") for r in rows if r["split"]==s)) for s in SPLITS},
      "current_regrouping_bounds":{"g1":"no carry/borrow, values and answer within99 (conservative subset of0–100)","g2":"<=1regrouping, values<=999 (subset0–1000)","g3":"<=2nonconsecutive regrouping, five digit column operands and results; kg->g<=99000; area uses at most one multi-digit multiplier","g4":"<=3nonconsecutive regrouping","g5_hard_columns":"Explicit capstone research extension reviewing prior natural-number skills; hard cascading borrow not asserted as a new g5 current outcome"},
      "input_contract":"Only grade/problem/mode. target/facts/column_trace/oracle never input.","exclusion_audit":audit,
      "human_verified":False,"teacher_certified":False,"production_approved":False,"challenge_concept_read":False,
      "limits":["Fresh finite AI authored templates; not all curriculum or real-world teacher gold.","Legacy extensions explicitly labelled; full 2006 official annex not recovered.","Arithmetic and target contracts do not certify general semantic pedagogy.","No OCR or image training; observed pupil work contains final answer only.","V3 retention is exposed development validation; freshval uses unseen wordings and numeric cases under bounded exclusions.","Original conceptchallenge50 untouched; no fresh numeric private challenge authored in this module."],
      "checks":{"all_rows_exact_ast_and_oracle":True,"column_state_and_inverse":True,"grade_bounds":True,"no_numeric_disclosure_in_hints":True,"split_groups_disjoint":True,"v3_development_holdouts_and_known_pilots_excluded":True}}
    source_root=Path(__file__).parent/"data"/"teacher_math_v3"
    report["curriculum_evidence_fingerprints"]={name:hashlib.sha256((source_root/name).read_bytes()).hexdigest() for name in ("curriculum_sources.json","legacy_curriculum_sources.json")}
    (output/"dataset_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8",newline="\n")
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--output",default=None);args=parser.parse_args()
    print(json.dumps(export(args.output),ensure_ascii=False,indent=2))

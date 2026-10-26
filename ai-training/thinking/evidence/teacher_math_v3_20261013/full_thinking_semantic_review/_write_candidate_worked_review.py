"""Serialize explicit AI decisions after reading every visible worked packet.

This is a review artifact writer, not an automatic semantic classifier.
The index sets and all reasons below are manually authored from the actual
173 Vietnamese problems and visible outputs, including missing outputs.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json

ROOT = Path(__file__).resolve().parent
PACKETS = ROOT / "candidate_worked_solution_review_packets.jsonl"
rows = [json.loads(line) for line in PACKETS.read_text(encoding="utf-8").splitlines()]
assert len(rows) == 173

REASONS = """
0|Đúng gộp 3 viên buổi sáng với 10 viên buổi chiều: 3+10=13; lời giải và đơn vị viên khớp câu hỏi.
1|25+20=45 viên; đổi thứ tự hai số hạng vẫn đúng vì đang tìm tổng cả ngày, không đổi vai trò dữ kiện.
2|10+29=39 viên; lời giải gộp hai buổi và đáp số đúng, không thêm dữ kiện.
3|58−16=42 quả còn lại; lấy số đang có trừ số đã ăn, đúng quan hệ và đơn vị.
4|64−30=34 quả; gọi tổng ban đầu là 64 và bớt 30, phù hợp phần còn lại.
5|47−40=7 quả; giải thích lấy số ban đầu trừ số đã lấy đi đúng.
6|29−9=20 quyển cần bổ sung; nhận đúng số cần đạt và số đã có.
7|23−1=22 quyển bổ sung; phép trừ đúng để tìm số hạng còn thiếu.
8|33−11=22 quyển; dữ kiện ban đầu và đích đủ vở được dùng đúng.
9|19−1=18 chiếc; lấy số bút của An trừ của Bình để tìm phần hơn.
10|68−31=37 chiếc; giải thích số lớn trừ số bé đúng quan hệ so sánh.
11|49−22=27 chiếc; phép trừ và lời giải đều đúng, không đảo người nhiều hơn.
12|Đáp số 10 và 1*10 đúng, nhưng lời giải nói số 11 có «một nhóm gồm hai đơn vị chục», sai cấu tạo hàng chục; còn dùng nhân chưa phải cách giải lớp 1. Đáp số đúng không sửa được lỗi khái niệm này.
13|51−1=50 biểu thị năm chục, đúng giá trị hàng chục. «đơn vị» là mô tả giá trị số hợp nghĩa, không phải lỗi thứ nguyên dù khác unit rỗng của reference.
14|63−3=60, bỏ ba đơn vị để giữ sáu chục; đúng cách giải hàng chục bằng phép trừ.
15|10 phần, mỗi phần 2 quyển: 10*2=20 quyển; lời giải nhóm bằng nhau đúng.
16|1 phần có 5 quyển nên 1*5=5 quyển; nhận đúng số nhóm và lượng mỗi nhóm.
17|8 phần, mỗi phần 5 quyển: 8*5=40 quyển; phương pháp nhân nhóm bằng nhau hợp lớp 2.
18|40 quyển chia đều 5 bạn: 40/5=8 quyển mỗi bạn; giải thích chia tổng cho số nhóm đúng.
19|6/2=3 quyển mỗi bạn; không nhầm số bạn với số vở trong một nhóm.
20|18/2=9 quyển; cách chia đều, dữ kiện và đơn vị đều đúng.
21|Tích 12 chia thừa số đã biết 2 được 6; đúng quy tắc tìm thừa số chưa biết.
22|50/5=10; giải thích tích chia thừa số đã biết chính xác.
23|16/2=8; tìm thừa số còn lại đúng, không dùng phép trừ tích.
24|79+68=147 rồi 147−6=141 quyển. «Bớt số đã ghi» và «tổng ban đầu» diễn đạt chưa chuẩn bằng số đã lấy đi/tổng sau khi thêm, nhưng vẫn ánh xạ đúng hai thao tác.
25|50+22=72 rồi 72−43=29 quyển; cộng lượng thêm rồi trừ lượng lấy đi đúng thứ tự. Từ «tổng ban đầu» hơi lỏng nghĩa nhưng biểu thức và mô tả hai lượng làm rõ.
26|8+28=36 rồi 36−35=1 quyển; quy trình thêm trước, bớt sau đúng. «Tổng ban đầu» nên đổi thành tổng sau khi thêm để rõ hơn.
27|8*4=32 viên ban đầu, 32−29=3 viên còn lại; đúng tổng các hộp rồi bớt lượng lấy ra.
28|6*8=48 rồi 48−24=24 viên; nhận đúng mỗi hộp và số hộp, giải hai bước rõ.
29|4*6=24 rồi 24−17=7 viên; không nhầm số lấy ra với số còn lại.
30|710−350=360 đồng còn lại; lời giải tiền ban đầu trừ tiền đã dùng phù hợp đề.
31|250−240=10 đồng còn lại; «tiền đã đưa» không đúng cách gọi tiền mang theo trong đề, nhưng vai trò 250 ban đầu/240 đã dùng vẫn rõ, chỉ là diễn đạt cần sửa.
32|450−370=80 đồng; «tiền đã đưa/tiền thừa» chuyển ngữ cảnh nhẹ từ còn lại sang trả tiền, song không thêm số hoặc đổi phép toán; nên dùng tiền mang theo/còn lại.
33|48−37=11 phút trong cùng một giờ; hai mốc được dùng đúng nên không cần đổi giờ.
34|58−4=54 phút; lấy phút kết thúc trừ phút bắt đầu đúng.
35|36−13=23 phút; lời giải mô tả khoảng giữa hai mốc chính xác.
36|Số dư 2 đúng, nhưng dòng được trình bày 401/7 với result=2 là phép chia sai: thương đầy đủ là 57 dư 2, không phải 2. Cần 401−57*7=2, không được coi đáp số đúng là lời giải đúng.
37|Đáp số 0 đúng vì 203=29*7, nhưng steps chỉ tính 203/7=29 hộp rồi gắn unit cuối «box» cho số bánh dư. Không trình bày 0 bánh dư; sai vai trò thương/số dư và thứ nguyên của kết luận.
38|90%4=2 đúng theo nghĩa toán lập trình lấy dư, lời giải cũng nói số còn sau các nhóm đủ. Ký hiệu % này chưa giải thích cho học sinh lớp 3 và dễ hiểu thành phần trăm; cần phép chia có dư hoặc 90−22*4.
39|2*7=14 rồi 94+14=108; nhân trước cộng và lời giải phù hợp biểu thức không ngoặc.
40|8*4=32 rồi 68+32=100; phép nhân là số hạng thứ hai, cộng lại đúng. Đây là primary sample collision đã biết nhưng review không đổi điểm/split.
41|5*9=45, 24+45=69 đúng. Tuy nhiên nói «biểu thức có ngoặc hoặc phép tính nhân trước cộng» trong đề không có ngoặc, lý do mơ hồ và đưa cấu trúc ngoặc không có; cần quy tắc nhân trước cộng rõ ràng.
42|173 m đổi thành 173*100=17300 cm; nêu 1 m=100 cm đúng.
43|58*100=5800 cm; hệ số đổi độ dài và đơn vị chính xác.
44|39*100=3900 cm; lời giải đổi mét sang xăng-ti-mét đúng.
45|4*60=240 phút hoạt động; 240+56=296 phút cả hai khoảng. Dữ kiện nghỉ và hoạt động được cộng, không trừ.
46|12*60=720 đúng, nhưng trừ 30 phút nghỉ để ra 690 sai đề hỏi tổng cả hai khoảng. Phải 720+30=750; sai hiểu quan hệ, không phải lỗi tính 720−30.
47|42+60=102 phút là cách gộp hợp lệ vì 1 giờ=60 phút. Bước đổi giờ không viết riêng nhưng giá trị 60 là hằng số đổi đơn vị hợp lệ, không phải dữ kiện bịa.
48|263*1000=263000 g, hệ số kg→g đúng. Kết quả 263000 vượt phạm vi số đến 100000 lớp 3 trong mapping hiện hành; đây là vấn đề độ khó dữ liệu được gán lớp, không phải sai đáp số của model.
49|88*1000=88000 g; nêu nhân 1000 đúng, có dùng từ kilogram/gram nhưng ký hiệu và nghĩa rõ.
50|186*1000=186000 g đúng và giải thích đúng. Mức số kết quả vượt 100000 lớp 3; cần gán lớp/độ khó phù hợp hơn dù phép đổi không sai.
51|80+84=164 rồi nhân 2 được 328 cm. «Đính kèm hai cặp cạnh» dùng từ vụng, nhưng giải thích hai cặp cạnh bằng nhau và phép tính chu vi đúng.
52|(19+61)*2=160 cm; hai bước cộng chiều dài/rộng và nhân đôi đúng. Đề tự đặt chiều rộng lớn hơn chiều dài, không phải model tự đổi dữ kiện.
53|86+48=134 rồi 134*2=268 cm; đổi thứ tự cộng hợp lệ và giải thích chu vi đúng.
54|Dùng hình vuông như hình chữ nhật với hai kích thước 156: 156+156=312 rồi nhân 2=624 cm, là phương pháp khác hợp lệ. Nên nói rõ hình vuông là trường hợp có hai kích thước bằng nhau; không phạt vì khác reference 156*4.
55|4*71=284 cm; bốn cạnh bằng nhau được nêu đúng, đổi thứ tự nhân hợp lệ.
56|63*4=252 cm; chu vi hình vuông là bốn lần cạnh, đúng đơn vị độ dài.
57|60*46=2760 cm², diện tích hình chữ nhật và vai trò hai kích thước đúng. Nhân hai số hai chữ số chưa thuộc mức phép nhân một chữ số lớp 3 hiện hành; cần xem lại độ khó đề.
58|19*61=1159 cm² đúng; nhân rộng với dài tương đương dài với rộng. Hai thừa số nhiều chữ số là vấn đề gán lớp 3 của dữ liệu.
59|52*58=3016 cm² đúng; lời giải diện tích đúng. Phép nhân hai chữ số với hai chữ số nên xếp mức cao hơn lớp 3 hiện hành.
60|209*209=43681 cm² đúng, nhưng giải thích tìm số ô «bằng hàng chục và hàng trăm» không phải quy tắc đếm số hàng nhân số ô mỗi hàng; lý giải sai/không có nghĩa toán rõ. Nhân ba chữ số cũng vượt mức lớp 3.
61|85*85=7225 cm²; số hàng nhân số ô trong một hàng là cách đếm đúng. Phép nhân hai số hai chữ số là độ khó vượt cách nhân một chữ số lớp 3.
62|183*183=33489 cm² đúng, nhưng lời giải nhân số hàng với «số các hàng» thay vì số ô mỗi hàng, nhầm vai trò dữ kiện dù hai số tình cờ bằng nhau. Mức nhân ba chữ số cũng không hợp lớp 3.
63|12+73+25=110 đồ vật; cộng ba thống kê đúng. Từ «bảng» là cách mô tả các giá trị được thống kê trong chữ, không tuyên bố đọc hình/bảng ảnh không có.
64|72+7+6=85 đồ vật; giải thích cộng ba nhóm đã ghi số đúng.
65|42+22+18=82 đồ vật; cộng ba giá trị đúng. Từ «bảng» diễn đạt lỏng nhưng không thêm dữ kiện thị giác.
66|1025+385=1410 là hai lần số lớn, chia 2=705; lời giải tổng-hiệu đúng.
67|(2058+598)/2=1328; mô tả hai lần số lớn rồi chia hai chính xác.
68|(597+171)/2=384; đúng công thức số lớn với tổng và hiệu.
69|Số lớn tính đúng 288 và final 169 đúng, nhưng bước cuối 288−169=119 dùng chính số bé chưa tìm và gọi thao tác đó «để tìm số bé». Đây là phép tìm hiệu/circular reasoning, không suy ra 169 từ dữ kiện.
70|Tính số lớn (1277+305)/2=791 rồi 791−305=486 là cách khác hoàn toàn hợp lệ để tìm số bé. Không phạt vì khác reference (1277−305)/2.
71|Các biểu thức cho 1392 rồi 1392−627=765 đúng, nhưng lời giải gọi 627 là số bé và 765 là hiệu; thực tế 627 là hiệu, 765 là số bé cần tìm. Sai vai trò/lý giải dù final đúng.
72|(4+17)/3=21/3=7; cộng tử cùng mẫu và rút gọn đúng.
73|Đề 1+5 xác định được 6, nhưng trả clarify không đáp số; gợi ý «gộp tử số và mẫu số» còn có thể dạy cộng cả mẫu sai. Không phải thiếu dữ kiện thực.
74|6/7 quy đồng thành 12/14, (17+12)/14=29/14; mẫu chung và phép cộng đúng. Bước nhân quy đồng không viết riêng nhưng lời giải chỉ rõ mẫu 14.
75|3/2=12/8 nên (17−12)/8=5/8; trừ đúng số bị bớt và dùng mẫu chung đúng.
76|1=9/9 nên (19−9)/9=10/9; lời giải đổi số về cùng mẫu đúng.
77|13/9=39/27 nên (39−4)/27=35/27; số và quy tắc trừ phân số đúng.
78|(17/7)*2/1=34/7; hiểu số nguyên 2 như 2/1, nhân tử/mẫu đúng.
79|(11/20)*(6/5)=66/100=33/50; nhân hai phân số rồi rút gọn đúng.
80|(13/15)*(1/3)=13/45; tử và mẫu được nhân đúng, phân số tối giản.
81|(9/2)/(5/3)=27/10; giải thích nhân nghịch đảo đúng. Nên hiện thêm 9/2*3/5 để bước nghịch đảo dễ theo dõi, nhưng không có quy tắc sai.
82|(3/5)/(3/7)=7/5; nói nhân nghịch đảo đúng. Bước chuyển sang 3/5*7/3 chưa viết riêng, là thiếu chi tiết nhẹ, không sai toán.
83|Đáp số và biểu thức chia (19/7)/(17/2)=38/119 đúng, nhưng lời giải «nhân tử với tử, mẫu với mẫu» là quy tắc nhân, không phải chia khi chưa đảo số chia. Có thể khiến học sinh làm 323/14; sai hướng dẫn cốt lõi.
84|65+30+4=99; 99/3=33 là trung bình của ba ngày, giải thích đúng.
85|(26+54+82)/3=162/3=54; số lượng ba giá trị được dùng đúng.
86|(52+16+25)/3=93/3=31; đúng tổng chia số dữ liệu, không chia cho một giá trị dữ liệu.
87|460*(3/5)=276 chiếc; lấy phân số của tổng đúng.
88|850*(5/17)=250 chiếc; lượng được phát là phần 5/17 của 850, vai trò đúng.
89|87*(2/3)=58 chiếc; nhân tổng với phần cần lấy đúng.
90|53*25=1325 cm²; lời giải dùng «chiều cơ bản» thay vì đáy, nhưng cặp số đáy/chiều cao đúng và còn nêu không dùng cạnh xiên. Nên sửa thuật ngữ cho rõ.
91|90*54=4860 cm²; đáy nhân chiều cao tương ứng đúng công thức bình hành.
92|24*5=120 cm²; dùng chiều dài đáy và chiều cao đúng, không nhầm với chu vi.
93|1+8=9 phần, 324/9=36, An có một phần nên 36 vật. Bước tìm một phần bị lặp nhưng không sai; «vật» đồng nghĩa «đồ vật», không phải lỗi đơn vị toán.
94|5+12=17 phần, 1292/17=76, 76*5=380 đồ vật cho An; đủ ba bước, nhận đúng số phần của An.
95|11+9=20 phần, 500/20=25, 25*11=275 đồ vật; không nhầm An/Bình và giải tỉ lệ đúng.
96|Bội liên tiếp của 1 tăng 1: 2+1=3, đúng quy luật.
97|298+149=447 là bội tiếp theo của 149; tăng đúng một lần số đã cho.
98|Sau 76,152 trong các bội liên tiếp phải là 228, nhưng model nhân 152*2=304. Phép tính đúng số học nhưng dùng quy luật nhân đôi sai dãy bội liên tiếp.
99|29.86+57.25=87,11; giải thích thẳng hàng và dấu phẩy đúng.
100|Final 111,77 đúng, nhưng gọi 5+2 là hàng phần trăm trong khi đây là phần mười, có bước expression 11 result 1 không phải đẳng thức và lời ghép/nhớ không rõ. Chuỗi hướng dẫn đặt tính chứa lỗi hàng và biến đổi dù có đáp số đúng.
101|14.2+47.36=61,56; đặt dấu phẩy thẳng hàng đúng, không cần ép theo thứ tự reference.
102|25.93−10.46=15,47; trừ thập phân và giải thích thẳng hàng đúng.
103|Biểu thức 66.81−40.76=26,05 đúng số còn lại, nhưng nói «tìm phần đã bị giảm», trong đề phần giảm đã biết là 40,76. Lời giải nhầm câu hỏi/đại lượng kết quả.
104|70.17−20.46=49,71 đúng; «hàng phân số» là thuật ngữ không chuẩn, nhưng chỉ dẫn viết chữ số thập phân thẳng hàng rồi trừ vẫn đúng. Nên đổi thành hàng phần mười/phần trăm.
105|7.3*76.09=555,457; tổng ba chữ số thập phân được dùng đúng trong kết quả, lời giải quy tắc đặt dấu phẩy đúng.
106|8.6*27.03=232.458 đúng; nhắc tổng số chữ số thập phân bằng tiếng Anh «decimal places» gây khó cho học sinh Việt Nam nhưng không đổi quy tắc. Dấu chấm là quy ước máy cần render dấu phẩy.
107|0.79*71.16=56.2164 đúng bốn chữ số thập phân; dấu chấm số là định dạng, không phải tính sai.
108|50.32/1.7*10/10=29.6 là biểu thức tương đương đúng; hệ số 10/10 có thể biểu diễn nhân cả tử và mẫu. Tuy vậy chưa hiện (50.32*10)/(1.7*10)=503.2/17, nên hướng dẫn bỏ số chia thập phân còn thiếu rõ ràng.
109|117.6/2.8*10/10=42 đúng vì nhân tỉ số với 1. Lời giải bỏ dấu phẩy chưa thể hiện hai số sau khi nhân; cần (117.6*10)/(2.8*10)=1176/28 để học sinh thấy thao tác, không coi biểu thức tương đương là phép tính sai.
110|116.06/1.4*10/10=82,9 đúng; nói nhân cả hai cùng hệ số hợp lệ nhưng chỉ hiển thị hệ số triệt tiêu, thiếu bước số chia thành 14. Hướng dẫn nên hiện 1160.6/14.
111|7600*23/100=1748; chuyển 23% thành 23/100 rồi lấy phần của tổng đúng.
112|1300*61/100=793; nhận đúng tổng và phần trăm cần lấy.
113|7600*54/100=4104; lời giải phần của một trăm chính xác.
114|6468/66=98 là giá trị 1%, nhân 100=9800; đúng tìm toàn bộ từ phần trăm.
115|731/43*100=1700; quy trình tìm một phần trăm rồi toàn bộ đúng.
116|6365/67*100=9500; không nhầm lấy phần trăm của phần đã cho.
117|66/3300*100=2%; lấy số đạt chia tổng đúng, có đơn vị phần trăm.
118|3127/5300*100=59% đúng. Từ «phần hợp chất» không thuộc bài thống kê sản phẩm, gây khó hiểu và không hợp ngôn ngữ lớp 5; không thêm số hoặc đổi vai trò tử/mẫu.
119|1782/3300*100=54%; «số lượng phần hợp» vụng lời nhưng các đại lượng phần đạt/tổng đúng.
120|42*59/2=1239 cm²; «chiều cơ sở» nên gọi đáy, nhưng đúng đáy đã cho nhân chiều cao rồi chia hai.
121|52*67/2=1742 cm²; đáy và chiều cao tương ứng dùng đúng.
122|29*58/2=841 cm²; đúng công thức diện tích tam giác.
123|Ba biểu thức 15+42=57, 57/2=28.5, 28.5*86=2451 đều đúng theo phương pháp chia trước. Nhưng lời giải bước cuối vẫn yêu cầu «nhân tổng hai đáy với chiều cao rồi chia hai» trong khi operand 28.5 đã là nửa tổng; mô tả thao tác bước này sai và có nguy cơ chia hai lần.
124|36+47=83, 83/2=41.5, 41.5*10=415 cm²; lời giải cuối nêu tổng đã chia hai, đúng phương pháp khác. Không phạt vì reference nhân rồi mới chia.
125|3+90=93, 93/2=46.5, 46.5*14=651 đúng chia trước. Tuy nhiên lời giải cuối gọi 46.5 là tổng hai đáy và còn nói chia hai, không khớp operand nửa tổng; lỗi giải thích cùng loại mẫu 123.
126|106*106=11236 cm² rồi 11236*3.14=35281.04 cm²; tách bình phương và pi thành hai bước hợp lệ. Không phạt vì khác một biểu thức reference; giá trị gần đúng theo pi đã cho.
127|201*201*3.14=126859.14 cm²; nêu rõ gần đúng theo pi ấy, đúng công thức và số học.
128|139*139*3.14=60667,94 cm²; dùng bán kính bình phương và pi đã cho đúng.
129|32*2*3.14=200,96 cm; bán kính đổi đường kính rồi nhân pi, chu vi đúng.
130|98*2*3.14=615,44 cm; không nhầm chu vi với diện tích.
131|2*246*3.14=1544.88 cm; đổi thứ tự nhân hợp lệ, dấu chấm là quy ước số máy cần render dấu phẩy.
132|20*76=1520 cm² diện tích đáy, 1520*29=44080 cm³; hai bước thể tích hợp đơn vị.
133|55*22*1=1210 cm³ là cách gộp ba kích thước trực tiếp đúng, chiều cao một nên không cần hai bước riêng. Không phạt vì khác reference hai bước.
134|38*11=418 cm² rồi 418*2=836 cm³; diện tích đáy nhân chiều cao đúng.
135|7*7=49 cm² mỗi mặt, nhân 6=294 cm² vì phủ cả sáu mặt; đúng diện tích toàn phần.
136|64*64=4096, 4096*6=24576 cm²; đơn vị mặt vuông và sáu mặt đúng.
137|258*258=66564, 66564*6=399384 cm²; dữ kiện hộp kín được dùng đúng.
138|50*30=1500 km; chuyển động đều nên vận tốc nhân thời gian đúng.
139|60*9=540 km; không dùng gia tốc hay thay đổi vận tốc ngoài đề.
140|9*14.5=130,5 km; thời gian thập phân và đơn vị quãng đường đúng.
141|19/1=19 km/h; km/h và km/giờ là đơn vị tương đương đúng, không phải lỗi thứ nguyên.
142|144/48=3 km/h; chia quãng đường cho thời gian đúng, km/h hợp nghĩa.
143|360/18=20 km/h; công thức vận tốc và đơn vị tương đương km/giờ đúng.
144|756/54=14 giờ; quãng đường chia vận tốc đúng, đề không nghỉ nên không cần bớt/cộng thời gian khác.
145|594/33=18 giờ; nhận đúng vận tốc giữ nguyên và thời gian cần tìm.
146|91/7=13 giờ; công thức thời gian đúng và không thêm thời gian nghỉ.
147|58.97*10000=589700 cm²; giải thích 100 cm*100 cm=10000 cm² đúng hệ số diện tích.
148|12.61*10000=126100 cm²; chuyển diện tích theo bình phương hệ số độ dài đúng.
149|90.68*10000=906800 cm²; nhấn mạnh bình phương hệ số đổi độ dài là lý do đúng, không dùng chỉ 100.
150|55.68*1000=55680 cm³; 1 dm=10 cm dẫn tới 10*10*10=1000 theo thể tích đúng.
151|1.39*1000=1390 cm³, đổi đơn vị đúng. Nhưng thêm hint không null trong chế độ worked_solution đã có lời giải/đáp số; trộn hợp đồng chế độ dù không làm sai toán.
152|76.34*1000=76340 cm³; giải thích ba chiều khi 1 dm=10 cm đúng.
153|266000/19=14000 đồng mỗi món rồi *28=392000 đồng; đơn giá không đổi phù hợp cùng loại hàng.
154|60000/15=4000, 4000*23=92000 đồng; đúng rút về đơn vị rồi nhân số món cần mua.
155|21000/7=3000, 3000*22=66000 đồng; các đại lượng số món/giá tiền dùng đúng.
156|5*132=660 người-ngày, chia 11=60 ngày; năng suất mỗi người và công việc giữ nguyên, tỉ lệ nghịch đúng.
157|5*120=600 người-ngày, 600/12=50 ngày; giải đúng lượng công việc không đổi.
158|11*91=1001 người-ngày, chia 7=143 ngày. «Tích thường thấy» giải thích yếu thay vì tích không đổi do cùng công việc/năng suất, nhưng q đã nêu điều kiện và hai phép/đơn vị đúng.
159|69+43=112 vật, lấy 69/112 để biểu thị khả năng đỏ khi chọn đều; đúng tử là đỏ, mẫu là toàn bộ. Unit trung gian vật thay khả năng vẫn hợp nghĩa đếm các vật.
160|79+14=93 vật, đỏ chiếm 79/93; đúng điều kiện mỗi vật cơ hội như nhau và không diễn giải thành tần suất thử.
161|83+58=141, đỏ có 83/141; tổng và phần đỏ đúng, phân số không cần đơn vị.
162|1/18 là số lần thấy chia số lần thử; không khẳng định xác suất chắc chắn của lần sau, đúng tần suất quan sát.
163|2/23 là tần suất quan sát, giải thích rõ chia số lần sự kiện cho số lần thử.
164|394/404=197/202; rút gọn đúng tỉ số quan sát, không hứa xác suất tương lai.
165|Final 963637 đúng, nhưng nói viết dấu phẩy cho số tự nhiên, yêu cầu nhớ ở cột không cần nhớ và cuối tính 6+3+1=10 trong khi phải 6+3=9. Các bước/carry không tạo ra đáp số đã ghi; hướng dẫn đặt tính sai nghiêm trọng.
166|Final 963637 đúng nhưng không giữ/đối chiếu kết quả quan sát 963638; bắt đầu hàng chục với 3+3 thay vì 0+3, bỏ cột đơn vị và nhớ, sai nhãn nhiều hàng, có lệnh «xóa kết quả». Dữ kiện chữ số/cách sửa bị bịa, không thể suy lỗi học sinh từ đáp số theo cách này.
167|Final 1080869 và từng phép cộng cột cơ bản đúng, nhưng lời giải lặp yêu cầu viết nhớ ở các cột 5+4,3+3,3+5 không có nhớ; bước gọi «gộp ... để được kết quả» lại 9+1=10, không phải ghép 1080869. Không đủ hướng dẫn đặt tính đúng để đạt kết quả.
168|Final 1104949 đúng nhưng nói «không cần nhớ» ở 5+9=14 và các cột cần nhớ, bỏ các +1 vào cột sau, gắn chữ số viết sai và hàng triệu 0+0=0 dù nói viết 1. Chuỗi carry trái với đáp số đúng.
169|Final 33072 đúng nhưng viết 0−8=10,7−9=16,0−9=10,2−8=11/10; các dòng này không phải phép trừ hợp lệ và không cập nhật mượn qua 0. Không thể dùng lời giải này để dạy trừ có mượn.
170|Không có visible_output và bị truncated; không có lời giải để so sánh 33073 quan sát với 33072 đúng. Ghi thất bại, không điền đáp số/reference thay model.
171|Không có visible_output và bị truncated; không có lời giải đầy đủ cho 838454−76991. Ghi thất bại, không sửa bằng phép tính từ reference.
172|Visible JSON bị cắt giữa bước hàng trăm với expression 1−8 chưa có result/đóng cấu trúc. Không có câu trả lời hoàn chỉnh; chỉ answer xuất hiện đầu chuỗi không đủ chứng minh giải đúng, ghi thất bại truncated.
""".strip().splitlines()
notes = {}
for line in REASONS:
    idx, reason = line.split("|", 1)
    notes[int(idx)] = reason
assert set(notes) == set(range(173)), "Every actual visible packet has an explicit authored reason"

semantic_fail = {12,36,37,41,46,60,62,69,71,73,83,98,100,103,123,125,165,166,167,168,169,170,171,172}
instruction_fail = {73,151,166,170,171,172}
grade_fail = {12,36,37,38,41,46,48,50,57,58,59,60,61,62,69,71,73,83,98,100,103,118,123,125,165,166,167,168,169,170,171,172}
invented = {41,166}
severe = {12,36,37,46,69,71,73,83,98,100,103,165,166,167,168,169,170,171,172}
operation_fail = semantic_fail
roles_fail = {12,37,46,60,62,69,71,73,83,98,100,103,123,125,165,166,167,168,169,170,171,172}
method_fail = {36,37,69,73,98,100,165,166,167,168,169,170,171,172}
guidance_fail = semantic_fail | {38,108,109,110}
numeric_fail = {46,73,98,170,171,172}
unit_fail = {37,73,170,171,172}
minor_wording = {24,25,26,31,32,47,49,51,54,63,65,81,82,90,93,104,106,107,108,109,110,118,119,120,123,125,131,158}
valid_alternative = {47,54,70,124,126,133}

stamp = datetime.now(timezone.utc).isoformat()
packet_hash = hashlib.sha256(PACKETS.read_bytes()).hexdigest()
decisions = []
for i, row in enumerate(rows):
    assert row["model"] == "candidate" and row["kind"] == "worked_solution"
    parsed = row["visible_output"]["strict_parsed"]
    review = {
        "status": "COMPLETED_AI_SEMANTIC_RESEARCH_REVIEW",
        "review_kind": "AI_SEMANTIC_RESEARCH_REVIEW",
        "human_verified": False,
        "teacher_certified": False,
        "semantic_correct": i not in semantic_fail,
        "instruction_followed": i not in instruction_fail,
        "grade_appropriate": i not in grade_fail,
        "invented_data_or_image": i in invented,
        "severe_error": i in severe,
        "reason": notes[i],
        "explanation_operation_consistent": i not in operation_fail,
        "data_roles_correct": i not in roles_fail,
        "displayed_method_valid": i not in method_fail,
        "step_by_step_guidance_useful": i not in guidance_fail,
        "final_numeric_correct": i not in numeric_fail,
        "final_unit_semantically_correct": i not in unit_fail,
        "final_numeric_and_unit_semantically_correct": i not in numeric_fail | unit_fail,
        "generated_answer_visible": parsed.get("answer") if parsed else None,
        "generated_unit_visible": parsed.get("unit") if parsed else None,
        "minor_wording_or_detail_issue": i in minor_wording,
        "valid_alternative_method": i in valid_alternative,
        "truncated_or_missing": bool(row["automatic_observations"]["strict_scores"]["truncated"] or row["visible_output"]["text"] is None),
        "reviewed_complete_visible_packet": True,
        "reviewed_at_utc": stamp,
    }
    decisions.append({
        "model": "candidate", "sample_id": row["sample_id"], "grade": row["grade"],
        "kind": "worked_solution", "topic": row["topic"], "packet_index": i,
        "packet_source_sha256": packet_hash,
        "visible_output_sha256": hashlib.sha256(json.dumps(row["visible_output"], ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest(),
        "review": review,
    })

out = ROOT / "candidate_worked_semantic_decisions.jsonl"
out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in decisions), encoding="utf-8", newline="\n")

FIELDS = ["semantic_correct", "instruction_followed", "grade_appropriate", "invented_data_or_image", "severe_error", "explanation_operation_consistent", "data_roles_correct", "displayed_method_valid", "step_by_step_guidance_useful", "final_numeric_correct", "final_unit_semantically_correct", "final_numeric_and_unit_semantically_correct", "truncated_or_missing", "minor_wording_or_detail_issue", "valid_alternative_method"]
def counts(items):
    return {"samples": len(items), **{f: {"true": sum(r["review"][f] for r in items), "false": sum(not r["review"][f] for r in items)} for f in FIELDS}}

summary = {
    "schema": "mvk_full_thinking_worked_semantic_review_summary_v1",
    "run_id": "qwen3_17b_teacher_math_v3_epoch1_seed20261013",
    "evaluation_id": "full_thinking_validation_seed20261013",
    "model": "candidate", "review_kind": "AI_SEMANTIC_RESEARCH_REVIEW",
    "status": "COMPLETED_ALL_173_VISIBLE_WORKED_PACKETS",
    "human_verified": False, "teacher_certified": False, "production_approved": False,
    "reviewed_at_utc": stamp,
    "packet_file": str(PACKETS), "packet_sha256": packet_hash,
    "decision_file": str(out), "decision_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    "all_sample_ids_unique": len({r["sample_id"] for r in decisions}) == 173,
    "all_packets_read_actual_visible": True,
    "hidden_thinking_reviewed_or_exported": False,
    "counts": counts(decisions),
    "per_grade": {str(g): counts([r for r in decisions if r["grade"] == g]) for g in range(1,6)},
    "correct_numeric_but_semantic_fail": [{"sample_id":r["sample_id"], "grade":r["grade"], "index":r["packet_index"], "reason":r["review"]["reason"]} for r in decisions if r["review"]["final_numeric_correct"] and not r["review"]["semantic_correct"]],
    "severe_examples": [{"sample_id":r["sample_id"], "grade":r["grade"], "index":r["packet_index"], "reason":r["review"]["reason"]} for r in decisions if r["review"]["severe_error"]],
    "valid_alternative_examples": [{"sample_id":r["sample_id"], "index":r["packet_index"], "reason":r["review"]["reason"]} for r in decisions if r["review"]["valid_alternative_method"]],
    "unit_alias_or_descriptive_difference_accepted": [13,93,141,142,143],
    "dimensional_unit_error": [37],
    "declared_grade_source_difficulty_issues": [48,50,57,58,59,60,61,62],
    "rubric_notes": [
        "semantic_correct checks visible arithmetic, data roles and step explanations; final answer alone is insufficient.",
        "instruction_followed records requested mode/completeness and preservation of observed work separately from mathematical correctness.",
        "Each explicit manual reason was written after reading its actual problem, reference and visible output; index sets serialize those decisions, not an automated classifier.",
        "Different valid methods are accepted. No original strict/raw score, source, training data, protocol or selection is changed.",
        "The 3 truncated outputs are failures, including the partial JSON containing an apparent answer field.",
        "Programming remainder operator % is mathematically valid but not accepted as sufficient child-facing grade 3 teaching without explanation.",
        "Unit aliases vật/đồ vật and km/h/km/giờ are not dimensional errors; descriptive đơn vị for a place-value number is accepted semantically.",
        "Grade suitability is an AI method/language judgment with explicit source difficulty flags, not a legal certification of every current and historical curriculum outcome.",
        "One AI reviewer assessed these worked outputs; independent review/adjudication by the parent may revise borderline semantic/wording labels with evidence.",
        "AI-authored teacher targets and one-seed development validation do not constitute human gold or general accuracy certification.",
    ],
}
(ROOT / "candidate_worked_semantic_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"status": summary["status"], "counts": summary["counts"], "packet_sha256": packet_hash, "decisions_sha256": summary["decision_sha256"]}, ensure_ascii=False))

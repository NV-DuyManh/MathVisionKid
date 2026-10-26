"""AI research review of every visible hint/guard; hand-authored decisions.

This reads only packets containing final visible answers, never raw hidden thoughts.
Flags/claims below were assigned after reading each problem and entire visible reply.
No lexical/automatic correctness score determines a semantic decision.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = {
    "baseline_hint": "baseline_hint_review_packets.jsonl",
    "candidate_hint": "candidate_hint_review_packets.jsonl",
    "baseline_guard": "baseline_guard_review_packets.jsonl",
    "candidate_guard": "candidate_guard_review_packets.jsonl",
}

# Per row: semantic correct, grade appropriate, invented facts, severe semantic
# error; useful standalone hint rating, evidence-grounded reason.
# B/C refer to baseline/candidate, not proposed selection.
B_HINT = [
    (1,1,0,0,"related_but_weak","3+10=13 đúng nhưng xuất cả phép tính/đáp số; lời kiểm tra không phải câu hỏi gợi ý."),
    (1,1,0,0,"related_but_weak","58-16=42 đúng; đưa đáp số rồi yêu cầu kiểm tra chung chung."),
    (1,1,0,0,"useful","29-9=20 đúng; gợi đúng phép trừ nhưng cùng lúc giải và lộ đáp số."),
    (1,1,0,0,"related_but_weak","19-1=18 đúng; gợi kiểm tra chung, không dẫn một bước tự làm."),
    (1,1,0,0,"answer_disclosure","Giải thích 1 chục=10 đơn vị đúng nhưng hint cũng nói thẳng giá trị 10."),
    (1,1,0,0,"absent","10*2=20 đúng; hint=null và đã giải hết bài."),
    (1,1,0,0,"useful","40÷5=8 đúng; gợi chia đều đúng nhưng kèm đáp số."),
    (0,0,0,1,"absent","Bước đầu ghi 2×x=12 nhưng result=x=12, sai; cuối x=6 đúng vẫn lộ đáp số và dùng chia hai vế thay cách lớp 2."),
    (1,1,0,0,"related_but_weak","79+68=147,147-6=141 đúng; giải toàn bộ, hint chỉ bảo kiểm tra."),
    (1,1,0,0,"related_but_weak","8*4=32,32-29=3 đúng; có lỗi từ viên/bộ thay hộp, hint kiểm tra chung."),
    (1,1,0,0,"useful","710-350=360 đúng; kiểm tra phép trừ bằng cộng ngược phù hợp nhưng đã lộ 360."),
    (1,1,0,0,"absent","48-37=11 phút đúng; không có hint, xuất lời giải."),
    (0,0,0,1,"useful","Kết quả dư 2 đúng nhưng bước số hộp ghi 57.2857... hộp dù phải là 57 hộp đủ; số thập phân chia dư chưa phù hợp lớp 3."),
    (1,1,0,0,"absent","2*7=14 rồi 94+14=108 đúng; hint=null, giải toàn bộ."),
    (1,1,0,0,"useful","173m=17300cm đúng; chỉ rõ đổi ×100 nhưng tiết lộ kết quả."),
    (1,1,0,0,"useful","Đổi 4 giờ=240 phút rồi cộng 56 được296 đúng; hint đổi cùng đơn vị hữu ích nhưng lời giải đầy đủ."),
    (1,1,0,0,"absent","263kg=263000g đúng; hint=null và đã xuất đáp số."),
    (0,1,0,1,"related_but_weak","Bước expression=2*(80+84) nhưng result=164 sai; cuối328 đúng không chữa được bước sai này."),
    (1,1,0,0,"useful","Chu vi 4*156=624 đúng; hint nêu công thức đúng nhưng đã giải."),
    (1,1,0,0,"absent","46*60=2760cm² đúng; hint=null, đưa đáp số."),
    (1,1,0,0,"useful","209*209=43681cm² đúng; hint nêu phép tính cần làm, nhưng đáp số đã lộ."),
    (1,1,0,0,"related_but_weak","12+73+25=110 đúng; gợi kiểm tra chung sau khi đã giải."),
    (1,0,0,0,"related_but_weak","705 đúng nhưng dùng hệ hai phương trình/cộng phương trình cho lớp4 và JSON expression không hợp lệ; không đưa câu hỏi hint."),
    (1,0,0,0,"related_but_weak","169 đúng nhưng diễn giải hệ/phép thế 2x+119 thay phương pháp tổng-hiệu lớp4; lộ đáp số."),
    (1,1,0,0,"absent","(4+17)/3=7 đúng; hint=null, giải hết."),
    (0,1,0,1,"related_but_weak","3/2=12/8 nhưng result=12;17/8-12/8 ghi result=5 thay5/8. Final5/8 đúng song hai bước sai."),
    (1,1,0,0,"related_but_weak","17/7*2=34/7 đúng; unit=tỉ lệ không cần thiết, gợi kiểm tra chung, lộ đáp số."),
    (1,1,0,0,"related_but_weak","(9/2)/(5/3)=27/10 và nghịch đảo đúng; unitless là tiếng Anh thừa, đã giải."),
    (1,0,0,0,"useful","(65+30+4)/3=33 đúng; thêm khái niệm mode không cần cho lớp4, đưa toàn bộ kết quả."),
    (1,1,0,0,"useful","460*3/5=276 đúng; hint tìm1/5 rồi×3 nêu cả đường giải và đã lộ276."),
    (1,1,0,0,"related_but_weak","53*25=1325cm² đúng; chỉ gợi kiểm tra phép nhân đã giải."),
    (1,1,0,0,"related_but_weak","1+8=9 phần,324/9=36 đúng; giải toàn bộ phân chia rồi gợi kiểm tra."),
    (1,1,0,0,"related_but_weak","Số tiếp theo3 đúng; hint xem quy tắc chung sau khi đã nói cả dãy."),
    (0,1,0,1,"useful","Bước đầu57.25+29.86 lại result57.25 sai; cuối87.11 đúng nhưng xuất bước sai và đáp số."),
    (1,1,0,0,"related_but_weak","25.93-10.46=15.47 đúng; gợi kiểm tra chung, unit tiếng Anh không cần."),
    (0,1,0,1,"answer_disclosure","Expression(73*7609)/1000=result555457 sai ở bước đầu; cuối555.457 đúng, hint nói thẳng kết quả."),
    (0,1,0,1,"useful","Expression50.32*10÷1.7*10 thiếu ngoặc không bảo toàn thương và không bằng result503.2; cuối29.6 đúng."),
    (1,1,0,0,"answer_disclosure","7600*0.23=1748 đúng; hint Không cần tính toán thêm, kết quả đã chính xác không để học sinh tự giải."),
    (1,1,0,0,"answer_disclosure","6468/(66/100)=9800 đúng; hint cũng lộ9800 trong phép kiểm."),
    (1,1,0,0,"useful","66/3300=2% đúng; trả đáp số và hint chứa phép tính đã làm0.02."),
    (1,1,0,0,"absent","42*59/2=1239cm² đúng; hint=null, giải hết."),
    (1,1,0,0,"related_but_weak","(15+42)*86/2=2451cm² đúng; đã giải ba bước, hint kiểm tra chung."),
    (1,1,0,0,"related_but_weak","106²*3.14=35281.04 đúng; JSON có escape LaTex không hợp lệ, lời gợi kiểm tra chung."),
    (1,1,0,0,"related_but_weak","2*3.14*32=200.96cm đúng; đã lộ đáp số, gợi kiểm tra chung."),
    (1,1,0,0,"useful","20*76*29=44080cm³ đúng; hint đưa đường nhân hai bước kèm đáp số."),
    (1,1,0,0,"useful","6*7²=294cm² đúng; nhắc sáu mặt phù hợp nhưng đã giải hết."),
    (1,1,0,0,"absent","50*30=1500km đúng; hint=null, xuất đáp số."),
    (1,1,0,0,"related_but_weak","19km/giờ đúng với chuyển động một giờ; gợi kiểm tra thông tin đã rõ, lộ số19."),
    (1,1,0,0,"answer_disclosure","756/54=14 giờ đúng; hint cũng nêu14 khi nhân ngược."),
    (1,0,0,0,"useful","58.97m²=589700cm² đúng nhưng explanation và hint đều bằng tiếng Anh, chưa phù hợp trợ giảng tiếng Việt."),
    (1,1,0,0,"absent","55.68dm³=55680cm³ đúng; hint=null và đã giải hết."),
    (0,1,0,1,"related_but_weak","266000/19 phải14000 nhưng ghi140000, khiến28 món=3920000 sai gấp10; hint không phát hiện lỗi."),
    (1,1,0,0,"useful","5*132/11=60 ngày đúng; gợi quan hệ tỉ lệ hữu ích nhưng giải toàn bộ."),
    (1,1,0,0,"related_but_weak","69/(69+43)=69/112 đúng; đã lộ phân số, gợi kiểm tra chung."),
    (1,1,0,0,"useful","Tần suất1/18 đúng; hỏi kiểm tra tử số dạng câu lệnh, đã lộ phân số."),
    (1,1,0,0,"related_but_weak","605904+357733=963637 đúng; lời gợi kiểm tra từ phải sang trái sau khi đưa kết quả."),
    (1,1,0,0,"useful","Tính lại ra963637 và chỉ đúng hàng đơn vị cần kiểm; không gán động cơ lỗi học sinh, nhưng giải/lộ hết đáp số."),
    (0,0,0,0,"useful","82070-48998=33072 đúng nhưng unit=82070 vô nghĩa; đã trả đáp số thay câu hỏi hint."),
    (0,0,0,1,"absent","Không có visible_output: không có câu hỏi gợi ý hay xử lý bài làm33073; không loại mẫu này khỏi đánh giá."),
]

C_HINT = [
    (1,1,0,0,"useful","Câu hỏi chọn phép cộng phù hợp không lộ13 nhưng status=clarify dù đề đủ dữ kiện."),
    (1,1,0,0,"useful","Một câu hỏi chọn phép tính tìm phần còn lại; không lộ42 hoặc giải sẵn."),
    (1,1,0,0,"useful","29-9=20 đúng nhưng answer và bước giải làm lộ20 dù hint hỏi quan hệ trước/sau."),
    (1,1,0,0,"useful","Hỏi phép so số lớn/bé phù hợp nhưng answer18 và unit đã lộ đáp số."),
    (0,0,0,1,"related_but_weak","Trả answer10 với unit=chục gây hiểu10 chục thay giá trị10; dùng Digit không phù hợp tiếng Việt lớp1; lộ đáp số."),
    (1,1,0,0,"useful","10*2=20 đúng nhưng đưa lời giải; câu hỏi các nhóm bằng nhau vốn đúng không cần bịa."),
    (1,1,0,0,"useful","Hỏi chia tổng cho số nhóm đúng nhưng answer8 làm lộ kết quả."),
    (1,1,0,0,"absent","12/2=6 đúng; không có hint và xuất toàn bộ lời giải."),
    (1,1,0,0,"useful","Hỏi cộng trước khi bớt phù hợp trình tự79+68 rồi-6; không nêu kết quả."),
    (1,1,0,0,"useful","Hỏi tìm tổng ban đầu trước khi bớt29 là bước đầu phù hợp; không lộ3."),
    (1,1,1,0,"related_but_weak","Hỏi chênh lệch tiền có với tiền dùng dẫn710-350, nhưng câu vụng và tự thêm để mua đồ không có trong đề."),
    (1,1,0,0,"useful","Hỏi phép tính tìm thời gian giữa hai mốc37,48 phù hợp và không lộ11."),
    (1,1,0,0,"related_but_weak","Answer2 là số dư đúng nhưng làm lộ đáp số; ghi nhớ số dư như thế nào quá mơ hồ."),
    (0,0,0,1,"misleading","Hint coi tổng đã biết và yêu cầu tìm số hạng, trái đề cần tổng94+2*7; answer108 đúng nhưng lộ đáp số."),
    (1,1,0,0,"useful","Câu hỏi1m bằng bao nhiêu cm hữu ích; tuy nhiên kèm173*100=17300 và đáp số."),
    (1,1,0,0,"related_but_weak","4 giờ=240 phút,+56=296 đúng; câu hỏi cộng trước tìm tổng không nhắc cần đổi cùng đơn vị và đã giải."),
    (1,1,0,0,"useful","Câu hỏi1kg bao nhiêu g đúng; kèm263000g nên lộ đáp số."),
    (1,1,0,0,"useful","Hỏi hai cặp cạnh bằng nhau dẫn chu vi chữ nhật, không nêu phép tính đã giải."),
    (1,0,0,0,"related_but_weak","Hỏi số cạnh để cộng liên quan chu vi vuông nhưng thuật ngữ hình chữ nhật vuông không chuẩn với lớp3."),
    (1,1,0,0,"useful","Hỏi cách tính diện tích chữ nhật đúng nhưng answer2760cm² làm lộ đáp số."),
    (1,1,0,0,"absent","209*209=43681 đúng nhưng explanation nhắc hai số hàng thay số ô/hàng và hint=null; đã giải hết."),
    (1,1,0,0,"useful","Hỏi phép kết hợp ba giá trị tìm tổng đúng, không nêu110."),
    (1,1,0,0,"related_but_weak","Câu hỏi tổng-hiệu liên quan số lớn nhưng lặp số lớn và không định hướng một bước cụ thể."),
    (1,1,0,0,"useful","Tìm số lớn288 rồi trừ119=169 đúng; hỏi tìm số lớn có thể là đường giải nhưng lộ toàn bộ."),
    (1,1,0,0,"related_but_weak","Hai phân số đã cùng mẫu3; hỏi mẫu chung hơi dư thừa và answer7 làm lộ kết quả."),
    (1,1,0,0,"useful","Một câu hỏi kiểm mẫu chung trước khi trừ17/8-3/2, chưa lộ5/8."),
    (1,1,0,0,"related_but_weak","Hỏi kết hợp tử/mẫu liên quan phép nhân nhưng không rõ phải nhân thế nào với2; không bịa số."),
    (1,1,0,0,"useful","Nghịch đảo để chia đúng và27/10 đúng; câu hỏi phù hợp nhưng đã giải/lộ kết quả."),
    (1,1,1,0,"useful","65+30+4=99,99/3=33 đúng; tự nói đã ghi trong bảng dù đề chỉ dữ liệu ba ngày, và lộ kết quả."),
    (1,1,0,0,"related_but_weak","Phần số là từ sai/phần cần tìm mơ hồ; vẫn hướng lượng460 và phần3/5, không nêu đáp số."),
    (1,1,0,0,"useful","Hỏi chọn chiều cao tương ứng thay cạnh xiên đúng nhưng answer1325cm² làm lộ đáp số."),
    (0,0,0,1,"misleading","Hint tìm tổng phần rồi chia cho tổng đồ vật đảo chiều phép chia; đúng phải324÷9; answer36 vẫn lộ."),
    (1,1,0,0,"useful","Hỏi mức tăng mỗi bước phù hợp nhưng answer3 lộ số tiếp theo."),
    (1,1,0,0,"useful","Hỏi đặt thẳng hàng chữ số/dấu phẩy trước cộng là một bước hữu ích, không lộ87.11."),
    (1,1,0,0,"related_but_weak","Hỏi số lớn trừ số bé phù hợp25.93-10.46 nhưng gần như nhắc lại đề, chưa giúp thao tác thập phân."),
    (1,1,0,0,"useful","Có thể dự kiến vị trí dấu phẩy từ số chữ số thập phân trước nhân; không lộ555.457 nhưng status=hint không thuộc schema."),
    (1,1,0,0,"useful","Hỏi nhân cả hai số cùng hệ số để số chia thành số tự nhiên đúng; chưa lộ29.6."),
    (0,0,0,0,"misleading","Đổi phần trăm rồi nhân tổng là hướng đúng nhưng đuôi không chính xác chưa làm câu hỏi vô nghĩa/không rõ có khẳng định sai hay không."),
    (1,1,0,0,"absent","6468/66*100=9800 đúng nhưng hint=null, đưa lời giải thay gợi ý."),
    (1,1,0,0,"useful","Hỏi đổi phân số thành phần trăm đúng nhưng answer2 lộ kết quả và thiếu% trong unit."),
    (1,1,0,0,"useful","Một câu hỏi nhân đáy/cao rồi chia số nào để nhớ hệ số1/2, chưa tính hoặc lộ1239."),
    (1,1,0,0,"full_solution_plan","Đưa đủ cả quy trình cộng hai đáy→nhân cao→chia2 trong một câu hỏi; không lộ số2451 nhưng quá nhiều bước cho một gợi ý."),
    (1,1,0,0,"absent","106²*3.14=35281.04 đúng; câu Không dùng hệ số pi trực tiếp vụng nhưng bước sau dùng3.14 đúng; hint=null, đã giải."),
    (1,1,0,0,"useful","Hỏi đường kính/bán kính trong công thức đúng nhưng bước32*2*3.14 và answer200.96 lộ đáp số."),
    (1,1,0,0,"full_solution_plan","20*76*29=44080 đúng; gợi nhân đủ ba kích thước và kèm cả lời giải, không còn tự giải."),
    (1,1,0,0,"useful","Hỏi số mặt lập phương để nghĩ diện tích toàn phần đúng; chưa cho diện tích một mặt hay kết quả294."),
    (1,1,0,0,"useful","Một câu hỏi nhắc quan hệ quãng đường=vận tốc×thời gian đúng; chưa tính1500."),
    (1,1,0,0,"absent","Trả19km mỗi giờ hợp nghĩa câu hỏi bao nhiêu km, khác unit tham chiếu km/giờ nhưng không khẳng định sai; hint=null và lộ19."),
    (1,1,0,0,"useful","Hỏi công thức tìm thời gian khi biết quãng đường/vận tốc đúng và không lộ14."),
    (0,0,0,1,"misleading","Đề đã cho diện tíchm²; hỏi đổi độ dài trước tính diện tích chuyển sang nhiệm vụ khác và dễ dùng sai hệ số100 thay10000."),
    (1,1,0,0,"useful","Hỏi1dm³ bao nhiêu cm³ đúng nhưng kèm55.68*1000=55680 và đáp số."),
    (1,1,0,0,"useful","Tìm đơn giá14000 rồi×28=392000 đúng; hỏi đơn giá hữu ích nhưng đã lộ lời giải."),
    (0,0,0,1,"absent","Không có visible_output, không thể coi là gợi ý đúng; mẫu vẫn nằm trong59."),
    (1,1,0,0,"useful","Hỏi số trường hợp đỏ và tổng số có thể chọn đúng, chưa tính112 hay69/112."),
    (1,1,0,0,"absent","Tần suất1/18 đúng nhưng hint=null và đã lộ phân số."),
    (1,1,0,0,"useful","Hỏi bắt đầu từ hàng nào và nhớ khi một cột đủ chục đúng; chưa cộng ra963637."),
    (0,0,1,1,"absent","Giữ answer963638 sai như học sinh; hàng chục0+3 ghi viết6 nhớ1, hàng nghìn5+7 ghi12 rồi viết3, và bịa nhiều cột/dấu nhớ không có bằng chứng; đúng tổng963637."),
    (1,0,0,0,"related_but_weak","Hỏi bắt đầu từ hàng nào liên quan đặt trừ nhưng ghi nhớ khi bớt một hàng mơ hồ thay đổi một chục/mượn; chưa lộ33072."),
    (1,1,0,0,"useful","Chỉ đúng hàng đơn vị sai vì10-8=2 khác chữ số3 học sinh; không bịa nguyên nhân/dấu mượn, nhưng câu là mệnh lệnh chấm hết thay câu hỏi."),
]

# Per guard: semantic, grade, invention, severe, valid reason, specific/useful
# clarification, complete clarification of all ambiguities, grounded reason.
B_GUARD = [
    (1,1,0,0,1,1,1,"Đúng cần số bút ban đầu, không bịa đáp số; nhưng steps và unit khácnull trong guard."),
    (1,1,0,0,1,1,1,"Nêu chính xác thiếu số bút ban đầu, không bịa; hint là hai câu trần thuật thay một câu hỏi."),
    (1,1,0,0,1,1,1,"Đúng thiếu số bút ban đầu nhưng status=unsupported thayclarify và vẫn tạo bước."),
    (1,1,0,0,1,1,0,"Đúng thiếu số ban đầu nhưng cũng đề nghị cung cấp số hiện có là đáp số cần tìm; unsupported và có bước thayclarify."),
    (1,1,0,0,1,1,1,"Nhận ra thiếu số ban đầu; hint chỉ nói thiếu chứ không hỏi bổ sung, và có bước trong guard."),
    (0,0,1,1,0,0,0,"Đổi tổng3698 quyển thành mỗi nhóm3698 quyển không có trong đề; bịa đáp số/giải bằng tiếng Anh dù thiếu số nhóm."),
    (0,1,1,1,0,0,0,"Hiểu sai tổng84887 là mỗi nhóm84887, khẳng định đề đã cho số mỗi nhóm; thiếu số nhóm nên phảiclarify."),
    (0,1,1,1,0,0,0,"Hiểu sai tổng33436 thành mỗi nhóm33436 và trả đáp số bịa; không hỏi số nhóm."),
    (1,1,0,0,1,1,1,"Đúng hỏi số nhóm, không bịa giá trị; nhưng viết bước76782÷? và unit thay bỏ trống."),
    (1,1,0,0,1,1,1,"Đúng cần số nhóm để chia81147; có bước sao chép số tổng dù không biết đáp số."),
    (0,1,1,0,1,1,0,"Đúng thiếu số chuyển nhưng tự chọn69520-? dù chưa rõ chuyển vào hay ra và hỏi lượng của ai."),
    (1,1,0,0,1,1,0,"Đúng thiếu lượng chuyển/nhóm khác, nhưng unsupported thayclarify và chưa hỏi hướng chuyển/đại lượng cần tìm."),
    (1,1,0,0,1,1,0,"Nêu thiếu lượng chuyển/kết quả mong muốn đúng, song có bước trống và chưa hỏi ai chuyển cho ai."),
    (0,1,1,0,1,1,0,"Nhận ra thiếu lượng chuyển/đại lượng cần tìm nhưng tự đặt36264+x dù hướng chuyển chưa biết; gợi có nhiều câu."),
    (0,1,1,0,1,1,0,"Thiếu dữ kiện đúng nhưng tự đặt24406-x và chỉ hỏi số chuyển/còn lại; hướng chuyển chưa biết."),
    (1,1,0,0,1,0,0,"Biết thiếu bảng và phép tính nhưng hỏi Tính gì với59694 thay yêu cầu gửi bảng/ảnh đã biết thiếu; bước sao chép số."),
    (1,1,0,0,1,1,0,"Đúng cần bảng/phép tính, có lời yêu cầu thêm thông tin; nhưng tạo bước và không một câu hỏi tronghintmode."),
    (1,1,0,0,1,1,0,"Nhận ra thiếu bảng/phép tính đúng, nhưng unsupported thayclarify, tạo bước sao chép9365."),
    (1,1,0,0,1,0,0,"Nhắc bảng chưa có nhưng chỉ xin điều kiện/phép tính quanh31368, chưa xin bảng; tạo bước và hint trần thuật."),
    (1,1,0,0,1,1,1,"Đúng yêu cầu thêm bài/bảng, không giả đã thấyảnh; vẫn tạo bước sao chép12042."),
    (1,1,0,0,1,0,0,"Từ chối chia0 đúng; nhưng answer vàunit là không thể chia,steps có lời giải, không hướng kiểm số chia."),
    (1,1,0,0,1,0,0,"Đúng chia0 không xác định; hint yêu cầu giải thích chứ không hỏi số chia, và cósteps/unit."),
    (1,1,0,0,1,0,0,"Đúng chia0 không xác định; answer là chuỗi không thể thực hiện và bước trongguard, câu hỏi quá chung."),
    (1,0,0,0,1,0,0,"Giải thích chia0 không xác định đúng nhưngstatus=solve/answer=undefined, tiếng Anh và có bước; không phải guard chuẩn."),
    (1,1,0,0,1,0,0,"Nhận chia0 không xác định đúng nhưng trả answer Không xác định/steps, hint lặp lại thay hỏi kiểm số chia."),
    (0,1,0,0,1,0,0,"Unsupported với lập trình đúng phạm vi nhưng gợi giảm số nhân vật để phù hợp làm lệch lý do phạm vi toán; vẫn tạo bước/unit."),
    (1,1,0,0,0,0,0,"Không bịa nhưng câu xin thêm yêu cầu chung không nói hoặc hướng về toán tiểu học; thiếu guardreason cụ thể."),
    (0,1,1,1,0,0,0,"Bịa không thể lập trình58094 nhân vật vì số lớn; giới hạn kỹ thuật không có bằng chứng, answer khácnull."),
    (0,1,0,1,0,0,0,"Statusunsupported nhưng hint xin mục tiêu/quy tắc trò chơi để lập trình, tiếp tục nhiệm vụ ngoài toán thay chuyển hướng."),
    (1,1,0,0,1,0,0,"Xin cụ thể bài toán/tính toán có liên quan toán nhưngstatusclarify thayunsupported cho yêu cầu lập trình và cósteps."),
]

C_GUARD = [
    (1,1,0,0,1,1,1,"Hỏi đúng số lượng ban đầu còn thiếu, không tính hoặc bịa đáp số."),
    (1,1,0,0,1,1,1,"Hỏi đúng số ban đầu; lượng hàng hơi lệch đối tượng bút nhưng không thêm số liệu/quy tắc."),
    (1,1,0,0,1,1,1,"Hỏi số ban đầu đúng với dữ kiện cần bổ sung."),
    (1,1,0,0,1,1,1,"Hỏi rõ số bút ban đầu còn thiếu."),
    (1,1,0,0,1,1,1,"Hỏi đúng số lượng ban đầu thay đoán42077 là đáp số."),
    (0,1,0,0,1,0,0,"Số nhóm là dữ kiện thiếu đúng nhưng đưa lựa chọn số bạn trong nhóm không giúp tìm số vở mỗi nhóm; cần hỏi riêng số nhóm."),
    (1,1,0,0,1,1,1,"Hỏi số nhóm đúng; gọi vở là phần thưởng chưa được nêu nhưng không đổi phép chia hay bịa số."),
    (1,1,0,0,1,1,1,"Hỏi số nhóm đúng, không giả tổng là số mỗi nhóm."),
    (1,1,0,0,1,1,1,"Câu hơi vụng nhưng hỏi số nhóm được chia đều là thông tin cần bổ sung."),
    (1,1,0,0,1,1,1,"Hỏi trực tiếp bao nhiêu nhóm nhận chia đều, đúng dữ kiện thiếu."),
    (0,1,1,1,1,0,0,"Tự chọn đồ vật đưa vào nhóm từ nhóm khác dù chiều chuyển chưa biết; hỏi lượng không sửa giả định về hướng."),
    (1,1,0,0,1,1,0,"Hỏi lượng chuyển và nguồn là hai dữ kiện thật còn thiếu; chưa xác định đang hỏi lượng của nhóm nào."),
    (1,1,0,0,1,1,0,"Hỏi số nhóm khác đúng dữ kiện chưa biết, là một bước làm rõ hợp lý nhưng chưa đủ hướng/lượng chuyển/đại lượng cần tìm."),
    (1,1,0,0,1,1,0,"Hỏi lượng đưa vào hoặc lấy đi không áp đặt dấu phép tính; chưa hỏi cụ thể kết quả của nhóm nào."),
    (0,1,1,1,1,0,0,"Tự giả định chuyển từ nhóm2 sang nhóm1; đề chưa chỉ hướng, nên có thể ép học sinh dùng phép cộng sai."),
    (1,1,0,0,1,1,1,"Nhắc đúng cần hình/bảng còn thiếu, không nhận đã nhìn thấy ảnh hoặc đoán đáp số."),
    (1,1,0,0,1,1,1,"Yêu cầu hình/bảng và đưa ví dụ thông tin cần là hợp lý, nhưng hint chứa hai câu hỏi thay một."),
    (1,1,0,0,1,1,1,"Hỏi thêm hình/bảng/giá trị để xác định đáp số đúng; không giả nội dungảnh."),
    (1,1,0,0,1,1,1,"Hỏi thêm bảng/hình/phép tính phù hợp nhưng chứa hai câu hỏi và mở lựa chọn quá rộng."),
    (1,1,0,0,1,1,0,"Nêu bảng/ảnh có thể bị thiếu là khả năng đúng rồi yêu cầu thêm thông tin, nhưng chưa trực tiếp xin ảnh/bảng."),
    (1,1,0,0,1,1,1,"Chia0 không xác định và hỏi kiểm số chia đúng; không đưa kết quả số."),
    (1,0,0,0,1,1,1,"Chia0 không xác định/hỏi kiểm số chia đúng; dùngzero thay0 không phù hợp giọng tiếng Việt lớp2."),
    (1,1,0,0,1,1,1,"Từ chối chia0 và hỏi kiểm số chia đúng."),
    (1,0,0,0,1,1,1,"Từ chối chia0/hỏi kiểm số chia đúng; dùngzero tiếng Anh không cần thiết."),
    (1,1,0,0,1,1,1,"Đúng chia0 không xác định, yêu cầu kiểm lại số chia."),
    (1,1,0,0,1,1,1,"Unsupported đúng với yêu cầu lập trình, chuyển sang hỏi bài toán tiểu học rõ ràng."),
    (1,1,0,0,1,1,0,"Unsupported đúng và đề nghị thêm câu hỏi toán; lựa chọn mô tả yêu cầu chung hơi rộng nhưng chưa nhận viếtcode."),
    (0,1,0,0,0,0,0,"Clarify thayunsupported với yêu cầu lập trình đã rõ; hỏi vấn đề toán hoặc yêu cầu giải quyết không đặt ranh giới phạm vi."),
    (0,1,0,0,0,0,0,"Clarify thayunsupported và xin hình/bảng/kích thước không liên quan yêu cầu lập trình; chuyển hướng thiếu căn cứ."),
    (0,1,0,1,0,0,0,"Clarify và xin ngôn ngữ lập trình/chức năng trò chơi, chấp nhận phát triển việc ngoài trợ giảng toán."),
]

# Explicitly reviewed instruction/leakage decisions, NOT scores from the packets.
# All baseline hints except the absent final one reveal a computed final answer.
B_HINT_NO_VISIBLE = {58}
C_HINT_LEAK = {
    2,3,4,5,6,7,12,13,14,15,16,19,20,23,24,27,28,30,31,32,
    38,39,42,43,44,47,50,51,54,56,
}
C_HINT_INSTRUCTION_FAIL = C_HINT_LEAK | {0,35,41,52,58}
# Guard instruction covers the declared JSON/status and one-question hint rule,
# separately from the meaning/usefulness of the request.
B_GUARD_INSTRUCTION_PASS = set()
C_GUARD_INSTRUCTION_FAIL = {16,18,27,28,29}
STUDENT_HANDLING = {
    ("baseline_hint",56): True,
    ("baseline_hint",58): False,
    ("candidate_hint",56): False,
    ("candidate_hint",58): True,
}


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def main():
    manual = {"baseline_hint":B_HINT,"candidate_hint":C_HINT,
              "baseline_guard":B_GUARD,"candidate_guard":C_GUARD}
    hashes = {}
    decisions = []
    for group, file_name in FILES.items():
        blob = (ROOT/file_name).read_bytes()
        hashes[file_name] = sha_bytes(blob)
        packets = [json.loads(line) for line in blob.decode("utf8").splitlines()]
        assert len(packets) == len(manual[group]) == (59 if group.endswith("hint") else 30)
        for idx, (packet, values) in enumerate(zip(packets, manual[group])):
            sem, grade, invent, severe, *rest = values
            is_hint = group.endswith("hint")
            vis = packet["visible_output"]["text"]
            try:
                visible_json = json.loads(vis) if vis is not None else None
            except (TypeError, json.JSONDecodeError):
                visible_json = None
            row = {
                "model":packet["model"],"sample_id":packet["sample_id"],
                "grade":packet["grade"],"topic":packet["topic"],
                "kind":packet["kind"],"mode":packet["mode"],
                "packet_file":file_name,"packet_index":idx,
                "packet_file_sha256":hashes[file_name],
                "visible_output_sha256":sha_bytes((vis or "").encode("utf8")),
                "problem_sha256":sha_bytes(packet["problem"].encode("utf8")),
                "review_kind":"AI_SEMANTIC_RESEARCH_REVIEW",
                "human_verified":False,"teacher_certified":False,
                "semantic_correct":bool(sem),"grade_appropriate":bool(grade),
                "invented_data_or_image":bool(invent),"severe_error":bool(severe),
                "visible_output_present":vis is not None,
                "generation_truncated":packet["automatic_observations"]["strict_scores"]["truncated"],
                "visible_parse_error":packet["visible_output"]["parse_error"],
                "observed_student_error_handled_correctly":STUDENT_HANDLING.get((group,idx)),
                "reason":rest[-1],
            }
            if is_hint:
                usefulness = rest[0]
                leakage = idx not in B_HINT_NO_VISIBLE if group == "baseline_hint" else idx in C_HINT_LEAK
                instruction = False if group == "baseline_hint" else idx not in C_HINT_INSTRUCTION_FAIL
                row.update({
                    "instruction_followed":instruction,
                    "hint_relevance":("absent" if usefulness == "absent" else
                                      "misleading" if usefulness == "misleading" else "related"),
                    "hint_usefulness":usefulness,
                    "answer_leakage":leakage,
                    "full_solution_plan_in_hint":usefulness == "full_solution_plan",
                    "unnecessary_clarification":group == "candidate_hint" and idx == 0,
                    "acceptable_hint":bool(sem and grade and instruction and not invent and not severe and not leakage and usefulness == "useful"),
                })
                # Grounded math usefulness and correctness can be true even though
                # the response leaks an answer. Do not hide those distinct failures.
                row["acceptable_for_intended_role"] = row["acceptable_hint"]
            else:
                valid, specific, complete, _reason = rest
                instruction = idx in B_GUARD_INSTRUCTION_PASS if group == "baseline_guard" else idx not in C_GUARD_INSTRUCTION_FAIL
                row.update({
                    "instruction_followed":instruction,
                    "guard_reason_valid":bool(valid),
                    "clarification_specific_and_useful":bool(specific),
                    "clarification_complete":bool(complete),
                    "false_refusal":False,
                    # Status can be semantically right even when schema/answer
                    # suppression makes strict_parsed null. Keep those distinct.
                    "guard_route_correct":isinstance(visible_json,dict) and visible_json.get("status") == packet["reference"]["target"]["status"],
                    "acceptable_guard":bool(sem and grade and instruction and valid and specific and not invent and not severe),
                })
                row["acceptable_for_intended_role"] = row["acceptable_guard"]
            decisions.append(row)
    assert len(decisions) == 178
    keys = [(r["model"],r["sample_id"]) for r in decisions]
    assert len(set(keys)) == 178
    # Every packet is reviewed, including missing/truncated visible answers.
    target = ROOT/"hint_guard_semantic_decisions.jsonl"
    target.write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in decisions),encoding="utf8")
    summary = {
        "review_kind":"AI_SEMANTIC_RESEARCH_REVIEW","human_verified":False,
        "teacher_certified":False,"selection_changed":False,
        "status":"COMPLETED_VISIBLE_HINT_GUARD_REVIEW",
        "packets_reviewed":178,"expected_packets":178,
        "input_packet_sha256":hashes,
        "decisions_file":target.name,"decisions_sha256":sha_bytes(target.read_bytes()),
        "definition_notes":[
            "semantic_correct evaluates truth/grounding of visible claims separately from instruction compliance; a numerically correct leaked full solution still fails its hint role.",
            "instruction_followed evaluates declared status/JSON answer suppression and one-question hint requirement; lexical-match and automatic hint_safe scores are not semantic decisions.",
            "grade_appropriate concerns response language/teaching method for the supplied grade, not certification of the engineered problem's official curriculum assignment.",
            "answer_leakage includes computed final answers even when wrong; absent visible responses fail and remain in the denominator.",
            "invented_data_or_image concerns asserted extra context, direction, values, or visual evidence; mild paraphrase drift is explained without equating it with hallucinated numbers.",
            "guard complete distinguishes all missing ambiguities from a useful first clarification question; not every useful first question must ask all missing facts at once.",
            "severe_error is a wrong numerical/procedural assertion, fabricated decisive input/direction, absent visible response, or active redirect into out-of-scope programming; hint answer leakage is counted separately and always fails acceptance.",
            "This is one AI reviewer research assessment of a development seed, not human verification or a hidden teacher benchmark. No hidden thinking text was reviewed or exported.",
        ],
        "models":{},"severe_examples":[],
        "recommendations_for_future_unfrozen_teacher_data":[
            "Strengthen one-step hint examples and answer suppression; thinking full solutions often leak the answer even when arithmetic is correct.",
            "Include contrastive guards for unknown division group count: say explicitly tổng cộng X quyển vở được chia đều, instead of the less clear nhóm nhận đều X phrasing; do not rewrite this frozen evaluation.",
            "Ask who transfers to whom before fixing addition/subtraction in ambiguous transfer problems, and avoid inferring carry/borrow marks from only the student's final answer.",
            "Redirect coding requests to elementary math consistently; do not ask for programming language/game features in the tutoring guard.",
            "Keep solve accuracy, explanation correctness, hint usefulness, answer leakage, and guard meaning as separate measures; this review does not change selection or authorize new training.",
        ],
    }
    bool_fields = ["semantic_correct","instruction_followed","grade_appropriate","invented_data_or_image","severe_error","acceptable_for_intended_role","answer_leakage","guard_reason_valid","clarification_specific_and_useful","clarification_complete","guard_route_correct"]
    for model in ["baseline","candidate"]:
        model_rows = [r for r in decisions if r["model"] == model]
        m = {}
        for kind in ["hint","guard"]:
            rows = [r for r in model_rows if r["kind"] == kind]
            assert len(rows) == (59 if kind == "hint" else 30)
            stats = {"samples":len(rows),"counts":{f:sum(r.get(f) is True for r in rows) for f in bool_fields if any(f in r for r in rows)}}
            if kind == "hint": stats["hint_usefulness"] = dict(Counter(r["hint_usefulness"] for r in rows))
            stats["per_grade"] = {}
            for g in range(1,6):
                grade_rows = [r for r in rows if r["grade"] == g]
                stats["per_grade"][str(g)] = {"samples":len(grade_rows),"counts":{f:sum(r.get(f) is True for r in grade_rows) for f in bool_fields if any(f in r for r in grade_rows)}}
            m[kind] = stats
        summary["models"][model] = m
    summary["severe_examples"] = [{k:r[k] for k in ["model","sample_id","grade","topic","kind","reason"]} for r in decisions if r["severe_error"]]
    summary["observed_student_error_cases"] = [{k:r[k] for k in ["model","sample_id","topic","observed_student_error_handled_correctly","answer_leakage","instruction_followed","reason"]} for r in decisions if r["observed_student_error_handled_correctly"] is not None]
    (ROOT/"hint_guard_semantic_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"packets":len(decisions),"models":summary["models"],"decisions_sha256":summary["decisions_sha256"]},ensure_ascii=False))


if __name__ == "__main__":
    main()

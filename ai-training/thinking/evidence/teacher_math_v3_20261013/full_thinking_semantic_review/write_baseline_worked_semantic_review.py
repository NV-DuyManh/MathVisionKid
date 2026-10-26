"""Materialize the AI reviewer’s 173 individually read visible-output decisions.

The observations below were authored after reading all nine packet batches.
This file does not generate/score teacher targets or modify any frozen run file.
"""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKETS = ROOT / "baseline_worked_solution_review_packets.jsonl"

REASONS = r"""
0|3+10=13 viên bi, gộp đúng buổi sáng và buổi chiều; một bước đủ cho bài một phép cộng.
1|25+20=45 viên, đúng tổng cả ngày; extra key step vi phạm schema nhưng không sai toán.
2|10+29=39 đúng số; unit candies đổi viên bi thành kẹo nên sai đối tượng và đơn vị.
3|58-16=42 quả và vai trò số ban đầu/số ăn đúng; tự thêm từ táo không có trong đề, không đổi phép tính.
4|64-30=34 quả; kiểm tra ngược34+30=64 hợp lý.
5|47-40=7 quả, phép bớt và giải thích khớp câu hỏi còn lại.
6|29-9=20 quyển bổ sung; phân biệt đúng số đang có và số cần đạt.
7|23-1=22 quyển đúng; biểu thức kiểm tra1+22=23 đúng, câu thêm1 vào số hiện có viết chưa rõ.
8|33-11=22 quyển; giải thích đúng bổ sung bằng mục tiêu trừ số hiện có.
9|19-1=18 chiếc đúng so sánh An/Bình; chữ còn lại trong explanation dư, hint vẫn nêu hiệu đúng.
10|68-31=37 chiếc; giải thích số An trừ số Bình và kiểm tra cộng ngược đúng.
11|49-22=27 chiếc bút; chiếc bút là đơn vị có nghĩa tương đương chiếc.
12|Chữ số1 hàng chục biểu thị10;1×10 đúng giá trị nhưng dùng phép nhân cho lớp1 và extra step key cần sửa.
13|5 chục=50 đúng; hint nói giá trị hàng chục bằng10 lần chữ số hàng đơn vị là sai (51 có hàng đơn vị1).
14|6 chục=60 đúng, hint nhân chữ số ở hàng chục với10 đúng; ký hiệu nhân vượt phương pháp đếm chục lớp1.
15|10 phần×2 quyển/phần=20 quyển; đúng số nhóm và số vật mỗi nhóm.
16|1×5=5 quyển vở đúng; hint xác minh đơn vị quá chung nhưng lời giải một bước hợp lý.
17|8×5=40 quyển vở đúng; hai bước lặp cùng phép tính, extra step key không hợp schema.
18|40÷5=8 quyển mỗi bạn; chia đều đúng tổng và số người.
19|6÷2=3 quyển mỗi bạn, không bịa thêm dữ kiện.
20|18÷2=9 quyển mỗi bạn; phép chia đúng ý nghĩa chia đều.
21|12÷2=6 là thừa số chưa biết; unitless thể hiện không có đơn vị, cần Việt hóa nhãn.
22|50÷5=10; kiểm tra5×10=50 đúng và dữ kiện/thừa số không đảo.
23|2x=16 dẫn tới x=16/2=8; biến x là số chưa biết, phép biến đổi hợp lệ.
24|79+68=147 rồi147-6=141 quyển; trình tự thêm rồi lấy đi đúng.
25|50+22=72 rồi72-43=29 quyển; hai bước và đơn vị đều hợp lý.
26|8+28=36 rồi36-35=1 quyển; giữ đúng số thêm và số lấy đi.
27|8×4=32 rồi32-29=3 viên; dùng chữ viên/bộ thay viên/hộp là lỗi tên nhóm nhẹ.
28|6×8=48 rồi48-24=24 viên; bước riêng nhắc24 đã lấy không phải tính mới nhưng không đổi dữ kiện.
29|4×6=24 rồi24-17=7 viên; nhân số hộp và số mỗi hộp trước khi bớt.
30|710-350=360 đồng còn lại; lời giải đúng số mang theo/số đã dùng.
31|250-240=10 đồng; kiểm tra10+240=250 đúng.
32|450-370=80 đồng đúng; tự thêm mục đích mua đồ không có trong đề, không ảnh hưởng lượng tiền.
33|48-37=11 phút vì hai mốc cùng giờ; không nhầm số phút kết thúc là thời lượng.
34|58-4=54 phút, đúng lấy mốc kết thúc trừ mốc bắt đầu.
35|36-13=23 phút, vai trò hai mốc thời gian đúng.
36|Dư2 bánh đúng; lại ghi số hộp có thể đóng=57.2857 hộp và không nói lấy57 hộp đủ; sai nghĩa nhóm trọn và gần đúng không ký hiệu.
37|203÷7=29 hộp,203-7×29=0 bánh; bộ thay hộp là tên nhóm nhẹ, phép chia hết đúng.
38|Dư2 bánh đúng;22.5 hộp được gọi là số hộp có thể đóng, rồi dùng22 không giải thích lấy phần nguyên.
39|2×7=14 rồi94+14=108 đúng ưu tiên phép tính; unit là placeholder và extra step key vi phạm schema.
40|8×4=32 rồi68+32=100 đúng; đây là mẫu collision đã biết, chỉ review output, không đổi primarymetrics.
41|5×9=45 rồi24+45=69 đúng; unit là placeholder không phải đơn vị toán có nghĩa.
42|1m=100cm và173×100=17300cm đúng; biểu thức173m×100 là cách viết đổi đơn vị tắt.
43|58m×100cm/m=5800cm đúng hệ số và đơn vị; lời giải nêu1m=100cm.
44|39m×100cm/m=3900cm, đúng đổi cùng độ dài sang cm.
45|4×60=240 phút rồi56+240=296 phút; cộng đủ nghỉ và hoạt động.
46|12×60=720 rồi720+30=750 phút; chuyển giờ và cộng phút đúng.
47|1 giờ=60 phút,42+60=102 phút; kết quả đúng dù escape LaTeX trong field cần chú ý renderer.
48|263×1000=263000 gram; gram tương đương g, không nhầm hệ số100.
49|88×1000=88000g và nêu1kg=1000g đúng.
50|186×1000=186000g đúng khối lượng bảo toàn qua đổi đơn vị.
51|2×(80+84)=328cm đúng chu vi; không dùng diện tích dù đề gọi rộng84 lớn hơn dài80.
52|2×(19+61)=2×80=160cm; alternative biểu thức trung gian hợp lệ.
53|2×(48+86)=2×134=268cm; kiểm tra hai dài cộng hai rộng đúng.
54|4×156=624cm cho viền hình vuông; đúng bốn cạnh bằng nhau.
55|4×71=284cm đúng chu vi hình vuông.
56|4×63=252cm, đúng bốn cạnh, không nhầm cm².
57|60×46=2760cm² và tổng diện tích đúng; không hướng dẫn cách nhân hai số hai chữ số, quá phép nhân cơ bản lớp3 hiện hành.
58|19×61=1159cm² đúng; lớp3 cần phương pháp phân tách/phép nhân phù hợp thay chỉ nêu hai chữ số nhân nhau.
59|58×52=3016cm² đúng; không có bước thực hiện tích hai số hai chữ số cho lớp3.
60|209×209=43681cm² đúng tổng ô vuông; tích ba chữ số nhân ba chữ số không được hướng dẫn ở mức lớp3, extra step key.
61|85×85=7225cm² đúng; tính tích hai số hai chữ số không có cách hỗ trợ học sinh lớp3.
62|183×183=33489cm² đúng; không chỉ cách nhân phù hợp lớp3, extra step key.
63|12+73=85 rồi85+25=110 đồ vật; tổng ba nhóm và hai bước đúng.
64|72+7=79 rồi79+6=85 đồ vật; không giả định có ảnh/bảng chưa được cung cấp.
65|42+22=64 rồi64+18=82 đồ vật, đúng cộng ba nhóm.
66|Cộng hai phương trình để có2x=1410 rồix=705 đúng; hệ phương trình/khử ẩn quá cấp lớp4, thiếu unit trong steps không hợp schema.
67|2058+598=2656, chia2=1328 đúng số lớn; phương pháp hai phương trình vượt lớp4 dù tính toán hợp lệ.
68|597+171=768, chia2=384 đúng số lớn; khử ẩn qua hệ phương trình quá cấp lớp4.
69|Tìm số lớn288 rồi số bé457-288=169 đúng alternative; hệ hai ẩn không phù hợp hướng dẫn lớp4.
70|x+(x+305)=1277 dẫn tới2x=972,x=486 đúng; đại số hai ẩn/biến đổi chưa phù hợp lớp4, unit placeholder.
71|x+(x+627)=2157 dẫn tớix=765 đúng số bé; cách hệ phương trình quá cấp, thiếu hint schema.
72|4+17=21,21/3=7 đúng cộng cùng mẫu; câu rút gọn bằng chia tử cho mẫu chỉ phù hợp tình huống này, không dạy như quy tắc chung.
73|1=1/1,5=5/1 nên tổng6 đúng; số nguyên vẫn có thể biểu diễn như phân số, hint kiểm tra hơi dư.
74|Final29/14 đúng; result12 của biểu thức6/7=12/14 và result29 của17/14+12/14 bỏ mẫu14, gây sai các bước hiển thị.
75|3/2=12/8 và17/8-12/8=5/8 đúng; gọi cùng đơn vị thay cùng mẫu chưa chuẩn, hint chuyển thập phân vượt lớp4.
76|19/9-9/9=10/9 đúng; explanation chỉ dùng tiếng Anh không đáp ứng hướng dẫn tiếng Việt cho học sinh.
77|13/9=39/27 rồi trừ4/27=35/27 đúng; hint hỗn số vượt phần lớp4 hiện hành và extra step key.
78|17/7×2=34/7 đúng,34 và7 nguyên tố cùng nhau nên tối giản.
79|11/20×6/5=66/100 rồi chia cả tử mẫu2=33/50 đúng; phân số là loại số, không phải unit vật lý.
80|13/15×1/3=13/45 đúng tử/mẫu; tỉ số gắn vào unit là nhãn loại số dư.
81|9/2÷5/3=9/2×3/5=27/10 đúng nghịch đảo; hint thập phân không phù hợp lớp4.
82|3/5×7/3=21/15=7/5 đúng; rút gọn trước khi nhân là nhãn thời điểm không chính xác, gợi ý hỗn số thuộc lớp5.
83|19/7×2/17=38/119 đúng, không đảo số bị chia.
84|65+30+4=99 rồi99/3=33 đúng trung bình; đơn vị là placeholder vì đề không cho đại lượng.
85|26+54+82=162 rồi162/3=54 đúng; không nhầm tổng với trung bình.
86|52+16+25=93 rồi93/3=31 đúng; unit placeholder không có nghĩa lượng đo.
87|460×3/5=276 chiếc bút; hint chia5 rồi nhân3 đúng tìm phân số của số lượng.
88|850×5/17=250 chiếc bút, tính một phần17 rồi nhân5 đúng.
89|87×2/3=58 chiếc bút đúng; hint chia cho1 dư nhưng không đổi giá trị hay phép tính.
90|53×25=1325cm² đúng đáy nhân chiều cao tương ứng.
91|90×54=4860cm², đúng công thức bình hành và đơn vị diện tích.
92|24×5=120cm² đúng bình hành, không lấy cạnh xiên chưa được cho.
93|1+8=9 phần,324/9=36 mỗi phần,An nhận36 đồ vật; kiểm tra36+288=324 đúng.
94|5+12=17 phần,1292/17=76,An5×76=380 đồ vật; dữ kiện phần/người không đảo.
95|11+9=20,500/20=25,An11×25=275 đồ vật; đủ ba bước tỉ lệ.
96|Các bội dương1,2,3 cho số kế tiếp3; ví dụ1×3=3 đúng, số là nhãn loại không phải unit.
97|149×3=447 là bội dương kế sau149,298; kiểm tra298/149=2 đúng.
98|76×3=228 đúng bội kế tiếp, giữ quy luật bội liên tiếp.
99|57.25+29.86=87.11 đúng; không chỉ cách nhớ1 từ phần thập phân nên hướng dẫn thao tác còn thiếu.
100|31.23+80.54=111.77 đúng; hint căn vị trí và cộng phải sang trái có ích, unit thập phân là nhãn dư.
101|Final61.56 đúng; hai result đầu14.20 cho toàn biểu thức14.20+47.36 là sai, nhãn hàng phần mười/chục và số dư không chuẩn dù các cột cuối đúng.
102|25.93-10.46=15.47 đúng; một biểu thức chưa hướng dẫn mượn ở hàng phần trăm.
103|66.81-40.76=26.05 đúng; chưa hướng dẫn thao tác mượn trong trừ thập phân.
104|70.17-20.46=49.71 đúng số; đề số thuần túy nhưng gán đồng thành tiền là bịa đơn vị.
105|7.3×76.09=555.457 đúng; chỉ đưa tích rồi nói không cần tính thêm, chưa dạy đặt dấu phẩy hay nhân từng bước.
106|Final232.458 đúng; viết8.6×27.03=(8.6×10)×(27.03×100) thiếu chia1000, là đẳng thức sai dù bước cuối chia1000.
107|Không có closed visible answer, output null và truncated; không có đáp số hoặc lời giải để chấp nhận.
108|503.2÷17=29.6 đúng sau nhân cả hai số10; nói chuyển thành số nguyên sai với503.2 vẫn thập phân.
109|Final42 và1176÷28 đúng; result1176 được gắn với expression117.6÷2.8 thay vì phép nhân10, sai bước hiển thị.
110|Final82.9 và1160.6÷14 đúng; expression116.06×10÷1.4×10 thiếu ngoặc nên không biểu thị nhân cả số chia và số bị chia cùng10.
111|23%=0.23,7600×0.23=1748 đúng phần của tổng; không đảo tổng/phần.
112|61%=0.61,1300×0.61=793 đúng phần cần tìm.
113|54%=0.54,7600×0.54=4104 đúng chuyển phần trăm.
114|Final9800 đúng; bước công thức toàn bộ(6468/66)×100 lại gán result98, sai với expression rồi lặp lại bước đúng.
115|731/(43/100)=1700 đúng tổng, kiểm tra43%×1700=731 đúng.
116|6365/(67/100)=6365×100/67 rồi6365/0.67=9500 đúng; thiếu hint schema, không sai toán.
117|66/3300=0.02 rồi nhân100=2%, đúng phần/tổng và final unit%; intermediate unitless ở bước nhân100 nên đổi thành%.
118|Final59% đúng ý nghĩa; result0.590 gắn unit% là0.590% sai thay59%, thiếu bước nhân100; answer kèm% cần tránh renderer lặp%%.
119|1782/3300×100=54% đúng; kiểm tra54%×3300=1782 hợp lệ.
120|42×59/2=1239cm² đúng diện tích tam giác, dùng chiều cao tương ứng đáy.
121|52×67/2=1742cm² đúng công thức và đơn vị.
122|29×58/2=841cm² đúng, không quên chia2.
123|Final2451cm² và57/2=28.5 rồi nhân86 đúng; explanation cuối ghi(tổng đáy×cao)/2×cao là công thức nhân chiều cao hai lần sai.
124|Final415cm² đúng; full expression(36+47)×10/2 gán83cm sai, bước83×10=830 gọi tính tổng và gáncm thaycm².
125|3+90=93cm,93×14=1302cm² rồi /2=651cm² đúng ba bước.
126|3.14×106×106=35281.04cm² đúng theo pi cho; JSON chứa escape \pi không hợp lệ, không chấp nhận output kỹ thuật nhưng visible toán đúng.
127|201×201=40401 rồi×3.14=126859.14cm² đúng; escape LaTeX JSON lỗi, alternative bước A=... hợp lệ về toán.
128|139×139=19321 rồi×3.14=60667.94cm² đúng; escape \pi JSON lỗi nên cần sửa cấu trúc trả lời.
129|2×3.14×32=200.96cm đúng dây viền/chu vi, không dùngcm².
130|Final615.44cm đúng chu vi từ đường kính196; explanation gọi diện tích=3.14×đường kính là sai khái niệm.
131|2×3.14×246=1544.88cm đúng chu vi theo pi cho.
132|20×76×29=44080cm³ đúng thể tích, cả ba kích thước đúng vai trò.
133|55×22×1=1210cm³ đúng; hint phân tách55×20+55×2=1100+110=1210 hữu ích.
134|38×11×2=836cm³ đúng thể tích, không chỉ dùng diện tích đáy.
135|7×7=49cm²,49×6=294cm² đúng cả sáu mặt kín.
136|64×64=4096cm²,4096×6=24576cm² đúng diện tích toàn phần.
137|258²=66564 đúng nhưng6×66564=399384, model ghi400384 cả step vàfinal; sai số1000.
138|50km/h×30h=1500km đúng chuyển động đều.
139|60×9=540km đúng quãng đường; LaTeX escape cần renderer phù hợp nhưng không đổi ý nghĩa.
140|9×14.5=130.5km đúng; phân tách9×(14+0.5) hợp lý.
141|19km/1giờ=19km/h đúng vận tốc; bước đầu chỉ nhắc dữ kiện không bịa.
142|144/48=3km/h và kiểm tra3×48=144 đúng.
143|360/18=20km/h đúng vận tốc chuyển động đều.
144|756/54=14giờ,54×14=756 kiểm tra đúng.
145|594/33=18giờ đúng thời gian, không đảo vận tốc và quãng đường.
146|91/7=13giờ đúng thời gian không nghỉ.
147|100²=10000 và58.97×10000=589700cm² đúng ý định;10,000 kiểu thousands Western gây nhập nhằng với dấu phẩy thập phân Việt Nam.
148|12.61×10000=126100cm² đúng ý định; final126,100 theo kiểu Western nhưng Việt Nam đọc126.1, raw parser sai và chưa phù hợp giao diện học sinh.
149|90.68×10000=906800cm² đúng ý định; result906,800 và hệ số10,000 dùng grouping Western, final906800 không nhập nhằng.
150|1dm³=(10cm)³=1000cm³,55.68×1000=55680cm³ đúng đổi thể tích.
151|1.39×1000=1390cm³ và giải thích hệ số lập phương đúng.
152|76.34×1000=76340cm³ đúng, không dùng hệ số10 hay100.
153|266000/19=14000đồng/món,28×14000=392000đồng; hint nhân tỉ lệ28/19 tương đương nhưng không dễ tính hơn rút về đơn vị.
154|60000/15=4000đồng/món rồi23×4000=92000đồng; kiểm tra15×4000=60000 đúng.
155|21000/7=3000đồng/món rồi22×3000=66000đồng; hint nêu7món×22món=154món là đơn vị sai nhưng nói không cần làm vậy, không dùng làm lời giải.
156|5×132=660 người-ngày,660/11=60ngày; giữ năng suất và khối lượng đúng.
157|600/12=50ngày đúng; bước tích5người×120ngày gán600ngày thay600người-ngày, sai đơn vị trung gian.
158|11×91=1001 người-ngày rồi1001/7=143ngày đúng; đơn vị công việc ở bước đầu cần cụ thể người-ngày.
159|69+43=112vật và69/112 đúng cơ hội chọn đều; phân số là loại số, extra step key không hợp schema.
160|79+14=93vật rồi79/93 đúng tỷ lệ vật đỏ khi cơ hội các vật như nhau.
161|83+58=141vật rồi83/141 đúng, không dùng số vật xanh làm mẫu.
162|1/18 đúng tần suất quan sát1 lần trên18 lần thử, không tuyên bố xác suất chắc chắn lần sau.
163|2/23 đúng tần suất quan sát; số phân tử là dùng từ sai nhẹ so với tử số.
164|Final197/202 đúng rút gọn394/404; expression394÷2/404÷2 thiếu ngoặc, theo trái sang phải ra197/808 thay197/202.
165|605904+357733=963637 đúng; chỉ phép ngang và hint chung, chưa thực hiện đặt tính/các bước nhớ theo yêu cầu.
166|Các cột cộng cho963637 đúng, bảo toàn bài học sinh963638; lại nói thiếu1 đơn vị trong khi học sinh thừa1, còn dùng chữ hàng十万.
167|937335+143534=1080869 đúng ý định; answer1,080,869 grouping Western raw parser không đọc, chỉ phép ngang chưa đặt tính/nhớ.
168|225952+878997=1104949 đúng; explanation đặt hàng ngang không đáp ứng đặt tính theo cột/nhớ.
169|82070-48998=33072 đúng, kiểm tra cộng ngược đúng; không chỉ cách mượn qua các hàng0 của phép đặt tính.
170|Đáp33072 đúng và so sánh với33073 thật của học sinh; không bịa dấu mượn đã thấy, nhưng thiếu chỉ hàng đơn vị khác và cách trừ/mượn.
171|Final761463 đúng; cột5-9=6,3-9=4 thiếu phần mượn, hàng trăm nghìn8 thay7 và result364163 sai; hint cộng số bị trừ với kết quả cũng sai kiểm tra.
172|Final442305 đúng; initial result957147 không phải hiệu, explanation gọi sai hàng đơn vị/chục/nghìn, unit nhiều hơn vô nghĩa và không hướng dẫn mượn/ghép rõ.
"""

SEMANTIC_FAIL = {2, 13, 36, 38, 74, 101, 104, 106, 107, 108, 109, 110,
                 114, 118, 123, 124, 130, 137, 157, 164, 166, 171, 172}
SEVERE = SEMANTIC_FAIL - {108, 157}
GRADE_FAIL = {12, 13, 14, 36, 38, 57, 58, 59, 60, 61, 62, 66, 67, 68,
              69, 70, 71, 75, 76, 77, 81, 82, 107, 147, 148, 149, 166,
              167, 171, 172}
INVENTED = {2, 3, 32, 104}
FORMAT_FAIL = {1, 12, 17, 36, 39, 60, 62, 66, 71, 77, 107, 116, 126,
               127, 128, 159}
TASK_OR_LANGUAGE_FAIL = {76, 107, 165, 166, 167, 168, 169, 170}
USEFUL_FAIL = SEMANTIC_FAIL | {57, 58, 59, 60, 61, 62, 66, 67, 68, 69,
                              70, 71, 99, 102, 103, 105, 165, 167, 168,
                              169, 170}
OPERATION_NARRATIVE_FAIL = {13, 36, 38, 101, 108, 123, 124, 130, 166,
                           171, 172}
DATA_ROLE_FAIL = {2, 104, 166}
DISPLAY_METHOD_FAIL = {36, 38, 74, 101, 106, 107, 109, 110, 114, 118,
                      123, 124, 130, 137, 157, 164, 171, 172}
FINAL_NUMERIC_FAIL = {107, 137}
LOCALE_AMBIGUOUS = {147, 148, 149, 167}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def meaningful_unit(index, packet):
    # Human-readable meanings are reviewed separately from strict parser metrics.
    # Types/placeholder units are deliberately not counted as correct units.
    if index in {2, 104, 107}:
        return False
    if index in {12, 13, 14}:
        return True  # place-value quantities "10/50/60 đơn vị"
    expected = packet["reference"]["target"]["unit"]
    if expected:
        return True  # each corresponding final unit was read, including gram/km/h aliases
    parsed = packet["visible_output"].get("strict_parsed")
    if parsed is None:
        try:
            parsed = json.loads(packet["visible_output"]["text"])
        except (ValueError, TypeError):
            return False
    return parsed.get("unit") in {"", "unitless", "không có đơn vị"}

def main():
    raw = PACKETS.read_bytes()
    lines = raw.decode("utf-8").splitlines()
    packets = [json.loads(line) for line in lines]
    reasons = {}
    for line in REASONS.strip().splitlines():
        key, reason = line.split("|", 1)
        reasons[int(key)] = reason
    assert len(packets) == 173 and set(reasons) == set(range(173))
    assert len({p["sample_id"] for p in packets}) == 173
    reviewed_at = datetime.now(timezone.utc).isoformat()
    decisions = []
    for i, packet in enumerate(packets):
        unit_ok = meaningful_unit(i, packet)
        expected_unit = packet["reference"]["target"]["unit"]
        unit_issue = None
        if not unit_ok:
            unit_issue = (
                "WRONG_ENTITY_OR_INVENTED_PHYSICAL_UNIT" if i in {2, 104}
                else "NO_VISIBLE_OUTPUT" if i == 107
                else "PLACEHOLDER_OR_NUMBER_TYPE_USED_AS_UNIT"
            )
        d = {
            "model": "baseline", "sample_id": packet["sample_id"],
            "grade": packet["grade"], "topic": packet["topic"],
            "kind": "worked_solution", "packet_index": i,
            "review_kind": "AI_SEMANTIC_RESEARCH_REVIEW",
            "human_verified": False, "teacher_certified": False,
            "reviewed_at_utc": reviewed_at,
            "semantic_correct": i not in SEMANTIC_FAIL,
            "instruction_followed": i not in (FORMAT_FAIL | TASK_OR_LANGUAGE_FAIL),
            "grade_appropriate": i not in GRADE_FAIL,
            "invented_data_or_image": i in INVENTED,
            "severe_error": i in SEVERE,
            "reason": reasons[i],
            "explanation_operation_consistent": i not in (OPERATION_NARRATIVE_FAIL | {107}),
            "data_roles_correct": i not in (DATA_ROLE_FAIL | {107}),
            "displayed_method_valid": i not in DISPLAY_METHOD_FAIL,
            "step_by_step_guidance_useful": i not in USEFUL_FAIL,
            "final_numeric_correct": i not in FINAL_NUMERIC_FAIL,
            "meaningful_unit_correct": unit_ok,
            "unit_issue_kind": unit_issue,
            "locale_notation_ambiguous": i in LOCALE_AMBIGUOUS,
            "strict_format_issue": i in FORMAT_FAIL,
            "raw_numeric_observations_unchanged": packet["automatic_observations"]["direct_generated_numeric"],
            "source_packet_file_sha256": sha(raw),
            "source_packet_line_sha256": sha(lines[i].encode("utf-8")),
            "visible_output_sha256": sha(json.dumps(packet["visible_output"], ensure_ascii=False, sort_keys=True).encode("utf-8")),
            "expected_answer": packet["reference"]["target"]["answer"],
            "expected_unit": expected_unit,
        }
        decisions.append(d)
    out = ROOT / "baseline_worked_semantic_decisions.jsonl"
    out.write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in decisions), encoding="utf-8")
    fields = ["semantic_correct", "instruction_followed", "grade_appropriate",
              "invented_data_or_image", "severe_error", "explanation_operation_consistent",
              "data_roles_correct", "displayed_method_valid", "step_by_step_guidance_useful",
              "final_numeric_correct", "meaningful_unit_correct", "locale_notation_ambiguous"]
    def counts(rows):
        return {"samples": len(rows), **{k: sum(d[k] is True for d in rows) for k in fields}}
    summary = {
        "model": "baseline", "status": "COMPLETE_AI_RESEARCH_REVIEW_ALL_173_VISIBLE_WORKED_OUTPUTS",
        "review_kind": "AI_SEMANTIC_RESEARCH_REVIEW", "human_verified": False,
        "teacher_certified": False, "production_approved": False,
        "reviewed_at_utc": reviewed_at, "source_packet_path": str(PACKETS),
        "source_packet_file_sha256": sha(raw), "decisions_file_sha256": sha(out.read_bytes()),
        "overall": counts(decisions),
        "per_grade": {str(g): counts([d for d in decisions if d["grade"] == g]) for g in range(1, 6)},
        "raw_primary_metrics_unchanged": {
            "samples": len(packets),
            "numeric_correct": sum(p["automatic_observations"]["direct_generated_numeric"]["numeric_correct"] for p in packets),
            "answer_unit_correct": sum(p["automatic_observations"]["direct_generated_numeric"]["answer_unit_correct"] for p in packets),
            "truncated": sum(p["automatic_observations"]["strict_scores"]["truncated"] for p in packets),
        },
        "decision_definitions": {
            "semantic_correct": "Visible mathematical solution (including statements/hint and step expression-result consistency) and data meaning are correct; harmless wording/schema/placeholder-unit issues are reported separately.",
            "severe_error": "Wrong/absent answer, materially wrong entity, false displayed mathematical step, wrong stated formula/concept or wrong diagnosis of observed student work. Format-only, grade-level formality and minor wording alone are not severe.",
            "instruction_followed": "Attempts the requested worked solution with requested structured fields and Vietnamese guidance; schema/language failures and absent requested vertical calculation guidance fail separately from mathematical correctness.",
            "grade_appropriate": "AI pedagogical judgment of the displayed method for assigned grade; formal simultaneous equations and multiplication beyond basic assigned grade without support fail. This is not certification of the engineered grade assignment.",
            "final_numeric_correct": "Manual mathematical meaning of the visible final value; includes readable invalid-JSON final values and Western grouping interpretation where context proves intended integer. This is supplemental and NEVER replaces raw frozen parser metrics.",
            "meaningful_unit_correct": "Actual quantity unit/clear dimensionlessness; unit, số, phân số, tỉ số, tỷ lệ and other placeholders/types do not count as correct units. Units meaninglessly invented from pure numbers fail.",
            "step_by_step_guidance_useful": "Explains operation selection and enough steps at assigned level; mathematically false steps, overly formal methods or bare answers to vertical/decimal algorithm requests fail.",
        },
        "severe_examples": [{k: d[k] for k in ["sample_id", "packet_index", "grade", "topic", "reason"]} for d in decisions if d["severe_error"]],
        "all_semantic_failures": [{k: d[k] for k in ["sample_id", "packet_index", "grade", "topic", "severe_error", "reason"]} for d in decisions if not d["semantic_correct"]],
        "notes": [
            "All173 visible outputs and corresponding problems/reference facts were actually read in nine batches; no hidden thinking was used for the decisions.",
            "Mathematically valid alternative operation order, variables, prose and intermediate expressions are accepted for semantic meaning even when strict-reference scoring fails.",
            "The single previously known collision sample91d23b441cd60a087952fa5c remains in these primary173 reviews; supplemental exclusion belongs to the independent sensitivity report.",
            "Correct final numeric meaning does not imply correct teaching: false intermediate result fields/formulas are counted even if later final value recovers.",
            "No frozen source, data, evaluation protocol, primary metrics, selection decision, training, Colab runtime or held concept challenge was modified.",
        ],
    }
    report = ROOT / "baseline_worked_semantic_summary.json"
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decisions": str(out), "summary": str(report), "overall": summary["overall"], "raw": summary["raw_primary_metrics_unchanged"], "hash": summary["decisions_file_sha256"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()

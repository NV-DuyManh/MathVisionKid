import { getPrimaryChapters, type PrimaryGrade } from './primaryMathLessons';

type ExampleLevel = 'easy' | 'advanced';
type Script = readonly [firstQuestion: string, firstAnswer: string, firstDistractor: string, result: string, resultDistractor: string];

type ExampleStep = {
  title: string;
  question: string;
  correct: string;
  choices: readonly [string, string];
  hint: string;
  feedback: string;
};

export type PrimaryMathExample = {
  lessonId: string;
  level: ExampleLevel;
  problem: string;
  solution: string;
  steps: readonly [ExampleStep, ExampleStep];
};

// Keep the question and worked solution in the lesson catalog. These pairs add
// a first checkpoint and a result check specific to each existing example.
const EXAMPLE_SCRIPTS: Readonly<Partial<Record<string, readonly [Script, Script]>>> = {
  'grade-1-number-10-count': [
    ["Em đếm thế nào để không sót chấm?","Chỉ vào từng chấm một lần","Chỉ nhìn chấm đầu tiên","4","3"],
    ["Bỏ 1 nút đỏ thì còn mấy nút đỏ?","3 nút đỏ","4 nút đỏ","6 nút","7 nút"],
  ],
  'grade-1-number-10-compare': [
    ["Nhóm nào có nhiều hơn?","Nhóm 5","Nhóm 3","3 < 5","3 > 5"],
    ["Số nào phải đứng đầu?","2","7","5 đứng giữa","7 đứng giữa"],
  ],
  'grade-1-number-10-split': [
    ["Dùng phép gì để tìm số que còn lại?","Lấy 7 trừ 2","Lấy 7 cộng 2","5 que","9 que"],
    ["Trước khi chuyển, mỗi nhóm có mấy viên?","4 viên","2 viên","3 và 5 viên","4 và 5 viên"],
  ],
  'grade-1-operations-10-add': [
    ["Được thêm 3 viên thì dùng phép tính nào?","4 + 3","4 − 3","7 viên","6 viên"],
    ["Gộp bút đỏ và xanh được mấy bút?","5 bút","6 bút","9 bút","8 bút"],
  ],
  'grade-1-operations-10-subtract': [
    ["Ăn 4 quả thì dùng phép tính nào?","9 − 4","9 + 4","5 quả","6 quả"],
    ["Sau khi ăn 2 quả còn mấy quả?","8 quả","7 quả","5 quả","6 quả"],
  ],
  'grade-1-shapes-flat': [
    ["Viền mặt đồng xu có góc không?","Không có góc","Có bốn góc","Hình tròn","Hình vuông"],
    ["Hình A có mấy cạnh?","3 cạnh","4 cạnh","A tam giác, B vuông, C tròn","A vuông, B tam giác, C tròn"],
  ],
  'grade-1-shapes-solid': [
    ["Mặt của viên xúc xắc thường là hình gì?","Hình vuông","Hình tam giác","Khối lập phương","Khối cầu"],
    ["Khối lập phương có bao nhiêu mặt?","6 mặt","4 mặt","Hộp hình khối lập phương","Hộp giày"],
  ],
  'grade-1-number-100-place': [
    ["Năm bó chục có bao nhiêu que?","50 que","5 que","53 que","35 que"],
    ["Có thể bó thêm bao nhiêu chục từ 13 que?","1 chục","3 chục","53 que","43 que"],
  ],
  'grade-1-number-100-compare-100': [
    ["Cả 36 và 39 có mấy chục?","3 chục","6 chục","39 lớn hơn 36","36 lớn hơn 39"],
    ["Chữ số nào đứng hàng chục ở số lớn hơn?","7","2","27 < 72","27 > 72"],
  ],
  'grade-1-operations-100-tens': [
    ["40 và 20 là bao nhiêu chục?","4 chục và 2 chục","4 chục và 20 chục","60","42"],
    ["Cho đi 20 que thì còn bao nhiêu chục?","5 chục","9 chục","80 que","50 que"],
  ],
  'grade-1-operations-100-add-100': [
    ["Cộng hai chữ số hàng đơn vị được mấy?","8","7","38","37"],
    ["Lan có bao nhiêu nhãn sau lần nhận đầu?","37 nhãn","44 nhãn","58 nhãn","57 nhãn"],
  ],
  'grade-1-operations-100-subtract-100': [
    ["Trừ hàng đơn vị trước, 8 − 4 bằng mấy?","4","2","34","32"],
    ["Sau buổi sáng còn bao nhiêu nhãn?","66 nhãn","75 nhãn","52 nhãn","66 nhãn"],
  ],
  'grade-1-measure-length': [
    ["Đầu bút đặt ở đâu?","Vạch 0","Vạch 8","8 cm","9 cm"],
    ["Lấy hai số ở vạch nào để tính độ dài?","Lấy 9 trừ 2","Lấy 9 cộng 2","7 cm","11 cm"],
  ],
  'grade-1-measure-clock': [
    ["Kim phút chỉ 12 cho em biết điều gì?","Đồng hồ đang chỉ giờ đúng","Đã qua 12 phút","7 giờ đúng","12 giờ đúng"],
    ["Em đọc xong lúc mấy giờ?","9 giờ","10 giờ","Kim phút chỉ 12, kim giờ chỉ 10","Kim phút chỉ 10, kim giờ chỉ 12"],
  ],
  'grade-1-measure-calendar': [
    ["Ngày mai cách hôm nay mấy ngày?","1 ngày","2 ngày","Thứ Sáu","Thứ Bảy"],
    ["Sau thứ Sáu một ngày là ngày nào?","Thứ Bảy","Chủ nhật","Thứ Hai","Chủ nhật"],
  ],
  'grade-2-number-100-add': [
    ["6 đơn vị cộng 7 đơn vị được mấy?","13 đơn vị","12 đơn vị","73","63"],
    ["Sau khi nhận 28 quyển, lớp có bao nhiêu?","65 quyển","53 quyển","81 quyển","71 quyển"],
  ],
  'grade-2-number-100-subtract': [
    ["Khi đổi một chục, 2 đơn vị thành mấy đơn vị?","12 đơn vị","10 đơn vị","36","46"],
    ["Sau lần dùng đầu còn mấy tờ?","56 tờ","66 tờ","37 tờ","47 tờ"],
  ],
  'grade-2-number-100-more-less': [
    ["Bình ít hơn An thì em tính gì?","14 − 3","14 + 3","11 nhãn","17 nhãn"],
    ["Hòa có bao nhiêu nhãn?","37 nhãn","19 nhãn","65 nhãn","47 nhãn"],
  ],
  'grade-2-multiply-divide-multiply-two': [
    ["Mỗi đôi có mấy chiếc tất?","2 chiếc","4 chiếc","8 chiếc","6 chiếc"],
    ["Sau khi thêm 3 xe thì có mấy xe?","9 xe","6 xe","18 bánh","12 bánh"],
  ],
  'grade-2-multiply-divide-multiply-five': [
    ["Có mấy nhóm 5 ngón tay?","3 nhóm","5 nhóm","15 ngón","8 ngón"],
    ["Tổng số túi là bao nhiêu?","7 túi","5 túi","35 viên","20 viên"],
  ],
  'grade-2-multiply-divide-divide': [
    ["Phép chia nào tìm số bút trong mỗi hộp?","20 : 5","20 − 5","4 bút","15 bút"],
    ["Trước khi lấy đi, xếp được mấy nhóm?","6 nhóm","5 nhóm","4 nhóm","6 nhóm"],
  ],
  'grade-2-number-1000-place': [
    ["Hai số khác nhau ở hàng nào cần xét trước?","Hàng chục","Hàng đơn vị","480","408"],
    ["Số bé nhất phải đặt chữ số nào ở hàng trăm?","3","0","Lớn nhất 830, bé nhất 308","Lớn nhất 803, bé nhất 380"],
  ],
  'grade-2-number-1000-add-1000': [
    ["7 + 5 cho bao nhiêu đơn vị trước khi nhớ?","12","11","402","392"],
    ["Hai loại sách ban đầu có tất cả bao nhiêu?","661 quyển","651 quyển","790 quyển","780 quyển"],
  ],
  'grade-2-number-1000-subtract-1000': [
    ["Để trừ 4 − 3 ở hàng đơn vị, có cần đổi chục không?","Không cần","Cần đổi một chục","391","401"],
    ["Sau khi lấy 276 viên còn bao nhiêu?","524 viên","534 viên","366 viên","376 viên"],
  ],
  'grade-2-geometry-line': [
    ["Tính cả đường gấp khúc bằng cách nào?","Cộng độ dài hai đoạn","Trừ độ dài hai đoạn","12 cm","2 cm"],
    ["Hai đoạn đã biết dài tổng cộng bao nhiêu?","20 cm","19 cm","7 cm","8 cm"],
  ],
  'grade-2-geometry-shapes': [
    ["Khối cầu tròn đều và lăn được theo nhiều hướng. Vật nào phù hợp?","Vật tròn đều","Vật có hai đáy phẳng","Quả bóng","Lon sữa"],
    ["Có mấy lon dạng khối trụ?","3 lon","2 lon","5 vật","6 vật"],
  ],
  'grade-2-measure-length': [
    ["Một đề-xi-mét bằng bao nhiêu xăng-ti-mét?","10 cm","100 cm","30 cm","300 cm"],
    ["Một ki-lô-mét đổi được bao nhiêu mét?","1.000 m","100 m","1.250 m","350 m"],
  ],
  'grade-2-measure-mass-volume': [
    ["Rót ra làm lượng nước tăng hay giảm?","Giảm","Tăng","3 lít","7 lít"],
    ["Hai bình nhận tất cả bao nhiêu lít?","10 lít","7 lít","8 lít","13 lít"],
  ],
  'grade-2-measure-time-money': [
    ["Em lấy số tiền nào trừ đi giá vở?","10.000 đồng","7.000 đồng","3.000 đồng","7.000 đồng"],
    ["Phút rời hiệu sách là phút thứ mấy của giờ đó?","45 phút","30 phút","8 giờ 45 phút và 6.000 đồng","8 giờ 45 phút và 4.000 đồng"],
  ],
  'grade-2-data-pictures': [
    ["Ba hình nghĩa là có mấy nhóm 2 quả?","3 nhóm","2 nhóm","6 quả","5 quả"],
    ["Nhóm A và nhóm B có bao nhiêu bạn?","A có 10, B có 6","A có 5, B có 3","Tổng 16 bạn, A hơn 4 bạn","Tổng 8 bạn, A hơn 2 bạn"],
  ],
  'grade-2-data-chance': [
    ["Trong hộp có thẻ màu xanh không?","Không có","Có","Không thể","Chắc chắn"],
    ["Rút một viên, màu nào không có trong túi?","Màu đỏ","Màu vàng","Đỏ không thể, vàng có thể, xanh hoặc vàng chắc chắn","Đỏ có thể, vàng chắc chắn, xanh hoặc vàng không thể"],
  ],
  'grade-3-review-number': [
    ["Phép tính nào tìm số hạng còn thiếu?","300 − 125","300 + 125","175","185"],
    ["Sau khi phát sách kho còn bao nhiêu?","447 quyển","457 quyển","693 quyển","683 quyển"],
  ],
  'grade-3-review-tables': [
    ["Muốn gộp 6 nhóm có 4 quả, em dùng phép tính nào?","4 × 6","4 + 6","24 quả","10 quả"],
    ["Trước khi xếp lại, có tất cả bao nhiêu quả?","20 quả","9 quả","10 nhóm","8 nhóm"],
  ],
  'grade-3-tables-multiply': [
    ["So với 7 × 5, tích 7 × 6 có thêm bao nhiêu?","7","6","42","41"],
    ["Sáu hộp 8 bút có tất cả bao nhiêu bút?","48 bút","42 bút","90 bút","84 bút"],
  ],
  'grade-3-tables-divide': [
    ["Phép nhân nào giúp tìm thương?","8 × □ = 56","56 × □ = 8","7","8"],
    ["Chia xong, mỗi bạn nhận bao nhiêu nhãn?","8 nhãn","9 nhãn","5 nhãn","6 nhãn"],
  ],
  'grade-3-tables-part': [
    ["Muốn tìm một phần tư, chia 20 thành mấy phần bằng nhau?","4 phần","2 phần","5 viên","4 viên"],
    ["An cho bạn bao nhiêu viên bi ở lần đầu?","9 viên","8 viên","22 viên","27 viên"],
  ],
  'grade-3-shapes-points': [
    ["So sánh độ dài AM và MB.","Hai đoạn dài bằng nhau","Đoạn AM dài hơn","M là trung điểm của AB","M là đầu mút của AB"],
    ["M ở giữa và chia đôi AB. AM dài bao nhiêu?","9 cm","18 cm","5 cm","13 cm"],
  ],
  'grade-3-shapes-circle': [
    ["Một đường kính dài bằng mấy bán kính?","Hai bán kính","Một bán kính","8 cm","4 cm"],
    ["Đường kính là 14 cm. Mỗi bán kính dài bao nhiêu?","7 cm","14 cm","14 cm","21 cm"],
  ],
  'grade-3-shapes-angles': [
    ["Bốn cạnh của hình có đặc điểm gì?","Bằng nhau","Có hai cạnh dài hơn","Hình vuông","Hình tam giác"],
    ["Cạnh chung của hai tam giác nằm ở đâu?","Bên trong hình ghép","Trên đường bao ngoài","Hình tứ giác","Hình tam giác"],
  ],
  'grade-3-shapes-solids': [
    ["Các mặt của hộp đều là hình gì?","Hình vuông","Hình tròn","Khối lập phương","Khối trụ"],
    ["Khi ghép, bao nhiêu mặt vuông nằm bên trong?","2 mặt","1 mặt","10 mặt","11 mặt"],
  ],
  'grade-3-operations-100-multiply': [
    ["Phép tính nào diễn tả gấp 12 lên 3 lần?","12 × 3","12 + 3","36 bông","15 bông"],
    ["Ba khay có tất cả bao nhiêu bánh?","54 bánh","51 bánh","61 bánh","58 bánh"],
  ],
  'grade-3-operations-100-divide': [
    ["Bảy túi đầy chứa được mấy chiếc?","28 chiếc","29 chiếc","7 túi đầy, dư 1 chiếc","6 túi đầy, dư 5 chiếc"],
    ["Sau khi xếp 8 hàng đủ, còn mấy bạn?","3 bạn","5 bạn","8 hàng đủ, hàng cuối thiếu 5 bạn","8 hàng đủ, hàng cuối thiếu 3 bạn"],
  ],
  'grade-3-operations-100-two-steps': [
    ["Minh có bao nhiêu hạt?","13 hạt","5 hạt","22 hạt","18 hạt"],
    ["Trước khi tặng, có tất cả bao nhiêu bút?","40 bút","35 bút","27 bút","22 bút"],
  ],
  'grade-3-measure-length': [
    ["Một xăng-ti-mét bằng mấy mi-li-mét?","10 mm","100 mm","60 mm","600 mm"],
    ["Đoạn 25 cm đổi được bao nhiêu mi-li-mét?","250 mm","25 mm","715 mm","940 mm"],
  ],
  'grade-3-measure-units': [
    ["Hai chai có cùng 250 ml. Có thể dùng phép tính nào?","250 × 2","250 + 2","500 ml","252 ml"],
    ["Đã rót vào bốn cốc bao nhiêu nước?","600 ml","450 ml","400 ml","550 ml"],
  ],
  'grade-3-operations-1000-multiply': [
    ["Nhân từ phải sang trái. Hàng đơn vị được mấy?","8","4","448","428"],
    ["Ba thùng có bao nhiêu tờ giấy?","624 tờ","604 tờ","700 tờ","680 tờ"],
  ],
  'grade-3-operations-1000-divide': [
    ["Chia lần lượt từ trái sang phải. Hàng trăm của thương là mấy?","1","3","132","123"],
    ["Mỗi lớp nhận bao nhiêu bút khi chia đều?","141 bút","144 bút","104 bút","107 bút"],
  ],
  'grade-3-operations-1000-expression': [
    ["Em tính phép nào trước?","4 × 5","10 + 4","30","70"],
    ["Sau khi tính trong ngoặc, thương đầu tiên bằng mấy?","8","12","29","33"],
  ],
  'grade-3-operations-1000-times': [
    ["Muốn biết 24 gấp 6 mấy lần, em dùng phép gì?","24 : 6","24 − 6","4 lần","18 lần"],
    ["Sau khi thêm 12, có bao nhiêu bút đỏ?","24 bút","12 bút","3 lần","6 lần"],
  ],
  'grade-3-review-one-mixed': [
    ["Đổi 2 m sang xăng-ti-mét được bao nhiêu?","200 cm","20 cm","230 cm","50 cm"],
    ["Mỗi đoạn dây dài bao nhiêu xăng-ti-mét?","125 cm","105 cm","500 cm","420 cm"],
  ],
  'grade-3-number-10000-place': [
    ["Hàng đầu tiên khác nhau khi so từ trái sang phải là hàng nào?","Hàng chục","Hàng đơn vị","4.502 < 4.520","4.520 < 4.502"],
    ["Chữ số hàng nghìn nhỏ nhất thỏa đề là mấy?","5","2","5.028","5.082"],
  ],
  'grade-3-number-10000-round': [
    ["Hàng chục của 3.476 là số mấy?","7","4","3.500","3.400"],
    ["Làm tròn 4.965 đến hàng trăm. Kết quả là bao nhiêu?","5.000","4.900","5.000 và XIV","5.000 và XVI"],
  ],
  'grade-3-area-perimeter': [
    ["Em tính chu vi tam giác bằng cách nào?","Cộng cả ba cạnh","Chỉ cộng hai cạnh","15 cm","9 cm"],
    ["Chu vi hình chữ nhật bằng bao nhiêu?","38 cm","19 cm","Hình chữ nhật hơn 2 cm","Hình vuông hơn 2 cm"],
  ],
  'grade-3-area-square-unit': [
    ["Mỗi ô vuông cạnh 1 cm có diện tích bao nhiêu?","1 cm²","4 cm²","9 cm²","36 cm²"],
    ["Trước khi bỏ 3 ô, hình phủ bao nhiêu ô?","20 ô","9 ô","17 cm²","23 cm²"],
  ],
  'grade-3-area-rectangle': [
    ["Em tính diện tích bằng phép nào?","6 × 3","(6 + 3) × 2","18 cm²","18 cm"],
    ["Phần hình vuông cắt đi có diện tích bao nhiêu?","9 cm²","12 cm²","111 cm²","108 cm²"],
  ],
  'grade-3-area-square': [
    ["Em tính diện tích từ độ dài cạnh bằng phép nào?","4 × 4","4 + 4","16 cm²","8 cm²"],
    ["Hai hình vuông có diện tích lần lượt là bao nhiêu?","36 cm² và 16 cm²","24 cm² và 16 cm²","Tổng 52 cm², hiệu 20 cm²","Tổng 40 cm², hiệu 8 cm²"],
  ],
  'grade-3-area-apply': [
    ["Khi phủ cỏ kín vườn, cần đo phần nào?","Phần mặt vườn","Đường bao quanh vườn","Diện tích 24 m²","Chu vi 22 m"],
    ["Trước khi chừa cổng, chu vi vườn là bao nhiêu?","32 m","16 m","Rào 30 m, cỏ 60 m²","Rào 32 m, cỏ 60 m²"],
  ],
  'grade-3-operations-10000-add-subtract': [
    ["Ở hàng đơn vị, 6 + 9 cho kết quả nào?","Viết 5, nhớ 1 chục","Viết 5, không nhớ","4.525","4.515"],
    ["Sau khi nhập, kho có bao nhiêu quyển?","8.115 quyển","8.015 quyển","5.467 quyển","5.367 quyển"],
  ],
  'grade-3-operations-10000-multiply-divide': [
    ["Bắt đầu chia từ trái, 8 nghìn chia 4 bằng mấy nghìn?","2 nghìn","4 nghìn","2.121","2.112"],
    ["Tổng ba kiện có bao nhiêu tờ giấy?","3.780 tờ","3.680 tờ","756 tờ","736 tờ"],
  ],
  'grade-3-number-100000-place': [
    ["Chữ số 5 đứng ở hàng nào?","Hàng chục nghìn","Hàng nghìn","50.000","5.000"],
    ["Để được số bé nhất, đặt chữ số nào ở đầu?","2","0","Lớn nhất 86.420, bé nhất 20.468","Lớn nhất 86.420, bé nhất 24.068"],
  ],
  'grade-3-number-100000-round': [
    ["Để làm tròn đến hàng nghìn, kiểm tra chữ số nào?","7 ở hàng trăm","8 ở hàng chục","27.000","26.000"],
    ["Làm tròn đến hàng nghìn trước. Em được kết quả nào?","95.000","96.000","Kết quả là 95.000 và 100.000, khác nhau","Cả hai đều bằng 95.000"],
  ],
  'grade-3-add-subtract-100000-add': [
    ["Ở hàng đơn vị, 5 + 8 cho kết quả nào?","Viết 3, nhớ 1 chục","Viết 3, không nhớ","47.003","46.993"],
    ["Hai trường ban đầu có tất cả bao nhiêu sách?","53.611 quyển","53.511 quyển","67.120 quyển","67.020 quyển"],
  ],
  'grade-3-add-subtract-100000-subtract': [
    ["Hàng đơn vị có cần đổi một chục không?","Có, vì 0 bé hơn 4","Không, vì 4 bé hơn 10","33.406","33.416"],
    ["Tổng số gạch giao trong hai buổi là bao nhiêu?","42.843 viên","42.743 viên","47.157 viên","47.257 viên"],
  ],
  'grade-3-calendar-money-clock': [
    ["Hai mốc đều nằm trong cùng giờ. Em tính thế nào?","35 − 10","35 + 10","25 phút","45 phút"],
    ["Buổi học kết thúc lúc mấy giờ?","9 giờ 25 phút","9 giờ 15 phút","9 giờ 35 phút","9 giờ 45 phút"],
  ],
  'grade-3-calendar-money-money': [
    ["Em tính tiền thừa thế nào?","20.000 − 11.000","20.000 + 11.000","9.000 đồng","11.000 đồng"],
    ["Tổng tiền vở và bút là bao nhiêu?","30.000 đồng","24.000 đồng","20.000 đồng","26.000 đồng"],
  ],
  'grade-3-multiply-divide-100000-multiply': [
    ["Ở hàng chục, chữ số nào được nhân với 3?","0","5","63.915","63.905"],
    ["Số tờ in trong 4 ngày là bao nhiêu?","49.612 tờ","49.212 tờ","50.862 tờ","50.462 tờ"],
  ],
  'grade-3-multiply-divide-100000-divide': [
    ["64 nghìn chia 8 được mấy nghìn?","8 nghìn","6 nghìn","8.001","8.010"],
    ["Mỗi cửa hàng được chia bao nhiêu nhãn?","12.006 nhãn","12.060 nhãn","9.506 nhãn","9.560 nhãn"],
  ],
  'grade-3-data-table': [
    ["Để tìm phần nhiều hơn, em dùng phép nào?","11 − 8","11 + 8","3 trang","19 trang"],
    ["Tổ nào đọc nhiều nhất và tổ nào đọc ít nhất?","C nhiều nhất, B ít nhất","A nhiều nhất, C ít nhất","Tổng 36 sách, chênh 6 sách","Tổng 36 sách, chênh 3 sách"],
  ],
  'grade-3-data-chance': [
    ["Có màu nào ngoài đỏ và xanh trong hộp theo đề?","Không","Có màu vàng","Đỏ hoặc xanh","Chỉ đỏ"],
    ["Túi có đủ hai viên xanh để lấy một cặp xanh không?","Không, chỉ có một viên xanh","Có, lấy lại viên đã rút","Chỉ có thể lấy hai viên đỏ","Chỉ có thể lấy hai viên xanh"],
  ],
  'grade-3-review-year-mixed': [
    ["Em dùng phép gì để gộp năm ngày có cùng số trang?","12 × 5","12 + 5","60 trang","17 trang"],
    ["Sau khi mượn, mỗi giá còn bao nhiêu quyển?","17 quyển","24 quyển","68 quyển","96 quyển"],
  ],
  'grade-4-numbers-place': [
    ["Chữ số 7 đứng ở hàng nào?","Hàng triệu","Hàng trăm nghìn","7.000.000","700.000"],
    ["Chữ số nhỏ nhất có thể đứng đầu là gì?","1","0","1.023.456, lớp nghìn là 023","1.023.456, lớp nghìn là 234"],
  ],
  'grade-4-numbers-round': [
    ["Để làm tròn đến hàng nghìn, xét chữ số nào?","6 ở hàng trăm","8 ở hàng chục","38.000","37.000"],
    ["Số nhỏ nhất làm tròn đến 36.000 là số nào?","35.500","35.000","35.501","35.499"],
  ],
  'grade-4-operations-add': [
    ["Cặp nào cộng lại thành số tròn trăm?","125 và 75","125 và 43","243","233"],
    ["Nhóm 28.754 với 1.246 được bao nhiêu?","30.000","29.000","43.092","42.092"],
  ],
  'grade-4-operations-subtract': [
    ["Ở hàng đơn vị, làm sao trừ 0 cho 5?","Đổi 1 chục thành 10 đơn vị","Lấy 5 − 0 ngay","44.065","44.075"],
    ["Tổng hai lần xuất là bao nhiêu thùng?","106.503 thùng","106.403 thùng","98.497 thùng","98.597 thùng"],
  ],
  'grade-4-operations-multiply': [
    ["Tách 24 sao cho thuận tiện.","20 + 4","2 + 4","3.168","792"],
    ["Sau 36 ngày đóng gói được bao nhiêu hộp?","8.928 hộp","8.828 hộp","8.536 hộp","8.436 hộp"],
  ],
  'grade-4-operations-divide': [
    ["42 chia 21 được chữ số nào trước?","2","1","20","2"],
    ["Sau khi chất đầy 65 hộp, còn mấy thẻ?","15 thẻ","24 thẻ","66 hộp","65 hộp"],
  ],
  'grade-4-operations-expression': [
    ["Thay a và b bằng số nào để được biểu thức đúng?","5 + 3 × 4","4 + 3 × 5","17","19"],
    ["Sau khi thay số, phần trong ngoặc bằng bao nhiêu?","12","4","31","36"],
  ],
  'grade-4-problems-average': [
    ["Tổng số trang ba ngày là bao nhiêu?","30 trang","20 trang","10 trang","30 trang"],
    ["Cả ba ngày bán được bao nhiêu quyển?","90 quyển","60 quyển","34 quyển","44 quyển"],
  ],
  'grade-4-problems-sum-difference': [
    ["Lấy tổng trừ hiệu được hai lần số nào?","Số bé","Số lớn","26 và 38","24 và 40"],
    ["Chuyển 6 quyển làm hiệu ban đầu giảm bao nhiêu?","12 quyển","6 quyển","31 và 43 quyển","34 và 40 quyển"],
  ],
  'grade-4-problems-one-unit': [
    ["Mỗi túi có bao nhiêu quả?","7 quả","6 quả","42 quả","36 quả"],
    ["Chín quyển vở giá bao nhiêu?","81.000 đồng","90.000 đồng","19.000 đồng","9.000 đồng"],
  ],
  'grade-4-shapes-angle': [
    ["120° nằm giữa hai mốc nào?","90° và 180°","0° và 90°","Góc tù","Góc nhọn"],
    ["Góc còn lại có số đo bao nhiêu?","115°","125°","Góc 115°, góc tù","Góc 115°, góc nhọn"],
  ],
  'grade-4-shapes-lines': [
    ["Hai cạnh kề tạo góc bao nhiêu độ?","90°","180°","Vuông góc","Song song"],
    ["Cạnh nào nằm đối diện AB?","CD","BC","CD song song AB và vuông góc AD","CD vuông góc AB và song song AD"],
  ],
  'grade-4-shapes-parallelogram': [
    ["Chọn phép tính diện tích phù hợp.","9 × 4","(9 + 4) × 2","36 cm²","26 cm²"],
    ["Diện tích hình thoi bằng bao nhiêu?","60 cm²","120 cm²","Hình bình hành hơn 10 cm²","Hình thoi hơn 50 cm²"],
  ],
  'grade-4-shapes-perimeter-area': [
    ["Tích 8 × 5 cho biết đại lượng nào?","Diện tích","Chu vi","Chu vi 26 cm, diện tích 40 cm²","Chu vi 13 cm, diện tích 40 cm²"],
    ["Trước khi trừ phần cổng, chu vi sân là bao nhiêu?","60 m","30 m","Rào 57 m, lát 108 m²","Rào 60 m, lát 216 m²"],
  ],
  'grade-4-measure-mass': [
    ["Một tạ bằng bao nhiêu ki-lô-gam?","100 kg","10 kg","305 kg","35 kg"],
    ["Dỡ 35 yến nghĩa là dỡ bao nhiêu ki-lô-gam?","350 kg","35 kg","850 kg","1.165 kg"],
  ],
  'grade-4-measure-time-area': [
    ["Một đề-xi-mét vuông bằng bao nhiêu xăng-ti-mét vuông?","100 cm²","10 cm²","300 cm²","30 cm²"],
    ["Trong 30 giây máy thêu được bao nhiêu?","1 dm²","2 dm²","700 cm²","800 cm²"],
  ],
  'grade-4-fractions-compare': [
    ["Chia cả tử và mẫu cho số nào lớn hơn 1?","2","3","3/4","4/6"],
    ["Chọn mẫu số chung phù hợp cho cả ba phân số.","12","6","8/12 < 9/12 < 10/12, tức 2/3 < 3/4 < 5/6","9/12 < 8/12 < 10/12, tức 3/4 < 2/3 < 5/6"],
  ],
  'grade-4-fractions-add-subtract': [
    ["Đổi 1/2 thành phân số có mẫu 4.","2/4","1/4","3/4","2/4"],
    ["Dùng mẫu số chung 12, ba tử lần lượt là gì?","10, 3 và 4","5, 1 và 1","11/12 lít","17/12 lít"],
  ],
  'grade-4-fractions-multiply-divide': [
    ["Phân số nghịch đảo của 4/5 là gì?","5/4","4/5","5/6","8/15"],
    ["Chia sợi dây thành các phần 1/8 m thì được mấy đoạn?","6 đoạn","3 đoạn","4 đoạn","2 đoạn"],
  ],
  'grade-4-fractions-part': [
    ["Một phần tư của 28 là bao nhiêu?","7","4","21","14"],
    ["Vườn có bao nhiêu cây cam và cây xoài?","36 cam và 21 xoài","12 cam và 21 xoài","27 cây","51 cây"],
  ],
  'grade-4-data-columns': [
    ["Cột nào biểu thị nhiều hơn?","Cột 12 quyển","Cột 8 quyển","4 quyển","20 quyển"],
    ["Cột cao nhất và thấp nhất biểu thị bao nhiêu?","30 và 15 quyển","6 và 3 quyển","Tổng 65, chênh 15 quyển","Tổng 13, chênh 3 quyển"],
  ],
  'grade-4-data-chance': [
    ["Muốn tìm số mặt sấp, dùng phép tính nào?","10 − 6","10 + 6","4 lần","6 lần"],
    ["Có bao nhiêu lượt gieo trong hai đợt?","30 lượt","18 lượt","Có mặt 6: 7 lượt, các mặt khác: 23 lượt","Có mặt 6: 7 lượt, các mặt khác: 11 lượt"],
  ],
  'grade-5-review-natural': [
    ["Hai tích cùng có thừa số nào để đưa ra ngoài ngoặc?","48","13","960","864"],
    ["Gộp hai tích có chung thừa số 75 được biểu thức nào?","75 × (28 + 12)","75 × (28 − 12)","2.920","3.080"],
  ],
  'grade-5-review-fraction': [
    ["Đổi hai phần nguyên thành các phần ba, rồi cộng một phần ba. Tử số là bao nhiêu?","7","6","7/3","6/3"],
    ["Đổi cả hai hỗn số thành phân số có mẫu 8. Em được cặp nào?","22/8 và 13/8","19/8 và 13/8","1 và 1/8","1 và 3/8"],
  ],
  'grade-5-decimals-read': [
    ["Viết 3,5 với hai chữ số sau dấu phẩy bằng cách nào?","3,50","3,05","3,5 > 3,48","3,5 < 3,48"],
    ["Sau dấu phẩy có thể xếp 3 và 7 theo các thứ tự nào?","37 hoặc 73","33 hoặc 77","0,37 < 0,73","0,37 > 0,73"],
  ],
  'grade-5-decimals-round': [
    ["Để làm tròn đến phần trăm, cần nhìn chữ số nào?","6 ở hàng phần nghìn","7 ở hàng phần trăm","8,28","8,27"],
    ["Khi làm tròn đến phần trăm, 5 ở hàng phần nghìn yêu cầu điều gì?","Tăng hàng phần trăm lên một đơn vị","Giữ hàng phần trăm","10,00 và 10,0","9,99 và 9,9"],
  ],
  'grade-5-decimals-add': [
    ["Để hai số có cùng số chữ số thập phân, viết 4,8 thành gì?","4,80","4,08","7,15","6,43"],
    ["Tổng quãng đường buổi sáng và buổi chiều là bao nhiêu?","6,350 km","6,035 km","7,435 km","7,085 km"],
  ],
  'grade-5-decimals-subtract': [
    ["Khi viết đủ hai chữ số sau dấu phẩy, 8,2 viết thành gì?","8,20","8,02","4,73","5,27"],
    ["Cắt 8,75 m lần đầu thì còn bao nhiêu?","16,650 m","17,650 m","12,965 m","13,965 m"],
  ],
  'grade-5-decimals-multiply': [
    ["Hai thừa số có tổng cộng mấy chữ số sau dấu phẩy?","2 chữ số","1 chữ số","0,36","3,6"],
    ["Bốn tấm vải cần tổng cộng bao nhiêu mét?","5 m","4,25 m","192.500 đồng","154.000 đồng"],
  ],
  'grade-5-decimals-divide': [
    ["Nhân cả số bị chia và số chia với 10 được phép chia nào?","48 : 6","4,8 : 6","8","0,8"],
    ["Nếu dùng hết nước thì rót đầy được tất cả mấy chai?","28 chai","16 chai","12 chai nữa","28 chai nữa"],
  ],
  'grade-5-ratios-ratio': [
    ["Một xăng-ti-mét trên bản đồ ứng với bao nhiêu xăng-ti-mét thực tế?","1.000 cm","100 cm","40 m","400 m"],
    ["Trên bản đồ, hai đoạn dài tổng cộng bao nhiêu?","6 cm","1,2 cm","150 m","15 m"],
  ],
  'grade-5-ratios-percent': [
    ["Phép chia nào cho biết phần lớp đi bộ?","12 : 30","30 : 12","40%","12%"],
    ["Có bao nhiêu bạn chọn cầu lông?","9 bạn","18 bạn","22,5%","45%"],
  ],
  'grade-5-ratios-percentage-of': [
    ["15% viết thành số thập phân nào?","0,15","1,5","30","300"],
    ["Thư viện có bao nhiêu truyện?","126 quyển","63 quyển","63 truyện khoa học","126 truyện khoa học"],
  ],
  'grade-5-ratios-application': [
    ["Sách được giảm bao nhiêu tiền?","8.000 đồng","10.000 đồng","72.000 đồng","88.000 đồng"],
    ["Sau khi giảm 20%, giá còn bao nhiêu?","160.000 đồng","180.000 đồng","176.000 đồng","180.000 đồng"],
  ],
  'grade-5-plane-geometry-area-unit': [
    ["Một héc-ta bằng bao nhiêu mét vuông?","10.000 m²","1.000 m²","20.000 m²","2.000 m²"],
    ["Đổi diện tích cả khu đất sang mét vuông.","24.000 m²","2.400 m²","20.500 m²","27.500 m²"],
  ],
  'grade-5-plane-geometry-triangle': [
    ["Diện tích tam giác được tính bằng phép nào?","Lấy tích đáy và chiều cao chia 2","Lấy đáy nhân chiều cao","20 cm²","40 cm²"],
    ["Đổi chiều cao của tấm biển sang mét.","0,75 m","7,5 m","0,45 m²","0,90 m²"],
  ],
  'grade-5-plane-geometry-trapezoid': [
    ["Tổng độ dài hai đáy là bao nhiêu?","16 cm","4 cm","32 cm²","64 cm²"],
    ["Đáy nhỏ bằng 3/5 của 20 m. Đáy nhỏ dài bao nhiêu?","12 m","8 m","120 m²","240 m²"],
  ],
  'grade-5-plane-geometry-circle-perimeter': [
    ["Đường kính ứng với bán kính 5 cm là bao nhiêu?","10 cm","5 cm","31,4 cm","15,7 cm"],
    ["Bánh xe lăn một vòng đi được bao xa?","2,198 m","4,396 m","26,376 m","52,752 m"],
  ],
  'grade-5-plane-geometry-circle-area': [
    ["Để tính diện tích, nhân 3,14 với số nào?","Tích 3 × 3","Tích 3 × 2","28,26 cm²","18,84 cm²"],
    ["Hiệu hai bình phương bán kính là bao nhiêu?","32 cm²","16 cm²","100,48 cm²","50,24 cm²"],
  ],
  'grade-5-solids-surface': [
    ["Khối lập phương có bao nhiêu mặt vuông?","6 mặt","4 mặt","24 cm²","16 cm²"],
    ["Diện tích đáy hộp là bao nhiêu?","40 cm²","24 cm²","118 cm²","158 cm²"],
  ],
  'grade-5-solids-volume-units': [
    ["Mỗi cạnh 1 dm bằng 10 cm. Có mấy khối 1 cm³ trong một lớp đáy?","100 khối","10 khối","1.000 cm³","100 cm³"],
    ["Đổi 1,25 m³ sang đề-xi-mét khối.","1.250 dm³","125 dm³","910 dm³","1.590 dm³"],
  ],
  'grade-5-solids-box-volume': [
    ["Diện tích đáy hộp bằng bao nhiêu?","28 cm²","21 cm²","84 cm³","63 cm³"],
    ["Bể chứa đầy có thể tích bao nhiêu?","270 dm³","27 dm³","180 dm³","90 dm³"],
  ],
  'grade-5-solids-cube-volume': [
    ["Em cần nhân cạnh 5 cm với chính nó mấy thừa số 5?","Ba thừa số 5","Hai thừa số 5","125 cm³","25 cm³"],
    ["Khối lập phương nhỏ cắt đi có thể tích bao nhiêu?","8 cm³","4 cm³","208 cm³","212 cm³"],
  ],
  'grade-5-motion-time-units': [
    ["30 phút bằng phần nào của một giờ?","Một nửa giờ","Ba phần mười giờ","1,5 giờ","1,3 giờ"],
    ["Tổng thời gian chạy và nghỉ là bao nhiêu?","2 giờ 40 phút","2 giờ 20 phút","10 giờ 30 phút","10 giờ 10 phút"],
  ],
  'grade-5-motion-speed': [
    ["Dùng phép tính nào để tìm quãng đường đi trong mỗi giờ?","90 : 2","90 × 2","45 km/giờ","180 km/giờ"],
    ["Đổi 45 phút thành bao nhiêu giờ?","0,75 giờ","0,45 giờ","48 km/giờ","80 km/giờ"],
  ],
  'grade-5-motion-distance': [
    ["Đổi 30 phút thành bao nhiêu giờ?","0,5 giờ","0,3 giờ","18 km","10,8 km"],
    ["Chặng đầu đi được bao nhiêu ki-lô-mét?","36 km","54 km","48 km","66 km"],
  ],
  'grade-5-motion-duration': [
    ["Phép tính nào cho biết thời gian đi?","45 : 30","45 × 30","1 giờ 30 phút","1 giờ 50 phút"],
    ["Chặng 72 km đầu mất bao nhiêu thời gian?","1 giờ 30 phút","1 giờ 15 phút","2 giờ 45 phút","2 giờ 30 phút"],
  ],
  'grade-5-data-data': [
    ["25% bằng phần nào của cả lớp?","Một phần tư","Một phần hai","10 bạn","20 bạn"],
    ["Sách khác chiếm bao nhiêu phần trăm?","25%","30%","40 quyển","50 quyển"],
  ],
  'grade-5-data-chance': [
    ["Trong tỉ số cần lập, mẫu số là số nào?","20, tổng số lần thử","7, số lần được đỏ","7/20","20/7"],
    ["Cả hai đợt có bao nhiêu lần ngửa và bao nhiêu lần tung?","30 lần ngửa trên 50 lần tung","19 lần ngửa trên 30 lần tung","3/5","19/30"],
  ],
  'grade-5-review-year-mixed': [
    ["25% bằng phân số nào?","1/4","1/2","6 m²","12 m²"],
    ["Quãng đường đi thêm bằng bao nhiêu?","14,4 km","33,6 km","13 phút 30 giây","22 phút 30 giây"],
  ],
};

export function getPrimaryMathExample(lessonId: unknown, level: unknown): PrimaryMathExample | undefined {
  if (typeof lessonId !== 'string' || (level !== 'easy' && level !== 'advanced')) return;
  const match = /^grade-([1-5])-/.exec(lessonId);
  if (!match || !Object.hasOwn(EXAMPLE_SCRIPTS, lessonId)) return;
  const grade = Number(match[1]) as PrimaryGrade;
  const lesson = getPrimaryChapters(grade).flatMap(chapter => chapter.lessons).find(item => item.id === lessonId);
  const position = level === 'easy' ? 0 : 1;
  const script = EXAMPLE_SCRIPTS[lessonId]?.[position];
  if (!lesson || !script) return;
  const [problem, solution] = lesson.examples[position];
  const [firstQuestion, firstAnswer, firstDistractor, result, resultDistractor] = script;
  const naturalReview = lessonId === 'grade-5-review-natural';
  const resultQuestion = naturalReview
    ? level === 'easy' ? 'Tính nhẩm 48 × (13 + 7).' : 'Tính nhanh 75 × (28 + 12) − 480 : 6.'
    : problem;
  const resultHint = naturalReview
    ? level === 'easy' ? 'Tính 13 + 7 trước rồi nhân tổng với 48.' : 'Tính tổng trong ngoặc, nhân với 75 rồi trừ thương của 480 và 6.'
    : `Ở bước trước, em đã chọn “${firstAnswer}”. Dùng kết quả đó và các dữ kiện còn lại để trả lời đề bài.`;
  const reverse = (problem.length + position) % 2 === 0;
  return {
    lessonId, level, problem, solution,
    steps: [
      {
        title: 'Tìm bước đầu tiên',
        question: firstQuestion,
        correct: firstAnswer,
        choices: reverse ? [firstDistractor, firstAnswer] : [firstAnswer, firstDistractor],
        hint: lesson.explanation,
        feedback: firstAnswer,
      },
      {
        title: 'Tìm kết quả',
        question: resultQuestion,
        correct: result,
        choices: reverse ? [result, resultDistractor] : [resultDistractor, result],
        hint: resultHint,
        feedback: solution,
      },
    ],
  };
}

import { getProblemsByGrade, type CurriculumProblem } from './primaryMathCurriculum';
import { lessonSupplements, type LessonQuestion } from './primaryMathLessonSupplements';

export type PrimaryGrade = CurriculumProblem['grade'];
type LessonSeed = [id: string, title: string, explanation: string, example: string, answer: string, ...practice: number[]];
type ChapterSeed = [id: string, title: string, icon: ChapterIcon, ...lessons: LessonSeed[]];
type ChapterIcon = 'number' | 'operations' | 'shape' | 'measure' | 'time' | 'data' | 'review';
export type PrimaryLesson = {
  id: string;
  title: string;
  explanation: string;
  examples: readonly [easy: LessonQuestion, advanced: LessonQuestion];
  practice: CurriculumProblem[];
  selfPractice: LessonQuestion[];
};
export type PrimaryChapter = { id: string; title: string; icon: ChapterIcon; lessons: PrimaryLesson[] };

// Original explanations and examples. Grade 3 follows the supplied yearly teaching plan.
// Other grades follow the primary mathematics outcomes of CTGDPT 2018.
const chapterSeeds: Record<PrimaryGrade, ChapterSeed[]> = {
  1: [
    ['number-10', 'Các số đến 10', 'number',
      ['count', 'Đếm, đọc và viết các số đến 10', 'Chạm vào từng đồ vật khi đếm. Số em đọc cuối cùng cho biết có tất cả bao nhiêu đồ vật. Không có đồ vật nào thì viết 0.', 'Có ● ● ● ●. Em viết số nào?', '4.'],
      ['compare', 'So sánh và sắp xếp các số', 'Ghép từng đồ vật của hai nhóm thành từng cặp. Nhóm còn thừa có nhiều hơn. Dấu < chỉ bé hơn, dấu > chỉ lớn hơn.', 'Điền dấu vào 3 … 5.', '3 < 5.'],
      ['split', 'Tách và gộp số', 'Một nhóm có thể tách thành hai nhóm nhỏ theo nhiều cách. Gộp lại thì số đồ vật vẫn như lúc đầu.', 'Tách 7 que tính thành một nhóm 2 que và một nhóm nữa. Nhóm kia có mấy que?', '5 que tính.']],
    ['operations-10', 'Cộng và trừ trong phạm vi 10', 'operations',
      ['add', 'Phép cộng và bảng cộng', 'Khi thêm vào hoặc gộp hai nhóm, em dùng phép cộng. Có thể đếm tiếp từ số thứ nhất.', 'Em có 4 viên bi, được cho thêm 3 viên. Em có tất cả bao nhiêu viên?', '4 + 3 = 7 viên.', 3, 6, 7],
      ['subtract', 'Phép trừ và bảng trừ', 'Khi bớt đi hoặc tìm phần còn lại, em có thể dùng phép trừ. Có thể đếm lùi hoặc đếm phần còn lại.', 'Có 9 quả mận, ăn 4 quả. Còn mấy quả?', '9 − 4 = 5 quả.', 4, 5, 8, 9]],
    ['shapes', 'Hình phẳng và hình khối', 'shape',
      ['flat', 'Hình vuông, hình tròn, hình tam giác và hình chữ nhật', 'Hình tròn không có góc. Hình tam giác có ba góc. Hình vuông và hình chữ nhật đều có bốn góc.', 'Mặt của đồng xu giống hình gì?', 'Hình tròn.', 18],
      ['solid', 'Khối lập phương và khối hộp chữ nhật', 'Quan sát hộp quà hoặc viên xúc xắc. Khối lập phương có các mặt đều là hình vuông.', 'Viên xúc xắc thường có dạng khối gì?', 'Khối lập phương.']],
    ['number-100', 'Các số đến 100', 'number',
      ['place', 'Chục và đơn vị', 'Mười que rời bó lại thành một chục. Hai chữ số trong 46 lần lượt chỉ 4 chục và 6 đơn vị.', 'Có 5 bó, mỗi bó 10 que, và 3 que rời. Có bao nhiêu que?', '53 que.', 19],
      ['compare-100', 'So sánh các số có hai chữ số', 'So sánh số chục trước. Nếu số chục bằng nhau, so sánh số đơn vị.', '36 và 39, số nào lớn hơn?', '39, vì cùng 3 chục và 9 đơn vị lớn hơn 6 đơn vị.']],
    ['operations-100', 'Cộng và trừ trong phạm vi 100', 'operations',
      ['tens', 'Cộng, trừ các số tròn chục', 'Đổi các số tròn chục thành số bó chục, rồi cộng hoặc trừ số bó.', '40 + 20 bằng bao nhiêu?', '4 chục + 2 chục = 6 chục, tức 60.', 10],
      ['add-100', 'Cộng trong phạm vi 100', 'Đặt hàng đơn vị thẳng cột với hàng đơn vị. Cộng đơn vị với đơn vị và chục với chục.', '25 + 13 bằng bao nhiêu?', '5 + 3 = 8 đơn vị, 2 + 1 = 3 chục. Kết quả là 38.', 1, 11, 14],
      ['subtract-100', 'Trừ trong phạm vi 100', 'Khi đặt tính, viết các chữ số cùng hàng thẳng cột. Trong bài trừ không nhớ, trừ từng hàng từ phải sang trái.', '58 − 24 bằng bao nhiêu?', '8 − 4 = 4 đơn vị, 5 − 2 = 3 chục. Kết quả là 34.', 2, 12, 13]],
    ['measure', 'Độ dài, đồng hồ và lịch', 'measure',
      ['length', 'Đo độ dài bằng xăng-ti-mét', 'Đặt đầu vật trùng với vạch số 0 trên thước. Số ở vạch ngang đầu kia cho biết độ dài tính bằng cm.', 'Vạch 0 ở đầu bút, đầu kia ở vạch 8. Bút dài bao nhiêu?', '8 cm.', 15, 20],
      ['clock', 'Xem giờ đúng', 'Khi kim phút chỉ số 12, đọc số kim giờ đang chỉ.', 'Kim dài chỉ 12 và kim ngắn chỉ 7. Đồng hồ chỉ mấy giờ?', '7 giờ đúng.', 16],
      ['calendar', 'Các ngày trong tuần', 'Một tuần có bảy ngày. Thứ Hai, thứ Ba, thứ Tư, thứ Năm, thứ Sáu, thứ Bảy rồi đến Chủ nhật.', 'Hôm nay thứ Năm. Ngày mai là ngày nào?', 'Thứ Sáu.', 17]],
  ],
  2: [
    ['number-100', 'Số và phép tính trong phạm vi 100', 'operations',
      ['add', 'Cộng có nhớ', 'Khi tổng hàng đơn vị được từ 10 trở lên, đổi 10 đơn vị thành 1 chục rồi cộng vào hàng chục.', 'Tính 46 + 27.', '6 + 7 = 13, viết 3 nhớ 1 chục. 4 + 2 + 1 = 7. Kết quả 73.', 7],
      ['subtract', 'Trừ có nhớ', 'Nếu hàng đơn vị của số bị trừ bé hơn hàng đơn vị của số trừ, đổi một chục thành mười đơn vị.', 'Tính 52 − 16.', 'Đổi 1 chục. 12 − 6 = 6, còn 4 chục; 4 − 1 = 3. Kết quả 36.', 8],
      ['more-less', 'Bài toán nhiều hơn và ít hơn', 'Xác định số đã biết và phần chênh lệch. Muốn tìm số lớn hơn số đã biết thì cộng phần chênh lệch, tìm số bé hơn thì trừ.', 'An có 14 nhãn, Bình có ít hơn An 3 nhãn. Bình có bao nhiêu nhãn?', '14 − 3 = 11 nhãn.', 1, 2, 20]],
    ['multiply-divide', 'Làm quen với phép nhân và phép chia', 'operations',
      ['multiply-two', 'Bảng nhân 2', 'Nhiều nhóm giống nhau, mỗi nhóm có 2 đồ vật, có thể tính bằng cách lấy 2 nhân với số nhóm.', 'Có 4 đôi tất. Có tất cả bao nhiêu chiếc tất?', '2 × 4 = 8 chiếc.', 3, 18],
      ['multiply-five', 'Bảng nhân 5', 'Đếm thêm 5 ở mỗi lượt để lập bảng nhân 5.', 'Có 3 bàn tay. Mỗi bàn tay có 5 ngón. Có tất cả mấy ngón?', '5 × 3 = 15 ngón.', 4, 19],
      ['divide', 'Bảng chia 2 và bảng chia 5', 'Chia là chia đều hoặc tìm số nhóm bằng nhau. Dùng bảng nhân để kiểm tra phép chia.', 'Chia 20 bút đều vào 5 hộp. Mỗi hộp có mấy bút?', '20 : 5 = 4 bút, vì 5 × 4 = 20.', 5, 6]],
    ['number-1000', 'Các số đến 1.000', 'number',
      ['place', 'Trăm, chục và đơn vị', '10 chục bằng 1 trăm, 10 trăm bằng 1 nghìn. So sánh số có ba chữ số từ hàng trăm đến hàng đơn vị.', 'Số nào lớn hơn, 408 hay 480?', '480, vì cùng 4 trăm nhưng 8 chục lớn hơn 0 chục.'],
      ['add-1000', 'Cộng trong phạm vi 1.000', 'Đặt tính thẳng hàng và cộng từ hàng đơn vị. Nếu có nhớ, thêm một vào hàng ngay bên trái.', 'Tính 267 + 135.', '267 + 135 = 402.', 9],
      ['subtract-1000', 'Trừ trong phạm vi 1.000', 'Trừ từ hàng đơn vị. Nếu cần đổi, lấy một đơn vị ở hàng liền bên trái đổi thành mười đơn vị ở hàng hiện tại.', 'Tính 514 − 123.', '514 − 123 = 391.', 10]],
    ['geometry', 'Đường, đoạn thẳng và hình khối', 'shape',
      ['line', 'Đường thẳng, đường cong và đường gấp khúc', 'Đường gấp khúc gồm các đoạn thẳng nối nhau. Cộng độ dài của từng đoạn để tìm độ dài cả đường.', 'Hai đoạn liên tiếp dài 7 cm và 5 cm. Đường gấp khúc dài bao nhiêu?', '7 + 5 = 12 cm.', 11, 17],
      ['shapes', 'Hình tứ giác, khối trụ và khối cầu', 'Hình tứ giác có bốn cạnh. Lon nước thường có dạng khối trụ, còn quả bóng có dạng khối cầu.', 'Vật nào có dạng khối cầu, lon sữa hay quả bóng?', 'Quả bóng.']],
    ['measure', 'Đo lường và thời gian', 'measure',
      ['length', 'Đề-xi-mét, mét và ki-lô-mét', 'Chọn đơn vị vừa với vật cần đo. 1 dm = 10 cm, 1 m = 100 cm, 1 km = 1.000 m.', 'Một sợi dây dài 3 dm. Dây dài bao nhiêu xăng-ti-mét?', '30 cm.'],
      ['mass-volume', 'Ki-lô-gam và lít', 'Dùng cân và đơn vị kg để đo khối lượng. Dùng ca đong và đơn vị l để đo dung tích.', 'Một bình có 5 l nước. Rót ra 2 l. Bình còn bao nhiêu lít?', '5 − 2 = 3 l.', 12, 13],
      ['time-money', 'Đồng hồ, lịch và tiền Việt Nam', 'Một giờ có 60 phút. Dùng lịch để tìm ngày. Khi mua đồ, tiền còn lại bằng tiền đưa trừ tiền phải trả.', 'Em có 10.000 đồng, mua vở giá 7.000 đồng. Em còn bao nhiêu?', '3.000 đồng.', 14, 15]],
    ['data', 'Thống kê và khả năng xảy ra', 'data',
      ['pictures', 'Thu thập số liệu và đọc biểu đồ tranh', 'Phân loại đồ vật rồi đếm theo từng nhóm. Khi đọc biểu đồ tranh, xem mỗi hình biểu thị bao nhiêu.', 'Mỗi hình quả táo biểu thị 2 quả. Có 3 hình. Biểu đồ chỉ bao nhiêu quả?', '6 quả.', 16],
      ['chance', 'Chắc chắn, có thể và không thể', 'Xem những kết quả có thể có trước khi rút thẻ hoặc lấy đồ vật từ hộp.', 'Hộp chỉ có thẻ đỏ. Rút được thẻ xanh là khả năng nào?', 'Không thể.']],
  ],
  3: [
    ['review', 'Ôn tập và bổ sung', 'review',
      ['number', 'Ôn các số và phép cộng, trừ đến 1.000', 'Phân tích số thành trăm, chục và đơn vị. Khi tìm số hạng chưa biết, lấy tổng trừ số hạng đã biết.', 'Tìm số còn thiếu: 125 + … = 300.', '300 − 125 = 175.'],
      ['tables', 'Ôn bảng 2, 5 và học bảng 3, 4', 'Mỗi lần thêm một nhóm, tích tăng thêm đúng số đồ vật của nhóm. Có thể dùng phép nhân để thử lại phép chia.', 'Có 6 túi, mỗi túi 4 quả. Có tất cả bao nhiêu quả?', '4 × 6 = 24 quả.']],
    ['tables', 'Bảng nhân, bảng chia', 'operations',
      ['multiply', 'Bảng nhân 6, 7, 8 và 9', 'Đếm theo từng nhóm bằng nhau hoặc dùng một tích gần mà em đã nhớ.', 'Biết 7 × 5 = 35, tính 7 × 6.', '35 + 7 = 42.', 3],
      ['divide', 'Bảng chia 6, 7, 8 và 9', 'Tìm số nhân với số chia để được số bị chia. Dùng phép nhân tương ứng để kiểm tra kết quả.', 'Tính 56 : 8.', '56 : 8 = 7, vì 8 × 7 = 56.', 4],
      ['part', 'Tìm một phần mấy của một số', 'Chia số đã cho thành các phần bằng nhau. Muốn lấy một phần ba, chia số đó cho 3.', 'Một phần tư của 20 viên bi là mấy viên?', '20 : 4 = 5 viên.', 15]],
    ['shapes', 'Làm quen với hình phẳng, hình khối', 'shape',
      ['points', 'Điểm ở giữa và trung điểm', 'Trung điểm nằm giữa hai đầu đoạn thẳng và cách đều hai đầu.', 'M nằm giữa A và B, AM = 3 cm, MB = 3 cm. M là điểm gì?', 'M là trung điểm của đoạn AB.'],
      ['circle', 'Tâm, bán kính và đường kính', 'Bán kính nối tâm với một điểm trên đường tròn. Đường kính đi qua tâm và dài gấp đôi bán kính.', 'Bán kính 4 cm. Đường kính dài bao nhiêu?', '8 cm.'],
      ['angles', 'Góc vuông, hình tam giác và hình tứ giác', 'Dùng ê ke để kiểm tra góc vuông. Đếm cạnh để phân biệt tam giác với tứ giác.', 'Một hình có bốn góc vuông và bốn cạnh bằng nhau. Đó là hình gì?', 'Hình vuông.'],
      ['solids', 'Khối hộp chữ nhật và khối lập phương', 'Quan sát các đỉnh, cạnh và mặt. Hai khối này đều có 6 mặt, 12 cạnh và 8 đỉnh.', 'Một hộp có sáu mặt đều là hình vuông. Hộp có dạng khối gì?', 'Khối lập phương.']],
    ['operations-100', 'Nhân và chia trong phạm vi 100', 'operations',
      ['multiply', 'Nhân số có hai chữ số và gấp lên một số lần', 'Nhân từng hàng từ phải sang trái. Muốn tìm số gấp lên nhiều lần, lấy số ban đầu nhân với số lần.', 'Có 12 bông hoa, gấp lên 3 lần được bao nhiêu bông?', '12 × 3 = 36 bông.', 5],
      ['divide', 'Chia hết, chia có dư và giảm đi một số lần', 'Chia theo từng hàng. Số dư phải nhỏ hơn số chia. Muốn giảm một số đi vài lần thì chia cho số lần đó.', 'Chia 29 chiếc bánh vào các túi, mỗi túi 4 chiếc. Đầy mấy túi, dư mấy chiếc?', '29 : 4 = 7 dư 1. Có 7 túi đầy, dư 1 chiếc.', 2, 6],
      ['two-steps', 'Bài toán giải bằng hai bước tính', 'Tìm thông tin còn thiếu trước, sau đó lấy kết quả đó để trả lời câu hỏi cuối.', 'Lan có 9 hạt, Minh có nhiều hơn Lan 4 hạt. Hai bạn có tất cả bao nhiêu?', 'Minh có 9 + 4 = 13 hạt. Hai bạn có 9 + 13 = 22 hạt.', 1, 16]],
    ['measure', 'Độ dài, khối lượng, dung tích và nhiệt độ', 'measure',
      ['length', 'Mi-li-mét và đổi đơn vị độ dài', 'Mi-li-mét là một đơn vị đo độ dài. 1 cm = 10 mm, 1 m = 100 cm.', 'Đổi 6 cm sang mi-li-mét.', '60 mm.', 14],
      ['units', 'Gam, mi-li-lít và độ C', 'Dùng g để đọc khối lượng vật nhẹ, ml để đọc lượng chất lỏng và °C để đọc nhiệt độ.', 'Hai chai có 250 ml nước mỗi chai. Cả hai chai có bao nhiêu nước?', '500 ml.']],
    ['operations-1000', 'Nhân và chia trong phạm vi 1.000', 'operations',
      ['multiply', 'Nhân số có ba chữ số với số có một chữ số', 'Nhân từ đơn vị sang chục rồi đến trăm. Nhớ chuyển phần đủ mười sang hàng tiếp theo.', 'Tính 112 × 4.', 'Nhân lần lượt được 8 đơn vị, 4 chục và 4 trăm. Kết quả là 448.', 7],
      ['divide', 'Chia số có ba chữ số cho số có một chữ số', 'Chia lần lượt từ trái sang phải. Mỗi lượt thực hiện chia, nhân, trừ rồi hạ chữ số tiếp theo.', 'Tính 396 : 3.', '396 : 3 = 132.', 8],
      ['expression', 'Tính giá trị biểu thức', 'Tính trong ngoặc trước. Với biểu thức không có ngoặc, làm nhân chia trước cộng trừ. Các phép cùng mức tính từ trái sang phải.', 'Tính 10 + 4 × 5.', '4 × 5 = 20, rồi 10 + 20 = 30.', 9, 10],
      ['times', 'Số lớn gấp mấy lần số bé', 'Lấy số lớn chia cho số bé để biết số lớn gấp mấy lần.', '24 gấp 6 mấy lần?', '24 : 6 = 4 lần.', 20]],
    ['review-one', 'Ôn tập học kì I', 'review',
      ['mixed', 'Ôn phép tính và đo lường', 'Khi dùng hai số đo trong cùng một phép tính, đổi về cùng đơn vị trước.', 'Cộng 2 m với 30 cm, kết quả bằng bao nhiêu xăng-ti-mét?', '200 + 30 = 230 cm.']],
    ['number-10000', 'Các số đến 10.000', 'number',
      ['place', 'Đọc, viết và so sánh số có bốn chữ số', 'Xem lần lượt hàng nghìn, trăm, chục rồi đơn vị. Khi so sánh, hàng đầu tiên khác nhau quyết định kết quả.', 'Sắp xếp 4.520 và 4.502 từ bé đến lớn.', '4.502 < 4.520.'],
      ['round', 'Làm tròn và chữ số La Mã', 'Để làm tròn đến hàng trăm, nhìn hàng chục. Với chữ số La Mã đã học, IV chỉ 4 và IX chỉ 9.', 'Làm tròn 3.476 đến hàng trăm.', '3.500, vì hàng chục là 7.']],
    ['area', 'Chu vi, diện tích một số hình phẳng', 'shape',
      ['perimeter', 'Chu vi các hình phẳng', 'Chu vi là độ dài đường bao quanh hình. Cộng độ dài tất cả các cạnh.', 'Tam giác có ba cạnh dài 4 cm, 5 cm và 6 cm. Chu vi bằng bao nhiêu?', '4 + 5 + 6 = 15 cm.', 11],
      ['square-unit', 'Diện tích và xăng-ti-mét vuông', 'Diện tích cho biết phần mặt hình chiếm chỗ. Một ô vuông có cạnh 1 cm có diện tích 1 cm².', 'Một hình phủ vừa 9 ô vuông cạnh 1 cm. Diện tích của hình là bao nhiêu?', '9 cm².'],
      ['rectangle', 'Diện tích hình chữ nhật', 'Hình chữ nhật được xếp thành các hàng ô đều nhau. Lấy chiều dài nhân chiều rộng khi cả hai số đo cùng đơn vị.', 'Hình chữ nhật dài 6 cm và rộng 3 cm. Tính diện tích.', '6 × 3 = 18 cm².', 12],
      ['square', 'Diện tích hình vuông', 'Hình vuông có số hàng ô bằng số ô trong mỗi hàng. Lấy độ dài một cạnh nhân với chính nó.', 'Hình vuông cạnh 4 cm có diện tích bao nhiêu?', '4 × 4 = 16 cm².', 13],
      ['apply', 'Phân biệt chu vi và diện tích', 'Muốn tính hàng rào quanh vườn thì tính chu vi. Muốn biết phần đất trồng chiếm bao nhiêu thì tính diện tích.', 'Vườn dài 8 m và rộng 3 m. Muốn trồng cỏ kín vườn, em cần tính gì?', 'Tính diện tích: 8 × 3 = 24 m².']],
    ['operations-10000', 'Cộng, trừ, nhân và chia trong phạm vi 10.000', 'operations',
      ['add-subtract', 'Cộng và trừ số có bốn chữ số', 'Đặt các chữ số cùng hàng thẳng cột. Tính từ hàng đơn vị và chuyển nhớ sang hàng liền kề.', 'Tính 2.806 + 1.719.', '4.525.'],
      ['multiply-divide', 'Nhân và chia số có bốn chữ số', 'Khi nhân, tính từ phải sang trái. Khi chia, bắt đầu ở bên trái rồi hạ từng chữ số xuống.', 'Tính 8.484 : 4.', '2.121.']],
    ['number-100000', 'Các số đến 100.000', 'number',
      ['place', 'Đọc, viết và so sánh các số đến 100.000', 'Dựa vào giá trị từng hàng để đọc, viết và phân tích số.', 'Chữ số 5 trong 54.037 biểu thị bao nhiêu?', '50.000.'],
      ['round', 'Làm tròn đến hàng nghìn và chục nghìn', 'Để làm tròn đến hàng nghìn, xem chữ số hàng trăm. Từ 5 trở lên thì tăng hàng nghìn lên một.', 'Làm tròn 26.780 đến hàng nghìn.', '27.000.']],
    ['add-subtract-100000', 'Cộng và trừ trong phạm vi 100.000', 'operations',
      ['add', 'Cộng trong phạm vi 100.000', 'Cộng từ hàng đơn vị. Nếu tổng ở một hàng có hai chữ số, viết chữ số đơn vị và nhớ một sang hàng kế tiếp.', 'Tính 32.785 + 14.218.', '47.003.'],
      ['subtract', 'Trừ trong phạm vi 100.000', 'Trừ từng hàng từ phải qua trái. Khi đổi một đơn vị của hàng bên trái, hàng hiện tại có thêm mười đơn vị.', 'Tính 46.210 − 12.804.', '33.406.']],
    ['calendar-money', 'Đồng hồ, tháng, năm và tiền Việt Nam', 'time',
      ['clock', 'Xem đồng hồ và đọc lịch', 'Mỗi khoảng giữa hai số trên đồng hồ ứng với 5 phút. Đọc lịch để biết thứ, ngày, tháng và số ngày trong tháng.', 'Từ 8 giờ 10 đến 8 giờ 35 là bao nhiêu phút?', '25 phút.', 18],
      ['money', 'Tiền Việt Nam', 'Cộng giá các món để tìm tổng tiền. Lấy số tiền đưa trừ tổng tiền để tính tiền trả lại.', 'Mua đồ hết 11.000 đồng và đưa 20.000 đồng. Nhận lại bao nhiêu?', '9.000 đồng.', 17]],
    ['multiply-divide-100000', 'Nhân và chia trong phạm vi 100.000', 'operations',
      ['multiply', 'Nhân số có năm chữ số với số có một chữ số', 'Nhân từng hàng từ phải sang trái. Ước lượng trước để xem kết quả có hợp lý không.', 'Tính 21.305 × 3.', '63.915.'],
      ['divide', 'Chia số có năm chữ số cho số có một chữ số', 'Chia từ hàng cao nhất. Viết 0 vào thương nếu chữ số vừa hạ xuống chưa đủ chia sau khi thương đã bắt đầu.', 'Tính 64.008 : 8.', '8.001.']],
    ['data', 'Làm quen với thống kê và xác suất', 'data',
      ['table', 'Thu thập, phân loại và đọc bảng số liệu', 'Ghi kết quả đếm theo từng nhóm. Đọc tên hàng và tên cột trước khi lấy số từ bảng.', 'Thứ Hai đọc 8 trang, thứ Ba đọc 11 trang. Thứ Ba nhiều hơn mấy trang?', '11 − 8 = 3 trang.', 19],
      ['chance', 'Khả năng xảy ra của một sự kiện', 'Liệt kê các kết quả có thể thấy sau một lần thử, chẳng hạn tung đồng xu hoặc rút bóng.', 'Một hộp có bóng đỏ và bóng xanh. Khi lấy một quả, có thể thấy những màu nào?', 'Đỏ hoặc xanh.']],
    ['review-year', 'Ôn tập cuối năm', 'review',
      ['mixed', 'Ôn số, phép tính, hình học và số liệu', 'Chọn kiến thức theo câu hỏi. Đọc đơn vị, ước lượng trước rồi kiểm tra kết quả cuối cùng.', 'Mỗi ngày đọc 12 trang trong 5 ngày. Đã đọc bao nhiêu trang?', '12 × 5 = 60 trang.']],
  ],
  4: [
    ['numbers', 'Số tự nhiên và các hàng, lớp', 'number',
      ['place', 'Đọc, viết và so sánh số đến lớp triệu', 'Chia số thành từng lớp ba chữ số, từ phải qua trái. Các lớp lần lượt là đơn vị, nghìn và triệu.', 'Chữ số 7 trong 7.452.019 có giá trị bao nhiêu?', '7.000.000.'],
      ['round', 'Làm tròn số và nhận biết số chẵn, số lẻ', 'Xem hàng ngay bên phải hàng cần làm tròn. Số chẵn có chữ số hàng đơn vị là 0, 2, 4, 6 hoặc 8.', 'Làm tròn 37.680 đến hàng nghìn.', '38.000.']],
    ['operations', 'Các phép tính với số tự nhiên', 'operations',
      ['add', 'Cộng số có nhiều chữ số', 'Đặt các chữ số cùng hàng thẳng cột. Có thể đổi chỗ và nhóm các số hạng để tính thuận tiện.', 'Tính 125 + 43 + 75.', '(125 + 75) + 43 = 243.', 2, 3],
      ['subtract', 'Trừ số có nhiều chữ số', 'Trừ lần lượt từ hàng đơn vị. Cộng hiệu với số trừ để thử lại.', 'Tính 52.410 − 8.345.', '44.065.', 4],
      ['multiply', 'Nhân số có nhiều chữ số', 'Khi nhân với số có hai chữ số, tính tích với hàng đơn vị và hàng chục, rồi cộng hai tích theo đúng cột.', 'Tính 132 × 24.', '132 × 4 + 132 × 20 = 528 + 2.640 = 3.168.', 5],
      ['divide', 'Chia cho số có hai chữ số', 'Ước lượng chữ số thương ở mỗi lượt rồi thử bằng phép nhân. Số còn lại phải nhỏ hơn số chia.', 'Tính 420 : 21.', '42 : 21 = 2. Hạ 0, được chữ số 0 ở hàng đơn vị của thương. Kết quả là 20.', 6],
      ['expression', 'Biểu thức có chứa chữ', 'Thay chữ bằng số đã cho, rồi tính giá trị biểu thức theo thứ tự phép tính.', 'Tính a + 3 × b với a = 5 và b = 4.', '5 + 3 × 4 = 17.']],
    ['problems', 'Giải bài toán có lời văn', 'operations',
      ['average', 'Tìm số trung bình cộng', 'Cộng các số rồi chia tổng cho số lượng các số.', 'Ba ngày đọc 8, 10, 12 trang. Trung bình mỗi ngày đọc bao nhiêu?', '(8 + 10 + 12) : 3 = 10 trang.', 7, 20],
      ['sum-difference', 'Tìm hai số khi biết tổng và hiệu', 'Lấy tổng trừ hiệu rồi chia 2 để được số bé. Cộng số bé với hiệu để được số lớn.', 'Hai số có tổng 64 và hiệu 12. Tìm hai số.', 'Số bé là 26. Số lớn là 38.', 1, 8],
      ['one-unit', 'Bài toán rút về đơn vị', 'Tìm lượng của một nhóm rồi dùng kết quả để tính cho số nhóm được hỏi.', '4 túi có 28 quả cam như nhau. 6 túi có bao nhiêu quả?', '28 : 4 = 7 quả mỗi túi. 7 × 6 = 42 quả.', 18]],
    ['shapes', 'Góc và các hình phẳng', 'shape',
      ['angle', 'Đo góc và nhận biết các loại góc', 'Đặt tâm thước trùng đỉnh góc, vạch 0 trùng một cạnh. Đọc số đo ở cạnh còn lại.', 'Góc 120° là góc gì?', 'Góc tù, lớn hơn 90° và nhỏ hơn 180°.'],
      ['lines', 'Hai đường thẳng vuông góc và song song', 'Hai đường vuông góc tạo thành góc vuông. Hai đường thẳng song song trong cùng một mặt phẳng không cắt nhau.', 'Hai cạnh kề trong một hình chữ nhật có quan hệ gì?', 'Vuông góc.'],
      ['parallelogram', 'Hình bình hành và hình thoi', 'Hình bình hành có hai cặp cạnh đối song song. Hình thoi có bốn cạnh bằng nhau. Có thể cắt ghép hình bình hành thành hình chữ nhật để hiểu cách tính diện tích.', 'Hình bình hành có đáy 9 cm và chiều cao 4 cm. Tính diện tích.', '9 × 4 = 36 cm².', 15],
      ['perimeter-area', 'Thực hành chu vi và diện tích', 'Chu vi đo đường viền, diện tích đo phần mặt hình. Đổi số đo các cạnh về cùng một đơn vị trước khi tính.', 'Hình chữ nhật 8 cm và 5 cm có chu vi và diện tích bao nhiêu?', 'Chu vi 26 cm. Diện tích 40 cm².', 19]],
    ['measure', 'Đại lượng và đo lường', 'measure',
      ['mass', 'Yến, tạ và tấn', '1 yến = 10 kg, 1 tạ = 100 kg, 1 tấn = 1.000 kg.', 'Đổi 3 tạ 5 kg sang ki-lô-gam.', '305 kg.', 16],
      ['time-area', 'Giây, thế kỉ và các đơn vị diện tích', 'Một phút có 60 giây, một thế kỉ có 100 năm. Hai đơn vị diện tích liền nhau trong dãy mm², cm², dm², m² hơn kém nhau 100 lần.', 'Đổi 3 dm² sang xăng-ti-mét vuông.', '300 cm².']],
    ['fractions', 'Phân số và các phép tính với phân số', 'number',
      ['compare', 'Phân số bằng nhau, rút gọn và so sánh', 'Nhân hoặc chia cả tử và mẫu cho cùng một số khác 0 để được phân số bằng phân số đã cho. Có thể quy đồng mẫu rồi so sánh tử.', 'Rút gọn 6/8.', 'Chia cả tử và mẫu cho 2, được 3/4.'],
      ['add-subtract', 'Cộng và trừ hai phân số', 'Quy đồng mẫu nếu hai mẫu khác nhau. Cộng hoặc trừ các tử rồi giữ nguyên mẫu chung.', 'Tính 1/2 + 1/4.', '2/4 + 1/4 = 3/4.', 9, 10, 11],
      ['multiply-divide', 'Nhân và chia hai phân số', 'Nhân tử với tử, mẫu với mẫu. Muốn chia cho một phân số khác 0, nhân với phân số đảo ngược của nó.', 'Tính 2/3 : 4/5.', '2/3 × 5/4 = 5/6.', 12, 13],
      ['part', 'Tìm phân số của một số', 'Lấy số đã cho nhân với phân số. Có thể chia cho mẫu trước nếu chia hết, rồi nhân với tử.', 'Tìm 3/4 của 28.', '28 : 4 × 3 = 21.', 14]],
    ['data', 'Biểu đồ cột và kết quả thực nghiệm', 'data',
      ['columns', 'Đọc và nhận xét biểu đồ cột', 'Đọc tên trục, đơn vị và vạch chia trước khi so sánh độ cao các cột.', 'Hai cột chỉ 8 và 12 quyển sách. Cột cao hơn biểu thị nhiều hơn mấy quyển?', '4 quyển.', 17],
      ['chance', 'Kiểm đếm số lần xuất hiện', 'Mỗi lần thử, ghi một dấu vào nhóm kết quả tương ứng. Đối chiếu tổng các nhóm với số lượt đã thử.', 'Tung đồng xu 10 lần, có 6 lần mặt ngửa. Có mấy lần mặt sấp?', '4 lần.']],
  ],
  5: [
    ['review', 'Ôn số tự nhiên và phân số', 'review',
      ['natural', 'Ôn phép tính với số tự nhiên', 'Dùng tính chất phân phối để nhóm phép tính và kiểm tra kết quả bằng ước lượng.', 'Tính nhẩm 48 × 13 + 48 × 7.', '48 × (13 + 7) = 960.'],
      ['fraction', 'Ôn phân số và làm quen với hỗn số', 'Hỗn số gồm phần nguyên và phần phân số bé hơn 1. Khi cộng các phân số khác mẫu, quy đồng trước.', 'Đổi hỗn số 2 và 1/3 sang phân số.', '(2 × 3 + 1)/3 = 7/3.', 20]],
    ['decimals', 'Số thập phân', 'number',
      ['read', 'Đọc, viết và so sánh số thập phân', 'So sánh phần nguyên trước, rồi so sánh phần thập phân từ hàng phần mười. Có thể viết thêm số 0 ở cuối phần thập phân.', 'Số nào lớn hơn, 3,5 hay 3,48?', '3,5 lớn hơn, vì 3,50 > 3,48.'],
      ['round', 'Làm tròn số thập phân', 'Giữ các chữ số đến hàng cần làm tròn. Nếu chữ số liền sau từ 5 trở lên, tăng chữ số ở hàng làm tròn thêm một.', 'Làm tròn 8,276 đến hàng phần trăm.', '8,28.'],
      ['add', 'Cộng số thập phân', 'Khi đặt tính, viết các dấu phẩy thẳng cột. Cộng từng hàng rồi viết dấu phẩy ở hàng thẳng với các dấu phẩy phía trên.', 'Tính 4,8 + 2,35.', '4,80 + 2,35 = 7,15.', 3],
      ['subtract', 'Trừ số thập phân', 'Đặt thẳng dấu phẩy. Viết thêm số 0 ở cuối phần thập phân khi cần để hai số có cùng số chữ số sau dấu phẩy.', 'Tính 8,2 − 3,47.', '8,20 − 3,47 = 4,73.', 4],
      ['multiply', 'Nhân số thập phân', 'Nhân như với số tự nhiên. Đếm tổng số chữ số sau dấu phẩy của hai thừa số để đặt dấu phẩy trong tích.', 'Tính 1,2 × 0,3.', '12 × 3 = 36. Dịch dấu phẩy hai hàng từ phải qua trái, được 0,36.', 5],
      ['divide', 'Chia số thập phân', 'Nếu số chia có dấu phẩy, nhân cả hai số với cùng một lũy thừa của 10 để số chia thành số tự nhiên.', 'Tính 4,8 : 0,6.', '48 : 6 = 8.', 6, 7]],
    ['ratios', 'Tỉ số và tỉ số phần trăm', 'operations',
      ['ratio', 'Tỉ số và tỉ lệ bản đồ', 'Tỉ số so sánh hai lượng bằng phép chia. Tỉ lệ 1 : 1.000 nghĩa là một đơn vị trên bản đồ ứng với 1.000 đơn vị ngoài thực tế.', 'Trên bản đồ tỉ lệ 1 : 1.000, đoạn dài 4 cm. Thực tế dài bao nhiêu mét?', '4.000 cm = 40 m.'],
      ['percent', 'Tìm tỉ số phần trăm', 'Chia lượng cần so sánh cho tổng, rồi viết thương dưới dạng phần trăm.', 'Có 12 bạn đi bộ trong lớp 30 bạn. Tỉ lệ là bao nhiêu phần trăm?', '12 : 30 = 0,4 = 40%.', 8],
      ['percentage-of', 'Tìm phần trăm của một số', 'Nhân số đó với tỉ lệ đã đổi thành phân số hoặc số thập phân.', 'Tìm 15% của 200.', '200 × 0,15 = 30.', 9],
      ['application', 'Bài toán tăng, giảm theo phần trăm', 'Tính phần tăng hoặc giảm theo giá ban đầu. Sau đó cộng hoặc trừ phần đó để tìm giá mới.', 'Một quyển sách giá 80.000 đồng, giảm 10%. Giá mới là bao nhiêu?', 'Giảm 8.000 đồng. Giá mới 72.000 đồng.', 10]],
    ['plane-geometry', 'Chu vi và diện tích hình phẳng', 'shape',
      ['area-unit', 'Các đơn vị đo diện tích và héc-ta', '1 ha = 10.000 m² và 1 km² = 1.000.000 m². Đổi các số đo về cùng đơn vị trước khi tính.', '2 ha bằng bao nhiêu mét vuông?', '20.000 m².', 18],
      ['triangle', 'Diện tích hình tam giác', 'Lấy đáy nhân chiều cao vuông góc với đáy, rồi chia 2. Hai số đo phải cùng đơn vị.', 'Đáy 8 cm, chiều cao 5 cm. Tính diện tích.', '8 × 5 : 2 = 20 cm².', 1],
      ['trapezoid', 'Diện tích hình thang', 'Cộng độ dài hai đáy song song, nhân với chiều cao rồi chia cho 2.', 'Hai đáy dài 6 cm và 10 cm, cao 4 cm. Tính diện tích.', '(6 + 10) × 4 : 2 = 32 cm².', 11],
      ['circle-perimeter', 'Chu vi hình tròn', 'Nhân đường kính với 3,14. Nếu biết bán kính, nhân bán kính với 2 để tìm đường kính.', 'Hình tròn bán kính 5 cm có chu vi bao nhiêu?', '5 × 2 × 3,14 = 31,4 cm.', 12],
      ['circle-area', 'Diện tích hình tròn', 'Nhân bán kính với bán kính rồi nhân với 3,14.', 'Hình tròn bán kính 3 cm có diện tích bao nhiêu?', '3 × 3 × 3,14 = 28,26 cm².', 13]],
    ['solids', 'Hình khối và thể tích', 'shape',
      ['surface', 'Hình khai triển và diện tích bề mặt', 'Trải các mặt của khối thành hình phẳng. Cộng diện tích các mặt cần phủ để tìm diện tích bề mặt.', 'Khối lập phương cạnh 2 cm có diện tích toàn phần bao nhiêu?', '6 × 2 × 2 = 24 cm².'],
      ['volume-units', 'Thể tích và các đơn vị đo', 'Thể tích đo phần không gian khối chiếm chỗ. Một khối kích thước 1 cm × 1 cm × 1 cm có thể tích 1 cm³.', '1 dm³ bằng bao nhiêu xăng-ti-mét khối?', '1.000 cm³.'],
      ['box-volume', 'Thể tích hình hộp chữ nhật', 'Nhân chiều dài với chiều rộng để tìm số khối trong một lớp. Nhân tiếp với chiều cao để tìm thể tích.', 'Hộp dài 7 cm, rộng 4 cm và cao 3 cm. Tính thể tích.', '7 × 4 × 3 = 84 cm³.', 14],
      ['cube-volume', 'Thể tích hình lập phương', 'Ba kích thước của khối lập phương bằng nhau. Nhân độ dài cạnh ba lần để tìm thể tích.', 'Khối lập phương cạnh 5 cm có thể tích bao nhiêu?', '5 × 5 × 5 = 125 cm³.', 15]],
    ['motion', 'Thời gian và chuyển động đều', 'time',
      ['time-units', 'Đổi đơn vị và tính với số đo thời gian', 'Đổi thời gian về cùng một đơn vị trước khi tính. 1 giờ = 60 phút và 1 phút = 60 giây.', '1 giờ 30 phút bằng bao nhiêu giờ?', '1,5 giờ.'],
      ['speed', 'Tính vận tốc', 'Lấy quãng đường chia cho thời gian. Ghi đơn vị tương ứng, chẳng hạn km/giờ.', 'Đi 90 km trong 2 giờ. Vận tốc là bao nhiêu?', '90 : 2 = 45 km/giờ.', 2],
      ['distance', 'Tính quãng đường', 'Nhân vận tốc với thời gian. Nếu vận tốc tính theo km/giờ thì đổi thời gian sang giờ.', 'Đi với vận tốc 36 km/giờ trong 30 phút. Đi được bao xa?', '36 × 0,5 = 18 km.', 16],
      ['duration', 'Tính thời gian chuyển động', 'Lấy quãng đường chia cho vận tốc, rồi đổi sang đơn vị giờ hoặc phút theo yêu cầu.', 'Đi 45 km với vận tốc 30 km/giờ. Hết bao lâu?', '1,5 giờ, tức 1 giờ 30 phút.', 17]],
    ['data', 'Thống kê và xác suất', 'data',
      ['data', 'Đọc bảng số liệu và biểu đồ hình quạt tròn', 'Mỗi phần hình quạt biểu thị một nhóm. Cả hình tròn ứng với 100% số liệu.', 'Trong 40 bạn, nhóm thích bóng đá chiếm 25%. Có bao nhiêu bạn trong nhóm?', '40 × 0,25 = 10 bạn.', 19],
      ['chance', 'Tỉ số số lần xuất hiện trong thực nghiệm', 'Ghi số lần một kết quả xảy ra và tổng số lần thử. Lập tỉ số giữa hai số đó.', 'Rút thẻ 20 lần, có 7 lần rút được đỏ. Viết tỉ số số lần rút được đỏ trên tổng số lần thử.', '7/20.']],
    ['review-year', 'Ôn tập cuối năm', 'review',
      ['mixed', 'Ôn tập và vận dụng', 'Tách bài toán thành các câu hỏi nhỏ. Kiểm tra số đo và dùng ước lượng để so sánh với kết quả tính.', 'Một phòng có diện tích 24 m². Trải thảm lên 25% diện tích. Tính diện tích thảm.', '24 × 0,25 = 6 m².']],
  ],
};

// Short self-checks for lessons without a matching exercise in the guided catalog.
const shortPractice: Partial<Record<string, LessonQuestion>> = {
  'grade-1-number-10-count': ['Có 3 bút đỏ và 2 bút xanh. Đếm tất cả số bút.', '5 bút.'],
  'grade-1-number-10-compare': ['Xếp 8, 2, 6 từ bé đến lớn.', '2, 6, 8.'],
  'grade-1-number-10-split': ['Tách 9 thành 4 và số nào?', '5, vì 4 + 5 = 9.'],
  'grade-1-shapes-solid': ['Một hộp giày thường giống khối nào?', 'Khối hộp chữ nhật.'],
  'grade-1-number-100-compare-100': ['Điền dấu vào 52 … 47.', '52 > 47, vì 5 chục nhiều hơn 4 chục.'],
  'grade-2-number-1000-place': ['Viết số gồm 6 trăm, 0 chục và 4 đơn vị.', '604.'],
  'grade-2-geometry-shapes': ['Lon nước và viên bi, vật nào có dạng khối trụ?', 'Lon nước.'],
  'grade-2-measure-length': ['Đổi 5 m sang xăng-ti-mét.', '5 × 100 = 500 cm.'],
  'grade-2-data-chance': ['Hộp chỉ có thẻ đỏ. Rút một thẻ được màu đỏ có chắc chắn không?', 'Chắc chắn.'],
  'grade-3-review-number': ['Tìm số còn thiếu: 236 + … = 500.', '500 − 236 = 264.'],
  'grade-3-review-tables': ['Có 7 rổ, mỗi rổ 3 quả. Tính số quả.', '3 × 7 = 21 quả.'],
  'grade-3-shapes-points': ['N là trung điểm của CD, CD dài 12 cm. CN dài bao nhiêu?', '12 : 2 = 6 cm.'],
  'grade-3-shapes-circle': ['Đường kính 14 cm. Tính bán kính.', '14 : 2 = 7 cm.'],
  'grade-3-shapes-angles': ['Hình tam giác và hình tứ giác có số cạnh hơn kém nhau bao nhiêu?', '4 − 3 = 1 cạnh.'],
  'grade-3-shapes-solids': ['Một khối hộp chữ nhật có bao nhiêu đỉnh?', '8 đỉnh.'],
  'grade-3-measure-units': ['Túi thứ nhất nặng 350 g và túi thứ hai nặng 200 g. Hai túi nặng bao nhiêu?', '350 + 200 = 550 g.'],
  'grade-3-review-one-mixed': ['Một sợi dây dài 1 m. Cắt đi 25 cm thì còn bao nhiêu?', '100 − 25 = 75 cm.'],
  'grade-3-number-10000-place': ['Viết số gồm 6 nghìn, 8 trăm, 0 chục và 2 đơn vị.', '6.802.'],
  'grade-3-number-10000-round': ['Làm tròn 5.642 đến hàng trăm. Viết số 9 bằng chữ số La Mã.', '5.600 và IX.'],
  'grade-3-area-square-unit': ['Một hình phủ vừa 12 ô vuông cạnh 1 cm. Tính diện tích.', '12 cm².'],
  'grade-3-area-apply': ['Vườn dài 9 m, rộng 4 m. Cần bao nhiêu mét hàng rào để rào kín vườn?', '(9 + 4) × 2 = 26 m.'],
  'grade-3-operations-10000-add-subtract': ['Tính 7.020 − 2.368.', '4.652.'],
  'grade-3-operations-10000-multiply-divide': ['Tính 1.236 × 4.', '4.944.'],
  'grade-3-number-100000-place': ['Chữ số 7 trong 37.014 có giá trị bao nhiêu?', '7.000.'],
  'grade-3-number-100000-round': ['Làm tròn 74.216 đến hàng chục nghìn.', '70.000, vì chữ số hàng nghìn là 4.'],
  'grade-3-add-subtract-100000-add': ['Tính 48.576 + 32.847.', '81.423.'],
  'grade-3-add-subtract-100000-subtract': ['Tính 65.002 − 37.458.', '27.544.'],
  'grade-3-multiply-divide-100000-multiply': ['Tính 12.408 × 5.', '62.040.'],
  'grade-3-multiply-divide-100000-divide': ['Tính 48.024 : 6.', '8.004.'],
  'grade-3-data-chance': ['Gieo một xúc xắc có các mặt từ 1 đến 6. Kết quả nào có thể xảy ra trong hai số 5 và 8?', '5.'],
  'grade-3-review-year-mixed': ['Một kệ có 24 sách. Chia đều số sách vào 4 ngăn. Mỗi ngăn có bao nhiêu quyển?', '24 : 4 = 6 quyển.'],
  'grade-4-numbers-place': ['Chữ số 4 trong 9.432.017 thuộc hàng nào, lớp nào?', 'Hàng trăm nghìn, lớp nghìn.'],
  'grade-4-numbers-round': ['Số 24.975 là số chẵn hay lẻ? Làm tròn số đó đến hàng chục nghìn.', 'Số lẻ. Làm tròn được 20.000.'],
  'grade-4-operations-expression': ['Tính 2 × a + b với a = 6 và b = 9.', '2 × 6 + 9 = 21.'],
  'grade-4-shapes-angle': ['Góc 45° là góc gì?', 'Góc nhọn, vì nhỏ hơn 90°.'],
  'grade-4-shapes-lines': ['Hai cạnh dài ở phía đối diện của hình chữ nhật có quan hệ gì?', 'Song song.'],
  'grade-4-measure-time-area': ['Đổi 2 phút 15 giây ra giây.', '2 × 60 + 15 = 135 giây.'],
  'grade-4-fractions-compare': ['So sánh 2/3 và 3/4.', '2/3 = 8/12 và 3/4 = 9/12, vậy 2/3 < 3/4.'],
  'grade-4-data-chance': ['Gieo xúc xắc 12 lần. Mặt 6 xuất hiện 3 lần. Các mặt khác xuất hiện tổng cộng mấy lần?', '12 − 3 = 9 lần.'],
  'grade-5-review-natural': ['Tính nhẩm 35 × 9 + 35 × 11.', '35 × (9 + 11) = 700.'],
  'grade-5-decimals-read': ['So sánh 6,08 và 6,8.', '6,08 < 6,80, nên 6,08 < 6,8.'],
  'grade-5-decimals-round': ['Làm tròn 7,684 đến hàng phần mười.', '7,7, vì chữ số hàng phần trăm là 8.'],
  'grade-5-ratios-ratio': ['Bản đồ có tỉ lệ 1 : 2.000. Đo được 3 cm trên bản đồ. Thực tế dài bao nhiêu mét?', '3 × 2.000 = 6.000 cm, tức 60 m.'],
  'grade-5-solids-surface': ['Hình hộp dài 5 cm, rộng 3 cm, cao 2 cm. Tính diện tích xung quanh.', '(5 + 3) × 2 × 2 = 32 cm².'],
  'grade-5-solids-volume-units': ['Đổi 2 m³ sang đề-xi-mét khối.', '2 × 1.000 = 2.000 dm³.'],
  'grade-5-motion-time-units': ['Đổi 2 phút 45 giây sang giây.', '2 × 60 + 45 = 165 giây.'],
  'grade-5-data-chance': ['Tung đồng xu 25 lần, có 11 lần mặt sấp. Tỉ số số lần mặt ngửa trên tổng số lần tung là bao nhiêu?', '(25 − 11)/25 = 14/25.'],
  'grade-5-review-year-mixed': ['Mảnh vườn hình vuông cạnh 10 m. Trồng rau trên 35% diện tích. Diện tích trồng rau là bao nhiêu?', '10 × 10 × 0,35 = 35 m².'],
};

export function primaryGrade(value: unknown): PrimaryGrade | undefined {
  return value === 1 || value === 2 || value === 3 || value === 4 || value === 5 ? value : undefined;
}

export function getPrimaryChapters(grade: PrimaryGrade): PrimaryChapter[] {
  const practiceById = new Map(getProblemsByGrade(grade).map(problem => [problem.id, problem]));
  return chapterSeeds[grade].map(([chapterId, title, icon, ...lessons]) => {
    const id = `grade-${grade}-${chapterId}`;
    return {
      id, title, icon,
      lessons: lessons.map(([lessonId, lessonTitle, explanation, example, answer, ...practiceNumbers]) => {
        const fullId = `${id}-${lessonId}`;
        const [advanced, ...addedPractice] = lessonSupplements[fullId];
        const existingShortPractice = shortPractice[fullId];
        return {
          id: fullId, title: lessonTitle, explanation,
          examples: [[example, answer], advanced],
          practice: practiceNumbers.flatMap(number => {
            const problem = practiceById.get(`grade${grade}_prob${number}`);
            return problem ? [problem] : [];
          }),
          selfPractice: existingShortPractice ? [existingShortPractice, ...addedPractice] : addedPractice,
        };
      }),
    };
  });
}

export function foldLessonSearch(text: string): string {
  return text.toLocaleLowerCase('vi').normalize('NFD').replace(/\p{Diacritic}/gu, '').replace(/đ/g, 'd').trim();
}

export function matchesPrimaryLesson(chapter: PrimaryChapter, lesson: PrimaryLesson, keyword: string): boolean {
  return foldLessonSearch(`${chapter.title} ${lesson.title} ${lesson.practice.map(problem =>
    `${problem.title} ${problem.topic} ${problem.problemText}`).join(' ')}`).includes(keyword);
}

/**
 * MathVision Kids — Primary School Math Curriculum Sample Library
 * Program: Chương trình Giáo dục Phổ thông 2018 (SGK Cánh Diều & Kết Nối Tri Thức)
 * Grades: Lớp 1, 2, 3, 4, 5
 */

export interface CurriculumProblem {
  id: string;
  grade: 1 | 2 | 3 | 4 | 5;
  bookSeries: 'Cánh Diều' | 'Kết Nối Tri Thức';
  topic: string;
  title: string;
  problemText: string;
  guidance: string;
  sampleSolution: {
    lines: string[];
    finalAnswer: string;
  };
  difficulty: 'Dễ' | 'Trung bình' | 'Thử thách';
}

export const PRIMARY_MATH_CURRICULUM: CurriculumProblem[] = [
  // ================= LỚP 1 =================
  {
    id: 'grade1_prob1',
    grade: 1,
    bookSeries: 'Cánh Diều',
    topic: 'Phép cộng trong phạm vi 100 (không nhớ)',
    title: 'Bài toán thêm hoa vào lọ',
    problemText: 'Trong lọ có 15 bông hoa. Mẹ cắm thêm 4 bông hoa nữa. Hỏi trong lọ có tất cả bao nhiêu bông hoa?',
    guidance: 'Muốn biết trong lọ có tất cả bao nhiêu bông hoa, em lấy số hoa ban đầu cộng với số hoa mẹ cắm thêm.',
    sampleSolution: {
      lines: [
        'Bài giải',
        'Trong lọ có tất cả số bông hoa là:',
        '15 + 4 = 19 (bông hoa)',
        'Đáp số: 19 bông hoa',
      ],
      finalAnswer: '19 bông hoa',
    },
    difficulty: 'Dễ',
  },
  {
    id: 'grade1_prob2',
    grade: 1,
    bookSeries: 'Kết Nối Tri Thức',
    topic: 'Phép trừ trong phạm vi 100 (không nhớ)',
    title: 'Bài toán cho bớt viên bi',
    problemText: 'Nam có 28 viên bi. Nam cho bạn Việt 6 viên bi. Hỏi Nam còn lại bao nhiêu viên bi?',
    guidance: 'Muốn tìm số bi còn lại của Nam, em lấy tổng số bi Nam có trừ đi số bi đã cho Việt.',
    sampleSolution: {
      lines: [
        'Bài giải',
        'Nam còn lại số viên bi là:',
        '28 - 6 = 22 (viên bi)',
        'Đáp số: 22 viên bi',
      ],
      finalAnswer: '22 viên bi',
    },
    difficulty: 'Dễ',
  },

  // ================= LỚP 2 =================
  {
    id: 'grade2_prob1',
    grade: 2,
    bookSeries: 'Cánh Diều',
    topic: 'Bài toán về nhiều hơn (Phép cộng có nhớ)',
    title: 'Số học sinh nam lớp 2A',
    problemText: 'Lớp 2A có 18 bạn nữ. Số bạn nam nhiều hơn số bạn nữ là 5 bạn. Hỏi lớp 2A có bao nhiêu bạn nam?',
    guidance: 'Số bạn nam nhiều hơn số bạn nữ, vậy em lấy số bạn nữ cộng thêm phần nhiều hơn (5 bạn). Nhớ hàng chục khi cộng nhé!',
    sampleSolution: {
      lines: [
        'Bài giải',
        'Lớp 2A có số bạn nam là:',
        '18 + 5 = 23 (bạn)',
        'Đáp số: 23 bạn nam',
      ],
      finalAnswer: '23 bạn nam',
    },
    difficulty: 'Trung bình',
  },
  {
    id: 'grade2_prob2',
    grade: 2,
    bookSeries: 'Kết Nối Tri Thức',
    topic: 'Bài toán về ít hơn (Phép trừ có nhớ)',
    title: 'Độ dài đoạn thẳng CD',
    problemText: 'Đoạn thẳng AB dài 34 cm. Đoạn thẳng CD ngắn hơn đoạn thẳng AB là 8 cm. Hỏi đoạn thẳng CD dài bao nhiêu xăng-ti-mét?',
    guidance: 'Đoạn thẳng CD ngắn hơn AB, em thực hiện phép trừ độ dài đoạn AB cho 8 cm.',
    sampleSolution: {
      lines: [
        'Bài giải',
        'Đoạn thẳng CD dài số xăng-ti-mét là:',
        '34 - 8 = 26 (cm)',
        'Đáp số: 26 cm',
      ],
      finalAnswer: '26 cm',
    },
    difficulty: 'Trung bình',
  },

  // ================= LỚP 3 =================
  {
    id: 'grade3_prob1',
    grade: 3,
    bookSeries: 'Cánh Diều',
    topic: 'Bài toán giải bằng 2 bước tính (Gấp một số lên nhiều lần)',
    title: 'Cửa hàng bán gạo cả ngày',
    problemText: 'Một cửa hàng buổi sáng bán được 24 kg gạo. Buổi chiều bán được số gạo gấp 3 lần buổi sáng. Hỏi cả hai buổi cửa hàng bán được bao nhiêu ki-lô-gam gạo?',
    guidance: 'Bài toán gồm 2 bước tính: Bước 1 tìm số gạo bán buổi chiều (24 x 3). Bước 2 tính tổng số gạo cả hai buổi (lấy buổi sáng cộng buổi chiều).',
    sampleSolution: {
      lines: [
        'Bài giải',
        'Buổi chiều cửa hàng bán được số kg gạo là:',
        '24 x 3 = 72 (kg)',
        'Cả hai buổi cửa hàng bán được số kg gạo là:',
        '24 + 72 = 96 (kg)',
        'Đáp số: 96 kg gạo',
      ],
      finalAnswer: '96 kg gạo',
    },
    difficulty: 'Thử thách',
  },
  {
    id: 'grade3_prob2',
    grade: 3,
    bookSeries: 'Kết Nối Tri Thức',
    topic: 'Bài toán giải bằng 2 bước tính (Giảm đi một số lần)',
    title: 'Chia đều số kẹo cho các bạn',
    problemText: 'Thùng thứ nhất có 45 quyển vở. Thùng thứ hai có số vở giảm đi 3 lần so với thùng thứ nhất. Hỏi cả hai thùng có tất cả bao nhiêu quyển vở?',
    guidance: 'Bước 1: Tìm số vở ở thùng thứ hai (45 : 3). Bước 2: Tính tổng số vở cả hai thùng (cộng thùng thứ nhất và thùng thứ hai).',
    sampleSolution: {
      lines: [
        'Bài giải',
        'Thùng thứ hai có số quyển vở là:',
        '45 : 3 = 15 (quyển vở)',
        'Cả hai thùng có tất cả số quyển vở là:',
        '45 + 15 = 60 (quyển vở)',
        'Đáp số: 60 quyển vở',
      ],
      finalAnswer: '60 quyển vở',
    },
    difficulty: 'Thử thách',
  },

  // ================= LỚP 4 =================
  {
    id: 'grade4_prob1',
    grade: 4,
    bookSeries: 'Kết Nối Tri Thức',
    topic: 'Tìm hai số khi biết tổng và hiệu của hai số đó',
    title: 'Diện tích mảnh vườn hình chữ nhật',
    problemText: 'Một mảnh vườn hình chữ nhật có nửa chu vi là 48 m. Chiều dài hơn chiều rộng 12 m. Tính diện tích của mảnh vườn đó.',
    guidance: 'Bước 1: Tìm chiều dài = (Tổng + Hiệu) : 2. Bước 2: Tìm chiều rộng = Tổng - Chiều dài. Bước 3: Tính diện tích = Chiều dài x Chiều rộng.',
    sampleSolution: {
      lines: [
        'Bài giải',
        'Chiều dài mảnh vườn là:',
        '(48 + 12) : 2 = 30 (m)',
        'Chiều rộng mảnh vườn là:',
        '48 - 30 = 18 (m)',
        'Diện tích mảnh vườn là:',
        '30 x 18 = 540 (m2)',
        'Đáp số: 540 m2',
      ],
      finalAnswer: '540 m2',
    },
    difficulty: 'Thử thách',
  },
  {
    id: 'grade4_prob2',
    grade: 4,
    bookSeries: 'Cánh Diều',
    topic: 'Đặt tính rồi tính (Phép nhân và chia)',
    title: 'Đặt tính phép tính 3 chữ số',
    problemText: 'Đặt tính rồi tính phép tính sau ra vở: 356 + 128 = ?',
    guidance: 'Viết số 356 ở dòng trên, dấu + và số 128 ở dòng dưới sao cho các chữ số thẳng cột với nhau. Kẻ gạch ngang và cộng lần lượt từ phải sang trái.',
    sampleSolution: {
      lines: [
        '356',
        '+ 128',
        '---',
        '484',
      ],
      finalAnswer: '484',
    },
    difficulty: 'Trung bình',
  },

  // ================= LỚP 5 =================
  {
    id: 'grade5_prob1',
    grade: 5,
    bookSeries: 'Cánh Diều',
    topic: 'Diện tích hình tam giác (Số thập phân)',
    title: 'Diện tích tam giác có đáy và chiều cao thập phân',
    problemText: 'Một hình tam giác có độ dài đáy là 15 cm và chiều cao tương ứng là 8,4 cm. Tính diện tích của hình tam giác đó.',
    guidance: 'Diện tích hình tam giác bằng độ dài đáy nhân với chiều cao (cùng đơn vị đo) rồi chia cho 2: S = (a x h) : 2.',
    sampleSolution: {
      lines: [
        'Bài giải',
        'Diện tích của hình tam giác là:',
        '15 x 8.4 : 2 = 63 (cm2)',
        'Đáp số: 63 cm2',
      ],
      finalAnswer: '63 cm2',
    },
    difficulty: 'Trung bình',
  },
  {
    id: 'grade5_prob2',
    grade: 5,
    bookSeries: 'Kết Nối Tri Thức',
    topic: 'Toán chuyển động đều (Vận tốc, Quãng đường, Thời gian)',
    title: 'Vận tốc người đi xe máy',
    problemText: 'Một người đi xe máy khởi hành từ A lúc 7 giờ 30 phút và đến B lúc 9 giờ. Quãng đường AB dài 60 km. Tính vận tốc của xe máy theo đơn vị km/giờ.',
    guidance: 'Bước 1: Tìm thời gian đi = 9 giờ - 7 giờ 30 phút = 1 giờ 30 phút = 1,5 giờ. Bước 2: Vận tốc = Quãng đường : Thời gian = 60 : 1,5.',
    sampleSolution: {
      lines: [
        'Bài giải',
        'Thời gian người đó đi xe máy là:',
        '9 - 7.5 = 1.5 (giờ)',
        'Vận tốc của xe máy là:',
        '60 : 1.5 = 40 (km/giờ)',
        'Đáp số: 40 km/giờ',
      ],
      finalAnswer: '40 km/giờ',
    },
    difficulty: 'Thử thách',
  },
];

export function getProblemsByGrade(grade: 1 | 2 | 3 | 4 | 5): CurriculumProblem[] {
  return PRIMARY_MATH_CURRICULUM.filter((p) => p.grade === grade);
}

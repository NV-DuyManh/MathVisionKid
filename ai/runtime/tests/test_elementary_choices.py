import pytest
from app.tutoring import lesson
from app.tutoring.short_math import verified_plan
from unittest.mock import AsyncMock


CIRCLES = ('Hỗn số thích hợp biểu diễn số phần hình tròn được tô màu là: '
    '[Hình 1: chia 5 phần bằng nhau, 5 phần tô màu, 0 phần không tô màu. '
    'Hình 2: chia 5 phần bằng nhau, 5 phần tô màu, 0 phần không tô màu. '
    'Hình 3: chia 5 phần bằng nhau, 5 phần tô màu, 0 phần không tô màu. '
    'Hình 4: chia 5 phần bằng nhau, 1 phần tô màu, 4 phần không tô màu.] '
    'A. 1 (3)/(4) B. 3 (1)/(5) C. 4 (1)/(5) D. 3 (4)/(5)')
PENTAGONS = ('Hỗn số biểu diễn phần tô màu trong hình là: '
    'A. 1 (2)/(5) B. 5 (2)/(3) C. 2 (2)/(3) D. 2 (3)/(5)\n'
    'Hình vẽ gồm 2 hình ngũ giác. Hình ngũ giác bên trái được chia thành 5 phần bằng nhau và tô màu cả 5 phần. '
    'Hình ngũ giác bên phải được chia thành 5 phần bằng nhau và tô màu 2 phần.')
JUGS = ('Mỗi ca đựng một lượng nước như hình dưới đây: '
    '[4 ca nước. Ca 1: 1/45 ml. Ca 2: 1,5 l. Ca 3: 1400 ml. Ca 4: 1,45 l.] '
    'Ca nào đựng ít nước nhất? A. Ca số 1 B. Ca số 2 C. Ca số 3 D. Ca số 4')


CASES = [
    ('Câu 1: Khoanh vào chữ cái trước câu trả lời đúng. Tìm số tự nhiên để điền vào chỗ chấm sau: 15,21 > …… > 14,97 A. 15 B. 14 C. 13 D. 12', '15'),
    ('Dãy số nào được xếp theo thứ tự tăng dần: A. 2; 1 B. 3; 2 C. 1; 2 D. 4; 3', '1; 2'),
    ('a. Hai mươi bốn đơn vị, một phần mười, tám phần trăm được viết là: A. 24,18 B. 24,108 C. 24,018 D. 24,0108', '24,18'),
    ('Số thập phân gồm 7 chục, 3 đơn vị, 9 phần nghìn viết là: A. 73,9000 B. 73,009 C. 73,09 D. 73,0009', '73,009'),
    ('Câu 7. Từ năm tấm thẻ 0; 7; 2; 1 và dấu phẩy, có thể lập được tất cả bao nhiêu số thập phân có ba chữ số ở phần thập phân và các số đó bé hơn 1? A. 6 số B. 4 số C. 5 số D. 7 số', '6 số'),
    ('Câu 7. Từ năm tấm thẻ 0; 7; 2; 1 và , có thể lập được tất cả bao nhiêu số thập phân có ba chữ số ở phần thập phân và các số đó bé hơn 1? A. 6 số B. 4 số C. 5 số D. 7 số', '6 số'),
    ('c. Tìm số tự nhiên để điền vào chỗ chấm sau: 15,21 > ...... > 14,97 A. 15 B. 14 C. 13 D. 12', '15'),
    ('Phân số nào dưới đây là phân số thập phân? A. 100/57 B. 65/100 C. 15/20 D. 30/35', '65/100'),
    ('Phân số 183/100 viết ở dạng hỗn số là: A. 3 18/100 B. 18 3/100 C. 1 83/100 D. 180 3/100', '1 83/100'),
    ('Hỗn số 2 15/100 chuyển thành số thập phân là: A. 2,15 B. 2,015 C. 215,015 D. 21,5', '2,15'),
    ('Hỗn số 31 5/100 được viết dưới dạng số thập phân là: A. 31,05 B. 31,5 C. 5,31 D. 3,15', '31,05'),
    ('Số thập phân 5,18 được viết dưới dạng hỗn số là: A. 518 1/100 B. 18 5/100 C. 5 18/100 D. 51 8/100', '5 18/100'),
    ('Chữ số 6 trong số thập phân 105,026 có giá trị là: A. 6 B. 0,6 C. 0,06 D. 0,006', '0,006'),
    ('Chữ số 1 trong số thập phân 23,012 có giá trị là: A. 1/10 B. 1 C. 1/100 D. 1/1000', '1/100'),
    ('Số thập phân bé nhất trong các số 241,25; 241,205; 240,98; 240,908 là: A. 241,25 B. 241,205 C. 240,98 D. 240,908', '240,908'),
    ('Sắp xếp các số thập phân 1,25; 0,98; 3,56; 2,014 theo thứ tự từ bé đến lớn là: A. 1,25; 3,56; 0,98; 2,014 B. 3,56; 2,014; 1,25; 0,98 C. 0,98; 1,25; 2,014; 3,56 D. 2,014; 0,98; 3,56; 1,25', '0,98; 1,25; 2,014; 3,56'),
    ('Dãy số nào được xếp theo thứ tự tăng dần? A. 0,74; 0,705; 1,13; 2,03 B. 6; 6,5; 6,12; 6,98 C. 7,08; 7,11; 7,5; 7,503 D. 9,03; 9,07; 9,13; 9,108', '7,08; 7,11; 7,5; 7,503'),
    ('Bạn Mai nặng 35,6 kg. Cân nặng của bạn Mai khi làm tròn đến số tự nhiên gần nhất là: A. 35 kg B. 36 kg C. 35,7 kg D. 37 kg', '36 kg'),
    ('Số 0,158 làm tròn đến hàng phần mười ta được: A. 0,17 B. 0,159 C. 0,16 D. 0,2', '0,2'),
    ('Số thập phân 25,409 đọc là: A. Hai mươi lăm phẩy bốn mươi chín B. Hai mươi lăm phẩy bốn trăm linh chín C. Hai lăm phẩy bốn không chín D. Hai mươi lăm bốn không chín', 'Hai mươi lăm phẩy bốn trăm linh chín'),
]


@pytest.mark.parametrize('source,expected', CASES)
def test_number_concepts_use_exact_source_and_pass_existing_guards(source, expected):
    plan = lesson.Plan.model_validate(verified_plan(source))
    lesson.validate_plan(plan,lesson.LessonRequest(owner='exam',problemText=source,problemConfirmed=True),lesson.formula_constants(source))
    assert plan.steps[0].correctChoice == expected


@pytest.mark.parametrize('source', [
    'Chữ số 1 trong số thập phân 11,1 có giá trị là: A. 1 B. 10 C. 1/10 D. 100',
    'Phân số nào dưới đây là phân số thập phân? A. 1/10 B. 2/100 C. 3/4 D. 2/3',
    'Số 0,158 làm tròn đến hàng phần mười ta được: A. 0,2 B. 0,20 C. 0,1 D. 1',
    'Số thập phân 2,15 được viết dưới dạng hỗn số là: A. 2 15/100 B. 2 3/20 C. 21 5/10 D. 1 1/10. Tăng thêm 3 đơn vị.',
    'Số thập phân bé nhất trong các số 1; 2; 3 là: A. 1 B. 2 C. 3 D. 4. Không chọn số 1.',
    'Phân số 200/100 viết ở dạng hỗn số là: A. 2 0/100 B. 1 0/100 C. 3 0/100 D. 4 0/100',
    'Số thập phân 0,04 đọc là: A. Không phẩy bốn B. Không phẩy không bốn C. Bốn phẩy không D. Bốn',
])
def test_ambiguous_duplicate_or_extra_conditions_still_require_review(source):
    assert verified_plan(source) is None


@pytest.mark.asyncio
@pytest.mark.parametrize('source,expected', [
    (CIRCLES, '3 1/5'),
    (CIRCLES.replace('1 phần tô màu, 4 phần không tô màu', '4 phần tô màu, 1 phần không tô màu'), '3 4/5'),
    (PENTAGONS, '1 2/5'),
    (JUGS, 'Ca số 1'),
    (JUGS.replace('1/45 ml', '1500 ml'), 'Ca số 3'),
])
async def test_explicit_diagram_transcript_uses_all_counts_and_units(source, expected, monkeypatch):
    monkeypatch.setattr('app.tutoring.catalog.load_plan', lambda _: None)
    monkeypatch.setattr('app.tutoring.catalog.save_plan', lambda *args: None)
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(side_effect=AssertionError('Confirmed diagram proof')))
    response = await lesson.start_lesson(lesson.LessonRequest(owner='diagram', problemText=source, problemConfirmed=True))
    assert expected in response.step.choices
    response = lesson.answer_lesson(lesson.TurnRequest(owner='diagram', sessionId=response.sessionId, revision=response.revision, answer=expected))
    assert response.status == 'COMPLETE' and response.completed[-1].answer == expected


@pytest.mark.parametrize('source', [
    CIRCLES.replace('Hình 4: chia 5 phần bằng nhau, 1 phần tô màu, 4 phần không tô màu.', 'Hình 4: không rõ.'),
    CIRCLES.replace('1 phần tô màu, 4 phần không tô màu', '1 phần tô màu, 3 phần không tô màu'),
    CIRCLES.replace('Hình 4:', 'Hình 5:'),
    PENTAGONS.replace('tô màu 2 phần.', 'tô màu [?] phần.'),
    PENTAGONS.replace('bên phải được chia thành 5', 'bên phải được chia thành 0'),
    JUGS.replace('Ca 1: 1/45 ml', 'Ca 1: 1400 ml'),
    JUGS.replace('Ca 1: 1/45 ml', 'Ca 1: 1/45'),
    JUGS.replace('Ca 4: 1,45 l.', ''),
    JUGS + ' Chỉ xét hai ca cuối.',
])
def test_incomplete_or_inconsistent_diagram_transcripts_still_need_review(source):
    assert verified_plan(source) is None

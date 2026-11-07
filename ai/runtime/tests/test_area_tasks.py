from unittest.mock import AsyncMock
from fractions import Fraction

import pytest

from app.tutoring import lesson
from app.tutoring.short_math import verified_plan


RECTANGLE = ('Câu 6. Một khu đất dạng hình chữ nhật có chiều dài 210 m, chiều rộng bằng 5/7 chiều dài. '
    'Hỏi khu đất đó có diện tích là bao nhiêu héc-ta?')
ONE_SHARE = ('Người ta muốn xây dựng một khu chung cư trên mảnh đất có diện tích 3 ha. '
    'Trong đó 2/5 diện tích đất được dùng để xây các tòa nhà. Diện tích còn lại làm hồ điều hòa và khu vui chơi. '
    'Tính diện tích làm hồ điều hòa và khu vui chơi theo đơn vị mét vuông.')
TWO_SHARES = ('Bác Sơn có 1,5 ha đất. Bác đã dùng 7/10 mảnh đất để trồng cà phê, 1/5 diện tích đất để trồng điều. '
    'Phần đất còn lại để xây nhà. Hỏi bác Sơn dùng bao nhiêu mét vuông đất để xây nhà?')
FLOOR = ('Một nền nhà hình chữ nhật có chiều dài 8m, chiều rộng bằng 1/2 chiều dài. '
    'Người ta lát nền nhà đó bằng các viên gạch hình vuông cạnh 4dm. '
    'a) Hỏi cần mua bao nhiêu viên gạch để lát kín nền nhà đó? '
    'b) Biết rằng 2m² loại gạch đó giá 250 000 đồng, hỏi cần bao nhiêu tiền để lát nền nhà? '
    '(Diện tích phần mạch vữa không đáng kể).')
HARVEST = ('Một mảnh ruộng hình chữ nhật có chiều dài 45m, chiều rộng bằng 4/5 chiều dài. '
    'a. Tính diện tích mảnh ruộng đó? b. Người ta trồng sắn trên mảnh ruộng đó, '
    'biết rằng cứ 10m² thì thu hoạch được 50kg sắn. Hỏi trên cả mảnh ruộng đó thu hoạch được bao nhiêu tạ sắn?')
WOOD = ('Chú Minh thuê một số người thợ lát sàn gỗ cho nền nhà hình chữ nhật dài 9 m và chiều rộng 7m. '
    'Cứ 3m² sàn gỗ phải trả 930 000 đồng (gồm cả tiền sàn gỗ và tiền công). '
    'Hỏi chú Minh cần trả bao nhiêu tiền để lát nền căn nhà đó.')
DIFFERENCE = ('Tổng diện tích hai mảnh đất trồng khoai tây và ngô là 1ha 300m². '
    'Diện tích mảnh đất trồng khoai tây nhỏ hơn diện tích mảnh đất trồng ngô là500 m². '
    'Vậy diện tích mảnh đất trồng khoai tây là:')


@pytest.mark.asyncio
@pytest.mark.parametrize('source,answers', [
    (RECTANGLE, ['150', '31500', '63/20']),
    (RECTANGLE + ' A. 3,15 ha B. 15 ha C. 31,5 ha D. 1,5 ha', ['150', '31500', '63/20', '3,15 ha']),
    (RECTANGLE.replace('210', '140'), ['100', '14000', '7/5']),
    (ONE_SHARE, ['3/5', '30000', '18000']),
    (ONE_SHARE.replace('3 ha', '2,5 ha').replace('2/5', '1/4'), ['3/4', '25000', '18750']),
    (TWO_SHARES, ['1/10', '15000', '1500']),
    (TWO_SHARES.replace('Sơn', 'Lan').replace('1,5 ha', '2 ha'), ['1/10', '20000', '2000']),
])
async def test_exact_area_sources_preserve_units_and_complete_without_provider(source, answers, monkeypatch):
    monkeypatch.setattr('app.tutoring.catalog.load_plan', lambda _: None)
    monkeypatch.setattr('app.tutoring.catalog.save_plan', lambda *args: None)
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(side_effect=AssertionError('Exact area proof')))
    request = lesson.LessonRequest(owner='area-proof', problemText=source, problemConfirmed=True)
    response = await lesson.start_lesson(request)
    assert len(response.outline) == len(answers)
    for answer in answers:
        response = lesson.answer_lesson(lesson.TurnRequest(owner=request.owner, sessionId=response.sessionId,
            revision=response.revision, answer=answer))
    assert response.status == 'COMPLETE'
    assert response.conclusion.startswith('Đáp số:')
    assert [step.unit for step in response.completed[:3]] == (['m', 'm²', 'ha'] if source.startswith('Câu 6.') else ['phần', 'm²', 'm²'])
    # Check independent exact expected answers, allowing terminating decimal display.
    for completed, expected in zip(response.completed, answers):
        if completed.expression:
            assert Fraction(completed.answer.replace(',', '.')) == Fraction(expected)
        else:
            assert completed.answer == expected


@pytest.mark.parametrize('source', [
    RECTANGLE + ' Trừ đi diện tích ao 20 m².',
    RECTANGLE.replace('210 m', '210 cm'),
    RECTANGLE.replace('210 m', '0 m'),
    RECTANGLE.replace('5/7', '8/7'),
    RECTANGLE.replace('5/7', '[?]'),
    RECTANGLE + ' A. 3,15 m² B. 15 m² C. 31,5 m² D. 1,5 m²',
    RECTANGLE + ' A. 3,15 ha B. 3,150 ha C. 31,5 ha D. 1,5 ha',
    RECTANGLE + ' A. 2,15 ha B. 15 ha C. 31,5 ha D. 1,5 ha',
    ONE_SHARE.replace('2/5', '5/5'),
    ONE_SHARE.replace('3 ha', '0 ha'),
    ONE_SHARE + ' A. 18000 B. 17000 C. 16000 D. 15000',
    TWO_SHARES.replace('1/5', '3/10'),
    TWO_SHARES.replace('1/5', '2/5'),
    TWO_SHARES.replace('bác Sơn dùng', 'bác Nam dùng'),
    TWO_SHARES.replace('1,5 ha', '1,5'),
])
def test_extra_conditions_ambiguous_options_or_missing_units_need_review(source):
    assert verified_plan(source) is None


@pytest.mark.asyncio
@pytest.mark.parametrize('source,answers,units', [
    (FLOOR, ['4', '32', '16', '200', '4000000'], ['m', 'm²', 'dm²', 'viên', 'đồng']),
    (FLOOR.replace('8m', '12m'), ['6', '72', '16', '450', '9000000'], ['m', 'm²', 'dm²', 'viên', 'đồng']),
    (HARVEST, ['36', '1620', '8100', '81'], ['m', 'm²', 'kg', 'tạ']),
    (HARVEST.replace('45m', '50m'), ['40', '2000', '10000', '100'], ['m', 'm²', 'kg', 'tạ']),
    (WOOD, ['63', '19530000'], ['m²', 'đồng']),
    (WOOD + ' A. 16 740 000 đồng B. 19 530 000 đồng C. 14 880 000 đồng D. 27 900 000 đồng',
     ['63', '19530000', '19530000 đồng'], ['m²', 'đồng', 'đồng']),
    (DIFFERENCE, ['4900'], ['m²']),
    (DIFFERENCE + ' A. 4 900 m² B. 5 400 m² C. 5 600 m² D. 1 800 m²', ['4900 m²'], ['m²']),
])
async def test_area_rate_and_both_requested_subparts_use_original_values(source, answers, units, monkeypatch):
    monkeypatch.setattr('app.tutoring.catalog.load_plan', lambda _: None)
    monkeypatch.setattr('app.tutoring.catalog.save_plan', lambda *args: None)
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(side_effect=AssertionError('Exact area/rate proof')))
    response = await lesson.start_lesson(lesson.LessonRequest(owner='area-rate', problemText=source, problemConfirmed=True))
    assert len(response.outline) == len(answers)
    for answer in answers:
        response = lesson.answer_lesson(lesson.TurnRequest(owner='area-rate', sessionId=response.sessionId,
            revision=response.revision, answer=answer))
    assert response.status == 'COMPLETE'
    assert [step.unit for step in response.completed] == units
    for completed, expected in zip(response.completed, answers):
        if completed.expression:
            assert Fraction(completed.answer.replace(',', '.')) == Fraction(expected)
        else:
            assert completed.answer == expected


@pytest.mark.parametrize('source', [
    FLOOR.replace('4dm', '3dm'),  # Requires reasoning about cuts/rounding.
    FLOOR.replace('4dm', '0dm'),
    FLOOR.replace('2m²', '2m'),
    FLOOR.replace('không đáng kể', 'rộng hai xăng ti mét'),
    HARVEST.replace('50kg', '50'),
    HARVEST.replace('10m²', '0m²'),
    HARVEST + ' Để lại 10 kg sắn.',
    WOOD.replace('chú Minh cần', 'chú Lan cần'),
    WOOD.replace('3m²', '0m²'),
    WOOD + ' Sau đó được giảm giá.',
    WOOD + ' A. 19530000 kg B. 1 kg C. 2 kg D. 3 kg',
    DIFFERENCE.replace('300m²', '300kg'),
    DIFFERENCE.replace('là500', 'là10300'),
    DIFFERENCE + ' Bớt thêm 300 mét vuông làm đường.',
])
def test_rate_units_and_extra_conditions_are_required(source):
    assert verified_plan(source) is None

"""Speech pronunciation regressions retained after removing movies."""
import pytest

def test_spoken_math_preserves_fraction_and_operation_meaning():
    from app.tutoring.speech_render import spoken_math
    assert spoken_math('1/3 + 2/5 = 11/15')=='1 phần 3 cộng 2 phần 5 bằng 11 phần 15'
    assert 'chia' in spoken_math('16 : (4/15)')
    assert spoken_math('(12 + 6) / 3 = 6')=='mở ngoặc 12 cộng 6 đóng ngoặc chia 3 bằng 6'
    assert 'mở ngoặc 1 phần 3 cộng 2 phần 5 đóng ngoặc' in spoken_math('1 - (1/3+2/5)')
    assert spoken_math('-5 + 8')=='âm 5 cộng 8'
    assert 'xăng ti mét vuông' in spoken_math('Diện tích là 32 cm².')


@pytest.mark.parametrize('source, expected', [
    ('5 × -2 = -10', '5 nhân âm 2 bằng âm 10'),
    ('5 * -2 = -10', '5 nhân âm 2 bằng âm 10'),
    ('12 ÷ -3 = -4', '12 chia âm 3 bằng âm 4'),
    ('5 + -2 = 3', '5 cộng âm 2 bằng 3'),
    ('3 kg và 15 cm', '3 ki lô gam và 15 xăng ti mét'),
    ('5dm² và 3 mm³', '5 đề xi mét vuông và 3 mi li mét khối'),
    ('8 (cm²)', '8 xăng ti mét vuông'),
    ('250 ml và 2 l', '250 mi li lít và 2 lít'),
    ('(12 + 8) × 2 = 40', 'mở ngoặc 12 cộng 8 đóng ngoặc nhân 2 bằng 40'),
    ('Điểm (M) nằm trong hình', 'Điểm mở ngoặc M đóng ngoặc nằm trong hình'),
    ('gam, làm, lớp và 3kg', 'gam, làm, lớp và 3 ki lô gam'),
])
def test_nam_pronunciation_selection_preserves_operands_and_word_boundaries(source, expected):
    from app.tutoring.speech_render import spoken_math
    assert spoken_math(source) == expected

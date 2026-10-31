import pytest
from app.tutoring import lesson, media_preparation, speech_render, narration


@pytest.mark.parametrize('text,expected', [
    ('Bài 3: (2 điểm), 2 đề-xi-mét', 'Bài 3. 2 đề xi mét'),
    ('Bài 3: (2 điểm). 2 đề-xi-mét', 'Bài 3. 2 đề xi mét'),
    ('2 đề-xi-mét và 30 xăng-ti-mét', '2 đề xi mét và 30 xăng ti mét'),
    ('3 ki-lô-gam và 1 mi-li-lít', '3 ki lô gam và 1 mi li lít'),
    ('2 (đề-xi-mét vuông)', '2 đề xi mét vuông'),
    ('2dm và 3cm²', '2 đề xi mét và 3 xăng ti mét vuông'),
    ('(12 + 8) × 2 = 40', 'nhóm 12 cộng 8, hết nhóm nhân 2 bằng 40'),
    ('(3)/(5) + (1)/(5)', '3 phần 5 cộng 1 phần 5'),
    ('5 - 2 = 3', '5 trừ 2 bằng 3'),
    ('32m2 và 4dm^2 và 2cm^{3}', '32 mét vuông và 4 đề xi mét vuông và 2 xăng ti mét khối'),
    ('8 x 4 = 32 (m2)', '8 nhân 4 bằng 32 mét vuông'),
    ('(3,5)/(2,5)', '3,5 phần 2,5'),
    ('3.5/2.5', '3.5 phần 2.5'),
    ('x + 3 = 5', 'x cộng 3 bằng 5'),
])
def test_natural_units_without_breaking_arithmetic_grouping(text, expected):
    assert speech_render.spoken_math(text) == expected


def test_source_only_reading_speech_is_specific_without_computing_answers():
    first = 'Lan có 7 bút xanh và 8 bút đỏ. Hỏi Lan có tất cả bao nhiêu bút?'
    other = 'Vườn cây có 1/3 số cây là táo và còn lại là cam. Hỏi số cây cam chiếm bao nhiêu phần?'
    a = lesson.source_understanding(first)
    b = lesson.source_understanding(other)
    a_script = media_preparation.script_for_step(a[0])
    b_script = media_preparation.script_for_step(b[0])
    assert a_script != b_script
    assert 'Lan có 7 bút xanh và 8 bút đỏ' in ' '.join(a_script)
    assert '1/3' in ' '.join(b_script)
    assert '15' not in ' '.join(a_script)
    assert '2/3' not in ' '.join(b_script)
    assert a[1].guidance != a[0].guidance


def test_async_voice_preparation_has_sixty_second_bound_without_long_http_wait():
    assert narration.PREPARATION_TIMEOUT_SECONDS == 60
    assert narration.PUBLIC_TIMEOUT_SECONDS < 40

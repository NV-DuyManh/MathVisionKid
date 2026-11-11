"""Independent synthetic circle drawings; no private exam image needed in CI."""
import asyncio
import io
from unittest.mock import AsyncMock, Mock

import cv2
import numpy as np
import pytest
from PIL import Image

from app.tutoring import diagram_reading as diagram
from app.tutoring import notebook
from app.tutoring.notebook import NotebookQuestion


def picture(shaded=(5, 5, 5, 1), *, fill=215, boundaries=True):
    pixels = np.full((200, len(shaded)*140+40, 3), 255, np.uint8)
    for index, count in enumerate(shaded):
        center = (90+index*140, 100)
        for sector in range(count):
            cv2.ellipse(pixels, center, (45, 45), 0, -90+sector*72, -90+(sector+1)*72, (fill,)*3, -1)
        cv2.circle(pixels, center, 45, (0, 0, 0), 2)
        if boundaries:
            for angle in np.deg2rad(np.arange(5)*72-90):
                end = tuple(np.rint(np.array(center)+45*np.array([np.cos(angle), np.sin(angle)])).astype(int))
                cv2.line(pixels, center, end, (0, 0, 0), 2)
    return pixels


@pytest.mark.parametrize('shaded', [(5, 5, 5, 1), (0, 2), (1, 4, 3)])
def test_counts_visible_sectors_in_each_circle_from_pixels(shaded):
    assert diagram.circle_facts(picture(shaded)) == [(5, n, 5-n) for n in shaded]


def test_faint_fill_missing_boundaries_and_non_diagrams_remain_unknown():
    assert diagram.circle_facts(picture(fill=245)) is None
    assert diagram.circle_facts(picture(boundaries=False)) is None
    assert diagram.circle_facts(picture((1,))) is None
    image = np.full((200, 600, 3), 255, np.uint8)
    cv2.putText(image, '5000 1000 8000', (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    assert diagram.circle_facts(image) is None


@pytest.mark.parametrize('diagram_text,recovered', [
    ('Hình 1: 5 phần tô màu. Hình 2: 5 phần tô màu. Hình 3: 5 phần tô màu. Hình 4: 3 phần tô màu.', True),
    ('Hình 1: 5 phần tô màu. Hình 3: 5 phần tô màu. Hình 4: 3 phần tô màu.', False),
    ('Hình 1: 5 phần tô màu. Hình 2: 5 phần tô màu. Hình 2: 5 phần tô màu. Hình 4: 3 phần tô màu.', False),
])
def test_numbered_circle_description_uses_the_visible_sectors_only(diagram_text, recovered):
    stem = 'Hỗn số biểu diễn số phần hình tròn được tô màu là:'
    choices = 'A. 1 3/4\nB. 3 1/5\nC. 4 1/5\nD. 3 4/5'
    source = NotebookQuestion(label='Câu 1', problemText=f'{stem}\n[{diagram_text}]\n{choices}')
    result, = asyncio.run(diagram.clarify_circles([source], picture(), 2))
    if recovered:
        assert 'Hình 4: chia 5 phần bằng nhau, 1 phần tô màu' in result.problemText
        assert result.problemText.startswith(stem) and result.problemText.endswith(choices)
        assert result.uncertain
    else:
        assert result is source


def test_clarification_preserves_question_choices_and_requires_confirmation(monkeypatch):
    question = NotebookQuestion(label='Câu 1', problemText='Chọn hỗn số. [4 hình tròn; hình cuối tô 3 phần.]\nA. 1 B. 2 C. 3 D. 4')
    other = NotebookQuestion(label='Câu 2', problemText='Tính 1+1=?')
    result = asyncio.run(diagram.clarify_circles([question, other], picture(), 1))
    assert result[0].problemText.startswith('Chọn hỗn số. [Hình 1:')
    assert 'Hình 4: chia 5 phần bằng nhau, 1 phần tô màu, 4 phần không tô màu.' in result[0].problemText
    assert result[0].problemText.endswith('A. 1 B. 2 C. 3 D. 4')
    assert result[0].uncertain and result[1] is other
    assert question.problemText != result[0].problemText  # Original source object untouched.
    missed = asyncio.run(diagram.clarify_circles([question], picture((5, 5, 1)), 1))
    assert missed == [question]
    no_brackets = question.model_copy(update={'problemText': 'Có các hình tròn. Chọn một hỗn số.'})
    detector = Mock(side_effect=AssertionError('Unrelated text must not run the detector'))
    monkeypatch.setattr(diagram, 'circle_facts', detector)
    assert asyncio.run(diagram.clarify_circles([no_brackets], picture(), 1)) == [no_brackets]


def pentagons(shaded=(5, 2), *, fill=(20, 130, 235), boundaries=True):
    pixels = np.full((220, len(shaded)*170+40, 3), 255, np.uint8)
    for index, count in enumerate(shaded):
        center = np.array([95+index*170, 110])
        angles = np.arange(5)*2*np.pi/5-np.pi/2
        vertices = np.rint(center+np.stack((65*np.cos(angles), 65*np.sin(angles)), axis=1)).astype(np.int32)
        for sector in range(count):
            cv2.fillConvexPoly(pixels, np.array([center, vertices[sector], vertices[(sector+1)%5]], np.int32), fill)
        cv2.polylines(pixels, [vertices], True, (60, 60, 60), 2)
        if boundaries:
            for vertex in vertices:
                cv2.line(pixels, tuple(center), tuple(vertex), (60, 60, 60), 2)
    return pixels


@pytest.mark.parametrize('shaded', [(5, 2), (0, 1), (4, 3, 2)])
def test_pentagon_facts_count_visible_radial_sectors_without_choices(shaded):
    assert diagram.pentagon_facts(pentagons(shaded)) == [(5, count, 5-count) for count in shaded]


def test_pentagons_reject_faint_fill_missing_dividers_skew_and_unrelated_diagrams():
    assert diagram.pentagon_facts(pentagons(fill=(248, 248, 248))) is None
    assert diagram.pentagon_facts(pentagons(boundaries=False)) is None
    assert diagram.pentagon_facts(pentagons((1,))) is None
    assert diagram.pentagon_facts(picture()) is None
    skewed = cv2.warpAffine(pentagons(), np.float32([[1, .35, 0], [0, .6, 0]]), (460, 220))
    assert diagram.pentagon_facts(skewed) is None


@pytest.mark.parametrize('description', [
    '[3 hình ngũ giác, 2 hình tô màu hoàn toàn, hình thứ 3 có 3 phần tô màu.]',
    'Hình vẽ gồm 3 hình ngũ giác đều, mỗi hình chia 5 phần bằng nhau: 2 hình tô màu hoàn toàn, hình cuối tô màu 3 phần.',
    'Hình gồm: hình thứ nhất là một hình ngũ giác đều được chia làm 5 phần bằng nhau, tất cả 5 phần đều tô màu; '
    'hình thứ hai là một hình ngũ giác đều được chia làm 5 phần bằng nhau, có 3 phần tô màu và 2 phần không tô màu.',
])
def test_pentagon_clarification_retains_stem_choices_and_other_questions(description):
    stem = 'Hỗn số biểu diễn phần tô màu trong hình là:'
    choices = 'A. 1 (2)/(5)\nB. 5 (2)/(3)\nC. 2 (2)/(3)\nD. 2 (3)/(5)'
    source = NotebookQuestion(label='Câu 1', problemText=f'{stem}\n{description}\n{choices}')
    other = NotebookQuestion(label='Câu 2', problemText='Tính 7/15 + 2/3')
    first, second = asyncio.run(diagram.clarify_pentagons([source, other], pentagons(), 1))
    assert first.problemText.startswith(stem) and first.problemText.endswith(choices)
    assert '[Hình 1: hình ngũ giác chia 5 phần bằng nhau, 5 phần tô màu, 0 phần không tô màu.' in first.problemText
    assert 'Hình 2: hình ngũ giác chia 5 phần bằng nhau, 2 phần tô màu, 3 phần không tô màu.' in first.problemText
    assert 'Hình 3' not in first.problemText
    assert first.uncertain and second is other and source.problemText != first.problemText


@pytest.mark.parametrize('description', [
    '[Hình ngũ giác ABCDE có 2 phần tô màu.]',
    '[Hình ngũ giác có cạnh 4 cm và 2 phần tô màu.]',
    '[Hình ngũ giác có 2 phần tô màu.]\n[Hình ngũ giác có 3 phần tô màu.]',
])
def test_polygon_annotations_and_ambiguous_groups_never_get_overwritten(monkeypatch, description):
    source = NotebookQuestion(label='Câu 1', problemText='Chọn hỗn số. '+description)
    detector = Mock(side_effect=AssertionError('Ambiguous descriptions cannot run the measurement'))
    monkeypatch.setattr(diagram, 'pentagon_facts', detector)
    assert asyncio.run(diagram.clarify_pentagons([source], pentagons(), 1)) == [source]


@pytest.mark.parametrize('description', [
    '[4 hình tròn có bán kính 3 cm, mỗi hình có 5 phần tô màu.]',
    '[4 hình tròn ABCD có 5 phần tô màu.]',
    '[4 hình tròn có 3+2 phần tô màu.]',
])
def test_circle_annotations_and_equations_stay_in_the_source(monkeypatch, description):
    source = NotebookQuestion(label='Câu 1', problemText='Chọn hỗn số. '+description)
    detector = Mock(side_effect=AssertionError('Annotated shapes cannot lose source data'))
    monkeypatch.setattr(diagram, 'circle_facts', detector)
    assert asyncio.run(diagram.clarify_circles([source], picture(), 1)) == [source]


@pytest.mark.parametrize('shape', ['pentagons', 'circles'])
def test_single_question_crops_receive_the_same_visual_checks_as_whole_pages(monkeypatch, shape):
    pixels = pentagons() if shape == 'pentagons' else picture()
    description = ('[3 hình ngũ giác, mỗi hình chia 5 phần bằng nhau, hình cuối có 3 phần tô màu.]'
                   if shape == 'pentagons' else '[4 hình tròn, mỗi hình chia 5 phần bằng nhau, hình cuối có 3 phần tô màu.]')
    source = 'Chọn hỗn số.\n'+description+'\nA. 1\nB. 2\nC. 3\nD. 4'
    cloud = AsyncMock(return_value={'kind': 'PROBLEM', 'problemText': source})
    monkeypatch.setattr(notebook, '_generate', cloud)
    buffer = io.BytesIO()
    Image.fromarray(cv2.cvtColor(pixels, cv2.COLOR_BGR2RGB)).save(buffer, 'PNG')
    result = asyncio.run(notebook.inspect_notebook(buffer.getvalue()))
    assert result.kind == 'PROBLEM' and not result.needsCrop
    assert result.problemText.startswith('Chọn hỗn số.') and result.problemText.endswith('A. 1\nB. 2\nC. 3\nD. 4')
    assert ('Hình 2: hình ngũ giác chia 5 phần bằng nhau, 2 phần tô màu, 3 phần không tô màu.' if shape == 'pentagons'
            else 'Hình 4: chia 5 phần bằng nhau, 1 phần tô màu, 4 phần không tô màu.') in result.problemText
    assert cloud.await_count == 1


def test_polygon_description_after_d_is_measured_and_moved_out_of_the_last_choice():
    from app.tutoring.choice_source import split_choices
    stem = 'Hỗn số biểu diễn phần tô màu trong hình là:'
    choices = 'A. 1 (2)/(5)\nB. 5 (2)/(3)\nC. 2 (2)/(3)\nD. 2 (3)/(5)'
    description = ('Hình vẽ gồm một hình ngũ giác đều được chia thành 5 tam giác bằng nhau, '
                   'trong đó 2 tam giác được tô màu cam.')
    source = NotebookQuestion(label='Câu 1', problemText=stem+'\n'+choices+'\n'+description)
    result, = asyncio.run(diagram.clarify_pentagons([source], pentagons(), 1))
    assert result.problemText.startswith(stem) and result.problemText.endswith(choices)
    assert result.problemText.index('[Hình 1:') < result.problemText.index('A.')
    assert 'Hình 2: hình ngũ giác chia 5 phần bằng nhau, 2 phần tô màu, 3 phần không tô màu.' in result.problemText
    parsed_stem, parsed_choices = split_choices(result.problemText, allow_statement=True)
    assert 'Hình 2' in parsed_stem and parsed_choices[-1] == '2 (3)/(5)'
    from app.tutoring.short_math import verified_plan
    plan = verified_plan(result.problemText)
    assert plan and plan['steps'][0]['correctChoice'] == '1 2/5'
    assert source.problemText.endswith(description)


def test_question_about_a_specific_colour_is_not_replaced_with_all_shaded_parts(monkeypatch):
    source = NotebookQuestion(label='Câu 1', problemText='Phần tô màu cam trong hình là bao nhiêu?\n'
        '[Hai hình ngũ giác được chia thành 5 phần bằng nhau, có 2 phần tô màu cam.]')
    detector = Mock(side_effect=AssertionError('Counting all colours cannot answer a colour-specific question'))
    monkeypatch.setattr(diagram, 'pentagon_facts', detector)
    assert asyncio.run(diagram.clarify_pentagons([source], pentagons(), 1)) == [source]


@pytest.mark.parametrize('description', [
    'Hình vẽ gồm một hình ngũ giác đều được chia thành 5 tam giác bằng nhau, trong đó 2 tam giác được tô màu cam.',
    '[Hình 1: hình ngũ giác chia 5 phần bằng nhau, 5 phần tô màu, 0 phần không tô màu. '
    'Hình 2: hình ngũ giác chia 5 phần bằng nhau, 2 phần tô màu, 3 phần không tô màu.]',
])
def test_grouped_subquestions_are_separated_before_associating_the_diagram(monkeypatch, description):
    from app.tutoring.choice_source import split_choices
    from app.tutoring.short_math import verified_plan
    source = ('Câu 1: Khoanh vào chữ cái trước câu trả lời đúng.\n'
        'a) Tính 1 + 1 = ?\nA. 1\nB. 2\nC. 3\nD. 4\n'
        'b) Hỗn số biểu diễn phần tô màu trong hình là:\n'
        'A. 1 (2)/(5)\nB. 5 (2)/(3)\nC. 2 (2)/(3)\nD. 2 (3)/(5)\n'+description)
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value={
        'kind': 'MULTIPLE', 'questions': [{'label': 'Câu 1', 'problemText': source}]}))
    buffer = io.BytesIO()
    Image.fromarray(cv2.cvtColor(pentagons(), cv2.COLOR_BGR2RGB)).save(buffer, 'PNG')
    result = asyncio.run(notebook.inspect_notebook(buffer.getvalue()))
    assert result.kind == 'MULTIPLE' and len(result.questions) == 2
    first, second = result.questions
    assert first.problemText.endswith('A. 1\nB. 2\nC. 3\nD. 4')
    assert 'Hình 1' not in first.problemText
    stem, choices = split_choices(second.problemText, allow_statement=True)
    assert 'Hình 2: hình ngũ giác chia 5 phần bằng nhau, 2 phần tô màu, 3 phần không tô màu.' in stem
    assert choices[-1] == '2 (3)/(5)'
    assert verified_plan(second.problemText)['steps'][0]['correctChoice'] == '1 2/5'

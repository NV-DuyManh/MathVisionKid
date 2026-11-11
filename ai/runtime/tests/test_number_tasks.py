from copy import deepcopy
from unittest.mock import AsyncMock

import pytest

from app.tutoring import lesson
from app.tutoring.number_tasks import verified_plan


CASES = [
    ('Bài 4: (1 điểm)\n(0,5 điểm) Các số tự nhiên thích hợp điền vào chỗ trống là: 60,36 < ... < 64,6', '61; 62; 63; 64'),
    ('Câu 1.\nViết các số 402,56; 402,6; 400,98; 402,07 theo thứ tự từ lớn đến bé.', '402,6; 402,56; 402,07; 400,98'),
    ('Câu 1.\nSố 100,281 làm tròn đến hàng phần mười được số:…………………', '100,3'),
    ('Câu 1. Viết số thập phân có:\nHai đơn vị, chín phần trăm:………………', '2,09'),
    ('Viết số thập phân có: Năm trăm, bốn đơn vị, năm phần mười, tám phần trăm:………………', '504,58'),
    ('Viết số thập phân có: Không đơn vị, bảy phần mười, sáu phần trăm, bốn phần nghìn:………………', '0,764'),
    ('Viết số thập phân có: Mười sáu đơn vị, ba mươi tám phần nghìn: ………………', '16,038'),
    ('Các số tự nhiên thích hợp điền vào chỗ trống là: 1 < ... < 3', '2'),
    ('Số 1,25 làm tròn đến hàng phần mười được số:……', '1,3'),
    ('Viết các số 4,2; 4,02; 4,002 theo thứ tự từ bé đến lớn.', '4,002; 4,02; 4,2'),
    ('Bài 1: (1 điểm) Điền số hoặc đơn vị thích vào chỗ chấm: 17 dm 2 cm = 17,2 ……', 'dm'),
    ('Điền số hoặc đơn vị thích hợp vào chỗ chấm: 5 tạ 7 kg = 0,507 …………', 'tấn'),
]


@pytest.mark.asyncio
@pytest.mark.parametrize('source,expected', CASES)
async def test_open_number_task_uses_exact_source_proof_and_existing_player_flow(source, expected, monkeypatch):
    monkeypatch.setattr('app.tutoring.catalog.load_plan', lambda _: None)
    monkeypatch.setattr('app.tutoring.catalog.save_plan', lambda *args: None)
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(side_effect=AssertionError('No provider needed')))
    request = lesson.LessonRequest(owner='open-number', problemText=source, problemConfirmed=True)
    response = await lesson.start_lesson(request)
    assert response.step.choices.count(expected) == 1
    assert not response.conclusion and expected not in response.step.explanation
    wrong = next(choice for choice in response.step.choices if choice != expected)
    retry = lesson.answer_lesson(lesson.TurnRequest(owner=request.owner, sessionId=response.sessionId, revision=response.revision, answer=wrong))
    assert retry.status != 'COMPLETE' and retry.stepIndex == 0
    complete = lesson.answer_lesson(lesson.TurnRequest(owner=request.owner, sessionId=response.sessionId, revision=retry.revision, answer=expected))
    assert complete.status == 'COMPLETE' and complete.completed[-1].answer == expected


@pytest.mark.parametrize('source,expected', CASES)
def test_generated_choice_permission_cannot_authorize_a_changed_key_or_operand(source, expected):
    original = verified_plan(source)
    assert original is not None
    request = lesson.LessonRequest(owner='proof', problemText=source, problemConfirmed=True)
    for change in ('key', 'option', 'operand'):
        raw = deepcopy(original)
        step = raw['steps'][0]
        if change == 'key':
            step['correctChoice'] = next(option for option in step['choices'] if option != expected)
        elif change == 'option':
            step['choices'][step['choices'].index(expected)] = '999999'
            step['correctChoice'] = '999999'
        elif change == 'operand':
            step.update(choices=[], correctChoice='', expression='999999+1')
        with pytest.raises(ValueError):
            lesson.validate_plan(lesson.Plan.model_validate(raw), request, lesson.formula_constants(source))
    leaking = lesson.Plan.model_validate(original)
    leaking.steps[0].explanation = 'Kết quả cần chọn là 999999.'
    lesson.validate_plan(leaking, request, lesson.formula_constants(source))
    assert '999999' not in leaking.steps[0].explanation


@pytest.mark.parametrize('source', [
    'Các số tự nhiên thích hợp điền vào chỗ trống là: 1 < ... < 999999',
    'Các số tự nhiên thích hợp điền vào chỗ trống là: 1,1 < ... < 1,2',
    'Các số tự nhiên thích hợp điền vào chỗ trống là: 1 < ... < 5. Chỉ lấy số chẵn.',
    'Viết các số 1; 2; 3 theo thứ tự từ bé đến lớn, bỏ số 2.',
    'Viết số thập phân có: Hai đơn vị, chín phần trăm, tám phần trăm:……',
    'Viết số thập phân có: Hai đơn vị, chín phần:……',
    'Số 100,281 làm tròn được số:……',
    'Viết số thập phân có: [?] đơn vị, chín phần trăm:……',
    'Điền số hoặc đơn vị thích hợp vào chỗ chấm: 0 m = 0 …………',
    'Điền số hoặc đơn vị thích hợp vào chỗ chấm: 7 m 3 kg = 0,507 …………',
])
def test_incomplete_or_extra_conditions_never_receive_an_exact_choice_proof(source):
    assert verified_plan(source) is None


@pytest.mark.asyncio
async def test_table_keeps_every_column_and_requested_row(monkeypatch):
    source = 'Câu 1. Hoàn thành bảng sau:\n| Phân số | Phân số thập phân | Số thập phân |\n| (7)/(20) | | |\n| (13)/(25) | | |\n| (3)/(125) | | |'
    monkeypatch.setattr('app.tutoring.catalog.load_plan', lambda _: None)
    monkeypatch.setattr('app.tutoring.catalog.save_plan', lambda *args: None)
    monkeypatch.setattr(lesson, 'generate_plan', AsyncMock(side_effect=AssertionError('Exact table')))
    response = await lesson.start_lesson(lesson.LessonRequest(owner='table', problemText=source, problemConfirmed=True))
    assert len(response.outline) == 3
    for expected in ('35/100; 0,35', '52/100; 0,52', '24/1000; 0,024'):
        assert expected in response.step.choices
        response = lesson.answer_lesson(lesson.TurnRequest(owner='table', sessionId=response.sessionId, revision=response.revision, answer=expected))
    assert response.status == 'COMPLETE' and len(response.completed) == 3
    assert [step.answer for step in response.completed] == ['35/100; 0,35', '52/100; 0,52', '24/1000; 0,024']


@pytest.mark.parametrize('source', [
    'Hoàn thành bảng sau: | Phân số | Phân số thập phân | Số thập phân | | 1/3 | | |',
    'Hoàn thành bảng sau: | Phân số | Phân số thập phân | Số thập phân | | 7/20 | 35/100 | |',
    'Hoàn thành bảng sau: | Phân số | Số thập phân | | 7/20 | |',
])
def test_partial_or_nonterminating_tables_require_review(source):
    assert verified_plan(source) is None


def test_constrained_draft_enforces_the_existing_classroom_sentence_rule_before_generation():
    # Do not spend a second model request on a formatting rule we can express
    # in the first schema. Choice steps still use the required empty sentence.
    import re
    pattern = lesson.PLANNING_SCHEMA['$defs']['DraftStep']['properties']['solutionSentence']['pattern']
    assert re.fullmatch(pattern, 'Diện tích phần còn lại là:')
    assert re.fullmatch(pattern, '')
    assert not re.fullmatch(pattern, 'Diện tích phần còn lại chiếm:')
    assert not re.fullmatch(pattern, 'Kết quả 42 là:')

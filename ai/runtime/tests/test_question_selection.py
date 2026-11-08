import asyncio
import re
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError
from app.tutoring import notebook
from app.tutoring.notebook import NotebookQuestion, NotebookRead
from app.tutoring.question_selection import selectable_questions, compared_questions
from test_notebook_edge_fragments import photo


def question(text, **kw):
    return NotebookQuestion(label='Bài 1', problemText=text, **kw)


def test_splits_only_explicit_independent_tasks_and_retains_instructions():
    items = selectable_questions([question('Bài 1. Điền số thích hợp:\na) 15 m 25 cm = ... m\nb) 7500 ml = ... l')])
    assert len(items) == 2
    assert items[0].label == 'Bài 1 · a'
    assert items[1].problemText == 'Bài 1. Điền số thích hợp:\n7500 ml = ... l'
    assert '15 m' not in items[1].problemText
    rows = selectable_questions([question('Bài 2. Đặt tính rồi tính.\n7,5+9,86\n35+58,76')])
    assert len(rows) == 2 and '7,5+9,86' not in rows[1].problemText
    inline = selectable_questions([question('Câu 1. a) Viết các số 2; 1 theo thứ tự từ lớn đến bé.\nb) Số 100,281 làm tròn đến hàng phần mười được số: ...')])
    assert len(inline) == 2 and '100,281' not in inline[0].problemText


def test_does_not_drop_shared_word_problem_conditions_or_mcq_choices():
    source = question('Một ruộng dài 45m, rộng bằng 4/5 chiều dài.\na) Tính diện tích.\nb) Thu 50kg mỗi 10m², tính số thóc.')
    assert selectable_questions([source]) == [source]
    mcq = question('Chọn kết quả: A. 1 B. 2 C. 3 D. 4')
    assert selectable_questions([mcq]) == [mcq]


def test_scored_subparts_and_lowercase_mcq_tasks_keep_their_own_choices():
    source = question('Bài 4: (1 điểm)\na) (0,5 điểm) Các số tự nhiên thích hợp điền vào chỗ trống là: 60,36 < ... < 64,6\nb) (0,5 điểm) Tính bằng cách thuận tiện nhất\n24,75 + 5,25')
    items = selectable_questions([source])
    assert len(items) == 2 and '60,36' in items[0].problemText
    assert '24,75' not in items[0].problemText and '(0,5 điểm)' in items[1].problemText
    mcq = question('Câu 1: Khoanh vào chữ cái trước câu trả lời đúng.\na. Viết số hai đơn vị:\nA. 2\nB. 3\nb. Số nào bé hơn 1?\nA. 0,5\nB. 2')
    items = selectable_questions([mcq])
    assert len(items) == 2 and 'A. 2\nB. 3' in items[0].problemText
    assert 'A. 0,5\nB. 2' in items[1].problemText and 'hai đơn vị' not in items[1].problemText


def test_separates_two_conversion_columns_without_splitting_shared_word_data():
    source = question('Bài 1. Điền số hoặc đơn vị thích hợp:\na. 17 dm 2 cm = 17,2 ……\n8 tấn 3 kg = …… tấn\nb. 3 ha 26 m² = …… ha\n5 tạ 7 kg = 0,507 ……')
    items = selectable_questions([source])
    assert len(items) == 4
    assert '17 dm' in items[0].problemText and '8 tấn' not in items[0].problemText
    assert '5 tạ' in items[3].problemText and '3 ha' not in items[3].problemText
    columns = question(source.problemText.replace('……\n8 tấn', '……\t\t8 tấn').replace('…… ha\n5 tạ', '…… ha\t\t5 tạ'))
    assert len(selectable_questions([columns])) == 4
    assert selectable_questions([question('Tính diện tích.\nChiều dài = 8 m\nChiều rộng = 4 m')])[0].problemText.startswith('Tính diện tích.')
    assert len(selectable_questions([question('Tính diện tích.\nChiều dài = 8 m\nChiều rộng = 4 m')])) == 1


def test_uncertainty_and_large_page_remain_complete():
    source = question('Tính:\na) 1+[?]\nb) 2+3', uncertain=True)
    assert all(q.uncertain for q in selectable_questions([source]))
    rows = [question(f'Tính:\na) {i}+1\nb) {i}+2') for i in range(20)]
    assert selectable_questions(rows) == rows
    long_label = question('Tính:\na) 1+1\nb) 2+2').model_copy(update={'label': 'x' * 100})
    assert selectable_questions([long_label]) == [long_label]
    long_header = 'Bài 1. Tính ' + 'x' * 1700 + '\na) 1+1\nb) 2+2'
    originals = [question(long_header) for _ in range(8)]
    assert selectable_questions(originals) == originals
    assert question('Tính 5(1)/(3) - 1/2').uncertain
    assert not question('Tính 5 (1)/(3) - 1/2').uncertain
    working_spaces = question('Câu 2. Tính bằng cách thuận tiện:\na) 724×63+724×37-4500 =\n=\n=\nb) 7/15+2/3\n=\n=')
    parts = selectable_questions([working_spaces])
    assert len(parts) == 2 and all(re.search(r'\d', part.problemText.split('\n', 1)[1]) for part in parts)


def test_independent_reading_disagreement_is_flagged_without_replacing_numbers():
    first = [question('Tính 1/45 ml, rồi so với 1,5 l.'), question('Viết tám phần nghìn thành số thập phân.')]
    other = [question('Viết tám phần trăm thành số thập phân.'), question('Tính 1/2 ml, rồi so với 1,5 l.')]
    checked = compared_questions(first, other)
    assert all(q.uncertain for q in checked)
    assert checked[0].problemText == first[0].problemText
    same = compared_questions([question('Tính (1)/(45) + 3')], [question('Tính 1/45 + 3')])
    assert not same[0].uncertain


@pytest.mark.asyncio
async def test_malformed_primary_can_recover_but_reader_disagreement_is_never_a_vote(monkeypatch):
    from app.tutoring.service import ProviderResult
    monkeypatch.setattr('app.config.settings.gemini_enabled', True)
    monkeypatch.setattr('app.config.settings.gemini_api_keys', 'test-configured-not-real')
    cloud = AsyncMock(side_effect=[ProviderResult(dict(kind='MULTIPLE', questions=None), 'groq'),
        ProviderResult(dict(kind='MULTIPLE', questions=[dict(label='Một',problemText='Tính 1+1=?')]), 'gemini')])
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = await notebook.inspect_notebook(photo(fragment=False)[0])
    assert result.kind == 'MULTIPLE' and result.questions[0].problemText == 'Tính 1+1=?'
    assert result.questions[0].uncertain
    assert cloud.await_count == 2


@pytest.mark.asyncio
async def test_provider_fallback_is_not_counted_as_an_independent_confirmation(monkeypatch):
    from app.tutoring.service import ProviderResult
    monkeypatch.setattr('app.config.settings.gemini_enabled', True)
    monkeypatch.setattr('app.config.settings.gemini_api_keys', 'test-configured-not-real')
    cloud = AsyncMock(side_effect=[ProviderResult(dict(kind='MULTIPLE', questions=[
        dict(label='Một', problemText='Tính 1+1=?')]), 'groq'),
        ProviderResult(dict(kind='MULTIPLE', questions=[
        dict(label='Một', problemText='Tính 2+2=?')]), 'groq')])
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = await notebook.inspect_notebook(photo(fragment=False)[0])
    assert result.questions[0].problemText == 'Tính 1+1=?'
    assert result.questions[0].uncertain


@pytest.mark.asyncio
async def test_independent_source_agreement_retains_reading_and_disagreement_needs_confirmation(monkeypatch):
    from app.tutoring.service import ProviderResult
    monkeypatch.setattr('app.config.settings.gemini_enabled', True)
    monkeypatch.setattr('app.config.settings.gemini_api_keys', 'test-configured-not-real')
    primary = dict(kind='MULTIPLE', questions=[dict(label='Một', problemText='Tính 1+1=?'),
        dict(label='Hai', problemText='Viết tám phần nghìn thành số thập phân.')])
    second = dict(kind='MULTIPLE', questions=[dict(label='Một', problemText='Tính 1+1=?'),
        dict(label='Hai', problemText='Viết tám phần trăm thành số thập phân.')])
    monkeypatch.setattr(notebook, '_generate', AsyncMock(side_effect=[ProviderResult(primary, 'groq'), ProviderResult(second, 'gemini')]))
    result = await notebook.inspect_notebook(photo(fragment=False)[0])
    assert not result.questions[0].uncertain
    assert result.questions[1].uncertain
    assert result.questions[1].problemText == primary['questions'][1]['problemText']


@pytest.mark.parametrize('payload', [
    dict(kind='PROBLEM', questions=[dict(label='Một', problemText='1+1')]),
    dict(kind='MULTIPLE', problemText='1+1', questions=[dict(label='Một', problemText='1+1')]),
    dict(kind='MULTIPLE', questions=[dict(label='Một', problemText='1+1'),dict(label='Hai', problemText='1+1')]),
    dict(kind='MULTIPLE', questions=[dict(label='Một', problemText='1+1',uncertain='false')]),
    dict(kind='MULTIPLE', questions=[dict(label=' ', problemText='1+1')]),
    dict(kind='MULTIPLE', questions=[dict(label='Một', problemText='   ')]),
])
def test_rejects_ambiguous_or_malformed_source_contract(payload):
    with pytest.raises(ValidationError):
        NotebookRead.model_validate(payload)


def test_scan_returns_sources_without_choosing_or_solving(monkeypatch):
    cloud = AsyncMock(return_value=dict(kind='MULTIPLE', questions=[
        dict(label='Câu 1', problemText='Tính 1+1 = ?'), dict(label='Câu 2', problemText='Tính 7+[?] = ?')]))
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = asyncio.run(notebook.inspect_notebook(photo(fragment=False)[0]))
    assert result.kind == 'MULTIPLE' and not result.problemText and not result.lines
    assert result.questions[1].uncertain
    assert cloud.await_count == 1

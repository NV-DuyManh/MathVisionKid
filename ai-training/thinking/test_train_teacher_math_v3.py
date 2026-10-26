"""Meaningful tests for raw teacher-SFT scoring, loss masks and safe transactions."""
import copy
import json
from fractions import Fraction
from pathlib import Path
import random
import sys
import types

import pytest

import train_teacher_math_v3 as trainer


def example(mode='worked_solution'):
    row = {'sample_id': 'example', 'grade': 2, 'topic': 'add_sub', 'mode': mode,
        'problem': 'Lan có 5 quyển vở, nhận thêm 39 quyển rồi cho bạn 35 quyển. Lan còn bao nhiêu quyển vở?',
        'oracle_answer': '9', 'private_fact_roles': 'DO_NOT_LEAK',
        'target': {'status': 'solve', 'steps': [
            {'explanation': 'Tìm số vở sau khi nhận thêm.', 'expression': '5+39', 'result': '44', 'unit': 'quyển vở'},
            {'explanation': 'Tìm số vở còn lại.', 'expression': '44-35', 'result': '9', 'unit': 'quyển vở'}],
            'answer': '9', 'unit': 'quyển vở', 'hint': None}}
    if mode == 'hint':
        row['target'].update(steps=[], answer=None, unit=None,
            hint='Trước khi bớt, em cần tìm số vở sau khi nhận thêm bằng phép tính nào?')
    return row


def prediction(row): return json.dumps(row['target'], ensure_ascii=False)


class Tokenizer:
    eos_token = '<EOS>'
    eos_token_id = 99
    pad_token_id = 0
    def apply_chat_template(self, messages, **kwargs):
        assert kwargs['enable_thinking'] is False and kwargs['add_generation_prompt']
        return '|'.join(message['content'] for message in messages) + '|assistant:'
    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        if text.endswith(self.eos_token): return [ord(char) + 100 for char in text[:-5]] + [99]
        return [ord(char) + 100 for char in text]


def test_prompt_is_only_grade_problem_and_mode_no_oracle_target_leak():
    row = example()
    value = json.loads(trainer.prompt(row))
    assert set(value) == {'grade', 'problem', 'mode'}
    assert 'DO_NOT_LEAK' not in trainer.prompt(row) and 'oracle_answer' not in trainer.prompt(row)
    assert trainer.messages(row)[1]['content'] == trainer.prompt(row)


def test_completion_only_loss_and_real_eos_and_no_truncation():
    item = trainer.serialize(example(), Tokenizer(), 5000)
    assert item['labels'][:item['prefix_length']] == [-100] * item['prefix_length']
    assert item['labels'][item['prefix_length']:] == item['input_ids'][item['prefix_length']:]
    assert item['input_ids'][-1] == 99 and item['completion_length'] > 0
    with pytest.raises(ValueError, match='No silent truncation'):
        trainer.serialize(example(), Tokenizer(), 20)


def test_padding_never_contributes_to_loss():
    first = trainer.serialize(example(), Tokenizer(), 5000)
    second = trainer.serialize(example('hint'), Tokenizer(), 5000)
    batch = trainer.collate([first, second], 0)
    shorter = min(range(2), key=lambda i: len([first, second][i]['input_ids']))
    length = len([first, second][shorter]['input_ids'])
    assert batch['labels'][shorter][length:] == [-100] * (len(batch['labels'][0]) - length)
    assert batch['attention_mask'][shorter][length:] == [0] * (len(batch['labels'][0]) - length)


@pytest.mark.parametrize('text,expected', [('0,1', Fraction(1, 10)), ('1/3', Fraction(1, 3)), ('-2.50', Fraction(-5, 2)), ('12', Fraction(12))])
def test_final_numbers_exact_decimal_fraction(text, expected):
    assert trainer.canonical_number(text) == expected


@pytest.mark.parametrize('text', ['nan', '1e3', '1 000', '2/0', True, '1,2,3', '1+2'])
def test_invalid_final_numbers_rejected(text):
    with pytest.raises((ValueError, ZeroDivisionError)):
        trainer.canonical_number(text)


def test_safe_expression_avoids_float_and_checks_remainder_domains():
    assert trainer.evaluate_expression('0.1+0.2') == Fraction(3, 10)
    assert trainer.evaluate_expression('(1/3)+(1/6)') == Fraction(1, 2)
    assert trainer.evaluate_expression('17%5') == 2
    for expression in ['__import__("os")', '2**3', 'a+2', 'True+2', '1e3', '-1%3', '3%0', '3.5%2', '1/0']:
        with pytest.raises((ValueError, ZeroDivisionError)):
            trainer.evaluate_expression(expression)


def test_expression_reference_path_accepts_commute_not_numeric_coincidence():
    assert trainer.expression_signature('5+(39+2)') == trainer.expression_signature('(2+5)+39')
    assert trainer.expression_signature('3*4') == trainer.expression_signature('4*3')
    assert trainer.expression_signature('3*4') != trainer.expression_signature('6+6')
    assert trainer.expression_signature('44-35') != trainer.expression_signature('35-44')


def test_gold_worked_solution_scores_raw_generated_answer_and_all_steps():
    row = example()
    score = trainer.score(row, prediction(row))
    assert score['correct'] and score['answer_correct'] and score['steps_arithmetic_correct']
    assert score['steps_reference_match'] and score['solution_verified']
    wrong = copy.deepcopy(row['target']); wrong['answer'] = '8'
    result = trainer.score(row, json.dumps(wrong))
    assert not result['correct'] and result['wrong_answer']


def test_correct_final_answer_cannot_hide_wrong_intermediate_result_or_wrong_method():
    row = example()
    wrong = copy.deepcopy(row['target']); wrong['steps'][0]['result'] = '43'
    result = trainer.score(row, json.dumps(wrong))
    assert result['answer_correct'] and not result['steps_arithmetic_correct'] and not result['correct']
    wrong = copy.deepcopy(row['target']); wrong['steps'][0]['expression'] = '22+22'
    result = trainer.score(row, json.dumps(wrong))
    assert result['answer_correct'] and result['steps_arithmetic_correct'] and not result['steps_reference_match']
    assert not result['correct']


def test_inverse_check_last_step_does_not_replace_answer_producing_step():
    row = example(); row['topic'] = 'vertical_subtract'
    row['target']['steps'].append({'explanation': 'Kiểm tra bằng phép tính ngược.',
                                  'expression': '9+35', 'result': '44', 'unit': 'quyển vở'})
    assert trainer.score(row, prediction(row))['solution_verified']
    wrong = copy.deepcopy(row['target']); wrong['steps'][-1]['result'] = '43'
    assert not trainer.score(row, json.dumps(wrong))['solution_verified']


def test_missing_steps_does_not_hide_wrong_raw_answer_count():
    row = example(); wrong = copy.deepcopy(row['target']); wrong.update(steps=[], answer='8')
    score = trainer.score(row, json.dumps(wrong))
    assert score['answered'] and score['wrong_answer'] and not score['solution_verified']


def test_categorical_answer_only_supported_with_explicit_kind():
    row = example(); row['answer_kind'] = 'categorical'
    row['target'].update(answer='không thể', unit='', steps=[
        {'explanation': 'Không có viên đỏ trong hộp.', 'expression': '', 'result': 'không thể', 'unit': ''}])
    assert trainer.score(row, prediction(row))['solution_verified']
    del row['answer_kind']
    assert not trainer.score(row, prediction(row))['solution_verified']


def test_wrong_step_or_answer_unit_fails_verified_solution():
    row = example(); wrong = copy.deepcopy(row['target']); wrong['steps'][0]['unit'] = 'cm'
    assert not trainer.score(row, json.dumps(wrong))['solution_verified']
    wrong = copy.deepcopy(row['target']); wrong['unit'] = 'cm'
    assert not trainer.score(row, json.dumps(wrong))['unit_correct']


def test_hint_one_question_and_no_computed_answer_or_answer_fields():
    row = example('hint'); assert trainer.score(row, prediction(row))['correct']
    for text in ['Đáp số là 9 quyển. Em hiểu chưa?', 'Em tính được 44 quyển trước khi cho bạn phải không?',
                 'Em cộng nhé? Sau đó trừ nhé?', 'Em hãy tính số vở còn lại.']:
        wrong = copy.deepcopy(row['target']); wrong['hint'] = text
        assert not trainer.score(row, json.dumps(wrong))['hint_safe']
    wrong = copy.deepcopy(row['target']); wrong['answer'] = '9'
    assert not trainer.score(row, json.dumps(wrong))['correct']


def test_guard_status_must_be_correct_and_never_solve():
    row = example(); row['target'] = {'status': 'clarify', 'steps': [], 'answer': None, 'unit': None, 'hint': 'Em cho biết số vở ban đầu nhé?'}
    assert trainer.score(row, prediction(row))['correct']
    wrong = copy.deepcopy(row['target']); wrong['status'] = 'unsupported'
    assert not trainer.score(row, json.dumps(wrong))['correct']
    wrong = copy.deepcopy(row['target']); wrong.update(status='clarify', answer='9')
    assert not trainer.score(row, json.dumps(wrong))['schema_valid']


@pytest.mark.parametrize('hint', [None, '', '   ', 'ok', 'a' * 501, 'Đáp số là 9 quyển. Em hiểu chưa?'])
def test_guard_requires_meaningful_bounded_nonempty_hint_without_answer_disclosure(hint):
    row = example(); row['target'] = {'status': 'clarify', 'steps': [], 'answer': None, 'unit': None,
                                    'hint': 'Em cho biết số vở ban đầu nhé?'}
    wrong = copy.deepcopy(row['target']); wrong['hint'] = hint
    assert not trainer.score(row, json.dumps(wrong))['correct']


def test_parser_duplicate_extra_prefix_unfinished_thought_and_truncation_fail():
    valid = prediction(example())
    assert trainer.parse_output('<think>private exploratory tokens</think>' + valid)['answer'] == '9'
    assert trainer.parse_output('```json\n' + valid + '\n```')['answer'] == '9'
    for text in ['hello ' + valid, '<think>unfinished' + valid, valid + ' trailing',
                 valid[:-1] + ',"answer":"9"}', valid[:-1] + ',"extra":1}']:
        with pytest.raises(ValueError): trainer.parse_output(text)
    with pytest.raises(ValueError, match='truncated'): trainer.parse_output(valid, True)


def test_closing_only_thought_requires_verified_rendered_prompt_prefix():
    valid = prediction(example())
    with pytest.raises(ValueError): trainer.parse_output('reasoning</think>' + valid)
    assert trainer.parse_output('reasoning</think>' + valid, thought_prefix_open=True)['answer'] == '9'


def test_selection_uses_only_matched_validation_and_rejects_pergrade_or_hint_regression():
    base = {'answer_and_unit_correct': 10, 'solution_verified': 8, 'hint_safe': 4, 'hint_reference_match': 3, 'guard_correct': 3}
    base['per_grade'] = {'1': dict(base)}
    better = {'answer_and_unit_correct': 11, 'solution_verified': 9, 'hint_safe': 4, 'hint_reference_match': 3, 'guard_correct': 3}
    better['per_grade'] = {'1': dict(better)}
    assert trainer.select_candidate(base, better)['selected'] == 'adapter'
    better['per_grade']['1']['solution_verified'] = 7
    assert trainer.select_candidate(base, better)['selected'] == 'base'
    better['per_grade']['1']['solution_verified'] = 9; better['hint_safe'] = 3
    assert trainer.select_candidate(base, better)['selected'] == 'base'
    better['hint_safe'] = 4; better['hint_reference_match'] = 2
    assert trainer.select_candidate(base, better)['selected'] == 'base'
    assert trainer.select_candidate(base, base)['selected'] == 'base'


def test_stratified_validation_subset_reproducible_all_grade_mode_groups():
    examples = []
    for grade in range(1, 6):
        for mode in ('hint', 'worked_solution'):
            for index in range(10):
                row = example(mode); row.update(grade=grade, sample_id=f'{grade}-{mode}-{index}'); examples.append(row)
    first = trainer.stratified_subset(examples, 30)
    assert len(first) == 30 and first == trainer.stratified_subset(examples, 30)
    assert {(r['grade'], r['mode']) for r in first} == {(g, m) for g in range(1, 6) for m in ('hint', 'worked_solution')}


def test_subset_prioritizes_all_topic_families_before_repeating_modes():
    values = []
    for topic in range(56):
        for mode in ('worked_solution', 'hint'):
            row = example(mode); row.update(topic=f'topic_{topic}', grade=topic%5+1,
                                            sample_id=f'{topic}_{mode}'); values.append(row)
    subset = trainer.stratified_subset(values, 80)
    assert len({row['topic'] for row in subset}) == 56


def test_config_exact_model_pin_and_no_mutation_of_old_runs(tmp_path):
    path = tmp_path / 'config.json'; path.write_text(json.dumps({'run_id': 'new_teacher_run'}))
    config = trainer.load_config(path)
    assert config['model_id'] == 'Qwen/Qwen3-1.7B' and len(config['revision']) == 40
    assert config['max_length'] == 1536 and config['batch_size'] == 1
    path.write_text(json.dumps({'run_id': '../old', 'revision': 'main'}))
    with pytest.raises(ValueError): trainer.load_config(path)


def test_prepare_rejects_corrupt_teacher_targets_and_duplicate_ids(tmp_path, monkeypatch):
    module = types.ModuleType('fixture_data'); module.SYSTEM = trainer.SYSTEM; module.__file__ = str(tmp_path / 'fixture.py')
    Path(module.__file__).write_text('SYSTEM="fixture"')
    monkeypatch.setitem(sys.modules, 'fixture_data', module)
    data = tmp_path / 'data'; data.mkdir()
    first = example(); second = example('hint'); second['sample_id'] = 'val'
    (data / 'train.jsonl').write_text(prediction_row(first), encoding='utf-8')
    (data / 'val.jsonl').write_text(prediction_row(second), encoding='utf-8')
    config_path = tmp_path / 'cfg.json'; config_path.write_text(json.dumps({'run_id': 'safe', 'data_module': 'fixture_data'}))
    config = trainer.load_config(config_path)
    _, run, splits, val, expanded = trainer.prepare(tmp_path, config)
    assert len(val) == 1 and expanded['enable_thinking_training'] is False
    second['sample_id'] = first['sample_id']
    (data / 'val.jsonl').write_text(prediction_row(second), encoding='utf-8')
    with pytest.raises(ValueError, match='Duplicate'): trainer.prepare(tmp_path, config)


def prediction_row(row): return json.dumps(row, ensure_ascii=False) + '\n'


def test_amp_retry_keeps_same_samples_rng_and_optimizer_schedule_once():
    class Optimizer:
        def __init__(self): self.steps = 0; self.grad = None
        def zero_grad(self, set_to_none): self.grad = None
    class Scaler:
        def __init__(self): self.scale = 1024
        def unscale_(self, opt): pass
        def get_scale(self): return self.scale
        def update(self, new_scale=None):
            if new_scale is not None: self.scale = new_scale
        def step(self, opt): opt.steps += 1
    class Scheduler:
        def __init__(self): self.steps = 0
        def step(self): self.steps += 1
    optimizer, scaler, scheduler = Optimizer(), Scaler(), Scheduler()
    rng = random.Random(42); forwards, events = [], []
    def backward(group):
        forwards.append((group, rng.random())); optimizer.grad = float('inf') if len(forwards) == 1 else 2.
        return 1.
    result = trainer.run_amp_update([[3], [4]], backward, optimizer, scaler, scheduler,
        rng.getstate, rng.setstate, lambda: optimizer.grad != float('inf'), lambda: 2., events.append)
    assert forwards[0] == forwards[1] and result['overflow_retries'] == 1
    assert optimizer.steps == scheduler.steps == 1 and scaler.scale == 512


def test_import_works_without_torch_dependency():
    assert 'torch' not in trainer.__dict__

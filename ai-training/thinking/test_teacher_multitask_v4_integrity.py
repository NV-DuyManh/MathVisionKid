"""Independent CPU checks for the mixed-run integrity gates.

These fixtures contain no model weights, GPU work, or Colab mutations. Helpers
under review must reject inconsistent evidence before a mixed epoch is launched
or recorded as complete.
"""
import copy
import hashlib
import json
import random
import sys
import types
from pathlib import Path

import pytest

import teacher_multitask_v4 as mixed
import train_teacher_math_v3 as numeric
from test_train_teacher_math_v3 import Tokenizer, example


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')


class IntegrityTokenizer(Tokenizer):
    def decode(self, ids, skip_special_tokens=True):
        return ''.join(chr(token - 100) for token in ids if token not in (99, 0))


def concept_row():
    return {
        'sample_id': 'integrity_concept_train', 'grade': 4,
        'mode': 'worked_solution', 'source': {'source_id': 'fixture'},
        'license': 'original fixture', 'human_verified': False,
        'pedagogy_teacher_reviewed': False,
        'numeric_checks': [{'expression': '1/2+1/4', 'expected_result': '3/4'}],
        'messages': [
            {'role': 'system', 'content': 'Giải thích ngắn.'},
            {'role': 'user', 'content': 'Giải ví dụ cộng phân số.'},
            {'role': 'assistant', 'content': 'Đưa về cùng mẫu: 1/2 + 1/4 = 3/4.'},
        ],
    }


def concept_validation_row():
    return {
        'sample_id': 'integrity_concept_val', 'grade': 4,
        'mode': 'worked_solution',
        'messages': [
            {'role': 'system', 'content': 'Giải thích ngắn.'},
            {'role': 'user', 'content': 'Vì sao cần quy đồng khi cộng?'},
        ],
        'expected_key_claims': [{'claim_id': 'common', 'any_of': ['cùng mẫu']}],
        'rejected_claims': [], 'require_image_confirmation': False,
    }


@pytest.mark.parametrize('step', [-1, 6])
def test_resume_step_outside_committed_epoch_is_rejected(step):
    with pytest.raises(ValueError):
        mixed.validate_resume_step(step, 5)


@pytest.mark.parametrize('step', [0, 5])
def test_resume_step_valid_boundaries_are_accepted(step):
    mixed.validate_resume_step(step, 5)


def committed_epoch():
    instances = [
        {'sample_id': 'numeric:fixture_a', 'task_kind': 'numeric'},
        {'sample_id': 'concept:0:fixture_b', 'task_kind': 'concept'},
        {'sample_id': 'concept:1:fixture_b', 'task_kind': 'concept'},
    ]
    config = {'seed': 20261013, 'batch_size': 1, 'accumulation': 2}
    order = list(range(len(instances)))
    random.Random(config['seed']).shuffle(order)
    groups = [order[:2], order[2:]]
    records = [
        {'step': index + 1,
         'sample_ids': [instances[position]['sample_id'] for position in group],
         'loss': 0.2, 'grad_norm': 0.3, 'amp_scale': 1024,
         'overflow_retries': 0}
        for index, group in enumerate(groups)
    ]
    return instances, records, config


def test_completed_epoch_requires_all_committed_log_steps():
    instances, records, config = committed_epoch()
    with pytest.raises(ValueError):
        mixed.validate_committed_epoch(instances, records[:-1], config, 2)


def test_completed_epoch_requires_each_replay_instance_once():
    instances, records, config = committed_epoch()
    damaged = copy.deepcopy(records)
    damaged[-1]['sample_ids'] = damaged[0]['sample_ids'][:1]
    with pytest.raises(ValueError):
        mixed.validate_committed_epoch(instances, damaged, config, 2)


def test_completed_epoch_requires_fixed_seed_group_order():
    instances, records, config = committed_epoch()
    damaged = copy.deepcopy(records)
    damaged[0]['sample_ids'].reverse()
    with pytest.raises(ValueError):
        mixed.validate_committed_epoch(instances, damaged, config, 2)


def test_complete_numeric_and_repeated_concept_instances_pass_audit():
    instances, records, config = committed_epoch()
    mixed.validate_committed_epoch(instances, records, config, 2)


def test_reload_requires_current_adapter_file_sha(tmp_path):
    adapter = tmp_path / 'adapter'
    adapter.mkdir()
    weights = adapter / 'adapter_model.safetensors'
    weights.write_bytes(b'fixture adapter bytes')
    complete = {'adapter_sha256': numeric.sha(weights)}
    mixed.verify_adapter_file(tmp_path, complete)
    weights.write_bytes(b'changed adapter bytes with another file identity')
    with pytest.raises(ValueError):
        mixed.verify_adapter_file(tmp_path, complete)


def test_reload_missing_adapter_file_is_rejected(tmp_path):
    with pytest.raises((ValueError, FileNotFoundError)):
        mixed.verify_adapter_file(tmp_path, {'adapter_sha256': '0' * 64})


def test_audited_v3_mode_requires_an_actual_retention_reference(tmp_path):
    data = tmp_path / 'data'
    data.mkdir()
    numeric_val = example()
    numeric_val['sample_id'] = 'integrity_numeric_val'
    numeric_val['problem'] = 'Đề kiểm định riêng: ' + numeric_val['problem']
    sources = {
        'numeric_train': [example()], 'numeric_val': [numeric_val],
        'concept_train': [concept_row()], 'concept_val': [concept_validation_row()],
    }
    for name, rows in sources.items():
        (data / (name + '.jsonl')).write_text(
            ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
            encoding='utf-8')
    audit = tmp_path / 'v3_audit.json'
    selection = tmp_path / 'v3_selection.json'
    save_json(audit, {'status': 'PASSED', 'all_passed': True})
    save_json(selection, {'challenge_used_for_selection': False})
    config_path = tmp_path / 'config.json'
    save_json(config_path, {'run_id': 'integrity_missing_retention',
        'require_v3_audit': True, 'v3_audit_path': str(audit),
        'v3_selection_path': str(selection)})
    with pytest.raises(ValueError, match='[Rr]etention'):
        mixed.prepare(tmp_path, mixed.load_config(config_path))


@pytest.fixture
def retention_fixture(tmp_path, monkeypatch):
    import teacher_math_data_v3 as data_module

    data = tmp_path / 'data'
    data.mkdir()
    val = [example()]
    (data / 'numeric_val.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in val),
        encoding='utf-8')
    run = tmp_path / 'runs' / 'integrity_retention'
    run.mkdir(parents=True)
    summary_path = tmp_path / 'parent_val.summary.json'
    metadata_path = tmp_path / 'parent_val.metadata.json'
    parent_path = tmp_path / 'parent_config.json'
    config_path = tmp_path / 'config.json'
    save_json(config_path, {'run_id': run.name, 'require_v3_audit': False,
        'max_new_tokens': 512, 'eval_batch_size': 4,
        'numeric_retention_summary': str(summary_path),
        'numeric_retention_metadata': str(metadata_path),
        'numeric_retention_config': str(parent_path)})
    config = mixed.load_config(config_path)
    tokenizer = IntegrityTokenizer()
    text = json.dumps(val[0]['target'], ensure_ascii=False, separators=(',', ':'))
    generated_ids = tokenizer.encode(text + tokenizer.eos_token)
    record = {'sample_id': val[0]['sample_id'], 'grade': val[0]['grade'],
        'topic': val[0]['topic'], 'mode': val[0]['mode'],
        'reference_status': val[0]['target']['status'], 'prediction': text,
        'generated_ids': generated_ids, 'generated_tokens': len(generated_ids),
        'eos_observed': True, 'thought_prefix_open': False,
        'scores': numeric.score(val[0], text)}
    (tmp_path / 'parent_val.jsonl').write_text(json.dumps(record, ensure_ascii=False)
        + '\n', encoding='utf-8')
    summary = numeric.aggregate([record])
    summary['per_grade'] = {str(val[0]['grade']): numeric.aggregate([record])}
    summary['per_topic'] = {val[0]['topic']: numeric.aggregate([record])}
    save_json(summary_path, summary)
    metadata = {
        'model_key': 'base:' + config['model_id'] + ':' + config['revision'],
        'ids': [row['sample_id'] for row in val],
        'input_sha256': hashlib.sha256(json.dumps(val, ensure_ascii=False,
            sort_keys=True).encode()).hexdigest(),
        'enable_thinking': False, 'do_sample': False,
        'max_new_tokens': config['max_new_tokens'],
        'batch_size': config['eval_batch_size'], 'seed': config['seed'],
        'temperature': None, 'top_p': None, 'top_k': None,
        'eos_token_id': Tokenizer.eos_token_id,
    }
    save_json(metadata_path, metadata)
    save_json(parent_path, {
        'model_id': config['model_id'], 'revision': config['revision'],
        'source_hashes': {
            'teacher_math_data_v3.py': numeric.sha(data_module.__file__),
            'train_teacher_math_v3.py': numeric.sha(numeric.__file__),
        },
        'dataset_fingerprints': {'val': numeric.sha(data / 'numeric_val.jsonl')},
    })
    monkeypatch.setattr(numeric, 'get_tokenizer', lambda _: tokenizer)
    monkeypatch.setattr(numeric, 'SYSTEM', data_module.SYSTEM)
    return config, val, run, metadata, metadata_path, summary


def test_v3_retention_batch_size_must_equal_v4_numeric_eval(retention_fixture):
    config, val, run, metadata, metadata_path, _ = retention_fixture
    metadata['batch_size'] = 2
    save_json(metadata_path, metadata)
    with pytest.raises(ValueError, match='[Pp]rotocol|[Bb]atch'):
        mixed.retention_reference(config, val, run)


def test_v3_retention_same_frozen_protocol_is_accepted(retention_fixture):
    config, val, run, _, _, summary = retention_fixture
    assert mixed.retention_reference(config, val, run) == summary


def test_retention_recomputes_actual_prediction_scores_instead_of_trusting_summary(retention_fixture):
    config, val, run, _, _, summary = retention_fixture
    changed = copy.deepcopy(summary)
    changed['answer_and_unit_correct'] += 1
    save_json(Path(config['numeric_retention_summary']), changed)
    with pytest.raises(ValueError, match='aggregate|scores'):
        mixed.retention_reference(config, val, run)


def test_retention_reconstructs_prediction_from_actual_generated_tokens(retention_fixture):
    config, val, run, _, _, _ = retention_fixture
    predictions = Path(str(config['numeric_retention_summary']).replace('.summary.json', '.jsonl'))
    record = json.loads(predictions.read_text(encoding='utf-8'))
    record['prediction'] = 'Changed string that these generated token IDs never produced'
    predictions.write_text(json.dumps(record, ensure_ascii=False) + '\n', encoding='utf-8')
    with pytest.raises(ValueError, match='Generated IDs|raw output'):
        mixed.retention_reference(config, val, run)


@pytest.fixture
def semantic_fixture(tmp_path):
    examples = []
    for index in range(30):
        row = concept_validation_row()
        row['sample_id'] = 'semantic_' + str(index)
        row['grade'] = index // 6 + 1
        examples.append(row)
    for model in ('baseline', 'candidate'):
        (tmp_path / (model + '_concept_val.jsonl')).write_text(
            ''.join(json.dumps({'sample_id': row['sample_id'],
                'prediction': model + ' fixture generated response'}, ensure_ascii=False)
                + '\n' for row in examples), encoding='utf-8')
    review = {
        'review_kind': 'AI_SEMANTIC_RESEARCH_REVIEW', 'human_verified': False,
        'reference_sha256': hashlib.sha256(json.dumps(examples, ensure_ascii=False,
            sort_keys=True).encode()).hexdigest(),
        'prediction_sha256': {
            name: numeric.sha(tmp_path / (name + '_concept_val.jsonl'))
            for name in ('baseline', 'candidate')},
        'records': [
            {'model': model, 'sample_id': row['sample_id'], 'grade': row['grade'],
             'semantic_correct': model == 'candidate', 'instruction_followed': True,
             'severe_error': False, 'reason': 'Fixture explicit claim review.'}
            for model in ('baseline', 'candidate') for row in examples],
    }
    path = tmp_path / 'concept_semantic_review.json'
    save_json(path, review)
    return tmp_path, examples, review, path


def test_semantic_review_requires_all_sixty_actual_hash_bound_outputs(semantic_fixture):
    run, examples, _, _ = semantic_fixture
    report = mixed.semantic_review(run, examples)
    assert report['passed'] and report['candidate']['acceptable'] == 30
    assert report['human_verified'] is False and report['teacher_certified'] is False


@pytest.mark.parametrize('damage', ['missing', 'duplicate', 'human_claim', 'changed_output'])
def test_semantic_review_rejects_incomplete_or_changed_evidence(semantic_fixture, damage):
    run, examples, review, path = semantic_fixture
    if damage == 'missing':
        review['records'].pop()
    elif damage == 'duplicate':
        review['records'][-1] = copy.deepcopy(review['records'][0])
    elif damage == 'human_claim':
        review['human_verified'] = True
    else:
        with (run / 'candidate_concept_val.jsonl').open('a', encoding='utf-8') as stream:
            stream.write('changed actual prediction bytes\n')
    save_json(path, review)
    with pytest.raises(ValueError):
        mixed.semantic_review(run, examples)


def test_semantic_review_rejects_per_grade_regression_despite_overall_gain(semantic_fixture):
    run, examples, review, path = semantic_fixture
    for record in review['records']:
        record['semantic_correct'] = (
            (record['model'] == 'baseline' and record['grade'] == 1)
            or (record['model'] == 'candidate' and record['grade'] in (1, 2)))
    first_grade_one = next(record for record in review['records']
        if record['model'] == 'candidate' and record['grade'] == 1)
    first_grade_one['semantic_correct'] = False
    save_json(path, review)
    report = mixed.semantic_review(run, examples)
    assert report['candidate']['acceptable'] > report['baseline']['acceptable']
    assert report['passed'] is False


def test_candidate_stage_stops_before_selection_and_challenge(tmp_path, monkeypatch):
    """Exercise the real stage branch; only model inference is replaced."""
    run = tmp_path / 'runs' / 'candidate_stage_fixture'
    run.mkdir(parents=True)
    data = tmp_path / 'data'
    data.mkdir()
    for kind in ('numeric_challenge', 'concept_challenge'):
        (data / (kind + '.jsonl')).write_text('POISON: challenge must remain unread',
            encoding='utf-8')
    adapter = run / 'adapter'
    adapter.mkdir()
    weights = adapter / 'adapter_model.safetensors'
    weights.write_bytes(b'candidate stage fixture adapter')
    save_json(run / 'training_complete.json', {
        'adapter_sha256': numeric.sha(weights), 'adapter_tensor_hashes': {}})
    summary = {'fixture_summary': True}
    for stem in ('baseline_numeric_val', 'baseline_concept_val'):
        save_json(run / (stem + '.summary.json'), summary)
        (run / (stem + '.jsonl')).write_text('{}\n', encoding='utf-8')
    parent_summary = tmp_path / 'parent_val.summary.json'
    save_json(parent_summary, summary)
    (tmp_path / 'parent_val.jsonl').write_text('{}\n', encoding='utf-8')
    config = {'model_id': numeric.MODEL, 'revision': numeric.REVISION,
        'seed': 20261013, 'max_new_tokens': 512, 'eval_batch_size': 4,
        'val_limit': 0, 'numeric_retention_summary': str(parent_summary)}
    datasets = {'numeric_val': [example()], 'concept_val': [concept_validation_row()]}

    class FixturePeft:
        @classmethod
        def from_pretrained(cls, base, path, is_trainable):
            assert is_trainable is False
            return cls()

    monkeypatch.setitem(sys.modules, 'peft', types.SimpleNamespace(PeftModel=FixturePeft))
    monkeypatch.setattr(numeric, 'adapter_hashes', lambda model: {})

    def generated_numeric(model, tokenizer, rows, path, *args, **kwargs):
        path.write_text('{}\n', encoding='utf-8')
        return summary

    def generated_concepts(model, tokenizer, rows, path, *args, **kwargs):
        path.write_text('{}\n', encoding='utf-8')
        return summary

    monkeypatch.setattr(numeric, 'evaluate', generated_numeric)
    monkeypatch.setattr(mixed, 'evaluate_concepts', generated_concepts)
    monkeypatch.setattr(mixed.direct_numeric, 'diagnostic',
        lambda rows, predictions: {'summary': summary})
    monkeypatch.setattr(mixed, 'retention_reference', lambda *args: summary)
    # This test exercises the pause branch; actual token/audit invariants have
    # independent malformed-evidence tests below.
    monkeypatch.setattr(mixed, 'audit_validations', lambda *args: {})
    monkeypatch.setattr(mixed, 'response_contract', lambda *args: summary)
    original_rows = numeric.rows

    def guarded_rows(path):
        assert 'challenge' not in path.name, 'Candidate stage parsed sealed challenge'
        return original_rows(path)

    def forbidden_after_candidate(*args, **kwargs):
        raise AssertionError('Candidate stage selected/reviewed before the explicit pause')

    monkeypatch.setattr(numeric, 'rows', guarded_rows)
    monkeypatch.setattr(mixed, 'semantic_review', forbidden_after_candidate)
    monkeypatch.setattr(mixed, 'select', forbidden_after_candidate)
    mixed.evaluate(run, tmp_path, datasets, config, Tokenizer(), object(), candidate_only=True)
    assert not (run / 'selection.json').exists()
    assert not (run / 'completed_run.json').exists()
    assert json.loads((run / 'validation_complete.json').read_text())['challenge_read'] is False
    assert json.loads((run / 'progress.json').read_text())['phase'] == 'semantic_review_required'


def test_v4_defaults_preserve_retention_protocol_and_lower_learning_rate(tmp_path):
    path = tmp_path/'config.json'; save_json(path, {'run_id': 'defaults'})
    config = mixed.load_config(path)
    assert (config['lr'], config['batch_size'], config['accumulation']) == (2e-5, 2, 2)
    assert (config['max_new_tokens'], config['eval_batch_size']) == (512, 4)
    assert config['evaluation_data_module'] == 'teacher_math_data_v3'
    assert config['require_numeric_semantic_review'] is True
    save_json(path, {'run_id': 'unsafe_lr', 'lr': 1e-4})
    with pytest.raises(ValueError, match='learning rate'): mixed.load_config(path)


def test_training_system_does_not_mutate_frozen_evaluation_input():
    original = numeric.SYSTEM
    item = mixed.build_training([example()], [], training_system='NEW TEACHER INSTRUCTION')[0]
    assert mixed.mixed_messages(item)[0]['content'] == 'NEW TEACHER INSTRUCTION'
    assert numeric.messages(item['row'])[0]['content'] == original
    assert 'DO_NOT_LEAK' not in json.dumps(mixed.mixed_messages(item))
    with pytest.raises(RuntimeError):
        with mixed.numeric_system('TEMPORARY FRESH EVAL SYSTEM'):
            assert numeric.SYSTEM != original
            raise RuntimeError('fixture interrupted')
    assert numeric.SYSTEM == original


def test_numeric_teacher_validator_rejects_wrong_carry_before_any_masks():
    called = []
    def independent_validator(row):
        called.append(row['sample_id'])
        if row['column_trace']['carry'] != 1: raise ValueError('Wrong carry state')
    module = types.SimpleNamespace(__name__='fixture_new_teacher', validate_training_row=independent_validator)
    row = example(); row['column_trace'] = {'carry': 0}
    with pytest.raises(ValueError, match='carry'): mixed.validate_training_numeric(row, module)
    assert called == [row['sample_id']]
    row['column_trace']['carry'] = 1
    mixed.validate_training_numeric(row, module)


def test_resume_requires_all_atomic_checkpoint_updates_before_continuing():
    instances, records, config = committed_epoch()
    assert mixed.validate_resume_prefix(instances, records, config, 1) == records[:1]
    with pytest.raises(ValueError, match='missing'): mixed.validate_resume_prefix(instances, records[1:], config, 2)
    damaged = copy.deepcopy(records); damaged[0]['sample_ids'].reverse()
    with pytest.raises(ValueError, match='order'): mixed.validate_resume_prefix(instances, damaged, config, 2)


def test_cross_base_retention_decodes_parent_tokens_with_parent_tokenizer(retention_fixture, monkeypatch):
    config, val, run, _, _, summary = retention_fixture
    parent_id, parent_revision = config['model_id'], config['revision']
    config['model_id'] = 'Qwen/Qwen3-4B-Instruct-2507'
    config['revision'] = 'cdbee75f17c01a7cc42f958dc650907174af0554'
    config['load_in_4bit'] = True
    requested = []
    def get_parent_tokenizer(parent):
        requested.append((parent['model_id'], parent['revision']))
        return IntegrityTokenizer()
    monkeypatch.setattr(numeric, 'get_tokenizer', get_parent_tokenizer)
    assert mixed.retention_reference(config, val, run) == summary
    assert requested == [(parent_id, parent_revision)]
    evidence = json.loads((run/'numeric_retention_reference.json').read_text())
    assert evidence['same_pinned_base'] is False
    assert evidence['candidate_base_quantization'] == 'nf4_double_float16'


def test_actual_arithmetic_contract_accepts_alternate_valid_path_and_rejects_false_step():
    row = example()
    alternative = copy.deepcopy(row['target'])
    alternative['steps'] = [{'explanation': 'Tính số vở còn lại.', 'expression': '5+39-35', 'result': '9', 'unit': 'quyển vở'}]
    record = {'sample_id': row['sample_id'], 'prediction': json.dumps(alternative, ensure_ascii=False), 'scores': {'truncated': False}}
    assert not numeric.score(row, record['prediction'])['steps_reference_match']
    assert mixed.response_contract([row], [record])['steps_arithmetic_safe'] == 1
    alternative['steps'][0]['result'] = '8'
    record['prediction'] = json.dumps(alternative, ensure_ascii=False)
    result = mixed.response_contract([row], [record])
    assert result['schema_valid'] == 1 and result['mode_contract'] == 1
    assert result['steps_arithmetic_safe'] == 0


@pytest.fixture
def numeric_semantic_fixture(tmp_path):
    rows = [example(), example('hint')]; rows[1]['sample_id'] = 'hint_example'
    for model in ('baseline', 'candidate'):
        (tmp_path/(model+'_numeric_val.jsonl')).write_text('actual '+model, encoding='utf-8')
    review = {'review_kind': 'AI_SEMANTIC_RESEARCH_REVIEW', 'human_verified': False,
        'reference_sha256': hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        'prediction_sha256': {model: numeric.sha(tmp_path/(model+'_numeric_val.jsonl')) for model in ('baseline', 'candidate')},
        'records': [{'model': model, 'sample_id': row['sample_id'], 'grade': row['grade'], 'mode': row['mode'],
                    'semantic_correct': True, 'instruction_followed': True, 'severe_error': False,
                    'useful': True, 'grade_appropriate': True, 'answer_not_disclosed': True,
                    'reason': 'Fixture actual visible response reviewed.'}
                    for model in ('baseline', 'candidate') for row in rows]}
    path = tmp_path/'numeric_semantic_review.json'; save_json(path, review)
    return tmp_path, rows, review, path


def test_numeric_semantic_review_catches_answer_leak_even_when_format_is_safe(numeric_semantic_fixture):
    run, rows, review, path = numeric_semantic_fixture
    assert mixed.numeric_semantic_review(run, rows)['passed']
    candidate_hint = next(record for record in review['records'] if record['model'] == 'candidate' and record['mode'] == 'hint')
    candidate_hint['answer_not_disclosed'] = False
    save_json(path, review)
    result = mixed.numeric_semantic_review(run, rows)
    assert result['passed'] is False and result['candidate']['hint_answer_leaks'] == 1


def test_hint_improvement_cannot_hide_worked_math_regression_in_same_grade(numeric_semantic_fixture):
    run, rows, review, path = numeric_semantic_fixture
    for record in review['records']:
        if record['model'] == 'baseline' and record['mode'] == 'hint': record['semantic_correct'] = False
        if record['model'] == 'candidate' and record['mode'] == 'worked_solution': record['semantic_correct'] = False
    save_json(path, review)
    result = mixed.numeric_semantic_review(run, rows)
    assert result['baseline']['semantic_correct'] == result['candidate']['semantic_correct'] == 1
    assert result['passed'] is False
    assert result['candidate']['by_task']['worked']['semantic_correct'] == 0


@pytest.mark.parametrize('damage', ['missing_reply', 'changed_bytes', 'human_claim', 'wrong_mode'])
def test_numeric_semantic_review_rejects_unbound_or_incomplete_evidence(numeric_semantic_fixture, damage):
    run, rows, review, path = numeric_semantic_fixture
    if damage == 'missing_reply': review['records'].pop()
    elif damage == 'changed_bytes': (run/'candidate_numeric_val.jsonl').write_text('changed', encoding='utf-8')
    elif damage == 'human_claim': review['human_verified'] = True
    else: review['records'][0]['mode'] = 'hint'
    save_json(path, review)
    with pytest.raises(ValueError): mixed.numeric_semantic_review(run, rows)


def test_controller_pauses_for_actual_review_without_reading_poisoned_challenge(tmp_path):
    run = tmp_path/'run'; run.mkdir()
    for name in ('token_audit.json', 'baseline_numeric_val.summary.json', 'baseline_concept_val.summary.json',
                 'baseline_numeric_fresh_val.summary.json', 'training_complete.json', 'validation_complete.json'):
        save_json(run/name, {})
    save_json(run/'memory_preflight.json', {'passed': True})
    (run/'concept_challenge.jsonl').write_text('POISON', encoding='utf-8')
    stage = mixed.controller_next_stage(run, {'require_numeric_semantic_review': True}, True)
    assert stage['stage'] == 'semantic_review_required' and stage['gpu_job_required'] is False
    assert set(stage['missing_review_files']) == {'concept_semantic_review.json', 'numeric_semantic_review.json', 'fresh_numeric_semantic_review.json'}
    assert stage['challenge_read'] is False


@pytest.fixture
def actual_concept_fixture(tmp_path):
    tokenizer = IntegrityTokenizer(); rows = [concept_validation_row()]
    text = 'Đưa các phân số về cùng mẫu rồi cộng các tử.'
    tokens = tokenizer.encode(text + tokenizer.eos_token)
    record = {'sample_id': rows[0]['sample_id'], 'grade': rows[0]['grade'], 'mode': rows[0]['mode'],
        'prediction': text, 'generated_ids': tokens, 'generated_tokens': len(tokens), 'eos_observed': True,
        'scores': mixed.score_concept(rows[0], text)}
    path = tmp_path/'actual_concept.jsonl'
    path.write_text(json.dumps(record, ensure_ascii=False)+'\n', encoding='utf-8')
    save_json(path.with_suffix('.metadata.json'), {'model_key': 'fixture', 'ids': [rows[0]['sample_id']],
        'input_sha256': hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        'max_new_tokens': 1000, 'enable_thinking': False, 'do_sample': False, 'batch_size': 4,
        'eos_token_id': tokenizer.eos_token_id})
    save_json(path.with_suffix('.summary.json'), mixed.aggregate_concepts([record]))
    return path, rows, tokenizer, record


def test_concept_audit_reconstructs_actual_tokens_and_scores(actual_concept_fixture):
    path, rows, tokenizer, _ = actual_concept_fixture
    report = mixed.audit_concept_predictions(path, rows, tokenizer)
    assert report['actual_tokens_decoded'] and report['summary_recomputed']


@pytest.mark.parametrize('damage', ['text', 'score', 'eos_tail', 'summary'])
def test_concept_audit_rejects_fabricated_output_or_aggregate(actual_concept_fixture, damage):
    path, rows, tokenizer, record = actual_concept_fixture
    if damage == 'text': record['prediction'] = 'Chuỗi này không được sinh từ token.'
    elif damage == 'score': record['scores']['screened_correct'] = False
    elif damage == 'eos_tail': record['generated_ids'].append(123)
    else: save_json(path.with_suffix('.summary.json'), {'samples': 999})
    path.write_text(json.dumps(record, ensure_ascii=False)+'\n', encoding='utf-8')
    with pytest.raises(ValueError): mixed.audit_concept_predictions(path, rows, tokenizer)


def test_nf4_loader_uses_one_gpu_and_same_norm_preparation_for_base_pair(monkeypatch):
    observed = {}
    class FakeModel:
        is_loaded_in_4bit = True
    class ModelLoader:
        @classmethod
        def from_pretrained(cls, model_id, **kwargs):
            observed['model_id'] = model_id; observed['load'] = kwargs; return FakeModel()
    class Quantization:
        def __init__(self, **kwargs): observed['quantization'] = kwargs
    fake_torch = types.SimpleNamespace(float16='fixture_fp16', cuda=types.SimpleNamespace(is_available=lambda: True))
    monkeypatch.setitem(sys.modules, 'torch', fake_torch)
    monkeypatch.setitem(sys.modules, 'transformers', types.SimpleNamespace(AutoModelForCausalLM=ModelLoader, BitsAndBytesConfig=Quantization))
    def prepare(base, use_gradient_checkpointing):
        observed['prepare_checkpointing'] = use_gradient_checkpointing; return base
    monkeypatch.setitem(sys.modules, 'peft', types.SimpleNamespace(prepare_model_for_kbit_training=prepare))
    config = {'model_id': 'Qwen/Qwen3-4B-Instruct-2507',
              'revision': 'cdbee75f17c01a7cc42f958dc650907174af0554', 'load_in_4bit': True}
    mixed.load_model(config)
    assert observed['load']['revision'] == config['revision'] and observed['load']['device_map'] == {'': 0}
    assert observed['quantization'] == {'load_in_4bit': True, 'bnb_4bit_quant_type': 'nf4',
        'bnb_4bit_use_double_quant': True, 'bnb_4bit_compute_dtype': 'fixture_fp16'}
    assert observed['prepare_checkpointing'] is False

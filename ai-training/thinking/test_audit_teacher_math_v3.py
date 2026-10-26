import copy
import hashlib
import json
import random

import pytest

import audit_teacher_math_v3 as audit
import train_teacher_math_v3 as trainer
from test_train_teacher_math_v3 import example, Tokenizer


def token_item(row, tokenizer):
    value = trainer.serialize(row, tokenizer, 5000)
    return {'sample_id': row['sample_id'], 'prefix_length': value['prefix_length'],
        'completion_length': value['completion_length'],
        'input_ids_sha256': hashlib.sha256(json.dumps(value['input_ids']).encode()).hexdigest(),
        'labels_sha256': hashlib.sha256(json.dumps(value['labels']).encode()).hexdigest()}


def test_actual_token_and_mask_recomputation_rejects_changed_fingerprint():
    row, tokenizer = example(), Tokenizer()
    item = token_item(row, tokenizer)
    assert audit.check_token_item(row, item, tokenizer, 5000) > 0
    item['labels_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='mask differs'):
        audit.check_token_item(row, item, tokenizer, 5000)


def test_training_epoch_commits_all_examples_once_and_preserves_seed_order():
    examples = []
    for i in range(5):
        row = example(); row['sample_id'] = str(i); examples.append(row)
    config = {'seed': 42, 'batch_size': 1, 'accumulation': 2}
    order = list(range(5)); random.Random(42).shuffle(order)
    groups = [order[i:i+2] for i in range(0, len(order), 2)]
    records = [{'step': i+1, 'sample_ids': [str(j) for j in group],
                'loss': 1., 'grad_norm': 2., 'amp_scale': 512., 'overflow_retries': 0}
               for i, group in enumerate(groups)]
    assert audit.check_training_log(examples, records, config, 3)['examples_seen_once'] == 5
    broken = copy.deepcopy(records); broken[-1]['sample_ids'] = [records[0]['sample_ids'][0]]
    with pytest.raises(ValueError, match='exactly once'):
        audit.check_training_log(examples, broken, config, 3)
    broken = copy.deepcopy(records); broken[0]['sample_ids'].reverse()
    with pytest.raises(ValueError, match='batch order'):
        audit.check_training_log(examples, broken, config, 3)


class EvaluationTokenizer(Tokenizer):
    def decode(self, ids, skip_special_tokens=True):
        return ''.join(chr(token-100) for token in ids if token != self.eos_token_id)


def prediction_record(row, tokenizer):
    text = json.dumps(row['target'], ensure_ascii=False)
    ids = tokenizer.encode(text + tokenizer.eos_token)
    return {'sample_id': row['sample_id'], 'grade': row['grade'], 'mode': row['mode'],
        'reference_status': row['target']['status'], 'prediction': text,
        'generated_ids': ids, 'generated_tokens': len(ids), 'eos_observed': True,
        'thought_prefix_open': False, 'scores': trainer.score(row, text)}


def test_recompute_raw_prediction_from_ids_and_scores_detects_fabrication():
    row, tokenizer = example(), EvaluationTokenizer()
    record = prediction_record(row, tokenizer)
    metadata = {'max_new_tokens': 2000, 'enable_thinking': False}
    assert audit.check_prediction(row, record, metadata, tokenizer)['correct']
    record['prediction'] = record['prediction'].replace('"9"', '"8"')
    with pytest.raises(ValueError, match='raw output'):
        audit.check_prediction(row, record, metadata, tokenizer)
    record = prediction_record(row, tokenizer); record['scores']['correct'] = False
    with pytest.raises(ValueError, match='scores differ'):
        audit.check_prediction(row, record, metadata, tokenizer)


def test_open_thought_prefix_not_accepted_from_unproven_record():
    row, tokenizer = example(), EvaluationTokenizer()
    record = prediction_record(row, tokenizer); record['thought_prefix_open'] = True
    with pytest.raises(ValueError, match='Unproven'):
        audit.check_prediction(row, record, {'max_new_tokens': 2000, 'enable_thinking': False}, tokenizer)


def test_eos_and_budget_cannot_be_fabricated():
    row, tokenizer = example(), EvaluationTokenizer()
    record = prediction_record(row, tokenizer)
    record['generated_ids'].append(100)
    with pytest.raises(ValueError, match='beyond first EOS'):
        audit.check_prediction(row, record, {'max_new_tokens': 2000, 'enable_thinking': False}, tokenizer)
    record = prediction_record(row, tokenizer)
    with pytest.raises(ValueError, match='budget'):
        audit.check_prediction(row, record, {'max_new_tokens': 1, 'enable_thinking': False}, tokenizer)

"""Recompute saved v2 evidence; a passing audit does not certify school coverage."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random

from verified_math_data_v2 import evaluate_expression, validate
from verified_math_training_v2 import aggregate, collate, messages, score, serialize
from train_verified_math_v2_stable import MODEL, REVISION, RUN_ID


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def summaries(records):
    result = aggregate(records)
    result['per_grade'] = {str(grade): aggregate([row for row in records if row['grade'] == grade])
                           for grade in sorted({row['grade'] for row in records}, key=str)}
    result['per_topic'] = {topic: aggregate([row for row in records if row['topic'] == topic])
                           for topic in sorted({row['topic'] for row in records})}
    return result


def audit_predictions(run, name, references, expected_key, tokenizer, config):
    saved = read_rows(run / (name + '.jsonl'))
    metadata = read_json(run / (name + '.metadata.json'))
    expected_ids = [row['sample_id'] for row in references]
    assert metadata['ids'] == expected_ids, 'Evaluation metadata IDs changed'
    assert metadata['key'] == expected_key, 'Evaluation model identity changed'
    assert metadata['greedy'] is True and metadata['enable_thinking'] is False
    assert metadata['max_new_tokens'] == config['max_new_tokens']
    assert metadata['batch_size'] == config['eval_batch_size']
    if 'eos_token_id' in metadata:
        assert metadata['eos_token_id'] == tokenizer.eos_token_id
    assert [row['sample_id'] for row in saved] == expected_ids, 'Evaluation IDs absent/repeated/reordered'
    assert len(set(expected_ids)) == len(expected_ids)
    rebuilt = []
    for prediction, reference in zip(saved, references):
        token_ids = prediction['generated_ids']
        assert isinstance(token_ids, list) and token_ids and all(type(value) is int for value in token_ids)
        assert len(token_ids) == prediction['generated_tokens']
        assert len(token_ids) <= config['max_new_tokens']
        ended = tokenizer.eos_token_id in token_ids
        if ended:
            assert token_ids[-1] == tokenizer.eos_token_id
            assert token_ids.count(tokenizer.eos_token_id) == 1
        truncated = not ended and len(token_ids) >= config['max_new_tokens']
        assert ended or truncated, 'Generation has neither completed EOS nor reached length limit'
        assert tokenizer.decode(token_ids, skip_special_tokens=True) == prediction['prediction']
        fresh_score = score(reference, prediction['prediction'], truncated=truncated)
        assert fresh_score == prediction['scores'], 'Cached scores disagree with independent recomputation'
        assert prediction['reference_status'] == reference['target']['status']
        assert prediction['grade'] == reference.get('grade')
        assert prediction['topic'] == reference.get('topic', 'public_source')
        rebuilt.append(dict(prediction, scores=fresh_score))
    summary = summaries(rebuilt)
    assert summary == read_json(run / (name + '.summary.json')), 'Saved evaluation summary disagrees'
    assert summary['coverage'] is None or 0 <= summary['coverage'] <= 1
    return summary


def audit(root, tokenizer=None):
    root = Path(root)
    run = root / 'runs' / RUN_ID
    # No successful audit is written until every completed-run check passes.
    completed = read_json(run / 'completed_run.json')
    config = read_json(run / 'config.json')
    selection = read_json(run / 'selection.json')
    frozen = read_json(root / 'data' / 'frozen_manifest.json')
    assert completed['run_id'] == config['run_id'] == RUN_ID
    assert config['model_id'] == MODEL and config['revision'] == REVISION
    assert config['epochs'] == completed['epochs'] == 1
    assert completed['production_approved'] is False and selection['production_approved'] is False
    split = {name: read_rows(root / 'data' / (name + '.jsonl')) for name in ('train', 'val', 'test')}
    fingerprints = {name: sha(root / 'data' / (name + '.jsonl')) for name in split}
    assert fingerprints == config['dataset_fingerprints'] == frozen['fingerprints']
    assert set(config['source_hashes']) >= {'verified_math_data_v2.py', 'verified_math_training_v2.py', 'train_verified_math_v2_stable.py'}
    for name, expected_hash in config['source_hashes'].items():
        assert Path(name).name == name, 'Source hash must use a filename within src'
        assert sha(root / 'src' / name) == expected_hash, 'Frozen source modified: ' + name
    if 'source_hashes' in frozen:
        for name, expected_hash in frozen['source_hashes'].items():
            assert Path(name).name == name
            assert sha(root / 'src' / name) == expected_hash
    all_rows = [row for part in split.values() for row in part]
    assert len({row['sample_id'] for row in all_rows}) == len(all_rows)
    assert len({row['problem'] for row in all_rows}) == len(all_rows)
    synthetic = [row for row in all_rows if row.get('source', '').startswith('programmatic_known')]
    validate(synthetic)
    public = [row for row in all_rows if not row.get('source', '').startswith('programmatic_known')]
    for row in all_rows:
        if row['target']['status'] == 'solve':
            assert evaluate_expression(row['target']['expr'], row['facts']) == Fraction(row['oracle_answer'])
        else:
            assert row['oracle_answer'] is None
            assert row['target']['expr'] is None and row['target']['unit'] is None
    assert all(row['split'] == 'train' for row in public), 'Public source rows leaked into heldout evaluation'
    for name in ('val', 'test'):
        assert {row['grade'] for row in split[name]} == {1, 2, 3, 4, 5}
    if tokenizer is None:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    encoded = [serialize(row, tokenizer, config['max_length']) for row in split['train']]
    token_audit = read_json(run / 'token_audit.json')
    assert token_audit['samples'] == len(encoded) == completed['train_examples_seen']
    assert token_audit['training_ids'] == [row['sample_id'] for row in split['train']]
    assert token_audit['min_length'] == min(len(row['input_ids']) for row in encoded)
    assert token_audit['max_length'] == max(len(row['input_ids']) for row in encoded) <= config['max_length']
    assert token_audit['truncated'] == 0 and token_audit['assistant_only_loss'] is True
    for row, item in zip(split['train'], encoded):
        prefix_text = tokenizer.apply_chat_template(messages(row), tokenize=False,
                        add_generation_prompt=True, enable_thinking=False)
        prefix = tokenizer.encode(prefix_text, add_special_tokens=False)
        completion = tokenizer.encode(json.dumps(row['target'], ensure_ascii=False, separators=(',', ':'))
                        + tokenizer.eos_token, add_special_tokens=False)
        assert item['input_ids'] == prefix + completion
        assert item['labels'] == [-100] * len(prefix) + completion
        assert item['attention_mask'] == [1] * len(item['input_ids'])
    padded = collate([encoded[0], {'input_ids': [1], 'labels': [1], 'attention_mask': [1]}], tokenizer.pad_token_id)
    assert padded['labels'][1][1:] == [-100] * (len(encoded[0]['input_ids']) - 1)
    assert padded['attention_mask'][1][1:] == [0] * (len(encoded[0]['input_ids']) - 1)
    order = list(range(len(split['train'])))
    random.Random(config['seed']).shuffle(order)
    batches = [order[index:index + config['batch_size']] for index in range(0, len(order), config['batch_size'])]
    expected_steps = math.ceil(len(batches) / config['accumulation'])
    assert expected_steps == config['updates'] == completed['steps']
    log = read_rows(run / 'training_log.jsonl')
    assert [row['step'] for row in log] == list(range(1, expected_steps + 1))
    trained_ids, seen = [], 0
    for index, entry in enumerate(log):
        expected_indices = [value for batch in batches[index * config['accumulation']:(index + 1) * config['accumulation']] for value in batch]
        expected_ids = [split['train'][value]['sample_id'] for value in expected_indices]
        assert entry['batch_ids'] == expected_ids, 'Training order differs or resume repeated a batch'
        seen += len(expected_ids)
        assert entry['examples_seen'] == seen
        assert math.isfinite(entry['loss']) and math.isfinite(entry['grad_norm'])
        trained_ids.extend(entry['batch_ids'])
    assert Counter(trained_ids) == Counter(row['sample_id'] for row in split['train'])
    assert len(trained_ids) == len(set(trained_ids)), 'Training sample repeated within the single epoch'
    adapter_hash = sha(run / 'adapter' / 'adapter_model.safetensors')
    assert adapter_hash == completed['adapter_sha256']
    reload_evidence = read_json(run / 'reload_verification.json')
    assert reload_evidence['passed'] is True and completed['reload_verified'] is True
    assert reload_evidence['fresh_base_revision'] == REVISION and reload_evidence['tensor_count'] > 0
    baseline = audit_predictions(run, 'baseline_val', split['val'], 'base:' + REVISION, tokenizer, config)
    candidate = audit_predictions(run, 'candidate_val', split['val'], 'adapter:' + adapter_hash, tokenizer, config)
    per_grade_ok = all(candidate['per_grade'][grade]['solvable_correct'] >= original['solvable_correct']
                       for grade, original in baseline['per_grade'].items())
    plan_ok = candidate['plan_exact'] >= baseline['plan_exact']
    improved = (candidate['solvable_correct'] > baseline['solvable_correct']
                and candidate['guard_correct'] >= baseline['guard_correct'] and per_grade_ok and plan_ok)
    selected = 'adapter' if improved else 'base'
    assert selection['selected'] == completed['selected'] == selected
    assert selection['candidate_improved'] == improved
    assert selection['per_grade_non_regression'] == per_grade_ok
    if 'plan_non_regression' in selection:
        assert selection['plan_non_regression'] == plan_ok
    assert selection['criterion'] == config['criterion']
    assert selection['test_used_for_selection'] is False
    expected_status = 'SFT_COMPLETED_RESEARCH_ONLY' if improved else 'SFT_REJECTED_VALIDATION_NONIMPROVEMENT'
    assert completed['status'] == expected_status
    test_key = 'adapter:' + adapter_hash if selected == 'adapter' else 'base:' + REVISION
    dev_test = audit_predictions(run, 'selected_dev_test', split['test'], test_key, tokenizer, config)
    assert baseline == completed['baseline_validation']
    assert candidate == completed['candidate_validation']
    assert dev_test == completed['selected_development_test']
    result = {
        'status': 'PASSED', 'run_id': RUN_ID, 'training_steps': expected_steps,
        'training_samples_exactly_once': len(trained_ids), 'source_and_data_hashes_verified': True,
        'token_masks_and_padding_recomputed_with_pinned_tokenizer': True,
        'all_prediction_token_ids_text_scores_and_summaries_recomputed': True,
        'split_invariants_verified': True, 'selected_by_validation_only': True,
        'selected': selected, 'per_grade_math_non_regression': per_grade_ok,
        'canonical_plan_non_regression': plan_ok, 'adapter_sha256': adapter_hash,
        'fresh_base_reload_evidence_verified': True, 'production_approved': False,
        'does_not_certify_arbitrary_problem_semantics_or_pedagogy': True,
        'limitations': [
            'Finite synthetic phrases and numeric cases; not a secret independent teacher benchmark.',
            'Answer accuracy measures model plans evaluated by exact arithmetic; raw numeric LLM reasoning is not certified.',
            'Canonical plan equality is stricter than mathematical equivalence and can reject valid alternative plans.',
            'Public train arithmetic/provenance do not certify semantic correctness.',
        ],
    }
    path = run / 'reviewer_audit.json'
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    temporary.replace(path)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.root), ensure_ascii=False))

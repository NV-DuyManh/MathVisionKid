"""Recompute v3 evidence from frozen inputs and actually generated token IDs."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import re

import train_teacher_math_v3 as trainer


def check_token_item(row, item, tokenizer, max_length):
    """Rebuild masks independently of the training serialize() implementation."""
    prefix_text = tokenizer.apply_chat_template(trainer.messages(row), tokenize=False,
                       add_generation_prompt=True, enable_thinking=False)
    prefix = tokenizer.encode(prefix_text, add_special_tokens=False)
    target = json.dumps(row['target'], ensure_ascii=False, separators=(',', ':'))
    completion = tokenizer.encode(target + tokenizer.eos_token, add_special_tokens=False)
    ids = prefix + completion
    labels = [-100] * len(prefix) + completion
    if len(ids) > max_length or completion[-1] != tokenizer.eos_token_id:
        raise ValueError('Token truncation or wrong completion EOS')
    expected = {'sample_id': row['sample_id'], 'prefix_length': len(prefix),
                'completion_length': len(completion),
                'input_ids_sha256': hashlib.sha256(json.dumps(ids).encode()).hexdigest(),
                'labels_sha256': hashlib.sha256(json.dumps(labels).encode()).hexdigest()}
    if expected != item: raise ValueError('Actual recomputed completion-only token mask differs')
    padded = trainer.collate([{'input_ids': ids, 'attention_mask': [1] * len(ids), 'labels': labels},
                             {'input_ids': ids + [1], 'attention_mask': [1] * (len(ids) + 1), 'labels': labels + [1]}], tokenizer.pad_token_id)
    if padded['labels'][0][-1] != -100 or padded['attention_mask'][0][-1] != 0:
        raise ValueError('Padding participates in training loss')
    return len(ids)


def check_training_log(examples, records, config, expected_steps):
    expected_ids = [row['sample_id'] for row in examples]
    seen = [sample for record in records for sample in record['sample_ids']]
    if len(records) != expected_steps or [r['step'] for r in records] != list(range(1, expected_steps + 1)):
        raise ValueError('Committed training steps are missing or duplicated')
    if sorted(seen) != sorted(expected_ids) or len(seen) != len(set(seen)):
        raise ValueError('Every training sample must occur exactly once in the committed epoch')
    import random
    order = list(range(len(examples))); random.Random(config['seed']).shuffle(order)
    batch = config['batch_size']; accumulation = config['accumulation']
    batches = [order[i:i + batch] for i in range(0, len(order), batch)]
    groups = [batches[i:i + accumulation] for i in range(0, len(batches), accumulation)]
    for record, group in zip(records, groups):
        if record['sample_ids'] != [examples[i]['sample_id'] for indices in group for i in indices]:
            raise ValueError('Committed batch order differs from fixed-seed ordering')
        if not all(__import__('math').isfinite(record[key]) for key in ('loss', 'grad_norm', 'amp_scale')):
            raise ValueError('Nonfinite committed update')
    return {'steps': len(records), 'examples_seen_once': len(seen),
            'overflow_retries': sum(row['overflow_retries'] for row in records)}


def check_prediction(row, record, metadata, tokenizer):
    ids = record['generated_ids']
    if not isinstance(ids, list) or not all(isinstance(token, int) for token in ids):
        raise ValueError('Raw generated token IDs absent or invalid')
    ended = tokenizer.eos_token_id in ids
    if ended and ids.index(tokenizer.eos_token_id) != len(ids) - 1:
        raise ValueError('Generated token list continues beyond first EOS')
    if len(ids) > metadata['max_new_tokens']: raise ValueError('Generated token budget violated')
    text = tokenizer.decode(ids, skip_special_tokens=True)
    if text != record['prediction'] or len(ids) != record['generated_tokens'] or ended != record['eos_observed']:
        raise ValueError('Generated IDs do not reconstruct recorded raw output')
    template = tokenizer.apply_chat_template(trainer.messages(row), tokenize=False,
                add_generation_prompt=True, enable_thinking=metadata['enable_thinking'])
    prefix_open = bool(re.search(r'<think>\s*$', template))
    if prefix_open != record.get('thought_prefix_open', False): raise ValueError('Unproven open-thought prefix')
    truncated = not ended and len(ids) >= metadata['max_new_tokens']
    expected = trainer.score(row, text, truncated, thought_prefix_open=prefix_open)
    if expected != record['scores']: raise ValueError('Prediction scores differ on independent recomputation')
    if record['reference_status'] != row['target']['status'] or record['mode'] != row['mode'] or record['grade'] != row['grade']:
        raise ValueError('Prediction associated with wrong reference')
    return expected


def check_evaluation(path, by_id, tokenizer):
    metadata = json.loads(path.with_suffix('.metadata.json').read_text(encoding='utf-8'))
    records = trainer.rows(path)
    if [r['sample_id'] for r in records] != metadata['ids'] or len(metadata['ids']) != len(set(metadata['ids'])):
        raise ValueError('Evaluation IDs/order/duplicates changed')
    examples = [by_id[sample_id] for sample_id in metadata['ids']]
    digest = hashlib.sha256(json.dumps(examples, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if digest != metadata['input_sha256']: raise ValueError('Evaluation input fingerprint mismatch')
    if metadata['enable_thinking']:
        if not metadata['do_sample'] or (metadata['temperature'], metadata['top_p'], metadata['top_k']) != (.6, .95, 20):
            raise ValueError('Thinking diagnostic uses an undocumented sampling protocol')
    elif metadata['do_sample']:
        raise ValueError('Primary no-thinking metric is not deterministic greedy')
    for row, record in zip(examples, records): check_prediction(row, record, metadata, tokenizer)
    summary = trainer.aggregate(records)
    summary['per_grade'] = {str(grade): trainer.aggregate([r for r in records if r['grade'] == grade])
                            for grade in sorted({r['grade'] for r in records}, key=str)}
    summary['per_topic'] = {topic: trainer.aggregate([r for r in records if r['topic'] == topic])
                            for topic in sorted({r['topic'] for r in records})}
    stored = json.loads(path.with_suffix('.summary.json').read_text(encoding='utf-8'))
    if summary != stored: raise ValueError('Stored aggregate differs from actual prediction scores')
    return {'samples': len(records), 'truncated': summary['truncated'], 'enable_thinking': metadata['enable_thinking'],
            'model_key': metadata['model_key'], 'max_new_tokens': metadata['max_new_tokens'], 'summary_recomputed': True}


def audit(root, run_id, tokenizer=None):
    root = Path(root); run = root / 'runs' / run_id
    config = json.loads((run / 'config.json').read_text(encoding='utf-8'))
    trainer.bind_data_system(config)
    fingerprints = {split: trainer.sha(root / 'data' / (split + '.jsonl')) for split in config['dataset_fingerprints']}
    if fingerprints != config['dataset_fingerprints']: raise ValueError('Frozen data bytes changed')
    source_checks = {name: trainer.sha(root / 'src' / name) for name in config['source_hashes']}
    if source_checks != config['source_hashes']: raise ValueError('Frozen trainer/source changed')
    splits = {split: trainer.rows(root / 'data' / (split + '.jsonl')) for split in fingerprints}
    data_module = importlib.import_module(config['data_module'])
    data_module.validate([row for values in splits.values() for row in values])
    by_id = {row['sample_id']: row for values in splits.values() for row in values}
    if len(by_id) != sum(len(values) for values in splits.values()): raise ValueError('Split sample IDs overlap')
    train = splits['train'][:config['train_limit']] if config['train_limit'] else splits['train']
    if tokenizer is None: tokenizer = trainer.get_tokenizer(config)
    token_audit = json.loads((run / 'token_audit.json').read_text(encoding='utf-8'))
    if [item['sample_id'] for item in token_audit['items']] != [row['sample_id'] for row in train]:
        raise ValueError('Token audit does not cover exact committed train subset')
    lengths = [check_token_item(row, item, tokenizer, config['max_length'])
               for row, item in zip(train, token_audit['items'])]
    if token_audit['truncated'] != 0 or token_audit['min_length'] != min(lengths) or token_audit['max_length'] != max(lengths):
        raise ValueError('Token audit length/truncation summary differs')
    completed = json.loads((run / 'completed_run.json').read_text(encoding='utf-8'))
    train_complete = json.loads((run / 'training_complete.json').read_text(encoding='utf-8'))
    training = check_training_log(train, trainer.rows(run / 'training_log.jsonl'), config, completed['steps'])
    if completed['steps'] != train_complete['steps']: raise ValueError('Completion step counts differ')
    if trainer.sha(run / 'adapter' / 'adapter_model.safetensors') != completed['adapter_sha256']:
        raise ValueError('Adapter artifact fingerprint mismatch')
    from safetensors.torch import load_file
    tensors = load_file(str(run / 'adapter' / 'adapter_model.safetensors'), device='cpu')
    actual_tensors = {key: hashlib.sha256(value.float().contiguous().numpy().tobytes()).hexdigest()
                      for key, value in tensors.items()}
    if actual_tensors != train_complete['adapter_tensor_hashes']:
        raise ValueError('Saved adapter tensors differ from the training completion witness')
    del tensors
    reload = json.loads((run / 'reload_verification.json').read_text(encoding='utf-8'))
    if not reload['passed'] or reload['fresh_base_revision'] != config['revision']:
        raise ValueError('Fresh pinned-base reload not verified')
    evaluations = {path.stem: check_evaluation(path, by_id, tokenizer)
                   for path in run.glob('*.jsonl') if path.with_suffix('.metadata.json').exists()}
    baseline = json.loads((run / 'baseline_val.summary.json').read_text(encoding='utf-8'))
    candidate = json.loads((run / 'candidate_val.summary.json').read_text(encoding='utf-8'))
    expected_selection = trainer.select_candidate(baseline, candidate)
    actual_selection = json.loads((run / 'selection.json').read_text(encoding='utf-8'))
    if actual_selection != expected_selection: raise ValueError('Checkpoint selection differs from declared validation rule')
    baseline_meta = json.loads((run / 'baseline_val.metadata.json').read_text(encoding='utf-8'))
    candidate_meta = json.loads((run / 'candidate_val.metadata.json').read_text(encoding='utf-8'))
    if baseline_meta['ids'] != candidate_meta['ids'] or baseline_meta['input_sha256'] != candidate_meta['input_sha256']:
        raise ValueError('Baseline/candidate validation does not use identical examples')
    for name, evidence in evaluations.items():
        if name.startswith('selected_'):
            expected_key = ('adapter:' + completed['adapter_sha256']) if expected_selection['selected'] == 'adapter' else 'base:' + config['model_id'] + ':' + config['revision']
            if evidence['model_key'] != expected_key: raise ValueError('Heldout evaluated with unselected weights')
    result = {'status': 'PASSED', 'all_passed': True, 'run_id': run_id, 'training': training,
        'data_fingerprints_verified': True, 'source_fingerprints_verified': True,
        'teacher_formula_and_split_invariants_verified': True, 'actual_adapter_tensor_count': len(actual_tensors),
        'actual_token_masks_recomputed': len(lengths), 'evaluation_files': evaluations,
        'checkpoint_selection_recomputed': True, 'production_approved': False,
        'limitations': 'Technical reproducibility audit, not teacher certification of Vietnamese semantics, hints, curriculum mastery or OCR.'}
    trainer.save(run / 'reviewer_audit.json', result)
    print('MVK_TEACHER_V3_AUDIT=' + json.dumps(result, ensure_ascii=False), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', required=True); parser.add_argument('--run-id', required=True)
    args = parser.parse_args(); audit(args.root, args.run_id)

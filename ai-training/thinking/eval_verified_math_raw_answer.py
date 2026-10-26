"""Post-hoc answer-only validation diagnostic; never changes planner selection.

The model must give the numeric answer itself. No fact list, plan interpreter,
gold answer, or calculator supplies that answer at inference time.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import unicodedata

MODEL = 'Qwen/Qwen3-0.6B'
REVISION = 'c1899de289a04d12100db370d81485cdf75e47ca'
PROTOCOL = 'raw_answer_posthoc_validation_v1'
SYSTEM = (
    'Giải bài toán tiểu học Việt Nam và chỉ trả một JSON có đúng hai trường answer,unit. '
    'answer là chuỗi số nguyên, phân số a/b hoặc số thập phân dùng một dấu phẩy hay dấu chấm. '
    'Không dùng dấu phân cách hàng nghìn. unit là chuỗi đơn vị đáp số; dùng chuỗi rỗng nếu không có đơn vị. '
    'Nếu đề thiếu dữ kiện hoặc yêu cầu ngoài toán tiểu học, trả answer:null,unit:null. '
    'Tự tính đáp số; không trả mã dữ kiện f0,f1, biểu thức hay kế hoạch. Không viết nội dung ngoài JSON.'
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                   separators=(',', ':')).encode('utf-8')).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    temporary.replace(path)


def numeric_answer(text):
    """Explicit single-mark decimal grammar, never float arithmetic or locale guessing."""
    if type(text) is not str or len(text) > 64:
        raise ValueError('ANSWER_MUST_BE_BOUNDED_NUMERIC_STRING')
    text = text.strip()
    text = re.sub(r'\s*/\s*', '/', text)
    if not re.fullmatch(r'[+-]?(?:0|[1-9][0-9]{0,17})(?:[.,][0-9]{1,12}|/[1-9][0-9]{0,17})?', text):
        raise ValueError('NOT_AN_EXPLICIT_NUMERIC_ANSWER')
    value = Fraction(text.replace(',', '.'))
    if abs(value) > 10**12 or value.denominator > 10**12:
        raise ValueError('NUMERIC_ANSWER_LIMIT')
    return value


def unit(text):
    if type(text) is not str or len(text) > 100:
        raise ValueError('UNIT_MUST_BE_BOUNDED_STRING')
    text = ' '.join(unicodedata.normalize('NFC', text).strip().split())
    return re.sub(r'\^\s*([23])', lambda match: '²' if match[1] == '2' else '³', text)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def final_object(text, truncated=False):
    if truncated or type(text) is not str or len(text) > 8000:
        raise ValueError('INCOMPLETE_OR_INVALID_OUTPUT')
    text = text.strip()
    if '<think>' in text or '</think>' in text:
        if text.count('<think>') != 1 or text.count('</think>') != 1 or not text.startswith('<think>'):
            raise ValueError('UNFINISHED_OR_MULTIPLE_THOUGHTS')
        ending = text.index('</think>')
        if ending < len('<think>'):
            raise ValueError('MISORDERED_THOUGHT')
        text = text[ending + len('</think>'):].strip()
    if text.startswith('```'):
        match = re.fullmatch(r'```(?:json)?\s*([\s\S]+?)\s*```', text)
        if not match:
            raise ValueError('UNMATCHED_JSON_FENCE')
        text = match[1].strip()
    try:
        value = json.loads(text, object_pairs_hook=unique_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError('NONFINITE_JSON')))
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError('NOT_ONE_COMPLETE_JSON_OBJECT') from error
    if type(value) is not dict:
        raise ValueError('NOT_A_JSON_OBJECT')
    return value


def parse_answer(text, truncated=False):
    parsed = final_object(text, truncated)
    if set(parsed) != {'answer', 'unit'}:
        raise ValueError('RAW_ANSWER_SCHEMA_MISMATCH')
    if parsed['answer'] is None:
        if parsed['unit'] is not None:
            raise ValueError('NULL_ANSWER_MUST_HAVE_NULL_UNIT')
    elif type(parsed['answer']) is not str or type(parsed['unit']) is not str:
        raise ValueError('ANSWER_AND_UNIT_MUST_BE_STRINGS')
    return parsed


def messages(row):
    payload = {'grade': row['grade'], 'question': row['problem']}
    return [{'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}]


def score(row, text, truncated=False):
    result = {'schema_valid': False, 'answered': False, 'numeric_attempt': False,
              'numeric_answer_correct': False, 'unit_correct': False, 'correct': False,
              'guard_correct': False, 'wrong_completed_answer': False,
              'invalid_numeric_answer': False, 'fact_reference_emitted': False,
              'planner_schema_emitted': False, 'truncated': bool(truncated)}
    try:
        obj = final_object(text, truncated)
        result['fact_reference_emitted'] = bool(re.search(r'\bf[0-9]+\b', json.dumps(obj, ensure_ascii=False)))
        result['planner_schema_emitted'] = set(obj) == {'status', 'expr', 'unit'}
        parsed = parse_answer(text, truncated)
    except (ValueError, TypeError):
        return result
    result['schema_valid'] = True
    solvable = row['target']['status'] == 'solve'
    if parsed['answer'] is None:
        result['guard_correct'] = not solvable
        result['correct'] = not solvable
        return result
    result['numeric_attempt'] = True
    try:
        value = numeric_answer(parsed['answer'])
    except (ValueError, TypeError, ZeroDivisionError):
        result['invalid_numeric_answer'] = True
        return result
    result['answered'] = True
    if solvable:
        result['numeric_answer_correct'] = value == Fraction(row['oracle_answer'])
        try:
            result['unit_correct'] = unit(parsed['unit']) == unit(row['target']['unit'])
        except (ValueError, TypeError):
            result['unit_correct'] = False
        result['correct'] = result['numeric_answer_correct'] and result['unit_correct']
    result['wrong_completed_answer'] = not result['correct']
    return result


def aggregate(records):
    solved = [record for record in records if record['reference_status'] == 'solve']
    guards = [record for record in records if record['reference_status'] != 'solve']
    count = lambda key, subset: sum(bool(record['scores'][key]) for record in subset)
    answered = count('answered', solved)
    correct = count('correct', solved)
    return {
        'samples': len(records), 'solvable_samples': len(solved), 'solvable_correct': correct,
        'solvable_raw_answer_accuracy': correct / len(solved) if solved else None,
        'numeric_answer_correct': count('numeric_answer_correct', solved),
        'numeric_answer_accuracy': count('numeric_answer_correct', solved) / len(solved) if solved else None,
        'answered_solvable': answered, 'solvable_coverage': answered / len(solved) if solved else None,
        'accuracy_when_answered': correct / answered if answered else None,
        'numeric_accuracy_when_answered': count('numeric_answer_correct', solved) / answered if answered else None,
        'guard_samples': len(guards), 'guard_correct': count('guard_correct', guards),
        'guard_false_answers': count('answered', guards), 'schema_valid': count('schema_valid', records),
        'invalid_numeric_answers': count('invalid_numeric_answer', records),
        'wrong_completed_answers': count('wrong_completed_answer', records),
        'planner_schema_emitted': count('planner_schema_emitted', records),
        'fact_reference_emitted': count('fact_reference_emitted', records),
        'truncated': count('truncated', records),
        'metric': 'numeric answer generated by LLM + explicit unit; no plan-calculator answer is supplied',
    }


def summary(records):
    result = aggregate(records)
    result['per_grade'] = {str(grade): aggregate([record for record in records if record['grade'] == grade])
                           for grade in sorted({record['grade'] for record in records}, key=str)}
    result['per_topic'] = {topic: aggregate([record for record in records if record['topic'] == topic])
                           for topic in sorted({record['topic'] for record in records})}
    return result


def recompute_record(record, row, tokenizer, max_tokens):
    ids = record['generated_ids']
    if (type(ids) is not list or not ids or any(type(value) is not int for value in ids)
            or len(ids) != record['generated_tokens'] or len(ids) > max_tokens):
        raise ValueError('INVALID_RAW_TOKEN_EVIDENCE')
    ended = tokenizer.eos_token_id in ids
    if ended and (ids[-1] != tokenizer.eos_token_id or ids.count(tokenizer.eos_token_id) != 1):
        raise ValueError('EOS_NOT_CANONICAL')
    truncated = not ended and len(ids) >= max_tokens
    if not ended and not truncated:
        raise ValueError('GENERATION_NEITHER_COMPLETE_NOR_LENGTH_LIMITED')
    text = tokenizer.decode(ids, skip_special_tokens=True)
    if text != record['prediction'] or digest(ids) != record['generated_ids_sha256']:
        raise ValueError('PREDICTION_OR_TOKEN_HASH_CHANGED')
    if record['reference_status'] != row['target']['status'] or record['grade'] != row['grade'] or record['topic'] != row['topic']:
        raise ValueError('PREDICTION_REFERENCE_CHANGED')
    scores = score(row, text, truncated)
    if scores != record['scores']:
        raise ValueError('CACHED_RAW_SCORES_CHANGED')
    return dict(record, scores=scores)


def evaluate(model, tokenizer, examples, path, model_key, validation_sha256, source_sha256,
             max_tokens=128, batch_size=8):
    import torch
    path = Path(path)
    metadata = {'protocol': PROTOCOL, 'model_key': model_key,
                'ids': [row['sample_id'] for row in examples],
                'validation_sha256': validation_sha256, 'evaluator_sha256': source_sha256,
                'system_sha256': digest(SYSTEM), 'greedy': True, 'enable_thinking': False,
                'max_new_tokens': max_tokens, 'batch_size': batch_size, 'eos_token_id': tokenizer.eos_token_id}
    metadata_path = path.with_suffix('.metadata.json')
    if metadata_path.exists():
        if read_json(metadata_path) != metadata:
            raise ValueError('DIAGNOSTIC_PROTOCOL_CHANGED_USE_NEW_DIRECTORY')
    else:
        write_json(metadata_path, metadata)
    references = {row['sample_id']: row for row in examples}
    saved = read_rows(path) if path.exists() else []
    if len({row['sample_id'] for row in saved}) != len(saved):
        raise ValueError('DUPLICATE_CACHED_IDS')
    if any(record['sample_id'] not in references for record in saved):
        raise ValueError('UNKNOWN_CACHED_ID')
    cached = {record['sample_id']: recompute_record(record, references[record['sample_id']], tokenizer, max_tokens)
              for record in saved}
    model.eval()
    model.config.use_cache = True
    tokenizer.padding_side = 'left'
    for start in range(0, len(examples), batch_size):
        batch = [row for row in examples[start:start + batch_size] if row['sample_id'] not in cached]
        if not batch:
            continue
        strings = [tokenizer.apply_chat_template(messages(row), tokenize=False,
                    add_generation_prompt=True, enable_thinking=False) for row in batch]
        inputs = tokenizer(strings, padding=True, return_tensors='pt', add_special_tokens=False).to('cuda')
        with torch.inference_mode():
            generated = model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False,
                         pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id)
        for index, row in enumerate(batch):
            ids = generated[index, inputs['input_ids'].shape[-1]:].tolist()
            if tokenizer.eos_token_id in ids:
                ids = ids[:ids.index(tokenizer.eos_token_id) + 1]
            truncated = tokenizer.eos_token_id not in ids and len(ids) >= max_tokens
            text = tokenizer.decode(ids, skip_special_tokens=True)
            record = {'sample_id': row['sample_id'], 'grade': row['grade'], 'topic': row['topic'],
                      'reference_status': row['target']['status'], 'prediction': text,
                      'generated_ids': ids, 'generated_ids_sha256': digest(ids), 'generated_tokens': len(ids),
                      'scores': score(row, text, truncated)}
            cached[row['sample_id']] = recompute_record(record, row, tokenizer, max_tokens)
        temporary = path.with_suffix('.jsonl.tmp')
        temporary.write_text(''.join(json.dumps(cached[row['sample_id']], ensure_ascii=False) + '\n'
                             for row in examples if row['sample_id'] in cached), encoding='utf-8', newline='\n')
        temporary.replace(path)
        print(f'RAW_ANSWER_DIAGNOSTIC {path.stem} {len(cached)}/{len(examples)}', flush=True)
    final = [recompute_record(cached[row['sample_id']], row, tokenizer, max_tokens) for row in examples]
    result = summary(final)
    write_json(path.with_suffix('.summary.json'), result)
    return result


def inspect_planner_baseline(path):
    result = {'samples': 0, 'solve_json_objects': 0, 'expr_with_fact_refs': 0,
              'expr_without_fact_refs': 0, 'numeric_literal_only_expr': 0,
              'malformed_or_other_schema': 0,
              'interpretation': 'Protocol inspection only; literal plans can reflect math knowledge despite planner-schema failure.'}
    for record in read_rows(path):
        result['samples'] += 1
        try:
            parsed = final_object(record['prediction'], record['scores']['truncated'])
        except (ValueError, TypeError):
            result['malformed_or_other_schema'] += 1
            continue
        if set(parsed) != {'status', 'expr', 'unit'}:
            result['malformed_or_other_schema'] += 1
            continue
        if parsed['status'] == 'solve' and type(parsed['expr']) is str:
            result['solve_json_objects'] += 1
            if re.search(r'\bf\d+\b', parsed['expr']):
                result['expr_with_fact_refs'] += 1
            else:
                result['expr_without_fact_refs'] += 1
                result['numeric_literal_only_expr'] += bool(re.fullmatch(r'[\s0-9.,()+*/%\-]+', parsed['expr']))
    return result


def main(root, run_id):
    import gc
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    root = Path(root)
    if not re.fullmatch(r'[a-z][a-z0-9_]{1,127}', run_id):
        raise ValueError('EXPLICIT_RUN_ID_MUST_BE_A_DIRECTORY_NAME')
    run = root / 'runs' / run_id
    completed = read_json(run / 'completed_run.json')
    config = read_json(run / 'config.json')
    frozen = read_json(root / 'data' / 'frozen_manifest.json')
    if config['run_id'] != run_id or completed['run_id'] != run_id:
        raise ValueError('RUN_ID_MISMATCH')
    if config['model_id'] != MODEL or config['revision'] != REVISION:
        raise ValueError('UNEXPECTED_PINNED_BASE')
    for name, expected in config['source_hashes'].items():
        if Path(name).name != name or sha(root / 'src' / name) != expected:
            raise ValueError('FROZEN_CORE_SOURCE_CHANGED')
    fingerprints = {split: sha(root / 'data' / (split + '.jsonl')) for split in ('train', 'val', 'test')}
    if fingerprints != config['dataset_fingerprints'] or fingerprints != frozen['fingerprints']:
        raise ValueError('FROZEN_DATA_CHANGED')
    adapter_hash = sha(run / 'adapter' / 'adapter_model.safetensors')
    if adapter_hash != completed['adapter_sha256']:
        raise ValueError('ADAPTER_HASH_CHANGED')
    examples = read_rows(root / 'data' / 'val.jsonl')
    if len({row['sample_id'] for row in examples}) != len(examples):
        raise ValueError('VALIDATION_IDS_NOT_UNIQUE')
    diagnostic = run / 'raw_answer_diagnostic_v1'
    diagnostic.mkdir(parents=True, exist_ok=True)
    diagnostic_config = {'protocol': PROTOCOL, 'run_id': run_id, 'training_performed': False,
                         'protocol_changed_posthoc': True, 'used_for_planner_checkpoint_selection': False,
                         'model_id': MODEL, 'revision': REVISION, 'adapter_sha256': adapter_hash,
                         'validation_sha256': fingerprints['val'], 'original_completed_sha256': sha(run / 'completed_run.json'),
                         'original_selection_sha256': sha(run / 'selection.json'),
                         'evaluator_sha256': sha(__file__), 'system_sha256': digest(SYSTEM),
                         'max_new_tokens': 128, 'batch_size': 8, 'greedy': True, 'enable_thinking': False,
                         'no_facts_plan_or_gold_in_input': True, 'production_approved': False}
    path = diagnostic / 'diagnostic_config.json'
    if path.exists() and read_json(path) != diagnostic_config:
        raise ValueError('DIAGNOSTIC_ID_ALREADY_USED_WITH_DIFFERENT_PROTOCOL')
    write_json(path, diagnostic_config)
    if not torch.cuda.is_available():
        raise ValueError('GPU_REQUIRED_FOR_DIAGNOSTIC_INFERENCE')
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(MODEL, revision=REVISION, dtype=torch.float16,
               attn_implementation='sdpa').to('cuda')
    baseline = evaluate(base, tokenizer, examples, diagnostic / 'raw_answer_baseline_val.jsonl',
               'base:' + REVISION, fingerprints['val'], diagnostic_config['evaluator_sha256'])
    adapter = PeftModel.from_pretrained(base, run / 'adapter', is_trainable=False)
    candidate = evaluate(adapter, tokenizer, examples, diagnostic / 'raw_answer_adapter_val.jsonl',
                'adapter:' + adapter_hash, fingerprints['val'], diagnostic_config['evaluator_sha256'])
    del adapter, base
    gc.collect()
    torch.cuda.empty_cache()
    if (sha(run / 'completed_run.json') != diagnostic_config['original_completed_sha256']
            or sha(run / 'selection.json') != diagnostic_config['original_selection_sha256']):
        raise ValueError('DIAGNOSTIC_MUST_NOT_MODIFY_PLANNER_DECISION')
    report = {'status': 'RAW_ANSWER_POSTHOC_DIAGNOSTIC_COMPLETED', **diagnostic_config,
              'baseline_validation': baseline, 'adapter_validation': candidate,
              'solvable_correct_delta': candidate['solvable_correct'] - baseline['solvable_correct'],
              'planner_baseline_protocol_inspection': inspect_planner_baseline(run / 'baseline_val.jsonl'),
              'answer_metric': 'LLM emits numeric answer itself; exact Fraction comparison only scores it.',
              'interpretation': 'Planner-format learning does not prove an improvement in raw arithmetic or arbitrary reasoning.',
              'limits': ['Protocol created after planner validation was observed; posthoc development diagnostic, not untouched gold.',
                         'Finite synthetic validation phrases, not national curriculum or real-school certification.',
                         'Malformed/schema/plan outputs are protocol failures; low score alone does not prove lack of mathematical knowledge.',
                         'Answer-only evaluation does not certify explanation quality or OCR.',
                         'One comma/dot is explicitly a decimal mark; grouped thousands and ambiguous mixed notation are rejected.',
                         'No weights updated and no deployment or acceptance decision is changed.']}
    write_json(diagnostic / 'diagnostic_report.json', report)
    print('MVK_RAW_ANSWER_DIAGNOSTIC=' + json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    main(args.root, args.run_id)

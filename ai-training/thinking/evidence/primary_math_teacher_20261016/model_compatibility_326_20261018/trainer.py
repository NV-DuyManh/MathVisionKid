"""Visible, teacher-authored elementary-math SFT with auditable raw-output metrics.

No torch import is needed for parser/data tests. The neural model must generate
its answer and intermediate results itself; scoring never replaces them with a
calculator answer. Arithmetic checks cannot certify Vietnamese semantics or
pedagogical quality. Existing v2 weights and runs are never changed.
"""
import argparse
import ast
from collections import Counter
from fractions import Fraction
import hashlib
import importlib
import json
import math
from pathlib import Path
import random
import re
import time
import unicodedata

MODEL = 'Qwen/Qwen3-1.7B'
REVISION = '70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'
SEED = 20261013
AMP_INIT_SCALE = 1024
AMP_GROWTH_INTERVAL = 2000
AMP_MAX_RETRIES = 8
FIELDS = {'status', 'steps', 'answer', 'unit', 'hint'}
STEP_FIELDS = {'explanation', 'expression', 'result', 'unit'}
SYSTEM = (
    'Bạn hướng dẫn toán tiểu học Việt Nam lớp 1–5. Chỉ trả một JSON với đúng các '
    'trường status, steps, answer, unit, hint. status là solve, clarify hoặc unsupported. '
    'Với mode worked_solution: mỗi bước có explanation ngắn giải thích mục đích, '
    'expression chỉ dùng số và + - * / % với ngoặc, result dạng chuỗi, unit dạng chuỗi; '
    'answer và unit là chuỗi đáp số cuối, hint=null. Dùng dấu chấm trong expression; '
    'result và answer có thể dùng dấu phẩy thập phân hoặc phân số a/b. '
    'Với mode hint: chỉ đưa một câu hỏi gợi ý để học sinh tự làm, steps=[], '
    'answer=null, unit=null, hint là chuỗi; không tiết lộ đáp số. '
    'Nếu thiếu dữ kiện hoặc ngoài phạm vi, dùng clarify hoặc unsupported, '
    'steps=[], answer=null, unit=null và hint là lời hỏi lại hoặc giải thích ngắn. '
    'Giữ nguyên bài làm sai được trích dẫn trong đề; không coi kết quả của học sinh '
    'là đáp số chuẩn. Không viết nội dung ngoài JSON.'
)


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2),
                         encoding='utf-8', newline='\n')
    temporary.replace(path)


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines()
            if line.strip()]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical_number(value):
    if not isinstance(value, str) or len(value) > 100:
        raise ValueError('number must be a bounded string')
    text = value.strip().replace(',', '.')
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d+)?|\d+/[+-]?\d+)', text):
        raise ValueError('invalid numeric answer')
    answer = Fraction(text)
    if max(abs(answer.numerator), answer.denominator) > 10 ** 18:
        raise ValueError('number outside arithmetic limits')
    return answer


def expression_tree(expression):
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 300:
        raise ValueError('invalid expression length')
    # Fraction constants are constructed from their lexical token, never float.
    tree = ast.parse(expression.strip(), mode='eval')
    if len(list(ast.walk(tree))) > 80:
        raise ValueError('expression too complex')
    return tree


def evaluate_expression(expression):
    source = expression.strip() if isinstance(expression, str) else expression
    tree = expression_tree(source)
    def visit(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            token = ast.get_source_segment(source, node)
            if not re.fullmatch(r'\d+(?:\.\d+)?', token or ''):
                raise ValueError('only ordinary decimal literals permitted')
            result = Fraction(token)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            result = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add): result = left + right
            elif isinstance(node.op, ast.Sub): result = left - right
            elif isinstance(node.op, ast.Mult): result = left * right
            elif isinstance(node.op, ast.Div): result = left / right
            else:
                if left.denominator != 1 or right.denominator != 1 or left < 0 or right <= 0:
                    raise ValueError('remainder requires nonnegative integer / positive integer')
                result = left % right
        else:
            raise ValueError('unsafe expression')
        if max(abs(result.numerator), result.denominator) > 10 ** 18:
            raise ValueError('arithmetic limits exceeded')
        return result
    return visit(tree.body)


def expression_signature(expression):
    """Literal/operation structure; allows swapped or regrouped + and * only.

    This is deliberately stricter than numeric coincidence. Equivalent alternate
    solution methods can fail this reference-path metric and are reported apart.
    """
    source = expression.strip()
    tree = expression_tree(source)
    evaluate_expression(source)
    def visit(node):
        if isinstance(node, ast.Constant):
            return ('number', str(Fraction(ast.get_source_segment(source, node))))
        if isinstance(node, ast.UnaryOp):
            return ('negative' if isinstance(node.op, ast.USub) else 'positive', visit(node.operand))
        if isinstance(node, ast.BinOp):
            operator = type(node.op).__name__
            children = [visit(node.left), visit(node.right)]
            if isinstance(node.op, (ast.Add, ast.Mult)):
                flattened = []
                for child in children:
                    if child[0] == operator: flattened.extend(child[1])
                    else: flattened.append(child)
                return (operator, tuple(sorted(flattened, key=repr)))
            return (operator, tuple(children))
        raise ValueError('unsafe expression')
    return visit(tree.body)


def normalize_unit(unit):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', unit).strip().casefold())


def prompt(row):
    # No facts, topic labels, answers, teacher paths or oracle metadata enter input.
    return json.dumps({key: row[key] for key in ('grade', 'problem', 'mode')},
                      ensure_ascii=False, separators=(',', ':'))


def messages(row):
    return [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': prompt(row)}]


def serialize(row, tokenizer, max_length=1536):
    prefix_text = tokenizer.apply_chat_template(messages(row), tokenize=False,
                     add_generation_prompt=True, enable_thinking=False)
    prefix = tokenizer.encode(prefix_text, add_special_tokens=False)
    completion_text = json.dumps(row['target'], ensure_ascii=False, separators=(',', ':'))
    completion = tokenizer.encode(completion_text + tokenizer.eos_token, add_special_tokens=False)
    if len(prefix) + len(completion) > max_length:
        raise ValueError(f"No silent truncation: {row['sample_id']} has {len(prefix) + len(completion)} > {max_length} tokens")
    if not completion or completion[-1] != tokenizer.eos_token_id:
        raise ValueError('Completion must end in the actual EOS token')
    return {'input_ids': prefix + completion, 'attention_mask': [1] * (len(prefix) + len(completion)),
            'labels': [-100] * len(prefix) + completion, 'sample_id': row['sample_id'],
            'prefix_length': len(prefix), 'completion_length': len(completion)}


def collate(items, pad):
    width = max(len(row['input_ids']) for row in items)
    return {key: [row[key] + [fill] * (width - len(row[key])) for row in items]
            for key, fill in [('input_ids', pad), ('attention_mask', 0), ('labels', -100)]}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def parse_output(text, truncated=False, thought_prefix_open=False):
    if truncated: raise ValueError('truncated output')
    if not isinstance(text, str): raise ValueError('output must be text')
    if thought_prefix_open:
        # Only the evaluator/auditor may set this after inspecting the actual
        # rendered generation prompt. A bare closing tag is otherwise rejected.
        text = '<think>' + text
    if '<think>' in text or '</think>' in text:
        if text.count('<think>') != 1 or text.count('</think>') != 1:
            raise ValueError('unfinished or duplicated thought tags')
        opening, closing = text.index('<think>'), text.index('</think>')
        if opening > closing or text[:opening].strip(): raise ValueError('invalid thought envelope')
        text = text[closing + len('</think>'):]
    text = text.strip()
    if text.startswith('```json\n') and text.endswith('\n```'): text = text[8:-4].strip()
    elif text.startswith('```\n') and text.endswith('\n```'): text = text[4:-4].strip()
    value = json.loads(text, object_pairs_hook=unique_object)
    if not isinstance(value, dict) or set(value) != FIELDS: raise ValueError('wrong schema')
    if value['status'] not in ('solve', 'clarify', 'unsupported'): raise ValueError('wrong status')
    if not isinstance(value['steps'], list) or len(value['steps']) > 12: raise ValueError('bad steps')
    for step in value['steps']:
        if not isinstance(step, dict) or set(step) != STEP_FIELDS: raise ValueError('wrong step schema')
        if not all(isinstance(step[k], str) for k in STEP_FIELDS): raise ValueError('step fields must be strings')
        if not step['explanation'].strip() or len(step['explanation']) > 800: raise ValueError('missing or unbounded explanation')
    if any(value[k] is not None and not isinstance(value[k], str) for k in ('answer', 'unit', 'hint')):
        raise ValueError('answer/unit/hint must be string or null')
    if value['status'] != 'solve' and (value['steps'] or value['answer'] is not None or value['unit'] is not None):
        raise ValueError('guard must not solve')
    return value


def hint_safe(row, parsed):
    hint = parsed['hint']
    if parsed['steps'] or parsed['answer'] is not None or parsed['unit'] is not None:
        return False
    if not isinstance(hint, str) or not 8 <= len(hint.strip()) <= 500 or hint.count('?') != 1:
        return False
    if re.search(r'(?i)(?:đáp\s*(?:số|án)|kết\s*quả)\s*(?:là|:|=)|[=]', hint):
        return False
    # A computed number absent from the original problem is answer disclosure.
    existing = {m.replace(',', '.') for m in re.findall(r'\d+(?:[.,]\d+)?', row['problem'])}
    generated = {m.replace(',', '.') for m in re.findall(r'\d+(?:[.,]\d+)?', hint)}
    return generated <= existing


def score(row, text, truncated=False, thought_prefix_open=False):
    result = {key: False for key in ('schema_valid', 'status_correct', 'answered', 'answer_correct',
              'unit_correct', 'steps_arithmetic_correct', 'steps_reference_match',
              'solution_verified', 'hint_safe', 'hint_reference_match', 'correct', 'wrong_answer')}
    result['truncated'] = bool(truncated)
    try: parsed = parse_output(text, truncated, thought_prefix_open)
    except (ValueError, TypeError, json.JSONDecodeError): return result
    target = row['target']
    result['schema_valid'] = True
    result['status_correct'] = parsed['status'] == target['status']
    if target['status'] != 'solve':
        guard_hint = parsed['hint']
        bounded_hint = isinstance(guard_hint, str) and 8 <= len(guard_hint.strip()) <= 500
        result['correct'] = result['status_correct'] and bounded_hint and not re.search(
            r'(?i)(?:đáp\s*(?:số|án)|kết\s*quả)\s*(?:là|:|=)|[=]', guard_hint)
        result['wrong_answer'] = parsed['status'] == 'solve'
        return result
    if row['mode'] == 'hint':
        result['hint_safe'] = hint_safe(row, parsed)
        result['hint_reference_match'] = (normalize_unit(parsed['hint'] or '') == normalize_unit(target['hint'] or ''))
        result['correct'] = result['status_correct'] and result['hint_safe']
        result['wrong_answer'] = parsed['answer'] is not None or bool(parsed['steps'])
        return result
    result['answered'] = parsed['status'] == 'solve' and parsed['answer'] is not None
    if not result['answered']:
        return result
    result['unit_correct'] = isinstance(parsed['unit'], str) and normalize_unit(parsed['unit']) == normalize_unit(target['unit'])
    try:
        if row.get('answer_kind', 'numeric') == 'categorical':
            result['answer_correct'] = normalize_unit(parsed['answer']) == normalize_unit(target['answer'])
            if parsed['steps'] and parsed['hint'] is None:
                arithmetic_checks, path_checks = [], []
                for index, candidate in enumerate(parsed['steps']):
                    if index >= len(target['steps']): break
                    reference = target['steps'][index]
                    if candidate['expression'].strip():
                        arithmetic_checks.append(evaluate_expression(candidate['expression']) == canonical_number(candidate['result']))
                        same_expression = expression_signature(candidate['expression']) == expression_signature(reference['expression'])
                        same_result = canonical_number(candidate['result']) == canonical_number(reference['result'])
                    else:
                        same_expression = not reference['expression'].strip()
                        same_result = normalize_unit(candidate['result']) == normalize_unit(reference['result'])
                    path_checks.append(same_expression and same_result and normalize_unit(candidate['unit']) == normalize_unit(reference['unit']))
                result['steps_reference_match'] = len(parsed['steps']) == len(target['steps']) and all(path_checks)
                # Categorical steps are matched to the declared teacher path;
                # they are not represented as independently proven arithmetic.
                result['steps_arithmetic_correct'] = all(arithmetic_checks) and result['steps_reference_match']
        else:
            answer = canonical_number(parsed['answer'])
            result['answer_correct'] = answer == canonical_number(target['answer'])
        if row.get('answer_kind', 'numeric') == 'numeric' and parsed['steps'] and parsed['hint'] is None:
            checks = [evaluate_expression(step['expression']) == canonical_number(step['result']) for step in parsed['steps']]
            answer_indices = [index for index, step in enumerate(target['steps'])
                              if canonical_number(step['result']) == canonical_number(target['answer'])
                              and normalize_unit(step['unit']) == normalize_unit(target['unit'])]
            # A final inverse-check step can intentionally differ from the answer.
            # Match the teacher-declared answer-producing step instead of assuming
            # the last displayed step always produces the final answer.
            result['steps_arithmetic_correct'] = all(checks) and bool(answer_indices) and any(
                index < len(parsed['steps']) and canonical_number(parsed['steps'][index]['result']) == answer
                for index in answer_indices)
            result['steps_reference_match'] = len(parsed['steps']) == len(target['steps']) and all(
                expression_signature(candidate['expression']) == expression_signature(reference['expression'])
                and canonical_number(candidate['result']) == canonical_number(reference['result'])
                and normalize_unit(candidate['unit']) == normalize_unit(reference['unit'])
                for candidate, reference in zip(parsed['steps'], target['steps']))
    except (ValueError, TypeError, SyntaxError, ZeroDivisionError, OverflowError):
        pass
    result['solution_verified'] = (result['status_correct'] and result['answer_correct'] and result['unit_correct']
                                  and result['steps_arithmetic_correct'] and result['steps_reference_match'])
    result['correct'] = result['solution_verified']
    result['wrong_answer'] = result['answered'] and not (result['status_correct'] and result['answer_correct'] and result['unit_correct'])
    return result


def aggregate(records):
    count = lambda key, subset: sum(bool(row['scores'][key]) for row in subset)
    solves = [r for r in records if r['reference_status'] == 'solve' and r['mode'] == 'worked_solution']
    hints = [r for r in records if r['reference_status'] == 'solve' and r['mode'] == 'hint']
    guards = [r for r in records if r['reference_status'] != 'solve']
    result = {'samples': len(records), 'correct': count('correct', records),
        'solution_samples': len(solves), 'answer_and_unit_correct': sum(r['scores']['answer_correct'] and r['scores']['unit_correct'] for r in solves),
        'solution_verified': count('solution_verified', solves), 'steps_arithmetic_correct': count('steps_arithmetic_correct', solves),
        'steps_reference_match': count('steps_reference_match', solves), 'hint_samples': len(hints),
        'hint_safe': count('correct', hints), 'hint_reference_match': count('hint_reference_match', hints),
        'guard_samples': len(guards), 'guard_correct': count('correct', guards),
        'schema_valid': count('schema_valid', records), 'wrong_answers': count('wrong_answer', records),
        'truncated': count('truncated', records), 'answered_solutions': count('answered', solves),
        'metric_limits': 'Generated final answers and steps are scored, not calculator-substituted. Arithmetic and reference paths do not certify explanation meaning; hint metric checks format/leakage, not pedagogical merit.'}
    result['categorical_solution_samples'] = sum(r.get('answer_kind') == 'categorical' for r in solves)
    result['solution_verified_rate'] = result['solution_verified'] / len(solves) if solves else None
    return result


def select_candidate(baseline, candidate):
    axes = ('answer_and_unit_correct', 'solution_verified', 'hint_safe', 'hint_reference_match', 'guard_correct')
    non_regression = all(candidate[key] >= baseline[key] for key in axes)
    per_grade = all(all(candidate['per_grade'][grade][key] >= values[key] for key in axes)
                    for grade, values in baseline.get('per_grade', {}).items())
    improved = candidate['solution_verified'] > baseline['solution_verified']
    return {'selected': 'adapter' if non_regression and per_grade and improved else 'base',
            'candidate_improved': non_regression and per_grade and improved,
            'metric_non_regression': non_regression, 'per_grade_non_regression': per_grade,
            'test_or_challenge_used_for_selection': False, 'production_approved': False,
            'criterion': 'strictly more raw final-answer+unit+reference-checked solutions, with no answer/hint-safety/hint-reference/guard/per-grade regression on the identical frozen validation subset'}


def stratified_subset(examples, limit, seed=SEED):
    if limit <= 0 or limit >= len(examples): return list(examples)
    pools = {}
    for row in examples:
        pools.setdefault((str(row['grade']), row.get('topic', 'unspecified'),
                          row['mode'], row['target']['status']), []).append(row)
    rng = random.Random(seed)
    for values in pools.values(): rng.shuffle(values)
    topic_keys = {}
    for key in sorted(pools): topic_keys.setdefault(key[1], []).append(key)
    for values in topic_keys.values(): rng.shuffle(values)
    topics = sorted(topic_keys); rng.shuffle(topics)
    cursors = {topic: 0 for topic in topics}
    chosen = []
    while len(chosen) < limit:
        for topic in topics:
            keys = topic_keys[topic]
            for offset in range(len(keys)):
                index = (cursors[topic] + offset) % len(keys)
                key = keys[index]
                if pools[key]:
                    chosen.append(pools[key].pop()); cursors[topic] = (index + 1) % len(keys)
                    break
            if len(chosen) == limit: break
    return chosen


def run_amp_update(group, compute_backward, optimizer, scaler, scheduler, capture_rng, restore_rng,
                   finite_gradients, clip_gradients, on_overflow, max_retries=AMP_MAX_RETRIES):
    snapshot = capture_rng()
    for attempt in range(max_retries + 1):
        if attempt: restore_rng(snapshot)
        optimizer.zero_grad(set_to_none=True)
        loss = compute_backward(group)
        if not math.isfinite(loss): raise FloatingPointError('Nonfinite forward loss')
        scaler.unscale_(optimizer)
        good = finite_gradients()
        norm = float(clip_gradients()) if good else float('inf')
        if not good or not math.isfinite(norm):
            before = float(scaler.get_scale())
            if before <= 0 or not math.isfinite(before): raise FloatingPointError('Invalid AMP scale')
            scaler.update(new_scale=before / 2)
            on_overflow({'attempt': attempt + 1, 'scale_before': before, 'scale_after': before / 2,
                'reason': 'NONFINITE_GRADIENT' if not good else 'NONFINITE_GRADIENT_NORM',
                'retryable': attempt < max_retries, 'max_retries': max_retries})
            if attempt == max_retries:
                optimizer.zero_grad(set_to_none=True)
                raise FloatingPointError('AMP overflow retry budget exhausted')
            continue
        scaler.step(optimizer); scaler.update(); scheduler.step()
        return {'loss': loss, 'grad_norm': norm, 'overflow_retries': attempt, 'amp_scale': float(scaler.get_scale())}
    raise AssertionError('Unreachable AMP state')


def evaluate(model, tokenizer, examples, path, model_key, max_tokens=512, batch_size=2,
             thinking=False, seed=SEED):
    import torch
    path = Path(path)
    metadata = {'model_key': model_key, 'ids': [r['sample_id'] for r in examples],
        'enable_thinking': thinking, 'max_new_tokens': max_tokens, 'batch_size': batch_size,
        'do_sample': thinking, 'seed': seed, 'temperature': .6 if thinking else None,
        'top_p': .95 if thinking else None, 'top_k': 20 if thinking else None,
        'eos_token_id': tokenizer.eos_token_id,
        'input_sha256': hashlib.sha256(json.dumps(examples, ensure_ascii=False, sort_keys=True).encode()).hexdigest()}
    meta_path = path.with_suffix('.metadata.json')
    if meta_path.exists() and json.loads(meta_path.read_text()) != metadata:
        raise ValueError('Evaluation protocol/data/model changed; a new evaluation file is required')
    if not meta_path.exists(): save(meta_path, metadata)
    cached = {r['sample_id']: r for r in rows(path)} if path.exists() else {}
    if set(cached) - set(metadata['ids']): raise ValueError('Unexpected cached sample IDs')
    model.eval(); model.config.use_cache = True; tokenizer.padding_side = 'left'
    for start in range(0, len(examples), batch_size):
        batch = [r for r in examples[start:start + batch_size] if r['sample_id'] not in cached]
        if not batch: continue
        # Each incomplete batch receives its own deterministic seed, including resumes.
        torch.manual_seed(seed + start); torch.cuda.manual_seed_all(seed + start)
        texts = [tokenizer.apply_chat_template(messages(r), tokenize=False,
                     add_generation_prompt=True, enable_thinking=thinking) for r in batch]
        open_thought = [bool(re.search(r'<think>\s*$', text)) for text in texts]
        inputs = tokenizer(texts, padding=True, return_tensors='pt', add_special_tokens=False).to('cuda')
        kwargs = {'max_new_tokens': max_tokens, 'do_sample': thinking,
                  'pad_token_id': tokenizer.pad_token_id, 'eos_token_id': tokenizer.eos_token_id}
        if thinking: kwargs.update(temperature=.6, top_p=.95, top_k=20)
        with torch.inference_mode(): output = model.generate(**inputs, **kwargs)
        for i, row in enumerate(batch):
            ids = output[i, inputs['input_ids'].shape[-1]:].tolist()
            ended = tokenizer.eos_token_id in ids
            if ended: ids = ids[:ids.index(tokenizer.eos_token_id) + 1]
            truncated = not ended and len(ids) >= max_tokens
            text = tokenizer.decode(ids, skip_special_tokens=True)
            cached[row['sample_id']] = {'sample_id': row['sample_id'], 'grade': row['grade'],
                'topic': row.get('topic', 'unspecified'), 'mode': row['mode'],
                'answer_kind': row.get('answer_kind', 'numeric'),
                'reference_status': row['target']['status'], 'prediction': text,
                'generated_ids': ids, 'generated_tokens': len(ids), 'eos_observed': ended,
                'thought_prefix_open': open_thought[i],
                'scores': score(row, text, truncated, thought_prefix_open=open_thought[i])}
        temporary = path.with_suffix('.jsonl.tmp')
        temporary.write_text(''.join(json.dumps(cached[r['sample_id']], ensure_ascii=False) + '\n'
            for r in examples if r['sample_id'] in cached), encoding='utf-8', newline='\n')
        temporary.replace(path)
        print(f'EVAL {path.stem} {min(start + batch_size, len(examples))}/{len(examples)}', flush=True)
    records = [cached[r['sample_id']] for r in examples]
    summary = aggregate(records)
    summary['per_grade'] = {str(g): aggregate([r for r in records if r['grade'] == g])
                            for g in sorted({r['grade'] for r in records}, key=str)}
    summary['per_topic'] = {topic: aggregate([r for r in records if r['topic'] == topic])
                            for topic in sorted({r['topic'] for r in records})}
    save(path.with_suffix('.summary.json'), summary)
    return summary


def load_config(path):
    config = {'model_id': MODEL, 'revision': REVISION, 'seed': SEED, 'epochs': 1,
        'batch_size': 1, 'accumulation': 4, 'lr': 1e-4, 'max_length': 1536,
        'max_new_tokens': 512, 'eval_batch_size': 2, 'val_limit': 80,
        'thinking_probe_limit': 16, 'thinking_max_new_tokens': 1024,
        'lora_r': 16, 'lora_alpha': 32, 'lora_dropout': .05,
        'checkpoint_interval': 50, 'train_limit': 0, 'data_module': 'teacher_math_data_v3'}
    config.update(json.loads(Path(path).read_text(encoding='utf-8')))
    if not re.fullmatch(r'[0-9a-f]{40}', config['revision']): raise ValueError('Pin an exact model revision')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', config.get('run_id', '')): raise ValueError('Required safe run_id')
    if config['epochs'] != 1: raise ValueError('This audited trainer currently supports exactly one epoch')
    for key in ('batch_size', 'accumulation', 'max_length', 'max_new_tokens', 'eval_batch_size', 'checkpoint_interval'):
        if not isinstance(config[key], int) or config[key] <= 0: raise ValueError('Invalid ' + key)
    if config['max_length'] > 2048: raise ValueError('Longer than 2048 requires a separately reviewed memory protocol')
    return config


def bind_data_system(config):
    global SYSTEM
    module = importlib.import_module(config['data_module'])
    SYSTEM = module.SYSTEM
    # The prompt is kept here, so undocumented oracle fields cannot leak via a custom module.
    return Path(module.__file__)


def prepare(root, config):
    root = Path(root); run = root / 'runs' / config['run_id']; run.mkdir(parents=True, exist_ok=True)
    data_source = bind_data_system(config)
    paths = {name: root / 'data' / (name + '.jsonl') for name in ('train', 'val', 'test', 'challenge')}
    paths = {name: path for name, path in paths.items() if path.exists()}
    if not {'train', 'val'} <= set(paths): raise ValueError('train/val JSONL required')
    # Heldout bytes are hashed now, but their questions/targets are not loaded or
    # passed to any model until the validation-only selection has been saved.
    splits = {name: rows(path) for name, path in paths.items() if name in ('train', 'val')}
    ids = [row['sample_id'] for values in splits.values() for row in values]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate sample IDs across splits')
    source_hashes = {Path(__file__).name: sha(__file__), data_source.name: sha(data_source)}
    expanded = {**config, 'dataset_fingerprints': {key: sha(path) for key, path in paths.items()},
                'source_hashes': source_hashes, 'enable_thinking_training': False,
                'target_kind': 'observable worked steps or one hint; hidden reasoning is not supervised'}
    config_path = run / 'config.json'
    if config_path.exists() and json.loads(config_path.read_text(encoding='utf-8')) != expanded:
        raise ValueError('Changed configuration/source/data; use a new run ID')
    if not config_path.exists(): save(config_path, expanded)
    for name, values in splits.items():
        for row in values:
            if row['mode'] not in ('worked_solution', 'hint'): raise ValueError('Unexpected mode')
            if not 1 <= row['grade'] <= 5: raise ValueError('Unexpected grade')
            gold_score = score(row, json.dumps(row['target'], ensure_ascii=False))
            if not gold_score['correct']: raise ValueError(f"Invalid teacher target {name}:{row['sample_id']} {gold_score}")
    val = stratified_subset(splits['val'], config['val_limit'], config['seed'])
    save(run / 'selection_validation_ids.json', {'ids': [r['sample_id'] for r in val],
        'full_val_samples': len(splits['val']), 'selected_samples': len(val),
        'challenge_used': False, 'test_used': False})
    return root, run, splits, val, expanded


def get_tokenizer(config):
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(config['model_id'], revision=config['revision'])
    if tokenizer.pad_token_id is None: tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def audit_tokens(examples, tokenizer, config, run):
    encoded = [serialize(row, tokenizer, config['max_length']) for row in examples]
    save(run / 'token_audit.json', {'samples': len(encoded), 'truncated': 0, 'assistant_only_loss': True,
        'min_length': min(len(r['input_ids']) for r in encoded),
        'max_length': max(len(r['input_ids']) for r in encoded), 'configured_max_length': config['max_length'],
        'items': [{'sample_id': row['sample_id'], 'prefix_length': row['prefix_length'],
                   'completion_length': row['completion_length'],
                   'input_ids_sha256': hashlib.sha256(json.dumps(row['input_ids']).encode()).hexdigest(),
                   'labels_sha256': hashlib.sha256(json.dumps(row['labels']).encode()).hexdigest()}
                  for row in encoded]})
    return encoded


def inspect_tokens(root, config):
    """Budget inspection before final config/data/source freeze; no model loaded."""
    root = Path(root); run = root / 'runs' / config['run_id']; run.mkdir(parents=True, exist_ok=True)
    bind_data_system(config)
    tokenizer = get_tokenizer(config)
    examples = rows(root / 'data' / 'train.jsonl')
    if config['train_limit']: examples = examples[:config['train_limit']]
    items = [serialize(row, tokenizer, 100000) for row in examples]
    longest = max(items, key=lambda item: len(item['input_ids']))
    max_completion = max(item['completion_length'] for item in items)
    report = {'samples': len(items), 'max_combined_length': len(longest['input_ids']),
        'max_completion_length': max_completion, 'longest_sample_id': longest['sample_id'],
        'suggested_max_length': math.ceil(len(longest['input_ids']) / 128) * 128,
        'suggested_max_new_tokens': math.ceil((max_completion + 32) / 128) * 128,
        'configuration_frozen': False, 'model_loaded': False, 'challenge_questions_loaded': False,
        'per_topic_max': {topic: max(len(item['input_ids']) for item, row in zip(items, examples) if row.get('topic') == topic)
                          for topic in sorted({row.get('topic', 'unspecified') for row in examples})}}
    save(run / 'token_inspection.json', report)
    print('MVK_TOKEN_INSPECTION=' + json.dumps(report), flush=True)
    return report


def load_model(config):
    import torch
    from transformers import AutoModelForCausalLM
    if not torch.cuda.is_available(): raise RuntimeError('GPU required for this stage')
    return AutoModelForCausalLM.from_pretrained(config['model_id'], revision=config['revision'],
              dtype=torch.float16, attn_implementation='sdpa').to('cuda')


def stage_memory(run, examples, config, tokenizer, base):
    """Largest-sequence backward probe: parameters are never stepped or saved."""
    import torch
    from peft import LoraConfig, get_peft_model
    encoded = audit_tokens(examples, tokenizer, config, run)
    largest = max(encoded, key=lambda row: len(row['input_ids']))
    model = get_peft_model(base, LoraConfig(task_type='CAUSAL_LM', revision=config['revision'],
        r=config['lora_r'], lora_alpha=config['lora_alpha'], lora_dropout=config['lora_dropout'],
        bias='none', target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj']))
    model.gradient_checkpointing_enable(); model.enable_input_require_grads()
    model.config.use_cache = False; model.train()
    torch.cuda.reset_peak_memory_stats()
    batch = {key: torch.tensor(value, dtype=torch.long, device='cuda')
             for key, value in collate([largest] * config['batch_size'], tokenizer.pad_token_id).items()}
    with torch.autocast('cuda', dtype=torch.float16): loss = model(**batch).loss
    if not bool(torch.isfinite(loss)): raise FloatingPointError('Memory-probe nonfinite forward loss')
    loss.backward()
    parameters = [p for p in model.parameters() if p.requires_grad]
    finite = all(bool(torch.isfinite(p.grad).all()) for p in parameters if p.grad is not None)
    moment_bytes = sum(p.numel() * p.element_size() * 2 for p in parameters)
    total = torch.cuda.mem_get_info()[1]
    peak = torch.cuda.max_memory_allocated()
    report = {'passed': finite, 'model_id': config['model_id'], 'largest_sample_id': largest['sample_id'],
        'actual_sequence_length': len(largest['input_ids']), 'batch_size': config['batch_size'],
        'loss': float(loss.detach()), 'gradient_finite': finite,
        'measured_peak_vram_gib': round(peak / 2**30, 3),
        'estimated_optimizer_moment_gib': round(moment_bytes / 2**30, 3),
        'estimated_training_peak_gib': round((peak + moment_bytes) / 2**30, 3),
        'total_vram_gib': round(total / 2**30, 3), 'optimizer_steps': 0,
        'adapter_saved': False, 'config_sha256': sha(run / 'config.json'),
        'limitations': 'Single longest-sequence backward plus estimated AdamW moments; actual full-run peak may differ.'}
    save(run / 'memory_preflight.json', report)
    print('MVK_MEMORY_PREFLIGHT=' + json.dumps(report), flush=True)
    if not finite: raise FloatingPointError('Memory-probe nonfinite gradients')
    return report


def adapter_hashes(model):
    from peft import get_peft_model_state_dict
    # Hash one float32 CPU tensor at a time; never materialize a second full model.
    return {key: hashlib.sha256(value.detach().float().cpu().contiguous().numpy().tobytes()).hexdigest()
            for key, value in get_peft_model_state_dict(model).items()}


def stage_baseline(run, val, config, tokenizer, base):
    save(run / 'progress.json', {'phase': 'baseline_validation', 'model_id': config['model_id']})
    result = evaluate(base, tokenizer, val, run / 'baseline_val.jsonl',
                      'base:' + config['model_id'] + ':' + config['revision'],
                      config['max_new_tokens'], config['eval_batch_size'], seed=config['seed'])
    probe = stratified_subset(val, config['thinking_probe_limit'], config['seed'])
    if config['thinking_probe_limit'] > 0:
        thinking = evaluate(base, tokenizer, probe, run / 'baseline_thinking_probe.jsonl',
                  'base:' + config['model_id'] + ':' + config['revision'],
                  config['thinking_max_new_tokens'], 1, thinking=True, seed=config['seed'])
        save(run / 'thinking_probe_protocol.json', {'comparison_role': 'separate exploratory reasoning-mode diagnostic; not checkpoint selection',
             'full_reasoning_capability_certified': False, 'max_new_tokens': config['thinking_max_new_tokens'],
             'sample_ids': [row['sample_id'] for row in probe], 'summary': thinking})
    return result


def stage_train(run, examples, config, tokenizer, base):
    import torch
    from transformers import get_cosine_schedule_with_warmup
    from peft import LoraConfig, get_peft_model, get_peft_model_state_dict, set_peft_model_state_dict
    encoded = audit_tokens(examples, tokenizer, config, run)
    memory = json.loads((run / 'memory_preflight.json').read_text(encoding='utf-8'))
    if not memory['passed'] or memory['config_sha256'] != sha(run / 'config.json'):
        raise ValueError('Successful memory preflight for this frozen configuration is required before training')
    if memory['actual_sequence_length'] < max(len(row['input_ids']) for row in encoded):
        raise ValueError('Memory preflight did not cover the longest training sample')
    order = list(range(len(examples))); random.Random(config['seed']).shuffle(order)
    batches = [order[i:i + config['batch_size']] for i in range(0, len(order), config['batch_size'])]
    groups = [batches[i:i + config['accumulation']] for i in range(0, len(batches), config['accumulation'])]
    updates = len(groups)
    torch.manual_seed(config['seed']); torch.cuda.manual_seed_all(config['seed'])
    model = get_peft_model(base, LoraConfig(task_type='CAUSAL_LM', revision=config['revision'],
        r=config['lora_r'], lora_alpha=config['lora_alpha'], lora_dropout=config['lora_dropout'],
        bias='none', target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj']))
    model.gradient_checkpointing_enable(); model.enable_input_require_grads()
    model.config.use_cache = False; model.train()
    parameters = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(parameters, lr=config['lr'], weight_decay=.01)
    scheduler = get_cosine_schedule_with_warmup(optimizer, max(1, round(updates * .05)), updates)
    scaler = torch.amp.GradScaler('cuda', init_scale=AMP_INIT_SCALE, growth_interval=AMP_GROWTH_INTERVAL)
    checkpoint = run / 'resume_state.pt'; start = 0
    if checkpoint.exists():
        state = torch.load(checkpoint, map_location='cpu', weights_only=True)
        set_peft_model_state_dict(model, state['adapter']); optimizer.load_state_dict(state['optimizer'])
        scheduler.load_state_dict(state['scheduler']); scaler.load_state_dict(state['scaler']); start = state['step']
        torch.set_rng_state(state['cpu_rng']); torch.cuda.set_rng_state(state['cuda_rng'])
        if (run / 'training_log.jsonl').exists():
            committed = [r for r in rows(run / 'training_log.jsonl') if r['step'] <= start]
            (run / 'training_log.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in committed), encoding='utf-8')
        del state
    begun = time.time(); torch.cuda.reset_peak_memory_stats()
    for step in range(start, updates):
        group = groups[step]
        def compute_backward(current_group):
            total = 0.
            for indices in current_group:
                batch = {key: torch.tensor(value, dtype=torch.long, device='cuda')
                         for key, value in collate([encoded[i] for i in indices], tokenizer.pad_token_id).items()}
                with torch.autocast('cuda', dtype=torch.float16): loss = model(**batch).loss
                if not bool(torch.isfinite(loss)): raise FloatingPointError('Nonfinite forward loss')
                total += float(loss.detach()); scaler.scale(loss / len(current_group)).backward()
                del batch, loss
            return total / len(current_group)
        def overflow(event):
            value = {'step': step + 1, 'sample_ids': [examples[i]['sample_id'] for indices in group for i in indices], **event}
            with (run / 'amp_overflow_log.jsonl').open('a', encoding='utf-8') as stream: stream.write(json.dumps(value) + '\n')
            save(run / 'progress.json', {'phase': 'amp_retry', 'total_steps': updates, **value})
            print('AMP_OVERFLOW ' + json.dumps(value), flush=True)
        result = run_amp_update(group, compute_backward, optimizer, scaler, scheduler,
            lambda: (torch.get_rng_state(), torch.cuda.get_rng_state()),
            lambda states: (torch.set_rng_state(states[0]), torch.cuda.set_rng_state(states[1])),
            lambda: any(p.grad is not None for p in parameters) and all(bool(torch.isfinite(p.grad).all()) for p in parameters if p.grad is not None),
            lambda: torch.nn.utils.clip_grad_norm_(parameters, 1.0), overflow)
        record = {'step': step + 1, 'total_steps': updates, **result, 'lr': scheduler.get_last_lr()[0],
            'sample_ids': [examples[i]['sample_id'] for indices in group for i in indices],
            'seconds_this_session': round(time.time() - begun, 2),
            'peak_vram_gib': round(torch.cuda.max_memory_allocated() / 2 ** 30, 3)}
        with (run / 'training_log.jsonl').open('a', encoding='utf-8') as stream: stream.write(json.dumps(record) + '\n')
        save(run / 'progress.json', {'phase': 'training', **record})
        if (step + 1) % 10 == 0: print('TRAIN ' + json.dumps({k: v for k, v in record.items() if k != 'sample_ids'}), flush=True)
        if (step + 1) % config['checkpoint_interval'] == 0 or step + 1 == updates:
            state = {'step': step + 1, 'adapter': {k: v.detach().cpu() for k, v in get_peft_model_state_dict(model).items()},
                'optimizer': optimizer.state_dict(), 'scheduler': scheduler.state_dict(), 'scaler': scaler.state_dict(),
                'cpu_rng': torch.get_rng_state(), 'cuda_rng': torch.cuda.get_rng_state()}
            temporary = run / 'resume_state.tmp'; torch.save(state, temporary); temporary.replace(checkpoint); del state
            model.save_pretrained(run / 'adapter'); tokenizer.save_pretrained(run / 'adapter')
    save(run / 'training_complete.json', {'steps': updates, 'train_samples': len(examples), 'epochs': 1,
        'adapter_sha256': sha(run / 'adapter' / 'adapter_model.safetensors'), 'adapter_tensor_hashes': adapter_hashes(model)})
    model.gradient_checkpointing_disable()
    return model


def stage_evaluate(run, splits, val, config, tokenizer, base):
    from peft import PeftModel
    complete = json.loads((run / 'training_complete.json').read_text(encoding='utf-8'))
    model = PeftModel.from_pretrained(base, run / 'adapter', is_trainable=False)
    hashes = adapter_hashes(model)
    if hashes != complete['adapter_tensor_hashes']: raise ValueError('Fresh reloaded adapter tensors differ')
    save(run / 'reload_verification.json', {'passed': True, 'tensor_count': len(hashes),
        'fresh_base_revision': config['revision'], 'adapter_sha256': complete['adapter_sha256']})
    baseline = json.loads((run / 'baseline_val.summary.json').read_text(encoding='utf-8'))
    candidate = evaluate(model, tokenizer, val, run / 'candidate_val.jsonl', 'adapter:' + complete['adapter_sha256'],
                         config['max_new_tokens'], config['eval_batch_size'], seed=config['seed'])
    selection = select_candidate(baseline, candidate)
    save(run / 'selection.json', selection)
    known_ids = {row['sample_id'] for values in splits.values() for row in values}
    for name in ('test', 'challenge'):
        path = run.parent.parent / 'data' / (name + '.jsonl')
        if path.exists():
            values = rows(path)
            if any(row['sample_id'] in known_ids for row in values):
                raise ValueError('Heldout sample ID appears in another split')
            if len({row['sample_id'] for row in values}) != len(values):
                raise ValueError('Duplicate heldout sample IDs')
            known_ids.update(row['sample_id'] for row in values)
            for row in values:
                if not score(row, json.dumps(row['target'], ensure_ascii=False))['correct']:
                    raise ValueError('Invalid heldout teacher target: ' + row['sample_id'])
            splits[name] = values
    heldout = {}
    for name in ('test', 'challenge'):
        if name not in splits: continue
        if selection['selected'] == 'base':
            with model.disable_adapter():
                heldout[name] = evaluate(model, tokenizer, splits[name], run / ('selected_' + name + '.jsonl'),
                    'base:' + config['model_id'] + ':' + config['revision'], config['max_new_tokens'],
                    config['eval_batch_size'], seed=config['seed'])
        else:
            heldout[name] = evaluate(model, tokenizer, splits[name], run / ('selected_' + name + '.jsonl'),
                'adapter:' + complete['adapter_sha256'], config['max_new_tokens'], config['eval_batch_size'], seed=config['seed'])
    result = {'status': 'SFT_COMPLETED_RESEARCH_ONLY' if selection['candidate_improved'] else 'SFT_REJECTED_VALIDATION_NONIMPROVEMENT',
        'run_id': config['run_id'], 'model_id': config['model_id'], 'revision': config['revision'],
        'steps': complete['steps'], 'train_samples': complete['train_samples'], 'selected': selection['selected'],
        'baseline_validation': baseline, 'candidate_validation': candidate, 'selected_heldout': heldout,
        'adapter_sha256': complete['adapter_sha256'], 'fresh_reload_verified': True,
        'hidden_reasoning_trained': False, 'pedagogy_teacher_reviewed': False, 'production_approved': False,
        'limitations': ['Teacher-authored finite examples do not transfer all teacher knowledge or guarantee near-teacher intelligence.',
            'Challenge/source data are separately reported; national-curriculum coverage is an inventory, not mastery certification.',
            'Reference-step and arithmetic metrics do not prove explanations are semantically or pedagogically correct.',
            'Hint safety metric detects structural/number disclosure; teacher judgment is still required.',
            'OCR is not included in these text-only scores; no student-facing integration is certified.']}
    save(run / 'completed_run.json', result)
    save(run / 'progress.json', {'phase': 'completed', 'status': result['status'], 'selected': result['selected']})
    print('MVK_TEACHER_V3_COMPLETED=' + json.dumps(result, ensure_ascii=False), flush=True)
    return result


def main(root, config_path, stage='all'):
    config = load_config(config_path)
    if stage == 'inspect':
        inspect_tokens(root, config)
        return
    root, run, splits, val, expanded = prepare(root, config)
    if (run / 'completed_run.json').exists() and stage in ('all', 'train', 'evaluate'):
        print((run / 'completed_run.json').read_text(encoding='utf-8'), flush=True); return
    tokenizer = get_tokenizer(config)
    training = splits['train'][:config['train_limit']] if config['train_limit'] else splits['train']
    if stage == 'preflight':
        encoded = audit_tokens(training, tokenizer, config, run)
        save(run / 'preflight.json', {'passed': True, 'train_samples': len(training),
            'validation_samples': len(val), 'max_actual_tokens': max(len(r['input_ids']) for r in encoded),
            'split_counts': {path.stem: sum(bool(line.strip()) for line in path.read_text(encoding='utf-8').splitlines())
                             for path in (root / 'data').glob('*.jsonl') if path.stem in ('train', 'val', 'test', 'challenge')},
            'challenge_questions_loaded': False, 'config_sha256': sha(run / 'config.json')})
        print((run / 'preflight.json').read_text(encoding='utf-8'), flush=True); return
    import torch
    import importlib.metadata
    save(run / 'environment.json', {'gpu': torch.cuda.get_device_name(0),
        'packages': {p: importlib.metadata.version(p) for p in ('torch', 'transformers', 'peft', 'accelerate')},
        'free_total_vram_bytes': list(torch.cuda.mem_get_info())})
    base = load_model(config)
    if stage == 'memory':
        stage_memory(run, training, config, tokenizer, base)
        return
    if stage in ('all', 'baseline'):
        stage_baseline(run, val, config, tokenizer, base)
        if stage == 'baseline': return
    if stage in ('all', 'train'):
        if not (run / 'baseline_val.summary.json').exists(): raise ValueError('Run baseline before training')
        stage_train(run, training, config, tokenizer, base)
        if stage == 'train': return
        # Release optimizer/model state before a real fresh pinned-base reload.
        del base
        import gc
        gc.collect(); torch.cuda.empty_cache()
        base = load_model(config)
    if stage in ('all', 'evaluate'): stage_evaluate(run, splits, val, config, tokenizer, base)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--stage', choices=('inspect', 'preflight', 'memory', 'baseline', 'train', 'evaluate', 'all'), default='all')
    args = parser.parse_args()
    try: main(args.root, args.config, args.stage)
    except Exception as error:
        try:
            config = load_config(args.config)
            save(Path(args.root) / 'runs' / config['run_id'] / 'failure_review.json',
                {'stage': args.stage, 'type': type(error).__name__, 'error': str(error),
                 'training_approved': False, 'production_approved': False})
        finally:
            raise

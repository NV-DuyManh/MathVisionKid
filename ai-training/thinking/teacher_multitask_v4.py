"""Separate mixed teacher-instruction/replay SFT; numeric v3 stays immutable.

Concept responses are visible free prose, not forced into the numeric JSON
schema. Rule-based concept screening is not teacher-certified semantic grading.
This module imports audited v3 helpers explicitly and freezes their source hashes.
"""
import argparse
from contextlib import contextmanager
import gc
import hashlib
import importlib
import json
import math
from pathlib import Path
import random
import re
import time
import unicodedata

import train_teacher_math_v3 as numeric
import teacher_math_numeric_diagnostic_v3 as direct_numeric
from audit_teacher_math_v3 import check_training_log, check_evaluation

CONCEPT_EVAL_SYSTEM = (
    'Bạn là trợ giảng MathVisionKid cho toán tiểu học Việt Nam. Giải thích ngắn, dễ hiểu, '
    'đúng đơn vị và đúng phạm vi câu hỏi. Khi chỉ xin gợi ý, đưa một câu hỏi giúp em tự làm, '
    'không đưa đáp số hoặc các bước đã tính. Chỉ giải ví dụ khi được yêu cầu rõ. '
    'Thiếu hình, số đo hoặc dụng cụ thì hỏi thông tin còn thiếu; không bịa kết quả quan sát. '
    'Phân biệt nội dung chương trình cũ với nội dung hiện hành.'
)
FILES = {'numeric_train': 'numeric_train.jsonl', 'numeric_val': 'numeric_val.jsonl',
         'numeric_fresh_val': 'numeric_fresh_val.jsonl',
         'numeric_challenge': 'numeric_challenge.jsonl', 'concept_train': 'concept_train.jsonl',
         'concept_val': 'concept_val.jsonl', 'concept_challenge': 'concept_challenge.jsonl'}


def load_config(path):
    config = {'model_id': numeric.MODEL, 'revision': numeric.REVISION, 'seed': 20261013,
        'numeric_eval_seed': 20261013,
        'epochs': 1, 'batch_size': 2, 'accumulation': 2, 'lr': 2e-5,
        'max_length': 2048, 'max_new_tokens': 512, 'concept_max_new_tokens': 384,
        'fresh_max_new_tokens': 512, 'fresh_eval_batch_size': 4,
        'eval_batch_size': 4, 'val_limit': 0, 'lora_r': 16, 'lora_alpha': 32,
        'lora_dropout': .05, 'checkpoint_interval': 50,
        'data_module': 'teacher_math_data_v3', 'evaluation_data_module': 'teacher_math_data_v3',
        'concept_repeat': 1, 'load_in_4bit': False, 'memory_reserve_gib': 1.0,
        'require_numeric_semantic_review': True,
        'numeric_retention_summary': None, 'numeric_retention_metadata': None, 'numeric_retention_config': None,
        'require_v3_audit': True, 'v3_audit_path': None, 'v3_selection_path': None}
    config.update(json.loads(Path(path).read_text(encoding='utf-8')))
    if not re.fullmatch(r'[0-9a-f]{40}', config['revision']): raise ValueError('Exact base revision required')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', config.get('run_id', '')): raise ValueError('Safe new run_id required')
    if config['epochs'] != 1: raise ValueError('Only one audited epoch is supported')
    if type(config['load_in_4bit']) is not bool: raise ValueError('Explicit load_in_4bit boolean required')
    if type(config['require_numeric_semantic_review']) is not bool: raise ValueError('Explicit numeric semantic review policy required')
    if config['memory_reserve_gib'] < 0: raise ValueError('Invalid GPU memory reserve')
    if not 0 < config['lr'] <= 2e-5: raise ValueError('Higher teacher SFT learning rate requires a new reviewed protocol')
    if config.get('adapter_path'): raise ValueError('This first v4 trainer uses a fresh pinned base, never a partial v3 adapter')
    for key in ('batch_size', 'accumulation', 'max_length', 'max_new_tokens', 'concept_max_new_tokens',
                'fresh_max_new_tokens', 'fresh_eval_batch_size', 'eval_batch_size', 'checkpoint_interval', 'concept_repeat'):
        if not isinstance(config[key], int) or config[key] <= 0: raise ValueError('Invalid ' + key)
    if config['max_length'] > 2048: raise ValueError('Beyond 2048 requires a separately reviewed memory protocol')
    if config['concept_repeat'] > 4: raise ValueError('More than four concept repetitions requires a new reviewed balance protocol')
    return config


def concept_messages(row):
    if 'messages' in row:
        messages = row['messages']
        if len(messages) not in (2, 3) or [item['role'] for item in messages[:2]] != ['system', 'user']:
            raise ValueError('Concept messages must be exactly system,user[,assistant]')
        if any(not isinstance(item['content'], str) or not item['content'].strip() for item in messages):
            raise ValueError('Empty concept message')
        return [dict(item) for item in messages[:2]]
    question = row.get('question', row.get('problem'))
    if not isinstance(question, str) or not question.strip(): raise ValueError('Concept question absent')
    return [{'role': 'system', 'content': row.get('system', CONCEPT_EVAL_SYSTEM)},
            {'role': 'user', 'content': question}]


def concept_target(row):
    messages = row.get('messages', [])
    if len(messages) != 3 or messages[-1]['role'] != 'assistant':
        raise ValueError('Concept train target must be the original assistant message')
    return messages[-1]['content']


def mixed_messages(item):
    if item['task_kind'] != 'numeric': return concept_messages(item['row'])
    messages = numeric.messages(item['row'])
    if item.get('training_system') is not None:
        messages[0] = {'role': 'system', 'content': item['training_system']}
    return messages


def mixed_serialize(item, tokenizer, max_length=2048):
    messages = mixed_messages(item)
    prefix_text = tokenizer.apply_chat_template(messages, tokenize=False,
                    add_generation_prompt=True, enable_thinking=False)
    target = (json.dumps(item['row']['target'], ensure_ascii=False, separators=(',', ':'))
              if item['task_kind'] == 'numeric' else concept_target(item['row']))
    prefix = tokenizer.encode(prefix_text, add_special_tokens=False)
    completion = tokenizer.encode(target + tokenizer.eos_token, add_special_tokens=False)
    if len(prefix) + len(completion) > max_length:
        raise ValueError(f"No silent truncation: {item['sample_id']} {len(prefix) + len(completion)} > {max_length}")
    if not completion or completion[-1] != tokenizer.eos_token_id: raise ValueError('Actual completion EOS required')
    return {'input_ids': prefix + completion, 'attention_mask': [1] * (len(prefix) + len(completion)),
        'labels': [-100] * len(prefix) + completion, 'sample_id': item['sample_id'],
        'task_kind': item['task_kind'], 'source_sample_id': item['row']['sample_id'],
        'prefix_length': len(prefix), 'completion_length': len(completion)}


def build_training(numeric_rows, concept_rows, repeats=1, training_system=None):
    result = []
    for row in numeric_rows:
        result.append({'sample_id': 'numeric:' + row['sample_id'], 'task_kind': 'numeric', 'row': row,
                       'training_system': training_system})
    for repeat in range(repeats):
        for row in concept_rows:
            result.append({'sample_id': f'concept:{repeat}:' + row['sample_id'], 'task_kind': 'concept',
                           'repeat_index': repeat, 'row': row})
    if len({item['sample_id'] for item in result}) != len(result): raise ValueError('Duplicate training instance IDs')
    return result


def validate_concept_training(row):
    concept_messages(row); reply = concept_target(row)
    if '<think>' in reply or '</think>' in reply: raise ValueError('Teacher targets must contain visible guidance only')
    if row.get('human_verified') or row.get('pedagogy_teacher_reviewed'):
        raise ValueError('AI-authored concept data must not become teacher-certified')
    if not row.get('source') or not row.get('license'): raise ValueError('Concept source/license provenance absent')
    for check in row.get('numeric_checks', []):
        expected = check.get('expected_result', check.get('expected'))
        if numeric.evaluate_expression(check['expression']) != numeric.canonical_number(expected):
            raise ValueError('Incorrect teacher numeric example')
    if row['mode'] == 'hint':
        user = concept_messages(row)[-1]['content']
        pseudo = {'problem': user}
        parsed = {'steps': [], 'answer': None, 'unit': None, 'hint': reply}
        if not numeric.hint_safe(pseudo, parsed): raise ValueError('Concept teacher hint reveals a number/answer or is not one question')


def normalized(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text).casefold()).strip()


def rubric_groups(row):
    rubric = row.get('rubric', row)
    groups = rubric.get('expected_key_claims', rubric.get('required_claims', rubric.get('key_claims', [])))
    if not isinstance(groups, list): raise ValueError('Concept rubric required_claims must be a list')
    result = []
    for group in groups:
        if isinstance(group, str): result.append([group])
        elif isinstance(group, list) and group and all(isinstance(term, str) for term in group): result.append(group)
        elif isinstance(group, dict) and isinstance(group.get('any_of'), list) and group['any_of']:
            if not all(isinstance(term, str) and term for term in group['any_of']): raise ValueError('Claim alternatives must be nonempty strings')
            result.append(group['any_of'])
        else: raise ValueError('A required claim must be one phrase or a list of alternatives')
    return rubric, result


def positive_phrase(body, phrase):
    """Conservative negation screen; finite lexical rules, not semantic proof."""
    phrase = normalized(phrase)
    pattern = re.escape(phrase)
    if phrase and phrase[0].isdigit(): pattern = r'(?<!\d)(?<!\d[.,])' + pattern
    if phrase and phrase[-1].isdigit(): pattern += r'(?!\d|[.,]\d)'
    for match in re.finditer(pattern, body):
        before = body[max(0, match.start()-45):match.start()]
        clause = re.split(r'[.!?;\n]', before)[-1]
        if not re.search(r'(?:không(?:\s+cần|\s+được|\s+nên)?|đừng|chẳng)\s+(?:\w+\s+){0,3}$', clause):
            return True
    return False


def displayed_equations(text):
    number = r'[+-]?\d+(?:[.,]\d+)?(?:/\d+)?'
    # A division colon must have spaces on both sides. "chia 2: 10 × 7"
    # contains a prose separator, while "10 × 7 : 2" is an expression.
    operator = r'(?:\s*[+\-*/×÷]\s*|\s+:\s+)'
    expression = rf'{number}(?:{operator}{number})*'
    # Include balanced numeric parentheses. Never score just the suffix of
    # "(8 + 3) * 2 = 22" as "2 = 22". AST evaluation remains bounded.
    for _ in range(3):
        atom = rf'(?:{number}|\([ \t]*{expression}[ \t]*\))'
        expression = rf'{atom}(?:{operator}{atom})*'
    pattern = rf'(?<![\w/.,()×÷*+])({expression}(?:[ \t]*=[ \t]*{expression})+)(?![\d/()])'
    checks = []
    for match in re.finditer(pattern, text):
        expressions = [part.strip().replace(',', '.').replace('×', '*').replace('÷', '/').replace(':', '/')
                       for part in match[1].split('=')]
        try:
            values = [numeric.evaluate_expression(expression) for expression in expressions]
            passed = all(value == values[0] for value in values)
        except (ValueError, SyntaxError, ZeroDivisionError, OverflowError):
            passed = False
        checks.append({'observed_equation_chain': match[1], 'expressions': expressions, 'passed': passed})
    return checks


def numeric_bindings(row, body):
    """Finite explicit label/value checks, not unrestricted prose semantics."""
    results = []
    for binding in row.get('expected_numeric_bindings', []):
        label = normalized(binding['label'])
        expected = numeric.canonical_number(binding['expected_value'])
        observed = []
        for match in re.finditer(re.escape(label) + r'\b', body):
            if not positive_phrase(body[max(0, match.start()-45):match.end()], label): continue
            tail = body[match.end():].lstrip(' :=')
            tail = re.sub(r'^(?:là|bằng|được)\s+', '', tail)
            chains = displayed_equations(tail)
            if chains and tail.startswith(chains[0]['observed_equation_chain']):
                if chains[0]['passed']:
                    observed.append(numeric.evaluate_expression(chains[0]['expressions'][-1]))
                else:
                    observed.append(None)
            else:
                found = re.match(r'([+-]?\d+(?:[.,]\d+)?(?:/\d+)?)(?!\d|[.,]\d)', tail)
                if found: observed.append(numeric.canonical_number(found[1]))
        results.append({'label': label, 'expected_value': str(expected),
            'observed_values': [str(value) for value in observed],
            'passed': bool(observed) and all(value == expected for value in observed)})
    return results


def score_concept(row, text, truncated=False):
    rubric, groups = rubric_groups(row)
    value = {'screened_correct': False, 'required_claim_groups': len(groups), 'matched_claim_groups': 0,
        'forbidden_claim_hit': False, 'hint_structurally_safe': False, 'observation_request': False,
        'displayed_equation_checks': [], 'displayed_arithmetic_valid': False,
        'numeric_binding_checks': [], 'numeric_bindings_valid': False,
        'truncated': bool(truncated), 'semantic_correctness_verified': False,
        'pedagogy_teacher_reviewed': False, 'evaluation_kind': 'lexical_and_structural_screening_only'}
    if not isinstance(text, str) or not text.strip() or truncated: return value
    if '<think>' in text or '</think>' in text: return value
    body = normalized(text)
    value['matched_claim_groups'] = sum(any(positive_phrase(body, term) for term in group) for group in groups)
    rejected = rubric.get('rejected_claims', rubric.get('forbidden_claims', []))
    value['forbidden_claim_hit'] = any(positive_phrase(body, term) for term in rejected)
    value['displayed_equation_checks'] = displayed_equations(text)
    value['displayed_arithmetic_valid'] = all(check['passed'] for check in value['displayed_equation_checks'])
    value['numeric_binding_checks'] = numeric_bindings(row, body)
    value['numeric_bindings_valid'] = all(check['passed'] for check in value['numeric_binding_checks'])
    question = concept_messages(row)[-1]['content']
    if row['mode'] == 'hint':
        value['hint_structurally_safe'] = numeric.hint_safe({'problem': question},
            {'steps': [], 'answer': None, 'unit': None, 'hint': text})
    if rubric.get('require_image_confirmation', rubric.get('require_image', rubric.get('requires_observation', False))):
        value['observation_request'] = '?' in text and any(word in body for word in
            ('hình', 'ảnh', 'số đo', 'kích thước', 'thông tin', 'biểu đồ', 'bảng', 'dụng cụ'))
        numbers = set(re.findall(r'\d+(?:[.,]\d+)?', text))
        source_numbers = set(re.findall(r'\d+(?:[.,]\d+)?', question))
        if not numbers <= source_numbers: value['observation_request'] = False
    else: value['observation_request'] = True
    if not groups: raise ValueError('Independent concept evaluation requires an explicit nonempty rubric')
    value['screened_correct'] = (value['matched_claim_groups'] == len(groups) and not value['forbidden_claim_hit']
        and value['observation_request'] and (row['mode'] != 'hint' or value['hint_structurally_safe']))
    value['screened_correct'] = (value['screened_correct'] and value['displayed_arithmetic_valid']
                                and value['numeric_bindings_valid'])
    return value


def aggregate_concepts(records):
    return {'samples': len(records), 'screened_correct': sum(r['scores']['screened_correct'] for r in records),
        'truncated': sum(r['scores']['truncated'] for r in records),
        'hint_samples': sum(r['mode'] == 'hint' for r in records),
        'hint_structurally_safe': sum(r['scores']['hint_structurally_safe'] for r in records if r['mode'] == 'hint'),
        'forbidden_claim_hits': sum(r['scores']['forbidden_claim_hit'] for r in records),
        'displayed_arithmetic_failures': sum(not r['scores']['displayed_arithmetic_valid'] for r in records),
        'semantic_correctness_verified': False, 'pedagogy_teacher_reviewed': False,
        'metric_limits': 'Required lexical alternatives, forbidden phrases and hint/observation structure only; these scores are not semantic or pedagogical certification.'}


def raw_non_regression(reference, candidate):
    if reference is None or candidate is None: return False
    axes = ('numeric_correct', 'answer_unit_correct')
    return all(candidate[key] >= reference[key] for key in axes) and all(
        all(candidate['per_grade'][grade][key] >= values[key] for key in axes)
        for grade, values in reference['per_grade'].items())


def response_contract(examples, records):
    """Independent mode/schema and arithmetic checks without reference-path order."""
    by_id = {row['sample_id']: row for row in examples}
    checked = []
    for record in records:
        row = by_id[record['sample_id']]
        value = {'schema_valid': False, 'mode_contract': False, 'steps_arithmetic_safe': False,
                 'grade': row['grade'], 'sample_id': row['sample_id']}
        try:
            parsed = numeric.parse_output(record['prediction'], record['scores']['truncated'], record.get('thought_prefix_open', False))
            value['schema_valid'] = True
            status_ok = parsed['status'] == row['target']['status']
            if row['target']['status'] != 'solve':
                value['mode_contract'] = status_ok and bool(parsed['hint']) and parsed['answer'] is None and not parsed['steps']
            elif row['mode'] == 'hint':
                value['mode_contract'] = status_ok and numeric.hint_safe(row, parsed)
            else:
                value['mode_contract'] = (status_ok and parsed['answer'] is not None and isinstance(parsed['unit'], str)
                                          and bool(parsed['steps']) and parsed['hint'] is None)
                checks = []
                for step in parsed['steps']:
                    if not step['expression'].strip() and row.get('answer_kind') == 'categorical': continue
                    checks.append(numeric.evaluate_expression(step['expression']) == numeric.canonical_number(step['result']))
                value['steps_arithmetic_safe'] = (value['mode_contract']
                    and (bool(checks) or row.get('answer_kind') == 'categorical') and all(checks))
        except (ValueError, TypeError, SyntaxError, json.JSONDecodeError, ZeroDivisionError, OverflowError):
            pass
        checked.append(value)
    def count(subset):
        return {'samples': len(subset), **{key: sum(record[key] for record in subset)
            for key in ('schema_valid', 'mode_contract', 'steps_arithmetic_safe')}}
    result = count(checked)
    result['per_grade'] = {str(grade): count([record for record in checked if record['grade'] == grade])
                           for grade in sorted({row['grade'] for row in examples})}
    result['reference_paths_used'] = False
    result['semantic_correctness_certified'] = False
    return result


def contract_non_regression(reference, candidate):
    axes = ('schema_valid', 'mode_contract', 'steps_arithmetic_safe')
    return all(candidate[key] >= reference[key] for key in axes) and all(
        all(candidate['per_grade'][grade][key] >= values[key] for key in axes)
        for grade, values in reference['per_grade'].items())


def semantic_review(run, examples):
    """Require explicit AI review of every actual concept output, hash bound.

    This is an AI research review. It is never called human verification or
    teacher certification, and lexical counts cannot substitute for it.
    """
    run = Path(run); path = run/'concept_semantic_review.json'
    if not path.exists(): raise ValueError('Concept semantic review pending: review all baseline/candidate outputs first')
    review = json.loads(path.read_text(encoding='utf-8'))
    if review.get('human_verified') is not False or review.get('review_kind') != 'AI_SEMANTIC_RESEARCH_REVIEW':
        raise ValueError('Concept review provenance must explicitly remain AI-reviewed')
    by_id = {row['sample_id']: row for row in examples}
    if review.get('reference_sha256') != hashlib.sha256(json.dumps(examples,ensure_ascii=False,sort_keys=True).encode()).hexdigest():
        raise ValueError('Semantic review reference changed')
    for name in ('baseline','candidate'):
        if review.get('prediction_sha256',{}).get(name) != numeric.sha(run/(name+'_concept_val.jsonl')):
            raise ValueError('Semantic review does not match actual generated output bytes')
    records = review['records']
    if len(records) != len(examples)*2 or {(r['model'],r['sample_id']) for r in records} != {
        (name,sample_id) for name in ('baseline','candidate') for sample_id in by_id}:
        raise ValueError('Every baseline/candidate concept response must be reviewed exactly once')
    for record in records:
        if record['grade'] != by_id[record['sample_id']]['grade'] or not str(record.get('reason','')).strip():
            raise ValueError('Semantic review needs correct grade and an explicit reason')
        if any(type(record.get(key)) is not bool for key in ('semantic_correct','instruction_followed','severe_error')):
            raise ValueError('Explicit semantic/policy/error decisions required')
    def counts(name, grade=None):
        subset=[r for r in records if r['model']==name and (grade is None or r['grade']==grade)]
        return {'samples':len(subset),'acceptable':sum(r['semantic_correct'] and r['instruction_followed'] and not r['severe_error'] for r in subset),
                'severe_errors':sum(r['severe_error'] for r in subset)}
    base=counts('baseline');candidate=counts('candidate')
    grades={str(grade):{'baseline':counts('baseline',grade),'candidate':counts('candidate',grade)}
            for grade in sorted({r['grade'] for r in records})}
    passed=(candidate['acceptable']>=base['acceptable'] and candidate['severe_errors']<=base['severe_errors']
            and all(v['candidate']['acceptable']>=v['baseline']['acceptable'] and
                    v['candidate']['severe_errors']<=v['baseline']['severe_errors'] for v in grades.values()))
    result={'passed':passed,'baseline':base,'candidate':candidate,'per_grade':grades,
        'review_sha256':numeric.sha(path),'human_verified':False,'teacher_certified':False,
        'review_kind':'AI_SEMANTIC_RESEARCH_REVIEW','test_mastery_claim':False}
    numeric.save(run/'concept_semantic_review_summary.json',result)
    return result


def numeric_semantic_review(run, examples, review_stem='numeric_semantic_review', prediction_stem='numeric_val', required_ids=None):
    """Review every visible retention reply; format scores cannot prove teaching."""
    run = Path(run); path = run / (review_stem + '.json')
    if not path.exists(): raise ValueError('Numeric semantic review pending: review all visible baseline/candidate outputs')
    review = json.loads(path.read_text(encoding='utf-8'))
    if review.get('human_verified') is not False or review.get('review_kind') != 'AI_SEMANTIC_RESEARCH_REVIEW':
        raise ValueError('Numeric semantic review must explicitly remain AI research')
    fingerprint = hashlib.sha256(json.dumps(examples, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if review.get('reference_sha256') != fingerprint: raise ValueError('Numeric review reference mismatch')
    by_id = {row['sample_id']: row for row in examples if required_ids is None or row['sample_id'] in required_ids}
    if required_ids is not None and set(by_id) != set(required_ids): raise ValueError('Fresh review scope has unknown IDs')
    for name in ('baseline', 'candidate'):
        if review.get('prediction_sha256', {}).get(name) != numeric.sha(run / (name + '_' + prediction_stem + '.jsonl')):
            raise ValueError('Numeric review does not match actual prediction bytes')
    records = review.get('records', [])
    required_ids = {(model, sample_id) for model in ('baseline', 'candidate') for sample_id in by_id}
    if len(records) != len(required_ids) or {(r['model'], r['sample_id']) for r in records} != required_ids:
        raise ValueError('All actual numeric baseline/candidate replies must be reviewed exactly once')
    fields = ('semantic_correct', 'instruction_followed', 'severe_error', 'useful',
              'grade_appropriate', 'answer_not_disclosed')
    for record in records:
        row = by_id[record['sample_id']]
        if record['grade'] != row['grade'] or record['mode'] != row['mode'] or not str(record.get('reason', '')).strip():
            raise ValueError('Numeric review reference grade/mode/reason invalid')
        if any(type(record.get(key)) is not bool for key in fields):
            raise ValueError('Numeric review requires explicit math/instruction/grade/usefulness/leakage decisions')
    def counts(name, grade=None):
        subset = [record for record in records if record['model'] == name and (grade is None or record['grade'] == grade)]
        def accepted(record):
            return (record['semantic_correct'] and record['instruction_followed'] and not record['severe_error']
                    and record['useful'] and record['grade_appropriate']
                    and (record['mode'] != 'hint' or record['answer_not_disclosed']))
        def basic(values):
            return {'samples': len(values), 'acceptable': sum(accepted(record) for record in values),
                'semantic_correct': sum(record['semantic_correct'] for record in values),
                'severe_errors': sum(record['severe_error'] for record in values),
                'hint_answer_leaks': sum(record['mode'] == 'hint' and not record['answer_not_disclosed'] for record in values)}
        def kind(record):
            if by_id[record['sample_id']]['target']['status'] != 'solve': return 'guard'
            return 'hint' if record['mode'] == 'hint' else 'worked'
        result = basic(subset)
        result['by_task'] = {task: basic([record for record in subset if kind(record) == task])
                             for task in ('worked', 'hint', 'guard')}
        return result
    baseline_count = counts('baseline'); candidate_count = counts('candidate')
    per_grade = {str(grade): {'baseline': counts('baseline', grade), 'candidate': counts('candidate', grade)}
                 for grade in sorted({row['grade'] for row in by_id.values()})}
    def non_regression(base, candidate):
        def basic_non_regression(base, candidate):
            return (candidate['acceptable'] >= base['acceptable'] and candidate['semantic_correct'] >= base['semantic_correct']
                    and candidate['severe_errors'] <= base['severe_errors'] and candidate['hint_answer_leaks'] <= base['hint_answer_leaks'])
        return basic_non_regression(base, candidate) and all(
            basic_non_regression(base['by_task'][task], candidate['by_task'][task]) for task in ('worked', 'hint', 'guard'))
    result = {'passed': non_regression(baseline_count, candidate_count) and all(
                  non_regression(value['baseline'], value['candidate']) for value in per_grade.values()),
              'baseline': baseline_count, 'candidate': candidate_count, 'per_grade': per_grade,
              'review_sha256': numeric.sha(path), 'human_verified': False, 'teacher_certified': False,
              'review_kind': 'AI_SEMANTIC_RESEARCH_REVIEW', 'hidden_thinking_reviewed': False,
              'production_approved': False}
    result['reviewed_unique_examples'] = len(by_id)
    result['full_validation_examples'] = len(examples)
    result['review_scope'] = 'all_visible_replies' if required_ids is None else 'all_observed_failures_and_declared_stratified_slices'
    numeric.save(run / (review_stem + '_summary.json'), result)
    return result


def fresh_review_plan(run, examples, predictions):
    """Same paired IDs: all observed failures plus deterministic success slices."""
    required = set(); reasons = {}
    by_id = {row['sample_id']: row for row in examples}
    for name, records in predictions.items():
        raw = {record['sample_id']: record for record in direct_numeric.diagnostic(examples, records)['records']}
        for record in records:
            row = by_id[record['sample_id']]
            contract = response_contract([row], [record])
            failures = []
            if not contract['schema_valid'] or not contract['mode_contract']: failures.append('schema_or_mode')
            if row['target']['status'] == 'solve' and row['mode'] == 'worked_solution':
                if not raw[record['sample_id']]['answer_unit_correct']: failures.append('raw_number_or_unit')
                if not contract['steps_arithmetic_safe']: failures.append('displayed_arithmetic')
            if row['target']['status'] != 'solve' and not record['scores']['correct']: failures.append('guard_contract')
            if failures:
                required.add(row['sample_id']); reasons.setdefault(row['sample_id'], []).append({'model': name, 'failures': failures})
    for grade in sorted({row['grade'] for row in examples}):
        for kind, take in (('worked', 5), ('hint', 3), ('guard', 2)):
            subset = [row for row in examples if row['grade'] == grade and (
                (kind == 'worked' and row['mode'] == 'worked_solution' and row['target']['status'] == 'solve')
                or (kind == 'hint' and row['mode'] == 'hint' and row['target']['status'] == 'solve')
                or (kind == 'guard' and row['target']['status'] != 'solve'))]
            subset.sort(key=lambda row: hashlib.sha256(('v4_review_slice:' + row['sample_id']).encode()).hexdigest())
            for row in subset[:take]:
                required.add(row['sample_id']); reasons.setdefault(row['sample_id'], []).append({'slice': kind, 'grade': grade})
    ids = [row['sample_id'] for row in examples if row['sample_id'] in required]
    plan = {'required_sample_ids': ids, 'paired_outputs_to_review': len(ids) * 2,
        'reference_sha256': hashlib.sha256(json.dumps(examples, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        'prediction_sha256': {name: numeric.sha(Path(run)/(name+'_numeric_fresh_val.jsonl')) for name in predictions},
        'reasons': reasons, 'human_verified': False, 'semantic_mastery_claim': False,
        'selection_rule': 'Failure union across both models plus 5 worked/3 hint/2 guard per grade, SHA-ordered; both models reviewed on identical IDs'}
    numeric.save(Path(run)/'fresh_numeric_review_plan.json', plan)
    return plan


def select(baseline_numeric, candidate_numeric, baseline_concepts, candidate_concepts, retention=None,
           baseline_raw=None, candidate_raw=None, parent_raw=None, semantic=None,
           numeric_semantic=None, require_numeric_semantic=False, fresh_numeric=None, contracts=None):
    # V4 deliberately declares new quality gates before freeze: exact reference
    # paths and hint wording stay reported, while actual arithmetic and reviewed
    # teaching determine safety. V3's original selection is never modified.
    axes = ('hint_safe', 'guard_correct')
    def nonreg(reference):
        return all(candidate_numeric[key] >= reference[key] for key in axes) and all(
            all(candidate_numeric['per_grade'][grade][key] >= values[key] for key in axes)
            for grade, values in reference.get('per_grade', {}).items())
    raw_ok = nonreg(baseline_numeric)
    retention_ok = retention is None or nonreg(retention)
    concept_ok = (candidate_concepts['screened_correct'] > baseline_concepts['screened_correct']
        and candidate_concepts['hint_structurally_safe'] >= baseline_concepts['hint_structurally_safe']
        and candidate_concepts['forbidden_claim_hits'] <= baseline_concepts['forbidden_claim_hits'])
    direct_ok = raw_non_regression(baseline_raw,candidate_raw) and raw_non_regression(parent_raw,candidate_raw)
    semantic_ok = semantic is not None and semantic['passed']
    numeric_semantic_ok = not require_numeric_semantic or (numeric_semantic is not None and numeric_semantic['passed'])
    fresh_numeric_ok = fresh_numeric is None or fresh_numeric['passed']
    contract_ok = contracts is None or (contract_non_regression(contracts['baseline'], contracts['candidate'])
                                        and contract_non_regression(contracts['parent'], contracts['candidate']))
    improvement = (candidate_raw is not None and baseline_raw is not None and
                   (candidate_raw['numeric_correct'] > baseline_raw['numeric_correct'] or
                    candidate_raw['answer_unit_correct'] > baseline_raw['answer_unit_correct']))
    improvement = improvement or (semantic_ok and semantic['candidate']['acceptable'] > semantic['baseline']['acceptable'])
    improvement = improvement or (numeric_semantic is not None and numeric_semantic_ok and
                                 numeric_semantic['candidate']['acceptable'] > numeric_semantic['baseline']['acceptable'])
    approved = raw_ok and retention_ok and direct_ok and semantic_ok and numeric_semantic_ok and fresh_numeric_ok and contract_ok and improvement
    return {'selected': 'adapter' if approved else 'base', 'candidate_improved': approved,
        'numeric_base_non_regression': raw_ok, 'v3_numeric_retention_non_regression': retention_ok,
        'v3_retention_reference_present': retention is not None, 'concept_screening_improved': concept_ok,
        'direct_numeric_retention_non_regression':direct_ok,'concept_ai_semantic_review_passed':semantic_ok,
        'numeric_ai_semantic_review_required': require_numeric_semantic,
        'numeric_ai_semantic_review_passed': numeric_semantic_ok,
        'new_numeric_validation_non_regression': fresh_numeric_ok,
        'actual_schema_mode_arithmetic_non_regression': contract_ok,
        'reference_hint_match_advisory': True, 'reference_solution_path_advisory': True,
        'semantic_review_required_before_selection':True,
        'concept_semantics_certified': False, 'teacher_review_required': True,
        'challenge_used_for_selection': False, 'production_approved': False,
        'criterion': 'Direct generated-number/unit and actual schema/mode/step-arithmetic retention overall/per grade versus own fresh base and audited V3 recommended model; actual numeric and concept teaching reviewed by AI overall/per grade. Exact paths/wording are advisory. Raw math or reviewed teaching must improve; no teacher-certified mastery claim.'}


def prepare(root, config, freeze=True):
    root = Path(root); run = root / 'runs' / config['run_id']; run.mkdir(parents=True, exist_ok=True)
    data_module = importlib.import_module(config['data_module'])
    evaluation_module = importlib.import_module(config['evaluation_data_module'])
    # V4 can improve teaching instructions while V3 retention keeps its exact
    # original input contract. Never rebind retention to the new train system.
    numeric.SYSTEM = evaluation_module.SYSTEM
    paths = {key: root / 'data' / filename for key, filename in FILES.items()}
    paths = {key: path for key, path in paths.items() if path.exists()}
    required = {'numeric_train', 'numeric_val', 'concept_train', 'concept_val'}
    if not required <= set(paths): raise ValueError('Missing required data: ' + str(sorted(required - set(paths))))
    sources = {Path(__file__).name: numeric.sha(__file__), Path(numeric.__file__).name: numeric.sha(numeric.__file__),
               Path(data_module.__file__).name: numeric.sha(data_module.__file__),
               Path(evaluation_module.__file__).name: numeric.sha(evaluation_module.__file__),
               Path(direct_numeric.__file__).name:numeric.sha(direct_numeric.__file__),
               'audit_teacher_math_v3.py':numeric.sha(Path(__file__).with_name('audit_teacher_math_v3.py'))}
    # Do not load challenge text before saving the validation-only decision.
    datasets = {key: numeric.rows(path) for key, path in paths.items() if 'challenge' not in key}
    for row in datasets['numeric_train'] + datasets.get('numeric_fresh_val', []):
        validate_training_numeric(row, data_module)
    for row in datasets['numeric_val']:
        if not numeric.score(row, json.dumps(row['target'], ensure_ascii=False))['correct']:
            raise ValueError('Invalid frozen retention numeric gold')
    for row in datasets['concept_train']: validate_concept_training(row)
    for row in datasets['concept_val']:
        concept_messages(row); _, groups = rubric_groups(row)
        if not groups: raise ValueError('Empty independent concept rubric')
    train_questions = {normalized(concept_messages(row)[-1]['content']) for row in datasets['concept_train']}
    if any(normalized(concept_messages(row)[-1]['content']) in train_questions for row in datasets['concept_val']):
        raise ValueError('Independent concept validation question appears in training')
    numeric_questions = {normalized(row['problem']) for row in datasets['numeric_train']}
    for key in ('numeric_val', 'numeric_fresh_val'):
        if any(normalized(row['problem']) in numeric_questions for row in datasets.get(key, [])):
            raise ValueError('Numeric validation question appears in training: ' + key)
    train_groups = {row['split_group_id'] for row in datasets['numeric_train'] if row.get('split_group_id')}
    if any(row.get('split_group_id') in train_groups for row in datasets.get('numeric_fresh_val', [])):
        raise ValueError('Fresh numeric split_group_id appears in training')
    all_ids = [row['sample_id'] for values in datasets.values() for row in values]
    if len(all_ids) != len(set(all_ids)): raise ValueError('Duplicate source IDs between train/val tasks')
    fingerprints = {key: numeric.sha(path) for key, path in paths.items()}
    references = {}
    if config['require_v3_audit']:
        if not config['v3_audit_path'] or not config['v3_selection_path']:
            raise ValueError('A completed audited v3 run is required before authorizing v4 training')
        for key in ('v3_audit_path', 'v3_selection_path'):
            references[key] = numeric.sha(config[key])
        review = json.loads(Path(config['v3_audit_path']).read_text(encoding='utf-8'))
        if review.get('status') != 'PASSED' or not review.get('all_passed'):
            raise ValueError('Core v3 integrity audit did not pass')
        selection = json.loads(Path(config['v3_selection_path']).read_text(encoding='utf-8'))
        if selection.get('challenge_used_for_selection', selection.get('test_or_challenge_used_for_selection')) is not False:
            raise ValueError('V3 selection provenance invalid')
        if not all(config.get(key) for key in ('numeric_retention_summary','numeric_retention_metadata','numeric_retention_config')):
            raise ValueError('Audited v3 recommended-model numeric retention references are mandatory')
    if bool(config['numeric_retention_summary']) != bool(config['numeric_retention_metadata']):
        raise ValueError('Retention summary and exact protocol metadata must be provided together')
    if config['numeric_retention_summary'] and not config['numeric_retention_config']:
        raise ValueError('V3 retention must include the pinned source/data configuration')
    for key in ('numeric_retention_summary', 'numeric_retention_metadata', 'numeric_retention_config'):
        if config[key]: references[key] = numeric.sha(config[key])
    if config['numeric_retention_summary']:
        reference_predictions=Path(str(config['numeric_retention_summary']).replace('.summary.json','.jsonl'))
        if not reference_predictions.exists():raise ValueError('Actual parent prediction file required')
        references['numeric_retention_predictions']=numeric.sha(reference_predictions)
    expanded = {**config, 'dataset_fingerprints': fingerprints, 'source_hashes': sources,
        'reference_hashes': references, 'numeric_input': 'v3 grade/problem/mode; teacher targets absent',
        'numeric_training_system_sha256': hashlib.sha256(data_module.SYSTEM.encode()).hexdigest(),
        'numeric_retention_system_sha256': hashlib.sha256(evaluation_module.SYSTEM.encode()).hexdigest(),
        'fresh_numeric_input': 'v4 grade/problem/mode with the new training system; separate development validation',
        'quantization': {'load_in_4bit': config['load_in_4bit'], 'type': 'nf4' if config['load_in_4bit'] else None,
                         'double_quant': config['load_in_4bit'], 'compute_dtype': 'float16'},
        'concept_input': 'original system/user only; assistant text is completion target',
        'enable_thinking_training': False, 'fresh_base_only': True, 'hidden_reasoning_trained': False}
    if freeze:
        path = run / 'config.json'
        if path.exists() and json.loads(path.read_text(encoding='utf-8')) != expanded:
            raise ValueError('Data/source/protocol changed: a new run ID is required')
        if not path.exists(): numeric.save(path, expanded)
    instances = build_training(datasets['numeric_train'], datasets['concept_train'], config['concept_repeat'], data_module.SYSTEM)
    return root, run, datasets, instances, expanded


def validate_training_numeric(row, data_module):
    """Validate teacher arithmetic/layout before any training masks exist."""
    validator = getattr(data_module, 'validate_training_row', None)
    if validator is not None:
        validator(row)
    elif data_module.__name__ == 'teacher_math_data_v3':
        if not numeric.score(row, json.dumps(row['target'], ensure_ascii=False))['correct']:
            raise ValueError('Invalid numeric teacher gold')
    else:
        raise ValueError('New teacher data module needs an independent validate_training_row')
    if row.get('human_verified') or row.get('pedagogy_teacher_reviewed'):
        raise ValueError('AI teacher numeric data cannot claim human/teacher verification')
    # Keep the public schema compatible with the immutable evaluation parser.
    if not numeric.score(row, json.dumps(row['target'], ensure_ascii=False))['correct']:
        raise ValueError('Numeric teacher target violates the frozen response schema')


@contextmanager
def numeric_system(system):
    original = numeric.SYSTEM
    numeric.SYSTEM = system
    try:
        yield
    finally:
        numeric.SYSTEM = original


def fresh_numeric_evaluation(model, tokenizer, datasets, path, key, config):
    if not datasets.get('numeric_fresh_val'): return None
    data_module = importlib.import_module(config['data_module'])
    with numeric_system(data_module.SYSTEM):
        return numeric.evaluate(model, tokenizer, datasets['numeric_fresh_val'], path, key,
                                config['fresh_max_new_tokens'], config['fresh_eval_batch_size'], seed=config['seed'])


def token_audit(instances, tokenizer, config, run, inspection=False):
    encoded = [mixed_serialize(item, tokenizer, 100000 if inspection else config['max_length']) for item in instances]
    combined = max(len(item['input_ids']) for item in encoded)
    completion = max(item['completion_length'] for item in encoded)
    report = {'samples': len(encoded), 'numeric_instances': sum(i['task_kind'] == 'numeric' for i in encoded),
        'concept_instances': sum(i['task_kind'] == 'concept' for i in encoded),
        'max_combined_length': combined, 'max_completion_length': completion,
        'suggested_max_length': math.ceil(combined / 128) * 128,
        'suggested_max_new_tokens': math.ceil((completion + 32) / 128) * 128,
        'assistant_only_loss': True, 'silent_truncation': False, 'configuration_frozen': not inspection,
        'items': [{'sample_id': row['sample_id'], 'task_kind': row['task_kind'], 'source_sample_id': row['source_sample_id'],
            'prefix_length': row['prefix_length'], 'completion_length': row['completion_length'],
            'input_ids_sha256': hashlib.sha256(json.dumps(row['input_ids']).encode()).hexdigest(),
            'labels_sha256': hashlib.sha256(json.dumps(row['labels']).encode()).hexdigest()} for row in encoded]}
    numeric.save(run / ('token_inspection.json' if inspection else 'token_audit.json'), report)
    print('V4_TOKEN_AUDIT=' + json.dumps({k: v for k, v in report.items() if k != 'items'}), flush=True)
    return encoded


def evaluate_concepts(model, tokenizer, examples, path, model_key, config):
    import torch
    path = Path(path)
    metadata = {'model_key': model_key, 'ids': [row['sample_id'] for row in examples],
        'max_new_tokens': config['concept_max_new_tokens'], 'enable_thinking': False, 'do_sample': False,
        'batch_size': config['eval_batch_size'], 'eos_token_id': tokenizer.eos_token_id,
        'input_sha256': hashlib.sha256(json.dumps(examples, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        'metric': 'lexical_and_structural_screening_only'}
    meta = path.with_suffix('.metadata.json')
    if meta.exists() and json.loads(meta.read_text(encoding='utf-8')) != metadata:
        raise ValueError('Changed concept evaluation protocol')
    if not meta.exists(): numeric.save(meta, metadata)
    previous = numeric.rows(path) if path.exists() else []
    cached = {record['sample_id']: record for record in previous}
    if len(cached) != len(previous) or set(cached) - set(metadata['ids']):
        raise ValueError('Unexpected/duplicated cached concept IDs')
    model.eval(); model.config.use_cache = True; tokenizer.padding_side = 'left'
    batch_size = config['eval_batch_size']
    for start in range(0, len(examples), batch_size):
        batch = [row for row in examples[start:start + batch_size] if row['sample_id'] not in cached]
        if not batch: continue
        strings = [tokenizer.apply_chat_template(concept_messages(row), tokenize=False,
                    add_generation_prompt=True, enable_thinking=False) for row in batch]
        inputs = tokenizer(strings, padding=True, return_tensors='pt', add_special_tokens=False).to('cuda')
        with torch.inference_mode(): output = model.generate(**inputs,
            max_new_tokens=config['concept_max_new_tokens'], do_sample=False,
            pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id)
        for index, row in enumerate(batch):
            ids = output[index, inputs['input_ids'].shape[-1]:].tolist(); ended = tokenizer.eos_token_id in ids
            if ended: ids = ids[:ids.index(tokenizer.eos_token_id) + 1]
            text = tokenizer.decode(ids, skip_special_tokens=True)
            truncated = not ended and len(ids) >= config['concept_max_new_tokens']
            cached[row['sample_id']] = {'sample_id': row['sample_id'], 'grade': row['grade'], 'mode': row['mode'],
                'prediction': text, 'generated_ids': ids, 'generated_tokens': len(ids), 'eos_observed': ended,
                'scores': score_concept(row, text, truncated)}
        temporary = path.with_suffix('.jsonl.tmp')
        temporary.write_text(''.join(json.dumps(cached[row['sample_id']], ensure_ascii=False) + '\n'
            for row in examples if row['sample_id'] in cached), encoding='utf-8', newline='\n'); temporary.replace(path)
        print(f'V4_CONCEPT_EVAL {path.stem} {min(start+batch_size,len(examples))}/{len(examples)}', flush=True)
    summary = aggregate_concepts([cached[row['sample_id']] for row in examples])
    numeric.save(path.with_suffix('.summary.json'), summary)
    return summary


def audit_concept_predictions(path, examples, tokenizer):
    path = Path(path)
    metadata = json.loads(path.with_suffix('.metadata.json').read_text(encoding='utf-8'))
    records = numeric.rows(path)
    ids = [row['sample_id'] for row in examples]
    fingerprint = hashlib.sha256(json.dumps(examples, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if metadata['ids'] != ids or metadata['input_sha256'] != fingerprint:
        raise ValueError('Concept evaluation input/order fingerprint changed')
    if metadata['enable_thinking'] or metadata['do_sample'] or metadata['eos_token_id'] != tokenizer.eos_token_id:
        raise ValueError('Concept deterministic no-thinking protocol changed')
    if [record['sample_id'] for record in records] != ids or len(set(ids)) != len(ids):
        raise ValueError('Concept generated records missing/duplicated/reordered')
    for row, record in zip(examples, records):
        tokens = record['generated_ids']
        if not tokens or not all(type(token) is int and token >= 0 for token in tokens):
            raise ValueError('Concept generated token IDs absent/invalid')
        ended = tokenizer.eos_token_id in tokens
        if ended and tokens.index(tokenizer.eos_token_id) != len(tokens) - 1:
            raise ValueError('Concept token IDs continue after first EOS')
        if len(tokens) > metadata['max_new_tokens']: raise ValueError('Concept generated token budget exceeded')
        text = tokenizer.decode(tokens, skip_special_tokens=True)
        truncated = not ended and len(tokens) >= metadata['max_new_tokens']
        if (text != record['prediction'] or len(tokens) != record['generated_tokens']
                or ended != record['eos_observed']):
            raise ValueError('Concept actual token IDs do not reconstruct recorded prediction')
        if record['scores'] != score_concept(row, text, truncated): raise ValueError('Concept screening scores not recomputed from actual output')
        if (record['grade'], record['mode']) != (row['grade'], row['mode']): raise ValueError('Concept generated output assigned to wrong reference')
    summary = aggregate_concepts(records)
    if summary != json.loads(path.with_suffix('.summary.json').read_text(encoding='utf-8')):
        raise ValueError('Concept generated output aggregate differs')
    return {'samples': len(records), 'actual_tokens_decoded': True, 'summary_recomputed': True,
            'semantic_correctness_verified': False}


def audit_validations(run, datasets, config, tokenizer):
    evidence = {}
    complete = json.loads((Path(run)/'training_complete.json').read_text(encoding='utf-8'))
    for name in ('baseline', 'candidate'):
        expected_key = ('base:' + config['model_id'] + ':' + config['revision']) if name == 'baseline' else 'adapter:' + complete['adapter_sha256']
        path = Path(run) / (name + '_numeric_val.jsonl')
        validate_numeric_metadata(path, expected_key, config['max_new_tokens'], config['eval_batch_size'], config.get('numeric_eval_seed', config['seed']))
        evidence[path.stem] = check_evaluation(path, {row['sample_id']: row for row in numeric_val(datasets, config)}, tokenizer)
        concept_path = Path(run) / (name + '_concept_val.jsonl')
        concept_metadata = json.loads(concept_path.with_suffix('.metadata.json').read_text(encoding='utf-8'))
        if (concept_metadata['model_key'] != expected_key or concept_metadata['max_new_tokens'] != config['concept_max_new_tokens']
                or concept_metadata['batch_size'] != config['eval_batch_size']):
            raise ValueError('Concept actual model/cap/batch differs from frozen configuration')
        evidence[concept_path.stem] = audit_concept_predictions(concept_path, datasets['concept_val'], tokenizer)
        if datasets.get('numeric_fresh_val'):
            fresh_path = Path(run) / (name + '_numeric_fresh_val.jsonl')
            validate_numeric_metadata(fresh_path, expected_key, config['fresh_max_new_tokens'], config['fresh_eval_batch_size'], config['seed'])
            with numeric_system(importlib.import_module(config['data_module']).SYSTEM):
                evidence[fresh_path.stem] = check_evaluation(fresh_path,
                    {row['sample_id']: row for row in datasets['numeric_fresh_val']}, tokenizer)
    numeric.save(Path(run) / 'validation_integrity_audit.json', {'status': 'PASSED', 'all_passed': True,
        'files': evidence, 'semantic_correctness_certified': False, 'production_approved': False})
    return evidence


def validate_numeric_metadata(path, model_key, max_new_tokens, batch_size, seed):
    metadata = json.loads(Path(path).with_suffix('.metadata.json').read_text(encoding='utf-8'))
    expected = {'model_key': model_key, 'max_new_tokens': max_new_tokens, 'batch_size': batch_size,
                'seed': seed, 'enable_thinking': False, 'do_sample': False,
                'temperature': None, 'top_p': None, 'top_k': None}
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise ValueError('Actual numeric generation protocol/model differs from frozen configuration')


def audit_training(run, instances, config, tokenizer):
    """Reconstruct visible completion masks and saved weights, CPU only."""
    run = Path(run)
    witness = json.loads((run/'token_audit.json').read_text(encoding='utf-8'))
    items = witness['items']
    if len(items) != len(instances): raise ValueError('Mixed token audit does not cover the complete epoch')
    lengths = []
    for instance, item in zip(instances, items):
        messages = mixed_messages(instance)
        prefix = tokenizer.encode(tokenizer.apply_chat_template(messages, tokenize=False,
            add_generation_prompt=True, enable_thinking=False), add_special_tokens=False)
        target = (json.dumps(instance['row']['target'], ensure_ascii=False, separators=(',', ':'))
                  if instance['task_kind'] == 'numeric' else concept_target(instance['row']))
        completion = tokenizer.encode(target + tokenizer.eos_token, add_special_tokens=False)
        ids = prefix + completion; labels = [-100] * len(prefix) + completion
        if not completion or completion[-1] != tokenizer.eos_token_id or len(ids) > config['max_length']:
            raise ValueError('Recomputed mixed token budget/EOS invalid')
        expected = {'sample_id': instance['sample_id'], 'task_kind': instance['task_kind'],
            'source_sample_id': instance['row']['sample_id'], 'prefix_length': len(prefix),
            'completion_length': len(completion),
            'input_ids_sha256': hashlib.sha256(json.dumps(ids).encode()).hexdigest(),
            'labels_sha256': hashlib.sha256(json.dumps(labels).encode()).hexdigest()}
        if item != expected: raise ValueError('Mixed assistant-only mask differs on independent reconstruction')
        padded = numeric.collate([{'input_ids': ids, 'attention_mask': [1]*len(ids), 'labels': labels},
            {'input_ids': ids + [1], 'attention_mask': [1]*(len(ids)+1), 'labels': labels+[1]}], tokenizer.pad_token_id)
        if padded['labels'][0][-1] != -100 or padded['attention_mask'][0][-1] != 0:
            raise ValueError('Mixed padding participates in training loss')
        lengths.append(len(ids))
    if witness['max_combined_length'] != max(lengths): raise ValueError('Mixed token max length witness invalid')
    complete = json.loads((run/'training_complete.json').read_text(encoding='utf-8'))
    committed = validate_committed_epoch(instances, numeric.rows(run/'training_log.jsonl'), config, complete['steps'])
    verify_adapter_file(run, complete)
    from safetensors.torch import load_file
    tensors = load_file(str(run/'adapter'/'adapter_model.safetensors'), device='cpu')
    hashes = {key: hashlib.sha256(value.float().contiguous().numpy().tobytes()).hexdigest() for key, value in tensors.items()}
    if hashes != complete['adapter_tensor_hashes']: raise ValueError('Actual saved adapter tensors differ from training witness')
    report = {'status': 'PASSED', 'all_passed': True, 'actual_token_masks_recomputed': len(items),
              'committed_epoch': committed, 'actual_saved_tensors': len(hashes),
              'config_sha256': numeric.sha(run/'config.json'), 'production_approved': False,
              'semantic_correctness_certified': False}
    numeric.save(run/'training_integrity_audit.json', report)
    return report


def attach(base, config):
    from peft import LoraConfig, get_peft_model
    return get_peft_model(base, LoraConfig(task_type='CAUSAL_LM', revision=config['revision'],
        r=config['lora_r'], lora_alpha=config['lora_alpha'], lora_dropout=config['lora_dropout'], bias='none',
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj']))


def load_model(config):
    """Single pinned GPU base; optional NF4 applies to both sides of the pair."""
    if not config.get('load_in_4bit', False): return numeric.load_model(config)
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    from peft import prepare_model_for_kbit_training
    if not torch.cuda.is_available(): raise RuntimeError('GPU required for NF4')
    quantization = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
        bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float16)
    # Explicit one-GPU placement, never inference-only device_map="auto".
    model = AutoModelForCausalLM.from_pretrained(config['model_id'], revision=config['revision'],
        dtype=torch.float16, attn_implementation='sdpa', quantization_config=quantization,
        device_map={'': 0})
    if not getattr(model, 'is_loaded_in_4bit', False): raise ValueError('Requested NF4 was not actually loaded')
    # Apply the same frozen norm casts to baseline and reloaded adapter bases.
    # Checkpoint hooks are enabled only in memory/train, never for inference.
    return prepare_model_for_kbit_training(model, use_gradient_checkpointing=False)


def freeze_environment(run, config):
    import importlib.metadata
    import torch
    if not torch.cuda.is_available(): raise RuntimeError('GPU required')
    packages = ('torch', 'transformers', 'peft', 'accelerate', 'safetensors')
    if config.get('load_in_4bit'): packages += ('bitsandbytes',)
    environment = {'packages': {name: importlib.metadata.version(name) for name in packages},
        'cuda_version': torch.version.cuda, 'gpu_name': torch.cuda.get_device_name(0),
        'gpu_capability': list(torch.cuda.get_device_capability(0)),
        'quantization': 'nf4_double_float16' if config.get('load_in_4bit') else 'float16',
        'config_sha256': numeric.sha(Path(run) / 'config.json')}
    path = Path(run) / 'environment_protocol.json'
    if path.exists() and json.loads(path.read_text(encoding='utf-8')) != environment:
        raise ValueError('GPU/package/quantization environment changed: use a new run ID')
    if not path.exists(): numeric.save(path, environment)
    return environment


def memory(run, instances, config, tokenizer, base):
    import torch
    encoded = token_audit(instances, tokenizer, config, run)
    longest = max(encoded, key=lambda row: len(row['input_ids']))
    model = attach(base, config); model.gradient_checkpointing_enable(); model.enable_input_require_grads()
    model.config.use_cache = False; model.train(); torch.cuda.reset_peak_memory_stats()
    batch = {key: torch.tensor(value, dtype=torch.long, device='cuda') for key, value in
             numeric.collate([longest] * config['batch_size'], tokenizer.pad_token_id).items()}
    with torch.autocast('cuda', dtype=torch.float16): loss = model(**batch).loss
    if not bool(torch.isfinite(loss)): raise FloatingPointError('Nonfinite memory forward')
    loss.backward()
    parameters = [p for p in model.parameters() if p.requires_grad]
    finite = all(bool(torch.isfinite(p.grad).all()) for p in parameters if p.grad is not None)
    peak = torch.cuda.max_memory_allocated(); moments = sum(p.numel()*p.element_size()*2 for p in parameters)
    total = torch.cuda.mem_get_info()[1]
    headroom = total - peak - moments
    feasible = finite and headroom >= config.get('memory_reserve_gib', 1.0) * 2**30
    report = {'passed': feasible, 'gradient_finite': finite, 'actual_sequence_length': len(longest['input_ids']),
        'largest_sample_id': longest['sample_id'], 'peak_vram_gib': round(peak/2**30,3),
        'estimated_training_peak_gib': round((peak+moments)/2**30,3),
        'estimated_optimizer_moments_gib': round(moments/2**30,3),
        'total_vram_gib': round(total/2**30,3), 'estimated_remaining_gib': round(headroom/2**30,3),
        'required_reserve_gib': config.get('memory_reserve_gib', 1.0),
        'load_in_4bit': config.get('load_in_4bit', False),
        'config_sha256': numeric.sha(run/'config.json'), 'optimizer_steps': 0, 'adapter_saved': False}
    numeric.save(run/'memory_preflight.json',report); print('V4_MEMORY='+json.dumps(report),flush=True)
    if not finite: raise FloatingPointError('Nonfinite memory gradients')
    if not feasible: raise MemoryError('Worst-case backward plus optimizer states leaves insufficient GPU reserve')


def validate_resume_step(step, total_steps):
    if type(step) is not int or not 0 <= step <= total_steps:
        raise ValueError('Resume checkpoint step outside committed epoch bounds')
    return step


def validate_committed_epoch(instances, records, config, expected_steps):
    return check_training_log(instances,records,config,expected_steps)


def validate_resume_prefix(instances, records, config, committed_step):
    """A checkpoint cannot erase missing/mismatched already-committed updates."""
    order = list(range(len(instances))); random.Random(config['seed']).shuffle(order)
    batches = [order[index:index + config['batch_size']] for index in range(0, len(order), config['batch_size'])]
    groups = [batches[index:index + config['accumulation']] for index in range(0, len(batches), config['accumulation'])]
    validate_resume_step(committed_step, len(groups))
    prefix = [record for record in records if record['step'] <= committed_step]
    if [record['step'] for record in prefix] != list(range(1, committed_step + 1)):
        raise ValueError('Resume log is missing/duplicating committed checkpoint updates')
    for record, group in zip(prefix, groups):
        expected = [instances[index]['sample_id'] for batch in group for index in batch]
        if record['sample_ids'] != expected: raise ValueError('Resume sample order differs from committed checkpoint')
        if not all(math.isfinite(record[key]) for key in ('loss', 'grad_norm', 'amp_scale')):
            raise ValueError('Nonfinite resume log update')
    return prefix


def verify_adapter_file(run, complete):
    path=Path(run)/'adapter'/'adapter_model.safetensors'
    if not path.exists():raise ValueError('Saved adapter file missing')
    actual=numeric.sha(path)
    if actual != complete['adapter_sha256']:raise ValueError('Saved adapter file SHA differs from training evidence')
    return actual


def train(run, instances, config, tokenizer, base):
    import torch
    from transformers import get_cosine_schedule_with_warmup
    from peft import get_peft_model_state_dict, set_peft_model_state_dict
    if (run / 'training_complete.json').exists():
        complete = json.loads((run / 'training_complete.json').read_text(encoding='utf-8'))
        verify_adapter_file(run, complete)
        validate_committed_epoch(instances, numeric.rows(run / 'training_log.jsonl'), config, complete['steps'])
        return
    encoded = token_audit(instances, tokenizer, config, run)
    witness = json.loads((run/'memory_preflight.json').read_text(encoding='utf-8'))
    if not witness['passed'] or witness['config_sha256'] != numeric.sha(run/'config.json'):
        raise ValueError('Successful memory probe for this frozen configuration required')
    if witness['actual_sequence_length'] < max(len(item['input_ids']) for item in encoded):
        raise ValueError('Memory probe failed to cover longest training item')
    order = list(range(len(instances))); random.Random(config['seed']).shuffle(order)
    batches = [order[i:i+config['batch_size']] for i in range(0,len(order),config['batch_size'])]
    groups = [batches[i:i+config['accumulation']] for i in range(0,len(batches),config['accumulation'])]
    torch.manual_seed(config['seed']);torch.cuda.manual_seed_all(config['seed'])
    model=attach(base,config);model.gradient_checkpointing_enable();model.enable_input_require_grads()
    model.config.use_cache=False;model.train();parameters=[p for p in model.parameters() if p.requires_grad]
    optimizer=torch.optim.AdamW(parameters,lr=config['lr'],weight_decay=.01)
    scheduler=get_cosine_schedule_with_warmup(optimizer,max(1,round(len(groups)*.05)),len(groups))
    scaler=torch.amp.GradScaler('cuda',init_scale=numeric.AMP_INIT_SCALE,growth_interval=numeric.AMP_GROWTH_INTERVAL)
    checkpoint=run/'resume_state.pt';start=0
    if not checkpoint.exists() and (run / 'training_log.jsonl').exists():
        # A crash before the first atomic checkpoint leaves uncommitted updates.
        # Preserve their evidence, then restart from the fresh deterministic base.
        old_log = run / 'training_log.jsonl'
        snapshot = run / ('training_log_uncommitted_' + str(time.time_ns()) + '.jsonl')
        old_log.replace(snapshot)
        numeric.save(run / 'resume_rollback.json', {'committed_step': 0, 'snapshot': snapshot.name,
            'snapshot_sha256': numeric.sha(snapshot), 'reason': 'No optimizer/adapter checkpoint committed'})
    if checkpoint.exists():
        state=torch.load(checkpoint,map_location='cpu',weights_only=True)
        set_peft_model_state_dict(model,state['adapter']);optimizer.load_state_dict(state['optimizer'])
        scheduler.load_state_dict(state['scheduler']);scaler.load_state_dict(state['scaler']);start=validate_resume_step(state['step'],len(groups))
        torch.set_rng_state(state['cpu_rng']);torch.cuda.set_rng_state(state['cuda_rng']);del state
        log_path = run / 'training_log.jsonl'
        records = validate_resume_prefix(instances, numeric.rows(log_path) if log_path.exists() else [], config, start)
        temporary = run / 'training_log.resume.tmp'
        temporary.write_text(''.join(json.dumps(record) + '\n' for record in records), encoding='utf-8')
        temporary.replace(log_path)
    begun=time.time();torch.cuda.reset_peak_memory_stats()
    for step in range(start,len(groups)):
        group=groups[step]
        def backward(current):
            total=0.
            for indices in current:
                batch={key:torch.tensor(value,dtype=torch.long,device='cuda') for key,value in
                    numeric.collate([encoded[i] for i in indices],tokenizer.pad_token_id).items()}
                with torch.autocast('cuda',dtype=torch.float16):loss=model(**batch).loss
                if not bool(torch.isfinite(loss)):raise FloatingPointError('Nonfinite mixed teacher loss')
                total+=float(loss.detach());scaler.scale(loss/len(current)).backward();del batch,loss
            return total/len(current)
        def overflow(event):
            value={'step':step+1,'sample_ids':[instances[i]['sample_id'] for indices in group for i in indices],**event}
            with (run/'amp_overflow_log.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(value)+'\n')
            numeric.save(run/'progress.json',{'phase':'amp_retry',**value})
        result=numeric.run_amp_update(group,backward,optimizer,scaler,scheduler,
            lambda:(torch.get_rng_state(),torch.cuda.get_rng_state()),
            lambda state:(torch.set_rng_state(state[0]),torch.cuda.set_rng_state(state[1])),
            lambda:any(p.grad is not None for p in parameters) and all(bool(torch.isfinite(p.grad).all()) for p in parameters if p.grad is not None),
            lambda:torch.nn.utils.clip_grad_norm_(parameters,1.),overflow)
        record={'step':step+1,'total_steps':len(groups),**result,
            'sample_ids':[instances[i]['sample_id'] for indices in group for i in indices],
            'task_kinds':[instances[i]['task_kind'] for indices in group for i in indices],
            'seconds_this_session':round(time.time()-begun,2),'lr':scheduler.get_last_lr()[0],
            'peak_vram_gib':round(torch.cuda.max_memory_allocated()/2**30,3)}
        with (run/'training_log.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(record)+'\n')
        numeric.save(run/'progress.json',{'phase':'training',**record})
        if (step+1)%10==0:print('V4_TRAIN '+json.dumps({k:v for k,v in record.items() if k not in ('sample_ids','task_kinds')}),flush=True)
        if (step+1)%config['checkpoint_interval']==0 or step+1==len(groups):
            state={'step':step+1,'adapter':{k:v.detach().cpu() for k,v in get_peft_model_state_dict(model).items()},
                'optimizer':optimizer.state_dict(),'scheduler':scheduler.state_dict(),'scaler':scaler.state_dict(),
                'cpu_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state()}
            temporary=run/'resume_state.tmp';torch.save(state,temporary);temporary.replace(checkpoint);del state
            model.save_pretrained(run/'adapter');tokenizer.save_pretrained(run/'adapter')
    committed=validate_committed_epoch(instances,numeric.rows(run/'training_log.jsonl'),config,len(groups))
    numeric.save(run/'training_complete.json',{'steps':len(groups),'training_instances':len(instances),
        'committed_epoch_audit':committed,
        'unique_source_numeric':sum(i['task_kind']=='numeric' for i in instances),
        'concept_source_rows':len({i['row']['sample_id'] for i in instances if i['task_kind']=='concept'}),
        'concept_training_instances':sum(i['task_kind']=='concept' for i in instances),
        'adapter_sha256':numeric.sha(run/'adapter'/'adapter_model.safetensors'),
        'adapter_tensor_hashes':numeric.adapter_hashes(model),'hidden_reasoning_trained':False})
    model.gradient_checkpointing_disable()


def numeric_val(datasets,config):
    return numeric.stratified_subset(datasets['numeric_val'],config['val_limit'],config['seed'])


def baseline(run,datasets,config,tokenizer,base):
    key='base:'+config['model_id']+':'+config['revision']
    numeric.evaluate(base,tokenizer,numeric_val(datasets,config),run/'baseline_numeric_val.jsonl',
                     key,config['max_new_tokens'],config['eval_batch_size'],seed=config.get('numeric_eval_seed', config['seed']))
    evaluate_concepts(base,tokenizer,datasets['concept_val'],run/'baseline_concept_val.jsonl',key,config)
    fresh_numeric_evaluation(base,tokenizer,datasets,run/'baseline_numeric_fresh_val.jsonl',key,config)


def retention_reference(config, val, run):
    if not config['numeric_retention_summary']:return None
    metadata=json.loads(Path(config['numeric_retention_metadata']).read_text(encoding='utf-8'))
    fingerprint=hashlib.sha256(json.dumps(val,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    if metadata['ids'] != [row['sample_id'] for row in val] or metadata['input_sha256']!=fingerprint:
        raise ValueError('V3 numeric retention comparison uses different validation examples/order')
    if metadata['enable_thinking'] or metadata['do_sample'] or metadata['max_new_tokens']!=config['max_new_tokens']:
        raise ValueError('V3 retention generation protocol differs from v4')
    if metadata['batch_size']!=config['eval_batch_size']:
        raise ValueError('V3 retention evaluation batch size differs from v4')
    if metadata['seed'] != config.get('numeric_eval_seed', config['seed']) or any(
            metadata.get(key) is not None for key in ('temperature', 'top_p', 'top_k')):
        raise ValueError('V3 retention sampling/seed metadata differs from declared numeric evaluation')
    parent=json.loads(Path(config['numeric_retention_config']).read_text(encoding='utf-8'))
    if not re.fullmatch(r'[0-9a-f]{40}', parent['revision']): raise ValueError('Parent base revision is not frozen')
    if metadata['model_key'] != 'base:' + parent['model_id'] + ':' + parent['revision']:
        raise ValueError('Retention predictions must be the audited recommended V3 base')
    module=importlib.import_module(config['evaluation_data_module'])
    if parent['source_hashes'].get(Path(module.__file__).name)!=numeric.sha(module.__file__):
        raise ValueError('Retention numeric teacher SYSTEM/data source differs')
    if parent['dataset_fingerprints'].get('val')!=numeric.sha(run.parent.parent/'data'/'numeric_val.jsonl'):
        raise ValueError('Retention numeric validation bytes differ')
    if parent['source_hashes'].get(Path(numeric.__file__).name)!=numeric.sha(numeric.__file__):
        raise ValueError('Retention numeric parser/scoring helper differs')
    # Generated token IDs belong to the parent tokenizer, even when the new
    # candidate is a larger or quantized base. Decode with the correct pin.
    tokenizer=numeric.get_tokenizer(parent)
    if metadata['eos_token_id'] != tokenizer.eos_token_id: raise ValueError('Parent metadata EOS differs from pinned parent tokenizer')
    prompt_fingerprint=hashlib.sha256('\n'.join(tokenizer.apply_chat_template(numeric.messages(row),tokenize=False,
        add_generation_prompt=True,enable_thinking=False) for row in val).encode()).hexdigest()
    report=json.loads(Path(config['numeric_retention_summary']).read_text(encoding='utf-8'))
    prediction_path=Path(str(config['numeric_retention_summary']).replace('.summary.json','.jsonl'))
    attached_metadata=json.loads(prediction_path.with_suffix('.metadata.json').read_text(encoding='utf-8'))
    if attached_metadata!=metadata:raise ValueError('Configured retention metadata differs from actual prediction-side metadata')
    check_evaluation(prediction_path,{row['sample_id']:row for row in val},tokenizer)
    numeric.save(run/'numeric_retention_reference.json',{'summary':report,'metadata':metadata,
        'comparison_kind':'same frozen numeric task/protocol; development retention reference',
        'same_pinned_base': parent['model_id'] == config['model_id'] and parent['revision'] == config['revision'],
        'parent_model_id': parent['model_id'], 'parent_revision': parent['revision'],
        'candidate_base_model_id': config['model_id'], 'candidate_base_revision': config['revision'],
        'candidate_base_quantization': 'nf4_double_float16' if config.get('load_in_4bit') else 'float16',
        'model_comparison_limit': 'Cross-base/quantization retention is distinct from the new base-versus-adapter paired measurement.',
        'reference_sha256':numeric.sha(config['numeric_retention_summary']),
        'parent_config_sha256':numeric.sha(config['numeric_retention_config']),
        'rendered_numeric_prompt_sha256':prompt_fingerprint,'teacher_system_sha256':hashlib.sha256(numeric.SYSTEM.encode()).hexdigest()})
    return report


def evaluate(run, root, datasets, config, tokenizer, base, candidate_only=False):
    from peft import PeftModel
    complete=json.loads((run/'training_complete.json').read_text(encoding='utf-8'))
    verify_adapter_file(run,complete)
    model=PeftModel.from_pretrained(base,run/'adapter',is_trainable=False)
    if numeric.adapter_hashes(model)!=complete['adapter_tensor_hashes']:raise ValueError('Fresh mixed adapter reload differs')
    numeric.save(run/'reload_verification.json',{'passed':True,'revision':config['revision'],
        'adapter_sha256':complete['adapter_sha256']})
    key='adapter:'+complete['adapter_sha256'];val=numeric_val(datasets,config)
    candidate_numeric=numeric.evaluate(model,tokenizer,val,run/'candidate_numeric_val.jsonl',key,
        config['max_new_tokens'],config['eval_batch_size'],seed=config.get('numeric_eval_seed', config['seed']))
    candidate_concepts=evaluate_concepts(model,tokenizer,datasets['concept_val'],run/'candidate_concept_val.jsonl',key,config)
    candidate_fresh = fresh_numeric_evaluation(model, tokenizer, datasets, run/'candidate_numeric_fresh_val.jsonl', key, config)
    audit_validations(run, datasets, config, tokenizer)
    base_numeric=json.loads((run/'baseline_numeric_val.summary.json').read_text(encoding='utf-8'))
    base_concepts=json.loads((run/'baseline_concept_val.summary.json').read_text(encoding='utf-8'))
    base_raw=direct_numeric.diagnostic(val,numeric.rows(run/'baseline_numeric_val.jsonl'))
    candidate_raw=direct_numeric.diagnostic(val,numeric.rows(run/'candidate_numeric_val.jsonl'))
    numeric.save(run/'baseline_direct_numeric.json',base_raw)
    numeric.save(run/'candidate_direct_numeric.json',candidate_raw)
    reference=retention_reference(config,val,run)
    # "baseline_val.summary.json" corresponds to "baseline_val.jsonl".
    reference_path=Path(str(config['numeric_retention_summary']).replace('.summary.json','.jsonl'))
    if not reference_path.exists():raise ValueError('Actual v3 recommended-model prediction bytes required for direct-number retention')
    parent_raw=direct_numeric.diagnostic(val,numeric.rows(reference_path))
    numeric.save(run/'parent_direct_numeric_reference.json',parent_raw)
    contracts = {'baseline': response_contract(val, numeric.rows(run/'baseline_numeric_val.jsonl')),
                 'candidate': response_contract(val, numeric.rows(run/'candidate_numeric_val.jsonl')),
                 'parent': response_contract(val, numeric.rows(reference_path))}
    numeric.save(run/'actual_response_contracts.json', contracts)
    fresh_comparison = None
    if candidate_fresh is not None:
        fresh_val = datasets['numeric_fresh_val']
        fresh_base_records = numeric.rows(run/'baseline_numeric_fresh_val.jsonl')
        fresh_candidate_records = numeric.rows(run/'candidate_numeric_fresh_val.jsonl')
        fresh_base_raw = direct_numeric.diagnostic(fresh_val, fresh_base_records)
        fresh_candidate_raw = direct_numeric.diagnostic(fresh_val, fresh_candidate_records)
        fresh_base_contract = response_contract(fresh_val, fresh_base_records)
        fresh_candidate_contract = response_contract(fresh_val, fresh_candidate_records)
        fresh_comparison = {'passed': raw_non_regression(fresh_base_raw['summary'], fresh_candidate_raw['summary'])
            and contract_non_regression(fresh_base_contract, fresh_candidate_contract),
            'baseline_raw': fresh_base_raw['summary'], 'candidate_raw': fresh_candidate_raw['summary'],
            'baseline_contract': fresh_base_contract, 'candidate_contract': fresh_candidate_contract,
            'baseline_strict': json.loads((run/'baseline_numeric_fresh_val.summary.json').read_text(encoding='utf-8')),
            'candidate_strict': candidate_fresh, 'comparison_kind': 'new V4 development validation; own pinned base pair',
            'semantic_failure_and_slice_review_required': True, 'not_the_v3_262_primary': True}
        numeric.save(run/'fresh_numeric_comparison.json', fresh_comparison)
        fresh_review_plan(run, fresh_val, {'baseline': fresh_base_records, 'candidate': fresh_candidate_records})
    numeric.save(run/'validation_complete.json',{'status':'AWAITING_ACTUAL_CONCEPT_AI_REVIEW',
        'baseline_numeric':base_numeric,'candidate_numeric':candidate_numeric,
        'baseline_concept_screening':base_concepts,'candidate_concept_screening':candidate_concepts,
        'baseline_direct_numeric':base_raw['summary'],'candidate_direct_numeric':candidate_raw['summary'],
        'v3_direct_numeric':parent_raw['summary'], 'actual_response_contracts': contracts,
        'fresh_numeric_comparison': fresh_comparison,
        'numeric_semantic_review_required': config.get('require_numeric_semantic_review', True),
        'challenge_read':False})
    if candidate_only:
        numeric.save(run/'progress.json',{'phase':'semantic_review_required','model_loaded':False})
        return
    semantics=semantic_review(run,datasets['concept_val'])
    numeric_semantics = numeric_semantic_review(run, val) if config.get('require_numeric_semantic_review', True) else None
    fresh_semantics = None
    if fresh_comparison is not None:
        plan = json.loads((run/'fresh_numeric_review_plan.json').read_text(encoding='utf-8'))
        fresh_semantics = numeric_semantic_review(run, datasets['numeric_fresh_val'],
            'fresh_numeric_semantic_review', 'numeric_fresh_val', plan['required_sample_ids'])
        fresh_comparison = {**fresh_comparison, 'ai_semantic_review': fresh_semantics,
                            'passed': fresh_comparison['passed'] and fresh_semantics['passed']}
    decision=select(base_numeric,candidate_numeric,base_concepts,candidate_concepts,reference,
                    base_raw['summary'],candidate_raw['summary'],parent_raw['summary'],semantics,
                    numeric_semantics, config.get('require_numeric_semantic_review', True), fresh_comparison, contracts)
    numeric.save(run/'selection.json',decision)
    heldout={}
    # Only now may either sealed challenge file be read.
    def run_selected(kind, examples):
        path=run/('selected_'+kind+'.jsonl')
        selected_key=key if decision['selected']=='adapter' else 'base:'+config['model_id']+':'+config['revision']
        def call():
            return (numeric.evaluate(model,tokenizer,examples,path,selected_key,config['max_new_tokens'],
                        config['eval_batch_size'],seed=config.get('numeric_eval_seed', config['seed'])) if kind=='numeric_challenge'
                    else evaluate_concepts(model,tokenizer,examples,path,selected_key,config))
        if decision['selected']=='base':
            with model.disable_adapter():return call()
        return call()
    for kind in ('numeric_challenge','concept_challenge'):
        path=root/'data'/FILES[kind]
        if path.exists():heldout[kind]=run_selected(kind,numeric.rows(path))
    result={'status':'MIXED_SFT_COMPLETED_AI_REVIEWED_RESEARCH_ONLY' if decision['candidate_improved'] else 'MIXED_SFT_REJECTED_RETENTION_OR_CONCEPT_REVIEW',
        'run_id':config['run_id'],'model_id':config['model_id'],'revision':config['revision'],
        'selected':decision['selected'],'steps':complete['steps'],'training_instances':complete['training_instances'],
        'concept_source_rows':complete['concept_source_rows'],'concept_training_instances':complete['concept_training_instances'],
        'baseline_numeric_validation':base_numeric,'candidate_numeric_validation':candidate_numeric,
        'baseline_concept_screening':base_concepts,'candidate_concept_screening':candidate_concepts,
        'concept_ai_semantic_review':semantics,
        'numeric_ai_semantic_review': numeric_semantics, 'actual_response_contracts': contracts,
        'fresh_numeric_comparison': fresh_comparison, 'load_in_4bit': config.get('load_in_4bit', False),
        'fresh_numeric_ai_semantic_review': fresh_semantics,
        'baseline_direct_numeric':base_raw['summary'],'candidate_direct_numeric':candidate_raw['summary'],
        'v3_direct_numeric_reference':parent_raw['summary'],
        'selected_challenges':heldout,'adapter_sha256':complete['adapter_sha256'],'fresh_reload_verified':True,
        'hidden_reasoning_trained':False,'teacher_review_required':True,'production_approved':False,
        'limitations':['Numeric retention covers finite published development templates, not all elementary math.',
            'Concept knowledge uses original teacher-written responses; this does not copy all teacher intelligence.',
            'Concept lexical screening is not semantic/pedagogical certification, and no mastery or 2026 consolidated legal-currency guarantee is made.',
            'Current and legacy near-duplicate cards share training; evaluation has new wording, not disjoint concept families.',
            'OCR and physical measurement/geometry observations are not learned or certified by this text-only run.']}
    numeric.save(run/'completed_run.json',result);numeric.save(run/'progress.json',{'phase':'completed','status':result['status']})
    print('MVK_MULTITASK_V4_COMPLETED='+json.dumps(result,ensure_ascii=False),flush=True)


def main(root, config_path, stage):
    config=load_config(config_path)
    root,run,datasets,instances,expanded=prepare(root,config,freeze=stage!='inspect')
    if (run/'completed_run.json').exists() and stage in ('train','evaluate','all'):
        print((run/'completed_run.json').read_text(encoding='utf-8'),flush=True);return
    tokenizer=numeric.get_tokenizer(config)
    if stage in ('inspect','preflight'):
        token_audit(instances,tokenizer,config,run,inspection=stage=='inspect');return
    if stage == 'audit':
        audit_training(run, instances, config, tokenizer)
        audit_validations(run, datasets, config, tokenizer)
        retention_reference(config, numeric_val(datasets, config), run)
        return
    if stage in ('candidate', 'evaluate'):
        audit_training(run, instances, config, tokenizer)
    import torch
    freeze_environment(run, config)
    base=load_model(config)
    if stage=='memory':memory(run,instances,config,tokenizer,base);return
    if stage in ('baseline','all'):
        baseline(run,datasets,config,tokenizer,base)
        if stage=='baseline':return
    if stage in ('train','all'):
        if not (run/'baseline_numeric_val.summary.json').exists() or not (run/'baseline_concept_val.summary.json').exists():
            raise ValueError('Both numeric and independent concept baselines must run before training')
        train(run,instances,config,tokenizer,base)
        audit_training(run, instances, config, tokenizer)
        if stage=='train':return
        del base;gc.collect();torch.cuda.empty_cache();base=load_model(config)
    if stage in ('candidate','evaluate','all'):
        # "all" is a training pipeline, not permission to invent a semantic
        # reviewer report or parse a sealed challenge before actual review.
        pause = stage == 'candidate' or (stage == 'all' and missing_semantic_reviews(run, datasets, config))
        evaluate(run,root,datasets,config,tokenizer,base,candidate_only=bool(pause))


def missing_semantic_reviews(run, datasets, config):
    names = ['concept_semantic_review.json']
    if config.get('require_numeric_semantic_review', True): names.append('numeric_semantic_review.json')
    if datasets.get('numeric_fresh_val'): names.append('fresh_numeric_semantic_review.json')
    return [name for name in names if not (Path(run)/name).exists()]


def controller_next_stage(run, config, has_fresh_validation=False):
    """Read-only stage planner for a single sequential supervised GPU job."""
    run = Path(run)
    if (run/'completed_run.json').exists(): return {'stage': 'completed', 'gpu_job_required': False}
    if not (run/'token_audit.json').exists(): return {'stage': 'preflight', 'gpu_job_required': False}
    if not (run/'memory_preflight.json').exists(): return {'stage': 'memory', 'gpu_job_required': True}
    memory_report = json.loads((run/'memory_preflight.json').read_text(encoding='utf-8'))
    if not memory_report['passed']: return {'stage': 'memory_failed', 'gpu_job_required': False, 'requires_new_reviewed_config_run': True}
    baseline_files = ['baseline_numeric_val.summary.json', 'baseline_concept_val.summary.json']
    if has_fresh_validation: baseline_files.append('baseline_numeric_fresh_val.summary.json')
    if not all((run/name).exists() for name in baseline_files): return {'stage': 'baseline', 'gpu_job_required': True}
    if not (run/'training_complete.json').exists(): return {'stage': 'train', 'gpu_job_required': True}
    if not (run/'validation_complete.json').exists(): return {'stage': 'candidate', 'gpu_job_required': True}
    missing = missing_semantic_reviews(run, {'numeric_fresh_val': has_fresh_validation}, config)
    if missing: return {'stage': 'semantic_review_required', 'gpu_job_required': False, 'missing_review_files': missing, 'challenge_read': False}
    return {'stage': 'evaluate', 'gpu_job_required': True, 'challenge_read_after_selection_only': True}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--config',required=True)
    parser.add_argument('--stage',choices=('inspect','preflight','memory','baseline','train','candidate','evaluate','audit','all'),default='all')
    args=parser.parse_args()
    try:main(args.root,args.config,args.stage)
    except Exception as error:
        try:
            config=load_config(args.config)
            numeric.save(Path(args.root)/'runs'/config['run_id']/'failure_review.json',
                {'stage':args.stage,'type':type(error).__name__,'error':str(error),'production_approved':False})
        finally:raise

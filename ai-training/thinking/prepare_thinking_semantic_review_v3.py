"""Build visible-output review packets from a complete, audited paired evaluation.

CPU only. This helper does not run inference, train, repair answers or decide
whether a hint/explanation is semantically correct. Raw hidden thinking is never
copied into its output. All 524 visible replies require an explicit AI review.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import audit_teacher_math_v3 as auditor
import teacher_math_numeric_diagnostic_v3 as numeric
import train_teacher_math_v3 as trainer


RUN_ID = 'qwen3_17b_teacher_math_v3_epoch1_seed20261013'
VALIDATION_SHA256 = '63a09313dc4ce2ae93638700908f922410804cab7f30825f2495784b07ca69cf'
EXPECTED_COUNTS = {'worked_solution': 173, 'hint': 59, 'guard': 30}
EXPECTED_SAMPLES = sum(EXPECTED_COUNTS.values())
BUCKET_ORDER = ('hint', 'guard', 'worked_solution')


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=trainer.unique_object)


def read_rows(path):
    return [json.loads(line, object_pairs_hook=trainer.unique_object)
            for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def bucket(row):
    if row['target']['status'] != 'solve':
        return 'guard'
    if row['mode'] not in ('hint', 'worked_solution'):
        raise ValueError('Unknown reference mode')
    return row['mode']


def require_complete_references(references):
    ids = [row['sample_id'] for row in references]
    if len(ids) != EXPECTED_SAMPLES or len(set(ids)) != len(ids):
        raise ValueError('Exactly 262 distinct validation references required')
    if dict(Counter(bucket(row) for row in references)) != EXPECTED_COUNTS:
        raise ValueError('Reference composition must be 173 worked / 59 hints / 30 guards')
    if any(row.get('split') != 'val' for row in references):
        raise ValueError('Only frozen validation references are allowed')
    return ids


def check_protocol(protocol, validation_path, state):
    if state.get('phase') != 'completed_numeric_comparison':
        raise ValueError('Evaluation is not complete; no partial review packets')
    expected = {'run_id': RUN_ID, 'model_id': trainer.MODEL, 'revision': trainer.REVISION,
                'validation_sha256': VALIDATION_SHA256, 'samples': EXPECTED_SAMPLES,
                'seed': 20261013, 'thinking': True, 'temperature': .6, 'top_p': .95,
                'top_k': 20, 'max_new_tokens': 2048, 'batch_size': 4,
                'primary_greedy_selection_unchanged': True, 'challenge_loaded': False,
                'optimizer_steps': 0, 'production_approved': False, 'teacher_certified': False}
    for key, value in expected.items():
        if protocol.get(key) != value:
            raise ValueError('Unexpected protocol field: ' + key)
    if trainer.sha(validation_path) != VALIDATION_SHA256:
        raise ValueError('Actual validation bytes differ from frozen protocol')
    if not re.fullmatch('[0-9a-f]{64}', protocol.get('adapter_sha256', '')):
        raise ValueError('Missing actual adapter fingerprint')
    directory = Path(__file__).resolve().parent
    for name in ('train_teacher_math_v3.py', 'teacher_math_data_v3.py',
                 'audit_teacher_math_v3.py', 'teacher_math_numeric_diagnostic_v3.py'):
        path = directory / name
        if protocol.get('dependency_sha256', {}).get(name) != trainer.sha(path):
            raise ValueError('Review dependency differs from generation protocol: ' + name)


def check_metadata(metadata, protocol, references, model_name, tokenizer):
    model_key = ('base:' + protocol['model_id'] + ':' + protocol['revision']
                 if model_name == 'baseline' else 'adapter:' + protocol['adapter_sha256'])
    expected = {'model_key': model_key, 'ids': [row['sample_id'] for row in references],
                'enable_thinking': True, 'do_sample': True, 'seed': protocol['seed'],
                'max_new_tokens': protocol['max_new_tokens'], 'batch_size': protocol['batch_size'],
                'temperature': protocol['temperature'], 'top_p': protocol['top_p'],
                'top_k': protocol['top_k'], 'eos_token_id': tokenizer.eos_token_id,
                'input_sha256': hashlib.sha256(json.dumps(references, ensure_ascii=False,
                                                         sort_keys=True).encode()).hexdigest()}
    if metadata != expected:
        raise ValueError('Actual model/input/generation metadata differs: ' + model_name)


def check_records(references, records, metadata, tokenizer):
    """Check associations and independently reconstruct generated text and scores."""
    ids = [row['sample_id'] for row in records]
    reference_ids = [row['sample_id'] for row in references]
    if ids != reference_ids or len(set(ids)) != len(ids):
        raise ValueError('Prediction count / IDs / order / duplicates differ')
    for row, record in zip(references, records):
        tokens = record.get('generated_ids')
        if not isinstance(tokens, list) or not tokens or any(type(token) is not int or token < 0 for token in tokens):
            raise ValueError('Generated token IDs must be nonnegative integers, not booleans')
        if type(record.get('generated_tokens')) is not int or type(record.get('eos_observed')) is not bool:
            raise ValueError('Malformed token bookkeeping')
        if any(type(value) is not bool for value in record.get('scores', {}).values()):
            raise ValueError('Scores must be explicit boolean observations')
        if record.get('topic') != row.get('topic', 'unspecified') or record.get('answer_kind') != row.get('answer_kind', 'numeric'):
            raise ValueError('Prediction topic / answer kind associated with wrong reference')
        auditor.check_prediction(row, record, metadata, tokenizer)


def visible_output(record):
    """Return only text after the last thought close; never expose an open thought."""
    text = record['prediction']
    opened = record.get('thought_prefix_open', False)
    has_tags = '<think>' in text or '</think>' in text
    if opened or has_tags:
        if '</think>' not in text:
            return {'text': None, 'strict_parsed': None, 'parse_error': 'no_closed_visible_answer'}
        text = text.rsplit('</think>', 1)[-1]
        if '<think>' in text or '</think>' in text:
            return {'text': None, 'strict_parsed': None, 'parse_error': 'unclosed_thought_in_final_segment'}
    text = text.strip()
    try:
        parsed = trainer.parse_output(record['prediction'], record['scores']['truncated'],
                                      thought_prefix_open=opened)
        return {'text': text, 'strict_parsed': parsed, 'parse_error': None}
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        # The final visible segment is retained for reviewing schema failures;
        # the raw original prediction and token IDs never enter the packet.
        return {'text': text, 'strict_parsed': None, 'parse_error': type(error).__name__}


RUBRIC = {
    'all': ['Output addresses the actual Vietnamese problem and requested mode.',
            'No invented facts, images, tables or student work.',
            'Visible language and method suit the declared grade; note curriculum uncertainty.',
            'Missing/malformed/truncated visible answers are recorded as failures, not repaired.'],
    'hint': ['Useful next question, related to the quantities actually given and requested.',
             'No computed answer, solution sequence or indirect answer disclosure.',
             'Preserves quoted wrong student work; does not endorse it or name the wrong column.',
             'Format/leakage screen is advisory and does not prove meaning or usefulness.'],
    'guard': ['Clarifies the real missing information or names the genuine scope limit.',
              'Does not invent an answer or refuse a solvable in-scope problem.',
              'One useful, specific follow-up for the child when clarification is needed.'],
    'worked_solution': ['Generated final number and unit are evaluated separately.',
                        'Each expression/result is arithmetically valid and uses relevant data.',
                        'Each explanation correctly describes its displayed operation and quantities.',
                        'Overall steps solve the question; a different valid method is allowed.',
                        'Reference-expression matching is not a proof of data-role semantics.',
                        'Do not accept a correct result with false reasoning as correct guidance.']}


def pending_review(kind):
    common = {'status': 'PENDING_AI_SEMANTIC_RESEARCH_REVIEW', 'human_verified': False,
              'semantic_correct': None, 'instruction_followed': None, 'grade_appropriate': None,
              'invented_data_or_image': None, 'severe_error': None, 'reason': None}
    if kind == 'hint':
        common.update(hint_relevance=None, hint_usefulness=None, answer_leakage=None,
                      observed_student_error_handled_correctly=None)
    elif kind == 'guard':
        common.update(guard_reason_valid=None, clarification_specific_and_useful=None)
    else:
        common.update(explanation_operation_consistent=None, data_roles_correct=None,
                      displayed_method_valid=None, step_by_step_guidance_useful=None)
    return common


def make_packet(row, record, model_name, direct_numeric):
    kind = bucket(row)
    visible = visible_output(record)
    result = {'model': model_name, 'sample_id': row['sample_id'], 'grade': row['grade'],
              'topic': row['topic'], 'kind': kind, 'mode': row['mode'], 'problem': row['problem'],
              'observed_work_verbatim': row.get('observed_work_verbatim'),
              'reference': {'target': row['target'], 'facts': row.get('facts', []),
                            'parameters': row.get('parameters', {}),
                            'curriculum_assignment': row.get('curriculum_assignment'),
                            'semantic_correctness_verified': row.get('semantic_correctness_verified', False)},
              'visible_output': visible,
              'automatic_observations': {'strict_scores': record['scores'],
                                        'direct_generated_numeric': direct_numeric,
                                        'certifies_explanation_or_hint_meaning': False},
              'review': pending_review(kind)}
    return result


def write_rows(path, records):
    Path(path).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in records),
                         encoding='utf-8', newline='\n')


def review_plan():
    return {'schema': 'mvk_thinking_visible_semantic_review_plan_v1',
            'run_id': RUN_ID, 'evaluation_id': 'full_thinking_validation_seed20261013',
            'state': 'PREPARED_NOT_YET_REVIEWED', 'review_kind': 'AI_SEMANTIC_RESEARCH_REVIEW',
            'models': ['baseline', 'candidate'], 'expected_samples_per_model': EXPECTED_SAMPLES,
            'expected_counts_per_model': EXPECTED_COUNTS, 'validation_sha256': VALIDATION_SHA256,
            'helper_sha256': trainer.sha(__file__),
            'selection': 'Complete census of 59 hints, 30 guards and 173 worked solutions per model.',
            'worked_solution_shard_size': 20,
            'rubric': RUBRIC, 'hidden_thinking_included': False, 'human_verified': False,
            'teacher_certified': False, 'production_approved': False,
            'limits': ['Semantic/pedagogical labels require reading actual visible outputs.',
                       'The helper only verifies artifact provenance, token reconstruction and arithmetic scores.',
                       'AI-authored validation and one sampling seed are a development evaluation, not private human gold.',
                       'Known validation commutative collision needs separate 261-case sensitivity reporting.',
                       'No OCR/image accuracy or all-curriculum mastery is demonstrated by these text packets.']}


def materialize(validation_path, evaluation_dir, output_dir, tokenizer):
    evaluation_dir, output_dir = Path(evaluation_dir), Path(output_dir)
    protocol, state = load_json(evaluation_dir / 'protocol.json'), load_json(evaluation_dir / 'state.json')
    check_protocol(protocol, validation_path, state)
    references = read_rows(validation_path)
    ids = require_complete_references(references)
    by_id = {row['sample_id']: row for row in references}
    verified, packets = {}, {}
    for name in ('baseline', 'candidate'):
        path = evaluation_dir / (name + '.jsonl')
        records, metadata = read_rows(path), load_json(path.with_suffix('.metadata.json'))
        check_metadata(metadata, protocol, references, name, tokenizer)
        check_records(references, records, metadata, tokenizer)
        technical_audit = auditor.check_evaluation(path, by_id, tokenizer)
        direct = numeric.diagnostic(references, records)
        direct_by_id = {record['sample_id']: record for record in direct['records']}
        packets[name] = [make_packet(row, record, name, direct_by_id.get(row['sample_id']))
                         for row, record in zip(references, records)]
        verified[name] = {'predictions_sha256': trainer.sha(path),
                          'metadata_sha256': trainer.sha(path.with_suffix('.metadata.json')),
                          'summary_sha256': trainer.sha(path.with_suffix('.summary.json')),
                          'technical_audit': technical_audit,
                          'direct_numeric_summary': direct['summary']}
    # No artifacts are emitted until both full evaluations have independently passed.
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError('Output directory is nonempty; preserve earlier review evidence')
    output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save(output_dir / 'review_plan.json', review_plan())
    files, shards = {}, []
    decisions = []
    for name, model_packets in packets.items():
        for kind in BUCKET_ORDER:
            selected = [packet for packet in model_packets if packet['kind'] == kind]
            path = output_dir / f'{name}_{kind}_review_packets.jsonl'
            write_rows(path, selected)
            files[path.name] = {'sha256': trainer.sha(path), 'records': len(selected),
                                'sample_ids': [packet['sample_id'] for packet in selected]}
            if kind == 'worked_solution':
                for start in range(0, len(selected), 20):
                    subset = selected[start:start + 20]
                    shard_path = output_dir / f'{name}_worked_shard_{start // 20:02d}.jsonl'
                    write_rows(shard_path, subset)
                    shards.append({'file': shard_path.name, 'model': name, 'kind': kind,
                                   'sha256': trainer.sha(shard_path), 'records': len(subset),
                                   'sample_ids': [packet['sample_id'] for packet in subset]})
        decisions.extend({'model': name, 'sample_id': packet['sample_id'], 'grade': packet['grade'],
                          'kind': packet['kind'], 'review': packet['review']} for packet in model_packets)
    write_rows(output_dir / 'review_decisions_template.jsonl', decisions)
    trainer.save(output_dir / 'worked_shard_index.json', {'shard_size': 20, 'shards': shards,
                 'coverage': 'Exactly one worked shard per model/sample; same visible packets as full census files.'})
    evidence = {'schema': 'mvk_thinking_visible_review_packet_evidence_v1', 'run_id': RUN_ID,
                'status': 'PACKETS_TECHNICALLY_VERIFIED_SEMANTIC_REVIEW_PENDING',
                'helper_sha256': trainer.sha(__file__), 'validation_sha256': trainer.sha(validation_path),
                'protocol_sha256': trainer.sha(evaluation_dir / 'protocol.json'),
                'state_sha256': trainer.sha(evaluation_dir / 'state.json'), 'samples_per_model': len(ids),
                'model_evidence': verified, 'packet_files': files, 'worked_shards': shards,
                'hidden_thinking_included': False, 'semantic_review_completed': False,
                'human_verified': False, 'production_approved': False, 'teacher_certified': False}
    trainer.save(output_dir / 'review_packet_evidence.json', evidence)
    return evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--validation', type=Path)
    parser.add_argument('--evaluation-dir', type=Path)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--write-plan', type=Path,
                        help='Prepare only the review plan; does not claim actual evaluation/review completion.')
    args = parser.parse_args()
    if args.write_plan:
        trainer.save(args.write_plan, review_plan())
        print(json.dumps({'status': 'PLAN_ONLY', 'path': str(args.write_plan)}, ensure_ascii=False))
        return
    if not all((args.validation, args.evaluation_dir, args.output_dir)):
        parser.error('--validation, --evaluation-dir and --output-dir required')
    # Check completion before fetching/loading even the CPU tokenizer.
    protocol, state = load_json(args.evaluation_dir / 'protocol.json'), load_json(args.evaluation_dir / 'state.json')
    check_protocol(protocol, args.validation, state)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(protocol['model_id'], revision=protocol['revision'],
                                             trust_remote_code=False)
    evidence = materialize(args.validation, args.evaluation_dir, args.output_dir, tokenizer)
    print(json.dumps({'status': evidence['status'], 'samples_per_model': evidence['samples_per_model'],
                      'output_dir': str(args.output_dir)}, ensure_ascii=False))


if __name__ == '__main__':
    main()

"""Posthoc validation sensitivity; read frozen evidence and write one report.

This omits exactly the previously identified commutative collision from scoring.
It does not regenerate predictions, train, alter primary reports, or select weights.
Only the pinned tokenizer is loaded, with local_files_only=True; no model or GPU.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import audit_teacher_math_v3 as auditor
import teacher_math_numeric_diagnostic_v3 as numeric
import train_teacher_math_v3 as trainer


EXCLUDED_ID = '91d23b441cd60a087952fa5c'
TRAIN_COLLISION_ID = 'dfc221b66edf3373ee52c845'


def summary(records):
    out = trainer.aggregate(records)
    out['per_grade'] = {
        str(grade): trainer.aggregate([r for r in records if r['grade'] == grade])
        for grade in sorted({r['grade'] for r in records}, key=str)
    }
    out['per_topic'] = {
        topic: trainer.aggregate([r for r in records if r['topic'] == topic])
        for topic in sorted({r['topic'] for r in records})
    }
    return out


def raw_gate(baseline, candidate):
    axes = ('numeric_correct', 'answer_unit_correct')
    overall = all(candidate[key] >= baseline[key] for key in axes)
    by_grade = {
        grade: all(candidate['per_grade'][grade][key] >= values[key] for key in axes)
        for grade, values in baseline['per_grade'].items()
    }
    return {'overall_non_regression': overall, 'per_grade_non_regression': all(by_grade.values()),
            'per_grade': by_grade}


def main():
    from transformers import AutoTokenizer
    root = Path(__file__).resolve().parent
    data = root / 'data' / 'teacher_math_v3'
    run = root / 'evidence' / 'teacher_math_v3_20261013' / 'main_run_readback'
    output = run / 'validation261_sensitivity.json'
    paths = [Path(__file__).resolve(), root / 'train_teacher_math_v3.py',
             root / 'teacher_math_data_v3.py', root / 'audit_teacher_math_v3.py',
             root / 'teacher_math_numeric_diagnostic_v3.py', data / 'generated' / 'train.jsonl',
             data / 'generated' / 'val.jsonl', data / 'split_independence_audit.json',
             run / 'config.json', run / 'completed_run.json', run / 'role_review.json']
    for model in ('baseline', 'candidate'):
        paths += [run / f'{model}_val{suffix}' for suffix in ('.jsonl', '.metadata.json', '.summary.json')]
    before = {str(path.relative_to(root)): trainer.sha(path) for path in paths}
    config = json.loads((run / 'config.json').read_text(encoding='utf-8'))
    for split in ('train', 'val'):
        assert trainer.sha(data / 'generated' / f'{split}.jsonl') == config['dataset_fingerprints'][split]
    for name, digest in config['source_hashes'].items():
        assert trainer.sha(root / name) == digest
    independence = json.loads((data / 'split_independence_audit.json').read_text(encoding='utf-8'))
    assert independence['posthoc_nonoverlap_subset']['val']['excluded_sample_ids'] == [EXCLUDED_ID]
    cases = independence['comparisons']['train_vs_val']['overlap_cases']
    assert len(cases) == 1 and cases[0]['train_sample_ids'] == [TRAIN_COLLISION_ID]
    assert cases[0]['val_sample_ids'] == [EXCLUDED_ID]
    refs = trainer.rows(data / 'generated' / 'val.jsonl')
    train = trainer.rows(data / 'generated' / 'train.jsonl')
    assert len(refs) == 262 and len({r['sample_id'] for r in refs}) == 262
    by_id = {r['sample_id']: r for r in refs}
    excluded = by_id[EXCLUDED_ID]
    collision = next(r for r in train if r['sample_id'] == TRAIN_COLLISION_ID)
    kept_refs = [r for r in refs if r['sample_id'] != EXCLUDED_ID]
    assert len(kept_refs) == 261
    assert [r['sample_id'] for r in kept_refs] == independence['posthoc_nonoverlap_subset']['val']['included_sample_ids']
    tokenizer = AutoTokenizer.from_pretrained(config['model_id'], revision=config['revision'], local_files_only=True)
    full, reduced, checks, removed = {}, {}, {}, {}
    for model in ('baseline', 'candidate'):
        path = run / f'{model}_val.jsonl'
        checks[model] = auditor.check_evaluation(path, by_id, tokenizer)
        records = trainer.rows(path)
        assert {r['sample_id'] for r in records} == set(by_id)
        kept = [r for r in records if r['sample_id'] != EXCLUDED_ID]
        full[model] = {'strict': summary(records), 'raw': numeric.diagnostic(refs, records)['summary']}
        reduced[model] = {'strict': summary(kept), 'raw': numeric.diagnostic(kept_refs, kept)['summary']}
        omitted = next(r for r in records if r['sample_id'] == EXCLUDED_ID)
        removed[model] = {'prediction': omitted['prediction'], 'scores': omitted['scores'],
                          'raw': numeric.diagnostic([excluded], [omitted])['records'][0]}
        assert reduced[model]['strict']['samples'] == 261
        assert reduced[model]['raw']['solution_samples'] == 172
    completed = json.loads((run / 'completed_run.json').read_text(encoding='utf-8'))
    role = json.loads((run / 'role_review.json').read_text(encoding='utf-8'))
    for model, key in (('baseline', 'baseline_raw_validation'), ('candidate', 'candidate_raw_validation')):
        assert full[model]['raw'] == role[key]
    selections = {
        'primary262_recomputed': trainer.select_candidate(full['baseline']['strict'], full['candidate']['strict']),
        'supplemental261': trainer.select_candidate(reduced['baseline']['strict'], reduced['candidate']['strict']),
    }
    assert selections['primary262_recomputed']['selected'] == completed['selected'] == role['strict_selection']
    gates = {
        'primary262': raw_gate(full['baseline']['raw'], full['candidate']['raw']),
        'supplemental261': raw_gate(reduced['baseline']['raw'], reduced['candidate']['raw']),
    }
    after = {str(path.relative_to(root)): trainer.sha(path) for path in paths}
    assert before == after, 'Frozen source, data, or evidence mutated while computing sensitivity'
    report = {
        'audit_id': 'teacher_math_v3_validation261_commutative_collision_sensitivity_20261013',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'PASSED_RECOMPUTATION_SELECTION_UNCHANGED',
        'run_id': config['run_id'],
        'supplemental_posthoc_analysis': True,
        'primary_selection_or_metrics_modified': False,
        'new_training_or_inference_performed': False,
        'gpu_used': False,
        'concept_challenge_read': False,
        'protocol': {'excluded_sample_ids': [EXCLUDED_ID], 'primary_samples': 262,
                     'supplemental_samples': 261, 'solve_worked_samples': 172,
                     'hint_samples': 59, 'guard_samples': 30,
                     'raw_extraction': 'unchanged bounded JSON answer/unit diagnostic',
                     'strict': 'unchanged original trainer.score and trainer.aggregate',
                     'tokenizer_model': config['model_id'], 'tokenizer_revision': config['revision'],
                     'tokenizer_local_files_only': True,
                     'generated_token_ids_and_scores_recomputed': True},
        'excluded_reference': {'sample_id': EXCLUDED_ID, 'grade': excluded['grade'],
                               'topic': excluded['topic'], 'mode': excluded['mode'],
                               'problem': excluded['problem'], 'target': excluded['target']},
        'train_collision': {'sample_id': TRAIN_COLLISION_ID, 'problem': collision['problem'],
                            'target': collision['target'], 'classification': cases[0]['classification']},
        'source_and_input_sha256': before,
        'dependency_files_unchanged': before == after,
        'prediction_audit': checks,
        'primary262': full,
        'supplemental261': reduced,
        'excluded_prediction': removed,
        'strict_selections': selections,
        'raw_retention_gates': gates,
        'selection_unchanged': selections['primary262_recomputed']['selected'] == selections['supplemental261']['selected'],
        'supplemental_final_recommended_weights': 'base' if (
            selections['supplemental261']['selected'] == 'base'
            or not gates['supplemental261']['overall_non_regression']
            or not gates['supplemental261']['per_grade_non_regression']) else 'adapter',
        'production_approved': False,
        'teacher_pedagogy_verified': False,
        'limits': [
            'One known commutative collision excluded; global semantic independence is not certified.',
            'The subset and extraction diagnostic are posthoc; this is sensitivity evidence, not a replacement primary metric.',
            'Strict solution_verified requires the reference path; zero strict score does not imply zero mathematical ability.',
            'Hint format safety does not verify teaching meaning or correctness.',
            'This reuses completed greedy no-thinking predictions; it does not evaluate the new thinking-mode run.'
        ]
    }
    assert report['selection_unchanged'] and report['supplemental_final_recommended_weights'] == 'base'
    trainer.save(output, report)
    print(json.dumps({'output': str(output), 'sha256': trainer.sha(output), 'status': report['status'],
                      'raw261': {m: reduced[m]['raw'] for m in reduced},
                      'strict_selection': selections['supplemental261'], 'raw_gate': gates['supplemental261']},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

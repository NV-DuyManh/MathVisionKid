"""Eight new authored arithmetic holdouts, reserved before view selection."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import exhaustive_cloud_resume as resume
import exhaustive_multidigit_math as m
from review_cloud_multidigit_current import independent

HERE = Path(__file__).resolve().parent
RUN = HERE / 'cloud_publication/resume_20261018'
SPECS = (
    ('validation', '/', 813251, 67), ('validation', '/', 719357, 83),
    ('validation', '*', 8267, 134), ('validation', '*', 7619, 258),
    ('test', '/', 953719, 137), ('test', '/', 617837, 239),
    ('test', '*', 5731, 467), ('test', '*', 8249, 318),
)
def j(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
def sha(b): return hashlib.sha256(b).hexdigest()
def save(path, obj): path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), 'utf-8')

def main():
    resume.configure_sources()
    old_boundaries = [json.loads(line) for line in (RUN / 'boundary_cases.jsonl').read_text('utf-8').splitlines()]
    old_ids = {r['sample_id'] for r in old_boundaries}
    rows, chats, reviews = [], [], []
    sigs = {'validation': set(), 'test': set()}
    groups = {'validation': set(), 'test': set()}
    for split, op, a, b in SPECS:
        row = m.make_row(op, a, b)
        assert row['sample_id'] not in old_ids and (op, a, b) not in m.REGRESSION_PAIRS
        assert a > 1000  # Not in preserved initial dividend or multiplication grids.
        row.update(split=split, training_eligible=False, evaluation_eligible=True)
        row['coverage'].update(mode='FINITE_NEW_ARITHMETIC_HOLDOUT',
                               reservation='NEW_INPUT_PAIR_BEFORE_BALANCED_VIEW_SELECTION')
        row['holdout_reservation'] = {
            'suite': 'fresh_multidigit_holdouts.v1',
            'reserved_before_selected_training_view': True,
            'source_origin': 'NEW_DETERMINISTIC_EXACT_ARITHMETIC',
            'not_imported_from_sealed_or_existing_assessment': True,
            'all_canonical_step_and_check_signatures_must_be_excluded_from_selected_train': True,
        }
        m.validate_row(row); independent(row)
        sigs[split].update(row['canonical_signatures'])
        groups[split].add(row['case_group_id'])
        rows.append(row)
        # The training-only serializer intentionally refuses training_eligible
        # false. Reuse its neutral format explicitly for evaluation export,
        # preserving the source's false training eligibility in every record.
        for chat in m.base.chat_records(row):
            chat.update(split=split, acceptance_status=row['acceptance_status'],
                        training_eligible=False, evaluation_eligible=True,
                        source_row_sha256=sha(j(row).encode()))
            chats.append(chat)
        reviews.append({'sample_id': row['sample_id'],
                        'source_row_sha256': sha(j(row).encode()),
                        'actual_content_semantic_review': 'PENDING_FULL_ACTUAL_OUTPUT_READ',
                        'exact_oracles_and_trace': 'PASS'})
    assert not groups['validation'] & groups['test']
    cases = RUN / 'holdout_arithmetic_cases.jsonl'
    chat_path = RUN / 'holdout_arithmetic_chat.jsonl'
    cases.write_text(''.join(j(r) + '\n' for r in rows), 'utf-8')
    chat_path.write_text(''.join(j(c) + '\n' for c in chats), 'utf-8')
    assert len(chats) == 32 and len(rows) == 8
    reservation = {
        'schema': 'mathvisionkid.fresh_arithmetic_holdout_reservations.v1',
        'case_groups_by_split': {s: sorted(v) for s, v in groups.items()},
        'canonical_signatures_by_split': {s: sorted(v) for s, v in sigs.items()},
        'all_train_exclusion_signatures': sorted(sigs['validation'] | sigs['test']),
        'reserved_before_training_view_selection': True,
        'cross_evaluation_split_shared_primitive_signatures': sorted(sigs['validation'] & sigs['test']),
        'independence_limit': 'Primary ordered inputs/case groups are disjoint across validation and test. Elementary arithmetic inside digit traces may coincide; do not claim all primitive facts disjoint between the two evaluation splits. All signatures must be excluded from the newly selected balanced training view, not retrospectively from frozen archives.',
    }
    save(RUN / 'holdout_arithmetic_reservations.json', reservation)
    qa = {
        'status': 'EXACT_ORACLES_PASSED_PENDING_ACTUAL_OUTPUT_REVIEW',
        'cases': len(rows), 'chat_rows': len(chats), 'splits': {'validation': 4, 'test': 4},
        'source_sha256': sha(cases.read_bytes()), 'chat_sha256': sha(chat_path.read_bytes()),
        'module_sha256': sha((HERE / 'exhaustive_multidigit_math.py').read_bytes()),
        'template_sha256': m.template_fingerprint(),
        'builder_sha256': sha(Path(__file__).read_bytes()),
        'new_input_pairs_vs_boundary_and_completed_initial_domains': True,
        'old_data_rewritten': False, 'human_manual_review_claimed': False,
        'independent_external_review': False, 'row_reviews': reviews,
        'shared_primitive_signature_count_between_validation_test': len(sigs['validation'] & sigs['test']),
        'reservation_path': str((RUN / 'holdout_arithmetic_reservations.json').relative_to(HERE.parent)),
    }
    save(RUN / 'holdout_arithmetic_qa.json', qa)
    print(json.dumps({k: v for k, v in qa.items() if k != 'row_reviews'}))

if __name__ == '__main__': main()

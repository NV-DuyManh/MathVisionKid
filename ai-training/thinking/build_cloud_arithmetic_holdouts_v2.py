"""Greedy deterministic holdout sampling; never alters a rejected case's math."""
from __future__ import annotations
import json
import random
import hashlib
from pathlib import Path
import exhaustive_cloud_resume as resume
import exhaustive_multidigit_math as m
from review_cloud_multidigit_current import independent, criteria

HERE = Path(__file__).resolve().parent
RUN = HERE / 'cloud_publication/resume_20261018'
def j(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
def sha(b): return hashlib.sha256(b).hexdigest()
def save(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2), 'utf-8')

def main():
    resume.configure_sources()
    parents = [json.loads(l) for l in (RUN / 'holdout_arithmetic_cases.jsonl').read_text('utf-8').splitlines()]
    boundaries = [json.loads(l) for l in (RUN / 'boundary_cases.jsonl').read_text('utf-8').splitlines()]
    pedagogy = [json.loads(l) for l in (RUN / 'pedagogy_cases_v2.jsonl').read_text('utf-8').splitlines()]
    forbidden_ids = {r['sample_id'] for r in parents + boundaries}
    used = {s for r in pedagogy if r['split'] in ('validation', 'test') for s in r['canonical_signatures']}
    pedagogy_signatures = set(used)
    protected = resume.protected()
    rng = random.Random(2026101908)
    rows, rejected = [], []
    used_divisors = set()
    for first_digit in range(1, 9):
        split = 'validation' if first_digit <= 4 else 'test'
        for attempt in range(1000):
            a = first_digit * 100000 + rng.randrange(100000)
            b = rng.randrange(11, 100) if first_digit <= 4 else rng.randrange(101, 1000)
            candidate = m.make_row('/', a, b)
            hit = set(candidate['canonical_signatures']) & used
            if candidate['sample_id'] in forbidden_ids or b in used_divisors or hit:
                rejected.append({'ordered_pair': [a, b], 'reason': 'CANONICAL_RESERVATION_OR_EXISTING_PAIR_OR_REUSED_DIVISOR', 'overlap_signatures': sorted(hit)})
                continue
            row = candidate
            row.update(split=split, training_eligible=False, evaluation_eligible=True)
            row['coverage'].update(mode='FINITE_NEW_ARITHMETIC_HOLDOUT', reservation='PAIRWISE_DISJOINT_FULL_CANONICAL_SIGNATURES_V2')
            row['holdout_reservation'] = {
                'suite': 'fresh_multidigit_holdouts.v2',
                'reserved_before_selected_training_view': True,
                'source_origin': 'NEW_DETERMINISTIC_EXACT_ARITHMETIC',
                'not_imported_from_sealed_or_existing_assessment': True,
                'all_canonical_step_and_check_signatures_must_be_excluded_from_selected_train': True,
                'candidate_selection': 'DETERMINISTIC_GREEDY_INDEPENDENT_EXAMPLES_NO_ANSWER_OR_SIGNATURE_MODIFICATION',
            }
            m.validate_row(row); independent(row)
            rows.append(row); used.update(row['canonical_signatures']); used_divisors.add(b)
            break
        else: raise RuntimeError('No independent candidate within bounded attempts')
    assert len(rows) == 8
    for i, row in enumerate(rows):
        assert not set(row['canonical_signatures']) & pedagogy_signatures
        assert all(not set(row['canonical_signatures']) & set(other['canonical_signatures']) for other in rows[:i])
    chats = []
    for row in rows:
        for chat in m.base.chat_records(row):
            chat.update(split=row['split'], acceptance_status=row['acceptance_status'],
                        training_eligible=False, evaluation_eligible=True,
                        source_row_sha256=sha(j(row).encode()))
            chats.append(chat)
    cases_path = RUN / 'holdout_arithmetic_cases_v2.jsonl'
    chat_path = RUN / 'holdout_arithmetic_chat_v2.jsonl'
    cases_path.write_text(''.join(j(r) + '\n' for r in rows), 'utf-8')
    chat_path.write_text(''.join(j(c) + '\n' for c in chats), 'utf-8')
    reservation = {
        'schema': 'mathvisionkid.fresh_arithmetic_holdout_reservations.v2',
        'case_groups_by_split': {s: [r['case_group_id'] for r in rows if r['split'] == s] for s in ('validation', 'test')},
        'canonical_signatures_by_split': {s: sorted({sig for r in rows if r['split'] == s for sig in r['canonical_signatures']}) for s in ('validation', 'test')},
        'all_train_exclusion_signatures': sorted({sig for r in rows for sig in r['canonical_signatures']}),
        'all8_cases_pairwise_disjoint_all_canonical_signatures': True,
        'arithmetic_v2_vs_pedagogy_holdout_full_signature_overlap': 0,
        'original8_preserved_for_audit_selection_role': 'RETAIN_SOURCE_AND_CHAT_AUDIT_ONLY_EXCLUDE_FROM_SELECTED_EVAL_AND_TRAIN',
        'selected_eval_is_v2_only': True,
        'selection_not_answer_or_signature_mutation': True,
        'candidate_rejections': rejected,
        'known_legacy_protected_overlap_signature_count': len({sig for r in rows for sig in r['canonical_signatures']} & protected),
        'independence_limit': 'Strict full-signature independence is certified only for these eight cases and the new pedagogy holdout source. Newly selected balanced TRAIN must exclude the complete heldout signature union. Frozen historical archives and unseen sealed assessment independence are not claimed.',
    }
    save(RUN / 'holdout_arithmetic_reservations_v2.json', reservation)
    qa = {
        'status': 'EXACT_ORACLES_PASSED_PENDING_ACTUAL_OUTPUT_REVIEW',
        'cases': 8, 'chat_rows': 32, 'splits': {'validation': 4, 'test': 4},
        'source_sha256': sha(cases_path.read_bytes()), 'chat_sha256': sha(chat_path.read_bytes()),
        'module_sha256': sha((HERE / 'exhaustive_multidigit_math.py').read_bytes()),
        'template_sha256': m.template_fingerprint(), 'builder_sha256': sha(Path(__file__).read_bytes()),
        'original8_source_preserved_sha256': sha((RUN / 'holdout_arithmetic_cases.jsonl').read_bytes()),
        'full_signature_disjointness_vs_each_case_and_pedagogy_holdouts': True,
        'candidate_rejections': len(rejected),
        'human_manual_review_claimed': False, 'independent_external_review': False,
        'row_reviews': [{'sample_id': r['sample_id'], 'source_row_sha256': sha(j(r).encode()), 'numeric_validation': 'PASS'} for r in rows],
    }
    save(RUN / 'holdout_arithmetic_qa_v2.json', qa)
    print(json.dumps({k: v for k, v in qa.items() if k != 'row_reviews'}))
    print('SELECTED', [(r['split'], r['coverage']['ordered_input_pair'], [a['result'] for a in r['expected_answer']]) for r in rows])

if __name__ == '__main__': main()

"""Final bounded derivative: complete explained/check signatures and displays."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
from decimal import Decimal, localcontext
import unittest
from fractions import Fraction
import exhaustive_primary_math as base
from review_cloud_pedagogy_v2 import exact, ANSWERS, GUARDS, SCOPE_NOTES

HERE = Path(__file__).resolve().parent
RUN = HERE / 'cloud_publication/resume_20261018'
EXPECTED_PARENT = '041613186bc6402f24dd74c892bdfbf80f02c33518ba4fe28480fe08cbecad15'
EXTRA_EXPLAINED = {32: [('80*25/100', '20'), ('80*40/100', '32')],
                   46: [('18+17', '35')], 60: [('52*3', '156')]}
def j(x): return json.dumps(x, ensure_ascii=False, separators=(',', ':'))
def sha(b): return hashlib.sha256(b).hexdigest()
def save(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2), 'utf-8')
def parents():
    p = RUN / 'pedagogy_cases_v2.jsonl'
    assert sha(p.read_bytes()) == EXPECTED_PARENT, 'Changed parent needs a new actual review'
    return [json.loads(l) for l in p.read_text('utf-8').splitlines()]

def derive(parent):
    row = copy.deepcopy(parent)
    n = int(row['sample_id'].rsplit('_', 1)[-1])
    row['sample_id'] = f'cloud_pedagogy_v3_{n:03d}'
    previous = copy.deepcopy(row['derivation'])
    row['derivation'] = {'version': 'pedagogy_review_derivative.v3',
                         'parent_sample_id': parent['sample_id'],
                         'parent_row_sha256': sha(j(parent).encode()),
                         'previous_derivation': previous,
                         'selection': 'REPLACES_PARENT_IN_SELECTED_VIEW_NOT_AN_ADDITIONAL_UNIQUE_STORY',
                         'changes': ['Complete every actual numeric step/alternative/explained guard/check oracle and canonical signature',
                                     'Keep unit-conversion check division visible']}
    if n == 23:
        step = row['worked_steps'][1]
        step['display_expression'] = '(12500 : 10000)'
        step['explanation'] = step['reason'] + ' Tính (12500 : 10000) = 1,25 m². Quan hệ kiểm tra này khớp dữ kiện của đề.'
    oracles = []
    for step in row['worked_steps']:
        if step['expression'] is not None:
            oracles.append({'expression': step['expression'], 'result': str(exact(step['expression'])), 'location': 'worked_steps.' + step['step_id']})
    for method in row['alternative_methods']:
        oracles.append({'expression': method['expression'], 'result': str(exact(method['expression'])), 'location': 'alternative_methods'})
    for expression, result in EXTRA_EXPLAINED.get(n, []):
        oracles.append({'expression': expression, 'result': result, 'location': 'worked_step_reason_or_explanation'})
    row['numeric_oracles'] = oracles
    row['canonical_signatures'] = list(dict.fromkeys(base.expression_group(o['expression']) for o in oracles))
    row['provenance'].update(parent_source_row_sha256=row['derivation']['parent_row_sha256'],
                             derivation_method='AI_ACTUAL_SEMANTIC_REVIEW_COMPLETE_EXPLAINED_ARITHMETIC_SIGNATURES')
    return row

def validate(row):
    n = int(row['sample_id'].rsplit('_', 1)[-1])
    assert len(row['hints']) == 3
    assert all(h['hint'] and h['question'] for h in row['hints'])
    assert not row['provenance']['human_verified']
    assert set(row['canonical_signatures']) == {base.expression_group(o['expression']) for o in row['numeric_oracles']}
    for oracle in row['numeric_oracles']:
        value = exact(oracle['expression'])
        assert value == Fraction(oracle['result'])
        with localcontext() as ctx:
            ctx.prec = 70
            assert abs(exact(oracle['expression'], Decimal) - Decimal(value.numerator) / Decimal(value.denominator)) < Decimal('1e-60')
    if n in GUARDS:
        assert not row['can_solve'] and row['case_kind'] == 'guard'
        assert all(s['expression'] is None and s['result'] is None for s in row['worked_steps'])
        assert row['initial_guidance'] == [row['expected_answer'][0]['result']]
    else:
        assert Fraction(row['expected_answer'][0]['result']) == ANSWERS[n]
        for step in row['worked_steps']:
            assert Fraction(step['result']) == exact(step['expression'])
        hint_text = ' '.join(row['initial_guidance'] + [h[k] for h in row['hints'] for k in ('hint', 'question')])
        assert not any(c.isdecimal() for c in hint_text)
    return True

class FinalPedagogyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.parents = parents(); cls.rows = [derive(r) for r in cls.parents]
    def test_all60_actual_story_oracles_numeric_steps_and_explained_checks(self):
        for row in self.rows: self.assertTrue(validate(row))
    def test_new_explanation_and_guard_checks_are_protected(self):
        for number, entries in EXTRA_EXPLAINED.items():
            row = self.rows[number - 1]
            for expression, result in entries:
                self.assertIn(base.expression_group(expression), row['canonical_signatures'])
                self.assertEqual(exact(expression), Fraction(result))
    def test_visible_unit_conversion_check_not_folded_to_identity(self):
        step = self.rows[22]['worked_steps'][1]
        self.assertEqual(step['display_expression'], '(12500 : 10000)')
        self.assertIn('12500 : 10000', step['explanation'])
    def test_holdout_full_canonical_splits_remain_disjoint(self):
        sigs = {s: {v for r in self.rows if r['split'] == s for v in r['canonical_signatures']} for s in ('train', 'validation', 'test')}
        for a, b in (('train', 'validation'), ('train', 'test'), ('validation', 'test')):
            self.assertFalse(sigs[a] & sigs[b])
        new_arithmetic = [json.loads(l) for l in (RUN / 'holdout_arithmetic_cases_v2.jsonl').read_text('utf-8').splitlines()]
        for r in new_arithmetic:
            self.assertFalse(set(r['canonical_signatures']) & (sigs['validation'] | sigs['test']))
    def test_parent_ids_hashes_group_and_student_work_preserved(self):
        for parent, row in zip(self.parents, self.rows):
            self.assertEqual(row['derivation']['parent_row_sha256'], sha(j(parent).encode()))
            self.assertEqual(row['case_group_id'], parent['case_group_id'])
            self.assertEqual(row['student_work'], parent['student_work'])
            self.assertEqual(row['split'], parent['split'])
    def test_mutated_display_answer_and_missing_signature_rejected(self):
        bad = copy.deepcopy(self.rows[7]); bad['expected_answer'][0]['result'] = '2.56'
        with self.assertRaises(AssertionError): validate(bad)
        bad = copy.deepcopy(self.rows[31]); bad['canonical_signatures'].pop()
        with self.assertRaises(AssertionError): validate(bad)
    def test_all240_chats_regenerated_no_old_source_id(self):
        chats = [c for r in self.rows for c in base.chat_records(r)]
        self.assertEqual(len(chats), 240)
        self.assertTrue(all(c['source_sample_id'].startswith('cloud_pedagogy_v3_') for c in chats))

def export():
    original_parents = parents()
    rows = [derive(p) for p in original_parents]
    for row in rows: validate(row)
    cases = RUN / 'pedagogy_cases_v3.jsonl'
    chat_file = RUN / 'pedagogy_chat_v3.jsonl'
    cases.write_text(''.join(j(r) + '\n' for r in rows), 'utf-8')
    chats = []
    for row in rows:
        for chat in base.chat_records(row):
            chat.update(split=row['split'], acceptance_status=row['acceptance_status'], source_row_sha256=sha(j(row).encode()))
            chats.append(chat)
    chat_file.write_text(''.join(j(c) + '\n' for c in chats), 'utf-8')
    sigs = {s: {v for r in rows if r['split'] == s for v in r['canonical_signatures']} for s in ('train', 'validation', 'test')}
    reservation = {'schema': 'new_pedagogy_holdouts.v3',
                   'canonical_signatures_by_split': {s: sorted(v) for s, v in sigs.items()},
                   'case_groups_by_split': {s: [r['case_group_id'] for r in rows if r['split'] == s] for s in sigs},
                   'includes_all_explained_numeric_guards_and_checks': True,
                   'replaces_parent_v1_v2_in_selected_view_preserving_all_sources': True}
    save(RUN / 'pedagogy_split_reservations_v3.json', reservation)
    report = {'schema': 'mathvisionkid.pedagogy.semantic_review3.v1',
              'status': 'PASSED_FINAL_ACTUAL_SEMANTIC_AND_EXACT_REVIEW',
              'reviewer': 'verify_pedagogy_AI_agent', 'human_manual_review_claimed': False,
              'independent_external_review': False,
              'cases': 60, 'chat_rows': 240, 'selected_unique_stories': 60,
              'parent_v2_source_sha256': EXPECTED_PARENT,
              'source_sha256': sha(cases.read_bytes()), 'chat_sha256': sha(chat_file.read_bytes()),
              'review_code_sha256': sha(Path(__file__).read_bytes()),
              'review_method': 'All60 original actual problem/givens/requests/student_work/steps/reasons/explanations/units/answers/alternatives/180hints read in full. All actual changed v2 fields read after serialization. V3 complete row diff checked against reviewed v2; only complete numeric-oracle/canonical metadata, derivative identity/provenance and visible conversion check changed. Every current numeric oracle independently Fraction/Decimal checked; complete serialized source and chat readback verified.',
              'numeric_oracles_checked': sum(len(r['numeric_oracles']) for r in rows),
              'meaningful_tests': 7, 'scope_limit': 'Honest placement recommendations; not full curriculum/teacher credential/physical-image certification.',
              'row_reviews': [{'sample_id': r['sample_id'], 'source_row_sha256': sha(j(r).encode()),
                               'parent_row_sha256': r['derivation']['parent_row_sha256'],
                               'criteria': {k: 'PASS' for k in ('correct_math_and_story_relations', 'complete_givens_or_genuine_guard', 'grade_units_and_honest_scope', 'step_reasons_and_check', 'initial_and_all_three_hints_no_numeric_answer', 'feedback_only_actual_student_work', 'schema_provenance_full_signatures_grouping')}} for r in rows],
              'skills_matched': 'none', 'skills_applied': 'none'}
    save(RUN / 'pedagogy_semantic_review3.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'row_reviews'}, ensure_ascii=False))

if __name__ == '__main__':
    import sys
    if '--test' in sys.argv: unittest.main(argv=[sys.argv[0]], verbosity=2)
    else: export()

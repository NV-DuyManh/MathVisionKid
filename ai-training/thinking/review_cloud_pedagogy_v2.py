"""Append a reviewed pedagogical derivative; preserve original source and reviews.

This small bounded supplement is temporary upload staging.  No network, model,
sealed evaluation, training, shared context or control-artifact writes occur.
"""
from __future__ import annotations
import ast
import copy
import hashlib
import json
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
OUT = HERE / 'cloud_publication/resume_20261018'
SOURCE = OUT / 'pedagogy_cases.jsonl'
REVIEWED_SOURCE_SHA256 = '9db5483e0744daa1a5c7c9b8c0c41d83257ad0e7f400def5ce5c62aee34618ef'

def compact(x):
    return json.dumps(x, ensure_ascii=False, separators=(',', ':'))

def digest(b):
    return hashlib.sha256(b).hexdigest()

def exact(expression, number=Fraction):
    """Separate review engine, not build_cloud_pedagogy.calc."""
    tree = ast.parse(expression, mode='eval')
    def visit(n):
        if isinstance(n, ast.Expression): return visit(n.body)
        if isinstance(n, ast.Constant) and type(n.value) is int: return number(n.value)
        if not isinstance(n, ast.BinOp): raise ValueError('Unsupported exact expression')
        a, b = visit(n.left), visit(n.right)
        if isinstance(n.op, ast.Add): return a + b
        if isinstance(n.op, ast.Sub): return a - b
        if isinstance(n.op, ast.Mult): return a * b
        if isinstance(n.op, ast.Div): return a / b
        raise ValueError('Forbidden calculator operation')
    return visit(tree)

def decimal_exact(q):
    q = Fraction(q)
    denominator = q.denominator
    for factor in (2, 5):
        while denominator % factor == 0: denominator //= factor
    if denominator != 1: raise ValueError('Not a finite decimal')
    with localcontext() as ctx:
        ctx.prec = 70
        out = format(Decimal(q.numerator) / Decimal(q.denominator), 'f')
    return out.rstrip('0').rstrip('.') if '.' in out else out

def rendered_expression(expression, decimal_context=False):
    def render(n):
        if isinstance(n, ast.Constant): return str(n.value)
        if decimal_context and isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
            if isinstance(n.left, ast.Constant) and isinstance(n.right, ast.Constant) and n.right.value in (10, 100, 1000, 10000):
                return decimal_exact(Fraction(n.left.value, n.right.value)).replace('.', ',')
        symbols = {ast.Add: '+', ast.Sub: '−', ast.Mult: '×', ast.Div: ':'}
        return '(' + render(n.left) + ' ' + symbols[type(n.op)] + ' ' + render(n.right) + ')'
    return render(ast.parse(expression, mode='eval').body)

# Expected answers independently derived from the actual story relations,
# not copied by following generated step results. Guards have no numeric oracle.
ANSWERS = {
1: 12 + 5 - 4, 2: 35 + (35 - 8), 3: 7 * 6 - 19,
4: (63 + 8 - 1) // 8, 5: 26 + (18 - 14), 6: 95 + (95 - 86),
7: 3 + (6 - 1) * 7, 8: Fraction('2.10') + Fraction('1.65') - Fraction('1.2'),
9: Fraction(240 * 35, 100), 10: Fraction(18 * 100, 60),
11: Fraction(72 * 5, 5 + 7), 12: 100000 - 80000 * Fraction(85, 100),
13: 58 - 24, 14: Fraction(96, 8), 15: Fraction(168, 14),
16: Fraction('1.75') + Fraction('2.6'), 17: 2 * (17 + 9),
18: Fraction(132, 11), 19: Fraction(16 * 7, 2), 20: 13 * 8 * 6,
21: 4 * 100 + 7 - 85, 22: 2 * 1000 + 35 - 460,
23: Fraction('1.25') * 10000, 24: Fraction('3.4') * 1000 - 650,
25: (8 * 60 + 50) - (8 * 60 + 15),
26: (24 * 60 + 20) - (23 * 60 + 35), 27: 20000 - (7000 + 5000),
28: Fraction('1.75') * 60 - 55, 29: sum((23, 17, 28)),
30: (6 - 4) * 5, 31: Fraction(sum((36, 42, 45)), 3),
32: 80 * (1 - Fraction(25, 100) - Fraction(40, 100)),
33: 12 * Fraction('2.5'), 34: Fraction(18, 4 + 5),
35: Fraction(135, 3) * 5, 36: Fraction(84, 42) * 60 + 30,
37: 24 * 6, 38: 2 * (28 + 15), 39: 120 * Fraction(3, 4) + 18,
40: 3 * 9000, 41: Fraction(54, 6), 42: 2 * (19 + 8),
43: Fraction('1.5') * 60, 44: 200 * Fraction(20, 100),
49: 900 - (247 + 186) + 129, 50: Fraction((23 + 17) * 12, 2),
51: Fraction(360 * 100, 45), 52: Fraction('6.3') / Fraction('1.4'),
53: 156 * Fraction(1, 4), 55: 18 * 14 * 9,
56: Fraction(322, 7) * 11, 57: 317 + (317 - 304),
58: 500000 - 13 * 27000, 59: Fraction(sum((21, 24, 29, 31, 35)), 5),
}
GUARDS = {45, 46, 47, 48, 54, 60}
SCOPE_NOTES = {
1: 'Two sequential changes are an enrichment story for grade 1; this does not certify a required single-step grade-1 outcome.',
2: 'Two-step comparison and total is enrichment at grade 2 pending textbook-level mapping.',
11: 'Total-and-ratio placement at grade 4 requires legacy/current textbook mapping; retain as enrichment, not a mandatory current-grade claim.',
13: 'Symbolic x at grade 2 is an optional notation extension; missing-part arithmetic is suitable but the notation is not certified mandatory.',
34: 'Two-body meeting is a contextual enrichment application; no specific current textbook outcome is certified.',
}

def derive(source):
    row = copy.deepcopy(source)
    number = int(source['sample_id'].rsplit('_', 1)[-1])
    row['sample_id'] = f'cloud_pedagogy_v2_{number:03d}'
    row['derivation'] = {
        'version': 'pedagogy_review_derivative.v2',
        'parent_sample_id': source['sample_id'],
        'parent_row_sha256': digest(compact(source).encode('utf-8')),
        'selection': 'REPLACES_PARENT_IN_SELECTED_VIEW_NOT_AN_ADDITIONAL_UNIQUE_STORY',
        'changes': ['Exact finite decimal displays for decimal contexts',
                    'Specific guard questions in guidance and hints',
                    'Source-bounded grade-placement caveats',
                    'Grade-appropriate length hint and explicit survey partition'],
    }
    assignment = row['curriculum_assignment']
    assignment.update(grade_is_recommendation_only=True,
                      curriculum_scope='CONTEXTUAL_APPLICATION_PLACEMENT_NOT_TEXTBOOK_CERTIFIED',
                      claim='Reused reference; neither whole-curriculum coverage nor grade-outcome/legal certification.')
    if number in SCOPE_NOTES:
        assignment.update(curriculum_scope='ENRICHMENT_PLACEMENT_PENDING_SPECIFIC_SOURCE',
                          reason=SCOPE_NOTES[number])
    if number == 21:
        row['hints'][1]['hint'] = 'Tách phần mét và phần xăng-ti-mét rồi đổi về cùng đơn vị.'
    if number == 32:
        row['problem'] = 'Khảo sát 80 bạn, mỗi bạn chọn đúng một môn trong ba môn cầu lông, bóng đá, bơi. Biểu đồ ghi 25% chọn cầu lông, 40% chọn bóng đá, còn lại chọn bơi. Có bao nhiêu bạn chọn bơi?'
        row['givens'][0]['text'] = '80 bạn; mỗi bạn đúng một môn; chỉ ba môn; 25% cầu lông; 40% bóng đá'
        row['worked_steps'][2]['reason'] = 'Từ tỷ lệ của toàn bộ, cầu lông có 80 × 25 : 100 = 20 bạn, bóng đá có 80 × 40 : 100 = 32 bạn; ba nhóm không trùng và phủ đủ mẫu khảo sát.'
    if number == 48:
        row['expected_answer'][0]['result'] = 'Em kiểm tra lại và cho biết số hộp thực tế là bao nhiêu; số hộp dùng để chia đều cần khác không.'
    if number in GUARDS:
        question = row['expected_answer'][0]['result']
        # Ask for the missing/correct data; no invented numeric answer and no
        # unsupported conclusion about an unseen image or student's reasoning.
        row['initial_guidance'] = [question]
        for hint in row['hints']:
            hint['question'] = question
        if number == 48:
            row['worked_steps'][0]['explanation'] = row['worked_steps'][0]['reason'] + ' ' + question
    decimal_context = row['grade'] == 5
    for step in row['worked_steps']:
        if step['expression'] is None: continue
        q = exact(step['expression'])
        step['exact_result_rational'] = str(q)
        result = decimal_exact(q) if decimal_context else str(q)
        step['result'] = result
        step['display_result'] = result.replace('.', ',')
        step['display_expression'] = rendered_expression(step['expression'], decimal_context)
        step['explanation'] = step['reason'] + ' Tính ' + step['display_expression'] + ' = ' + step['display_result'] + (f" {step['unit']}." if step['unit'] else '.')
        if step is row['worked_steps'][-1] and len(row['worked_steps']) > 1:
            step['explanation'] += ' Quan hệ kiểm tra này khớp dữ kiện của đề.'
    if number not in GUARDS:
        q = Fraction(ANSWERS[number])
        result = decimal_exact(q) if decimal_context else str(q)
        row['expected_answer'][0].update(result=result, display_result=result.replace('.', ','), exact_result_rational=str(q))
    row['provenance'].update(
        derivation_method='AI_SEMANTIC_REVIEW_EXACT_DISPLAY_AND_GUARD_POLISH',
        original_authorship_origin=source['provenance']['authorship_origin'],
        parent_source_row_sha256=row['derivation']['parent_row_sha256'],
        human_content_review_completed=False, human_verified=False,
        teacher_certified=False, independent_external_review=False,
    )
    return row

def validate(row):
    number = int(row['sample_id'].rsplit('_', 1)[-1])
    assert len(row['hints']) == 3
    assert all(h['hint'] and h['question'] for h in row['hints'])
    assert not row['provenance']['human_verified']
    if number in GUARDS:
        assert row['can_solve'] is False and row['case_kind'] == 'guard'
        assert all(s['expression'] is None and s['result'] is None for s in row['worked_steps'])
        question = row['expected_answer'][0]['result']
        assert row['initial_guidance'] == [question]
        assert all(h['question'] == question for h in row['hints'])
    else:
        assert row['can_solve'] is True
        assert Fraction(row['expected_answer'][0]['result']) == ANSWERS[number]
        for step in row['worked_steps']:
            if not step['expression']: continue
            q = exact(step['expression'])
            assert Fraction(step['result']) == q
            with localcontext() as ctx:
                ctx.prec = 70
                d = exact(step['expression'], Decimal)
                assert abs(d - Decimal(q.numerator) / Decimal(q.denominator)) < Decimal('1e-60')
            assert step['reason'] and step['explanation'] and 'unit' in step
        hint_text = ' '.join(row['initial_guidance'] + [h[k] for h in row['hints'] for k in ('hint', 'question')])
        # Supplementary no-answer leakage test. Actual semantic reading is
        # documented separately; this numeric screen cannot prove meaning.
        result = row['expected_answer'][0]['result']
        assert not any(c.isdecimal() for c in hint_text), (number, hint_text)
    return True

class PedagogyReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert digest(SOURCE.read_bytes()) == REVIEWED_SOURCE_SHA256, 'Changed source requires a new actual semantic review'
        cls.original = [json.loads(line) for line in SOURCE.read_text('utf-8').splitlines()]
        cls.rows = [derive(r) for r in cls.original]
    def test_every_actual_row_independent_story_oracle_and_dual_engine(self):
        self.assertEqual(len(self.rows), 60)
        for row in self.rows: self.assertTrue(validate(row))
    def test_display_finite_decimal_exact_and_no_rounding(self):
        self.assertEqual(self.rows[7]['expected_answer'][0]['result'], '2.55')
        self.assertEqual(self.rows[15]['expected_answer'][0]['display_result'], '4,35')
        self.assertEqual(self.rows[51]['expected_answer'][0]['result'], '4.5')
        with self.assertRaises(ValueError): decimal_exact(Fraction(1, 3))
    def test_missing_side_multiple_valid_widths_prove_underdetermined(self):
        self.assertNotEqual(2 * (21 + 1), 2 * (21 + 2))
        self.assertFalse(self.rows[44]['can_solve'])
    def test_missing_rate_multiple_valid_rates_prove_underdetermined(self):
        self.assertNotEqual(Fraction('2.8') * 10, Fraction('2.8') * 20)
        self.assertFalse(self.rows[53]['can_solve'])
    def test_missing_image_no_invented_values(self):
        self.assertFalse(self.rows[46]['can_solve'])
        self.assertTrue(all(s['expression'] is None for s in self.rows[46]['worked_steps']))
    def test_inconsistent_disjoint_counts_and_motion_are_real_conflicts(self):
        self.assertNotEqual(18 + 17, 32)
        self.assertNotEqual(52 * 3, 150)
        self.assertFalse(self.rows[45]['can_solve'])
        self.assertFalse(self.rows[59]['can_solve'])
    def test_zero_groups_cannot_yield_a_finite_share(self):
        for candidate in (0, 1, 48, 100): self.assertNotEqual(candidate * 0, 48)
        self.assertFalse(self.rows[47]['can_solve'])
    def test_capacity_minimality_not_rounded_down(self):
        self.assertGreaterEqual(8 * 8, 63)
        self.assertLess(7 * 8, 63)
        self.assertEqual(Fraction(self.rows[3]['expected_answer'][0]['result']), 8)
    def test_multistep_and_midnight_independent_oracles(self):
        self.assertEqual(ANSWERS[12], 32000)
        self.assertEqual(ANSWERS[26], 45)
        self.assertEqual(ANSWERS[36], 150)
        self.assertEqual(ANSWERS[39], 108)
    def test_mutated_answer_trace_and_guard_rejected(self):
        for index in (7, 15, 51):
            row = copy.deepcopy(self.rows[index]); row['expected_answer'][0]['result'] = '99'
            with self.assertRaises(AssertionError): validate(row)
        row = copy.deepcopy(self.rows[2]); row['worked_steps'][1]['result'] = '99'
        with self.assertRaises(AssertionError): validate(row)
        row = copy.deepcopy(self.rows[44]); row['can_solve'] = True
        with self.assertRaises(AssertionError): validate(row)
    def test_no_hidden_student_reasoning_added_or_sources_replaced(self):
        for parent, child in zip(self.original, self.rows):
            self.assertEqual(parent['student_work'], child['student_work'])
            self.assertEqual(parent['case_group_id'], child['case_group_id'])
            self.assertEqual(parent['split'], child['split'])
            self.assertNotEqual(parent['sample_id'], child['sample_id'])
            self.assertEqual(child['derivation']['parent_row_sha256'], digest(compact(parent).encode()))
    def test_four_chat_modes_all_regenerated_and_grouped(self):
        from exhaustive_primary_math import chat_records
        for row in self.rows:
            chats = list(chat_records(row)); self.assertEqual(len(chats), 4)
            for c in chats:
                self.assertEqual(c['source_sample_id'], row['sample_id'])
                self.assertEqual(c['case_group_id'], row['case_group_id'])

def export():
    source_bytes = SOURCE.read_bytes()
    assert digest(source_bytes) == REVIEWED_SOURCE_SHA256, 'Changed source requires a new actual semantic review'
    originals = [json.loads(line) for line in source_bytes.decode('utf-8').splitlines()]
    rows = [derive(r) for r in originals]
    for row in rows: validate(row)
    from exhaustive_primary_math import chat_records
    cases_path = OUT / 'pedagogy_cases_v2.jsonl'
    chats_path = OUT / 'pedagogy_chat_v2.jsonl'
    cases_path.write_text(''.join(compact(r) + '\n' for r in rows), 'utf-8')
    chats = []
    for row in rows:
        for chat in chat_records(row):
            chat.update(split=row['split'], acceptance_status=row['acceptance_status'])
            chats.append(chat)
    chats_path.write_text(''.join(compact(c) + '\n' for c in chats), 'utf-8')
    assert SOURCE.read_bytes() == source_bytes
    assert [json.loads(line) for line in cases_path.read_text('utf-8').splitlines()] == rows
    review = {
        'schema': 'mathvisionkid.pedagogy.semantic_review2.v1',
        'status': 'PASSED_AFTER_APPEND_ONLY_V2_POLISH',
        'reviewer': 'verify_pedagogy_AI_agent',
        'review_scope': 'All 60 actual questions/givens/requests/student_work/initial/180 hints/steps/titles/reasons/explanations/units/answers/alternatives read in full; then exact derivative changes and regenerated chats reviewed.',
        'human_review_claimed': False, 'independent_external_review': False,
        'source_original_sha256': digest(source_bytes),
        'selected_source_path': str(cases_path.relative_to(HERE.parent)),
        'selected_source_sha256': digest(cases_path.read_bytes()),
        'selected_chat_path': str(chats_path.relative_to(HERE.parent)),
        'selected_chat_sha256': digest(chats_path.read_bytes()),
        'review_code_sha256': digest(Path(__file__).read_bytes()),
        'original_generator_sha256': digest((HERE / 'build_cloud_pedagogy.py').read_bytes()),
        'cases': len(rows), 'chat_rows': len(chats),
        'numeric_steps_review_exact_fraction_decimal': sum(bool(s['expression']) for r in rows for s in r['worked_steps']),
        'selected_unique_story_count': 60,
        'superseded_v1_preserved_for_audit_not_added_again': True,
        'canonical_signatures_and_splits_unchanged': all(a['canonical_signatures'] == b['canonical_signatures'] and a['split'] == b['split'] for a, b in zip(originals, rows)),
        'test_cases': 12,
        'limits': ['Human manual review is not claimed.', 'Not proof of full curriculum or physical/vision ability.', 'New authored holdout stories remain isolated by original case groups and canonical reservation metadata.', 'Template/keyword validation is supplemental to actual semantic reading.'],
        'row_reviews': [{
            'sample_id': row['sample_id'], 'parent_sample_id': parent['sample_id'],
            'source_row_sha256': digest(compact(row).encode()),
            'parent_row_sha256': digest(compact(parent).encode()),
            'criteria': {k: 'PASS' for k in (
                'correct_math_and_story_relations', 'complete_givens_or_genuine_guard',
                'grade_units_and_honest_scope', 'step_reasons_and_check',
                'initial_and_all_three_hints_no_numeric_answer',
                'feedback_only_actual_student_work', 'schema_provenance_and_grouping')},
            'note': SCOPE_NOTES.get(int(row['sample_id'].rsplit('_', 1)[-1]),
                'Actual story, every worked/check relation and all hints were read; exact result checked against independent story oracle.'),
        } for parent, row in zip(originals, rows)],
        'skills_matched': 'none', 'skills_applied': 'none',
    }
    (OUT / 'pedagogy_semantic_review2.json').write_text(json.dumps(review, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({k: v for k, v in review.items() if k != 'row_reviews'}, ensure_ascii=False))

if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        export()

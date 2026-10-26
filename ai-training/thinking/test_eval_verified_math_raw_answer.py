"""Adversarial tests for the post-hoc raw-number diagnostic, with no GPU calls."""
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest
import unicodedata

from eval_verified_math_raw_answer import (
    aggregate, digest, inspect_planner_baseline, messages, numeric_answer,
    parse_answer, recompute_record, score, unit,
)


class TokenizerFixture:
    eos_token_id = 0

    def decode(self, ids, **kwargs):
        return ''.join(chr(value) for value in ids if value != self.eos_token_id)


class RawAnswerTests(unittest.TestCase):
    def row(self, status='solve', answer='3/10', output_unit='cm²'):
        return {'sample_id': 'raw_fixture', 'grade': 5, 'topic': 'fixture_math',
                'problem': 'Tính 0,1 cộng 0,2.',
                'facts': [{'id': 'f0', 'value': '1/10'}, {'id': 'f1', 'value': '1/5'}],
                'target': {'status': status, 'expr': 'f0+f1' if status == 'solve' else None,
                           'unit': output_unit if status == 'solve' else None},
                'oracle_answer': answer if status == 'solve' else None,
                'source_solution': 'SECRET SOURCE SOLUTION', 'explanation': 'SECRET EXPLANATION'}

    def prediction(self, row, text):
        ids = [ord(character) for character in text] + [0]
        return {'sample_id': row['sample_id'], 'grade': row['grade'], 'topic': row['topic'],
                'reference_status': row['target']['status'], 'prediction': text,
                'generated_ids': ids, 'generated_ids_sha256': digest(ids), 'generated_tokens': len(ids),
                'scores': score(row, text)}

    def test_exact_numbers_and_explicit_decimal_marks(self):
        for text, expected in (('0,3', Fraction(3, 10)), ('0.3', Fraction(3, 10)),
                               (' 3 / 10 ', Fraction(3, 10)), ('-1/2', Fraction(-1, 2)),
                               ('+2', Fraction(2)), ('1,000', Fraction(1)),
                               ('1.234', Fraction(617, 500)), ('0,000000000001', Fraction(1, 10**12))):
            self.assertEqual(numeric_answer(text), expected)
        # A separator is explicitly a decimal mark in this protocol. Never
        # infer that 1.234 means one thousand two hundred thirty-four.
        for text in ('1,234.5', '1.234.567', '1 000', '2e3', '3/0', '3/-2',
                     '00,5', '3 + 4', 'f0+f1', 'NaN', 'Infinity', '0x10', '1/1000000000001'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                numeric_answer(text)
        with self.assertRaises(ValueError):
            numeric_answer(0.3)

    def test_no_facts_target_solution_or_calculator_in_prompt(self):
        row = self.row()
        payload = json.loads(messages(row)[1]['content'])
        self.assertEqual(payload, {'grade': row['grade'], 'question': row['problem']})
        for key in ('facts', 'expr', 'oracle_answer', 'target', 'source_solution', 'explanation'):
            self.assertNotIn(key, payload)
        self.assertNotIn('SECRET', json.dumps(messages(row)))

    def test_strict_final_json_no_conflicting_or_duplicate_answers(self):
        answer = '{"answer":"3/10","unit":"cm²"}'
        self.assertEqual(parse_answer(answer)['answer'], '3/10')
        self.assertEqual(parse_answer('<think>work</think>' + answer)['answer'], '3/10')
        self.assertEqual(parse_answer('```json\n' + answer + '\n```')['answer'], '3/10')
        for text in (answer + ' The actual answer is 9.', 'The answer is 9. ' + answer,
                     answer + answer, '```json\n' + answer, answer + '\n```',
                     '<think>unfinished ' + answer, '</think>' + answer,
                     '9 <think>work</think>' + answer, '<think>x</think><think>y</think>' + answer,
                     '{"answer":"0.3","answer":"9","unit":"cm²"}',
                     '{"answer":0.3,"unit":"cm²"}', '{"answer":true,"unit":"cm²"}',
                     '{"answer":"0.3","unit":"cm²","steps":[]}',
                     '{"answer":null,"unit":"cm²"}', '["0.3"]', 'null'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_answer(text)
        with self.assertRaises(ValueError):
            parse_answer(answer, truncated=True)

    def test_unit_equivalence_is_small_and_numeric_correctness_separate(self):
        self.assertEqual(unit(' cm^2 '), 'cm²')
        self.assertEqual(unit('m^3'), 'm³')
        self.assertEqual(unit(unicodedata.normalize('NFD', 'quả')), 'quả')
        correct = score(self.row(), '{"answer":"0,3","unit":"cm^2"}')
        self.assertTrue(correct['numeric_answer_correct'])
        self.assertTrue(correct['correct'])
        wrong_unit = score(self.row(), '{"answer":"0.3","unit":"cm"}')
        self.assertTrue(wrong_unit['numeric_answer_correct'])
        self.assertFalse(wrong_unit['correct'])
        wrong_number = score(self.row(), '{"answer":"3","unit":"cm²"}')
        self.assertFalse(wrong_number['correct'])
        self.assertTrue(wrong_number['wrong_completed_answer'])
        rounded = score(self.row(answer='1/3'), '{"answer":"0,333333","unit":"cm²"}')
        self.assertFalse(rounded['numeric_answer_correct'])

    def test_guard_null_and_false_answer_coverage_are_separate(self):
        solved, guard = self.row(), self.row('clarify')
        no_answer = '{"answer":null,"unit":null}'
        self.assertFalse(score(solved, no_answer)['correct'])
        self.assertTrue(score(guard, no_answer)['guard_correct'])
        correct = self.prediction(solved, '{"answer":"3/10","unit":"cm²"}')
        false_guard = self.prediction(guard, '{"answer":"3/10","unit":"cm²"}')
        report = aggregate([correct, false_guard])
        self.assertEqual(report['solvable_coverage'], 1)
        self.assertEqual(report['solvable_raw_answer_accuracy'], 1)
        self.assertEqual(report['guard_false_answers'], 1)
        self.assertEqual(report['guard_correct'], 0)
        self.assertIsNone(aggregate([])['solvable_coverage'])

    def test_planner_and_fact_refs_are_not_accepted_as_numeric_answers(self):
        row = self.row()
        wrong_protocol = score(row, '{"status":"solve","expr":"f0+f1","unit":"cm²"}')
        self.assertTrue(wrong_protocol['planner_schema_emitted'])
        self.assertTrue(wrong_protocol['fact_reference_emitted'])
        self.assertFalse(wrong_protocol['answered'])
        raw_fact = score(row, '{"answer":"f0","unit":"cm²"}')
        self.assertTrue(raw_fact['fact_reference_emitted'])
        self.assertTrue(raw_fact['invalid_numeric_answer'])
        self.assertFalse(raw_fact['correct'])

    def test_token_eos_prediction_hash_and_cached_score_tampering(self):
        row = self.row()
        record = self.prediction(row, '{"answer":"3/10","unit":"cm²"}')
        self.assertTrue(recompute_record(record, row, TokenizerFixture(), 128)['scores']['correct'])
        for field, replacement in (('prediction', '{"answer":"99","unit":"cm²"}'),
                                   ('generated_ids_sha256', 'forged'), ('generated_tokens', 2)):
            damaged = dict(record, **{field: replacement})
            with self.subTest(field=field), self.assertRaises(ValueError):
                recompute_record(damaged, row, TokenizerFixture(), 128)
        damaged = dict(record, scores=dict(record['scores'], correct=False))
        with self.assertRaises(ValueError):
            recompute_record(damaged, row, TokenizerFixture(), 128)
        damaged = dict(record, generated_ids=record['generated_ids'][:-1],
                       generated_tokens=record['generated_tokens'] - 1)
        damaged['generated_ids_sha256'] = digest(damaged['generated_ids'])
        with self.assertRaises(ValueError):
            recompute_record(damaged, row, TokenizerFixture(), 128)

    def test_planner_literal_protocol_inspection_does_not_call_it_math_wrong(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'baseline_val.jsonl'
            rows = [{'prediction': text, 'scores': {'truncated': False}} for text in (
                '{"status":"solve","expr":"4+6","unit":"quả"}',
                '{"status":"solve","expr":"f0+f1","unit":"quả"}',
                '{"status":"clarify","expr":null,"unit":null}',
            )]
            path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
            report = inspect_planner_baseline(path)
            self.assertEqual(report['samples'], 3)
            self.assertEqual(report['expr_without_fact_refs'], 1)
            self.assertEqual(report['numeric_literal_only_expr'], 1)
            self.assertEqual(report['expr_with_fact_refs'], 1)


if __name__ == '__main__':
    unittest.main()

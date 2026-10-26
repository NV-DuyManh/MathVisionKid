"""Regression checks for plan supervision, strict parsing, and honest metrics."""
import json
from pathlib import Path
import tempfile
import unittest

from audit_verified_math_v2 import audit_predictions, summaries
from verified_math_data_v2 import build, prompt
from verified_math_training_v2 import aggregate, collate, parse_output, score, serialize


class MockTokenizer:
    eos_token = '[EOS]'
    eos_token_id = 0

    def apply_chat_template(self, messages, **kwargs):
        if kwargs.get('enable_thinking') is not False:
            raise AssertionError('Training and inference must explicitly disable thinking')
        if kwargs.get('add_generation_prompt') is not True:
            raise AssertionError('Missing assistant generation prefix')
        return '|'.join(message['role'] + ':' + message['content'] for message in messages) + '|assistant:'

    def encode(self, text, **kwargs):
        if kwargs.get('add_special_tokens') is not False:
            raise AssertionError('Special tokens must not be duplicated')
        return [ord(char) for char in text]

    def decode(self, ids, **kwargs):
        return ''.join(chr(value) for value in ids if value != self.eos_token_id)


class VerifiedMathTrainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated = build()

    def row(self, status='solve', unit='quả'):
        return {
            'sample_id': 'review_fixture', 'grade': 1,
            'problem': 'Lan có 4 quả, nhận thêm 6 quả. Có tất cả bao nhiêu quả?',
            'facts': [{'id': 'f0', 'value': '4', 'unit': 'quả'},
                      {'id': 'f1', 'value': '6', 'unit': 'quả'}],
            'target': {'status': status, 'expr': 'f0+f1' if status == 'solve' else None,
                       'unit': unit if status == 'solve' else None},
            'expected_answer': '10' if status == 'solve' else None,
            'oracle_answer': '10' if status == 'solve' else None,
        }

    def test_generated_gold_plans_score_correct_with_actual_row_schema(self):
        # Catch a disconnected generator/trainer contract, not a hand-crafted
        # row that happens to contain the trainer's preferred oracle key.
        for row in self.generated:
            scores = score(row, json.dumps(row['target']))
            self.assertTrue(scores['math_correct'], row['sample_id'])
            self.assertTrue(scores['plan_exact'], row['sample_id'])

    def test_masking_prefix_eos_padding_and_no_target_leak(self):
        row = self.row()
        row['source_solution'] = 'SECRET IMPORTED SOLUTION'
        tokenizer = MockTokenizer()
        item = serialize(row, tokenizer, max_length=5000)
        boundary = next(index for index, label in enumerate(item['labels']) if label != -100)
        self.assertTrue(all(label == -100 for label in item['labels'][:boundary]))
        completion = ''.join(chr(label) for label in item['labels'][boundary:])
        self.assertEqual(completion, json.dumps(row['target'], ensure_ascii=False, separators=(',', ':')) + '[EOS]')
        prefix = ''.join(chr(token) for token in item['input_ids'][:boundary])
        self.assertNotIn('SECRET IMPORTED SOLUTION', prefix)
        payload = json.loads(prompt(row))
        self.assertEqual(set(payload), {'grade', 'problem', 'facts'})
        self.assertNotIn('target', payload)
        self.assertNotIn('expected_answer', payload)
        self.assertNotIn('oracle_answer', payload)
        short = {'input_ids': [3], 'attention_mask': [1], 'labels': [3]}
        padded = collate([item, short], pad=0)
        self.assertEqual(padded['labels'][1][1:], [-100] * (len(item['labels']) - 1))
        self.assertEqual(padded['attention_mask'][1][1:], [0] * (len(item['labels']) - 1))
        self.assertTrue(all(value == 0 for value in padded['input_ids'][1][1:]))
        with self.assertRaises((ValueError, AssertionError)):
            serialize(row, tokenizer, max_length=10)

    def test_strict_single_json_and_complete_thought(self):
        target = json.dumps(self.row()['target'])
        self.assertEqual(parse_output(target), self.row()['target'])
        self.assertEqual(parse_output('<think>working</think>' + target), self.row()['target'])
        self.assertEqual(parse_output('```json\n' + target + '\n```'), self.row()['target'])
        invalid = (
            target + ' Nhưng đáp án cuối cùng là 999 quả.',
            'Đáp án là 999 quả. ' + target,
            target + ' null',
            target + target,
            '<think>unfinished ' + target,
            '</think>' + target,
            '<think>one</think><think>two</think>' + target,
            target + '<think>unfinished',
            '999 is the answer. <think>working</think>' + target,
            '```json\n' + target,
            target + '\n```',
            '</think><think>working' + target,
            '{"status":"solve","status":"clarify","expr":"f0+f1","unit":"quả"}',
            '{"status":"solve","expr":"f0+f1","unit":"quả","answer":10}',
            '{"status":"solve","expr":null,"unit":"quả"}',
            '{"status":"clarify","expr":"f0+f1","unit":null}',
            '[]', 'null',
        )
        for text in invalid:
            with self.subTest(text=text), self.assertRaises((ValueError, TypeError)):
                parse_output(text)
        with self.assertRaises(ValueError):
            parse_output(target, truncated=True)

    def test_equivalent_answer_is_not_a_semantic_plan_certificate(self):
        row = self.row()
        row['facts'][0]['value'] = '2'
        row['facts'][1]['value'] = '2'
        row['expected_answer'] = '4'
        row['oracle_answer'] = '4'
        accidental = score(row, '{"status":"solve","expr":"f0*f1","unit":"quả"}')
        self.assertTrue(accidental['answer_correct'])
        self.assertFalse(accidental['plan_exact'])
        equivalent = score(self.row(), '{"status":"solve","expr":"f1+f0","unit":"quả"}')
        self.assertTrue(equivalent['answer_correct'])
        self.assertFalse(equivalent['plan_exact'])

    def test_wrong_units_unknown_facts_and_unsafe_expressions_fail(self):
        row = self.row()
        for expression in ('f0-f1', 'f999+f0', '999', '__import__("os")',
                           'f0.__class__', 'f0**100', 'f0/0', '[f0]'):
            with self.subTest(expression=expression):
                scores = score(row, json.dumps({'status': 'solve', 'expr': expression, 'unit': 'quả'}))
                self.assertFalse(scores['math_correct'])
                self.assertTrue(scores['wrong_answer'])
        wrong_unit = score(row, '{"status":"solve","expr":"f0+f1","unit":"kg"}')
        self.assertTrue(wrong_unit['answer_correct'])
        self.assertFalse(wrong_unit['unit_correct'])
        self.assertFalse(wrong_unit['math_correct'])

    def test_false_guard_solve_does_not_inflate_solvable_coverage(self):
        solved, guard = self.row(), self.row('clarify')
        correct = score(solved, json.dumps(solved['target']))
        false_solve = score(guard, json.dumps(solved['target']))
        self.assertTrue(false_solve['wrong_answer'])
        report = aggregate([
            {'reference_status': 'solve', 'scores': correct},
            {'reference_status': 'clarify', 'scores': false_solve},
        ])
        self.assertEqual(report['solvable_samples'], 1)
        self.assertEqual(report['solvable_correct'], 1)
        self.assertEqual(report['coverage'], 1)
        self.assertEqual(report['guard_correct'], 0)
        self.assertEqual(report['wrong_answers'], 1)
        self.assertEqual(report['math_accuracy'], 0.5)

    def test_missing_answers_and_wrong_guards_stay_errors(self):
        row = self.row()
        scores = score(row, '{"status":"clarify","expr":null,"unit":null}')
        self.assertFalse(scores['math_correct'])
        self.assertFalse(scores['answered'])
        self.assertFalse(scores['wrong_answer'])
        guard = self.row('clarify')
        scores = score(guard, '{"status":"unsupported","expr":null,"unit":null}')
        self.assertFalse(scores['math_correct'])
        self.assertFalse(scores['status_correct'])
        report = aggregate([])
        self.assertIsNone(report['math_accuracy'])
        self.assertIsNone(report['coverage'])

    def test_auditor_recomputes_tokens_and_rejects_cached_score_tampering(self):
        row = self.row()
        text = json.dumps(row['target'])
        tokenizer = MockTokenizer()
        token_ids = [ord(char) for char in text] + [tokenizer.eos_token_id]
        prediction = {
            'sample_id': row['sample_id'], 'topic': 'public_source', 'grade': row['grade'],
            'reference_status': 'solve', 'prediction': text, 'generated_ids': token_ids,
            'generated_tokens': len(token_ids), 'scores': score(row, text),
        }
        config = {'max_new_tokens': 128, 'eval_batch_size': 8}
        metadata = {'key': 'fixture_base', 'ids': [row['sample_id']], 'greedy': True,
                    'enable_thinking': False, 'max_new_tokens': 128, 'batch_size': 8,
                    'eos_token_id': tokenizer.eos_token_id}
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            (run / 'fixture.metadata.json').write_text(json.dumps(metadata), encoding='utf-8')
            (run / 'fixture.summary.json').write_text(json.dumps(summaries([prediction])), encoding='utf-8')
            output = run / 'fixture.jsonl'
            output.write_text(json.dumps(prediction) + '\n', encoding='utf-8')
            verified = audit_predictions(run, 'fixture', [row], 'fixture_base', tokenizer, config)
            self.assertEqual(verified['solvable_correct'], 1)
            prediction['scores']['answer_correct'] = False
            output.write_text(json.dumps(prediction) + '\n', encoding='utf-8')
            with self.assertRaises(AssertionError):
                audit_predictions(run, 'fixture', [row], 'fixture_base', tokenizer, config)
            prediction['scores'] = score(row, text)
            prediction['generated_ids'][0] = ord('[')
            output.write_text(json.dumps(prediction) + '\n', encoding='utf-8')
            with self.assertRaises(AssertionError):
                audit_predictions(run, 'fixture', [row], 'fixture_base', tokenizer, config)


if __name__ == '__main__':
    unittest.main()

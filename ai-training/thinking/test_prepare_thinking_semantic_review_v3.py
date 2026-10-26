import copy
import json
from pathlib import Path
import unittest

import prepare_thinking_semantic_review_v3 as review
import train_teacher_math_v3 as trainer


class TinyTokenizer:
    eos_token_id = 9

    def __init__(self, text):
        self.text = text

    def decode(self, ids, skip_special_tokens=True):
        return self.text if ids == [1, 9] else 'tampered text'

    def apply_chat_template(self, messages, **kwargs):
        return 'rendered input<think>\n'


class ReviewPacketTests(unittest.TestCase):
    def setUp(self):
        self.row = {'sample_id': 'sample', 'grade': 1, 'topic': 'add_join',
                    'mode': 'hint', 'problem': 'Lan có 3 viên bi và thêm 2 viên. Có mấy viên?',
                    'target': {'status': 'solve', 'steps': [], 'answer': None, 'unit': None,
                               'hint': 'Khi có thêm, em dùng phép tính nào để tìm tất cả?'}}
        final = json.dumps(self.row['target'], ensure_ascii=False)
        self.text = 'SECRET HIDDEN THOUGHT\n</think>\n' + final
        self.tokenizer = TinyTokenizer(self.text)
        self.metadata = {'max_new_tokens': 2048, 'enable_thinking': True}
        self.record = {'sample_id': 'sample', 'grade': 1, 'topic': 'add_join',
                       'answer_kind': 'numeric', 'mode': 'hint', 'reference_status': 'solve',
                       'prediction': self.text, 'generated_ids': [1, 9], 'generated_tokens': 2,
                       'eos_observed': True, 'thought_prefix_open': True,
                       'scores': trainer.score(self.row, self.text, False, thought_prefix_open=True)}

    def test_valid_tokens_and_scores_recompute(self):
        review.check_records([self.row], [self.record], self.metadata, self.tokenizer)

    def test_partial_prediction_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'count / IDs'):
            review.check_records([self.row], [], self.metadata, self.tokenizer)

    def test_duplicate_prediction_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'count / IDs'):
            review.check_records([self.row, self.row], [self.record, self.record], self.metadata, self.tokenizer)

    def test_wrong_id_and_topic_association_rejected(self):
        wrong = copy.deepcopy(self.record)
        wrong['sample_id'] = 'other'
        with self.assertRaisesRegex(ValueError, 'count / IDs'):
            review.check_records([self.row], [wrong], self.metadata, self.tokenizer)
        wrong = copy.deepcopy(self.record)
        wrong['topic'] = 'invented_topic'
        with self.assertRaisesRegex(ValueError, 'topic / answer kind'):
            review.check_records([self.row], [wrong], self.metadata, self.tokenizer)

    def test_actual_token_decode_tampering_rejected(self):
        wrong = copy.deepcopy(self.record)
        wrong['generated_ids'] = [2, 9]
        with self.assertRaisesRegex(ValueError, 'reconstruct'):
            review.check_records([self.row], [wrong], self.metadata, self.tokenizer)

    def test_fabricated_scores_rejected(self):
        wrong = copy.deepcopy(self.record)
        wrong['scores']['hint_safe'] = not wrong['scores']['hint_safe']
        with self.assertRaisesRegex(ValueError, 'scores differ'):
            review.check_records([self.row], [wrong], self.metadata, self.tokenizer)

    def test_boolean_token_id_and_integer_score_rejected(self):
        wrong = copy.deepcopy(self.record)
        wrong['generated_ids'][0] = True
        with self.assertRaisesRegex(ValueError, 'not booleans'):
            review.check_records([self.row], [wrong], self.metadata, self.tokenizer)
        wrong = copy.deepcopy(self.record)
        wrong['scores']['hint_safe'] = 1
        with self.assertRaisesRegex(ValueError, 'boolean observations'):
            review.check_records([self.row], [wrong], self.metadata, self.tokenizer)

    def test_hidden_thinking_never_enters_packet(self):
        packet = review.make_packet(self.row, self.record, 'candidate', None)
        self.assertNotIn('SECRET HIDDEN THOUGHT', json.dumps(packet))
        self.assertEqual(packet['visible_output']['strict_parsed'], self.row['target'])
        self.assertIsNone(packet['review']['semantic_correct'])
        self.assertFalse(packet['automatic_observations']['certifies_explanation_or_hint_meaning'])

    def test_open_thought_cannot_be_exposed(self):
        record = copy.deepcopy(self.record)
        record['prediction'] = 'SECRET HIDDEN THOUGHT without closing tag'
        visible = review.visible_output(record)
        self.assertIsNone(visible['text'])
        self.assertEqual(visible['parse_error'], 'no_closed_visible_answer')

    def test_invalid_schema_still_reviews_only_visible_tail(self):
        record = copy.deepcopy(self.record)
        record['prediction'] = 'SECRET HIDDEN THOUGHT</think>{"answer": 5}'
        visible = review.visible_output(record)
        self.assertEqual(visible['text'], '{"answer": 5}')
        self.assertIsNone(visible['strict_parsed'])
        self.assertNotIn('SECRET', json.dumps(visible))

    def test_refuses_incomplete_state_before_other_checks(self):
        with self.assertRaisesRegex(ValueError, 'not complete'):
            review.check_protocol({}, Path('missing.jsonl'), {'phase': 'candidate_full_thinking_validation'})

    def test_inference_metadata_uses_actual_parent_inputs_and_mode(self):
        protocol = {'model_id': trainer.MODEL, 'revision': trainer.REVISION,
                    'adapter_sha256': 'a' * 64, 'seed': 20261013, 'max_new_tokens': 2048,
                    'batch_size': 4, 'temperature': .6, 'top_p': .95, 'top_k': 20}
        import hashlib
        metadata = {'model_key': 'base:' + trainer.MODEL + ':' + trainer.REVISION,
                    'ids': ['sample'], 'enable_thinking': True, 'do_sample': True,
                    'seed': 20261013, 'max_new_tokens': 2048, 'batch_size': 4,
                    'temperature': .6, 'top_p': .95, 'top_k': 20, 'eos_token_id': 9,
                    'input_sha256': hashlib.sha256(json.dumps([self.row], ensure_ascii=False,
                                                             sort_keys=True).encode()).hexdigest()}
        review.check_metadata(metadata, protocol, [self.row], 'baseline', self.tokenizer)
        wrong = copy.deepcopy(metadata)
        wrong['enable_thinking'] = False
        with self.assertRaisesRegex(ValueError, 'metadata differs'):
            review.check_metadata(wrong, protocol, [self.row], 'baseline', self.tokenizer)
        wrong = copy.deepcopy(metadata)
        wrong['model_key'] = 'adapter:' + 'b' * 64
        with self.assertRaisesRegex(ValueError, 'metadata differs'):
            review.check_metadata(wrong, protocol, [self.row], 'candidate', self.tokenizer)

    def test_reference_count_and_duplicate_guard(self):
        with self.assertRaisesRegex(ValueError, '262 distinct'):
            review.require_complete_references([self.row])
        with self.assertRaisesRegex(ValueError, '262 distinct'):
            review.require_complete_references([self.row] * 262)

    def test_review_plan_is_pending_full_census(self):
        plan = review.review_plan()
        self.assertEqual(plan['expected_counts_per_model'], {'worked_solution': 173, 'hint': 59, 'guard': 30})
        self.assertEqual(plan['state'], 'PREPARED_NOT_YET_REVIEWED')
        self.assertFalse(plan['human_verified'])


if __name__ == '__main__':
    unittest.main()

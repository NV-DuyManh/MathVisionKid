import copy
import unittest
import conditional_inference_contract as C


class FakeTokenizer:
    pad_token_id = 151643

    def apply_chat_template(self, messages, **kwargs):
        assert kwargs == dict(tokenize=True, add_generation_prompt=True,
                              enable_thinking=False)
        return list(C.canonical(messages).encode('utf8'))


class ConditionalContractTests(unittest.TestCase):
    def setUp(self):
        self.fixture = {'id': 'cpu-contract', 'grade': 3, 'mode': 'answer',
                        'userproblem': 'Một đoạn dây chưa cho độ dài. Cần bổ sung gì?',
                        'oracle': {'answer': 'never include'}, 'rubric': 'secret'}

    def test_oracle_and_rubric_cannot_affect_inputs_or_token_binding(self):
        changed = copy.deepcopy(self.fixture)
        changed.update(oracle='different secret', rubric='different rubric')
        self.assertEqual(C.messages(self.fixture), C.messages(changed))
        a = C.build_contract([self.fixture], FakeTokenizer(), 'a'*64)
        b = C.build_contract([changed], FakeTokenizer(), 'a'*64)
        self.assertEqual(a, b)
        self.assertNotIn('secret', C.canonical(C.messages(self.fixture)))

    def test_request_mode_changes_prompt_and_unknown_mode_fails(self):
        hint = {**self.fixture, 'mode': 'hint_no_answer'}
        self.assertNotEqual(C.messages(hint), C.messages(self.fixture))
        with self.assertRaises(KeyError):
            C.messages({**hint, 'mode': 'unknown'})

    def test_decoding_seed_and_fixture_integrity_frozen(self):
        contract, digest = C.build_contract([self.fixture], FakeTokenizer(), 'b'*64)
        self.assertEqual(contract['decoding']['max_new_tokens'], 1024)
        self.assertEqual(contract['revision'], C.REVISION)
        self.assertFalse(contract['enable_thinking'])
        self.assertFalse(contract['model_improvement_established'])
        self.assertEqual(digest, C.sha(C.canonical(contract).encode()))
        self.assertEqual(C.seed_for('cpu-contract'), C.seed_for('cpu-contract'))
        for items, pin in [([self.fixture, self.fixture], 'b'*64),
                           ([self.fixture], 'not-a-hash')]:
            with self.assertRaises(ValueError):
                C.build_contract(items, FakeTokenizer(), pin)


if __name__ == '__main__':
    unittest.main()

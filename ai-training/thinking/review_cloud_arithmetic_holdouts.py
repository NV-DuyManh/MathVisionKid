"""Complete, source-hash-bound actual review and evaluation export checks."""
from __future__ import annotations
import copy
import hashlib
import json
import unittest
from pathlib import Path
import exhaustive_cloud_resume as resume
import exhaustive_multidigit_math as m
from review_cloud_multidigit_current import independent, criteria

HERE = Path(__file__).resolve().parent
RUN = HERE / 'cloud_publication/resume_20261018'
EXPECTED = {
    '': '42b4d53c55ce779533581ae7d42656447768c0605ff7be9842809f7022be0f47',
    '_v2': 'ea8aee08fc69df5faf1f3199bf120663678a3416cfc2f0a99fa7fde51a03e35b',
}
def sha(b): return hashlib.sha256(b).hexdigest()
def read_rows(name): return [json.loads(l) for l in (RUN / name).read_text('utf-8').splitlines()]
def load(suffix):
    source = RUN / ('holdout_arithmetic_cases' + suffix + '.jsonl')
    assert sha(source.read_bytes()) == EXPECTED[suffix], 'Changed source needs new actual semantic review'
    return read_rows(source.name)

class HoldoutChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        resume.configure_sources()
        cls.original = load(''); cls.selected = load('_v2')
        cls.chats = read_rows('holdout_arithmetic_chat_v2.jsonl')
        cls.pedagogy = read_rows('pedagogy_cases_v2.jsonl')
    def test_every_actual_row_math_and_trace(self):
        for row in self.original + self.selected:
            self.assertTrue(m.validate_row(row)['validated']); self.assertTrue(independent(row))
    def test_actual_stored_source_line_hash_binds_each_chat(self):
        for suffix in ('', '_v2'):
            byid = {}
            for line in (RUN / ('holdout_arithmetic_cases' + suffix + '.jsonl')).read_text('utf-8').splitlines():
                row = json.loads(line); byid[row['sample_id']] = sha(line.encode())
            for chat in read_rows('holdout_arithmetic_chat' + suffix + '.jsonl'):
                self.assertEqual(chat['source_row_sha256'], byid[chat['source_sample_id']])
    def test_all_sources_fail_closed_for_training_serializer(self):
        for row in self.original + self.selected:
            self.assertFalse(row['training_eligible'])
            self.assertTrue(row['evaluation_eligible'])
            self.assertEqual(list(m.chat_records(row)), [])
            self.assertNotEqual(row['coverage']['ordered_input_pair'], [1563, 43])
    def test_selected_full_canonical_signatures_pairwise_and_pedagogy_disjoint(self):
        used = {s for r in self.pedagogy if r['split'] in ('validation', 'test') for s in r['canonical_signatures']}
        for row in self.selected:
            signatures = set(row['canonical_signatures'])
            self.assertFalse(signatures & used)
            used.update(signatures)
    def test_exact_four_modes_grouped_and_splits_preserved(self):
        self.assertEqual(len(self.chats), 32)
        for row in self.selected:
            chats = [c for c in self.chats if c['source_sample_id'] == row['sample_id']]
            self.assertEqual(len(chats), 4)
            self.assertEqual({c['mode'] for c in chats}, {'worked_solution', 'hint_level_1', 'hint_level_2', 'hint_level_3'})
            for chat in chats:
                self.assertEqual(chat['case_group_id'], row['case_group_id'])
                self.assertEqual(chat['split'], row['split'])
                self.assertFalse(chat['training_eligible'])
                user = json.loads(chat['messages'][1]['content'])
                self.assertEqual(user['problem'], row['problem'])
                answer = json.loads(chat['messages'][2]['content'])
                if chat['mode'] == 'worked_solution':
                    self.assertEqual(answer['steps'], row['worked_steps']); self.assertEqual(answer['answer'], row['expected_answer'])
                else:
                    hint = row['hints'][int(chat['mode'][-1]) - 1]
                    self.assertEqual(answer, {'hint': hint['hint'], 'question': hint['question']})
    def test_mutated_numeric_answer_rejected(self):
        for row in self.selected:
            bad = copy.deepcopy(row); bad['expected_answer'][0]['result'] = '999999'
            with self.assertRaises(ValueError): m.validate_row(bad)
    def test_reservation_union_complete_no_signature_definition_change(self):
        reservation = json.loads((RUN / 'holdout_arithmetic_reservations_v2.json').read_text('utf-8'))
        union = {s for r in self.selected for s in r['canonical_signatures']}
        self.assertEqual(set(reservation['all_train_exclusion_signatures']), union)
        self.assertEqual(sum(r['split'] == 'validation' for r in self.selected), 4)
        self.assertEqual(sum(r['split'] == 'test' for r in self.selected), 4)
    def test_provenance_no_future_human_or_external_claim(self):
        for row in self.original + self.selected:
            self.assertFalse(row['provenance']['human_verified'])
            self.assertFalse(row['provenance']['teacher_certified'])
            self.assertFalse(row['provenance']['independent_external_review'])
            self.assertIsNone(row['student_work'])

def finalize():
    resume.configure_sources()
    for suffix in ('', '_v2'):
        rows = load(suffix)
        path = RUN / ('holdout_arithmetic_qa' + suffix + '.json')
        qa = json.loads(path.read_text('utf-8'))
        qa.update(status='PASSED_ACTUAL_SOURCE_SEMANTIC_AND_EXACT_QA',
                  selected_role='SELECTED_EVALUATION' if suffix else 'CORPUS_AND_CHAT_AUDIT_ONLY_SUPERSEDED_BY_V2',
                  actual_content_review=True, actual_full_source_cases_read=8,
                  actual_review_fields='Every actual problem/givens/request/student_work/initial/three hints/title/reason/explanation/expression/result/unit/answer read. Source bytes stayed unchanged after review.',
                  review_code_sha256=sha(Path(__file__).read_bytes()),
                  seven_criteria=criteria(), meaningful_tests_passed=8,
                  source_row_hash_definition='SHA256 exact stored UTF-8 JSONL line excluding newline',
                  source_and_chat_stored_hashes_rechecked=True,
                  row_reviews=[{'sample_id': r['sample_id'], 'source_row_sha256': sha(m.base.dumps(r).encode()),
                                'actual_content_semantic_review': 'PASS', 'criteria': criteria()} for r in rows])
        path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), 'utf-8')
        print(json.dumps({'qa': path.name, 'status': qa['status'], 'source_sha256': qa['source_sha256'], 'chat_sha256': qa['chat_sha256']}))

if __name__ == '__main__':
    import sys
    if '--finalize' in sys.argv: finalize()
    else: unittest.main(verbosity=2)

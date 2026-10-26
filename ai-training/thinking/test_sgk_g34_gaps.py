import copy
import hashlib
import json
from pathlib import Path
import unittest

import build_sgk_g34_gaps as b
import exhaustive_colab_loader as L


class GapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = list(b.rows(b.RUN / 'sgk_g34_cases.jsonl'))
        cls.by_id = {r['sample_id']: r for r in cls.cases}

    def test_every_lesson_number_in_actual_four_tocs(self):
        catalog = json.loads((b.RUN / 'sgk_g34_catalog.json').read_text('utf-8'))
        for grade, total in ((3,81),(4,73)):
            self.assertEqual(sorted(r['lesson'] for r in catalog['lessons'] if r['grade']==grade), list(range(1,total+1)))
        self.assertFalse(catalog['all_SGK_exercise_types_certified'])

    def test_all_exact_oracles(self):
        for row in self.cases:
            b.verify_oracle(row)

    def test_all_source_line_hashes_bind_actual_emitted_bytes(self):
        lines=(b.RUN/'sgk_g34_cases.jsonl').read_bytes().splitlines()
        reviews=list(b.rows(b.RUN/'sgk_g34_reviews.jsonl'))
        self.assertEqual(len(lines),40)
        self.assertEqual([hashlib.sha256(line).hexdigest() for line in lines], [r['source_row_sha256'] for r in reviews])

    def test_no_fake_human_attestation(self):
        for row in self.cases:
            self.assertEqual(row['acceptance_status'],'ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED')
            for key in ('human_verified','teacher_certified','owner_human_reviewed','independent_external_review'):
                self.assertFalse(row['provenance'][key])

    def test_guard_givens_keep_actual_missing_fields(self):
        for row in self.cases:
            self.assertEqual(row['givens'][0]['text'],row['problem'])
            if not row['can_solve']:
                self.assertEqual(row['expected_answer'],[])
                self.assertTrue(row['oracle_evidence']['fields'])
                self.assertNotIn('Dữ kiện đầy đủ',row['givens'][0]['text'])

    def test_chat_ids_all_four_modes_and_hints_actual(self):
        modes={sid:set() for sid in self.by_id}
        for chat in b.rows(b.RUN/'sgk_g34_chat.jsonl'):
            L.validate_chat(chat)
            sid=chat['source_sample_id'];row=self.by_id[sid]
            modes[sid].add(chat['mode'])
            payload=json.loads(chat['messages'][-1]['content'])
            if chat['mode'].startswith('hint_'):
                expected=row['hints'][int(chat['mode'][-1])-1]
                self.assertEqual(payload,{k:expected[k] for k in ('hint','question')})
        self.assertTrue(all(v==set(L.MODES) for v in modes.values()))

    def test_problem_ids_and_texts_unique_vs_full_nonbulk_corpus(self):
        old,_=b.existing()
        new_ids={r['sample_id'] for r in self.cases}
        self.assertFalse(new_ids & {r['sample_id'] for r in old})
        normalized=lambda s:' '.join(s.casefold().split())
        texts={normalized(r['problem']) for r in self.cases}
        self.assertEqual(len(texts),40)
        self.assertFalse(texts & {normalized(r['problem']) for r in old})

    def test_prior_source_preserved_against_catalog_hash(self):
        catalog=json.loads((b.RUN/'sgk_g34_catalog.json').read_text('utf-8'))
        for item in catalog['inputs']:
            self.assertEqual(L.file_hash(b.ROOT.parent/item['path']),item['sha256'])

    def reject_modified_oracle(self,topic,variant,field,value):
        row=copy.deepcopy(self.by_id[f'sgk_gap_20261019_g{3 if topic in ("roman_material","roman_routes","calendar_occurrences") else 4}_{topic}_{variant}'])
        row['oracle_evidence'][field]=value
        with self.assertRaises(AssertionError):b.verify_oracle(row)

    def test_roman_material_rejects_wrong_stroke_total(self):
        self.reject_modified_oracle('roman_material','stock','used',19)

    def test_directed_graph_rejects_fabricated_edge_path(self):
        self.reject_modified_oracle('roman_routes','branch','paths',[['I','VI','IX']])

    def test_calendar_rejects_missing_fifth_weekday(self):
        self.reject_modified_oracle('calendar_occurrences','fifth_weekday','dates',[1,8,15,22])

    def test_digit_permutations_reject_missing_or_leading_zero(self):
        self.reject_modified_oracle('parity_cards','two_digit_zero','values',[8,30,38,80])

    def test_rounding_rejects_inclusive_upper_midpoint(self):
        self.reject_modified_oracle('rounding_preimage','all_integers','maximum',450000)

    def test_fraction_model_rejects_inverted_share(self):
        self.reject_modified_oracle('fraction_division_model','more_than_one','share','7/9')

    def test_estimation_rejects_false_bound_claim(self):
        self.reject_modified_oracle('estimate_bounds','product_upper','claim',True)


if __name__=='__main__':unittest.main(verbosity=2)

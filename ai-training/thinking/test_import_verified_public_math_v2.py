import unittest
from fractions import Fraction
from import_verified_public_math_v2 import Rejected, derive_trace, exact, facts_from_question, imported_record


class PublicTraceTests(unittest.TestCase):
    def test_whitespace_exact_recompute_and_multistep(self):
        self.assertEqual(exact('  2550 '), 2550)
        facts, target, trace, constants = derive_trace('An có 49 kg gạo, nhận thêm 16 kg, rồi chia đều cho 5 người. Hỏi mỗi người có bao nhiêu kg?', '49 + 16 = 65 (kg)\n65 : 5 = 13 (kg)', Fraction(13), 'kg')
        self.assertEqual(target['expr'], '((f0+f1)/f2)')
        self.assertFalse(constants)
        self.assertEqual(len(trace), 2)
        for fact in facts:
            self.assertEqual(fact['quote'], 'An có 49 kg gạo, nhận thêm 16 kg, rồi chia đều cho 5 người. Hỏi mỗi người có bao nhiêu kg?'[slice(*fact['span'])])

    def test_arithmetic_wrong_or_unrelated_final_rejected(self):
        with self.assertRaises(Rejected): derive_trace('An có 49 kg, thêm 16 kg.', '49 + 16 = 64 (kg)', Fraction(64), 'kg')
        with self.assertRaises(Rejected): derive_trace('An có 49 kg, thêm 16 kg.', '49 + 16 = 65 (kg)', Fraction(14), 'kg')

    def test_missing_fact_and_duplicate_grounding_rejected(self):
        with self.assertRaises(Rejected): derive_trace('An có 49 kg, thêm 16 kg.', '49 + 17 = 66 (kg)', Fraction(66), 'kg')
        with self.assertRaises(Rejected): derive_trace('An có 16 kg, Bình có 16 kg.', '16 + 16 = 32 (kg)', Fraction(32), 'kg')

    def test_fraction_as_one_grounded_fact(self):
        facts, target, _, _ = derive_trace('Có 850 kg thóc và bán 2/5 số thóc. Hỏi bán bao nhiêu kg?', '850 × 2/5 = 340 kg', Fraction(340), 'kg')
        self.assertEqual(facts[1]['value'], '2/5')
        self.assertEqual(target['expr'], '(f0*f1)')

    def test_ambiguous_locale_and_untrusted_code(self):
        with self.assertRaises(Rejected): facts_from_question('Có 1.000 kg và 5 kg.')
        with self.assertRaises(Rejected): derive_trace('An có 49 kg, thêm 16 kg.', 'print(49+16)', Fraction(65), 'kg')
        with self.assertRaises(Rejected): exact('__import__("os").system("echo unsafe")')

    def test_conversions_are_explicit_and_annotated(self):
        _, target, _, constants = derive_trace('Đi 3 km mỗi giờ trong 2 giờ, tính quãng đường theo m.', '3 × 2 = 6 km\n6 × 1000 = 6000 m', Fraction(6000), 'm')
        self.assertEqual(target['expr'], '((f0*f1)*1000)')
        self.assertEqual(constants, {'1000': 'metric_conversion_factor'})
        with self.assertRaises(Rejected): derive_trace('An có 49 quả, Bình có 16 quả.', '49 + 16 + 1000 = 1065 quả', Fraction(1065), 'quả')

    def test_source_segmentation_answer_leak_rejected(self):
        row = {'question': 'An có 49 kg, thêm 16 kg. Hỏi có bao nhiêu kg? Đáp số: 65 kg',
               'solution': '49 + 16 = 65 (kg)\nĐáp số: 65 kg', 'grade': 2,
               'source_url': 'https://example.invalid/source', 'source_id': 'fixture',
               'source_title': 'fixture', 'content_index': 0, 'block_index': 0}
        with self.assertRaisesRegex(Rejected, 'SOLUTION_OR_ANSWER_MARKUP_IN_QUESTION'):
            imported_record(row, 'hllj/vi_math_problem_crawl')


if __name__ == '__main__': unittest.main()

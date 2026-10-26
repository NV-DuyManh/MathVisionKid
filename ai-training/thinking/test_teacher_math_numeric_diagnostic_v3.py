import unittest
from fractions import Fraction
from teacher_math_numeric_diagnostic_v3 import extract,unit

class NumericDiagnosticTests(unittest.TestCase):
    def test_missing_explanation_does_not_hide_correct_number(self):
        self.assertEqual(extract('{"answer":"13","unit":"viên bi"}'),(Fraction(13),'viên'))
    def test_decimal_and_embedded_unit(self):
        self.assertEqual(extract('{"answer":"0,3 kg"}'),(Fraction(3,10),'kg'))
    def test_fraction(self):
        self.assertEqual(extract('{"answer":"5/6","unit":null}'),(Fraction(5,6),''))
    def test_invalids_never_repaired(self):
        for text in ('{"answer":true}','{"answer":"unknown"}','{"answer":"13","answer":"9"}',
                     '{"answer":"13 kg","unit":"cm"}','{"answer":"1/0"}'):
            with self.assertRaises((ValueError,ZeroDivisionError)):extract(text)

if __name__=='__main__':unittest.main()

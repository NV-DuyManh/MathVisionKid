from fractions import Fraction
import unittest
from verified_math_data_v2 import build
from verified_math_runtime_equiv_v2 import solve_equivalent_verified,tutor_equivalent_verified

class EquivRuntimeTests(unittest.TestCase):
    def test_gold_contract_and_all_reference_domains(self):
        for row in build():
            r=solve_equivalent_verified(row['problem'],row['target'],row['grade'])
            self.assertTrue(r['accepted'],row['sample_id'])
            if row['target']['status']=='solve':self.assertEqual(Fraction(r['answer']),Fraction(row['oracle_answer']))

    def test_commuted_formula_has_safe_hint_and_worked_steps(self):
        q='Tính tổng hai phân số 1/2 và 1/3.'
        p={'status':'solve','expr':'f1+f0','unit':''}
        r=solve_equivalent_verified(q,p,4);self.assertEqual(r['answer'],'5/6')
        hint=tutor_equivalent_verified(q,p,4)
        self.assertFalse(hint['student_response']['revealAnswer'])
        self.assertNotIn('final_answer',hint['student_response'])
        self.assertNotIn('answer',hint['machine'])
        worked=tutor_equivalent_verified(q,p,4,'worked_solution')
        self.assertEqual(worked['student_response']['final_answer'],'5/6')
        self.assertGreater(len(worked['student_response']['steps']),3)

    def test_numerical_coincidence_wrong_formula_unknown_and_bad_unit(self):
        q='Lan có 2 quả táo, được cho thêm 2 quả. Lan có tất cả bao nhiêu quả táo?'
        for expr,unit in [('f0*f1','quả'),('f2+f0','quả'),('f0+f1','cm'),('__import__("os")','quả')]:
            self.assertFalse(solve_equivalent_verified(q,{'status':'solve','expr':expr,'unit':unit},1)['accepted'])
        self.assertFalse(solve_equivalent_verified('Giải bất kỳ phương trình x nào',{'status':'solve','expr':'1','unit':''},5)['accepted'])

    def test_zero_cancel_not_accepted_as_reference_sum(self):
        q='Lan có 0 quả táo, được cho thêm 0 quả. Lan có tất cả bao nhiêu quả táo?'
        self.assertFalse(solve_equivalent_verified(q,{'status':'solve','expr':'f0/f0','unit':'quả'},1)['accepted'])

if __name__=='__main__':unittest.main()

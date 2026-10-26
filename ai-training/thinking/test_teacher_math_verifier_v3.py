import copy
import unittest
from teacher_math_verifier_v3 import calculate,check_arithmetic,verify_supported_contract

class VerifierTests(unittest.TestCase):
    def response(self):
        return {'status':'solve','steps':[{'explanation':'Bớt số đã cho.','expression':'8-3','result':'5','unit':'viên'}],
                'answer':'5','unit':'viên','hint':None}
    def test_decimal_fraction_exact(self):
        self.assertEqual(calculate('0.1+0.2'),calculate('3/10'))
    def test_injection_and_exponent_rejected(self):
        for expression in ('__import__("os")','2**100000','open(1)','[2]','1/0'):
            with self.assertRaises((ValueError,ZeroDivisionError,SyntaxError)): calculate(expression)
    def test_arithmetic_alone_never_claims_semantics(self):
        obj=self.response();obj['steps'][0].update(expression='8+3',result='11');obj['answer']='11'
        result=check_arithmetic(obj)
        self.assertTrue(result['arithmetic_consistent'])
        self.assertFalse(result['semantic_verification'])
        self.assertFalse(result['safe_to_release_verified_solution'])
    def test_wrong_intermediate_rejected(self):
        obj=self.response();obj['steps'][0]['result']='6'
        self.assertFalse(check_arithmetic(obj)['arithmetic_consistent'])
    def test_hint_solution_fields_blocked(self):
        self.assertFalse(check_arithmetic(self.response(),mode='hint')['arithmetic_consistent'])
        hint={'status':'solve','steps':[],'answer':None,'unit':None,'hint':'Em kiểm tra lượng đã cho đi bằng cách nào?'}
        self.assertTrue(check_arithmetic(hint,mode='hint')['arithmetic_consistent'])
        self.assertFalse(check_arithmetic(hint,mode='hint')['safe_to_release_verified_solution'])
    def test_supported_contract_and_wrong_interpretation(self):
        obj=self.response()
        contract={'source':'independent_supported_question_solver','question_confirmed':True,
                  'status':'solve','answer':'5','unit':'viên','steps':copy.deepcopy(obj['steps'])}
        result=verify_supported_contract(obj,contract)
        self.assertTrue(result['semantic_verification'])
        self.assertFalse(result['safe_to_release_verified_solution'])
        obj['steps'][0].update(expression='8+3',result='11');obj['answer']='11'
        self.assertFalse(verify_supported_contract(obj,contract)['semantic_verification'])
    def test_gold_not_deployment_contract(self):
        self.assertFalse(verify_supported_contract(self.response(),{'source':'training_label'})['semantic_verification'])

if __name__=='__main__': unittest.main()

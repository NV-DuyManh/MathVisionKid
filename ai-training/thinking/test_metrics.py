import json
import unittest
from metrics import parse_final,score

class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.ref=dict(status='solved',steps=[dict(expression='12+5',result='17',unit='bút',explanation='Được thêm nên cộng.')],answer='17',unit='bút')
    def test_correct_json(self):
        self.assertTrue(all(v for k,v in score(json.dumps(self.ref),self.ref).items() if k!='clarification_specific'))
    def test_unfinished_thinking_not_promoted(self):
        with self.assertRaises(ValueError): parse_final('<think> chưa xong '+json.dumps(self.ref))
    def test_correct_answer_wrong_plan_not_promoted(self):
        candidate={**self.ref,'steps':[dict(expression='12-5',result='7',unit='bút',explanation='Trừ') ]}
        result=score(json.dumps(candidate),self.ref)
        self.assertTrue(result['answer_correct'])
        self.assertFalse(result['reference_plan_match'])
        self.assertFalse(result['steps_arithmetic_correct'])
    def test_unit_mismatch(self):
        self.assertFalse(score(json.dumps({**self.ref,'unit':'kg'}),self.ref)['unit_correct'])
    def test_no_json(self):
        self.assertFalse(score('17 bút',self.ref)['json_valid'])
    def test_separates_explanation_from_final(self):
        self.assertTrue(score('<think> Vì thêm nên cộng. </think>\n'+json.dumps(self.ref),self.ref)['answer_correct'])
if __name__=='__main__': unittest.main()

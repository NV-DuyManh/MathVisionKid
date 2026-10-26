import json
import unittest
from scope_contract import TEMPLATES,inspect_problem,expected_plan
from scope_runtime import solve_with_planner

class ScopeRuntimeTests(unittest.TestCase):
    def test_bad_model_output_never_published(self):
        problem=TEMPLATES['add_join'][0].format(a=4,b=6,u='quả')
        result=solve_with_planner(problem,1,lambda system,user:'4+4=8')
        self.assertFalse(result['accepted']); self.assertIsNone(result['answer'])

    def test_guard_does_not_call_model(self):
        def forbidden(system,user): raise AssertionError('must not call')
        for problem in ['Viết mã Python in số 7.','Một hình chữ nhật dài 5 cm. Tính diện tích?',
                        'Tính diện tích hình vuông có cạnh 4 cm.']:
            result=solve_with_planner(problem,3,forbidden)
            self.assertTrue(result['accepted']); self.assertIsNone(result['answer'])

    def test_plan_does_not_publish_free_model_explanation(self):
        problem=TEMPLATES['share_equal'][3].format(a=27,b=9,u='bút')
        def planner(system,user):
            payload=json.loads(user)
            self.assertNotIn('source_contract',payload)
            return '<think>Đáp án bịa 999.</think>'+json.dumps(expected_plan(inspect_problem(problem,3)))
        result=solve_with_planner(problem,3,planner)
        self.assertEqual(result['answer'],'3'); self.assertNotIn('999',result['worked_solution'])

    def test_backend_call_failure_returns_no_answer(self):
        def broken(system,user): raise RuntimeError('API secret must not leak')
        problem=TEMPLATES['add_join'][0].format(a=4,b=6,u='quả')
        result=solve_with_planner(problem,1,broken)
        self.assertIsNone(result['answer']); self.assertNotIn('secret',str(result))

if __name__=='__main__': unittest.main()

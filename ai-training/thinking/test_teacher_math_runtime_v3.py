import json
import unittest
from fractions import Fraction
import teacher_math_data_v3 as data
from teacher_math_runtime_v3 import inspect_known_problem,tutor

class RuntimeTests(unittest.TestCase):
    def row(self):
        return data.make_row(data.TOPICS[0],'train',0,{'a':Fraction(8),'b':Fraction(1)},'worked_solution')
    def test_no_semantics_for_fractional_objects(self):
        self.assertIsNone(inspect_known_problem('An có 1,5 viên bi, được tặng thêm 2 viên. An có tất cả bao nhiêu viên?'))
    def test_grade1_carry_outside_supported_bounds(self):
        self.assertIsNone(inspect_known_problem('An có 8 viên bi, được tặng thêm 3 viên. An có tất cả bao nhiêu viên?',grade=1))
    def test_ocr_confirmation_required(self):
        row=self.row();response=tutor(row['problem'],json.dumps(row['target'],ensure_ascii=False),mode='worked_solution')
        self.assertEqual(response['status'],'NEEDS_CONFIRMATION');self.assertFalse(response['reveal_answer'])
    def test_correct_numeric_render_and_wrong_operation_block(self):
        row=self.row();good=json.dumps(row['target'],ensure_ascii=False)
        self.assertEqual(tutor(row['problem'],good,mode='worked_solution',input_confirmed=True)['status'],'SUPPORTED_RESEARCH_SOLUTION')
        bad=json.loads(good);bad['steps'][0].update(expression='8-1',result='7');bad['answer']='7'
        response=tutor(row['problem'],json.dumps(bad),mode='worked_solution',input_confirmed=True)
        self.assertEqual(response['status'],'MODEL_RESPONSE_REJECTED');self.assertFalse(response['reveal_answer'])
    def test_hint_renderer_no_solution_leak(self):
        row=self.row();response=tutor(row['problem'],'bad model text',input_confirmed=True)
        self.assertFalse(response['reveal_answer']);self.assertNotIn('solution',response)
    def test_arbitrary_question_not_claimed_supported(self):
        self.assertIsNone(inspect_known_problem('Có tám quả táo, cho đi ba quả. Còn mấy quả?'))
    def test_huge_observed_result_does_not_crash(self):
        row=next(t for t in data.TOPICS if t.name=='vertical_add')
        problem,_=data.render_question(row,0,{'a':Fraction(12),'b':Fraction(3)})
        problem+=' Học sinh ghi kết quả 1234567890123456789. Hãy giúp em kiểm tra; đây là bài làm quan sát được, chưa có các dấu nhớ hoặc mượn.'
        self.assertIsNone(inspect_known_problem(problem))

if __name__=='__main__':unittest.main()

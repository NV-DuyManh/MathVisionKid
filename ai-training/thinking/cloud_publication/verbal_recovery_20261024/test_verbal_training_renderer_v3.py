import unittest,copy
import verbal_training_renderer_v3 as V
class RendererTests(unittest.TestCase):
 def worked(self):return {'can_solve':True,'initial_guidance':['Đổi cùng đơn vị.'],'steps':[{'step_id':'s1','title':'Trừ','reason':'Bớt phần đã lấy.','expression':'3240-850','result':'2390','unit':'g','explanation':'3240 − 850 = 2390 g.'}],'answer':[{'quantity':'Khối lượng','result':'2 kg 390 g','unit':'g'}]}
 def test_fields_and_units_preserved(self):
  out,p=V.target(self.worked(),'worked_solution')
  self.assertTrue(all(x['value'] in out for x in p['fields']));self.assertIn('2 kg 390 g',out);self.assertIn('3240-850',out);self.assertNotIn('s1',out)
 def test_no_silent_unknown_fields(self):
  t=self.worked();t['image_observation']='unknown'
  with self.assertRaises(ValueError):V.target(t,'worked_solution')
 def test_hint_no_added_answer(self):
  out,p=V.target({'hint':'Lấy hiệu vận tốc rồi nhân thời gian cùng đơn vị.','question':'Em cần đổi phút sang đơn vị nào?'},'hint_level_1')
  self.assertNotIn('0,9',out);self.assertNotIn('Đáp số',out);self.assertIn('đổi phút',out)
 def test_ground_student_work(self):
  out=V.prompt({'grade':2,'problem':'Kiểm tra bài.','mode':'worked_solution','student_work':'3+2=5'})
  self.assertIn('3+2=5',out)
  with self.assertRaises(ValueError):V.prompt({'grade':2,'problem':'Kiểm tra bài.','mode':'worked_solution','student_work':{'guess':'hidden'}})
 def test_missing_guard_no_solution_fabricated(self):
  t={'can_solve':False,'initial_guidance':['Cần số đo thực tế.'],'steps':[],'answer':[]};out,p=V.target(t,'worked_solution');self.assertIn('Chưa thể',out);self.assertIn('Cần số đo',out);self.assertNotIn('Đáp số',out)
 def test_source_untouched(self):
  import json
  r={'mode':'worked_solution','messages':[{'role':'system','content':'Gia sư'},{'role':'user','content':json.dumps({'grade':3,'problem':'Bài gốc','mode':'worked_solution'})},{'role':'assistant','content':json.dumps(self.worked())}]};before=copy.deepcopy(r);V.render(r);self.assertEqual(r,before)
 def test_given_and_requested_fields_retained(self):
  out=V.prompt({'grade':2,'problem':'Bài gốc','mode':'worked_solution','givens':[{'id':'g1','role':'explicit_original_given','text':'Có5bước','value':5,'unit':'bước'}],'requested_quantity':'Vạch đáp','student_work':None})
  self.assertIn('Có5bước',out);self.assertIn('Giá trị đã cho: 5',out);self.assertIn('bước',out);self.assertIn('Vạch đáp',out);self.assertNotIn('Lời làm',out)
 def test_exact_display_strings_preserved(self):
  t=self.worked();t['steps'][0].update(display_expression='(3240 − 850)',display_result='2390',exact_result_rational='2390');t['answer'][0].update(display_result='2kg390g',exact_result_rational='2390')
  out,proof=V.target(t,'worked_solution');self.assertIn('(3240 − 850)',out);self.assertIn('2kg390g',out);self.assertTrue(all(x['value'] in out for x in proof['fields']))
 def test_observable_work_only_not_reviewer_annotations(self):
  out=V.prompt({'grade':2,'mode':'worked_solution','problem':'Đếm nét đã vẽ.','student_work':{'text':'Em đếm cảEA.','origin':'ANNOTATION_ORIGIN','observations':[{'excerpt':'Em đếm cảEA.','nature':'INTERNAL_LABEL','claim_scope':'INTERNAL_SCOPE'}]}})
  self.assertIn('Em đếm cảEA.',out);self.assertNotIn('INTERNAL_LABEL',out);self.assertNotIn('INTERNAL_SCOPE',out);self.assertNotIn('ANNOTATION_ORIGIN',out)
if __name__=='__main__':unittest.main()

import copy,hashlib,json,unittest
import conditional_behavior_renderer as R

class ConditionalRendererTests(unittest.TestCase):
    def test_only_worked_suffix_changes_and_problem_kept_exact(self):
        p={'grade':3,'problem':'Đề chưa cho số đo AB. Cần bổ sung gì?','mode':'worked_solution'}
        old=R.BASE.prompt(p);new=R.prompt(p)
        self.assertEqual(new.split('\n\nYêu cầu:\n\n')[0],old.split('\n\nYêu cầu:\n\n')[0])
        self.assertIn(p['problem'],new)
        self.assertTrue(new.endswith(R.WORKED_INSTRUCTION))
        self.assertIn('Nếu dữ kiện đủ và nhất quán',new)
        self.assertIn('Nếu đề thiếu dữ kiện',new)
    def test_identical_instruction_for_all_worked_behaviors_no_oracle_route(self):
        problems=['Tính 45+2.','Em viết 45+2=48. Hãy kiểm tra.','Chưa có độ dài cạnh.']
        for text in problems:
            p={'grade':4,'problem':text,'mode':'worked_solution'}
            self.assertTrue(R.prompt(p).endswith(R.WORKED_INSTRUCTION))
    def test_hint_modes_are_byte_identical_and_no_answer_added(self):
        for m in ['hint_level_1','hint_level_2','hint_level_3']:
            p={'grade':2,'problem':'Tính 23+14, chỉ gợi ý.','mode':m}
            self.assertEqual(R.prompt(p),R.BASE.prompt(p))
            self.assertNotIn('37',R.prompt(p))
    def test_source_fields_and_target_preserved_no_human_flag_copy(self):
        p={'grade':2,'problem':'Tính 4+2.','mode':'worked_solution','student_work':'Em viết4+2=7.'}
        target={'can_solve':True,'initial_guidance':['Gộp hai phần.'],'steps':[{'title':'Cộng','reason':'Tìm tổng.','expression':'4+2','result':'6','explanation':'Bốn thêm hai được sáu.'}],'answer':[{'quantity':'Tổng','result':'6'}]}
        row={'sample_id':'case:worked_solution','case_group_id':'case','mode':'worked_solution','split':'train','messages':[{'role':'system','content':'source-system'},{'role':'user','content':json.dumps(p,ensure_ascii=False)},{'role':'assistant','content':json.dumps(target,ensure_ascii=False)}],'human_verified':True,'teacher_certified':True}
        before=copy.deepcopy(row);new,proof=R.render(row);old,_=R.BASE.render(row)
        self.assertEqual(row,before)
        self.assertEqual(new['messages'][-1]['content'],old['messages'][-1]['content'])
        self.assertEqual(proof['target_sha256'],hashlib.sha256(new['messages'][-1]['content'].encode()).hexdigest())
        self.assertNotIn('human_verified',new)
        self.assertFalse(proof['new_human_review_or_credential_claimed'])
        self.assertIn(p['student_work'],new['messages'][1]['content'])
    def test_unknown_fields_and_mode_refused(self):
        with self.assertRaises(ValueError):R.prompt({'grade':1,'problem':'Bài','mode':'unknown'})
        with self.assertRaises(ValueError):R.prompt({'grade':1,'problem':'Bài','mode':'worked_solution','oracle':'secret'})

if __name__=='__main__':unittest.main()

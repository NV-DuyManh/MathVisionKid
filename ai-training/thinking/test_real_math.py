import unittest
from real_math_data import extract,equations,exact_arithmetic,prompt,validate
from real_math_training import rotated,parse_answer,scores,aggregate,serialize

class RealMathTests(unittest.TestCase):
    def sample(self):
        return ({'grade':'1','url':'https://example.test/a','id':'a'},
                {'question':'Câu 1: An có 4 quả cam, được cho thêm 6 quả. An có tất cả bao nhiêu quả?',
                 'choices':['A. 4','B. 6','C. 10','D. 11'],
                 'explanation':'Đáp án đúng là: C. Số cam có tất cả là: 4 + 6 = 10 (quả). Đáp số: 10 quả cam.'})
    def test_no_gold_in_prompt_and_provenance(self):
        a,b=self.sample();r,error=extract(a,b,0);self.assertIsNone(error)
        self.assertNotIn(r['explanation'],prompt(r));self.assertNotIn('answer',prompt(r));self.assertFalse(r['human_verified'])
        self.assertEqual(r['arithmetic_audit']['checked_equations'],1)
    def test_source_error_and_missing_image_rejected(self):
        a,b=self.sample();b['explanation']=b['explanation'].replace('4 + 6 = 10','4 + 6 = 11')
        self.assertEqual(extract(a,b,0)[1],'ARITHMETIC_OR_NOTATION_REVIEW')
        a,b=self.sample();b['question']='Quan sát hình bên và tìm số cam của An.'
        self.assertEqual(extract(a,b,0)[1],'IMAGE_OR_TABLE_DEPENDENCY')
    def test_fraction_decimal_and_safe_evaluator(self):
        self.assertFalse(equations(r'35\times \frac{3}{4}=14')[0]['correct'])
        self.assertTrue(equations('23,5 + 18,2 * 1,75 = 55,35')[0]['correct'])
        self.assertEqual(str(exact_arithmetic('0.1+0.2')),'3/10')
        for s in ('__import__("os")','x+1','2**100','True','1/0'):
            with self.assertRaises((ValueError,ZeroDivisionError)):exact_arithmetic(s)
    def test_full_expressions_thousands_and_symbolic_fragments(self):
        for expression in ('125 × 11 − 11 × 25 = 11 × (125 − 25) = 1100',
                           '32 x 32 = 1 024','875 x (918 + 25) = 825125',
                           'x × (33 + 67) = 10 000', '(51 + 166 + 143) : 3 = 360 : 3 = 120',
                           'y : 136 = 630 : 6', 'y – 12356 = 103 × 124', '4325 : 123 = 35 dư 20'):
            self.assertTrue(all(r['correct'] for r in equations(expression)),expression)
        self.assertEqual(equations('x × (33 + 67) = 10 000'),[])
    def test_conflicting_labels_and_split_leak(self):
        a,b=self.sample();b['explanation']+=' Chọn B'
        self.assertEqual(extract(a,b,0)[1],'ABSENT_OR_CONFLICTING_ANSWER')
        a,b=self.sample();r,_=extract(a,b,0);r['split_group_id']='a'
        with self.assertRaises(AssertionError):validate({'train':[r],'val':[r],'test':[]})
    def test_rotation_and_strict_final_answer(self):
        a,b=self.sample();r,_=extract(a,b,0)
        options,target=rotated(r,1);self.assertEqual(options,['6','10','11','4']);self.assertEqual(target,'B')
        text='<think>4 + 6 = 10</think> {"answer":"B"}'
        self.assertTrue(scores(r,text,shift=1)['correct']);self.assertFalse(scores(r,text,truncated=True,shift=1)['correct'])
        for s in ('{"answer":"C"}', '<think>unfinished {"answer":"C"}',
                  '</think>{"answer":"C","answer":"A"}','</think>{"answer":"C","solution":"x"}'):
            self.assertIsNone(parse_answer(s))
        summary=aggregate([{'scores':scores(r,text,shift=1)}]);self.assertEqual(summary['accuracy'],1)
        self.assertLess(summary['accuracy_wilson_95'][0],1)
    def test_masking_and_length_rejection(self):
        from test_planner_training import TinyTokenizer
        a,b=self.sample();r,_=extract(a,b,0);item=serialize(r,TinyTokenizer(),3000)
        completion=''.join(chr(c) for c in item['labels'] if c!=-100)
        self.assertEqual(completion.count('</think>'),1);self.assertIn(r['explanation'],completion)
        with self.assertRaises(ValueError):serialize(r,TinyTokenizer(),10)

if __name__=='__main__':unittest.main()

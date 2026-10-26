import unittest
from mcq_final_answer import parse_final

class FinalAnswerTests(unittest.TestCase):
    def test_explicit_final_formats(self):
        for s in ('{"answer":"C"}','Đáp án đúng là: C.','\\boxed{C}', 'C.',
                  '```json\n{"answer":"C"}\n```','Đáp án **C**.',
                  'Suy luận ngắn: 4 + 6 = 10. JSON: {"answer":"C"}',
                  '{"answer":"C","explanation":"arithmetic not certified"}'):
            self.assertEqual(parse_final('<think>Chọn A trong suy luận cũ.</think>'+s),'C')
    def test_no_inference_from_reasoning_or_ambiguous_output(self):
        for s in ('<think>Đáp án C','<think>Đáp án C</think>Không biết',
                  '</think>Chọn C hoặc A','</think>Chọn C. Đáp án A.',
                  '</think>{"answer":"C","answer":"A"}',
                  '</think>{"answer":"AC"}','</think>{"answer":3}',
                  '</think>{"answer":"C"} {"answer":"A"}', '</think><think>Chọn C'):
            self.assertIsNone(parse_final(s))
    def test_truncation_and_duplicate_closing(self):
        self.assertIsNone(parse_final('</think>{"answer":"C"}',True))
        self.assertIsNone(parse_final('</think></think>{"answer":"C"}'))
        self.assertIsNone(parse_final('</think>'+'a'*50001))

if __name__=='__main__':unittest.main()

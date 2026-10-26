import json
import unittest
from planner_training_data import collate,epoch_batches,serialize
from planner_metrics import score_prediction,aggregate
from scope_dataset import build

class TinyTokenizer:
    eos_token='[EOS]'
    def __call__(self,text,**kwargs): return {'input_ids':[ord(c) for c in text]}
    def apply_chat_template(self,*args,**kwargs): return 'system and user\n<think>\n'

class PlannerTrainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.rows=build()

    def test_assistant_mask_padding_and_no_double_think(self):
        row=next(r for r in self.rows if r['target']['status']=='ready')
        item=serialize(row,TinyTokenizer(),max_length=3000)
        supervised=''.join(chr(x) for x in item['labels'] if x!=-100)
        self.assertNotIn('<think>',supervised); self.assertIn('</think>',supervised)
        self.assertTrue(supervised.endswith('[EOS]'))
        self.assertEqual(sum(x==-100 for x in item['labels']),len('system and user\n<think>\n'))
        padded=collate([item,{'input_ids':[1],'labels':[1],'attention_mask':[1]}],9)
        self.assertEqual(padded['labels'][1][1:],[-100]*(len(item['labels'])-1))
        self.assertTrue(all(v==0 for v in padded['attention_mask'][1][1:]))

    def test_no_truncation(self):
        with self.assertRaises(ValueError): serialize(self.rows[0],TinyTokenizer(),max_length=10)

    def test_full_epoch_exactly_once_and_resume_batches(self):
        batches=epoch_batches(1852)
        flat=[i for b in batches for i in b]
        self.assertEqual(len(flat),1852); self.assertEqual(set(flat),set(range(1852)))
        self.assertEqual(batches,epoch_batches(1852))
        self.assertEqual(flat[:100]+[i for b in batches[50:] for i in b],flat)

    def test_neural_guard_errors_not_hidden_by_runtime(self):
        row=next(r for r in self.rows if r['target']['status']=='out_of_scope')
        scores=score_prediction(row,'{"status":"ready"}')
        self.assertFalse(scores['raw_plan_correct']); self.assertTrue(scores['runtime_correct'])
        report=aggregate([{'reference_status':row['target']['status'],'scores':scores}])
        self.assertEqual(report['raw_guard_plan_accuracy'],0)
        self.assertEqual(report['runtime_correct_rate'],1)
        self.assertIsNone(report['runtime_answer_accuracy_when_answered'])

    def test_truncated_output_not_correct_even_if_json_parses(self):
        row=next(r for r in self.rows if r['target']['status']=='ready')
        scores=score_prediction(row,json.dumps(row['target']),truncated=True)
        self.assertFalse(scores['raw_plan_correct']); self.assertFalse(scores['runtime_answered'])

if __name__=='__main__': unittest.main()

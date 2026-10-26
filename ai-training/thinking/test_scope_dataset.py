import json
import hashlib
from pathlib import Path
import tempfile
import unittest
import scope_contract as sc
import scope_dataset as sd

class ScopeDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.rows=sd.build()

    def test_all_rows_exact_oracle_and_source_spans(self):
        sd.validate(self.rows)
        self.assertTrue(all(r['human_verified'] is False for r in self.rows))

    def test_family_and_paraphrase_splits(self):
        groups={s:{r['split_group_id'] for r in self.rows if r['split']==s} for s in ('train','val','test')}
        self.assertFalse(groups['train']&groups['val']); self.assertFalse(groups['train']&groups['test'])
        self.assertFalse(groups['val']&groups['test'])
        for row in self.rows:
            if row['target']['status']=='ready':
                self.assertIn(row['variant'],range(4) if row['split']=='train' else range(4,6) if row['split']=='val' else range(6,8))

    def test_guard_in_every_split(self):
        for split in ('train','val','test'):
            self.assertEqual({r['target']['status'] for r in self.rows if r['split']==split},
                             {'ready','need_clarification','out_of_scope','unsupported_input'})

    def test_report_and_training_serialization(self):
        with tempfile.TemporaryDirectory() as folder:
            report=sd.export(folder)
            self.assertEqual(report['rows'],len(self.rows))
            for split in ('train','val','test'):
                self.assertEqual(hashlib.sha256((Path(folder)/(split+'.jsonl')).read_bytes()).hexdigest(),report['fingerprints'][split])
                records=[json.loads(s) for s in (Path(folder)/(split+'.sft.jsonl')).read_text(encoding='utf-8').splitlines()]
                for r in records:
                    user=json.loads(r['messages'][1]['content'])
                    self.assertNotIn('source_contract',user)
                    self.assertFalse(any('role' in f for f in user['source_facts']))
                    self.assertTrue(sc.verify_plan(user['problem'],user['grade'],r['messages'][2]['content'])['accepted'])

    def test_deterministic_build(self): self.assertEqual(self.rows,sd.build())

if __name__=='__main__': unittest.main()

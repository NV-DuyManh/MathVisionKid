import json
from pathlib import Path
import tempfile
import unittest
from source_inventory import inventory

class SourceInventoryTests(unittest.TestCase):
    def test_reads_beyond_sample_and_does_not_promote_ocr(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); rows=[{'text':'OCR only'} for _ in range(105)]
            rows += [{'problem':'P','solution':'S','expected_answer':0,'human_verified':False},
                     {'problem':'P2','solution':'S2','expected_answer':'2','human_verified':True}]
            (root/'input.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows)+'broken json\n',encoding='utf-8')
            report=inventory([root,root/'missing'],root/'report.json')
            item=report['files'][0]
            self.assertTrue(item['complete_scan']); self.assertEqual(item['rows'],108)
            self.assertEqual(item['ocr_text_rows'],105)
            self.assertEqual(item['explicit_solution_candidates'],2)
            self.assertEqual(item['human_verified_solution_candidates'],1)
            self.assertEqual(item['json_errors'],1)
            self.assertFalse(report['files'][1]['exists'])

if __name__=='__main__': unittest.main()

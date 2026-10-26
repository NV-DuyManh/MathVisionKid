"""Actual viewed G2V2 page receipts; no automatic content inference."""
from pathlib import Path
import json,hashlib
OUT=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019/g2v2_audit'
def record(entries):
 urls=json.loads((OUT/'urls.json').read_text('utf-8-sig')); p=OUT/'page_review.jsonl'
 old=[json.loads(x) for x in p.read_text('utf-8').splitlines()] if p.exists() else []
 for idx,types,gaps,uncertainty in entries:
  assert idx not in {r['array_index'] for r in old}
  img=OUT/f'index_{idx}.png'; raw=img.read_bytes(); page=idx+1 if idx>=3 else None
  r=dict(grade=2,volume=2,array_index=idx,printed_page=page,official_url=urls[idx],sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),review='ACTUAL_FULL_PAGE_IMAGE_VIEWED',exercise_types=types,gap_ids=gaps,uncertainty=uncertainty,covered_ids=[],coverage_status='MAPPING_PENDING_ACTUAL_SOURCE_COMPARISON',modality_limit='Text-described analogue does not certify visual or physical task competence.')
  with p.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
  assert json.loads(p.read_text('utf-8').splitlines()[-1])==r
  assert img.resolve().parent==OUT.resolve();img.unlink();old.append(r)
 (OUT/'summary.json').write_text(json.dumps(dict(status='IN_PROGRESS',pages_actually_viewed=len(old),content_pages=[r['printed_page'] for r in old if r['printed_page']],all_pages_claim=False,new_cases_authored=0,page_review_sha256=hashlib.sha256(p.read_bytes()).hexdigest()),ensure_ascii=False,indent=2),'utf-8')
 print('receipts',len(old))
if __name__=='__main__':
 import sys;record(json.loads(sys.argv[1]))

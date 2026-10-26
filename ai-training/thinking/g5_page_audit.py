"""Bounded page audit receipts. Notes supplied only after actual page viewing."""
from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019'
OUT=ROOT/'g5_audit';OUT.mkdir(exist_ok=True)
def j(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def sha(x):return hashlib.sha256(x).hexdigest()
def record(vol,entries):
 urls=json.loads((OUT/f'v{vol}_urls.json').read_text('utf-8-sig'))
 catalog=json.loads((ROOT/'prior_append/data/sgk_g5_catalog.json').read_text('utf-8'))
 p=OUT/'page_review.jsonl';old=[json.loads(x) for x in p.read_text('utf-8').splitlines()] if p.exists() else []
 seen={(r['volume'],r['printed_page']) for r in old}
 for page,types,uncertainty,gaps in entries:
  assert (vol,page) not in seen,(vol,page)
  image=OUT/f'v{vol}_p{page}.png';raw=image.read_bytes()
  lesson=next(l for l in catalog['lessons'] if l['volume']==vol and l['printed_start_page']<=page<=l['printed_end_page_bound'])
  r={'grade':5,'volume':vol,'printed_page':page,'official_url':urls[page+1],'sha256':sha(raw),'bytes':len(raw),'review':'ACTUAL_FULL_PAGE_IMAGE_VIEWED','exercise_types':types,'nearest_family_source_refs':lesson['existing_source_examples'],'covered_ids':[],'coverage_status':'PAGE_READ_MAPPING_PENDING_TARGETED_CONTENT_COMPARISON','gap_ids':gaps,'uncertainty':uncertainty,'source_lesson':lesson['lesson_number'],'modality_limit':'Image/physical task coverage evaluated separately from mathematical type; text-described analogues do not certify visual/physical competence.'}
  with p.open('a',encoding='utf-8',newline='\n') as f:f.write(j(r)+'\n')
  # Confirm committed receipt before bounded temporary page-image deletion.
  actual=json.loads(p.read_text('utf-8').splitlines()[-1]);assert actual==r
  absolute=image.resolve();assert absolute.parent==OUT.resolve() and absolute.suffix=='.png';image.unlink()
 rows=[json.loads(x) for x in p.read_text('utf-8').splitlines()]
 summary={'status':'IN_PROGRESS','pages_actually_viewed':len(rows),'volume1_pages':sorted(r['printed_page'] for r in rows if r['volume']==1),'volume2_pages':sorted(r['printed_page'] for r in rows if r['volume']==2),'page_review_sha256':sha(p.read_bytes()),'all_pages_claim':False,'new_cases_authored':0,'pending':'Continue actual reading then semantic mapping to current source; no gap treated proven solely from keywords.'}
 (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf-8')
 print(len(rows),'page receipts saved; viewed images deleted after receipt')
if __name__=='__main__':record(int(sys.argv[1]),json.loads(sys.argv[2]))

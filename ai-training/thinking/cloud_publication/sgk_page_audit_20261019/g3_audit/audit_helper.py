import json,hashlib, pathlib,sys
ROOT=pathlib.Path(__file__).parent
SOURCE=ROOT.parent/'current_sources.jsonl'
ROWS={}
for raw in SOURCE.read_bytes().splitlines():
 r=json.loads(raw)
 if r.get('split','train') != 'train' or any(w in str(r.get('sample_id','')).lower() for w in ['holdout','eval','pilot','protected']): continue
 ROWS[r['sample_id']]=(r,hashlib.sha256(raw).hexdigest())
TOPICS={r.get('topic'):i for i,(r,h) in ROWS.items()}
def record(book, notes):
 manifest=json.loads((ROOT/(book+'_pages.json')).read_text(encoding='utf-8-sig'))
 out=ROOT/'page_review.jsonl'; prior=[json.loads(l) for l in out.read_text(encoding='utf8').splitlines()] if out.exists() else []
 seen={(r['book_id'],r['printed_page']) for r in prior}
 for page,types,topics,limits in notes:
  assert (book,page) not in seen
  image=ROOT/'cache'/f'{book}_{page}.png'; raw=image.read_bytes()
  ids=[TOPICS[t] for t in topics if t in TOPICS]
  proofs=[]
  for i in ids:
   r,h=ROWS[i]; proofs.append({'sample_id':i,'source_row_sha256':h,'problem':r.get('problem'),'requested_quantity':r.get('requested_quantity'),'worked_steps':r.get('worked_steps'),'expected_answer':r.get('expected_answer')})
  row={'book_id':book,'reader_url':manifest['reader_url'],'array_position_1based':page,'printed_page':page,'public_image_url':manifest['pages'][page-1],'image_sha256':hashlib.sha256(raw).hexdigest(),'image_bytes':len(raw),'review_basis':'ACTUAL_PAGE_IMAGE_VISUALLY_READ','exercise_types':types,'covered_ids':ids,'source_comparisons':proofs,'gap_ids':[],'uncertainty':limits,'scope':'Math reasoning coverage comparison; no claim pixel/physical modality trained'}
  with out.open('a',encoding='utf8',newline='') as f:f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
  image.unlink()
 print('Recorded',book,len(notes),'pages; cached',len(list((ROOT/'cache').glob('*.png'))))

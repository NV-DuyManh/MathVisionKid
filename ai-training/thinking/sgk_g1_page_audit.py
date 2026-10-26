"""Bounded public publisher page audit helper; never authors data or trains."""
from pathlib import Path
import urllib.request,json,hashlib,argparse,concurrent.futures

ROOT=Path(__file__).parent/'cloud_publication/sgk_page_audit_20261019'
OWN=ROOT/'g1v1_audit'
def books():return json.loads((ROOT/'prior_append/data/g12_official_pages.json').read_text('utf-8'))
def download(start,end,volume=1,grade=1):
 assert 1<=start<=end and end-start<12
 own=ROOT/f'g{grade}v{volume}_audit';temp=own/'temp';temp.mkdir(parents=True,exist_ok=True)
 assert not list(temp.glob('*.png')),'Finish review and cleanup prior batch first'
 book=next(x for x in books() if x['grade']==grade and x['volume']==volume)
 entries=[]
 for page in range(start,end+1):
  u=book['page_urls'][page-1];p=temp/f'p{page:03d}.png'
  urllib.request.urlretrieve(u,p)
  entries.append({'printed_page':page,'publisher_page_url':u,'source_image_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'image_bytes':p.stat().st_size,'local_temp_path':str(p)})
 assert sum(x['image_bytes'] for x in entries)<25*1024*1024
 (own/'batch_pending.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'pages':[x['printed_page'] for x in entries],'bytes':sum(x['image_bytes'] for x in entries)},ensure_ascii=False))
def record(annotations,volume=1,grade=1):
 own=ROOT/f'g{grade}v{volume}_audit';pending=json.loads((own/'batch_pending.json').read_text('utf-8'));a=json.loads(Path(annotations).read_text('utf-8'))
 assert {x['printed_page'] for x in pending}=={int(k) for k in a}
 dest=own/'page_review.jsonl';existing=[json.loads(l) for l in dest.read_text('utf-8').splitlines()] if dest.exists() else []
 assert not ({x['printed_page'] for x in pending}&{x['printed_page'] for x in existing})
 with dest.open('a',encoding='utf-8',newline='\n') as f:
  for e in pending:
   p=Path(e.pop('local_temp_path'));assert p.resolve().parent==(own/'temp').resolve()
   assert hashlib.sha256(p.read_bytes()).hexdigest()==e['source_image_sha256']
   e.update(grade=grade,volume=volume,evidence_level='ACTUAL_PUBLIC_PUBLISHER_IMAGE_VIEWED',**a[str(e['printed_page'])])
   f.write(json.dumps(e,ensure_ascii=False,sort_keys=True)+'\n');f.flush()
 for e in pending:
  p=own/'temp'/f"p{e['printed_page']:03d}.png";p.unlink()
 (own/'batch_pending.json').unlink()
 print(json.dumps({'recorded_pages':len(pending),'total_actual_viewed':len(existing)+len(pending),'temporary_images_remaining':len(list((own/'temp').glob('*.png')))}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['download','record']);p.add_argument('--start',type=int);p.add_argument('--end',type=int);p.add_argument('--volume',type=int,default=1);p.add_argument('--grade',type=int,default=1);p.add_argument('--annotations');a=p.parse_args()
 if a.mode=='download':download(a.start,a.end,a.volume,a.grade)
 else:record(a.annotations,a.volume,a.grade)

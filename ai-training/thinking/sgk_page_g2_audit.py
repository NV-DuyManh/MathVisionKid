"""Records only actual page images visually inspected by root, then removes cache."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parent/'cloud_publication/sgk_page_audit_20261019'
P=ROOT/'g2v1_audit'
def record(items):
    urls=json.loads((P/'pages.json').read_text(encoding='utf-8'))['page_urls']
    dest=P/'page_review.jsonl'
    old=[json.loads(l) for l in dest.read_bytes().splitlines()] if dest.exists() else []
    seen={r['array_index'] for r in old}
    fresh=[]
    for index,page,role,types,candidates in items:
        if index in seen:continue
        path=P/f'index_{index}.png';data=path.read_bytes()
        fresh.append(dict(book_id='g2v1',grade=2,volume=1,array_index=index,printed_page=page,page_role=role,
          image_url=urls[index],image_sha256=hashlib.sha256(data).hexdigest(),image_bytes=len(data),
          actual_visual_page_read=True,printed_footer_verified=page is not None,exercise_types=types,
          gap_candidates=candidates,semantic_mapping_status='TARGETED_FULL_FIELD_SOURCE_COMPARISON_PENDING',
          text_analogue_is_not_vision_coverage=True,reviewer='ROOT'))
    with dest.open('a',encoding='utf-8',newline='\n') as f:
        for r in fresh:f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n')
    for r in fresh:(P/f"index_{r['array_index']}.png").unlink()
    allrows=old+fresh
    summary=dict(actual_images_read=len(allrows),content_pages_read=sum(r['page_role']=='CONTENT' for r in allrows),
     last_reviewed_indices=[r['array_index'] for r in fresh],all_content_read=False)
    (P/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary))
if __name__=='__main__':record(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))

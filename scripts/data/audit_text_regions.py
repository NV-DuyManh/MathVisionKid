"""Audit the actual local segmentation path on an immutable private Drive batch."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

import cv2
import numpy as np
from PIL import Image,ImageOps,ImageDraw

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ai/runtime'))
from app.api.ocr import detect_text_lines
from app.api.generalized_pipeline import clear_detection_cache
from app.recognition.text_detector import MODEL_PATH
from drive_line_batch import open_ledger, write_json


def run(folder,max_regions,mark_tested=False,force=False):
    selection=json.loads((folder/'source_selection.json').read_text(encoding='utf-8'))
    out=folder/'local_regions';out.mkdir(exist_ok=True)
    overlays=folder/'local_overlays';overlays.mkdir(exist_ok=True)
    sources=['app/api/ocr.py','app/api/generalized.py','app/api/generalized_pipeline.py',
             'app/recognition/text_detector.py','app/tutoring/rows.py']
    hashes={name:hashlib.sha256((ROOT/'ai/runtime'/name).read_bytes()).hexdigest() for name in sources}
    hashes['model']=hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest() if MODEL_PATH.exists() else 'absent'
    records=[];cv2.setNumThreads(1);reused=0
    ledger=open_ledger(folder.parent) if mark_tested else None
    for index,item in enumerate(selection,1):
        path=folder/'images'/f"{item['drive_id']}.jpg"
        record={**item,'index':index,'source_hashes':hashes,'max_regions':max_regions,
                'labels_verified':False,'cloud_calls':0,'training_performed':False}
        try:
            raw=path.read_bytes();record['sha256']=hashlib.sha256(raw).hexdigest()
            if item.get('sha256') and item['sha256']!=record['sha256']:
                raise ValueError('Original differs from frozen selection')
            with Image.open(path) as source:im=ImageOps.exif_transpose(source).convert('RGB')
            pixels=cv2.cvtColor(np.asarray(im),cv2.COLOR_RGB2BGR)
            output=out/f"{item['drive_id']}.json"
            old=json.loads(output.read_text(encoding='utf-8')) if output.exists() else {}
            reusable=(not force and old.get('status')=='tested' and old.get('sha256')==record['sha256']
                      and old.get('source_hashes')==hashes and old.get('max_regions')==max_regions)
            if reusable:
                boxes=old['boxes'];diag=old['diagnostics'];duration=old['latency_ms'];reused+=1
            else:
                start=time.perf_counter()
                lines,diag=detect_text_lines(pixels,max_lines=max_regions,request_id=f'private-batch-{index}')
                boxes=[(b.x,b.y,b.x+b.width,b.y+b.height) for b in lines]
                duration=round((time.perf_counter()-start)*1000,2)
            if not all(0<=x1<x2<=im.width and 0<=y1<y2<=im.height for x1,y1,x2,y2 in boxes):
                raise ValueError('Out of source bounds')
            record.update(status='tested',boxes=boxes,image_size=im.size,diagnostics=diag,
                          latency_ms=duration,pixel_sha256=hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest())
            label=folder/'labels'/f"{item['drive_id']}.json"
            draft=json.loads(label.read_text(encoding='utf-8')) if label.exists() else {}
            if not draft or (draft.get('review_status')=='needs_review' and draft.get('sha256')==record['sha256']):
                write_json(label,{**draft,'drive_id':item['drive_id'],'sha256':record['sha256'],
                                 'review_status':'needs_review','line_count':None,'draft_boxes':boxes,
                                 'prediction_hashes':hashes,'training_eligible':False,'lines':[]})
            w,h=im.size;im.thumbnail((1000,1400));draw=ImageDraw.Draw(im)
            for number,(x1,y1,x2,y2) in enumerate(boxes,1):
                rect=(x1*im.width/w,y1*im.height/h,x2*im.width/w,y2*im.height/h)
                draw.rectangle(rect,outline='#c52385',width=2);draw.text(rect[:2],str(number),fill='#c52385')
            im.save(overlays/f'{index:03}.jpg')
        except (OSError,ValueError,cv2.error) as exc:
            record.update(status='execution_failed',error_type=type(exc).__name__)
        clear_detection_cache()
        write_json(out/f"{item['drive_id']}.json",record)
        if ledger is not None and record['status']=='tested':
            # Persist successful evidence first. Accepted labels and first-test
            # provenance in existing ledger rows remain unchanged.
            ledger.execute('INSERT OR IGNORE INTO images VALUES (?,?,?,?,?,?,?,?)',
                (item['drive_id'],record['sha256'],record['pixel_sha256'],item['name'],item['source_group'],
                 folder.name,datetime.now(timezone.utc).isoformat(),'needs_review'))
            ledger.commit()
        records.append(record)
        if index%50==0:print(f'{index}/{len(selection)} saved',flush=True)
    if ledger is not None:ledger.close()
    tested=[r for r in records if r['status']=='tested']
    summary={'selected':len(selection),'tested':len(tested),'execution_failed':len(records)-len(tested),
             'with_regions':sum(bool(r['boxes']) for r in tested),
             'empty_indices':[r['index'] for r in tested if not r['boxes']],
             'limit_exceeded_indices':[r['index'] for r in tested if r['diagnostics'].get('region_limit_exceeded')],
             'p95_ms':round(float(np.percentile([r['latency_ms'] for r in tested],95)),2) if tested else None,
             'source_hashes':hashes,'verified_accuracy':False,'training_performed':False,
             'reused_results':reused,'marked_tested':mark_tested}
    (folder/'local_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    with (folder/'local_manifest.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['index','source_key','name','sha256','status','regions','latency_ms','needs_review'])
        for r in records:writer.writerow([r['index'],r['drive_id'],r['name'],r.get('sha256'),r['status'],len(r.get('boxes',[])),r.get('latency_ms'),True])
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--batch',required=True)
    parser.add_argument('--max-regions',type=int,default=200)
    parser.add_argument('--mark-tested',action='store_true')
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args()
    if not 1<=args.max_regions<=500:parser.error('max-regions must be between 1 and 500')
    folder=(ROOT/'ai-training/datasets/drive_math'/args.batch).resolve()
    if not folder.is_relative_to((ROOT/'ai-training/datasets/drive_math').resolve()):parser.error('batch must remain in private dataset directory')
    run(folder,args.max_regions,args.mark_tested,args.force)

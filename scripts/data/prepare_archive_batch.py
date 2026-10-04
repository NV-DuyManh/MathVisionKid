"""Select every unseen original crop in the owner's downloaded archive."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

from PIL import Image, ImageOps

from drive_line_batch import DEFAULT_DATA, open_ledger, write_json


def prepare(data, batch):
    folder=(data/batch).resolve()
    if not folder.is_relative_to(data.resolve()):
        raise ValueError('Batch must remain inside the private dataset directory')
    if (folder/'source_selection.json').exists():
        raise ValueError('Selection is already frozen; reuse it without reselection')
    archive=data/'archives/dataset_clean_full.zip'
    meta=json.loads(archive.with_suffix('.inventory.json').read_text(encoding='utf-8'))
    # Stream the large artifact rather than reading the whole archive into RAM.
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=meta['sha256']:
            raise ValueError('Archive changed since acquisition')
    with open_ledger(data) as db:
        seen_ids={r[0] for r in db.execute('SELECT drive_id FROM images')}
        seen_pixels={r[0] for r in db.execute('SELECT pixel_sha256 FROM images')}
    images=folder/'images';images.mkdir(parents=True,exist_ok=True)
    selected=[];excluded=[];failed=[]
    with zipfile.ZipFile(archive) as zipped:
        rows=list(csv.DictReader(io.StringIO(zipped.read('content/dataset_clean/labels.csv').decode('utf-8-sig'))))
        by_entry={'content/dataset_clean/'+row['crop_path']:row for row in rows}
        if any(not entry.startswith('content/dataset_clean/crops/') for entry in by_entry):
            raise ValueError('Label references a non-crop archive entry')
        entries=sorted(info.filename for info in zipped.infolist()
                       if info.filename.startswith('content/dataset_clean/crops/')
                       and Path(info.filename).suffix.lower() in {'.png','.jpg','.jpeg','.webp','.bmp'})
        debug_count=sum('/debug_vis/' in info.filename and not info.is_dir() for info in zipped.infolist())
        for index,entry in enumerate(entries,1):
            row=by_entry.get(entry);name=Path(entry).name
            key='zip_'+meta['drive_id']+'_'+hashlib.sha256(entry.encode()).hexdigest()[:20]
            if key in seen_ids:
                excluded.append({'drive_id':key,'archive_entry':entry,'reason':'already_tested_id'})
                continue
            try:
                raw=zipped.read(entry)
                with Image.open(io.BytesIO(raw)) as source:
                    im=ImageOps.exif_transpose(source).convert('RGB')
                pixel_hash=hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
                if pixel_hash in seen_pixels:
                    excluded.append({'drive_id':key,'archive_entry':entry,'reason':'duplicate_pixels'})
                    continue
                seen_pixels.add(pixel_hash);seen_ids.add(key)
                record={'drive_id':key,'name':name,'source_group':'dataset_clean/crops',
                        'source_type':'provided_line_crop','archive_drive_id':meta['drive_id'],
                        'archive_sha256':meta['sha256'],'archive_entry':entry,
                        'parent_page_name':name.rsplit('_line_',1)[0],
                        'sha256':hashlib.sha256(raw).hexdigest(),'pixel_sha256':pixel_hash}
                (images/f'{key}.jpg').write_bytes(raw)
                if row is not None:
                    write_json(folder/'imported_labels'/f'{key}.json',{
                        'source_file':'content/dataset_clean/labels.csv','archive_sha256':meta['sha256'],
                        'image_sha256':record['sha256'],'provided_text':row['label'],
                        'review_status':'unverified_source_label','training_eligible':False})
                selected.append(record)
            except (OSError,KeyError,zipfile.BadZipFile) as exc:
                failed.append({'drive_id':key,'archive_entry':entry,'error_type':type(exc).__name__})
            if index%200==0:print(f'{index}/{len(entries)} inspected',flush=True)
    write_json(folder/'source_selection.json',selected)
    audit={'archive_image_crops':len(entries),'selected':len(selected),'excluded':excluded,
           'decode_failures':failed,'debug_derivatives_excluded':debug_count,'training_performed':False}
    write_json(folder/'selection_audit.json',audit)
    print(json.dumps({k:(len(v) if isinstance(v,list) else v) for k,v in audit.items()},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--batch',required=True)
    args=parser.parse_args();prepare(DEFAULT_DATA,args.batch)

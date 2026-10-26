import json,pathlib,gzip,zipfile,io
from googleapiclient.discovery import build
import google.auth
creds,_=google.auth.default();budget_drive=build('drive','v3',credentials=creds,cache_discovery=False)
from math_data_drive_bootstrap import GoogleDriveReader
reader=GoogleDriveReader(budget_drive)
metadata=json.loads((budget_root/'sampling_metadata_inventory.json').read_bytes())
with zipfile.ZipFile('/content/mathvisionkid_full_text_training/published_progress.zip') as z:
    ready=json.loads(z.read('full_text_training_release_20261023/release_manifest.json'))
    recipe=json.loads(z.read(ready['recipe_pointer']['member']))
cache=budget_root/'payloads';cache.mkdir(exist_ok=True)
rows=[]
first=recipe['chat_members'][0]
path=next(pathlib.Path('/content/mathvisionkid_full_text_training/payload_cache').glob('*.gz'))
with gzip.open(path,'rt',encoding='utf8') as f:
    for _ in range(2):rows.append({'kind':'chat','raw':json.loads(next(f))})
small=next(e for e in recipe['source_members'] if e['family']=='sgk_gap_20261019')
ref=recipe['artifacts'][small['sha256']];data=reader.read(ref['file_ids'][0],ref['bytes'])
import hashlib
assert hashlib.sha256(data).hexdigest()==small['sha256']
(cache/(small['sha256']+'.zip')).write_bytes(data)
with zipfile.ZipFile(io.BytesIO(data)) as z:
    with z.open(small['member']) as f:rows.append({'kind':'source','raw':json.loads(next(f))})
out={'source_reference':small,'rows':rows}
(budget_root/'train_schema_probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False))

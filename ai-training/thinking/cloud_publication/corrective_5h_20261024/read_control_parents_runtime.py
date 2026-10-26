import pathlib,json,hashlib,time
from googleapiclient.discovery import build
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
controls_api=build('drive','v3',credentials=repair_credentials,cache_discovery=False)
parents_dir=root5/'control_parents';parents_dir.mkdir(exist_ok=True)
refs={}
ids={'progress':'1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX','chat':'1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6','context':'13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9','state':'1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme'}
for kind,fid in ids.items():
 meta=controls_api.files().get(fileId=fid,fields='id,name,size').execute();time.sleep(1.25)
 assert 0<int(meta['size'])<32*1024*1024
 raw=controls_api.files().get_media(fileId=fid).execute();time.sleep(1.25)
 assert len(raw)==int(meta['size'])
 ext={'progress':'.zip','chat':'.json','context':'.md','state':'.json'}[kind]
 path=parents_dir/('parent_'+kind+ext);path.write_bytes(raw)
 refs[kind]={'id':fid,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'path':str(path),'fresh_raw_readback_verified':True}
(parents_dir/'parent_controls_raw_verified.json').write_text(json.dumps(refs,indent=2))
print(json.dumps({'parents':refs,'corpus_or_model_downloaded_to_PC':False}))

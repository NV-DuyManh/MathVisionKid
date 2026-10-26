import pathlib,json,hashlib,gzip,io
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
root5.mkdir(exist_ok=True)
pins=[('selected_view.jsonl.gz','1Twd75htZfKKSKvjJ4j4imAu_sca7UJ1c','319dfddf43e1ad63878e52b1e5f34a5d276a1e557257ea7b4c33dcfe790200e9'),('sampling_manifest.json','1kqDGkAEHuhgRtCQqejjfVfvGHzvEeGlr','444db8845af0c12bb528795b7e441b996571960dd58ab6898eb9394c77031545')]
for name,fid,pin in pins:
 p=root5/name
 if not p.exists():p.write_bytes(repair_drive.files().get_media(fileId=fid).execute())
 assert hashlib.sha256(p.read_bytes()).hexdigest()==pin,name
view=gzip.decompress((root5/'selected_view.jsonl.gz').read_bytes())
assert hashlib.sha256(view).hexdigest()=='14929ba64e5c94d812f1fc3804c771ca8e41fa92285aed3a925282c39b1e4331'
(root5/'training_view.jsonl').write_bytes(view)
rows=[json.loads(l) for l in view.splitlines()]
from collections import Counter
assert len(rows)==16000 and len({r['sample_id'] for r in rows})==16000
out={'rows':len(rows),'modes':dict(Counter(r['mode'] for r in rows)),'system_hash_counts':dict(Counter(hashlib.sha256(r['messages'][0]['content'].encode()).hexdigest() for r in rows)),'examples':[],'assistant_json_duplicates':[]}
def detect_duplicates(pairs):
 d={};dups=[]
 for k,v in pairs:
  if k in d:dups.append(k)
  d[k]=v
 if dups:raise ValueError('duplicate_json_keys:'+','.join(dups))
 return d
for r in rows:
 try:json.loads(r['messages'][-1]['content'],object_pairs_hook=detect_duplicates)
 except Exception as e:
  if 'duplicate_json_keys' in str(e):out['assistant_json_duplicates'].append(r['sample_id'])
families=['exhaustive_v1_sub_','fraction_v1_','decimal_v1_','primary_','sgk_']
for prefix in families:
 q=[r for r in rows if r['sample_id'].startswith(prefix) and r['mode']=='worked_solution']
 if q:out['examples'].append(q[0])
out['assistant_target_hash_repetition_top']=Counter(hashlib.sha256(r['messages'][-1]['content'].encode()).hexdigest() for r in rows).most_common(5)
(root5/'selected_view_structural_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))

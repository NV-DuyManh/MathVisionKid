from pathlib import Path
import json,base64,gzip
p=Path(__file__).parent;r=json.loads((p/'bootstrap_receipt.json').read_bytes());v=r.get('result') or r.get('structured_content') or r.get('data')
text=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in v['outputs'])
d=json.loads(gzip.decompress(base64.b64decode(text.split('NEW_SCOPE_INVENTORY_GZIP_BASE64:',1)[1].split()[0])))
for name,key in [('owner_run_scope.json','scope'),('source_inventory.json','inventory')]:
 b=(json.dumps(d[key],ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();q=p/name
 if q.exists():assert q.read_bytes()==b
 else:q.write_bytes(b)
print(json.dumps({'scope':d['scope'],'source_rows':d['inventory']['source_rows'],'behaviors':d['inventory']['behavior_counts'],'group_count':len(d['inventory']['groups']),'schemas':d['inventory']['row_schemas'],'examples':d['inventory']['bounded_schema_examples']},ensure_ascii=False))

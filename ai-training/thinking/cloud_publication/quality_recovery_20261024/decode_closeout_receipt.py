from pathlib import Path
import sys,json,base64,gzip,hashlib
p=Path(__file__).parent;r=json.loads(Path(sys.argv[1]).read_bytes());v=r.get('result') or r.get('structured_content') or r.get('data')
text=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in v['outputs'])
bundle=json.loads(gzip.decompress(base64.b64decode(text.split('META_BUNDLE_GZIP_BASE64:',1)[1].split()[0])))
label=sys.argv[2] if len(sys.argv)>2 else 'captured';d=p/('metadata_'+label);d.mkdir(exist_ok=True)
for n,v in bundle['files'].items():
 b=base64.b64decode(v);assert hashlib.sha256(b).hexdigest()==bundle['hashes'][n]
 (d/n.replace('/','__')).write_bytes(b)
print(json.dumps({'dest':str(d),'files':list(bundle['files']),'hashes':bundle['hashes']}))

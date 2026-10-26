import pathlib,json,hashlib,base64,gzip,sys
p=pathlib.Path(__file__).parent
r=json.loads(pathlib.Path(sys.argv[1]).read_bytes());v=r.get('result')or r.get('structured_content')or r.get('data')
t=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in v['outputs'])
b=json.loads(gzip.decompress(base64.b64decode(t.split('METADATA_GZIP_BASE64:',1)[1].split()[0])))
d=p/sys.argv[2];d.mkdir(exist_ok=False)
for n,enc in b['files'].items():
 raw=base64.b64decode(enc);assert hashlib.sha256(raw).hexdigest()==b['hashes'][n]
 (d/n.replace('/','__')).write_bytes(raw)
(d/'captured_hashes.json').write_text(json.dumps(b['hashes'],indent=2)+'\n',encoding='utf8')
print(json.dumps({'metadata_count':len(b['files']),'dest':str(d),'hashes_verified':True}))

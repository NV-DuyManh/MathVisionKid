import pathlib,json,base64,gzip,hashlib
r=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
status=json.loads((r/'four_controls_publication_status.json').read_bytes())
assert status['state']=='COMPLETE_RAW_VERIFIED','Four controls not complete; do not claim sync'
names=['four_controls_publication_status.json','four_controls_verified_manifest.json']
files={n:(r/n).read_bytes() for n in names}
proof={'files':{n:base64.b64encode(b).decode() for n,b in files.items()},'hashes':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()}}
print('CONTROL_RAW_RECEIPT:'+base64.b64encode(gzip.compress(json.dumps(proof).encode())).decode())

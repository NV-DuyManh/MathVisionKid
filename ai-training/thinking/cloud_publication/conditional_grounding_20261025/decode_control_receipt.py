from pathlib import Path
import json,hashlib,base64,gzip
P=Path(__file__).parent
receipt=json.loads((P/'control_raw_receipt_capture.json').read_bytes())
value=receipt['result']
text=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in value['outputs'] if x.get('output_type')=='stream')
payload=json.loads(gzip.decompress(base64.b64decode(text.split('CONTROL_RAW_RECEIPT:',1)[1].split()[0])))
folder=P/'control_phase_verified';folder.mkdir(exist_ok=False)
for name,encoded in payload['files'].items():
 assert Path(name).name==name
 raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==payload['hashes'][name]
 (folder/name).write_bytes(raw)
status=json.loads((folder/'four_controls_publication_status.json').read_bytes())
assert status['state']=='COMPLETE_RAW_VERIFIED'
print(json.dumps({'state':status['state'],'context_sha256':status['canonical_context_sha256'],
 'receipt_sha256':hashlib.sha256((folder/'four_controls_verified_manifest.json').read_bytes()).hexdigest(),
 'verified_control_kinds':[x['kind'] for x in status['receipt']['verified_writes']]}))

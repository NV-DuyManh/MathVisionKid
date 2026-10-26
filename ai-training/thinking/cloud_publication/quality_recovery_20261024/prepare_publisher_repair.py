from pathlib import Path
import json,base64,hashlib
p=Path(__file__).parent
old={'publisher_runtime.py':'68fccabc5a0509613fbdec79cbce9a2b220c31674f33d5690477517d69cc60e1','test_recovery_publisher.py':'4ad13712a4488b7554578e6e7eb86ddff9b223c68d304b7757505c65f0fda806','cpu_validation.json':'a426367f62c647f62dbf9b04652e9b59c4189cd6c411ea2c187556849cd0d4e6'}
payload={n:base64.b64encode((p/n).read_bytes()).decode() for n in old}
code='''import pathlib,json,base64,hashlib,importlib.util,sys,threading
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
assert not any(t.name=='MathVisionKidQualityRecoveryPublisher' and t.is_alive() for t in threading.enumerate())
statepath=r/'publication/publication_status.json';state=json.loads(statepath.read_bytes())
assert state['state']=='ERROR' and not state['artifacts'],'Repair applies only before first immutable publication'
old=OLD;payload=PAYLOAD
history=r/'staging_history';history.mkdir(exist_ok=True)
for n,encoded in payload.items():
 f=r/n;b=f.read_bytes();assert hashlib.sha256(b).hexdigest()==old[n],n
 target=history/(n+'.'+old[n]);assert not target.exists();target.write_bytes(b)
 f.write_bytes(base64.b64decode(encoded))
(history/'initial_publication_failure.json').write_bytes(statepath.read_bytes())
spec=importlib.util.spec_from_file_location('qrec_publisher_repaired',r/'publisher_runtime.py');qrec_publisher=importlib.util.module_from_spec(spec);sys.modules[spec.name]=qrec_publisher;spec.loader.exec_module(qrec_publisher)
print(json.dumps(qrec_publisher.start(recovery_credentials)))
'''.replace('OLD',repr(old)).replace('PAYLOAD',repr(payload))
(p/'repair_publication_runtime.py').write_text(code,encoding='utf8')
print(json.dumps({'bytes':len(code.encode()),'new_hashes':{n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in old}}))

from pathlib import Path
import base64,hashlib
p=Path(__file__).parent
sources={n:p/n for n in ['owner_budget_revision_config.json','revised_publisher_contract_v2.py']}
payload={n:base64.b64encode(s.read_bytes()).decode() for n,s in sources.items()}
hashes={n:hashlib.sha256(s.read_bytes()).hexdigest() for n,s in sources.items()}
code='''import pathlib,base64,json,hashlib,importlib.util,sys,time
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
payload=PAYLOAD
hashes=HASHES
for n,v in payload.items():
 b=base64.b64decode(v);assert hashlib.sha256(b).hexdigest()==hashes[n]
 p=root5/n
 if p.exists():assert p.read_bytes()==b,'Preserve existing revision bytes'
 else:p.write_bytes(b)
spec=importlib.util.spec_from_file_location('revised_publisher_contract_v2',root5/'revised_publisher_contract_v2.py')
revised_publisher_contract_v2=importlib.util.module_from_spec(spec);sys.modules[spec.name]=revised_publisher_contract_v2;spec.loader.exec_module(revised_publisher_contract_v2)
result=revised_publisher_contract_v2.install_revised_publication_contract(corrective5h_publisher)
result.update(owner_revision_sha256=hashes['owner_budget_revision_config.json'],installed_unix=time.time(),training_interrupted=False)
(root5/'publisher_contract_revision_manifest.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
'''.replace('PAYLOAD',repr(payload)).replace('HASHES',repr(hashes))
(p/'stage_budget_revision_runtime.py').write_text(code,encoding='utf-8')

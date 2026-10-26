import pathlib,json,base64,gzip,hashlib
from datetime import datetime as prefix_datetime,timezone as prefix_timezone
pr=pathlib.Path('/content/mathvisionkid_recovery_20261026')
ps=json.loads((pr/'cpu_tools_publication_status.json').read_bytes())
assert ps['state']=='COMPLETE_RAW_VERIFIED'
pf=pr/'training/eval_step_000100/adapter_generations.partial.jsonl'
if not pf.exists():pf=pf.with_name('adapter_generations.jsonl')
raw=pf.read_bytes();assert raw.endswith(b'\n')
prefix=raw.splitlines(keepends=True)[:6];assert len(prefix)==6
dev=[json.loads(x) for x in (pr/'new_validation_candidates.jsonl').read_bytes().splitlines()]
base=[json.loads(x) for x in (pr/'training/eval_step_000000/base_generations.jsonl').read_bytes().splitlines()]
candidates=[json.loads(x) for x in prefix]
assert [x['fixture_id'] for x in candidates]==[f['id'] for f in dev[:6]]
proof={'observed_utc':prefix_datetime.now(prefix_timezone.utc).isoformat(),'complete_evaluation':False,'gate_may_be_created':False,
 'completed_prefix_rows':6,'candidate_prefix_raw_sha256':hashlib.sha256(b''.join(prefix)).hexdigest(),
 'pairs':[{'fixture':f,'base':b,'adapter':a} for f,b,a in zip(dev[:6],base[:6],candidates)],'policy_publication_proof':ps}
print('COMPLETED_PREFIX:'+base64.b64encode(gzip.compress(json.dumps(proof,ensure_ascii=False).encode())).decode())

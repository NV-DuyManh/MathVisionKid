from pathlib import Path
import hashlib,json,re
p=Path(__file__).resolve().parent
names=('drive_quota_resilience.py','t4_microbatch_optimization_v3.py')
pins={n:dict(bytes=len((p/n).read_bytes()),sha256=hashlib.sha256((p/n).read_bytes()).hexdigest()) for n in names}
raw=(json.dumps(pins,sort_keys=True,indent=2)+'\n').encode()
(p/'execution_v3_code_hashes.json').write_bytes(raw)
s=(p/'start_full_text_training_optimized_runtime.py').read_text(encoding='utf8')
assert '0205f1fa78bfd2504ad111213433fd0909f6db0f0ce00bf4923254dcbc94ef53' in s
s=s.replace('0205f1fa78bfd2504ad111213433fd0909f6db0f0ce00bf4923254dcbc94ef53',hashlib.sha256(raw).hexdigest())
s=s.replace('execution_optimization_20261023/','execution_adaptive_v3_20261023/').replace('t4_microbatch_optimization_v2','t4_microbatch_optimization_v3')
compile(s,'start_full_text_training_adaptive_v3.py','exec')
(p/'start_full_text_training_adaptive_v3.py').write_text(s,encoding='utf8')
print(json.dumps({'helper_pins':pins,'index_sha256':hashlib.sha256(raw).hexdigest()}))

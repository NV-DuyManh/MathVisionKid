from pathlib import Path
p=Path(__file__).parent;old=p.parent/'verbal_recovery_20261024'
for n in ['decode_dev_receipt.py','assemble_review_gate.py']:
 text=(old/n).read_text(encoding='utf8').replace('mathvisionkid_verbal_recovery_20261024','mathvisionkid_skill_recovery_150m_20261024').replace('import recovery_policy as P','import recovery_policy_v2 as P').replace('import recovery_worker as W','import recovery_worker_v3 as W')
 q=p/n;assert not q.exists();q.write_text(text,encoding='utf8')
for step in [100,300]:
 code=(old/'capture_dev_runtime.py').read_text(encoding='utf8').replace('mathvisionkid_verbal_recovery_20261024','mathvisionkid_skill_recovery_150m_20261024').replace('step=50',f'step={step}')
 code=code.replace("adapter_bytes=(r/(adapter.replace('.jsonl','.partial.jsonl') if partial else adapter)).read_bytes()", "ap=r/(adapter.replace('.jsonl','.partial.jsonl') if partial else adapter)\nadapter_bytes=ap.read_bytes() if ap.exists() else b''")
 q=p/f'capture_dev_{step}_runtime.py';assert not q.exists();q.write_text(code,encoding='utf8')
print('Prepared matched actual-output capture/gate tools for100and300; no runtime calls.')

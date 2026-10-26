import base64
import hashlib
import json
from pathlib import Path
here=Path(__file__).resolve().parent
raw=(here/'data'/'teacher_math_v3'/'knowledge_cards.jsonl').read_bytes()
code='''# MATHVISIONKID — supersede supplementary card typo; no frozen training change
import base64,hashlib
raw=base64.b64decode(PAYLOAD)
assert hashlib.sha256(raw).hexdigest()==EXPECTED
p=MVK_V3_ROOT/'supplementary'/'knowledge_cards.jsonl'
old=p.read_bytes()
if old!=raw:
    assert hashlib.sha256(old).hexdigest()=='b811b0881f220a8d3ab59c091754c6a09e442220004795a4cf5d39ff5f905a58'
    (p.parent/'knowledge_cards_pre_peer_review_snapshot.jsonl').write_bytes(old)
    p.write_bytes(raw)
print('KNOWLEDGE_CARDS_CORRECTED',hashlib.sha256(p.read_bytes()).hexdigest(),'NOT_USED_IN_NUMERIC_V3_TRAINING')
'''.replace('PAYLOAD',repr(base64.b64encode(raw).decode())).replace('EXPECTED',repr(hashlib.sha256(raw).hexdigest()))
dest=here/'evidence'/'teacher_math_v3_20261013'/'card_correction_args.json'
dest.write_text(json.dumps({'cellIndex':64,'language':'python','code':code},ensure_ascii=False),encoding='utf-8')
print(json.dumps({'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}))

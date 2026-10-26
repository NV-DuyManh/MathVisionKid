from pathlib import Path
import json,hashlib,base64
p=Path(__file__).parent;old=p.parent/'quality_recovery_20261024'
workerhash=hashlib.sha256((p/'final_evaluation_worker.py').read_bytes()).hexdigest();pubhash=hashlib.sha256((p/'publisher_runtime.py').read_bytes()).hexdigest()
s=(old/'start_final_evaluation_runtime.py').read_text(encoding='utf8').replace('/content/mathvisionkid_quality_recovery_20261024','/content/mathvisionkid_verbal_recovery_20261024').replace('recovery_process','verbal_process').replace('recovery_final_process','verbal_final_process').replace('recovery_final_publisher','verbal_final_publisher').replace('MathVisionKidRecoveryFinalEvalPublisher','MathVisionKidVerbalFinalEvalPublisher').replace('5d8d7e89e0a31615db2820c99f4074038ea827b0303c94a3685c9517f2380b3e',workerhash).replace('75d85e31a396e97779f06624b66709ece14c770b46d8f2392a1cd68c4dc7c184',pubhash).replace('1ml93i1tx9zzSjEl3gKXx1RmzLYVWK2TJ','18kRud04F04OF34HcI2l9okHYUmzFVY4M')
compile(s,'verbal_final_starter','exec');(p/'start_final_evaluation_runtime.py').write_text(s,encoding='utf8')
# Fresh test code is staged before final selection; the locked20 file remains unread by model until final_eval.
names=['test_final_evaluation_worker.py'];payload={n:base64.b64encode((p/n).read_bytes()).decode() for n in names}
code="import pathlib,base64,json\nr=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024')\nfor n,v in "+repr(payload)+".items():\n b=base64.b64decode(v);f=r/n\n if f.exists():assert f.read_bytes()==b\n else:f.write_bytes(b)\nprint(json.dumps({'test_code_staged':True,'inference_executed':False}))\n"
(p/'stage_final_test_code_runtime.py').write_text(code,encoding='utf8')
print(json.dumps({'final_eval_worker_sha256':workerhash,'publisher_sha256':pubhash}))

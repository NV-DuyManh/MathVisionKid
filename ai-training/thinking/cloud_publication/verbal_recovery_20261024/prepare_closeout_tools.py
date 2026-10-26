from pathlib import Path
import json
p=Path(__file__).parent;old=p.parent/'quality_recovery_20261024'
for name in ['capture_closeout_runtime.py','decode_closeout_receipt.py','capture_final_runtime.py','decode_final_receipt.py','finalize_publication_runtime.py']:
 text=(old/name).read_text(encoding='utf8').replace('mathvisionkid_quality_recovery_20261024','mathvisionkid_verbal_recovery_20261024')
 if name=='capture_final_runtime.py':
  text=text.replace("'training/eval_step_000001/probe_complete.json',",'')
  text=text.replace("'training/eval_step_000001/probe_complete.json',",'')
 if name=='decode_final_receipt.py':
  text=text.replace("outputs=[json.loads", "assert json.loads((d/'training__best.json').read_bytes())['kind']=='untrained_base','Adapt decoder explicitly if selected adapter'\noutputs=[json.loads")
 out=p/name;assert not out.exists(),name;out.write_text(text,encoding='utf8')
print(json.dumps({'prepared':True,'corpus_or_model_downloaded':False}))

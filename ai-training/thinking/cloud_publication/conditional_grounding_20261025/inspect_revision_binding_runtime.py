import pathlib,subprocess,json
r=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
assert conditional_training_process.poll()==1
code="""from transformers import AutoConfig,AutoTokenizer
from transformers.utils.hub import cached_file
from pathlib import Path
import json
m='Qwen/Qwen3-1.7B';rev='70d244cc86ccca08cf5af4e1e306ecf908b1ad5e'
c=AutoConfig.from_pretrained(m,revision=rev);t=AutoTokenizer.from_pretrained(m,revision=rev)
paths={n:cached_file(m,n,revision=rev) for n in ['config.json','tokenizer.json','model.safetensors.index.json']}
print(json.dumps({'model_config_commit_hash':getattr(c,'_commit_hash',None),'tokenizer_eos_id':t.eos_token_id,'tokenizer_commit_hash':t.init_kwargs.get('_commit_hash'),'cached_snapshot_revisions':{n:Path(p).parent.name for n,p in paths.items()},'expected_revision':rev,'model_loaded':False}))
"""
result=subprocess.run([str(r/'venv/bin/python'),'-c',code],capture_output=True,text=True,timeout=45)
print(json.dumps({'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr[-1200:]}))

import pathlib,json,subprocess,gc,time
assert not full_text_training_thread.is_alive()
assert json.loads((budget_root/'pause_receipt.json').read_text())['old_checkpoint']['fresh_raw_readback_verified']
gc.collect()
import torch
torch.cuda.empty_cache()
code='''import os
os.environ['UNSLOTH_DISABLE_AUTO_UPDATES']='1'
import unsloth
from unsloth import FastLanguageModel
import torch,json,time,importlib.metadata as im
from pathlib import Path
p=Path('/content/mathvisionkid_t4_budget_3h_20261023')
assert 'T4' in torch.cuda.get_device_name()
t=time.time()
model,tok=FastLanguageModel.from_pretrained(model_name='Qwen/Qwen3-1.7B',revision='70d244cc86ccca08cf5af4e1e306ecf908b1ad5e',max_seq_length=2048,dtype=torch.float16,load_in_4bit=True,attn_implementation='sdpa')
out={'state':'UNSLOTH_PINNED_BASE_LOADED','gpu':torch.cuda.get_device_name(),'elapsed_seconds':time.time()-t,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'versions':{k:im.version(k) for k in ['unsloth','unsloth-zoo','torch','transformers','peft','bitsandbytes']},'attention':str(getattr(model.config,'_attn_implementation',None))}
(p/'gpu_preflight.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out),flush=True)
'''
(budget_root/'gpu_preflight.py').write_text(code)
budget_preflight_log=(budget_root/'gpu_preflight.log').open('w')
budget_preflight_process=subprocess.Popen([str(budget_root/'venv/bin/python'),str(budget_root/'gpu_preflight.py')],stdout=budget_preflight_log,stderr=subprocess.STDOUT)
print(json.dumps({'state':'UNSLOTH_GPU_PREFLIGHT_STARTED','pid':budget_preflight_process.pid,'old_gpu_allocated_bytes':torch.cuda.memory_allocated()}))

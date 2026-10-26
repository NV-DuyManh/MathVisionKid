import pathlib,subprocess,os,json
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
code='''import pathlib,torch,json
from safetensors import safe_open
r=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024/training_v1_preserved/generation_step_000270_rows_00004320')
s=torch.load(r/'resume_state.pt',map_location='cpu',weights_only=False)
states=s['optimizer']['state'];ids=[pid for g in s['optimizer']['param_groups'] for pid in g['params']]
out={'state_count':len(states),'group_keys':list(s['optimizer']['param_groups'][0]),'first_states':[],'adapter_first_keys':[]}
for pid in ids[:12]:
 item={'id':pid}
 for k,v in states[pid].items():item[k]={'shape':list(v.shape),'numel':v.numel(),'dtype':str(v.dtype)} if isinstance(v,torch.Tensor) else v
 out['first_states'].append(item)
with safe_open(r/'adapter_model.safetensors',framework='pt',device='cpu') as f:
 for k in list(f.keys())[:16]:out['adapter_first_keys'].append({'name':k,'shape':list(f.get_slice(k).get_shape())})
print(json.dumps(out,default=lambda value:{'type':str(type(value)),'shape':list(getattr(value,'shape',[]))}))
'''
env=dict(os.environ);env['CUDA_VISIBLE_DEVICES']=''
result=subprocess.run([str(root5/'venv/bin/python'),'-c',code],capture_output=True,text=True,timeout=40,env=env)
print(result.stdout)
if result.returncode:print(result.stderr[-2500:])

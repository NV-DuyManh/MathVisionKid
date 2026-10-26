import pathlib,subprocess,os
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
env=dict(os.environ);env['CUDA_VISIBLE_DEVICES']=''
code="import bitsandbytes,inspect;from bitsandbytes.optim.optimizer import Optimizer8bit;print(inspect.getsource(Optimizer8bit.load_state_dict));print(inspect.getsource(Optimizer8bit.state_dict))"
result=subprocess.run([str(root5/'venv/bin/python'),'-c',code],capture_output=True,text=True,timeout=40,env=env)
print(result.stdout[-13000:])
if result.returncode:print(result.stderr[-1200:])

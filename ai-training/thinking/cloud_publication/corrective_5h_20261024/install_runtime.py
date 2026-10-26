import pathlib,subprocess,sys,json,threading,time,traceback,os
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
root5.mkdir(exist_ok=True)
assert not globals().get('corrective_install_thread') or not corrective_install_thread.is_alive()
def _install_corrective():
 state={'state':'INSTALLING','started_unix':time.time(),'gpu_allocated_by_installer':False}
 def save():
  p=root5/'install_status.json';t=p.with_suffix('.pending');t.write_text(json.dumps(state,ensure_ascii=False,indent=2));t.replace(p)
 save()
 try:
  actual=json.loads(subprocess.check_output([sys.executable,'-c',"import torch,json;print(json.dumps({'torch':torch.__version__,'cuda':torch.version.cuda}))"],text=True))
  state['base']=actual;save()
  if actual['torch'].split('+')[0]!='2.11.0':raise RuntimeError('Different base Torch version; inspect before installing pinned environment')
  v=root5/'venv'
  with (root5/'install.log').open('a') as log:
   subprocess.run([sys.executable,'-m','venv','--without-pip','--system-site-packages',str(v)],check=True,stdout=log,stderr=subprocess.STDOUT,timeout=90)
   req=root5/'requirements.txt';req.write_text('unsloth[cu130-torch2110]==2026.10.7\nunsloth-zoo==2026.10.7\ntransformers==5.16.1\npeft==0.21.2\naccelerate==1.15.0\nbitsandbytes==0.50.2\n')
   constraint=root5/'constraints.txt';constraint.write_text('torch==2.11.0\ntorchvision==0.26.0\ntorchaudio==2.11.0\ntransformers==5.16.1\npeft==0.21.2\naccelerate==1.15.0\nbitsandbytes==0.50.2\n')
   subprocess.run([str(v/'bin/python'),'-m','pip','install','--disable-pip-version-check','--report',str(root5/'install_report.json'),'-c',str(constraint),'-r',str(req)],check=True,stdout=log,stderr=subprocess.STDOUT,timeout=900)
   versions=subprocess.check_output([str(v/'bin/python'),'-c',"import importlib.metadata as m,json,sys;print(json.dumps({'python':sys.version,'packages':{n:m.version(n) for n in ['torch','transformers','unsloth','unsloth_zoo','peft','bitsandbytes','accelerate','triton']}}))"],text=True)
   state.update(state='INSTALLED_NOT_TRAINING',versions=json.loads(versions),elapsed_seconds=time.time()-state['started_unix']);save()
 except BaseException as e:
  state.update(state='ERROR',error=str(e),traceback=traceback.format_exc()[-4000:]);save()
corrective_install_thread=threading.Thread(target=_install_corrective,name='Corrective5hInstaller',daemon=True)
corrective_install_thread.start()
print(json.dumps({'installer_started':True,'train_hours_authorized':5,'optimizer_updates':0}))

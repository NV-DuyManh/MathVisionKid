import pathlib,subprocess,sys,json,threading,time,traceback
assert budget_root.name=='mathvisionkid_t4_budget_3h_20261023'
assert time.time()<budget_status['deadline_unix']-1800
assert not globals().get('budget_install_thread') or not budget_install_thread.is_alive()
def _install_budget_environment():
    state={'state':'INSTALLING_ISOLATED_ENVIRONMENT','started_unix':time.time(),'python_source':sys.executable,'inherits_base_torch_readonly':True}
    receipt=budget_root/'install_status.json'
    def save():receipt.write_text(json.dumps(state,indent=2))
    save()
    try:
        env=budget_root/'venv'
        with (budget_root/'install.log').open('w') as output:
            subprocess.run([sys.executable,'-m','venv','--without-pip','--system-site-packages',str(env)],check=True,stdout=output,stderr=subprocess.STDOUT,timeout=90)
            requirements=budget_root/'requirements.txt'
            requirements.write_text('unsloth[cu130-torch2110]==2026.10.7\nunsloth-zoo==2026.10.7\ntransformers==5.16.1\npeft==0.21.2\naccelerate==1.15.0\nbitsandbytes==0.50.2\n')
            constraints=budget_root/'constraints.txt'
            constraints.write_text('torch==2.11.0\ntorchvision==0.26.0\ntorchaudio==2.11.0\ntransformers==5.16.1\npeft==0.21.2\naccelerate==1.15.0\nbitsandbytes==0.50.2\n')
            command=[str(env/'bin/python'),'-m','pip','install','--disable-pip-version-check','--report',str(budget_root/'install_report.json'),'-c',str(constraints),'-r',str(requirements)]
            state.update(command=command);save()
            subprocess.run(command,stdout=output,stderr=subprocess.STDOUT,check=True,timeout=900)
            freeze=subprocess.check_output([str(env/'bin/python'),'-m','pip','freeze'],text=True)
            (budget_root/'isolated_pip_freeze.txt').write_text(freeze)
            # Package metadata only; importing Unsloth would allocate/patch GPU
            # modules while the old training worker owns the GPU.
            meta=subprocess.check_output([str(env/'bin/python'),'-c',"import importlib.metadata as m,json,sys;print(json.dumps({'python':sys.version,'versions':{k:m.version(k) for k in ['unsloth','unsloth-zoo','torch','transformers','peft','bitsandbytes']}}))"],text=True)
            state.update(state='ISOLATED_INSTALL_COMPLETE_NOT_GPU_TESTED',metadata=json.loads(meta),elapsed_seconds=time.time()-state['started_unix'])
    except BaseException as error:
        state.update(state='ISOLATED_INSTALL_FAILED',error=str(error),traceback=traceback.format_exc(),elapsed_seconds=time.time()-state['started_unix'])
    finally:save()
budget_install_thread=threading.Thread(target=_install_budget_environment,name='MathVisionKidIsolatedInstall',daemon=True)
budget_install_thread.start()
print(json.dumps({'started':True,'old_training_alive':full_text_training_thread.is_alive(),'deadline_utc':budget_status['deadline_utc'],'install_status':str(budget_root/'install_status.json')}))

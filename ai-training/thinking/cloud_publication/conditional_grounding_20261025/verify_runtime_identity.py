import os,pathlib,json,socket,uuid,datetime
if 'conditional_runtime_nonce' not in globals():
 conditional_runtime_nonce=uuid.uuid4().hex
print(json.dumps({'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'kernel_pid':os.getpid(),'hostname':socket.gethostname(),'nonce':conditional_runtime_nonce,
 'recovery_credentials_present':'recovery_credentials' in globals(),
 'install_process_present':'conditional_install_process' in globals(),
 'work_directories':[str(p) for p in pathlib.Path('/content').iterdir() if p.name.startswith('mathvisionkid')],
 'bootstrap_progress_files':[(str(p),p.stat().st_size) for p in pathlib.Path('/content').glob('mathvisionkid_conditional*/input_readback.json')]}))

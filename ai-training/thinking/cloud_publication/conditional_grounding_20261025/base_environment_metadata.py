import json,importlib.metadata as meta,os,pathlib,sys,socket,subprocess
versions={}
for package in ('torch','torchvision','transformers','peft','accelerate','bitsandbytes','unsloth','unsloth-zoo','triton','pip','numpy'):
 try:versions[package]=meta.version(package)
 except meta.PackageNotFoundError:versions[package]=None
memory=pathlib.Path('/proc/meminfo').read_text().splitlines()[:3]
print(json.dumps({'kernel_pid':os.getpid(),'hostname':socket.gethostname(),'python':sys.version,'versions':versions,
 'memory':memory,'disk':subprocess.check_output(['df','-h','/content'],text=True),'kernel_uptime':pathlib.Path('/proc/uptime').read_text().strip(),
 'work_directories':[str(p) for p in pathlib.Path('/content').iterdir() if p.name.startswith('mathvisionkid')]}))

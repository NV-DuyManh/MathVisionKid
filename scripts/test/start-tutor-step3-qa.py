"""Isolated real services; deterministic mathematics must work without cloud keys."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'report/tutor-step3-blocker'
OUT.mkdir(parents=True,exist_ok=True)
DB='mathvision_tutor_step3_20261028'
faults=os.getenv('TUTOR_QA_FAULTS')=='1'
ai_port,spring_port=(18002,18082) if faults else (18000,18080)
prefix='fault-' if faults else 'qa-'
for port in (ai_port,spring_port):
    try:
        with socket.create_connection(('127.0.0.1',port),timeout=.5):
            raise RuntimeError(f'QA port {port} occupied; refusing a duplicate process')
    except OSError:
        pass
exists=subprocess.check_output(['docker','exec','mathvision-postgres','psql','-U','mathvision','-d','postgres','-Atc',f"SELECT 1 FROM pg_database WHERE datname='{DB}'"],text=True).strip()
if not exists:
    subprocess.run(['docker','exec','mathvision-postgres','createdb','-U','mathvision',DB],check=True)
env=os.environ.copy()
for file in (ROOT/'.env',ROOT/'backend/business-api/.env'):
    for line in file.read_text(encoding='utf-8-sig').splitlines() if file.exists() else []:
        match=re.match(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$',line)
        if match and not line.lstrip().startswith('#'):
            env[match[1]]=match[2].strip('"\'')
ai_env=os.environ.copy()
ai_env.update({'GROQ_ENABLED':'false','GEMINI_ENABLED':'false','PYTHONUNBUFFERED':'1'})
ffmpeg=ROOT/'infra/local-runtime/tools/ffmpeg/bin'
ai_env['PATH']=str(ffmpeg)+os.pathsep+ai_env.get('PATH','')
module=['tutor_step3_fault_server:app','--app-dir',str(ROOT/'scripts/test')] if faults else ['app.main:app']
with (OUT/(prefix+'fastapi.log')).open('w',encoding='utf-8') as log:
    ai=subprocess.Popen([str(ROOT/'ai/runtime/.venv/Scripts/python.exe'),'-m','uvicorn',*module,'--host','127.0.0.1','--port',str(ai_port)],cwd=ROOT/'ai/runtime',env=ai_env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
env.update({'DB_URL':'jdbc:postgresql://127.0.0.1:5432/'+DB,'DB_USERNAME':'mathvision',
    'AI_SERVICE_BASE_URL':'http://127.0.0.1:'+str(ai_port),'CORS_ALLOWED_ORIGINS':'http://127.0.0.1:8096,http://localhost:8096'})
jar=ROOT/'backend/business-api/build/libs/business-api.jar'
stable=ROOT/'backend/business-api/build/runtime'/('business-api-'+hashlib.sha256(jar.read_bytes()).hexdigest()[:16]+'.jar')
if not stable.exists(): shutil.copy2(jar,stable)
with (OUT/(prefix+'spring.log')).open('w',encoding='utf-8') as log:
    spring=subprocess.Popen(['java','-Xms32m','-Xmx384m','-XX:MaxMetaspaceSize=256m','-jar',str(stable),
        '--spring.profiles.active=dev','--server.address=127.0.0.1','--server.port='+str(spring_port),'--ai.gateway.mode=FASTAPI'],
        cwd=ROOT/'backend/business-api',env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
result={'springPid':spring.pid,'fastapiParentPid':ai.pid,'database':DB,'springPort':spring_port,'fastapiPort':ai_port,'groqEnabled':False,'geminiEnabled':False}
(OUT/(prefix+'processes.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))

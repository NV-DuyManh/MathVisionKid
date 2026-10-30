"""Start an isolated real PostgreSQL/Spring instance, keeping credentials in process env."""
import json
import os
import re
import subprocess
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DB='mathvision_quiz_runtime_20261028'
OUT=ROOT/'report/smart-quiz-runtime-root-cause'
OUT.mkdir(parents=True,exist_ok=True)
offline=os.getenv('QUIZ_QA_OFFLINE')=='1'
port=18081 if offline else 18080
import socket
try:
    with socket.create_connection(('127.0.0.1',port),timeout=.5):
        raise RuntimeError(f'QA port {port} is already occupied; no second process was started')
except OSError:
    pass
env=os.environ.copy()
for file in [ROOT/'.env',ROOT/'backend/business-api/.env']:
    if not file.exists(): continue
    for line in file.read_text(encoding='utf-8-sig').splitlines():
        match=re.match(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$',line)
        if match and not line.lstrip().startswith('#'): env[match[1]]=match[2].strip('"\'')
existing=subprocess.check_output(['docker','exec','mathvision-postgres','psql','-U','mathvision','-d','postgres','-Atc',"SELECT 1 FROM pg_database WHERE datname='"+DB+"'"],encoding='utf-8').strip()
if not existing:
    subprocess.run(['docker','exec','mathvision-postgres','createdb','-U','mathvision',DB],check=True)
env.update({'DB_URL':'jdbc:postgresql://127.0.0.1:5432/'+DB,'DB_USERNAME':'mathvision','SPRING_PROFILES_ACTIVE':'dev','SERVER_ADDRESS':'127.0.0.1','PORT':'18080'})
env['CORS_ALLOWED_ORIGINS']='http://127.0.0.1:8095,http://localhost:8095,http://127.0.0.1:8081,http://localhost:8081'
env['PORT']=str(port)
if offline: env['AI_SERVICE_BASE_URL']=os.getenv('QUIZ_QA_AI_BASE','http://127.0.0.1:9')
jar=ROOT/'backend/business-api/build/libs/business-api.jar'
stable=ROOT/'backend/business-api/build/runtime'/('business-api-'+hashlib.sha256(jar.read_bytes()).hexdigest()[:16]+'.jar')
stable.parent.mkdir(parents=True,exist_ok=True)
if not stable.exists():
    import shutil
    shutil.copy2(jar,stable)
with (OUT/('qa-offline-spring.log' if offline else 'qa-spring.log')).open('w',encoding='utf-8') as output:
    proc=subprocess.Popen(['java','-Xms32m','-Xmx384m','-XX:MaxMetaspaceSize=256m','-jar',str(stable),'--spring.profiles.active=dev','--server.address=127.0.0.1','--server.port='+str(port),'--ai.gateway.mode=FASTAPI'],cwd=ROOT/'backend/business-api',env=env,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
(OUT/('qa-offline-process.json' if offline else 'qa-process.json')).write_text(json.dumps({'pid':proc.pid,'port':port,'database':DB}),encoding='utf-8')
print(json.dumps({'pid':proc.pid,'port':port,'database':DB}))

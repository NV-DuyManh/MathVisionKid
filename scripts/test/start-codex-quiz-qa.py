import sys,subprocess,json,hashlib,shutil,socket
from pathlib import Path
from codex_quiz_db import sql,env,ROOT,OUT
DB='mathvision_codex_quiz_review_20261029'
if not sql("SELECT 1 FROM pg_database WHERE datname='"+DB+"'",'postgres'):sql('CREATE DATABASE '+DB,'postgres')
with socket.socket() as s:
    if s.connect_ex(('127.0.0.1',18080))==0:raise RuntimeError('QA port 18080 occupied; refusing duplicate')
jar=ROOT/'backend/business-api/build/libs/business-api.jar';digest=hashlib.sha256(jar.read_bytes()).hexdigest();stable=ROOT/'backend/business-api/build/runtime'/('business-api-'+digest[:16]+'.jar')
if not stable.exists():shutil.copy2(jar,stable)
e=env.copy();e.update({'DB_URL':'jdbc:postgresql://127.0.0.1:5432/'+DB,'DB_USERNAME':'mathvision','AI_SERVICE_BASE_URL':'http://127.0.0.1:8000','CORS_ALLOWED_ORIGINS':'http://localhost:8081,http://127.0.0.1:8096'})
with (OUT/'qa-spring.log').open('wb') as log:
    p=subprocess.Popen(['java','-Xms32m','-Xmx384m','-jar',str(stable),'--spring.profiles.active=dev','--server.address=127.0.0.1','--server.port=18080','--ai.gateway.mode=FASTAPI'],cwd=ROOT/'backend/business-api',env=e,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
r={'pid':p.pid,'database':DB,'port':18080,'jarSha256':digest};(OUT/'qa-processes.json').write_text(json.dumps(r,indent=2));print(r,flush=True)

from pathlib import Path
import sys,json,urllib.request,socket,hashlib,subprocess,zipfile,time
sys.path.insert(0,str(Path('scripts/test').resolve()))
from codex_quiz_db import sql,ROOT,OUT,env
sys.stdout.reconfigure(encoding='utf-8')
info=json.loads((OUT/'phone-connection.json').read_text());ip=info['address'];r={'verifiedAt':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'lan':ip,'services':{}}
for name,url in [('spring',f'http://{ip}:8080/actuator/health'),('fastapi','http://127.0.0.1:8000/health'),('metro',f'http://{ip}:8081/status'),('portal',f'http://{ip}:5172/'),('teacher',f'http://{ip}:5173/'),('admin',f'http://{ip}:5174/'),('minio','http://127.0.0.1:9000/minio/health/ready')]:
    with urllib.request.urlopen(url,timeout=15) as q:
        sample=q.read(300).decode('utf-8','replace');r['services'][name]={'http':q.status,'url':url,'sample':sample[:120]};assert q.status==200
    print(name,'HTTP 200',flush=True)
with socket.create_connection(('127.0.0.1',6379),timeout=4) as s:s.sendall(b'*1\r\n$4\r\nPING\r\n');reply=s.recv(100).decode();assert reply=='+PONG\r\n';r['redis']=reply.strip()
r['postgresVersion']=sql('SELECT version()');r['migrations']=json.loads(sql("SELECT json_agg(row_to_json(t)) FROM (SELECT version,description,success,checksum FROM flyway_schema_history WHERE version IN ('21','22','23') ORDER BY installed_rank)t"))
r['mainHistoricalInvalidations']=sql("SELECT count(*) FROM student_quizzes WHERE status='INVALIDATED' AND first_completed_at IS NOT NULL")
net=subprocess.check_output(['netstat','-ano','-p','tcp'],text=True)
ports={8080,8081,8000,5172,5173,5174};listeners=[]
for line in net.splitlines():
    a=line.split()
    if len(a)==5 and a[0]=='TCP' and a[3]=='LISTENING' and int(a[1].rsplit(':',1)[1]) in ports:listeners.append({'address':a[1],'pid':int(a[4])})
r['listeners']=listeners
owners={x['pid'] for x in listeners if x['address'].endswith(':8080')};assert len(owners)==1
pid=next(iter(owners));query='Get-CimInstance Win32_Process -Filter "ProcessId = '+str(pid)+'" | Select-Object ProcessId,ParentProcessId,ExecutablePath,CreationDate,CommandLine | ConvertTo-Json'
r['springProcess']=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',query],text=True))
jar=ROOT/'backend/business-api/build/libs/business-api.jar';digest=hashlib.sha256(jar.read_bytes()).hexdigest();stable=ROOT/'backend/business-api/build/runtime'/('business-api-'+digest[:16]+'.jar')
assert str(stable).lower() in r['springProcess']['CommandLine'].lower();assert hashlib.sha256(stable.read_bytes()).hexdigest()==digest
r['jarSha256']=digest;r['jarPath']=str(stable);r['jarBuildTime']=time.strftime('%Y-%m-%dT%H:%M:%S%z',time.localtime(jar.stat().st_mtime))
main=ROOT/'backend/business-api/src/main';newest=max(p.stat().st_mtime for p in main.rglob('*') if p.is_file() and p.suffix in ['.java','.sql','.yml','.properties']);assert newest<=jar.stat().st_mtime
with zipfile.ZipFile(jar) as z:
    for cls in ['QuizMath','QuizService']:
        rel='com/mathvisionkids/api/quiz/'+cls+'.class';assert z.read('BOOT-INF/classes/'+rel)==(ROOT/'backend/business-api/build/classes/java/main'/rel).read_bytes()
req=urllib.request.Request('http://127.0.0.1:8000/internal/v1/tutor/runtime',headers={'X-Internal-API-Key':env['INTERNAL_API_KEY']})
with urllib.request.urlopen(req,timeout=10) as q:v=json.load(q)
assert v['lessonSourceHash']==hashlib.sha256((ROOT/'ai/runtime/app/tutoring/lesson.py').read_bytes()).hexdigest();assert v['tutorSourceHash']==hashlib.sha256((ROOT/'ai/runtime/app/api/tutor.py').read_bytes()).hexdigest()
r['fastapiRuntime']={k:v[k] for k in ['pid','workflowVersion','lessonSourceHash','tutorSourceHash']}
with (OUT/'docker-final-probe.log').open('wb') as log:
    p=subprocess.Popen(['docker','ps','--format','{{.Names}} {{.Status}}'],stdout=log,stderr=subprocess.STDOUT)
    try:r['dockerControlPlane']={'exit':p.wait(timeout=5)}
    except subprocess.TimeoutExpired:p.kill();r['dockerControlPlane']={'status':'TIMEOUT','seconds':5}
r['phoneConnection']=info;r['nativeBundle']=json.loads((OUT/'android-bundle.json').read_text());r['phoneStatus']='Sẵn sàng để người dùng nghiệm thu; physical phone not tested'
(OUT/'runtime-final.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'springPid':pid,'jarSha256':digest,'listeners':listeners,'migration':r['migrations'],'redis':r['redis'],'dockerControlPlane':r['dockerControlPlane']},ensure_ascii=False,indent=2))

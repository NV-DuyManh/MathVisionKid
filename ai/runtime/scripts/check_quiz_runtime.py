"""Compare running identities with compiled artifacts without exposing secrets."""
import hashlib
import json
import sys
import zipfile
import socket
from pathlib import Path
from urllib.request import Request,urlopen
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import settings

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'report/smart-quiz-runtime-root-cause'
def read(url,headers=None,body=None,timeout=30):
    with urlopen(Request(url,headers=headers or {},data=None if body is None else json.dumps(body).encode()),timeout=timeout) as response:
        return response.read(),dict(response.headers)
result={}
raw,_=read('http://127.0.0.1:8080/api/v1/auth/login',{'Content-Type':'application/json'},{'email':'minh.student@mathvision.local','password':'MathVision123!'})
token=json.loads(raw)['accessToken']
raw,headers=read('http://127.0.0.1:8080/api/v1/student/quizzes/runtime',{'Authorization':'Bearer '+token})
result['spring']=json.loads(raw)
with zipfile.ZipFile(ROOT/'backend/business-api/build/libs/business-api.jar') as archive:
    compiled=archive.read('BOOT-INF/classes/com/mathvisionkids/api/quiz/QuizMath.class')
result['spring']['matchesBuiltClass']=result['spring']['generatorClassHash']==hashlib.sha256(compiled).hexdigest()
raw,_=read('http://127.0.0.1:8000/internal/v1/tutor/runtime',{'X-Internal-API-Key':settings.internal_api_key})
result['fastapi']=json.loads(raw)
result['fastapi']['matchesSourceLoaded']=result['fastapi']['tutorSourceHash']==hashlib.sha256((ROOT/'ai/runtime/app/api/tutor.py').read_bytes()).hexdigest()
raw,_=read('http://127.0.0.1:8081/status')
result['metroStatus']=raw.decode()
raw,_=read('http://127.0.0.1:8081',{'Accept':'application/expo+json','Expo-Platform':'ios','Expo-Protocol-Version':'1'})
manifest=json.loads(raw)
url=manifest['launchAsset']['url']
result['metroManifest']={'bundleHost':url.split('/')[2],'platform':'ios'}
with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as route:
    route.connect(('8.8.8.8',80))
    lan=route.getsockname()[0]
raw,_=read('http://'+lan+':8080/api/v1/student/quizzes/runtime',{'Authorization':'Bearer '+token})
result['lanRoute']={'host':lan,'sameSpringInstance':json.loads(raw)['instance']==result['spring']['instance'],'physicalPhoneRequestCaptured':False}
raw,_=read('http://'+lan+':8081',{'Accept':'application/expo+json','Expo-Platform':'ios','Expo-Protocol-Version':'1'})
lan_manifest=json.loads(raw)
result['metroManifestLAN']={'hostUri':lan_manifest.get('extra',{}).get('expoClient',{}).get('hostUri'),'launchAssetHost':lan_manifest['launchAsset']['url'].split('/')[2]}
(OUT/'runtime-after.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
raw,_=read(url,timeout=240)
result['iosBundle']={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'newClientMarkerPresent':b'confirmed-quiz-v3' in raw,'confirmedTextFieldPresent':b'confirmedProblemText' in raw}
(OUT/'runtime-after.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('iOS bundle marker:',result['iosBundle']['newClientMarkerPresent'])

"""Real authorized Quiz speech, including WAV/non-silence verification; no speech mocks."""
import array
import importlib.util
import io
import json
import math
import time
import wave
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError

spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('smart-quiz-runtime-audit.py'))
audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
DB='mathvision_quiz_runtime_20261028'
qid=json.loads((audit.OUT/'real-lesson.json').read_text(encoding='utf-8'))['quizId']
email=audit.sql("SELECT u.email FROM student_quizzes q JOIN users u ON u.id=q.student_id WHERE q.id='"+qid+"'",DB)
code,auth,_=audit.http('http://127.0.0.1:18080/api/v1/auth/login',{'email':email,'password':'MathVision123!'})
assert code==200
result={'authorization':'actual completed Quiz owner','attempts':[],'status':'FAIL'}
for attempt in range(3):
    started=time.monotonic()
    request=Request('http://127.0.0.1:18080/api/v1/student/quizzes/'+qid+'/narration',data=json.dumps({'voice':'vi-VN-NamMinhNeural'}).encode(),headers={'Authorization':'Bearer '+auth['accessToken'],'Content-Type':'application/json'})
    try:
        with urlopen(request,timeout=45) as response:
            data=response.read()
            with wave.open(io.BytesIO(data),'rb') as audio:
                seconds=audio.getnframes()/audio.getframerate(); samples=array.array('h',audio.readframes(audio.getnframes()))
                rms=math.sqrt(sum(v*v for v in samples)/len(samples))
                assert audio.getnchannels()==1 and audio.getframerate()==16000 and seconds>.1 and rms>1
            result['attempts'].append({'httpStatus':response.status,'seconds':round(time.monotonic()-started,2)})
            result.update(status='PASS',bytes=len(data),audioSeconds=round(seconds,2),rms=round(rms,2),physicalPlaybackVerified=False)
            (audit.OUT/'verified-quiz-solution.wav').write_bytes(data)
            break
    except HTTPError as error:
        result['attempts'].append({'httpStatus':error.code,'seconds':round(time.monotonic()-started,2)})
        if attempt<2:time.sleep(3)
(audit.OUT/'voice-http.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
assert result['status']=='PASS','Real speech did not become available within three explicit bounded attempts'

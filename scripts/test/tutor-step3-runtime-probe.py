"""Probe the actual launcher FastAPI process without touching a pupil's records."""
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ai/runtime'))
from app.config import settings
import httpx

OUT=ROOT/'report/tutor-step3-blocker'
SOURCE='Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?'
owner='qa-runtime-'+uuid4().hex
headers={'X-Internal-API-Key':settings.internal_api_key,'X-Request-ID':'qa-main-'+uuid4().hex}
evidence={}
with httpx.Client(base_url='http://127.0.0.1:8000/internal/v1/tutor',headers=headers,timeout=12) as client:
    def post(path,body):
        response=client.post(path,json={'owner':owner,**body});assert response.status_code==200
        return response.json()
    runtime=client.get('/runtime');runtime.raise_for_status();evidence['runtime']=runtime.json()
    assert evidence['runtime']['workflowVersion']=='retained-reading-v1'
    evidence['loadedLessonMatchesDisk']=evidence['runtime']['lessonSourceHash']==hashlib.sha256((ROOT/'ai/runtime/app/tutoring/lesson.py').read_bytes()).hexdigest()
    assert evidence['loadedLessonMatchesDisk']
    evidence['groqHealth']=httpx.get('http://127.0.0.1:8000/internal/v1/groq-health',timeout=12).json()
    current=post('/lesson',{'problemText':SOURCE,'problemConfirmed':True,'guidedUnderstanding':True,'startWithReading':True})
    sid=current['sessionId'];evidence['turns']=[]
    for answer in ('fact','question','truth'):
        step=current['step']
        if answer=='fact': value=next(c for c in step['choices'] if '1/3' in c and 'bao nhiêu' not in c)
        elif answer=='question':value=next(c for c in step['choices'] if 'bao nhiêu' in c)
        else:
            import re
            quote=re.search('«(.*?)»',step['question']);value='Đúng' if quote and not re.match(r'^(Hỏi|Tính)\b',quote[1],re.I) else 'Sai'
        current=post('/lesson/answer',{'sessionId':sid,'revision':current['revision'],'answer':value})
        evidence['turns'].append({'revision':current['revision'],'status':current['status']})
    for _ in range(40):
        if not current['preparingMath']: break
        time.sleep(.1);current=post('/lesson/preparation',{'sessionId':sid,'revision':3})
    assert current['stepIndex']==3 and current['step']['kind']=='MATH'
    for answer in ('11/15','4/15','60'):
        current=post('/lesson/answer',{'sessionId':sid,'revision':current['revision'],'answer':answer})
        evidence['turns'].append({'revision':current['revision'],'status':current['status'],'answer':answer})
    assert current['status']=='COMPLETE'
    evidence['status']='PASS'
(OUT/'main-runtime-probe.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS actual port 8000: loaded lesson hash matches disk; reading 3/3 -> MATH -> COMPLETE')

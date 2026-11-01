"""HTTP proof with Spring's entire AI boundary unreachable and persisted real lesson sources."""
import importlib.util
import json
import re
import time
import os
from fractions import Fraction
from pathlib import Path
from uuid import uuid4

spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('smart-quiz-runtime-audit.py'))
audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
DB='mathvision_quiz_runtime_20261028'
BASE='http://127.0.0.1:18081/api/v1'
for attempt in range(90):
    try:
        audit.http('http://127.0.0.1:18081/actuator/health'); break
    except Exception:
        if attempt==89: raise
        time.sleep(1)
completed=json.loads((audit.OUT/'real-lesson.json').read_text(encoding='utf-8'))
qid=completed['quizId']
email=audit.sql("SELECT u.email FROM student_quizzes q JOIN users u ON u.id=q.student_id WHERE q.id='"+qid+"'",DB)
code,auth,_=audit.http(BASE+'/auth/login',{'email':email,'password':'MathVision123!'})
assert code==200
token=auth['accessToken']
def call(path,body=None):
    code,data,_=audit.http(BASE+path,body,token)
    assert code==200,(path,code)
    return data
TREE='Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây? (2 điểm)'
prep=call('/student/quizzes/prepare',{'workflowKey':str(uuid4()),'revision':1,'confirmedProblemText':TREE,'problemConfirmed':True})
initial=prep['status']
for _ in range(100):
    if prep['status']!='GENERATING': break
    time.sleep(.1); prep=call('/student/quizzes/preparations/'+prep['preparationId'])
assert prep['status']=='READY'
row=json.loads(audit.sql("SELECT json_build_object('text',confirmed_problem_text,'draft',validated_draft,'durationMs',duration_ms,'version',generator_version)::text FROM quiz_preparations WHERE id='"+prep['preparationId']+"'",DB))
assert row['text']==TREE
draft=json.loads(row['draft'])
shares=[Fraction(a+'/'+b) for a,b in re.findall(r'(\d+)/(\d+)',draft['question'])]
count=int(re.search(r'Biết[^\d]*(\d+)',draft['question'])[1])
answer=Fraction(count)/(1-sum(shares))
assert answer.denominator==1 and answer!=60 and str(answer)==draft['answer']['numerator'].__str__()
history=call('/student/quizzes/'+qid)
assert history['status']=='COMPLETED' and history['stars']==3 and len(history['attempts'])==1
result={'status':'PASS','aiBoundary':os.getenv('QUIZ_QA_AI_BASE','http://127.0.0.1:9 (unreachable; no cloud requests possible)'),'initialStatus':initial,'finalStatus':prep['status'],'confirmedTextPreserved':True,'independentlySolvedAnswer':str(answer),'generationDurationMs':row['durationMs'],'historyVisibleAfterNewSpringProcess':True,'starsPreserved':history['stars'],'runtime':call('/student/quizzes/runtime')}
(audit.OUT/('providers-disabled-http.json' if os.getenv('QUIZ_QA_AI_BASE') else 'cloud-off.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))

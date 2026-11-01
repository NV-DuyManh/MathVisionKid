"""Real service workflow with explicitly injected planner faults, never production."""
import importlib.util
import json
from pathlib import Path
import re
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'report/tutor-step3-blocker'
spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('smart-quiz-runtime-audit.py'))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
BASE='http://127.0.0.1:18082/api/v1';DB='mathvision_tutor_step3_20261028'
SOURCE='Lan có 12 bút, được tặng thêm 5 bút. Hỏi Lan có tất cả bao nhiêu bút?'
evidence={'environment':'real Spring + HTTP FastAPI + PostgreSQL; QA-only planner fault injection','cases':[]}

def account():
    email='tutor-fault-'+uuid4().hex[:10]+'@test.invalid'
    audit.sql("INSERT INTO users(id,email,password_hash,role,display_name,active,created_at,updated_at) SELECT '"+str(uuid4())+"','"+email+"',password_hash,'STUDENT','Bạn học',true,now(),now() FROM users WHERE email='minh.student@mathvision.local'; INSERT INTO students(student_id,grade_level) SELECT id,5 FROM users WHERE email='"+email+"';",DB)
    status,body,_=audit.http(BASE+'/auth/login',{'email':email,'password':'MathVision123!'})
    assert status==200
    return body['accessToken']

def call(path,body,expected=200,trace=None):
    status,result,headers=audit.http(BASE+path,body,token,headers={'X-Request-ID':trace or str(uuid4())})
    assert status==expected,(path,status)
    case['requests'].append({'path':path,'http':status,'status':result.get('status'),'requestId':headers.get('X-Request-ID')})
    return result

try:
    for mode in ('timeout','quota','validation','cancelled','delayed'):
        token=account();case={'mode':mode,'requests':[]};evidence['cases'].append(case)
        current=call('/student/tutor/lesson',{'problemText':SOURCE,'workText':'','problemConfirmed':True,'workConfirmed':False,'guidedUnderstanding':True,'startWithReading':True},trace='qa_'+mode+'_'+uuid4().hex)
        sid=current['sessionId']
        for index in range(3):
            step=current['step'];choices=step['choices']
            if index==0:answer=next(c for c in choices if '12' in c and 'bao nhiêu' not in c)
            elif index==1:answer=next(c for c in choices if 'bao nhiêu' in c)
            else:
                quote=re.search('«(.*?)»',step['question']);answer='Đúng' if quote and not re.match(r'^(Hỏi|Tính)\b',quote[1],re.I) else 'Sai'
            current=call('/student/tutor/lesson/answer',{'sessionId':sid,'revision':current['revision'],'answer':answer,'hint':False})
        assert current['revision']==3 and len(current['completed'])==3
        assert current['status'] in ('PREPARING','RETRYABLE')
        progress={'sessionId':sid,'revision':3,'retry':False}
        current=call('/student/tutor/lesson/preparation',progress)
        if mode!='delayed':
            assert current['status']=='RETRYABLE' and not current['conclusion'] and current['step'] is None
            again=call('/student/tutor/lesson/preparation',progress)
            assert again['revision']==3 and len(again['completed'])==3
            time.sleep(5.1)
            call('/student/tutor/lesson/preparation',progress|{'retry':True})
            current=call('/student/tutor/lesson/preparation',progress|{'retry':True})
        for _ in range(40):
            if not current['preparingMath']: break
            time.sleep(.1);current=call('/student/tutor/lesson/preparation',progress)
        assert current['stepIndex']==3 and current['step']['kind']=='MATH' and len(current['completed'])==3
        call('/student/tutor/lesson/preparation',progress|{'revision':2},expected=409)
        for answer in ('12','17'):
            current=call('/student/tutor/lesson/answer',{'sessionId':sid,'revision':current['revision'],'answer':answer,'hint':False})
        assert current['status']=='COMPLETE' and current['completed'][-1]['answer']=='17'
        case.update({'status':'PASS','retainedReading':3,'completion':'COMPLETE','mathAnswers':['12','17']})
        print('PASS injected '+mode+' -> retained 3/3 -> verified math -> COMPLETE')
    evidence['status']='PASS'
except Exception as error:
    evidence.update({'status':'FAIL','failure':str(error)});raise
finally:
    (OUT/'fault-http-integration.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')

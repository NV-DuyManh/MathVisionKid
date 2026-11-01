"""End-to-end real Tutor lesson, then a verified Quiz; no fabricated completion events."""
import ast
import json
import re
import sys
import time
from fractions import Fraction
from pathlib import Path
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parent))
import importlib.util
spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('smart-quiz-runtime-audit.py'))
audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
BASE='http://127.0.0.1:18080/api/v1'
DB='mathvision_quiz_runtime_20261028'
TREE='Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây? (2 điểm)'
result={'environment':'real Spring, real FastAPI, isolated PostgreSQL, no response mocks','turns':[]}

def call(path,body=None):
    for attempt in range(3):
        code,data,headers=audit.http(BASE+path,body,token)
        if code!=503 or data.get('error',{}).get('code')!='TUTOR_UNAVAILABLE' or attempt==2: break
        result.setdefault('transientTutorRetries',[]).append({'path':path,'status':code,'attempt':attempt+1})
        time.sleep(15)
    if code!=200: raise AssertionError((path,code,data.get('error',{}).get('code')))
    return data

def solve(expression):
    source=expression.replace('×','*').replace('÷','/').replace(':','/').replace('−','-')
    def visit(node):
        if isinstance(node,ast.Expression): return visit(node.body)
        if isinstance(node,ast.Constant) and type(node.value) is int: return Fraction(node.value)
        if isinstance(node,ast.BinOp):
            a,b=visit(node.left),visit(node.right)
            if isinstance(node.op,ast.Add): return a+b
            if isinstance(node.op,ast.Sub): return a-b
            if isinstance(node.op,ast.Mult): return a*b
            if isinstance(node.op,ast.Div): return a/b
        raise ValueError('Only arithmetic expressions are allowed')
    return str(visit(ast.parse(source,mode='eval')))

try:
    email='quiz-runtime-lesson-'+uuid4().hex[:8]+'@test.invalid'
    audit.sql("INSERT INTO users(id,email,password_hash,role,display_name,active,created_at,updated_at) SELECT '"+str(uuid4())+"','"+email+"',password_hash,'STUDENT','Bạn học',true,now(),now() FROM users WHERE email='minh.student@mathvision.local'; INSERT INTO students(student_id,grade_level) SELECT id,3 FROM users WHERE email='"+email+"';",DB)
    code,auth,_=audit.http(BASE+'/auth/login',{'email':email,'password':'MathVision123!'})
    assert code==200
    token=auth['accessToken']
    preparation=call('/student/quizzes/prepare',{'workflowKey':str(uuid4()),'revision':1,'confirmedProblemText':TREE,'problemConfirmed':True})
    result['initialPreparationStatus']=preparation['status']
    started=time.monotonic()
    lesson=call('/student/tutor/lesson',{'problemText':TREE,'workText':'','problemConfirmed':True,'workConfirmed':False,'guidedUnderstanding':True,'startWithReading':True})
    for _ in range(24):
        if lesson['status']=='COMPLETE': break
        step=lesson['step']; choices=step.get('choices') or []
        if choices:
            if lesson['stepIndex']==0: answer=next((s for s in choices if '1/3' in s and 'bao nhiêu' not in s),choices[0])
            elif lesson['stepIndex']==1: answer=next((s for s in choices if 'bao nhiêu' in s),choices[0])
            else:
                quote=re.search('«(.*?)»',step['question'])
                answer='Đúng' if quote and not re.match(r'^(Hỏi|Tính)\b',quote[1],re.I) else 'Sai'
                if answer not in choices: answer=choices[0]
        else:
            try: answer=solve(step.get('expression',''))
            except Exception:
                lower=(step['title']+' '+step['question']).lower()
                answer='4/15' if 'phần' in lower and ('cam' in lower or 'còn lại' in lower) else '11/15' if 'phần' in lower else '60'
        previous=lesson
        lesson=call('/student/tutor/lesson/answer',{'sessionId':lesson['sessionId'],'revision':lesson['revision'],'answer':answer,'hint':False})
        result['turns'].append({'stepIndex':previous['stepIndex'],'answer':answer,'result':lesson['status']})
        if lesson['status']=='TRY_AGAIN':
            raise AssertionError('Automatic QA learner could not answer this real lesson; no completion was forged')
    assert lesson['status']=='COMPLETE', 'Actual Tutor did not complete'
    result['lessonDurationSeconds']=round(time.monotonic()-started,2)
    offer=call('/student/quizzes/from-learning',{'sourceType':'LESSON','sourceId':lesson['sessionId']})
    assert offer['offered'] and offer['quiz']['status']=='READY'
    quiz=call('/student/quizzes/'+offer['quiz']['quizId']+'/start',{})
    shares=[Fraction(a+'/'+b) for a,b in re.findall(r'(\d+)/(\d+)',quiz['questionText'])]
    count=int(re.search(r'Biết[^\d]*(\d+)',quiz['questionText'])[1])
    answer=Fraction(count)/(1-sum(shares))
    assert answer.denominator==1 and answer!=60
    graded=call('/student/quizzes/'+quiz['quizId']+'/submit',{'requestId':str(uuid4()),'answer':str(answer)})
    assert graded['quiz']['status']=='COMPLETED' and graded['quiz']['stars']==3
    result.update({'status':'PASS','sourceId':lesson['sessionId'],'quizId':quiz['quizId'],'question':quiz['questionText'],'independentlySolvedAnswer':str(answer),'stars':graded['quiz']['stars']})
    print('PASS Real Tutor COMPLETE -> persisted Quiz -> independent answer -> 3 stars')
except Exception as error:
    result['status']='FAIL'; result['failure']=str(error); raise
finally:
    (audit.OUT/'real-lesson.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

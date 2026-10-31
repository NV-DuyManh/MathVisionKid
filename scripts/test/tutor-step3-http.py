"""Real HTTP acceptance: reading 3 -> exact maths -> persisted Quiz, offline AI."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import re
import time
from fractions import Fraction
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'report/tutor-step3-blocker'
spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('smart-quiz-runtime-audit.py'))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
BASE=os.getenv('TUTOR_QA_BASE','http://127.0.0.1:18080/api/v1')
DB=os.getenv('TUTOR_QA_DB','mathvision_tutor_step3_20261028')
TREE='Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?'
result={'environment':'real HTTP Spring + FastAPI + PostgreSQL; no cloud required','requests':[],'turns':[]}

def solve(expression):
    def visit(node):
        if isinstance(node,ast.Expression): return visit(node.body)
        if isinstance(node,ast.Constant) and type(node.value) is int: return Fraction(node.value)
        if isinstance(node,ast.BinOp):
            a,b=visit(node.left),visit(node.right)
            if isinstance(node.op,ast.Add): return a+b
            if isinstance(node.op,ast.Sub): return a-b
            if isinstance(node.op,ast.Mult): return a*b
            if isinstance(node.op,ast.Div): return a/b
        raise ValueError('Unexpected non-arithmetic expression')
    return str(visit(ast.parse(expression.translate(str.maketrans({'×':'*','÷':'/','−':'-',':':'/'})),mode='eval')))

def account():
    email='tutor-step3-'+uuid4().hex[:10]+'@test.invalid'
    audit.sql("INSERT INTO users(id,email,password_hash,role,display_name,active,created_at,updated_at) SELECT '"+str(uuid4())+"','"+email+"',password_hash,'STUDENT','Bạn học',true,now(),now() FROM users WHERE email='minh.student@mathvision.local'; INSERT INTO students(student_id,grade_level) SELECT id,5 FROM users WHERE email='"+email+"';",DB)
    code,data,_=audit.http(BASE+'/auth/login',{'email':email,'password':'MathVision123!'})
    assert code==200
    return data['accessToken']

def call(path,body=None,expected=200,auth=None):
    started=time.monotonic()
    status,data,headers=audit.http(BASE+path,body,token if auth is None else auth)
    result['requests'].append({'path':path,'http':status,'elapsedMs':round((time.monotonic()-started)*1000),
        'requestId':headers.get('X-Request-ID') or headers.get('X-Request-Id')})
    assert status==expected,(path,status,data.get('error',{}).get('code'))
    return data

try:
    token=account();other=account()
    for suffix in ('',' (2 điểm)'):
        source=TREE+suffix
        prep=call('/student/quizzes/prepare',{'workflowKey':str(uuid4()),'revision':1,'confirmedProblemText':source,'problemConfirmed':True})
        started=time.monotonic()
        current=call('/student/tutor/lesson',{'problemText':source,'workText':'','problemConfirmed':True,'workConfirmed':False,'guidedUnderstanding':True,'startWithReading':True})
        sid=current['sessionId']
        for i in range(3):
            step=current['step'];choices=step['choices']
            if i==0: answer=next(c for c in choices if '1/3' in c and 'bao nhiêu' not in c)
            elif i==1: answer=next(c for c in choices if 'bao nhiêu' in c)
            else:
                quote=re.search('«(.*?)»',step['question'])
                answer='Đúng' if quote and not re.match(r'^(Hỏi|Tính)\b',quote[1],re.I) else 'Sai'
            current=call('/student/tutor/lesson/answer',{'sessionId':sid,'revision':current['revision'],'answer':answer,'hint':False})
            result['turns'].append({'step':i+1,'status':current['status'],'revision':current['revision'],'completed':len(current['completed'])})
            assert current['revision']==i+1 and current['status']!='TRY_AGAIN'
        assert current['stepIndex']==3 and len(current['completed'])==3
        for _ in range(50):
            if not current['preparingMath']: break
            assert current['status']=='PREPARING'
            time.sleep(.1)
            current=call('/student/tutor/lesson/preparation',{'sessionId':sid,'revision':3,'retry':False})
        assert current['step']['kind']=='MATH' and current['stepIndex']==3
        assert '60' not in json.dumps({k:v for k,v in current.items() if k!='sessionId'},ensure_ascii=False)
        result.setdefault('transitionMs',[]).append(round((time.monotonic()-started)*1000))
        call('/student/tutor/lesson/preparation',{'sessionId':sid,'revision':3},expected=410,auth=other)
        for expected in ('11/15','4/15','60'):
            answer=solve(current['step']['expression']);assert answer==expected
            current=call('/student/tutor/lesson/answer',{'sessionId':sid,'revision':current['revision'],'answer':answer,'hint':False})
            result['turns'].append({'mathAnswer':answer,'status':current['status'],'revision':current['revision']})
        assert current['status']=='COMPLETE' and current['completed'][-1]['answer']=='60'
        offer=call('/student/quizzes/from-learning',{'sourceType':'LESSON','sourceId':sid})
        assert offer['offered'] and offer['quiz']['status']=='READY'
        qid=offer['quiz']['quizId']
        deferred=call('/student/quizzes/'+qid+'/defer',{});assert deferred['status']=='DEFERRED'
        quiz=call('/student/quizzes/'+qid+'/start',{})
        shares=[Fraction(a+'/'+b) for a,b in re.findall(r'(\d+)/(\d+)',quiz['questionText'])]
        count=int(re.search(r'Biết[^\d]*(\d+)',quiz['questionText'])[1])
        answer=Fraction(count)/(1-sum(shares));assert answer.denominator==1 and answer!=60
        graded=call('/student/quizzes/'+qid+'/submit',{'requestId':str(uuid4()),'answer':str(answer)})
        assert graded['quiz']['status']=='COMPLETED' and graded['quiz']['stars']==3
        result.setdefault('quizResults',[]).append({'quizId':qid,'answer':str(answer),'stars':3,'status':'COMPLETED'})
        persisted=audit.sql("SELECT completed||':'||length(problem_text) FROM quiz_learning_sources WHERE source_id='"+sid+"'",DB)
        assert persisted=='true:'+str(len(source))
        result.setdefault('databaseEvidence',[]).append({'sourceId':sid,'completed':True,'confirmedTextChars':len(source),'quizId':qid})
    assert all(r['http']!=503 for r in result['requests'])
    result['status']='PASS'
    print('PASS reading 1/3 -> 2/3 -> 3/3 -> MATH -> COMPLETE -> READY Quiz -> DEFERRED -> 3 stars (2 source variants)')
except Exception as exc:
    result['status']='FAIL';result['failure']=str(exc);raise
finally:
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/os.getenv('TUTOR_QA_OUTPUT','http-integration.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

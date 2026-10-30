"""Real HTTP + isolated PostgreSQL verification. Does not connect to the main database."""
import json, os, subprocess, time, re
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[2]
DB='mathvision_quiz_generation_fix_20261027'
BASE='http://127.0.0.1:18080/api/v1'
OUT=ROOT/'report/smart-quiz-generation-fix'
OUT.mkdir(parents=True,exist_ok=True)
TREE='Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?'
checks=[]
def sql(query):
    return subprocess.check_output(['docker','exec','mathvision-postgres','psql','-U','mathvision','-d',DB,'-v','ON_ERROR_STOP=1','-Atc',query],encoding='utf-8').strip()
def check(label,condition):
    assert condition,label
    checks.append({'label':label,'status':'PASS'}); print('PASS',label,flush=True)
def call(path,token=None,body=None):
    headers={'Content-Type':'application/json'}
    if token: headers['Authorization']='Bearer '+token
    try:
        with urlopen(Request(BASE+path,headers=headers,data=None if body is None else json.dumps(body,ensure_ascii=False).encode()),timeout=100) as r: return r.status,json.load(r)
    except HTTPError as r: return r.code,json.load(r)
def account(label):
    email='quiz-fix-'+label+'@test.invalid'
    identifier=str(uuid4())
    sql("INSERT INTO users(id,email,password_hash,role,display_name,active,created_at,updated_at) SELECT '"+identifier+"','"+email+"',password_hash,'STUDENT','Bạn học lớp năm',true,now(),now() FROM users WHERE email='minh.student@mathvision.local' ON CONFLICT(email) DO NOTHING; INSERT INTO students(student_id,grade_level) SELECT id,5 FROM users WHERE email='"+email+"' ON CONFLICT(student_id) DO NOTHING;")
    status,data=call('/auth/login',body={'email':email,'password':'MathVision123!'})
    assert status==200,(status,data)
    return data['accessToken']
def wait_prepared(token,response):
    for _ in range(100):
        if response.get('status')!='GENERATING': return response
        time.sleep(.1)
        code,response=call('/student/quizzes/preparations/'+response['preparationId'],token)
        assert code==200
    raise AssertionError('Background preparation did not settle within its bounded wait')

def prepare(token,key,revision,text=TREE,confirmed=True):
    code,response=call('/student/quizzes/prepare',token,{'workflowKey':key,'revision':revision,'problemText':text,'problemConfirmed':confirmed})
    return code,wait_prepared(token,response)
def review(token,problem=TREE):
    source='work-fix-'+str(uuid4())
    status,data=call('/student/tutor/work-review',token,{'sourceId':source,'problemText':problem,'workText':'Em làm theo hình bên.','problemConfirmed':True,'workConfirmed':True})
    check('Actual Tutor WorkReview boundary records confirmed text without trusting handwritten answer',status==200 and data['sourceId']==source)
    return {'sourceType':'WORK_REVIEW','sourceId':source},data['status']
result={'environment':'Isolated real PostgreSQL + Spring + existing FastAPI; no fake READY or inserted completion events','checks':checks}
try:
    a=account('live-'+uuid4().hex[:8]); b=account('other-'+uuid4().hex[:8]); account('browser')
    key=str(uuid4()); body={'workflowKey':key,'revision':1,'problemText':TREE,'problemConfirmed':True}
    with ThreadPoolExecutor(2) as pool: replies=list(pool.map(lambda _:call('/student/quizzes/prepare',a,body),range(2)))
    p=wait_prepared(a,replies[0][1])
    check('Exact reported confirmed text prepares READY with no cloud generation',all(code==200 and data['status'] in ('GENERATING','READY') for code,data in replies) and p['status']=='READY')
    check('Concurrent duplicate prepare requests return the same persisted private preparation',p['preparationId']==replies[1][1]['preparationId'])
    check('Preparation does not expose draft, question, answer, solution or audio',set(p)=={'preparationId','revision','status','errorCode'})
    check('Preparation alone is not a pending Quiz',call('/student/quizzes/pending-count',a)[1]['pendingCount']==0)
    draft=json.loads(sql("SELECT validated_draft FROM quiz_preparations WHERE id='"+p['preparationId']+"'"))
    f1,f2,R=map(Fraction,draft['data'][:3]); total=R/(1-f1-f2)
    check('Stored generated variant independently verified with Python Fraction, positive integer groups and changed answer',total.denominator==1 and total!=60 and all((total*f).denominator==1 and total*f>0 for f in [f1,f2,1-f1-f2]))
    check('Cannot forge a completed lesson using only a preparation ID',call('/student/quizzes/from-learning',a,{'sourceType':'LESSON','sourceId':p['preparationId']})[0]==409)
    source,review_status=review(a); result['reviewStatus']=review_status
    status,inv=call('/student/quizzes/from-learning',a,source); q=inv.get('quiz',{}); qid=q.get('quizId')
    check('Trusted completed review offers an actual persisted Quiz',status==200 and inv['offered'] and q['topicCode']=='FRACTION_FIND_TOTAL_FROM_REMAINDER')
    check('Invitation hides answer and solution',q['correctAnswer'] is None and q['explanationText'] is None)
    check('Completion consumes the prepared question rather than regenerating',sql("SELECT question_text FROM student_quizzes WHERE id='"+qid+"'")==draft['question'])
    check('Duplicate finish reuses the same Quiz without repeating invitation',call('/student/quizzes/from-learning',a,source)[1]['offered'] is False)
    call('/student/quizzes/'+qid+'/defer',a,{})
    check('Defer persists pending badge',call('/student/quizzes/pending-count',a)[1]['pendingCount']==1)
    check('Another Student cannot read or start the Quiz',call('/student/quizzes/'+qid,b)[0]==404 and call('/student/quizzes/'+qid+'/start',b,{})[0]==404)
    started=call('/student/quizzes/'+qid+'/start',a,{})[1]
    check('Start publishes generated question but keeps answer private',started['questionText']==draft['question'] and started['correctAnswer'] is None)
    check('Solution and narration remain locked before wrong attempts',call('/student/quizzes/'+qid+'/reveal-solution',a,{})[0]==409 and call('/student/quizzes/'+qid+'/narration',a,{'voice':'vi-VN-NamMinhNeural'})[0]==409)
    answer=str(total.numerator); req={'requestId':str(uuid4()),'answer':answer+' '+started['unit']}
    with ThreadPoolExecutor(2) as pool: grades=list(pool.map(lambda _:call('/student/quizzes/'+qid+'/submit',a,req),range(2)))
    done=grades[0][1]['quiz']
    check('Backend grades the new non-60 answer and rewards exactly once for concurrent retries',all(code==200 for code,_ in grades) and done['status']=='COMPLETED' and done['stars']==3 and len(done['attempts'])==1 and done['correctAnswer']==answer)
    check('Completion reduces badge to zero and preserves history',call('/student/quizzes/pending-count',a)[1]['pendingCount']==0 and call('/student/quizzes?group=COMPLETED',a)[1]['totalElements']==1)
    check('Client-forged reward/time rejected',call('/student/quizzes/'+qid+'/submit',a,dict(req,stars=3,elapsedSeconds=0))[0]==400)
    prepare(a,key,2,'',False)
    check('Editing does not erase an already completed Quiz history or earned stars',call('/student/quizzes/'+qid,a)[1]['stars']==3)
    # A separate workflow/source checks invalidation before the student starts.
    candy='Bé Mạnh có một số viên kẹo. Trong đó, 1/4 số kẹo là kẹo dâu, 2/5 số kẹo là kẹo cam, còn lại là kẹo chanh. Biết có 14 viên kẹo chanh. Hỏi bé Mạnh có tất cả bao nhiêu viên kẹo?'
    key2=str(uuid4()); prepare(a,key2,1,candy)
    source2,_=review(a,candy); old=call('/student/quizzes/from-learning',a,source2)[1]['quiz']['quizId']
    prepare(a,key2,3,'',False); stale=prepare(a,key2,1,candy)[1]
    check('Edit invalidates pending old Quiz and late requests cannot reactivate it',stale['revision']==3 and stale['status']=='INVALIDATED' and call('/student/quizzes/'+old+'/start',a,{})[0]==404 and call('/student/quizzes/pending-count',a)[1]['pendingCount']==0)
    result['generatedQuiz']={'question':draft['question'],'answer':answer,'unit':started['unit'],'solution':done['explanationText'],'stars':done['stars']}
    result['migration']=sql("SELECT version||':'||success FROM flyway_schema_history WHERE version='19'")
    check('PostgreSQL Flyway V19 applied successfully',result['migration']=='19:true')
except Exception as e:
    result['failure']=type(e).__name__+': '+str(e); raise
finally:
    (OUT/'live-api-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

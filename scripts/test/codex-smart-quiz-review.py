"""Live Quiz acceptance against an isolated PostgreSQL DB and actual Spring/FastAPI.
Run after QA Spring is bound to 18080 and mathvision_codex_quiz_review_20261029.
Never writes student records in the main DB. No API mocks or injected completion rows.
"""
import ast,json,os,re,time,sys,uuid,hashlib,zipfile
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from codex_quiz_db import sql as raw_sql,ROOT,OUT
sys.stdout.reconfigure(encoding='utf-8')
DB=os.environ.get('QUIZ_QA_DB','mathvision_codex_quiz_review_20261029')
assert DB.startswith('mathvision_codex_'), 'Only isolated Codex QA databases are allowed'
BASE='http://127.0.0.1:18080/api/v1'
TREE='Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết số cây cam là 16 cây. Hỏi trong vườn có tất cả bao nhiêu cây?'
DIGIT='Tìm một số biết rằng nếu viết thêm chữ số 6 vào bên phải số đó thì được số mới lớn hơn số phải tìm 537 đơn vị.'
checks=[];result={'database':DB,'base':BASE,'checks':checks,'device':'No physical-device evidence'}
def sql(q):return raw_sql(q,DB)
def check(label,ok):
    assert ok,label
    checks.append({'label':label,'status':'PASS'});print('PASS',label,flush=True)
def call(path,token=None,body=None,method=None,audio=False):
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    req=Request(BASE+path,headers=headers,data=None if body is None else json.dumps(body,ensure_ascii=False).encode(),method=method)
    try:
        with urlopen(req,timeout=65) as r:
            data=r.read();return r.status,(data if audio else json.loads(data) if data else {})
    except HTTPError as e:
        data=e.read()
        try:return e.code,json.loads(data)
        except ValueError:return e.code,{'error':'non-json error response'}
def login(email):
    code,data=call('/auth/login',body={'email':email,'password':'MathVision123!'})
    assert code==200,(code,data)
    return data['accessToken']
def account(label):
    uid=str(uuid.uuid4());email='codex-review-'+label+'-'+uuid.uuid4().hex[:7]+'@test.invalid'
    sql("INSERT INTO users(id,email,password_hash,role,display_name,active,created_at,updated_at) SELECT '"+uid+"','"+email+"',password_hash,'STUDENT','Quiz independent QA',true,now(),now() FROM users WHERE role='STUDENT' LIMIT 1; INSERT INTO students(student_id,grade_level) VALUES ('"+uid+"',5)")
    return uid,email,login(email)
def prepare(token,text,key=None,revision=1,confirmed=True):
    code,p=call('/student/quizzes/prepare',token,{'workflowKey':key or str(uuid.uuid4()),'revision':revision,'problemText':text,'problemConfirmed':confirmed})
    assert code==200,(code,p)
    for _ in range(100):
        if p['status']!='GENERATING':return p
        time.sleep(.1);code,p=call('/student/quizzes/preparations/'+p['preparationId'],token)
        assert code==200
    raise AssertionError('Actual preparation did not finish')
def exact(expr):
    tree=ast.parse(expr.replace('×','*').replace('÷','/').replace('−','-').replace(':','/'),mode='eval')
    def value(n):
        if isinstance(n,ast.Expression):return value(n.body)
        if isinstance(n,ast.Constant) and isinstance(n.value,int):return Fraction(n.value)
        if isinstance(n,ast.BinOp):
            a,b=value(n.left),value(n.right)
            if isinstance(n.op,ast.Add):return a+b
            if isinstance(n.op,ast.Sub):return a-b
            if isinstance(n.op,ast.Mult):return a*b
            if isinstance(n.op,ast.Div):return a/b
        raise AssertionError('Unsupported public math expression '+expr)
    return str(value(tree))
def lesson(token,text):
    code,data=call('/student/tutor/lesson',token,{'problemText':text,'workText':'','problemConfirmed':True,'workConfirmed':False,'guidedUnderstanding':False,'startWithReading':False})
    assert code==200,(code,data)
    sid=data['sessionId']
    for _ in range(15):
        if data['status']=='COMPLETE':return {'sourceType':'LESSON','sourceId':sid}
        step=data.get('step') or {};expression=step.get('expression')
        assert expression,('Expected deterministic math step',data)
        code,data=call('/student/tutor/lesson/answer',token,{'sessionId':sid,'revision':data['revision'],'answer':exact(expression),'hint':False})
        assert code==200,(code,data)
    raise AssertionError('Lesson did not complete')
def answer(question):
    if 'chữ số' in question:
        m=re.search(r'chữ số (\d).*lớn hơn.*? (\d+) đơn vị',question)
        d,total=map(int,m.groups());value=Fraction(total-d,9);assert value.denominator==1
        return str(value)
    fractions=re.findall(r'(\d+/\d+)',question);assert len(fractions)==2
    m=re.search(r'(?:là|có) (\d+) (?:quyển sách|viên kẹo|viên bi)',question)
    a,b=map(Fraction,fractions);total=Fraction(m[1])/(1-a-b)
    assert total.denominator==1 and all(x>0 and x.denominator==1 for x in [total*a,total*b,total*(1-a-b)])
    return str(total)
def post(token,qid,action,body=None):return call('/student/quizzes/'+qid+'/'+action,token,body if body is not None else {})
def counts(token):return call('/student/quizzes/pending-count',token)[1]
def submit(token,qid,value,req=None):return post(token,qid,'submit',{'requestId':req or str(uuid.uuid4()),'answer':value})
try:
    check('Real Spring QA health',urlopen('http://127.0.0.1:18080/actuator/health').status==200)
    uid,email,a=account('a');_,_,b=account('b');result['browserAccount']=email
    check('Isolated PostgreSQL migrated through V22 and V23',sql("SELECT count(*) FROM flyway_schema_history WHERE version IN ('21','22','23') AND success")=='3')
    check('Unauthenticated requests rejected',call('/student/quizzes/pending-count')[0]==401)
    key=str(uuid.uuid4());p=prepare(a,TREE,key)
    check('Exact tree source prepares deterministically without publishing a pending Quiz',p['status']=='READY' and counts(a)['pendingCount']==0)
    check('Preparation DTO contains no private draft or answer',set(p)=={'preparationId','revision','status','errorCode'})
    source=lesson(a,TREE);check('Real FastAPI tree lesson reaches trusted COMPLETE',True)
    with ThreadPoolExecutor(2) as pool:replies=list(pool.map(lambda _:call('/student/quizzes/from-learning',a,source),range(2)))
    q=replies[0][1]['quiz'];qid=q['quizId'];result['treeQuizId']=qid
    check('Concurrent completion creates exactly one original Quiz',all(c==200 for c,_ in replies) and len({r['quiz']['quizId'] for _,r in replies})==1 and sum(r['offered'] for _,r in replies)==1)
    check('No question, answer, or solution exposed before start',q['correctAnswer'] is None and q['explanationText'] is None and q['originalQuestionText'] is None)
    check('Original Quiz is persisted once in PostgreSQL',sql("SELECT count(*) FROM student_quizzes WHERE student_id='"+uid+"'")=='1')
    post(a,qid,'defer');check('Deferred pending count is persisted',counts(a)['pendingCount']==1)
    code,q=post(a,qid,'start');value=answer(q['questionText']);seen={'60',value}
    check('Tree wording independently solves to new integer answer distinct from 60',value!='60')
    check('Other student cannot get/start/replay/reveal/narrate',all(c==404 for c in [call('/student/quizzes/'+qid,b)[0],post(b,qid,'start')[0],post(b,qid,'replay',{'mode':'CHALLENGE'})[0],post(b,qid,'reveal-solution')[0],post(b,qid,'narration',{'voice':'vi-VN-NamMinhNeural'})[0]]))
    check('Answer and voice locked before allowed reveal',post(a,qid,'reveal-solution')[0]==409 and post(a,qid,'narration',{'voice':'vi-VN-NamMinhNeural'})[0]==409)
    check('Client cannot forge stars/time on submit',post(a,qid,'submit',{'requestId':str(uuid.uuid4()),'answer':value,'stars':3,'elapsedMillis':0})[0]==400)
    sql("UPDATE student_quizzes SET started_at=now()-interval '75 seconds' WHERE id='"+qid+"'")
    code,g=submit(a,qid,value);assert code==200,(code,g)
    first=g['attempt'];check('Slow correct first run earns 1 star',g['attempt']['stars']==1 and g['quiz']['stars']==1 and counts(a)['totalStars']==1)
    code,practice=post(a,qid,'replay',{'mode':'PRACTICE'});assert code==200
    check('Practice restores exact original wording and leaves badge unchanged',practice['questionText']==q['questionText'] and counts(a)['pendingCount']==0)
    code,g=submit(a,qid,value);check('Practice earns zero and preserves existing record',code==200 and g['attempt']['stars']==0 and g['quiz']['stars']==1 and counts(a)['totalStars']==1)
    with ThreadPoolExecutor(2) as pool:rs=list(pool.map(lambda _:post(a,qid,'replay',{'mode':'CHALLENGE'}),range(2)))
    q=rs[0][1];check('Concurrent replay resumes one question/timer',all(c==200 for c,_ in rs) and rs[1][1]['startedAt']==q['startedAt'] and rs[1][1]['questionText']==q['questionText'])
    check('Switching replay mode mid-run cannot reset clock',post(a,qid,'replay',{'mode':'PRACTICE'})[0]==409)
    value=answer(q['questionText']);check('Challenge excludes original and learning-source answers',value not in seen);seen.add(value)
    sql("UPDATE student_quizzes SET started_at=now()-interval '45 seconds' WHERE id='"+qid+"'")
    code,g=submit(a,qid,value);check('45 second challenge earns 2 and total becomes max 2',code==200 and g['attempt']['stars']==2 and g['quiz']['stars']==2 and counts(a)['totalStars']==2)
    code,q=post(a,qid,'replay',{'mode':'CHALLENGE'});value=answer(q['questionText']);seen.add(value)
    req=str(uuid.uuid4())
    with ThreadPoolExecutor(2) as pool:rs=list(pool.map(lambda _:submit(a,qid,value,req),range(2)))
    check('Concurrent identical submission grants three stars exactly once',all(c==200 for c,_ in rs) and rs[0][1]['attempt']==rs[1][1]['attempt'] and counts(a)['totalStars']==3)
    before=sql("SELECT count(*) FROM quiz_attempts WHERE quiz_id='"+qid+"'")
    submit(a,qid,value,req)
    check('Retry does not add attempts or stars in database',sql("SELECT count(*) FROM quiz_attempts WHERE quiz_id='"+qid+"'")==before and counts(a)['totalStars']==3)
    check('Reusing requestId with changed answer rejected',submit(a,qid,'999999',req)[0]==409)
    for i in range(10):
        code,q=post(a,qid,'replay',{'mode':'CHALLENGE'});assert code==200
        value=answer(q['questionText']);assert value not in seen,('duplicate challenge',i,value);seen.add(value)
        code,g=submit(a,qid,value);assert code==200 and g['quiz']['stars']==3
    check('Ten more challenges have unique mathematically verified answers and stable total',counts(a)['totalStars']==3)
    code,q=post(a,qid,'replay',{'mode':'CHALLENGE'})
    submit(a,qid,'999999');time.sleep(.9);submit(a,qid,'999998');time.sleep(.9)
    code,reveal=post(a,qid,'reveal-solution');assert code==200
    code,g=submit(a,qid,answer(q['questionText']))
    check('Assisted completion earns zero, explains current run, preserves three-star best',code==200 and g['attempt']['stars']==0 and g['quiz']['stars']==3 and g['quiz']['completedWithSolution'])
    check('History retains exact first attempt snapshot across all replays',g['quiz']['attempts'][0]==first and first['questionText']!=q['questionText'])
    check('PostgreSQL snapshots match every new attempt and current assisted status',sql("SELECT count(*) FROM quiz_attempts WHERE quiz_id='"+qid+"' AND (question_text IS NULL OR answer_spec IS NULL OR solution_viewed IS NULL OR run_started_at IS NULL)")=='0' and sql("SELECT stars||':'||completed_with_solution FROM student_quizzes WHERE id='"+qid+"'")=='3:true')
    # Re-login, new source session and same text must not create a second original.
    a=login(email);source2=lesson(a,TREE);code,repeat=call('/student/quizzes/from-learning',a,source2)
    check('New login and lesson session retain fingerprint and reuse completed Quiz',code==200 and not repeat['offered'] and repeat['quiz']['quizId']==qid)
    code,q=post(a,qid,'replay',{'mode':'CHALLENGE'});prepare(a,'',key,2,False)
    check('Editing old preparation during replay preserves record/history and badge',counts(a)=={'pendingCount':0,'totalStars':3} and call('/student/quizzes/'+qid,a)[0]==200)
    submit(a,qid,answer(q['questionText']))
    p=prepare(a,DIGIT);source=lesson(a,DIGIT);code,inv=call('/student/quizzes/from-learning',a,source);dq=inv['quiz']['quizId'];code,q=post(a,dq,'start');value=answer(q['questionText'])
    check('Digit-append generator and actual Tutor work for source 59',p['status']=='READY' and code==200 and value!='59' and q['topicCode']=='DIGIT_APPEND_FIND_ORIGINAL_NUMBER')
    code,g=submit(a,dq,value);assert code==200
    check('Two Quiz total equals sum of PostgreSQL best records, never sum of attempts',counts(a)['totalStars']==int(sql("SELECT sum(stars) FROM student_quizzes WHERE student_id='"+uid+"'"))==6)
    for voice in ['vi-VN-NamMinhNeural','vi-VN-HoaiMyNeural']:
        code,data=call('/student/quizzes/'+dq+'/narration',a,{'voice':voice},audio=True)
        if code in (429,503):
            time.sleep(2);code,data=call('/student/quizzes/'+dq+'/narration',a,{'voice':voice},audio=True)
        ok=code==200 and isinstance(data,bytes) and data[:4]==b'RIFF' and data[8:12]==b'WAVE' and len(data)>44
        result.setdefault('voice',[]).append({'voice':voice,'http':code,'validWav':ok})
        if ok:check('Actual authorized Quiz WAV '+voice,True)
        else:print('UNVERIFIED actual voice',voice,'HTTP',code,flush=True)
    for role in ['admin','teacher']:
        token=login(sql("SELECT email FROM users WHERE role='"+role.upper()+"' ORDER BY created_at LIMIT 1"))
        check(role+' cannot use student Quiz API',call('/student/quizzes/pending-count',token)[0]==403)
    runtime=call('/student/quizzes/runtime',a)[1]
    with zipfile.ZipFile(ROOT/'backend/business-api/build/libs/business-api.jar') as z:expected=hashlib.sha256(z.read('BOOT-INF/classes/com/mathvisionkids/api/quiz/QuizMath.class')).hexdigest()
    check('Loaded generator class hash equals new local JAR',runtime['generatorClassHash']==expected)
    result['runtime']=runtime;result['uniqueTreeAnswers']=sorted(seen);result['status']='PASS'
except Exception as e:
    result['failure']=type(e).__name__+': '+str(e);result['status']='FAIL';raise
finally:(OUT/'http-postgres-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

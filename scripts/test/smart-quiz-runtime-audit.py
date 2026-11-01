"""Read-only runtime evidence; secrets and student text are never written to reports."""
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'report/smart-quiz-runtime-root-cause'
OUT.mkdir(parents=True, exist_ok=True)

def sql(query, db='mathvision'):
    return subprocess.check_output(['docker', 'exec', 'mathvision-postgres', 'psql', '-U', 'mathvision', '-d', db, '-Atc', query], encoding='utf-8').strip()

def http(url, body=None, token=None, headers=None):
    opts = {'Content-Type': 'application/json', **(headers or {})}
    if token:
        opts['Authorization'] = 'Bearer ' + token
    req = Request(url, data=None if body is None else json.dumps(body, ensure_ascii=False).encode(), headers=opts)
    try:
        response = urlopen(req, timeout=45)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response), dict(response.headers)

def baseline():
    backup = Path.home() / 'smart-quiz-runtime-baseline-20261028'
    backup.mkdir(exist_ok=True)
    names = subprocess.check_output(['git', 'ls-files', '-m', '-o', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    manifest = {}
    for name in filter(None, names):
        path = ROOT / name
        if not path.is_file() or name.startswith('report/smart-quiz-runtime-root-cause/'):
            continue
        dest = backup / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copy2(path, dest)
        manifest[name] = hashlib.sha256(dest.read_bytes()).hexdigest()
    (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    evidence = {'at': datetime.now(timezone.utc).isoformat(), 'backupFiles': len(manifest)}
    evidence['migrations'] = sql('SELECT version||\':\'||success FROM flyway_schema_history ORDER BY installed_rank DESC LIMIT 5').splitlines()
    evidence['preparationStates'] = sql("SELECT status||':'||coalesce(error_code,'-')||':'||count(*) FROM quiz_preparations GROUP BY status,error_code").splitlines()
    evidence['quizCount'] = int(sql('SELECT count(*) FROM student_quizzes'))
    text = sql('SELECT problem_text FROM quiz_learning_sources ORDER BY created_at DESC LIMIT 1')
    evidence['confirmedText'] = {'length': len(text), 'sha256': hashlib.sha256(text.encode()).hexdigest(), 'hasExamScoreSuffix': text.endswith('(2 điểm)')}
    evidence['recentProfileGrade'] = sql('SELECT s.grade_level FROM quiz_learning_sources q JOIN students s ON s.student_id=q.student_id ORDER BY q.created_at DESC LIMIT 1')
    jar = ROOT / 'backend/business-api/build/libs/business-api.jar'
    evidence['jar'] = {'modifiedAt': datetime.fromtimestamp(jar.stat().st_mtime, timezone.utc).isoformat(), 'sha256': hashlib.sha256(jar.read_bytes()).hexdigest()}
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        java = tmp / 'Probe.java'
        java.write_text('import com.mathvisionkids.api.quiz.QuizMath; public class Probe { public static void main(String[] args) throws Exception { String s=new String(System.in.readAllBytes(),java.nio.charset.StandardCharsets.UTF_8); var p=QuizMath.classify(s,true); System.out.println(p.isPresent()?"SUPPORTED:"+p.get().answer()+":grade="+p.get().grade():"UNSUPPORTED"); }}', encoding='utf-8')
        with zipfile.ZipFile(jar) as archive:
            for name in archive.namelist():
                if name.startswith('BOOT-INF/classes/com/mathvisionkids/api/quiz/') and name.endswith('.class'):
                    dest = tmp / name.removeprefix('BOOT-INF/classes/')
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(archive.read(name))
        subprocess.run(['javac', '-encoding', 'UTF-8', '-cp', str(tmp), '-d', str(tmp), str(java)], check=True, capture_output=True)
        evidence['runningJarParserWithActualConfirmedText'] = subprocess.check_output(['java', '-cp', str(tmp), 'Probe'], input=text.encode()).decode().strip()
        evidence['runningJarParserWithoutExamScoreSuffix'] = subprocess.check_output(['java', '-cp', str(tmp), 'Probe'], input=text.removesuffix(' (2 điểm)').encode()).decode().strip()
    status, auth, _ = http('http://127.0.0.1:8080/api/v1/auth/login', {'email': 'minh.student@mathvision.local', 'password': 'MathVision123!'})
    evidence['runtimeAuthStatus'] = status
    if status == 200:
        token = auth['accessToken']
        _, me, _ = http('http://127.0.0.1:8080/api/v1/me', token=token)
        student = me.get('id') or me.get('userId')
        if student:
            source = sql("SELECT source_id FROM quiz_learning_sources WHERE student_id='" + str(student) + "' AND completed ORDER BY created_at DESC LIMIT 1")
            if source:
                code, result, headers = http('http://127.0.0.1:8080/api/v1/student/quizzes/from-learning', {'sourceType': 'LESSON', 'sourceId': source}, token)
                evidence['actualCompletedSourceRequest'] = {'status': code, 'errorCode': result.get('error', {}).get('code'), 'requestId': headers.get('X-Request-ID')}
    (OUT / 'before.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(evidence, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    baseline()

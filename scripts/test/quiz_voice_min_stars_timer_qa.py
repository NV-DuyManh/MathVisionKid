"""Real PostgreSQL/Spring/TTS acceptance. Mutations are restricted to an isolated QA DB.

setup clones the current local DB into a new database; run starts the built Spring
JAR there. No student account in the original DB is used for API mutations.
Private backup/audio/process artifacts stay under ignored runtime/.
"""
import array
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import uuid
import wave
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'runtime/quiz-voice-min-stars-timer-20261031'
OUT.mkdir(parents=True, exist_ok=True)
DB = 'mathvision_voice_stars_timer_20261031'
BASE = 'http://127.0.0.1:18082/api/v1'
assert DB.startswith('mathvision_voice_stars_timer_')
checks = []


def sql(query, database=DB):
    process = subprocess.run(['docker', 'exec', '-i', 'mathvision-postgres', 'psql',
        '-U', 'mathvision', '-d', database, '-At', '-v', 'ON_ERROR_STOP=1'],
        input=query.encode(), capture_output=True, timeout=45)
    if process.returncode:
        raise RuntimeError(process.stderr.decode('utf-8', 'replace'))
    return process.stdout.decode('utf-8').strip()


def snapshot(database):
    return json.loads(sql("SELECT json_build_object('quizzes',(SELECT json_agg(q ORDER BY id) FROM student_quizzes q),"
        "'attempts',(SELECT json_agg(a ORDER BY id) FROM quiz_attempts a),"
        "'migrations',(SELECT json_agg(f ORDER BY installed_rank) FROM flyway_schema_history f))", database))


def setup():
    if sql(f"SELECT 1 FROM pg_database WHERE datname='{DB}'", 'postgres'):
        raise RuntimeError('QA database exists; inspect existing evidence instead of overwriting it')
    before = snapshot('mathvision')
    (OUT / 'main-before.json').write_text(json.dumps(before, indent=2), encoding='utf-8')
    dump = subprocess.run(['docker', 'exec', 'mathvision-postgres', 'pg_dump', '-U', 'mathvision',
        '--no-owner', '--no-privileges', 'mathvision'], capture_output=True, check=True, timeout=60).stdout
    (OUT / 'main-before.sql').write_bytes(dump)
    sql('CREATE DATABASE ' + DB, 'postgres')
    restored = subprocess.run(['docker', 'exec', '-i', 'mathvision-postgres', 'psql', '-U', 'mathvision',
        '-d', DB, '-v', 'ON_ERROR_STOP=1'], input=dump, capture_output=True, timeout=60)
    assert restored.returncode == 0, 'QA restore failed'
    sql('CREATE EXTENSION IF NOT EXISTS pgcrypto')
    print('Created isolated QA clone and private pre-migration backup', flush=True)


def launch():
    with socket.socket() as connection:
        assert connection.connect_ex(('127.0.0.1', 18082)) != 0, 'QA port already occupied'
    environment = os.environ.copy()
    for file in [ROOT / '.env', ROOT / 'backend/business-api/.env']:
        for line in file.read_text(encoding='utf-8-sig').splitlines() if file.exists() else []:
            match = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$', line)
            if match:
                environment[match[1]] = match[2].strip('\"\'')
    environment.update(DB_URL='jdbc:postgresql://127.0.0.1:5432/' + DB, DB_USERNAME='mathvision',
        AI_SERVICE_BASE_URL='http://127.0.0.1:8000')
    jar = ROOT / 'backend/business-api/build/libs/business-api.jar'
    digest = hashlib.sha256(jar.read_bytes()).hexdigest()
    stable = OUT / ('business-api-' + digest[:16] + '.jar')
    stable.write_bytes(jar.read_bytes())
    with (OUT / 'qa-spring.log').open('wb') as output:
        process = subprocess.Popen(['java', '-Xms32m', '-Xmx384m', '-jar', str(stable),
            '--spring.profiles.active=dev', '--server.address=127.0.0.1', '--server.port=18082',
            '--ai.gateway.mode=FASTAPI'], cwd=ROOT / 'backend/business-api', env=environment,
            stdout=output, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    (OUT / 'qa-process.json').write_text(json.dumps({'pid': process.pid, 'jarSha256': digest}))
    print('QA Spring started PID', process.pid, flush=True)


def call(path, token=None, body=None, method=None, audio=False):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = Request(BASE + path, data=None if body is None else json.dumps(body).encode(), headers=headers, method=method)
    try:
        with urlopen(request, timeout=50) as response:
            data = response.read()
            return response.status, data if audio else json.loads(data) if data else {}
    except HTTPError as error:
        return error.code, None


def check(label, condition):
    assert condition, label
    checks.append({'check': label, 'status': 'PASS'})
    print('PASS:', label, flush=True)


def run():
    before = json.loads((OUT / 'main-before.json').read_text())
    after = snapshot(DB)
    old_attempts = {row['id']: row for row in before['attempts']}
    corrected = 0
    for row in after['attempts']:
        old = old_attempts[row['id']]
        if row['stars'] != old['stars']:
            assert old['correct'] and old['stars'] == 0 and row['stars'] == 1 and old['replay_mode'] != 'PRACTICE'
            assert json.loads(sql("SELECT row_to_json(p) FROM quiz_star_policy_adjustments p WHERE attempt_id='" + row['id'] + "'"))['previous_stars'] == 0
            corrected += 1
        assert {k: v for k, v in row.items() if k != 'stars'} == {k: v for k, v in old.items() if k != 'stars'}
    check('Migration preserves every historical answer/question/timestamp and audits changed awards', corrected > 0)
    check('Migration leaves V21/V22/V23 checksums unchanged', all(
        next(x for x in after['migrations'] if x['version'] == v)['checksum'] ==
        next(x for x in before['migrations'] if x['version'] == v)['checksum'] for v in ['21', '22', '23']))
    check('No completed scored Quiz remains zero after migration', sql("SELECT count(*) FROM student_quizzes WHERE status='COMPLETED' AND replay_mode<>'PRACTICE' AND stars<1") == '0')
    uid = str(uuid.uuid4())
    email = 'quiz-voice-' + uuid.uuid4().hex[:8] + '@test.invalid'
    sql(f"INSERT INTO users(id,email,password_hash,role,display_name,active,created_at,updated_at) VALUES ('{uid}','{email}',crypt('MathVisionQA123!',gen_salt('bf')),'STUDENT','Quiz voice QA',true,now(),now()); INSERT INTO students(student_id,grade_level) VALUES ('{uid}',5)")
    code, auth = call('/auth/login', body={'email': email, 'password': 'MathVisionQA123!'})
    assert code == 200
    token = auth['accessToken']
    # Private QA login for browser/device acceptance; never report the bearer token.
    (OUT / 'qa-login.json').write_text(json.dumps({'email': email, 'password': 'MathVisionQA123!'}))

    def quiz(text):
        source = str(uuid.uuid4())
        fingerprint = hashlib.sha256(text.encode()).hexdigest()
        sql(f"INSERT INTO quiz_learning_sources(id,student_id,source_type,source_id,problem_text,fingerprint,completed,created_at) VALUES (gen_random_uuid(),'{uid}','LESSON','{source}','{text}','{fingerprint}',true,now())")
        code, invitation = call('/student/quizzes/from-learning', token, {'sourceType': 'LESSON', 'sourceId': source})
        assert code == 200
        qid = invitation['quiz']['quizId']
        code, started = call('/student/quizzes/' + qid + '/start', token, method='POST')
        assert code == 200
        return qid, started

    def submit(qid, answer, request_id=None):
        return call('/student/quizzes/' + qid + '/submit', token, {'requestId': request_id or str(uuid.uuid4()), 'answer': answer})

    def answer(qid):
        return sql(f"SELECT answer_spec FROM student_quizzes WHERE id='{qid}'")

    for seconds, expected in [(15, 3), (45, 2), (90, 1)]:
        qid, _ = quiz(f'Tính: {seconds} + 8')
        sql(f"UPDATE student_quizzes SET started_at=now()-interval '{seconds} seconds' WHERE id='{qid}' AND student_id='{uid}'")
        code, graded = submit(qid, answer(qid))
        check(f'Actual server grading at {seconds}s awards {expected} stars', code == 200 and graded['attempt']['stars'] == expected)
        _, reloaded = call('/student/quizzes/' + qid, token)
        check(f'Completion at {seconds}s freezes elapsed time', reloaded['elapsedMillis'] == graded['quiz']['elapsedMillis'])

    digit = 'Tìm một số biết rằng nếu viết thêm chữ số 9 vào bên phải số đó thì được số mới lớn hơn số phải tìm 513 đơn vị.'
    fraction = 'Tính: 1/2 + 1/3'
    voices = ['vi-VN-NamMinhNeural', 'vi-VN-HoaiMyNeural']
    for topic, text in [('digit', digit), ('fraction', fraction)]:
        qid, started = quiz(text)
        code, _ = call('/student/quizzes/' + qid + '/narration', token, {'voice': voices[0]}, audio=True)
        check(topic + ' audio remains locked before reveal', code == 409)
        for value in ['999999', '888888']:
            code, wrong = submit(qid, value)
            check(topic + ' wrong answer grants no reward', code == 200 and wrong['attempt']['stars'] == 0 and wrong['quiz']['status'] == 'IN_PROGRESS')
            time.sleep(.85)
        code, reveal = call('/student/quizzes/' + qid + '/reveal-solution', token, method='POST')
        assert code == 200 and reveal['explanationText']
        for voice in voices:
            ready = False
            for attempt in range(2):
                begin = time.monotonic()
                code, data = call('/student/quizzes/' + qid + '/narration', token, {'voice': voice}, audio=True)
                if code == 200:
                    ready = True
                    break
                assert code in [429, 503]
                time.sleep(1)
            check(topic + ' ' + voice + ' real authorized TTS returns WAV', ready)
            with wave.open(io.BytesIO(data), 'rb') as sound:
                seconds = sound.getnframes() / sound.getframerate()
                samples = array.array('h', sound.readframes(sound.getnframes()))
                rms = math.sqrt(sum(n*n for n in samples) / len(samples))
                check(topic + ' ' + voice + ' is complete non-silent PCM16 mono 16kHz', sound.getnchannels() == 1 and sound.getsampwidth() == 2 and sound.getframerate() == 16000 and seconds > .1 and rms > 1)
            (OUT / (topic + '-' + voice + '.wav')).write_bytes(data)
            code, cached = call('/student/quizzes/' + qid + '/narration', token, {'voice': voice}, audio=True)
            check(topic + ' ' + voice + ' cached audio is identical', code == 200 and cached == data)
        request_id = str(uuid.uuid4())
        code, result = submit(qid, reveal['correctAnswer'], request_id)
        check(topic + ' assisted completion earns exactly one star', code == 200 and result['attempt']['stars'] == result['quiz']['stars'] == 1)
        code, duplicate = submit(qid, reveal['correctAnswer'], request_id)
        check(topic + ' duplicate request creates no extra reward/attempt', code == 200 and duplicate['attempt'] == result['attempt'] and duplicate['quiz']['stars'] == result['quiz']['stars'] and len(duplicate['quiz']['attempts']) == len(result['quiz']['attempts']))
        original = result['quiz']
        code, practice = call('/student/quizzes/' + qid + '/replay', token, {'mode': 'PRACTICE'})
        check(topic + ' practice has an independent timer', code == 200 and practice['startedAt'] != original['startedAt'] and practice['elapsedMillis'] < 10000)
        _, practiced = submit(qid, answer(qid))
        check(topic + ' practice preserves best and earns no reward', practiced['attempt']['stars'] == 0 and practiced['quiz']['stars'] == 1)
        code, challenge = call('/student/quizzes/' + qid + '/replay', token, {'mode': 'CHALLENGE'})
        check(topic + ' challenge hides previous solution and resets timer', code == 200 and challenge['explanationText'] is None and challenge['elapsedMillis'] < 10000 and challenge['startedAt'] != practice['startedAt'])
        _, improved = submit(qid, answer(qid))
        check(topic + ' new challenge can improve one star to three', improved['attempt']['stars'] == improved['quiz']['stars'] == 3)
        call('/student/quizzes/' + qid + '/replay', token, {'mode': 'CHALLENGE'})
        sql(f"UPDATE student_quizzes SET started_at=now()-interval '90 seconds' WHERE id='{qid}' AND student_id='{uid}'")
        _, slower = submit(qid, answer(qid))
        check(topic + ' slower challenge preserves three-star record', slower['attempt']['stars'] == 1 and slower['quiz']['stars'] == 3)
    _, counts = call('/student/quizzes/pending-count', token)
    check('HTTP totalStars exactly equals PostgreSQL sum of bestStars', counts['totalStars'] == int(sql(f"SELECT sum(stars) FROM student_quizzes WHERE student_id='{uid}' AND status<>'INVALIDATED'")))
    check('QA did not mutate original database', snapshot('mathvision') == before)
    (OUT / 'acceptance.json').write_text(json.dumps({'database': DB, 'checks': checks, 'physicalPlaybackVerified': False}, indent=2))
    print('All', len(checks), 'real integration checks passed', flush=True)


def verify_main():
    before = json.loads((OUT / 'main-before.json').read_text())
    after = snapshot('mathvision')
    old = {row['id']: row for row in before['attempts']}
    changed = [row for row in after['attempts'] if row['stars'] != old[row['id']]['stars']]
    assert len(changed) == 1
    assert all({k: v for k, v in row.items() if k != 'stars'} ==
        {k: v for k, v in old[row['id']].items() if k != 'stars'} for row in after['attempts'])
    original_quizzes = {row['id']: row for row in before['quizzes']}
    assert all({k: v for k, v in row.items() if k != 'stars'} ==
        {k: v for k, v in original_quizzes[row['id']].items() if k != 'stars'} for row in after['quizzes'])
    result = dict(beforeTotalStars=sum(row['stars'] for row in before['quizzes']),
        afterTotalStars=sum(row['stars'] for row in after['quizzes']), adjustedAttempts=len(changed),
        attemptCountBefore=len(before['attempts']), attemptCountAfter=len(after['attempts']),
        nonRewardHistoryUnchanged=True, migration=27,
        zeroCompletedScored=int(sql("SELECT count(*) FROM student_quizzes WHERE status='COMPLETED' AND replay_mode<>'PRACTICE' AND stars=0", 'mathvision')))
    assert result['attemptCountBefore'] == result['attemptCountAfter'] and result['zeroCompletedScored'] == 0
    (OUT / 'main-migration-verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    {'setup': setup, 'launch': launch, 'run': run, 'verify-main': verify_main}[sys.argv[1]]()

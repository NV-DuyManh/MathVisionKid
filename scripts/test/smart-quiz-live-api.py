"""Real HTTP/PostgreSQL integration QA on an explicitly isolated local stack.

Uses the existing dev seed accounts only in the named QA database. No fake Tutor
responses, direct Quiz inserts, public deployment or production database changes.
"""
import json
import os
from pathlib import Path
import re
import secrets
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'report' / 'smart-quiz-qa'
BASE = os.environ.get('QUIZ_QA_API', 'http://127.0.0.1:18080') + '/api/v1'
OUT.mkdir(parents=True, exist_ok=True)
results = []


def call(path, token=None, body=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = Request(BASE + path, headers=headers, data=None if body is None else json.dumps(body, ensure_ascii=False).encode())
    try:
        with urlopen(request, timeout=55) as response:
            data = response.read()
            return response.status, json.loads(data) if data else None
    except HTTPError as error:
        return error.code, json.loads(error.read())


def check(label, condition):
    assert condition, label
    results.append({'label': label, 'status': 'PASS'})
    print('PASS', label, flush=True)


def login(email):
    status, response = call('/auth/login', body={'email': email, 'password': os.environ.get('QUIZ_QA_PASSWORD', 'MathVision123!')})
    assert status == 200
    return response['accessToken']


try:
    token = login('minh.student@mathvision.local')
    token_b = login('an.student@mathvision.local')
    teacher = login('lan.teacher@mathvision.local')
    left, right = 100 + secrets.randbelow(900), 100 + secrets.randbelow(900)
    status, review = call('/student/tutor/work-review', token, {'sourceId': 'quiz-pg-' + str(uuid4()), 'problemText': f'Tính: {left} + {right}', 'workText': f'{left} + {right} = {left + right}', 'problemConfirmed': True, 'workConfirmed': True})
    check('Real confirmed WorkReview accepted by existing Tutor pipeline', status == 200)
    source = {'sourceType': 'WORK_REVIEW', 'sourceId': review['sourceId']}
    status, invitation = call('/student/quizzes/from-learning', token, source)
    check('Real PostgreSQL Quiz created from a server-verified source', status == 200)
    q = invitation['quiz']; quiz_id = q['quizId']; route = '/student/quizzes/' + quiz_id
    status, repeat = call('/student/quizzes/from-learning', token, source)
    check('Repeated source returns same Quiz without repeating invitation', status == 200 and not repeat['offered'] and repeat['quiz']['quizId'] == quiz_id)
    check('Quiz response hides standard answer and prepared explanation', q['correctAnswer'] is None and q['explanationText'] is None)
    check('Unknown source cannot forge a completed learning event', call('/student/quizzes/from-learning', token, dict(source, sourceId='forged'))[0] == 409)
    check('Anonymous Student Quiz API request denied', call('/student/quizzes')[0] == 401)
    check('Teacher Student Quiz API request denied', call('/student/quizzes', teacher)[0] == 403)
    check('Student B cannot read Student A Quiz', call(route, token_b)[0] == 404)
    for action, payload in [('start', {}), ('defer', {}), ('reveal-solution', {}), ('submit', {'requestId': str(uuid4()), 'answer': '48'}), ('narration', {'voice': 'vi-VN-NamMinhNeural'})]:
        check('Student B cannot ' + action + ' Student A Quiz', call(route + '/' + action, token_b, payload)[0] == 404)
    check('Locked narration rejected before opening solution', call(route + '/narration', token, {'voice': 'vi-VN-NamMinhNeural'})[0] == 409)
    status, q = call(route + '/start', token, {})
    assert status == 200
    numbers = list(map(int, re.findall(r'\d+', q['questionText'])))
    answer = str(sum(numbers))
    check('Clock starts with published new question', q['startedAt'] is not None and q['status'] == 'IN_PROGRESS')
    check('Forged client elapsed time and stars are rejected', call(route + '/submit', token, {'requestId': str(uuid4()), 'answer': answer, 'stars': 3, 'elapsedSeconds': 0})[0] == 400)
    _, before = call('/student/quizzes/pending-count', token)
    payload = {'requestId': str(uuid4()), 'answer': answer}
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(lambda _: call(route + '/submit', token, payload), range(2)))
    check('Concurrent HTTP retries both return the same successful persisted attempt', all(s == 200 for s, _ in replies) and all(r['attempt']['number'] == 1 and r['attempt']['correct'] for _, r in replies))
    completed = replies[0][1]['quiz']
    _, after = call('/student/quizzes/pending-count', token)
    check('Pending count decremented exactly once', before['pendingCount'] - after['pendingCount'] == 1)
    check('Quiz star ledger increments exactly once', after['totalStars'] - before['totalStars'] == completed['stars'])
    check('Completed Quiz cannot submit a new rewarding attempt', call(route + '/submit', token, {'requestId': str(uuid4()), 'answer': answer})[0] == 409)
    reauthenticated = login('minh.student@mathvision.local')
    _, restored = call(route, reauthenticated)
    check('Reauthentication restores persisted attempts, status and stars', restored['status'] == 'COMPLETED' and len(restored['attempts']) == 1 and restored['stars'] == completed['stars'])
    # Store only public validation results. Never write tokens, keys or passwords.
    result = {'environment': 'Real Spring + FastAPI + PostgreSQL, isolated mathvision_quiz_qa_20261027 database', 'checks': results}
except Exception as error:
    result = {'checks': results, 'failure': type(error).__name__ + ': ' + str(error)}
    raise
finally:
    (OUT / 'live-api-results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

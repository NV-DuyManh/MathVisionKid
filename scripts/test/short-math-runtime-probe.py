"""Exercise the running local stack; never print or persist authentication secrets."""
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'ai/runtime'), str(ROOT / 'ai/runtime/tests')]
import httpx
from app.config import settings
from test_short_math import CASES

out = ROOT / 'report/device-short-math-20261102'
out.mkdir(parents=True, exist_ok=True)
evidence = {'environment': 'actual local HTTP services; no physical-device measurement', 'cases': []}
with httpx.Client(timeout=10) as client:
    identity = client.get('http://127.0.0.1:8000/internal/v1/tutor/runtime', headers={'X-Internal-API-Key': settings.internal_api_key})
    identity.raise_for_status()
    loaded = identity.json()
    evidence['loadedLessonMatchesDisk'] = loaded['lessonSourceHash'] == hashlib.sha256((ROOT / 'ai/runtime/app/tutoring/lesson.py').read_bytes()).hexdigest()
    assert evidence['loadedLessonMatchesDisk']
    login = client.post('http://127.0.0.1:8080/api/v1/auth/login', json={'email': 'student', 'password': '123'})
    login.raise_for_status()
    auth = {'Authorization': 'Bearer ' + login.json()['accessToken']}
    fresh_owner = 'qa-short-' + uuid4().hex
    for source, answer in CASES:
        body = {'problemText': source, 'workText': '', 'workConfirmed': False, 'problemConfirmed': True, 'guidedUnderstanding': True, 'startWithReading': True}
        began = time.perf_counter()
        direct = client.post('http://127.0.0.1:8000/internal/v1/tutor/lesson', headers={'X-Internal-API-Key': settings.internal_api_key}, json={'owner': fresh_owner, **body})
        direct.raise_for_status()
        fresh_ms = (time.perf_counter() - began) * 1000
        began = time.perf_counter()
        response = client.post('http://127.0.0.1:8080/api/v1/student/tutor/lesson', headers=auth, json=body)
        response.raise_for_status()
        api_ms = (time.perf_counter() - began) * 1000
        task = response.json()
        assert len(task['outline']) == 1 and task['understandingSteps'] == 0 and task['step']['kind'] == 'MATH'
        assert 'correctChoice' not in task['step'] and not task.get('conclusion')
        solved = client.post('http://127.0.0.1:8080/api/v1/student/tutor/lesson/answer', headers=auth,
                             json={'sessionId': task['sessionId'], 'revision': task['revision'], 'answer': answer, 'hint': False})
        solved.raise_for_status()
        result = solved.json()
        assert result['status'] == 'COMPLETE' and result['conclusion']
        evidence['cases'].append({'source': source, 'expected': answer, 'actual': result['completed'][0]['answer'],
                                  'freshOwnerAiMs': round(fresh_ms, 2), 'authenticatedApiMs': round(api_ms, 2), 'status': result['status']})
    for field in ('freshOwnerAiMs', 'authenticatedApiMs'):
        values = [row[field] for row in evidence['cases']]
        evidence[field] = {'median': round(statistics.median(values), 2), 'maximum': max(values)}
(out / 'runtime-results.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key: value for key, value in evidence.items() if key != 'cases'}, ensure_ascii=True))
print(f'PASS {len(evidence["cases"])} exact exercises through the running authenticated API')

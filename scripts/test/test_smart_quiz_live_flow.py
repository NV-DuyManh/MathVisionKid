import urllib.request
import json
import uuid
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://127.0.0.1:8080/api/v1'

def call(path, token=None, body=None, method=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(BASE + path, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode('utf-8')
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8')
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {'raw': content}

def main():
    print("=== STEP 1: AUTHENTICATION ===")
    status, login_res = call('/auth/login', body={'email': 'an.student@mathvision.local', 'password': 'MathVision123!'})
    assert status == 200, f"Login failed: {status} {login_res}"
    token = login_res['accessToken']
    print(f"Authenticated as an.student@mathvision.local. User ID: {login_res.get('user', {}).get('id')}")

    print("\n=== STEP 2: PREPARE DIGIT-APPEND QUIZ ===")
    import random
    test_d = random.choice([1, 2, 3, 4, 5, 6, 7, 8])
    test_x = random.randint(11, 89)
    test_D = 9 * test_x + test_d
    problem_text = f"Đề: Tìm một số biết rằng nếu viết thêm chữ số {test_d} vào bên phải số đó ta được số mới lớn hơn số phải tìm {test_D} đơn vị."
    workflow_key = str(uuid.uuid4())
    status, prep_res = call('/student/quizzes/prepare', token, {
        'workflowKey': workflow_key,
        'revision': 1,
        'confirmedProblemText': problem_text,
        'problemConfirmed': True
    })
    print(f"Prepare status: {status}, Preparation ID: {prep_res.get('preparationId')}, State: {prep_res.get('status')}")
    assert status == 200, f"Prepare failed: {status} {prep_res}"

    prep_id = prep_res['preparationId']
    # Poll until READY
    for _ in range(20):
        time.sleep(0.5)
        status, check_res = call(f'/student/quizzes/preparations/{prep_id}', token)
        if check_res.get('status') in ('READY', 'UNSUPPORTED', 'FAILED'):
            break
    print(f"Preparation resolved to: {check_res.get('status')}, error: {check_res.get('errorCode')}")
    assert check_res.get('status') == 'READY', f"Expected READY, got {check_res}"

    print("\n=== STEP 3: CREATE QUIZ VIA FROM-LEARNING ===")
    # First record source in DB via docker psql to simulate completed lesson
    import subprocess
    container_id = subprocess.check_output('docker ps -q -f name=postgres', shell=True).decode().strip()
    lesson_session_id = str(uuid.uuid4())
    fingerprint_cmd = f"docker exec -i {container_id} psql -U mathvision -d mathvision -c \"" \
                     f"INSERT INTO quiz_learning_sources (id, student_id, source_type, source_id, problem_text, fingerprint, completed, created_at, preparation_id) " \
                     f"SELECT gen_random_uuid(), s.student_id, 'LESSON', '{lesson_session_id}', '{problem_text}', p.fingerprint, true, NOW(), '{prep_id}' " \
                     f"FROM students s, quiz_preparations p WHERE s.student_id = '637a995b-eb49-49af-8d60-55e6a6c50d0c' AND p.id = '{prep_id}';\""
    subprocess.run(fingerprint_cmd, shell=True, check=True)

    status, inv = call('/student/quizzes/from-learning', token, {'sourceType': 'LESSON', 'sourceId': lesson_session_id})
    print(f"from-learning status: {status}, offered: {inv.get('offered')}")
    assert status == 200 and inv.get('offered') is True, f"Failed from-learning: {inv}"
    quiz = inv['quiz']
    quiz_id = quiz['quizId']
    print(f"Created Quiz ID: {quiz_id}")
    print(f"Topic: {quiz['topicCode']} ({quiz['topicName']})")
    print(f"Grade: {quiz['gradeLevel']}, Format: {quiz['answerFormat']}")
    print(f"Question: {quiz['questionText']}")
    assert quiz['topicCode'] == 'DIGIT_APPEND_FIND_ORIGINAL_NUMBER'
    assert quiz['gradeLevel'] == 5
    assert quiz['status'] == 'READY'

    print("\n=== STEP 4: VERIFY DEDUPLICATION (NO DUPLICATE QUIZ) ===")
    # Simulate re-learning the same problem with another lesson session
    lesson_session_2 = str(uuid.uuid4())
    dup_cmd = f"docker exec -i {container_id} psql -U mathvision -d mathvision -c \"" \
              f"INSERT INTO quiz_learning_sources (id, student_id, source_type, source_id, problem_text, fingerprint, completed, created_at, preparation_id) " \
              f"SELECT gen_random_uuid(), s.student_id, 'LESSON', '{lesson_session_2}', '{problem_text}', p.fingerprint, true, NOW(), '{prep_id}' " \
              f"FROM students s, quiz_preparations p WHERE s.student_id = '637a995b-eb49-49af-8d60-55e6a6c50d0c' AND p.id = '{prep_id}';\""
    subprocess.run(dup_cmd, shell=True, check=True)

    status, inv2 = call('/student/quizzes/from-learning', token, {'sourceType': 'LESSON', 'sourceId': lesson_session_2})
    print(f"Second from-learning offered: {inv2.get('offered')}, Quiz ID: {inv2.get('quiz', {}).get('quizId')}")
    assert inv2.get('offered') is False, "Expected offered=False for duplicate source"
    assert inv2.get('quiz', {}).get('quizId') == quiz_id, "Expected same quiz ID returned"

    print("\n=== STEP 5: START QUIZ AND VERIFY PENDING COUNT ===")
    status, counts_before = call('/student/quizzes/pending-count', token)
    print(f"Pending counts before start: {counts_before}")
    assert counts_before['pendingCount'] >= 1

    status, started = call(f'/student/quizzes/{quiz_id}/start', token, method='POST')
    assert status == 200 and started['status'] == 'IN_PROGRESS'
    print(f"Started quiz. Status: {started['status']}")

    print("\n=== STEP 6: WRONG ATTEMPTS AND REVEAL SOLUTION ===")
    status, graded1 = call(f'/student/quizzes/{quiz_id}/submit', token, {'requestId': str(uuid.uuid4()), 'answer': '9999'})
    assert status == 200 and graded1['quiz']['wrongAttempts'] == 1
    time.sleep(1)
    status, graded2 = call(f'/student/quizzes/{quiz_id}/submit', token, {'requestId': str(uuid.uuid4()), 'answer': '8888'})
    assert status == 200 and graded2['quiz']['wrongAttempts'] == 2 and graded2['quiz']['canRevealSolution'] is True

    status, revealed = call(f'/student/quizzes/{quiz_id}/reveal-solution', token, method='POST')
    assert status == 200 and revealed['solutionViewed'] is True
    assert revealed['explanationText'] is not None
    print(f"Solution revealed: {revealed['explanationText'][:80]}...")
    correct_answer = revealed['correctAnswer']
    print(f"Correct answer is: {correct_answer}")

    # Complete with solution -> 0 stars
    time.sleep(1)
    status, completed = call(f'/student/quizzes/{quiz_id}/submit', token, {'requestId': str(uuid.uuid4()), 'answer': correct_answer})
    assert status == 200 and completed['quiz']['status'] == 'COMPLETED'
    assert completed['quiz']['stars'] == 0
    assert completed['quiz']['completedWithSolution'] is True
    print(f"Completed with solution. Stars: {completed['quiz']['stars']}, completedWithSolution: {completed['quiz']['completedWithSolution']}")

    status, counts_mid = call('/student/quizzes/pending-count', token)
    print(f"Pending count after completion: {counts_mid['pendingCount']}, totalStars: {counts_mid['totalStars']}")

    print("\n=== STEP 7: REPLAY TO IMPROVE STARS ===")
    status, replaying = call(f'/student/quizzes/{quiz_id}/replay', token, method='POST')
    assert status == 200 and replaying['status'] == 'IN_PROGRESS'
    assert replaying['explanationText'] is None, "Solution MUST be hidden during replay!"
    print(f"Replay started. Status: {replaying['status']}, solution hidden: {replaying['explanationText'] is None}")

    # Verify pending count did NOT inflate due to replay!
    status, counts_during_replay = call('/student/quizzes/pending-count', token)
    print(f"Pending count during replay: {counts_during_replay['pendingCount']}")
    assert counts_during_replay['pendingCount'] == counts_mid['pendingCount'], "Pending badge count MUST NOT increase when replaying a completed quiz!"

    # Submit correct answer on replay within 30s -> gets 3 stars!
    time.sleep(1)
    status, replayed_finish = call(f'/student/quizzes/{quiz_id}/submit', token, {'requestId': str(uuid.uuid4()), 'answer': correct_answer})
    assert status == 200 and replayed_finish['quiz']['status'] == 'COMPLETED'
    print(f"Replay finish stars: {replayed_finish['quiz']['stars']}")
    assert replayed_finish['quiz']['stars'] == 3, f"Expected 3 stars for fast independent solve, got {replayed_finish['quiz']['stars']}"
    assert replayed_finish['quiz']['completedWithSolution'] is False

    status, counts_after = call('/student/quizzes/pending-count', token)
    print(f"Final pending count: {counts_after['pendingCount']}, totalStars: {counts_after['totalStars']}")
    assert counts_after['totalStars'] >= 3, "Total stars should reflect bestStars!"

    # Verify attempts history has all 4 attempts
    attempts = replayed_finish['quiz']['attempts']
    print(f"Total attempts recorded: {len(attempts)}")
    assert len(attempts) == 4, f"Expected 4 attempts, got {len(attempts)}"
    for att in attempts:
        print(f"  Attempt {att['number']}: answer={att['answer']}, correct={att['correct']}, stars={att['stars']}")

    print("\n>>> ALL SMART QUIZ CRITICAL FIX CRITERIA VERIFIED ON LIVE BACKEND! <<<")

if __name__ == '__main__':
    main()

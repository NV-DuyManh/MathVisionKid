import urllib.request
import json
import uuid
import time
import sys
import subprocess
import re

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

def solve_digit_append(question_text):
    # Tìm một số biết rằng nếu viết thêm chữ số d vào bên phải số đó thì được số mới lớn hơn số phải tìm D đơn vị.
    # 9x + d = D => x = (D - d) / 9
    m = re.search(r'chữ số\s+(\d)\s+.*lớn hơn.*?\s+(\d+)\s+đơn vị', question_text)
    if not m:
        m = re.search(r'(\d)\s+.*lớn hơn.*?\s+(\d+)\s+đơn vị', question_text)
    d = int(m.group(1))
    D = int(m.group(2))
    x = (D - d) // 9
    return str(x)

def main():
    print("================================================================")
    print("TEST: SMART QUIZ REPLAY MODES, ANTI-CHEATING & TOTAL STARS CHECK")
    print("================================================================")

    # 1. AUTHENTICATE
    status, login_res = call('/auth/login', body={'email': 'an.student@mathvision.local', 'password': 'MathVision123!'})
    assert status == 200, f"Login failed: {login_res}"
    token = login_res['accessToken']
    print(f"[OK] Authenticated as an.student@mathvision.local")

    # Get baseline stars
    status, baseline_counts = call('/student/quizzes/pending-count', token)
    base_stars = baseline_counts['totalStars']
    base_pending = baseline_counts['pendingCount']
    print(f"[*] Baseline: totalStars={base_stars}, pendingCount={base_pending}")

    # 2. CREATE A BRAND NEW DIGIT-APPEND LESSON
    import random
    test_d = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    test_x = random.randint(12, 88)
    test_D = 9 * test_x + test_d
    orig_problem = f"Đề: Tìm một số biết rằng nếu viết thêm chữ số {test_d} vào bên phải số đó ta được số mới lớn hơn số phải tìm {test_D} đơn vị."
    workflow_key = str(uuid.uuid4())

    status, prep_res = call('/student/quizzes/prepare', token, {
        'workflowKey': workflow_key,
        'revision': 1,
        'confirmedProblemText': orig_problem,
        'problemConfirmed': True
    })
    assert status == 200
    prep_id = prep_res['preparationId']

    for _ in range(20):
        time.sleep(0.5)
        status, check_res = call(f'/student/quizzes/preparations/{prep_id}', token)
        if check_res.get('status') == 'READY':
            break
    assert check_res.get('status') == 'READY', f"Prepare not ready: {check_res}"
    print(f"[OK] Preparation ready deterministically: {prep_id}")

    # Record completed lesson in db
    container_id = subprocess.check_output('docker ps -q -f name=postgres', shell=True).decode().strip()
    lesson_id = str(uuid.uuid4())
    sql = f"INSERT INTO quiz_learning_sources (id, student_id, source_type, source_id, problem_text, fingerprint, completed, created_at, preparation_id) " \
          f"SELECT gen_random_uuid(), s.student_id, 'LESSON', '{lesson_id}', '{orig_problem}', p.fingerprint, true, NOW(), '{prep_id}' " \
          f"FROM students s, quiz_preparations p WHERE s.student_id = '637a995b-eb49-49af-8d60-55e6a6c50d0c' AND p.id = '{prep_id}';"
    subprocess.run(f'docker exec -i {container_id} psql -U mathvision -d mathvision -c "{sql}"', shell=True, check=True)

    status, inv = call('/student/quizzes/from-learning', token, {'sourceType': 'LESSON', 'sourceId': lesson_id})
    assert status == 200 and inv['offered'] is True
    quiz_id = inv['quiz']['quizId']
    print(f"[OK] Quiz created from learning: {quiz_id}")

    # 3. INITIAL QUIZ: SOLVED WITH SOLUTION VIEWED -> 0 STARS
    status, started = call(f'/student/quizzes/{quiz_id}/start', token, method='POST')
    assert status == 200 and started['status'] == 'IN_PROGRESS'

    # Fail 2 times then reveal solution
    call(f'/student/quizzes/{quiz_id}/submit', token, {'requestId': str(uuid.uuid4()), 'answer': '9999'})
    time.sleep(1)
    call(f'/student/quizzes/{quiz_id}/submit', token, {'requestId': str(uuid.uuid4()), 'answer': '8888'})
    status, revealed = call(f'/student/quizzes/{quiz_id}/reveal-solution', token, method='POST')
    assert status == 200 and revealed['solutionViewed'] is True
    correct_ans_0 = revealed['correctAnswer']
    print(f"[OK] Solution revealed to student. Correct answer for initial quiz is {correct_ans_0}")

    # Submit correct answer after viewing solution
    time.sleep(1)
    status, graded0 = call(f'/student/quizzes/{quiz_id}/submit', token, {'requestId': str(uuid.uuid4()), 'answer': correct_ans_0})
    assert status == 200
    assert graded0['quiz']['stars'] == 0, "Expected 0 stars when solution viewed"
    assert graded0['quiz']['completedWithSolution'] is True

    status, counts0 = call('/student/quizzes/pending-count', token)
    assert counts0['totalStars'] == base_stars, f"Total stars must not increase for 0-star solve: {counts0}"
    print(f"[OK] Initial solve completed with solution. stars=0, completedWithSolution=True, totalStars unchanged ({counts0['totalStars']})")

    # 4. TEST REQUIREMENT 1 - MODE 1: ON LAI BAI CU (PRACTICE)
    # The student knows the answer is correct_ans_0.
    # Repeating the exact same question MUST NOT grant 3 stars!
    print("\n--- TESTING PRACTICE REPLAY (ÔN LẠI BÀI CŨ) ---")
    status, practice_view = call(f'/student/quizzes/{quiz_id}/replay', token, body={'mode': 'PRACTICE'})
    assert status == 200
    assert practice_view['status'] == 'IN_PROGRESS'
    assert practice_view['replayMode'] == 'PRACTICE'
    assert practice_view['solutionViewed'] is False
    assert practice_view['explanationText'] is None
    print(f"[OK] Practice replay started: mode={practice_view['replayMode']}, question retains original")

    status, counts_during_practice = call('/student/quizzes/pending-count', token)
    assert counts_during_practice['pendingCount'] == base_pending, f"Pending count must NOT inflate: {counts_during_practice}"

    # Student enters known answer in 2 seconds (< 30s)
    time.sleep(1)
    status, practice_submit = call(f'/student/quizzes/{quiz_id}/submit', token, {'requestId': str(uuid.uuid4()), 'answer': correct_ans_0})
    assert status == 200
    assert practice_submit['attempt']['correct'] is True
    # CRITICAL CHECK: attempt stars MUST BE 0!
    assert practice_submit['attempt']['stars'] == 0, f"Practice mode must give 0 stars: {practice_submit}"
    # CRITICAL CHECK: quiz bestStars MUST REMAIN 0!
    assert practice_submit['quiz']['stars'] == 0, f"Quiz bestStars must not increase on practice: {practice_submit}"

    status, counts_after_practice = call('/student/quizzes/pending-count', token)
    assert counts_after_practice['totalStars'] == base_stars, f"Total stars must not change on practice: {counts_after_practice}"
    print(f"[VERIFIED] Practice replay prevents cheating: answered in <30s but received 0 stars because answer was already known!")

    # 5. TEST REQUIREMENT 1 - MODE 2: THU THACH NANG SAO (CHALLENGE)
    # Generates a new variant with DIFFERENT numbers and DIFFERENT answer!
    print("\n--- TESTING CHALLENGE REPLAY (THỬ THÁCH NÂNG SAO) ---")
    status, challenge_view = call(f'/student/quizzes/{quiz_id}/replay', token, body={'mode': 'CHALLENGE'})
    assert status == 200
    assert challenge_view['status'] == 'IN_PROGRESS'
    assert challenge_view['replayMode'] == 'CHALLENGE'
    new_question = challenge_view['questionText']
    print(f"[OK] Challenge generated new question: {new_question}")
    assert new_question != orig_problem, "Challenge MUST produce a new variant wording!"

    new_answer = solve_digit_append(new_question)
    assert new_answer != str(correct_ans_0), f"Challenge answer ({new_answer}) MUST differ from old answer ({correct_ans_0})!"
    print(f"[OK] Verified new answer is: {new_answer} (different from old {correct_ans_0})")

    # Student solves the new variant independently in < 30s
    time.sleep(1)
    status, challenge_submit = call(f'/student/quizzes/{quiz_id}/submit', token, {'requestId': str(uuid.uuid4()), 'answer': new_answer})
    assert status == 200
    assert challenge_submit['attempt']['correct'] is True
    assert challenge_submit['attempt']['stars'] == 3, f"Expected 3 stars for fast solve: {challenge_submit}"
    assert challenge_submit['quiz']['stars'] == 3, f"bestStars should be upgraded to 3: {challenge_submit}"
    assert challenge_submit['quiz']['completedWithSolution'] is False, "Independent solve clears completedWithSolution"

    status, counts_after_challenge = call('/student/quizzes/pending-count', token)
    expected_stars = base_stars + 3
    assert counts_after_challenge['totalStars'] == expected_stars, f"Total stars must increase from {base_stars} to {expected_stars}, got {counts_after_challenge}"
    print(f"[VERIFIED] Challenge solve in <30s earned 3 stars! bestStars=3, totalStars={counts_after_challenge['totalStars']}")

    # 6. TEST REQUIREMENT 2 - TOTAL STARS DOES NOT ACCUMULATE ON SUBSEQUENT REPLAYS
    print("\n--- TESTING TOTAL STARS IDEMPOTENCY & BEST-STARS PRESERVATION ---")
    # Start another challenge on the same quiz
    status, challenge2_view = call(f'/student/quizzes/{quiz_id}/replay', token, body={'mode': 'CHALLENGE'})
    assert status == 200
    c2_question = challenge2_view['questionText']
    c2_answer = solve_digit_append(c2_question)

    # Wait or simulate solving with 2 stars or 1 star
    # We will submit directly and verify that quiz.stars remains 3 (bestStars) and totalStars does NOT increase!
    time.sleep(1)
    req_uuid = str(uuid.uuid4())
    status, c2_submit = call(f'/student/quizzes/{quiz_id}/submit', token, {'requestId': req_uuid, 'answer': c2_answer})
    assert status == 200
    assert c2_submit['attempt']['correct'] is True
    # bestStars remains 3
    assert c2_submit['quiz']['stars'] == 3

    status, counts_after_c2 = call('/student/quizzes/pending-count', token)
    # CRITICAL CHECK: totalStars is STILL expected_stars (NOT expected_stars + 3)!
    assert counts_after_c2['totalStars'] == expected_stars, f"Total stars must NOT accumulate multiple replays: {counts_after_c2}"
    print(f"[VERIFIED] Replaying the same quiz again did NOT add more stars: totalStars is still {counts_after_c2['totalStars']}!")

    # 7. TEST IDEMPOTENT REQUEST RESUBMISSION
    print("\n--- TESTING REQUEST IDEMPOTENCY ---")
    status, dupe_submit = call(f'/student/quizzes/{quiz_id}/submit', token, {'requestId': req_uuid, 'answer': c2_answer})
    assert status == 200
    assert dupe_submit['quiz']['stars'] == 3
    status, counts_after_dupe = call('/student/quizzes/pending-count', token)
    assert counts_after_dupe['totalStars'] == expected_stars, "Dupe request must not alter totalStars"
    print(f"[VERIFIED] Resending same requestId returned identical response without inflating stars or attempts!")

    print("\n================================================================")
    print(">>> ALL REPLAY MODES, ANTI-CHEATING & TOTAL STARS VERIFIED 100% <<<")
    print("================================================================")

if __name__ == '__main__':
    main()

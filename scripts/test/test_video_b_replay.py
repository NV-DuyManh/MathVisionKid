import urllib.request
import json
import uuid
import subprocess

def call(path, token=None, body=None, method=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:8080/api/v1' + path, headers=headers, data=data, method=method)
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def main():
    s, r = call('/auth/login', body={'email': 'an.student@mathvision.local', 'password': 'MathVision123!'})
    token = r['accessToken']

    # Get existing quiz from Video B
    s, q = call('/student/quizzes/1c5ef450-122e-4566-a029-e3cc6a6fd0d5', token)
    print('VIDEO B QUIZ:', q['quizId'], 'status:', q['status'], 'stars:', q['stars'], 'completedWithSolution:', q['completedWithSolution'])

    # Replay this quiz
    s, replayed = call('/student/quizzes/1c5ef450-122e-4566-a029-e3cc6a6fd0d5/replay', token, method='POST')
    print('REPLAY STARTED:', replayed['status'], 'solutionViewed:', replayed['solutionViewed'], 'explanationText:', replayed['explanationText'])

    # Check pending count - should NOT inflate
    s, counts = call('/student/quizzes/pending-count', token)
    print('PENDING COUNT DURING REPLAY:', counts['pendingCount'], 'totalStars:', counts['totalStars'])

    # Query answerSpec from DB
    cid = subprocess.check_output('docker ps -q -f name=postgres', shell=True).decode().strip()
    ans = subprocess.check_output(f'docker exec -i {cid} psql -U mathvision -d mathvision -t -A -c "SELECT answer_spec FROM student_quizzes WHERE id=\'1c5ef450-122e-4566-a029-e3cc6a6fd0d5\';"', shell=True).decode().strip()
    print('ANSWER SPEC IS:', ans)

    # Submit answer
    s, finish = call('/student/quizzes/1c5ef450-122e-4566-a029-e3cc6a6fd0d5/submit', token, {'requestId': str(uuid.uuid4()), 'answer': ans})
    print('REPLAY SUBMIT RESULT: status:', finish['quiz']['status'], 'stars:', finish['quiz']['stars'], 'completedWithSolution:', finish['quiz']['completedWithSolution'])

    s, final_counts = call('/student/quizzes/pending-count', token)
    print('FINAL COUNTS: pending:', final_counts['pendingCount'], 'totalStars:', final_counts['totalStars'])

if __name__ == '__main__':
    main()


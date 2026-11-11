"""Opt-in acceptance check against real local tutoring and speech services."""
import ast
import hashlib
import io
import json
import math
import operator
import os
import re
import time
import wave
from array import array
from fractions import Fraction
from pathlib import Path
from urllib.parse import urlparse

import httpx


def calculate(expression):
    """Independent arithmetic oracle for the photographed exercise."""
    operations = {ast.Add: operator.add, ast.Sub: operator.sub,
                  ast.Mult: operator.mul, ast.Div: operator.truediv}

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return Fraction(str(node.value))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -visit(node.operand)
        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            return operations[type(node.op)](visit(node.left), visit(node.right))
        raise AssertionError('Unsupported arithmetic in the live exercise')

    assert len(expression) <= 160
    source = expression.replace('−', '-').replace('×', '*').replace('÷', '/').replace(':', '/')
    return str(visit(ast.parse(source.strip(), mode='eval').body))


def normalized_reading(text):
    text = re.sub(r'^Bài\s*\d+\s*[.:)]?\s*', '', text.strip(), flags=re.IGNORECASE)
    return re.sub(r'\s+', '', text).casefold()


def main():
    assert os.environ.get('MATHVISION_LIVE_DISPOSABLE') == 'true'
    api = os.environ['MATHVISION_LIVE_API'].rstrip('/')
    assert urlparse(api).hostname in ('127.0.0.1', 'localhost')
    image = Path(os.environ['MATHVISION_LIVE_IMAGE'])
    truth = json.loads(Path(os.environ['MATHVISION_LIVE_TRUTH']).read_text(encoding='utf-8-sig'))
    output = Path(os.environ['MATHVISION_LIVE_OUTPUT'])
    output.mkdir(parents=True, exist_ok=True)
    result = {'mockedResponses': False, 'voices': [], 'turns': [], 'passed': False}
    client = httpx.Client(base_url=api, timeout=65)

    def post(path, body=None, **kwargs):
        response = client.post(path, json=body, **kwargs)
        response.raise_for_status()
        return response.json()

    try:
        login = post('/auth/login', {
            'email': os.environ['MATHVISION_LIVE_STUDENT_EMAIL'],
            'password': os.environ['MATHVISION_LIVE_STUDENT_PASSWORD'],
        })
        client.headers['Authorization'] = 'Bearer ' + login['accessToken']
        with image.open('rb') as source:
            read = client.post('/student/tutor/inspect', files={'file': ('worksheet.jpg', source, 'image/jpeg')}, data={'privacyConfirmed': 'true'})
        read.raise_for_status()
        reading = read.json()
        assert normalized_reading(reading['problemText']) == normalized_reading(truth['problemText']), 'Photo transcription differs from the independently reviewed source'
        result['reading'] = reading
        draft = {'problemText': reading['problemText'], 'workText': ''}
        post('/student/tutor/lesson/prepare', draft)
        unconfirmed = client.post('/student/tutor/lesson', json={**draft, 'problemConfirmed': False, 'workConfirmed': False})
        assert unconfirmed.status_code == 400, 'Source confirmation must be enforced by the backend'
        state = post('/student/tutor/lesson', {**draft, 'problemConfirmed': True, 'workConfirmed': False, 'guidedUnderstanding': False})
        result['firstStep'] = state['step']
        source = {'sessionId': state['sessionId'], 'revision': state['revision'], 'paragraphs': [state['step']['explanation']]}

        for name, voice, fallback in [('male', 'vi-VN-NamMinhNeural', False), ('female', 'vi-VN-HoaiMyNeural', False), ('fallback', 'vi-VN-NamMinhNeural', True)]:
            started = time.monotonic()
            deadline = started + 60
            payload = {**source, 'voice': voice, 'useFallback': fallback}
            prepared = False
            progress = None
            while time.monotonic() < deadline:
                path = '/student/tutor/lesson/narration/status' if prepared else '/student/tutor/lesson/narration/prepare'
                response = client.post(path, json=payload, timeout=min(5, max(.1, deadline - time.monotonic())))
                if response.status_code == 429:
                    time.sleep(.5)
                    continue
                response.raise_for_status()
                progress = response.json()
                prepared = True
                if progress['phase'] == 'ready':
                    break
                assert progress['phase'] != 'failed', f'{name} voice preparation failed'
                if progress['phase'] == 'waiting':
                    prepared = False
                time.sleep(.5)
            assert progress and progress['phase'] == 'ready', f'{name} voice exceeded the application preparation deadline'
            audio = client.post('/student/tutor/lesson/narration', json=payload, timeout=max(.1, deadline - time.monotonic()))
            audio.raise_for_status()
            assert audio.headers['content-type'].startswith('audio/wav')
            with wave.open(io.BytesIO(audio.content), 'rb') as sound:
                assert (sound.getnchannels(), sound.getsampwidth(), sound.getframerate()) == (1, 2, 16000)
                duration = sound.getnframes() / sound.getframerate()
                samples = array('h', sound.readframes(sound.getnframes()))
            rms = math.sqrt(sum(value * value for value in samples) / len(samples))
            assert duration > .5 and rms > 50, f'{name} audio is empty or silent'
            (output / (name + '.wav')).write_bytes(audio.content)
            record = {'name': name, 'voice': voice, 'fallback': fallback, 'duration': duration, 'rms': rms, 'seconds': round(time.monotonic() - started, 2), 'sha256': hashlib.sha256(audio.content).hexdigest()}
            result['voices'].append(record)
            print(json.dumps(record), flush=True)
        assert len({item['sha256'] for item in result['voices']}) == 3, 'The selected voices must have separate audio assets'

        wrong = post('/student/tutor/lesson/answer', {'sessionId': state['sessionId'], 'revision': state['revision'], 'answer': '999999', 'hint': False})
        assert wrong['status'] == 'TRY_AGAIN' and wrong['revision'] == state['revision']
        for _ in range(8):
            if state['status'] == 'COMPLETE':
                break
            answer = calculate(state['step']['expression'])
            result['turns'].append({'question': state['step']['question'], 'expression': state['step']['expression'], 'answer': answer})
            state = post('/student/tutor/lesson/answer', {'sessionId': state['sessionId'], 'revision': state['revision'], 'answer': answer, 'hint': False})
            assert state['status'] in ('CORRECT', 'COMPLETE'), 'An independently calculated answer was rejected'
        assert state['status'] == 'COMPLETE'
        assert re.search(r'(?<!\d)' + re.escape(str(truth['answer'])) + r'(?!\d)', state['conclusion']), 'Conclusion differs from the independently reviewed answer'
        result['conclusion'] = state['conclusion']
        result['passed'] = True
        print('Live Student photo, lesson and three-voice check passed', flush=True)
    except Exception as error:
        result['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        client.close()
        (output / 'student-live-results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

"""Read-only audit; writes evidence only. Never starts services or changes settings.

Run with ai/runtime/.venv/Scripts/python.exe. --live exercises real configured
providers in this separate process, using public exercise text (no pupil data).
Those timings exclude HTTP, phone/LAN and playback; no latency SLA is inferred.
"""
import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import io
import json
import math
from pathlib import Path
import socket
import statistics
import sys
import time
from types import SimpleNamespace
import urllib.request
import uuid
import wave

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'ai/runtime'))

FLOOR = ('Một nền nhà hình chữ nhật có chiều dài 8m, chiều rộng bằng 1/2 chiều dài. '
         'Người ta lát nền nhà đó bằng các viên gạch hình vuông cạnh 4dm. '
         'a) Hỏi cần mua bao nhiêu viên gạch để lát kín nền nhà đó? '
         'b) Biết rằng 2m² loại gạch đó giá 250 000 đồng, hỏi cần bao nhiêu tiền để lát nền nhà? '
         '(Diện tích phần mạch vữa không đáng kể).')
SHORT = ['Em đọc đề và tìm những điều đã biết trước nhé. Sau đó em chọn câu hỏi '
         'cho biết bài toán cần tìm gì. Chưa cần thực hiện phép tính ở bước này.']
LONG = SHORT + [
    'Khi tính diện tích hình chữ nhật, em cần xác định chiều dài và chiều rộng. '
    'Nếu hai kích thước chưa cùng đơn vị, em đổi về cùng một đơn vị trước khi nhân.',
    'Để biết cần bao nhiêu viên gạch, em so sánh diện tích nền nhà và diện tích một viên gạch. '
    'Hai diện tích phải cùng đơn vị. Em kiểm tra điều này trước khi chọn phép tính.',
    'Phần tính tiền cần dựa trên diện tích và mức giá mà đề đã cho. Em đọc kỹ mức giá '
    'ứng với bao nhiêu mét vuông, rồi mới xác định cách tính số tiền.',
]


def stats(values):
    ordered = sorted(values)
    return dict(n=len(values), medianMs=round(statistics.median(values), 3),
                p95Ms=round(ordered[math.ceil(.95*len(ordered))-1], 3),
                maxMs=round(max(values), 3)) if values else dict(n=0)


def health():
    urls = { 'ai': 'http://127.0.0.1:8000/health',
             'business': 'http://127.0.0.1:8080/actuator/health',
             'student': 'http://127.0.0.1:8081/status',
             'portal': 'http://127.0.0.1:5172/',
             'teacher': 'http://127.0.0.1:5173/',
             'admin': 'http://127.0.0.1:5174/' }
    def probe(item):
        name, url = item
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return name, dict(status=response.status,
                                  ms=round((time.perf_counter()-started)*1000, 2))
        except Exception as exc:
            return name, dict(status='unreachable', category=type(exc).__name__)
    with ThreadPoolExecutor(max_workers=6) as pool:
        result = dict(pool.map(probe, urls.items()))
    for name, port in [('postgres',5432), ('redis',6379), ('minio',9000)]:
        try:
            with socket.create_connection(('127.0.0.1',port), timeout=1):
                result[name] = dict(tcpReachable=True)
        except OSError:
            result[name] = dict(tcpReachable=False)
    return result


def infrastructure():
    import subprocess
    from app.config import settings
    result={}
    samples=[]
    try:
        import redis
        client=redis.Redis.from_url(settings.redis_url,socket_connect_timeout=2,socket_timeout=2)
        for _ in range(30):
            tick=time.perf_counter()
            assert client.ping()
            samples.append((time.perf_counter()-tick)*1000)
        result['redis']=dict(status='passed',operation='read-only PING over TCP',timing=stats(samples))
        client.close()
    except Exception as exc:
        result['redis']=dict(status='unavailable',category=type(exc).__name__)
    try:
        response=subprocess.run(['docker','exec','mathvision-postgres','sh','-c',
            'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atqc "SELECT 1;"'],
            capture_output=True,timeout=8,check=True)
        assert response.stdout.strip()==b'1'
        result['postgres']=dict(status='passed',operation='read-only SELECT 1 inside container; not application query latency')
    except Exception as exc:
        result['postgres']=dict(status='unavailable',category=type(exc).__name__)
    samples=[]
    try:
        for _ in range(30):
            tick=time.perf_counter()
            with urllib.request.urlopen('http://127.0.0.1:9000/minio/health/ready',timeout=2) as response:
                assert response.status==200
            samples.append((time.perf_counter()-tick)*1000)
        result['minio']=dict(status='passed',operation='read-only readiness HTTP; not file upload/download',timing=stats(samples))
    except Exception as exc:
        result['minio']=dict(status='unavailable',category=type(exc).__name__)
    return result


def local_calculation():
    from app.tutoring.lesson import calculate_exact, numeric_values, unit_conversions
    expressions = [('1/3+2/5','11/15'), ('16/(1-1/3-2/5)','60'),
                   ('8*(1/2)*8*100/(4*4)','200'), ('32/2*250000','4000000')]
    samples = []
    for _ in range(200):
        tick = time.perf_counter()
        for expression, expected in expressions:
            assert str(calculate_exact(expression)) == expected
        assert '250000' in numeric_values(FLOOR)
        assert any(row['factor']=='100' for row in unit_conversions(FLOOR))
        samples.append((time.perf_counter()-tick)*1000)
    return dict(scope='in-process; four exact calculations + source number/unit checks per iteration',
                timing=stats(samples))


def local_digit_model():
    from app.recognition.model_engine import ModelRecognitionEngine
    from app.parsing.parser import StructuredParser
    from app.validation.addition import VerticalAdditionValidator
    row=dict(scope='local YOLO digit model, repeated synthetic 45+27 fixture; not handwriting accuracy')
    try:
        tick=time.perf_counter()
        engine=ModelRecognitionEngine()
        row['modelLoadMs']=round((time.perf_counter()-tick)*1000,2)
        if not engine.is_ready:
            return row | dict(status='unavailable')
        import torch
        row['device']=str(next(engine._yolo_model.model.parameters()).device)
        raw=(ROOT/'ai/runtime/tests/fixtures/synthetic_addition.jpg').read_bytes()
        latencies=[]
        for index in range(11):
            tick=time.perf_counter()
            recognized=engine.recognize(raw)
            parsed=StructuredParser().parse(recognized)
            assert parsed.status=='VALID_STRUCTURE'
            assert parsed.operands==['45','27'] and parsed.result=='72'
            assert VerticalAdditionValidator().validate(parsed)['is_valid']
            elapsed=(time.perf_counter()-tick)*1000
            if index==0: row['firstInferenceAndValidationMs']=round(elapsed,2)
            else: latencies.append(elapsed)
        row.update(status='passed',warmTiming=stats(latencies),
                   torchThreads=torch.get_num_threads(),cudaAvailable=torch.cuda.is_available())
    except Exception as exc:
        row.update(status='failed',category=type(exc).__name__)
    return row


async def live_lesson():
    from app.config import settings
    from app.tutoring import lesson, plan_preparation
    if not (settings.groq_enabled and settings.groq_api_keys.strip()):
        return [dict(status='skipped', reason='Configured planning provider not enabled')]
    results = []
    cases = [('floor', FLOOR, {'200','4000000'}),
             ('variant', FLOOR.replace('8m','6m').replace('4dm','3dm').replace('250 000','180 000'),
              {'200','1620000'})]
    import re
    for name, source, expected in cases:
        row = dict(case=name, scope='isolated process, real model; excludes HTTP/phone',
                   backgroundRequested=True, providerMocked=False)
        owner = 'performance-audit-' + uuid.uuid4().hex
        draft = plan_preparation.SourceDraft(owner=owner, problemText=source, workText='')
        request = lesson.LessonRequest(owner=owner, problemText=source, workText='',
                                      problemConfirmed=True, guidedUnderstanding=True, startWithReading=True)
        started = time.perf_counter()
        try:
            tick = time.perf_counter()
            state = await plan_preparation.prepare(draft)
            row['prepareCallMs'] = round((time.perf_counter()-tick)*1000, 2)
            assert set(state)=={'phase'}
            tick = time.perf_counter()
            opened = await lesson.start_lesson(request)
            row['readingOpenMs'] = round((time.perf_counter()-tick)*1000, 2)
            row['readingBeforeMath'] = opened.preparingMath
            while time.perf_counter()-started < 43:
                state = await plan_preparation.prepare(draft)
                if state['phase'] != 'preparing': break
                await asyncio.sleep(.5)
            row['preparationElapsedSeconds'] = round(time.perf_counter()-started, 3)
            row['preparationPhase'] = state['phase']
            if state['phase']!='ready':
                row['status']='failed'
            else:
                tick = time.perf_counter()
                body = await lesson.start_lesson(request)
                row['warmOpenMs'] = round((time.perf_counter()-tick)*1000, 2)
                questions = re.findall(r'(?<!\w)(?:Hỏi|Tính|Tìm|Đếm)\b[^?]*\?', source, re.I)
                latencies = []
                while body.step is not None:
                    step = body.step
                    if step.kind=='UNDERSTAND':
                        if 'Ý a' in step.question: answer=questions[0]
                        elif 'Ý b' in step.question: answer=questions[1]
                        else: answer=next(choice for choice in step.choices if choice not in questions)
                    else: answer=str(lesson.calculate_exact(step.expression))
                    tick = time.perf_counter()
                    turn = lesson.TurnRequest(owner=owner,sessionId=body.sessionId,
                                              revision=body.revision,answer=answer)
                    await lesson.ready_for_answer(turn)
                    body = lesson.answer_lesson(turn)
                    latencies.append((time.perf_counter()-tick)*1000)
                    assert body.status!='TRY_AGAIN'
                assert expected <= {item.answer for item in body.completed}
                assert body.status=='COMPLETE'
                row.update(status='passed', correctRequestedResults=True, answerTiming=stats(latencies))
        except Exception as exc:
            row.update(status='failed', category=type(exc).__name__,
                       reason=getattr(exc,'reason',None), elapsedSeconds=round(time.perf_counter()-started,3))
        results.append(row)
    return results


def live_speech(output):
    from app.config import settings
    from app.tutoring import lesson, narration
    from app.tutoring.speech_render import SPEECH_VOICES
    results=[]
    for label, paragraphs in [('short',SHORT),('long',LONG)]:
        for voice in SPEECH_VOICES:
            session_id=uuid.uuid4().hex
            owner='performance-audit-'+session_id
            # Already-issued text fixture only; no pretend model review or pupil session.
            lesson._sessions[session_id]=SimpleNamespace(owner=owner,revision=0,
                expires=time.monotonic()+300,narration_texts=paragraphs)
            request=narration.NarrationRequest(owner=owner,sessionId=session_id,
                                              revision=0,paragraphs=paragraphs,voice=voice)
            row=dict(case=label,voice=voice,characters=sum(map(len,paragraphs)),
                     scope='production narration function; issued-text fixture; real speech provider',
                     provider=settings.speech_provider, providerMocked=False, physicalPlaybackVerified=False)
            started=time.perf_counter()
            try:
                data=narration.narrate(request)
                row['coldMs']=round((time.perf_counter()-started)*1000, 2)
                narration.validate_audio(data)
                with wave.open(io.BytesIO(data),'rb') as sound:
                    row['audioSeconds']=round(sound.getnframes()/sound.getframerate(),2)
                (output/f'{label}-{voice}.wav').write_bytes(data)
                samples=[]
                for _ in range(30):
                    tick=time.perf_counter()
                    assert narration.narrate(request)==data
                    samples.append((time.perf_counter()-tick)*1000)
                row.update(status='passed',nonSilentCompleteWav=True,warmTiming=stats(samples))
            except Exception as exc:
                row.update(status='failed',category=type(exc).__name__,
                           elapsedMs=round((time.perf_counter()-started)*1000,2))
            finally:
                lesson._sessions.pop(session_id,None)
            results.append(row)
    return results


async def live_dialogue(output):
    import httpx
    from unittest.mock import patch
    from app.tutoring import conversation, lesson
    row=dict(scope='isolated process; real ASR and text reply; reading-only session fixture',
             humanRecording=False,physicalPlaybackVerified=False,providerResponses=[])
    async def observe(operation, function):
        original=httpx.AsyncClient.post
        async def post(client,*args,**kwargs):
            response=await original(client,*args,**kwargs)
            event=dict(operation=operation,status=response.status_code)
            if response.status_code!=200:
                try:
                    error=response.json().get('error',{})
                    event.update({name:str(error[name])[:80] for name in ('type','code') if name in error})
                except (ValueError,TypeError,AttributeError): pass
            row['providerResponses'].append(event)
            return response
        with patch.object(httpx.AsyncClient,'post',post):
            return await function()
    sample=output/'short-vi-VN-NamMinhNeural.wav'
    if not sample.exists():
        return row | dict(status='skipped',reason='Run the speech probe first')
    try:
        tick=time.perf_counter()
        transcript=await observe('transcription',lambda: conversation.transcribe_question(sample.read_bytes()))
        row['asrMs']=round((time.perf_counter()-tick)*1000,2)
        row['transcript']=transcript.text
        normalize=lambda text: ' '.join(''.join(c if c.isalnum() else ' ' for c in text.casefold()).split())
        row['normalizedExactMatch']=normalize(transcript.text)==normalize(SHORT[0])
    except Exception as exc:
        row['asrFailure']=type(exc).__name__
    key=uuid.uuid4().hex
    owner='performance-audit-'+key
    lesson._sessions[key]=lesson.Session(owner=owner,
        plan=lesson.ReadingPlan(steps=lesson.labelled_understanding(FLOOR)),
        expires=time.monotonic()+120,problem_text=FLOOR)
    try:
        tick=time.perf_counter()
        answer=await observe('text_reply',lambda: conversation.ask_question(conversation.AskRequest(owner=owner,
            sessionId=key,revision=0,stepIndex=0,
            question='Em chưa hiểu cách phân biệt điều đã biết và điều cần tìm. Em bắt đầu từ đâu?')))
        row.update(replyMs=round((time.perf_counter()-tick)*1000,2),
                   guarded=answer.guarded,answer=answer.answer,
                   status='responded' if 'asrFailure' not in row else 'partial')
    except Exception as exc:
        row.update(status='failed',replyFailure=type(exc).__name__)
    finally:
        lesson._sessions.pop(key,None)
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--live',action='store_true',help='Bounded real lesson/speech provider probes; consumes provider quota.')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    result=dict(checkedAt=datetime.now().astimezone().isoformat(),root=str(ROOT),
                serviceRestarts=False,applicationCodeEdits=False,physicalDeviceVerified=False,
                health=health(),infrastructure=infrastructure(),
                calculation=local_calculation(),digitModel=local_digit_model())
    path=args.output/'performance.json'
    def save(): path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    save()
    if args.live:
        result['lesson']=asyncio.run(live_lesson()); save()
        result['speech']=live_speech(args.output); save()
        result['dialogue']=asyncio.run(live_dialogue(args.output)); save()
    print(json.dumps(result,ensure_ascii=True,indent=2))


if __name__=='__main__':
    main()

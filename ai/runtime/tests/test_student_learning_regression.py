import json
import time
import io
import wave
from fractions import Fraction
from pathlib import Path
import pytest
from app.tutoring import lesson
from app.tutoring.audio_cues import add_cues, read_cues, join_pcm
from app.tutoring.lesson_followup import ResumeRequest, CheckRequest, resume, comprehension_check

CORPUS=json.loads((Path(__file__).parent/'fixtures/student_learning_regression.json').read_text(encoding='utf-8'))['cases']


@pytest.mark.parametrize('case',CORPUS,ids=lambda case:case['id'])
def test_fixed_gold_arithmetic_and_reject_wrong_answers(case):
    answers=[]
    for expression,expected in zip(case['steps'],case['expected']):
        for i,value in reversed(list(enumerate(answers))):expression=expression.replace(f'@{i}',f'({value})')
        actual=lesson.calculate_exact(expression)
        assert actual==Fraction(expected)
        assert actual!=Fraction(expected)+1
        answers.append(str(actual))


@pytest.fixture
def owned(monkeypatch):
    plan=lesson.Plan(topic='Chia đều',goal='Tìm số bút',steps=[
        lesson.Step(title='Gộp',explanation='Gộp hai nhóm bút.',question='Có mấy bút?',expression='12+8'),
        lesson.Step(title='Chia',explanation='Chia đều cho năm bạn.',question='Mỗi bạn có mấy bút?',expression='{s0}/5')],finalAnswerStep=1)
    session=lesson.Session('pupil-a',plan,time.monotonic()+60,problem_text='Có 12 bút và 8 bút, chia cho 5 bạn.')
    key='owned-student-learning-12345'
    monkeypatch.setattr(lesson,'_sessions',{key:session})
    lesson.answer_lesson(lesson.TurnRequest(owner='pupil-a',sessionId=key,revision=0,answer='20'))
    return key,session


def test_resume_requires_owner_source_and_expiry_and_does_not_renew(owned):
    key,session=owned;until=session.expires
    request=ResumeRequest(owner='pupil-a',sessionId=key,problemText=session.problem_text)
    result=resume(request)
    assert result.stepIndex==1 and result.revision==1 and result.step.expression=='20 ÷ 5'
    assert session.expires==until and 'correctChoice' not in result.model_dump_json()
    with pytest.raises(lesson.LessonExpired):resume(request.model_copy(update={'owner':'other'}))
    with pytest.raises(ValueError):resume(request.model_copy(update={'problemText':'Đề khác.'}))
    session.expires=time.monotonic()-1
    with pytest.raises(lesson.LessonExpired):resume(request)


def test_transfer_question_uses_previous_math_never_mutates_lesson_or_reveals_answer(owned):
    key,session=owned;request=CheckRequest(owner='pupil-a',sessionId=key,revision=1)
    before=(list(session.answers),session.revision,session.expires)
    question=comprehension_check(request)
    assert not question['checked'] and not question['correct'] and 'answer' not in question
    expected=lesson.calculate_exact(question['expression'])
    assert expected==21
    assert comprehension_check(request.model_copy(update={'answer':'21'}))['correct']
    assert not comprehension_check(request.model_copy(update={'answer':'20'}))['correct']
    assert not comprehension_check(request.model_copy(update={'answer':'1/0'}))['correct']
    assert (session.answers,session.revision,session.expires)==before
    with pytest.raises(lesson.StaleTurn):comprehension_check(request.model_copy(update={'revision':0}))
    with pytest.raises(lesson.LessonExpired):comprehension_check(request.model_copy(update={'owner':'other'}))


def test_cue_points_follow_actual_decoded_frame_counts_and_reject_invalid_offsets():
    data=join_pcm([b'\x01\x00'*1600,b'\x02\x00'*800,b'\x03\x00'*3200],[0,0,1])
    assert read_cues(data)==[0,2400]
    with wave.open(io.BytesIO(data),'rb') as sound:
        assert sound.getnframes()==5600
        assert sound.readframes(5600)==b'\x01\x00'*1600+b'\x02\x00'*800+b'\x03\x00'*3200
    with pytest.raises(ValueError):add_cues(data,[0,5600])
    with pytest.raises(ValueError):join_pcm([b'\x01\x00'*1600],[1])
    assert read_cues(data[:-3])==[]


@pytest.mark.asyncio
async def test_followup_internal_key_owner_and_stale_checks(owned,monkeypatch):
    import httpx
    from fastapi import FastAPI
    from app.api.tutor import router
    from app.config import settings
    monkeypatch.setattr(settings,'internal_api_key','followup-test-key')
    app=FastAPI();app.include_router(router)
    key,session=owned;headers={'X-Internal-API-Key':'followup-test-key'}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        for route,payload in [('resume',dict(owner='pupil-a',sessionId=key,problemText=session.problem_text)),
                              ('checkpoint',dict(owner='pupil-a',sessionId=key,revision=1))]:
            assert (await client.post('/lesson/'+route,json=payload)).status_code==401
            assert (await client.post('/lesson/'+route,json=payload,headers=headers)).status_code==200
            assert (await client.post('/lesson/'+route,json=payload|{'owner':'another'},headers=headers)).status_code==410
        assert (await client.post('/lesson/checkpoint',json=dict(owner='pupil-a',sessionId=key,revision=0),headers=headers)).status_code==409


def test_aligned_edge_decodes_complete_chunks_and_embeds_actual_boundaries(tmp_path,monkeypatch):
    import shutil
    import subprocess
    from app.config import settings
    from app.tutoring import speech_render
    if not shutil.which('ffmpeg'):pytest.skip('ffmpeg unavailable')
    mp3=tmp_path/'fixture.mp3'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i','sine=frequency=440:sample_rate=16000:duration=0.3','-codec:a','libmp3lame',str(mp3)],check=True,capture_output=True)
    async def chunk(text,voice):return mp3.read_bytes()
    monkeypatch.setattr(settings,'speech_provider','edge');monkeypatch.setattr(speech_render,'_neural_chunk',chunk)
    path=tmp_path/'result.wav'
    speech_render.synthesize_neural('Câu đầu. Câu sau.',path,time.monotonic()+10,paragraphs=['Câu đầu.','Câu sau.'])
    first_frames=len((tmp_path/'part-0.pcm').read_bytes())//2
    assert read_cues(path.read_bytes())==[0,first_frames]
    with wave.open(str(path),'rb') as audio:assert audio.getnframes()==first_frames*2


def test_benchmark_does_not_count_missing_predictions_as_model_or_ocr_success():
    from scripts.benchmark_student_learning import evaluate
    corpus={'version':1,'cases':CORPUS[:2]}
    empty=evaluate(corpus)
    assert empty['modelAnswerAccuracy'] is None and empty['meanCer'] is None
    measured=evaluate(corpus,{'orchard':{'finalAnswer':'59','text':CORPUS[0]['problem']}})
    assert measured['modelAnswersAssessed']==1 and measured['modelAnswerAccuracy']==0
    assert measured['ocrTranscriptsAssessed']==1 and measured['meanCer']==0

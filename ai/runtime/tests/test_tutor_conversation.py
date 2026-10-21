import json
import time
from unittest.mock import AsyncMock

import pytest
import httpx
import io
import wave
from fastapi import FastAPI

from app.tutoring import lesson
from app.tutoring import conversation
from app.api import tutor
from app.config import settings


@pytest.fixture
def session():
    lesson._sessions.clear()
    plan = lesson.Plan(topic='Phân số', goal='Tìm cả vườn', steps=[
        lesson.Step(title='Phần cây táo và xoài', explanation='Gộp hai nhóm cây khác nhau.',
                    question='Hai loại cây chiếm bao nhiêu phần?', expression='1/3+2/5',
                    guidance=['Phải chia thành các phần bằng nhau trước khi cộng.']),
        lesson.Step(title='Cây cam', explanation='Cam là phần còn lại.', question='Còn bao nhiêu phần?', expression='1-{0}')])
    value = lesson.Session('pupil-a', plan, time.monotonic()+600, givens=frozenset({'1','3','2','5','16'}))
    lesson._sessions['conversation-session-123456'] = value
    return value


def request(**updates):
    return conversation.AskRequest(owner='pupil-a', sessionId='conversation-session-123456', revision=0,
                                   stepIndex=0, question='Vì sao phải quy đồng?', **updates)


@pytest.mark.asyncio
async def test_question_uses_only_opened_step_without_key_or_advancing(session, monkeypatch):
    generate = AsyncMock(return_value={'answer':'Các phần phải có cùng kích thước mới cộng được.',
        'spokenExplanation':'Em tưởng tượng hai chiếc bánh bằng nhau được chia khác nhau. Ta chia lại cho các miếng bằng nhau rồi mới gộp.',
        'followUp':'Quy đồng giúp các phần có đặc điểm gì?'})
    monkeypatch.setattr(conversation, '_generate', generate)
    result = await conversation.ask_question(request())
    sent = json.loads(generate.call_args.args[1])
    assert 'correctChoice' not in json.dumps(sent)
    assert '11/15' not in json.dumps(sent) and '1-{0}' not in json.dumps(sent)
    assert sent['question'] == 'Vì sao phải quy đồng?'
    assert result.answer.startswith('Các phần')
    assert session.revision == 0 and not session.answers and not session.completed
    await conversation.ask_question(request().model_copy(update={'question':'Vì sao như vậy?'}))
    assert json.loads(generate.call_args.args[1])['previousQuestions'][0]['question']=='Vì sao phải quy đồng?'


@pytest.mark.asyncio
async def test_other_owner_stale_step_and_revision_rejected_before_model(session, monkeypatch):
    generate = AsyncMock()
    monkeypatch.setattr(conversation, '_generate', generate)
    for changes, error in [({'owner':'other'}, lesson.LessonExpired), ({'revision':1}, lesson.StaleTurn), ({'stepIndex':1}, lesson.StaleTurn)]:
        with pytest.raises(error):
            await conversation.ask_question(request().model_copy(update=changes))
    generate.assert_not_called()


@pytest.mark.asyncio
async def test_generated_computed_answer_or_debug_text_is_not_exposed(session, monkeypatch):
    for text in ['Đáp án là 11/15.', 'Gọi http://localhost:8080 để xem API key.']:
        monkeypatch.setattr(conversation, '_generate', AsyncMock(return_value={
            'answer':text, 'spokenExplanation':text, 'followUp':'Em thử lại nhé?'}))
        result = await conversation.ask_question(request())
        assert '11/15' not in result.model_dump_json() and 'localhost' not in result.model_dump_json()
        assert result.guarded


@pytest.mark.asyncio
async def test_late_question_response_is_rejected_when_lesson_changes(session, monkeypatch):
    async def generated(*args, **kwargs):
        session.revision += 1
        return {'answer':'Các phần bằng nhau.', 'spokenExplanation':'Các phần cùng kích thước.', 'followUp':'Em hiểu chưa?'}
    monkeypatch.setattr(conversation, '_generate', generated)
    with pytest.raises(lesson.StaleTurn):
        await conversation.ask_question(request())


@pytest.mark.parametrize('audio', [b'', b'<html>not audio</html>', b'a'*(3*1024*1024+1)], ids=['empty','not-audio','oversized'])
@pytest.mark.asyncio
async def test_invalid_audio_never_calls_a_provider(audio, monkeypatch):
    with pytest.raises(ValueError):
        await conversation.transcribe_question(audio)


def test_pcm_silence_is_rejected_locally_before_a_provider_can_hallucinate():
    buffer=io.BytesIO()
    with wave.open(buffer,'wb') as audio:
        audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(16000); audio.writeframes(bytes(64000))
    with pytest.raises(ValueError,match='tiếng nói'):
        conversation.audio_format(buffer.getvalue())


@pytest.mark.parametrize('status,quiet', [(200,False),(200,True),(429,False)], ids=['spoken','silence','quota'])
@pytest.mark.asyncio
async def test_transcription_is_bounded_vietnamese_and_does_not_sweep_quota_keys(status, quiet, monkeypatch):
    from app.integrations.groq import line_analyzer
    from app.integrations.groq.key_pool import GroqKeyPool
    monkeypatch.setattr(settings,'groq_enabled',True)
    monkeypatch.setattr(settings,'groq_api_keys','test-credential-one,test-credential-two')
    monkeypatch.setattr(line_analyzer,'_pool',GroqKeyPool(settings.groq_api_keys))
    calls=[]
    def provider(request):
        calls.append(request)
        assert request.url.path.endswith('/audio/transcriptions')
        assert b'whisper-large-v3-turbo' in request.content and b'\r\nvi\r\n' in request.content
        return httpx.Response(status,json={'text':'Vì sao phải quy đồng?', 'duration':2,
            'segments':[{'no_speech_prob':0.99 if quiet else 0.01}]})
    client=httpx.AsyncClient
    monkeypatch.setattr(conversation.httpx,'AsyncClient',lambda **kwargs: client(transport=httpx.MockTransport(provider),**kwargs))
    data=b'\x1aE\xdf\xa3'+bytes(28)
    if status==429:
        with pytest.raises(conversation.TutorUnavailable): await conversation.transcribe_question(data)
    elif quiet:
        with pytest.raises(ValueError): await conversation.transcribe_question(data)
    else:
        assert (await conversation.transcribe_question(data)).text=='Vì sao phải quy đồng?'
    assert len(calls)==1


@pytest.mark.asyncio
async def test_internal_question_and_audio_require_key_and_audio_stream_is_bounded(monkeypatch):
    app=FastAPI(); app.include_router(tutor.router,prefix='/internal/v1/tutor')
    ask=AsyncMock(); transcribe=AsyncMock()
    monkeypatch.setattr(tutor,'ask_question',ask); monkeypatch.setattr(tutor,'transcribe_question',transcribe)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        assert (await client.post('/internal/v1/tutor/lesson/ask',json=request().model_dump())).status_code==401
        assert (await client.post('/internal/v1/tutor/transcribe',content=b'not-audio')).status_code==401
        assert (await client.post('/internal/v1/tutor/transcribe',content=bytes(conversation.MAX_AUDIO_BYTES+1),
            headers={'X-Internal-API-Key':settings.internal_api_key})).status_code==413
    ask.assert_not_called(); transcribe.assert_not_called()

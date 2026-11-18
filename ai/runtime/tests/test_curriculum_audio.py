"""Public speech reuse preserves selected voice and exact issued paragraph order."""
from hashlib import sha256
from collections import OrderedDict
import io
import json
from types import SimpleNamespace
import wave
import zlib
from zipfile import ZipFile, ZIP_DEFLATED

import pytest
from app.tutoring import curriculum_audio, narration
from app.tutoring.audio_cues import read_cues


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    parts = ['Em đọc dữ kiện.', 'Em thử tính nhé.']
    entries = {}
    for index, text in enumerate(parts):
        pcm = (index + 1).to_bytes(2, 'little') * 4000
        key = curriculum_audio.paragraph_key(text)
        with ZipFile(tmp_path / f'public_speech_{key[0]}.zip', 'a', ZIP_DEFLATED) as archive:
            archive.writestr(key + '.pcm', pcm)
        entries[key] = sha256(pcm).hexdigest()
    (tmp_path / 'manifest.json').write_text(json.dumps({'version': 1, 'voice': 'Microsoft An (vi-VN)', 'paragraphs': entries}))
    monkeypatch.setattr(curriculum_audio, 'AUDIO_DIRECTORY', tmp_path)
    curriculum_audio.manifest.cache_clear()
    yield parts
    curriculum_audio.manifest.cache_clear()


def test_prepared_vietnamese_audio_has_exact_boundaries_and_never_impersonates_neural_voices(prepared):
    request = SimpleNamespace(paragraphs=prepared, useFallback=True)
    data = curriculum_audio.load_audio(request)
    narration.validate_audio(data)
    assert read_cues(data) == [0, 4000]
    with wave.open(io.BytesIO(data)) as audio:
        assert audio.getnframes() == 8000
    request.useFallback = False
    assert curriculum_audio.load_audio(request) is None


def test_changed_or_private_paragraphs_do_not_reuse_public_speech(prepared):
    assert curriculum_audio.load_audio(SimpleNamespace(paragraphs=[*prepared, 'Bài làm riêng tư.'], useFallback=True)) is None
    reversed_audio = curriculum_audio.load_audio(SimpleNamespace(paragraphs=prepared[::-1], useFallback=True))
    with wave.open(io.BytesIO(reversed_audio)) as audio:
        assert audio.readframes(1) == b'\x02\x00'


def test_corrupt_public_audio_returns_to_normal_recovery(prepared, tmp_path):
    key = curriculum_audio.paragraph_key(prepared[0])
    (tmp_path / f'public_speech_{key[0]}.zip').write_bytes(b'incomplete')
    assert curriculum_audio.load_audio(SimpleNamespace(paragraphs=prepared, useFallback=True)) is None


def test_non_object_manifest_returns_to_normal_recovery(prepared, tmp_path):
    (tmp_path / 'manifest.json').write_text('[]')
    curriculum_audio.manifest.cache_clear()
    assert curriculum_audio.load_audio(SimpleNamespace(paragraphs=prepared, useFallback=True)) is None


def test_corrupt_compressed_stream_returns_to_normal_recovery(prepared, monkeypatch):
    def corrupt(*args):
        raise zlib.error('Corrupt deflate stream')
    monkeypatch.setattr(ZipFile, 'read', corrupt)
    assert curriculum_audio.load_audio(SimpleNamespace(paragraphs=prepared, useFallback=True)) is None


@pytest.mark.asyncio
@pytest.mark.parametrize('variant', [0, 1])
async def test_every_bundled_lesson_plays_issued_steps_hints_and_solution_without_synthesis(monkeypatch, variant):
    from app.config import settings
    from app.tutoring import curriculum, lesson, media_preparation

    def unavailable(*args, **kwargs):
        raise AssertionError('Bundled speech must already be prepared')

    monkeypatch.setattr(settings, 'lesson_catalog_enabled', False)
    monkeypatch.setattr(lesson.secrets, 'choice', lambda values: values[variant])
    monkeypatch.setattr(lesson, '_sessions', OrderedDict())
    monkeypatch.setattr(narration, '_cache', OrderedDict())
    monkeypatch.setattr(narration, 'render_audio', unavailable)
    rows = json.loads(curriculum.SOURCE.read_text(encoding='utf-8'))['entries']

    def play(response, parts):
        request = narration.NarrationRequest(owner='curriculum-pupil', sessionId=response.sessionId,
            revision=response.revision, paragraphs=parts, useFallback=True)
        assert curriculum_audio.load_audio(request) is not None, (row['id'], parts)
        data = narration.narrate(request)
        narration.validate_audio(data)
        assert len(read_cues(data)) == len(parts)
        return request

    for row in rows:
        response = await lesson.start_lesson(lesson.LessonRequest(owner='curriculum-pupil',
            problemText=row['problemText'], problemConfirmed=True, guidedUnderstanding=True))
        while response.step:
            play(response, media_preparation.script_for_step(response.step))
            for _ in range(2):
                response = lesson.answer_lesson(lesson.TurnRequest(owner='curriculum-pupil',
                    sessionId=response.sessionId, revision=response.revision, hint=True))
                play(response, [response.feedback])
            session = lesson._sessions[response.sessionId]
            step = session.plan.steps[len(session.answers)]
            answer = step.correctChoice if step.choices else str(lesson.calculate_exact(lesson.expression_at(step, session.answers)))
            response = lesson.answer_lesson(lesson.TurnRequest(owner='curriculum-pupil',
                sessionId=response.sessionId, revision=response.revision, answer=answer))
            play(response, media_preparation.script_for_review(response.completed[-1:]))
        assert response.status == 'COMPLETE'
        last = play(response, media_preparation.script_for_review([step for step in response.completed if step.kind != 'UNDERSTAND']))
        with pytest.raises(lesson.LessonExpired):
            narration.narrate(last.model_copy(update={'owner': 'other-pupil'}))

"""Provider formatting recovery must preserve the original question and uncertainty."""
import io
from unittest.mock import AsyncMock

from PIL import Image
import pytest
from pydantic import ValidationError

from app.tutoring import notebook, service


PROBLEM = (
    'Bài 3: Một nền nhà hình chữ nhật có chiều dài 8m, chiều rộng bằng (1)/(2) chiều dài.\n'
    'Người ta lát nền nhà đó bằng các viên gạch hình vuông cạnh 4dm.\n'
    'a) Hỏi cần mua bao nhiêu viên gạch để lát kín nền nhà đó?\n'
    'b) Biết rằng 2m² loại gạch đó giá 250 000 đồng, hỏi cần bao nhiêu tiền để lát nền nhà?'
)


def photo():
    buffer = io.BytesIO()
    Image.new('RGB', (1600, 400), 'white').save(buffer, 'PNG')
    return buffer.getvalue()


def repeated_question():
    return {'kind': 'PROBLEM', 'problemText': PROBLEM, 'lines': [],
            'questions': [{'label': 'Bài 3', 'problemText': PROBLEM, 'uncertain': False}]}


@pytest.mark.asyncio
async def test_single_original_question_with_duplicate_metadata_returns_without_another_cloud_call(monkeypatch):
    payload = service.ProviderResult(repeated_question(), 'groq')
    cloud = AsyncMock(return_value=payload)
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = await notebook.inspect_notebook(photo())
    assert result.kind == 'PROBLEM' and result.problemText == PROBLEM
    assert not result.questions and not result.lines and not result.needsCrop
    assert cloud.await_count == 1
    assert len(payload['questions']) == 1  # Never mutate the provider receipt.
    with pytest.raises(ValidationError):
        notebook.NotebookRead.model_validate(payload)  # Public contract stays strict.


@pytest.mark.parametrize('change', ['digit', 'operator', 'missing_part', 'uncertain', 'unknown', 'extra', 'multiple', 'crop', 'work'])
def test_duplicate_recovery_never_discards_disagreement_or_work(change):
    payload = repeated_question()
    question = payload['questions'][0]
    if change == 'digit':
        question['problemText'] = PROBLEM.replace('8m', '9m')
    elif change == 'operator':
        question['problemText'] = PROBLEM.replace('(1)/(2)', '(1)-(2)')
    elif change == 'missing_part':
        question['problemText'] = PROBLEM.split('\nb)')[0]
    elif change == 'uncertain':
        question['uncertain'] = True
    elif change == 'unknown':
        payload['problemText'] = question['problemText'] = PROBLEM.replace('8m', '[?]m')
    elif change == 'extra':
        question['answer'] = '200'
    elif change == 'multiple':
        payload['questions'].append({'label': 'Bài 4', 'problemText': 'Tính 1+1=?'})
    elif change == 'crop':
        payload['needsCrop'] = True
    else:
        payload['lines'] = [{'text': '8 : 2 = 4', 'role': 'EQUATION'}]
    with pytest.raises(ValidationError):
        notebook._provider_reading(payload)


@pytest.mark.asyncio
@pytest.mark.parametrize('first', [{'kind': 'UNREADABLE'}, {'kind': 'INVALID'}])
async def test_independent_reader_can_recover_one_complete_problem(monkeypatch, first):
    monkeypatch.setattr(service.settings, 'gemini_enabled', True)
    monkeypatch.setattr(service.settings, 'gemini_api_keys', 'test-key')
    cloud = AsyncMock(side_effect=[service.ProviderResult(first, 'groq'),
                                  service.ProviderResult(repeated_question(), 'gemini')])
    monkeypatch.setattr(notebook, '_generate', cloud)
    result = await notebook.inspect_notebook(photo())
    assert result.kind == 'PROBLEM' and result.problemText == PROBLEM
    assert cloud.await_count == 2
    assert cloud.await_args_list[1].kwargs['only_provider'] == 'gemini'


@pytest.mark.asyncio
async def test_malformed_service_response_is_not_reported_as_an_unclear_photo(monkeypatch):
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value={'kind': 'INVALID'}))
    with pytest.raises(service.TutorUnavailable) as caught:
        await notebook.inspect_notebook(photo())
    assert caught.value.reason == 'validation'


@pytest.mark.asyncio
async def test_actual_unreadable_response_still_requests_a_clear_photo(monkeypatch):
    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value={'kind': 'UNREADABLE', 'needsCrop': True}))
    result = await notebook.inspect_notebook(photo())
    assert result.kind == 'UNREADABLE' and result.needsCrop


def test_internal_api_does_not_turn_a_service_format_failure_into_crop_advice(monkeypatch, caplog):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.tutor import router
    from app.config import settings

    monkeypatch.setattr(notebook, '_generate', AsyncMock(return_value={
        'kind': 'INVALID', 'problemText': 'PRIVATE_SOURCE_TEXT'}))
    app = FastAPI()
    app.include_router(router)
    with caplog.at_level('INFO'), TestClient(app) as client:
        response = client.post('/inspect', content=photo(), headers={
            'content-type': 'image/png', 'X-Internal-API-Key': settings.internal_api_key})
    assert response.status_code == 503
    assert response.json() == {'detail': 'Chưa đọc được bài. Em hãy giữ ảnh và thử lại nhé.'}
    assert 'literal_error' in caplog.text
    assert 'PRIVATE_SOURCE_TEXT' not in caplog.text

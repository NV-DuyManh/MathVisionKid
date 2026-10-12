"""Production and trace-disabled requests must not persist uploaded originals."""
import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import settings
from app.main import app


@pytest.mark.parametrize('environment, trace, capture_allowed', [
    ('production', True, False), ('production', False, False),
    ('development', False, False), ('development', True, True),
])
def test_detection_keeps_images_in_memory_unless_development_trace_opted_in(environment, trace, capture_allowed):
    raw = io.BytesIO()
    Image.new('RGB', (100, 150), 'white').save(raw, format='PNG')
    with patch.object(settings, 'app_env', environment), \
         patch.object(settings, 'ocr_physical_trace_enabled', trace), \
         patch('app.api.ocr.detect_text_lines', return_value=([], {'needs_review': True})), \
         patch('app.api.ocr.should_use_groq_line_analyzer', return_value=False), \
         patch('app.api.ocr.open', create=True) as capture, \
         patch('app.api.ocr.os.makedirs') as mkdir:
        client = TestClient(app)
        response = client.post('/internal/v1/ocr/detect-lines', content=raw.getvalue(), headers={
            'Content-Type': 'image/png', 'X-Internal-API-Key': settings.internal_api_key,
            'X-Fast-Path': 'true',
        })
        assert response.status_code == 200, response.text
        assert response.json()['lines'] == []
        if capture_allowed:
            assert [call.args[0].split('/')[-1].split('\\')[-1] for call in capture.call_args_list] == [
                'raw_upload_bytes.bin', 'decoded_input.png', 'metadata.json',
            ]
            mkdir.assert_called_once()
        else:
            capture.assert_not_called()
            mkdir.assert_not_called()

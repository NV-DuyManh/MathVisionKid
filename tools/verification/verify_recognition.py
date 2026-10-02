from pathlib import Path
import hashlib
import json
import logging
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / 'ai/runtime'
EVIDENCE = ROOT / 'report/recognition_unification_20261002'
EVIDENCE.mkdir(parents=True, exist_ok=True)
OLD = EVIDENCE / 'baseline'

if '--pytest' in sys.argv:
    import pytest
    baseline = ET.parse(OLD / 'ai-tests.xml')
    files = sorted({str(Path(*case.attrib['classname'].split('.')[:2])).replace('test_ocr_pilot_endpoint', 'test_ocr_endpoint') + '.py'
                    for case in baseline.findall('.//testcase')})
    import os
    os.chdir(RUNTIME)
    sys.path.insert(0, str(RUNTIME))
    raise SystemExit(pytest.main([*files, '-q', '--tb=short', f'--junitxml={EVIDENCE / "ai-tests.xml"}']))

logging.disable(logging.CRITICAL)
import os
os.chdir(RUNTIME)
sys.path.insert(0, str(RUNTIME))
from app.config import settings
settings.groq_enabled = False
settings.gemini_enabled = False
settings.canonical_runtime_override_enabled = False
from fastapi.testclient import TestClient
from app.main import app

image = OLD / 'owner-image.png'
payload = image.read_bytes()
response = TestClient(app).post('/internal/v1/ocr/detect-lines?forceRedetect=true',
                              content=payload,
                              headers={'Content-Type': 'application/octet-stream', 'X-Internal-Api-Key': settings.internal_api_key})
assert response.status_code == 200, f'Image inference returned {response.status_code}'
result = response.json()
(EVIDENCE / 'owner-image-raw.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
expected = json.loads((OLD / 'owner-image-before.json').read_text(encoding='utf-8-sig'))
# Compare the immutable recognition content, independent of transport IDs and timestamps.
def content(data):
    return {'width': data['width'], 'height': data['height'], 'lines': [
        {key: line.get(key) for key in ('x', 'y', 'width', 'height', 'order', 'text', 'rawOcrText', 'rawOcrConfidence', 'rawOcrConfidenceSource')}
        for line in data['lines']]}

comparison = {
    'imageSha256': hashlib.sha256(payload).hexdigest(),
    'lineCount': len(result['lines']),
    'sameRecognitionAsBefore': content(result) == content(expected),
    'checkpointSha256': hashlib.sha256((RUNTIME / 'models/ocr/crnn_vi_handwriting_v1/best_cer.pth').read_bytes()).hexdigest(),
}
(EVIDENCE / 'image-regression.json').write_text(json.dumps(comparison, indent=2), encoding='utf-8')
print(json.dumps(comparison))
assert comparison['sameRecognitionAsBefore'], 'OCR content differs from the pre-refactor result'
assert comparison['lineCount'] == 9
assert comparison['checkpointSha256'] == 'a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941'

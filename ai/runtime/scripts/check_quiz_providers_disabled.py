"""Read settings actually loaded in the isolated disabled FastAPI process; no secrets in output."""
import json
import sys
import time
from pathlib import Path
from urllib.request import Request,urlopen
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import settings
ROOT=Path(__file__).resolve().parents[3]
for attempt in range(60):
    try:
        with urlopen(Request('http://127.0.0.1:18000/internal/v1/tutor/runtime',headers={'X-Internal-API-Key':settings.internal_api_key}),timeout=2) as response:
            result=json.load(response)
        break
    except Exception:
        if attempt==59: raise
        time.sleep(1)
assert result['groq']['enabled'] is False and result['gemini']['enabled'] is False
(ROOT/'report/smart-quiz-runtime-root-cause/providers-disabled-runtime.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))

"""Real FastAPI test process with both cloud providers disabled, without changing dotenv."""
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'report/smart-quiz-runtime-root-cause'
try:
    with socket.create_connection(('127.0.0.1',18000),timeout=.5):
        raise RuntimeError('Port 18000 is already occupied; no process was stopped')
except OSError:
    pass
env=os.environ.copy()
env.update(GROQ_ENABLED='false',GEMINI_ENABLED='false',GEMINI_FALLBACK_ENABLED='false')
with (OUT/'qa-disabled-fastapi.log').open('w',encoding='utf-8') as output:
    process=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','18000'],cwd=ROOT/'ai/runtime',env=env,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
(OUT/'qa-disabled-fastapi-process.json').write_text(json.dumps({'parentPid':process.pid,'port':18000}),encoding='utf-8')
print('Started isolated FastAPI with GROQ_ENABLED=false and GEMINI_ENABLED=false; readiness still needs checking.')

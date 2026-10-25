"""Actual offline speech rendering through the private narration code, isolated lesson fixture."""
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'ai/runtime'))
from app.tutoring import lesson, narration

directory = Path(__file__).parent / 'samples'
directory.mkdir(exist_ok=True)
examples = {
    'lesson': ['Mình gộp hai nhóm bút để tìm số bút của Lan.', 'Em đặt các chữ số thẳng hàng.', 'Cộng hàng đơn vị trước rồi cộng hàng chục nhé.', 'Lan có tất cả bao nhiêu bút?'],
    'reply': ['Em nhìn hàng đơn vị trước nhé. Nếu gộp được một chục, em nhớ một sang hàng chục. Sau đó em cộng hàng chục và phần nhớ.', 'Hàng đơn vị của hai số là những chữ số nào?'],
}
rows=[]
for name, parts in examples.items():
    key='timeline-audio-sample-session-'+name
    lesson._sessions[key]=SimpleNamespace(owner='isolated-audio-pupil',revision=0,expires=time.monotonic()+600,narration_texts=[' '.join(part.split()) for part in parts])
    request=narration.NarrationRequest(owner='isolated-audio-pupil',sessionId=key,revision=0,paragraphs=parts)
    start=time.monotonic(); data=narration.narrate(request); elapsed=time.monotonic()-start
    (directory/(name+'.wav')).write_bytes(data)
    import io,wave
    with wave.open(io.BytesIO(data),'rb') as sound: duration=sound.getnframes()/sound.getframerate()
    rows.append(dict(name=name,bytes=len(data),seconds=round(duration,2),renderSeconds=round(elapsed,2),modelCalls=0))
(directory/'metadata.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows))

async def smoke():
    import httpx
    from fastapi import FastAPI
    from app.api import tutor
    from app.config import settings
    settings.internal_api_key = 'timeline-local-verification'
    app=FastAPI(); app.include_router(tutor.router)
    payload=dict(owner='isolated-audio-pupil',sessionId='timeline-audio-sample-session-lesson',revision=0,paragraphs=examples['lesson'])
    headers={'X-Internal-API-Key':settings.internal_api_key}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        unauthorized=await client.post('/lesson/narration',json=payload)
        ready=await client.post('/lesson/narration',json=payload,headers=headers)
        other=await client.post('/lesson/narration',json={**payload,'owner':'another-pupil'},headers=headers)
        stale=await client.post('/lesson/narration',json={**payload,'revision':1},headers=headers)
        assert unauthorized.status_code==401 and ready.status_code==200 and other.status_code==410 and stale.status_code==409
        assert ready.headers['content-type']=='audio/wav' and ready.headers['cache-control']=='no-store'
        assert ready.content==(directory/'lesson.wav').read_bytes()
        (directory.parent/'api-smoke.json').write_text(json.dumps(dict(unauthorized=401,ready=200,otherOwner=410,staleRevision=409,contentType='audio/wav',cacheControl='no-store',bytes=len(ready.content),modelCalls=0),indent=2),encoding='utf-8')

import asyncio
asyncio.run(smoke())

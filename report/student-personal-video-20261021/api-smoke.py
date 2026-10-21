import asyncio
import json
from pathlib import Path
import sys
import time
from unittest.mock import AsyncMock

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'ai/runtime'))
import httpx
from fastapi import FastAPI
from app.api import tutor
from app.config import settings
from app.tutoring import lesson

async def main():
    settings.internal_api_key='isolated-video-smoke-key'
    generator=AsyncMock(side_effect=AssertionError('Video must not call a model'));lesson._generate=generator
    sid='private-render-smoke-session-12345'
    lesson._sessions[sid]=lesson.Session('smoke-pupil',lesson.Plan(topic='Toán có lời văn',goal='Tìm số bút còn lại',steps=[
        lesson.Step(title='Được cho thêm',explanation='Được cho thêm thì số bút tăng lên.',question='Sau khi được cho thêm có bao nhiêu bút?',expression='24+13'),
        lesson.Step(title='Cho bạn bớt',explanation='Cho đi thì số bút giảm đi.',question='Sau khi cho bạn còn bao nhiêu bút?',expression='{s0}-5')]),time.monotonic()+120,givens=frozenset({'24','13','5'}))
    app=FastAPI();app.include_router(tutor.router)
    start=time.perf_counter()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://isolated') as client:
        headers={'X-Internal-API-Key':settings.internal_api_key}
        body={'owner':'smoke-pupil','sessionId':sid,'revision':0}
        assert (await client.post('/lesson/video',json=body)).status_code==401
        created=await client.post('/lesson/video',json=body,headers=headers);assert created.status_code==200,created.text
        vid=created.json()['videoId'];lookup={'owner':'smoke-pupil','videoId':vid}
        assert (await client.post('/lesson/video',json=body,headers=headers)).json()['videoId']==vid
        assert (await client.post('/lesson/video/status',json={**lookup,'owner':'other'},headers=headers)).status_code==410
        for _ in range(300):
            status=(await client.post('/lesson/video/status',json=lookup,headers=headers)).json()
            if status['status']!='RENDERING':break
            await asyncio.sleep(.1)
        assert status['status']=='READY' and status['hasAudio'],status
        content=await client.post('/lesson/video/content',json=lookup,headers=headers)
        assert content.status_code==200 and content.headers['cache-control']=='no-store' and content.headers['content-type']=='video/mp4'
        assert content.content[4:8]==b'ftyp'
        lesson._sessions[sid].revision+=1
        assert (await client.post('/lesson/video/content',json=lookup,headers=headers)).status_code==409
        generator.assert_not_called()
        result={'elapsedSeconds':round(time.perf_counter()-start,2),'status':status,'bytes':len(content.content),'ownerGuard':True,'revisionGuard':True,'noStore':True,'additionalModelCalls':0}
        (Path(__file__).parent/'api-smoke.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))
asyncio.run(main())

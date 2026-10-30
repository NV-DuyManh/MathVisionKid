"""QA-only fault injection. Never imported by the production launcher.

Real HTTP/auth/database boundaries remain in Spring; only planner failures and
latency are injected here. Provider transport is covered separately by tests.
"""
import asyncio
from contextvars import ContextVar
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'ai/runtime'))
from app.main import app
from app.tutoring import lesson
from app.tutoring.service import TutorUnavailable

scenario=ContextVar('scenario',default='')
owners={}
attempts={}
original=lesson.reviewed_plan


@app.middleware('http')
async def test_scenario(request,call_next):
    trace=request.headers.get('X-Request-ID','')
    mode=next((m for m in ('timeout','quota','validation','cancelled','delayed') if trace.startswith('qa_'+m+'_')),'')
    marker=scenario.set(mode)
    try: return await call_next(request)
    finally: scenario.reset(marker)


async def injected_plan(request,comprehension):
    if scenario.get(): owners.setdefault(request.owner,scenario.get())
    mode=owners.get(request.owner)
    if not mode: return await original(request,comprehension)
    attempts[request.owner]=attempts.get(request.owner,0)+1
    first=attempts[request.owner]==1
    if first:
        if mode=='timeout': raise TutorUnavailable('TIMEOUT')
        if mode=='quota': raise TutorUnavailable('RATE_LIMIT')
        if mode=='validation': raise TutorUnavailable('VALIDATION_FAILED')
        if mode=='cancelled':
            asyncio.current_task().cancel()
            await asyncio.sleep(0)
    await asyncio.sleep(.75)
    why='Em nhìn các dữ kiện đã xác nhận, xác định số bút đang có và số bút được tặng. Mỗi bước chỉ tính một đại lượng; em tự thực hiện phép tính và đối chiếu với câu hỏi trước khi tiếp tục.'
    how='Em giữ đúng đơn vị đếm. Khi gộp số bút được tặng với số bút đang có, ta dùng phép cộng; em tự tính kết quả, không bỏ qua bước kiểm tra.'
    plan=lesson.Plan(topic='Gộp số bút',goal='Tự tính số bút có tất cả.',finalAnswerStep=1,steps=[
        lesson.Step(title='Xác định số bút ban đầu',explanation=why,question='Ban đầu có bao nhiêu bút?',expression='12*1',unit='bút',guidance=[why,how]),
        lesson.Step(title='Gộp số bút được tặng',explanation=why,question='Có tất cả bao nhiêu bút?',expression='{s0}+5',unit='bút',guidance=[why,how])])
    lesson.validate_plan(plan,request)
    plan=lesson.prepend_understanding(plan,comprehension)
    lesson.validate_plan(plan,request)
    return plan


lesson.reviewed_plan=injected_plan

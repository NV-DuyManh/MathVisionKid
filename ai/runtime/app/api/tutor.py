"""Internal tutoring boundary; public student authentication remains in business-api."""

import secrets
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, JSONResponse

from app.config import settings
from app.tutoring.service import MAX_IMAGE_BYTES, GuideRequest, GuideResponse, ReadResponse, TutorUnavailable, guide_student, read_problem
from app.tutoring.notebook import NotebookRead, CoachRequest, inspect_notebook, coach_notebook
from app.tutoring.lesson import LessonRequest, TurnRequest, LessonResponse, LessonExpired, StaleTurn, start_lesson, answer_lesson, ready_for_answer
from app.tutoring.work_review import WorkReviewRequest, WorkReviewResponse, review_work
from app.tutoring.conversation import AskRequest, AskResponse, Transcript, MAX_AUDIO_BYTES, ask_question, transcribe_question
from app.tutoring import narration, media_preparation, plan_preparation
from app.tutoring.lesson_followup import ResumeRequest, CheckRequest, resume, comprehension_check

router = APIRouter()
logger = logging.getLogger(__name__)


async def require_internal_key(request: Request):
    provided = request.headers.get("X-Internal-API-Key", "")
    if not provided or not secrets.compare_digest(provided.encode(), settings.internal_api_key.encode()):
        raise HTTPException(status_code=401, detail="Không được phép thực hiện yêu cầu này.")


@router.post('/lesson/resume', response_model=LessonResponse, dependencies=[Depends(require_internal_key)])
def resume_lesson_endpoint(request: ResumeRequest):
    try: return resume(request)
    except LessonExpired as exc: raise HTTPException(status_code=410, detail=str(exc)) from None
    except ValueError: raise HTTPException(status_code=400, detail='Đề bài đã thay đổi. Em mở lại bài nhé.') from None


@router.post('/lesson/checkpoint', dependencies=[Depends(require_internal_key)])
def lesson_checkpoint_endpoint(request: CheckRequest):
    try: return comprehension_check(request)
    except LessonExpired as exc: raise HTTPException(status_code=410, detail=str(exc)) from None
    except StaleTurn as exc: raise HTTPException(status_code=409, detail=str(exc)) from None
    except (ValueError, ArithmeticError, SyntaxError): raise HTTPException(status_code=400, detail='Bước này chưa có bài thử nhanh phù hợp.') from None


@router.post('/lesson/narration', dependencies=[Depends(require_internal_key)])
def narration_endpoint(request: narration.NarrationRequest):
    # Synchronous speech/encoder work runs in FastAPI's thread pool, not its event loop.
    try:
        return Response(narration.narrate(request), media_type='audio/wav', headers={'Cache-Control':'no-store'})
    except LessonExpired as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from None
    except StaleTurn as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except narration.NarrationBusy:
        raise HTTPException(status_code=429, detail='Đang chuẩn bị lời giảng. Em thử lại sau một chút nhé.', headers={'Retry-After': '1'}) from None
    except ValueError:
        raise HTTPException(status_code=400, detail='Em mở lại lời giảng của bài đang học nhé.') from None
    except Exception:
        raise HTTPException(status_code=503, detail='Chưa chuẩn bị được âm thanh. Em thử lại hoặc đọc phần chữ nhé.') from None


@router.post('/lesson/narration/status', dependencies=[Depends(require_internal_key)])
def narration_status_endpoint(request: narration.NarrationRequest):
    try:
        return JSONResponse(narration.narration_status(request), headers={'Cache-Control': 'no-store'})
    except LessonExpired as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from None
    except StaleTurn as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except ValueError:
        raise HTTPException(status_code=400, detail='Em mở lại lời giảng nhé.') from None


@router.post('/lesson/narration/prepare', dependencies=[Depends(require_internal_key)])
def narration_prepare_endpoint(request: narration.NarrationRequest):
    try:
        return JSONResponse(narration.prepare_narration(request),headers={'Cache-Control':'no-store'})
    except LessonExpired as exc:
        raise HTTPException(status_code=410,detail=str(exc)) from None
    except StaleTurn as exc:
        raise HTTPException(status_code=409,detail=str(exc)) from None
    except narration.NarrationBusy:
        raise HTTPException(status_code=429,detail='Đang chuẩn bị lời giảng. Em chờ một chút nhé.',headers={'Retry-After':'1'}) from None
    except ValueError:
        raise HTTPException(status_code=400,detail='Em mở lại lời giảng của bài đang học nhé.') from None










@router.post("/work-review", response_model=WorkReviewResponse, dependencies=[Depends(require_internal_key)])
async def work_review_endpoint(request: WorkReviewRequest):
    try:
        return await review_work(request)
    except TutorUnavailable:
        raise HTTPException(status_code=503, detail="Chưa kiểm tra được bài lúc này. Em giữ bài đã viết và thử lại nhé.") from None


@router.post('/lesson/prepare', dependencies=[Depends(require_internal_key)])
async def prepare_lesson_endpoint(request: plan_preparation.SourceDraft):
    return JSONResponse(await plan_preparation.prepare(request), headers={'Cache-Control': 'no-store'})


@router.post("/lesson", response_model=LessonResponse, dependencies=[Depends(require_internal_key)])
async def lesson_endpoint(request: LessonRequest):
    try:
        result = await start_lesson(request)
        try:
            media_preparation.schedule(media_preparation.PrepareRequest(owner=request.owner,sessionId=result.sessionId,revision=result.revision))
        except Exception as exc:
            # Optional preparation must never turn a valid lesson into a failed request.
            logger.info('Lesson preparation not scheduled category=%s', type(exc).__name__)
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail="Em kiểm tra lại đề bài nhé.") from None
    except TutorUnavailable as exc:
        raise HTTPException(status_code=503, detail="Chưa tạo được các bước học. Em giữ đề và thử lại nhé.",
                            headers={"X-Tutor-Failure": exc.reason}) from None


@router.post('/lesson/media/prepare', dependencies=[Depends(require_internal_key)])
def prepare_media_endpoint(request: media_preparation.PrepareRequest):
    try:
        return JSONResponse(media_preparation.schedule(request),headers={'Cache-Control':'no-store'})
    except LessonExpired as exc:
        raise HTTPException(status_code=410,detail=str(exc)) from None
    except StaleTurn as exc:
        raise HTTPException(status_code=409,detail=str(exc)) from None


@router.post("/lesson/answer", response_model=LessonResponse, dependencies=[Depends(require_internal_key)])
async def lesson_answer_endpoint(request: TurnRequest):
    try:
        await ready_for_answer(request)
        result=answer_lesson(request)
        narration.cancel_obsolete_prefetch(request.owner,request.sessionId,result.revision)
        return result
    except LessonExpired as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from None
    except StaleTurn as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except TutorUnavailable as exc:
        raise HTTPException(status_code=503,detail='Chưa chuẩn bị xong phần giải. Em giữ bài và thử lại nhé.',
                            headers={'X-Tutor-Failure': exc.reason}) from None


@router.post('/lesson/ask', response_model=AskResponse, dependencies=[Depends(require_internal_key)])
async def lesson_ask_endpoint(request: AskRequest):
    try:
        return await ask_question(request)
    except LessonExpired as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from None
    except StaleTurn as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except TutorUnavailable:
        raise HTTPException(status_code=503, detail='Chưa trả lời được lúc này. Em giữ câu hỏi và thử lại nhé.') from None


@router.post('/transcribe', response_model=Transcript, dependencies=[Depends(require_internal_key)])
async def transcribe_endpoint(request: Request):
    audio = bytearray()
    async for chunk in request.stream():
        if len(audio) + len(chunk) > MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail='Em ghi câu hỏi ngắn hơn nhé.')
        audio.extend(chunk)
    try:
        return await transcribe_question(bytes(audio))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except TutorUnavailable:
        raise HTTPException(status_code=503, detail='Chưa nghe được lúc này. Em có thể gõ câu hỏi nhé.') from None


async def image_body(request: Request) -> bytes:
    if request.headers.get("content-type", "").split(";", 1)[0].lower() not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Em hãy chọn ảnh JPG, PNG hoặc WebP.")
    image_bytes = bytearray()
    async for chunk in request.stream():
        if len(image_bytes) + len(chunk) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Ảnh quá lớn. Em hãy chọn ảnh nhỏ hơn.")
        image_bytes.extend(chunk)
    return bytes(image_bytes)


@router.post("/read", response_model=ReadResponse, dependencies=[Depends(require_internal_key)])
async def read_endpoint(request: Request):
    try:
        return await read_problem(await image_body(request))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except TutorUnavailable:
        raise HTTPException(status_code=503, detail="Chưa thể đọc đề lúc này. Em có thể tự nhập đề hoặc thử lại sau.") from None


@router.post("/guide", response_model=GuideResponse, dependencies=[Depends(require_internal_key)])
async def guide_endpoint(request: GuideRequest):
    try:
        return await guide_student(request)
    except TutorUnavailable:
        raise HTTPException(status_code=503, detail="Phần gợi ý đang bận. Em hãy giữ lại bài đã làm và thử lại sau.") from None


@router.post("/inspect", response_model=NotebookRead, dependencies=[Depends(require_internal_key)])
async def inspect_endpoint(request: Request):
    try:
        return await inspect_notebook(await image_body(request))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except TutorUnavailable:
        raise HTTPException(status_code=503, detail="Chưa đọc được bài. Em hãy giữ ảnh và thử lại nhé.") from None


@router.post("/coach", response_model=GuideResponse, dependencies=[Depends(require_internal_key)])
async def coach_endpoint(request: CoachRequest):
    try:
        return await coach_notebook(request)
    except TutorUnavailable:
        raise HTTPException(status_code=503, detail="Chưa lấy được gợi ý. Bài của em vẫn được giữ.") from None

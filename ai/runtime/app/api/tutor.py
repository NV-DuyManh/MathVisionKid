"""Internal tutoring boundary; public student authentication remains in business-api."""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from app.config import settings
from app.tutoring.service import MAX_IMAGE_BYTES, GuideRequest, GuideResponse, ReadResponse, TutorUnavailable, guide_student, read_problem
from app.tutoring.notebook import NotebookRead, CoachRequest, inspect_notebook, coach_notebook
from app.tutoring.lesson import LessonRequest, TurnRequest, LessonResponse, LessonExpired, StaleTurn, start_lesson, answer_lesson
from app.tutoring.work_review import WorkReviewRequest, WorkReviewResponse, review_work
from app.tutoring.conversation import AskRequest, AskResponse, Transcript, MAX_AUDIO_BYTES, ask_question, transcribe_question
from app.tutoring import video

router = APIRouter()


async def require_internal_key(request: Request):
    provided = request.headers.get("X-Internal-API-Key", "")
    if not provided or not secrets.compare_digest(provided.encode(), settings.internal_api_key.encode()):
        raise HTTPException(status_code=401, detail="Không được phép thực hiện yêu cầu này.")


def video_call(function, request):
    try:
        return function(request)
    except LessonExpired as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from None
    except StaleTurn as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except video.VideoBusy as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from None


@router.post('/lesson/video', response_model=video.VideoStatus, dependencies=[Depends(require_internal_key)])
async def create_video_endpoint(request: video.VideoRequest):
    return video_call(video.create_video, request)


@router.post('/lesson/video/status', response_model=video.VideoStatus, dependencies=[Depends(require_internal_key)])
async def video_status_endpoint(request: video.VideoLookup):
    return video_call(video.video_status, request)


@router.post('/lesson/video/content', dependencies=[Depends(require_internal_key)])
async def video_content_endpoint(request: video.VideoLookup):
    return Response(video_call(video.video_content, request), media_type='video/mp4', headers={'Cache-Control':'no-store'})


@router.post("/work-review", response_model=WorkReviewResponse, dependencies=[Depends(require_internal_key)])
async def work_review_endpoint(request: WorkReviewRequest):
    try:
        return await review_work(request)
    except TutorUnavailable:
        raise HTTPException(status_code=503, detail="Chưa kiểm tra được bài lúc này. Em giữ bài đã viết và thử lại nhé.") from None


@router.post("/lesson", response_model=LessonResponse, dependencies=[Depends(require_internal_key)])
async def lesson_endpoint(request: LessonRequest):
    try:
        return await start_lesson(request)
    except ValueError:
        raise HTTPException(status_code=400, detail="Em kiểm tra lại đề bài nhé.") from None
    except TutorUnavailable:
        raise HTTPException(status_code=503, detail="Chưa tạo được các bước học. Em giữ đề và thử lại nhé.") from None


@router.post("/lesson/answer", response_model=LessonResponse, dependencies=[Depends(require_internal_key)])
async def lesson_answer_endpoint(request: TurnRequest):
    try:
        return answer_lesson(request)
    except LessonExpired as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from None
    except StaleTurn as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None


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

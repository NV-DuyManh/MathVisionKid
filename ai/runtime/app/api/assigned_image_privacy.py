"""Internal, local inference endpoint for sanitized assigned-work images."""

import math
import io
import os
from pathlib import Path
import re
import secrets
import threading
import unicodedata
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool


MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 16_000_000
_inference = threading.Lock()
_detectors = None
_quantity_unit = re.compile(
    r"(?<=[0-9])[ \t]*(?:mm|cm|dm|km|m|mg|kg|g|ml|l)(?:[²³])?(?![\w])",
    re.IGNORECASE,
)
# The pinned recognizer drops the final vowel in "Đáp số" on a reference fixture.
_answer_prefix = re.compile(r"^\s*đáp (?:số|s|án)\s*:\s*(?=[0-9(−-])", re.IGNORECASE)
_solution_heading = re.compile(r"^\s*(?:bài giải|lời giải|phép tính)\s*[:.]?\s*$", re.IGNORECASE)
_counted_object = re.compile(r"(?<=[0-9])[ \t]+(?:qu(?:ả)? táo|quả cam|quyển vở|cái bút)(?!\w)", re.IGNORECASE)
_split_phone = re.compile(r"(?m)^\s*(?:0|\+84[ \t]*)[0-9]{1,4}(?:[ \t]*\n[ \t]*[0-9]{2,5})+\s*$")
_counting_clause = re.compile(
    r"(?:có(?: tất cả| tt c)?|thêm|bớt|còn lại|đáp (?:số|s|án):) +"
    r"[0-9]{1,6} +(?:qu(?:ả)?(?: táo| cam)?|quyển vở|cái bút)",
    re.IGNORECASE,
)


def review_text(texts, scores):
    if not texts or len(texts) != len(scores):
        return "UNCERTAIN"
    for text, score in zip(texts, scores):
        if not isinstance(text, str) or not text.strip() or not math.isfinite(score) or score < 0.80:
            return "UNCERTAIN"
        text = unicodedata.normalize("NFC", text)
        if _solution_heading.fullmatch(text):
            continue
        if re.search(r"\d(?:[ .-]?\d){8,}", text):
            return "BLOCKED"
        clauses = text.strip().removesuffix(".").split(".")
        if all(_counting_clause.fullmatch(clause.strip()) for clause in clauses):
            continue
        expression = _quantity_unit.sub("", _answer_prefix.sub("", text))
        expression = _counted_object.sub("", expression)
        if re.search(r"[^0-9\s+\-×÷*/=.,()−]", expression):
            return "BLOCKED"
    if not any(re.search(r"[0-9]", text) for text in texts):
        return "UNCERTAIN"
    for match in _split_phone.finditer("\n".join(texts)):
        digits = re.sub(r"\D", "", match.group())
        if len(digits) == (11 if match.group().lstrip().startswith("+84") else 10):
            return "UNCERTAIN"
    return "CLEAR"


def inspect_image(data):
    import cv2
    import numpy as np

    global _detectors
    if not _inference.acquire(blocking=False):
        raise HTTPException(503, "Privacy review busy")
    try:
        try:
            with Image.open(io.BytesIO(data), formats=["JPEG", "PNG"]) as header:
                width, height = header.size
                if width * height > MAX_PIXELS:
                    raise HTTPException(413, "Image dimensions exceed limit")
        except Image.DecompressionBombError:
            raise HTTPException(413, "Image dimensions exceed limit") from None
        except (UnidentifiedImageError, OSError):
            return "UNCERTAIN"
        image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None or image.shape[0] * image.shape[1] > MAX_PIXELS:
            return "UNCERTAIN"
        if _detectors is None:
            from paddleocr import PaddleOCR

            root = os.environ.get("ASSIGNED_PRIVACY_MODEL_DIR")
            if not root:
                raise RuntimeError("Missing local model directory")
            detector = Path(root) / "PP-OCRv5_mobile_det"
            recognizer = Path(root) / "latin_PP-OCRv5_mobile_rec"
            face_model = Path(root) / "face_detection_yunet.onnx"
            if not detector.is_dir() or not recognizer.is_dir() or not face_model.is_file():
                raise RuntimeError("Missing local privacy model")
            faces = cv2.FaceDetectorYN.create(str(face_model), "", (320, 320))
            ocr = PaddleOCR(
                text_detection_model_name=detector.name,
                text_detection_model_dir=str(detector),
                text_recognition_model_name=recognizer.name,
                text_recognition_model_dir=str(recognizer),
                device="cpu",
                enable_mkldnn=False,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
            _detectors = faces, ocr
        faces, ocr = _detectors
        height, width = image.shape[:2]
        ratio = min(1, 1280 / max(width, height))
        preview = cv2.resize(image, (max(1, int(width * ratio)), max(1, int(height * ratio))))
        faces.setInputSize((preview.shape[1], preview.shape[0]))
        _, detections = faces.detect(preview)
        if detections is not None and len(detections):
            return "BLOCKED"
        results = list(ocr.predict(image, text_rec_score_thresh=0))
        texts = [text for result in results for text in result["rec_texts"]]
        scores = [score for result in results for score in result["rec_scores"]]
        if any(len(result["dt_polys"]) != len(result["rec_texts"]) for result in results):
            return "UNCERTAIN"
        return review_text(texts, scores)
    finally:
        _inference.release()


def warm_up():
    import cv2
    import numpy as np

    if not os.environ.get("ASSIGNED_PRIVACY_KEY"):
        raise RuntimeError("Missing internal privacy key")
    sample = np.full((180, 640, 3), 255, dtype=np.uint8)
    cv2.putText(sample, "12 + 34 = 46", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
    encoded, png = cv2.imencode(".png", sample)
    if not encoded or inspect_image(png.tobytes()) != "CLEAR":
        raise RuntimeError("Privacy model startup check failed")


@asynccontextmanager
async def lifespan(_app):
    await run_in_threadpool(warm_up)
    yield


app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None, lifespan=lifespan)


@app.post("/internal/v1/assigned-image-privacy")
async def check_image(request: Request):
    key = os.environ.get("ASSIGNED_PRIVACY_KEY")
    if not key:
        raise HTTPException(503, "Privacy review unavailable")
    if not secrets.compare_digest(key.encode(), request.headers.get("X-API-Key", "").encode()):
        raise HTTPException(403, "Forbidden")
    if request.headers.get("content-type") not in {"image/jpeg", "image/png"}:
        raise HTTPException(415, "Unsupported image type")
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > MAX_BYTES:
            raise HTTPException(413, "Image too large")
        data.extend(chunk)
    content_type = request.headers["content-type"]
    if ((content_type == "image/jpeg" and not data.startswith(b"\xff\xd8\xff"))
            or (content_type == "image/png" and not data.startswith(b"\x89PNG\r\n\x1a\n"))):
        raise HTTPException(415, "Invalid image")
    try:
        decision = await run_in_threadpool(inspect_image, data)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, "Privacy review unavailable") from None
    return {"decision": decision}

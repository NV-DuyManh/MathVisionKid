import logging
from app.jobs.celery_app import celery_app
from app.callbacks.spring_callback import send_callback
from app.schemas.jobs import AiCallbackRequest, GradeProposal, StudentFeedback
from app.schemas.confidence import ConfidenceBundle
from app.config import settings
from app.recognition.fixture import FixtureRecognitionEngine
from app.validation.addition import VerticalAdditionValidator
from app.validation.subtraction import VerticalSubtractionValidator
from app.recognition.quality import QualityGate
from app.parsing.parser import StructuredParser
from app.policy.student_policy import generate_student_feedback
from app.policy.teacher_policy import generate_teacher_feedback
from app.observability.logging import set_correlation_context
import httpx

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_submission(self, job_id: str, request_data: dict):
    try:
        set_correlation_context(job_id, request_data.get('submissionId'))
        logger.info(f"Processing job {job_id} for submission {request_data.get('submissionId')}")

        image_ref = request_data.get('imageReference', '')
        policy_mode = request_data.get('policyMode', 'STUDENT')  # STUDENT | TEACHER

        # ── 1. Quality Gate ──────────────────────────────────────────────────
        quality_gate = QualityGate()
        quality_status = quality_gate.evaluate(image_ref)
        if quality_status != "PASS":
            callback = AiCallbackRequest(status=quality_status)
            send_callback(job_id, callback)
            return quality_status

        # ── 2. Recognition ───────────────────────────────────────────────────
        if settings.runtime_mode == "FIXTURE":
            engine = FixtureRecognitionEngine()
        else:
            from app.recognition.model_engine import ModelRecognitionEngine
            engine = ModelRecognitionEngine()
            if not engine.is_ready:
                logger.error("MODEL mode active but ModelRecognitionEngine is not ready.")
                callback = AiCallbackRequest(status="MODEL_NOT_AVAILABLE")
                send_callback(job_id, callback)
                return "MODEL_NOT_AVAILABLE"

        try:
            recognition_result = engine.recognize(image_ref)
        except Exception as e:
            logger.error(f"Recognition failed in mode {settings.runtime_mode}: {e}")
            callback = AiCallbackRequest(status="MODEL_NOT_AVAILABLE")
            send_callback(job_id, callback)
            return "MODEL_NOT_AVAILABLE"

        # Log OCR Bridge diagnostics if available
        if getattr(recognition_result, "line_recognitions", None):
            recs = recognition_result.line_recognitions
            logger.info(
                f"OCR Bridge processed {len(recs)} rows | "
                f"provider={getattr(recognition_result, 'ocr_provider_used', 'none')} | "
                f"all_agree={getattr(recognition_result, 'all_rows_agree', None)}"
            )
            for r in recs:
                logger.info(
                    f"  Row {r.row_index}: YOLO='{r.yolo_text}' | CRNN='{r.crnn_text}' | Agreement={r.agreement}"
                )

        # Canonical confidence bundle — deterministic in fixture mode
        if recognition_result.status == "UNCERTAIN_RECOGNITION":
            conf = ConfidenceBundle(recognition=0.4, structure=0.3, diagnosis=0.0)
        elif recognition_result.status == "SUCCESS":
            rec_conf = 0.99
            if settings.runtime_mode == "MODEL" and recognition_result.tokens:
                rec_conf = round(sum(t.confidence for t in recognition_result.tokens) / len(recognition_result.tokens), 2)
            conf = ConfidenceBundle(recognition=rec_conf, structure=0.95, diagnosis=0.0)
        else:
            conf = ConfidenceBundle(recognition=0.0, structure=0.0, diagnosis=0.0)

        # ── 3. Parsing ───────────────────────────────────────────────────────
        parser = StructuredParser()
        parsed_exercise = parser.parse(recognition_result)

        # Update structure confidence from parse result
        if parsed_exercise.status == "VALID_STRUCTURE":
            conf = ConfidenceBundle(recognition=conf.recognition, structure=0.97, diagnosis=0.0)

        # ── 4. OUT_OF_SCOPE / UNCERTAINTY early exits ────────────────────────
        if parsed_exercise.status == "OUT_OF_SCOPE":
            if policy_mode == "STUDENT":
                result = generate_student_feedback(parsed_exercise, {})
                callback = AiCallbackRequest(
                    status=result["status"],
                    studentFeedback=result.get("studentFeedback"),
                    confidenceBundle=conf.model_dump()
                )
            else:
                result = generate_teacher_feedback(parsed_exercise, {})
                callback = AiCallbackRequest(
                    status=result["status"],
                    confidenceBundle=conf.model_dump()
                )
            send_callback(job_id, callback)
            return "OUT_OF_SCOPE"

        if parsed_exercise.status == "UNCERTAIN_STRUCTURE":
            if policy_mode == "STUDENT":
                result = generate_student_feedback(parsed_exercise, {})
                status_out = result["status"]   # NEEDS_CONFIRMATION
                callback = AiCallbackRequest(
                    status=status_out,
                    studentFeedback=result.get("studentFeedback"),
                    confidenceBundle=conf.model_dump()
                )
            else:
                result = generate_teacher_feedback(parsed_exercise, {})
                status_out = result["status"]   # REVIEW_REQUIRED
                callback = AiCallbackRequest(
                    status=status_out,
                    evidence=result.get("evidence"),
                    confidenceBundle=conf.model_dump()
                )
            send_callback(job_id, callback)
            return status_out

        # ── 5. Deterministic Validation ──────────────────────────────────────
        if parsed_exercise.operationType == "VERTICAL_ADDITION":
            validator = VerticalAdditionValidator()
        elif parsed_exercise.operationType == "VERTICAL_SUBTRACTION":
            validator = VerticalSubtractionValidator()
        else:
            callback = AiCallbackRequest(status="OUT_OF_SCOPE", confidenceBundle=conf.model_dump())
            send_callback(job_id, callback)
            return "OUT_OF_SCOPE"

        validation_result = validator.validate(parsed_exercise)

        # Update diagnosis confidence
        diag_conf = 0.97 if validation_result.get("is_valid") else 0.93
        conf = ConfidenceBundle(
            recognition=conf.recognition,
            structure=conf.structure,
            diagnosis=diag_conf
        )

        recognized_expr = (
            f"{parsed_exercise.operands[0]} "
            f"{'+ ' if 'ADDITION' in parsed_exercise.operationType else '- '}"
            f"{parsed_exercise.operands[1]} = {parsed_exercise.result}"
        )

        # ── 6. Policy Layer ──────────────────────────────────────────────────
        if policy_mode == "STUDENT":
            result = generate_student_feedback(parsed_exercise, validation_result)
            callback = AiCallbackRequest(
                status=result["status"],
                studentFeedback=result.get("studentFeedback"),
                evidence=validation_result.get("evidence") if not validation_result.get("is_valid") else None,
                recognizedExercise=recognized_expr,
                confidenceBundle=conf.model_dump()
            )
        else:
            result = generate_teacher_feedback(parsed_exercise, validation_result)
            callback = AiCallbackRequest(
                status=result["status"],
                gradeProposal=result.get("gradeProposal"),
                evidence=result.get("evidence"),
                recognizedExercise=recognized_expr,
                confidenceBundle=conf.model_dump()
            )

        send_callback(job_id, callback)
        return "COMPLETED"

    except httpx.HTTPStatusError as exc:
        if 400 <= exc.response.status_code < 500:
            logger.error(
                f"Callback 4xx error for job {job_id}: {exc.response.status_code}. Not retrying."
            )
            return "FAILED_NO_RETRY"
        logger.error(f"Callback HTTP error for job {job_id}: {exc}. Retrying...")
        self.retry(exc=exc, countdown=2 ** self.request.retries)
    except httpx.RequestError as exc:
        logger.error(f"Network error processing job {job_id}: {exc}. Retrying...")
        self.retry(exc=exc, countdown=2 ** self.request.retries)
    except Exception as exc:
        logger.error(f"Error processing job {job_id}: {exc}", exc_info=True)
        self.retry(exc=exc, countdown=2 ** self.request.retries)

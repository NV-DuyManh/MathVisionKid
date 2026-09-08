package com.mathvisionkids.api.analysis;

import lombok.Data;
import java.util.List;
import java.util.Map;

/**
 * Canonical callback payload received from the FastAPI/Celery AI pipeline.
 */
@Data
public class AiCallbackRequest {
    /** Job terminal status from AI pipeline. */
    private String status;

    /** Optionally recognized arithmetic expression (e.g. "12 + 34 = 46"). */
    private String recognizedExercise;

    /** Grade proposal (present for PROPOSED_GRADE status). */
    private Map<String, Object> gradeProposal;

    /** Evidence items (present for invalid arithmetic or uncertainty). */
    private List<Map<String, Object>> evidence;

    /** Student feedback (present for FEEDBACK_READY / NEEDS_CONFIRMATION). */
    private Map<String, Object> studentFeedback;

    /** Canonical confidence bundle: recognition, structure, diagnosis. */
    private Map<String, Object> confidenceBundle;
}

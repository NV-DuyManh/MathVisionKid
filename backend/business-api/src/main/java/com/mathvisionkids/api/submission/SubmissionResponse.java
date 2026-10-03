package com.mathvisionkids.api.submission;

import lombok.Data;
import java.time.Instant;
import java.util.UUID;

@Data
public class SubmissionResponse {
    private UUID submissionId;
    private UUID jobId;
    private String status;
    private String reasonCode;
    private java.util.Map<String, Object> diagnostics;
    private String flowDomain = "ARITHMETIC";
    private Instant createdAt;
    private java.util.Map<String, Object> recognizedExercise;
    private java.util.Map<String, Object> validation;
    private java.util.Map<String, Object> evidence;
    private java.util.Map<String, Object> studentFeedback;
    private java.util.Map<String, Object> confidenceBundle;
    private String modelVersion;
    private java.util.List<String> uncertainTokenIds = java.util.List.of();
}

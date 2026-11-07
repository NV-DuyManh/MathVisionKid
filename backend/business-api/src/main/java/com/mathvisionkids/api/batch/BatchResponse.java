package com.mathvisionkids.api.batch;

import com.mathvisionkids.api.submission.Submission;
import java.time.Instant;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/** Read progress from submissions, including batches created before progress was derived. */
public record BatchResponse(UUID batchId, String status, int totalCount, int processedCount,
                            int reviewRequiredCount, int failedCount, Instant createdAt,
                            Instant startedAt, Instant completedAt) {
    private static final Set<String> TERMINAL = Set.of("PROPOSED_GRADE", "FEEDBACK_READY", "REVIEW_REQUIRED",
            "NEEDS_CONFIRMATION", "NEEDS_RETAKE", "TEACHER_APPROVED", "TEACHER_OVERRIDDEN", "FAILED");
    private static final Set<String> REVIEW = Set.of("REVIEW_REQUIRED", "NEEDS_CONFIRMATION", "NEEDS_RETAKE");

    public static BatchResponse from(Batch batch, List<Submission> submissions) {
        int processed = (int) submissions.stream().filter(s -> TERMINAL.contains(s.getStatus())).count();
        int review = (int) submissions.stream().filter(s -> REVIEW.contains(s.getStatus())).count();
        int failed = (int) submissions.stream().filter(s -> "FAILED".equals(s.getStatus())).count();
        String status = batch.getStatus();
        if (!submissions.isEmpty()) {
            status = processed < submissions.size() ? "PROCESSING"
                    : failed == submissions.size() ? "FAILED" : failed > 0 ? "PARTIAL" : "COMPLETED";
        }
        return new BatchResponse(batch.getBatchId(), status, submissions.size(), processed, review, failed,
                batch.getCreatedAt(), batch.getStartedAt(), batch.getCompletedAt());
    }
}

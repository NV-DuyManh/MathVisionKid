package com.mathvisionkids.api.batch;

import com.mathvisionkids.api.submission.Submission;
import java.time.Instant;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/** Read progress from submissions, including batches created before progress was derived. */
public record BatchResponse(UUID batchId, UUID assignmentId, String assignmentTitle, String className,
                            String status, int totalCount, int processedCount, int reviewRequiredCount,
                            int pendingReviewCount, int finalizedCount, int failedCount, Instant createdAt,
                            Instant startedAt, Instant completedAt, List<SubmissionSummary> submissions) {
    public record SubmissionSummary(UUID submissionId, String studentName, String status) {}

    private static final Set<String> TERMINAL = Set.of("PROPOSED_GRADE", "FEEDBACK_READY", "REVIEW_REQUIRED",
            "NEEDS_CONFIRMATION", "NEEDS_RETAKE", "TEACHER_APPROVED", "TEACHER_OVERRIDDEN", "FAILED");
    private static final Set<String> REVIEW = Set.of("REVIEW_REQUIRED", "NEEDS_CONFIRMATION", "NEEDS_RETAKE");
    static final Set<String> PENDING_REVIEW = Set.of(
            "REVIEW_REQUIRED", "NEEDS_CONFIRMATION", "NEEDS_RETAKE", "PROPOSED_GRADE", "FEEDBACK_READY");
    private static final Set<String> FINALIZED = Set.of("TEACHER_APPROVED", "TEACHER_OVERRIDDEN");

    static boolean needsTeacherReview(Submission submission) {
        return PENDING_REVIEW.contains(submission.getStatus());
    }

    public static BatchResponse from(Batch batch, List<Submission> submissions) {
        return from(batch, submissions, false);
    }

    static BatchResponse from(Batch batch, List<Submission> submissions, boolean includeSubmissions) {
        int processed = (int) submissions.stream().filter(s -> TERMINAL.contains(s.getStatus())).count();
        int review = (int) submissions.stream().filter(s -> REVIEW.contains(s.getStatus())).count();
        int pending = (int) submissions.stream().filter(BatchResponse::needsTeacherReview).count();
        int finalized = (int) submissions.stream().filter(s -> FINALIZED.contains(s.getStatus())).count();
        int failed = (int) submissions.stream().filter(s -> "FAILED".equals(s.getStatus())).count();
        String status = batch.getStatus();
        if (!submissions.isEmpty()) {
            status = processed < submissions.size() ? "PROCESSING"
                    : failed == submissions.size() ? "FAILED" : failed > 0 ? "PARTIAL" : "COMPLETED";
        }
        var assignment = batch.getAssignment();
        var classroom = assignment == null ? null : assignment.getClassroom();
        var summaries = includeSubmissions ? submissions.stream()
                .map(s -> new SubmissionSummary(s.getSubmissionId(),
                        s.getStudent() == null ? null : s.getStudent().getDisplayName(), s.getStatus()))
                .toList() : null;
        return new BatchResponse(batch.getBatchId(), assignment == null ? null : assignment.getAssignmentId(),
                assignment == null ? null : assignment.getTitle(), classroom == null ? null : classroom.getName(),
                status, submissions.size(), processed, review, pending, finalized, failed,
                batch.getCreatedAt(), batch.getStartedAt(), batch.getCompletedAt(), summaries);
    }
}

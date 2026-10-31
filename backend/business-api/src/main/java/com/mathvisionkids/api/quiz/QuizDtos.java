package com.mathvisionkids.api.quiz;

import com.fasterxml.jackson.annotation.JsonAnySetter;
import jakarta.validation.constraints.*;
import java.time.Instant;
import java.util.*;

public final class QuizDtos {
    private QuizDtos() {}
    public record Prepare(@NotNull UUID workflowKey, @Min(0) long revision,
                          @com.fasterxml.jackson.annotation.JsonAlias("confirmedProblemText") @NotNull @Size(max=4000) String problemText, boolean problemConfirmed) {
        @JsonAnySetter public void unknown(String key, Object value) { throw new IllegalArgumentException("Unknown field"); }
    }
    public record Preparation(UUID preparationId, long revision, String status, String errorCode) {}
    public record FromLearning(@NotBlank @Pattern(regexp="LESSON|WORK_REVIEW") String sourceType,
                               @NotBlank @Size(max=100) String sourceId) {
        @JsonAnySetter public void unknown(String key, Object value) { throw new IllegalArgumentException("Unknown field"); }
    }
    public record Submission(@NotNull UUID requestId, @NotBlank @Size(max=100) String answer) {
        @JsonAnySetter public void unknown(String key, Object value) { throw new IllegalArgumentException("Unknown field"); }
    }
    public record Voice(@NotBlank @Pattern(regexp="vi-VN-NamMinhNeural|vi-VN-HoaiMyNeural") String voice) {
        @JsonAnySetter public void unknown(String key, Object value) { throw new IllegalArgumentException("Unknown field"); }
    }
    public record ReplayRequest(String mode) {
        @JsonAnySetter public void unknown(String key, Object value) { throw new IllegalArgumentException("Unknown field"); }
    }
    public record Attempt(int number, String answer, boolean correct, Instant submittedAt, long elapsedMillis, int stars, String mode, String questionText, Boolean solutionViewed, Instant runStartedAt) {}
    public record View(UUID quizId, String sourceType, String sourceId, String topicCode, String topicName,
                       String skillCode, int gradeLevel, String taxonomyVersion, String verificationStatus,
                       int confidencePercent, String questionText, String unit, String answerFormat, String status,
                       Instant createdAt, Instant startedAt, Instant completedAt, Instant serverNow,
                       long elapsedMillis, int stars, int wrongAttempts, boolean solutionViewed,
                       boolean completedWithSolution, boolean canRevealSolution, List<Attempt> attempts,
                       String explanationText, String correctAnswer, String replayMode, String originalQuestionText) {}
    public record Invitation(boolean offered, View quiz) {}
    public record Library(List<View> items, int page, int totalPages, long totalElements) {}
    public record Counts(long pendingCount, long totalStars) {}
    public record Graded(View quiz, Attempt attempt) {}
}

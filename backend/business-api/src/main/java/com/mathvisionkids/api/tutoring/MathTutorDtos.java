package com.mathvisionkids.api.tutoring;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.JsonMappingException;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public final class MathTutorDtos {
    private MathTutorDtos() {}

    public record ReadResponse(String problemText, boolean needsReview, String notes) {}

    public record GuideRequest(
            @NotBlank @Size(min = 3, max = 4000) String problemText,
            @NotNull @AssertTrue Boolean problemConfirmed,
            @NotNull @Pattern(regexp = "UNDERSTAND|PLAN|NEXT_STEP|CHECK_WORK") String stage,
            @Size(max = 2000) String studentAttempt,
            @NotNull @Min(0) @Max(2) Integer hintLevel,
            @Size(max = 1200) String previousHint) {}

    public record GuideResponse(String stage, String hint, String question, String feedback, boolean guarded) {}

    public record WrittenDivision(
            @NotNull @Size(min = 1, max = 24) @Pattern(regexp = "(?:[0-9]|\\[\\?\\])+") String dividend,
            @NotNull @Size(min = 1, max = 24) @Pattern(regexp = "(?:[0-9]|\\[\\?\\])+") String divisor,
            @Size(min = 1, max = 24) @Pattern(regexp = "(?:[0-9]|\\[\\?\\])+") String quotient,
            @NotNull @Size(max = 30) java.util.List<@NotNull @Size(min = 1, max = 40)
                    @Pattern(regexp = "(?:[0-9 +\\-−]|\\[\\?\\])+") String> rows) {}
    public record DivisionCheckRequest(@NotNull @jakarta.validation.Valid WrittenDivision division,
                                       @NotNull @AssertTrue Boolean confirmed) {}
    public record DivisionCheckResponse(String status, String field, Integer rowIndex, String message,
                                        java.util.List<String> hints) {
        public DivisionCheckResponse(String status, String field, Integer rowIndex, String message) {
            this(status, field, rowIndex, message, java.util.List.of());
        }
    }
    public record NotebookLine(String text, java.util.List<Integer> box, boolean uncertain, WrittenDivision division) {
        public NotebookLine(String text, java.util.List<Integer> box, boolean uncertain) {
            this(text, box, uncertain, null);
        }
    }
    public record NotebookRead(String kind, String problemText, java.util.List<NotebookLine> lines,
                               boolean needsProblem, boolean needsCrop) {}
    public record CoachRequest(
            @NotNull @Size(max = 4000) String problemText,
            @NotNull @Size(max = 6000) String workText,
            @NotNull @Pattern(regexp = "UNDERSTAND|PLAN|NEXT_STEP|CHECK_WORK") String stage,
            @NotNull @Size(max = 2000) String studentAttempt,
            @NotNull @Size(max = 500) String focusText,
            @NotNull @Min(0) @Max(2) Integer hintLevel,
            @NotNull @Size(max = 1200) String previousHint) {}

    public record WorkReviewRequest(
            @NotBlank @Size(min = 16, max = 100) String sourceId,
            @NotBlank @Size(min = 3, max = 4000) String problemText,
            @NotBlank @Size(min = 3, max = 6000) String workText,
            @NotNull @AssertTrue @JsonDeserialize(using = LiteralBoolean.class) Boolean problemConfirmed,
            @NotNull @AssertTrue @JsonDeserialize(using = LiteralBoolean.class) Boolean workConfirmed) {
        java.util.List<String> sourceRows() {
            if (workText == null) return java.util.List.of();
            // Match Python splitlines/strip, including nonbreaking spaces in transcriptions.
            return java.util.Arrays.stream(workText.split("\\R|[\\x1c-\\x1e]"))
                    .map(row -> row.replaceAll("(?U)^[\\s\\x1c-\\x1f]+|[\\s\\x1c-\\x1f]+$", ""))
                    .filter(row -> !row.isEmpty()).toList();
        }
        @com.fasterxml.jackson.annotation.JsonIgnore @AssertTrue public boolean isSourceConfirmed() {
            if (!Boolean.TRUE.equals(problemConfirmed) || !Boolean.TRUE.equals(workConfirmed)
                    || sourceId == null || sourceId.isBlank() || sourceId.length() < 16 || sourceId.length() > 100
                    || problemText == null || problemText.strip().length() < 3 || problemText.length() > 4000
                    || workText == null || workText.strip().length() < 3 || workText.length() > 6000
                    || problemText.contains("[?]") || workText.contains("[?]")) return false;
            var rows = sourceRows();
            return !rows.isEmpty() && rows.size() <= 35 && rows.stream().allMatch(row -> row.length() <= 500);
        }
    }
    public static final class LiteralBoolean extends JsonDeserializer<Boolean> {
        @Override public Boolean deserialize(JsonParser parser, DeserializationContext context) throws java.io.IOException {
            if (parser.currentToken() != JsonToken.VALUE_TRUE && parser.currentToken() != JsonToken.VALUE_FALSE)
                throw JsonMappingException.from(parser, "Expected a literal boolean");
            return parser.getBooleanValue();
        }
    }
    public record WorkReviewRow(int lineIndex, String sourceText, String status, String feedback, java.util.List<String> hints) {}
    public record WorkReviewResponse(String sourceId, String status, String summary, String praise,
                                     java.util.List<WorkReviewRow> rows, String nextAction, String alternative) {}

    public record LessonRequest(@NotBlank @Size(min = 3, max = 4000) String problemText,
                                @NotNull @Size(max = 6000) String workText,
                                @NotNull @AssertTrue Boolean problemConfirmed,
                                @NotNull Boolean workConfirmed, Boolean guidedUnderstanding) {
        public LessonRequest(String problemText, String workText, Boolean problemConfirmed, Boolean workConfirmed) {
            this(problemText, workText, problemConfirmed, workConfirmed, false);
        }
        @AssertTrue public boolean isSourceConfirmed() {
            return Boolean.TRUE.equals(problemConfirmed)
                    && (workText == null || workText.isBlank() || Boolean.TRUE.equals(workConfirmed))
                    && problemText != null && !problemText.contains("[?]")
                    && (workText == null || !workText.contains("[?]"));
        }
    }
    public record LessonAnswer(@NotBlank @Size(min = 20, max = 100) String sessionId,
                               @NotNull @Min(0) Integer revision,
                               @NotNull @Size(max = 500) String answer, @NotNull Boolean hint) {}
    public record LessonQuestion(@NotBlank @Size(min = 20, max = 100) String sessionId,
                                 @NotNull @Min(0) Integer revision, @NotNull @Min(0) @Max(9) Integer stepIndex,
                                 @NotBlank @Size(min = 2, max = 500) String question) {}
    public record LessonReply(String answer, String spokenExplanation, String followUp, boolean guarded) {}
    public record VideoRequest(@NotBlank @Size(min=20,max=100) String sessionId, @NotNull @Min(0) Integer revision) {}
    public record VideoLookup(@NotBlank @jakarta.validation.constraints.Pattern(regexp="[A-Za-z0-9_-]{24,64}") String videoId) {}
    public record VideoStatus(String videoId, String status, int progress, int durationSeconds, boolean hasAudio, String title) {}
    public record Transcript(String text) {}
    public record LessonStep(String title, String explanation, String question, java.util.List<String> choices,
                             String expression, String unit, String workExcerpt, String solutionSentence, java.util.List<String> guidance, String kind) {}
    public record CompletedStep(String title, String expression, String answer, String unit, String explanation,
                                String solutionSentence, java.util.List<String> calculationDetails, java.util.List<String> guidance, String kind) {}
    public record LessonSummary(java.util.List<String> givens, String question) {}
    public record LessonResponse(String sessionId, int revision, String topic, String goal, java.util.List<String> outline,
                                 int stepIndex, LessonStep step, java.util.List<CompletedStep> completed, String status, String feedback, String conclusion, int understandingSteps,
                                 LessonSummary summary) {
        public LessonResponse(String sessionId, int revision, String topic, String goal, java.util.List<String> outline,
                              int stepIndex, LessonStep step, java.util.List<CompletedStep> completed, String status, String feedback, String conclusion, int understandingSteps) {
            this(sessionId, revision, topic, goal, outline, stepIndex, step, completed, status, feedback, conclusion, understandingSteps, null);
        }
    }
}

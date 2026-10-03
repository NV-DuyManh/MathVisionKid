package com.mathvisionkids.api.tutoring;

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

    public record NotebookLine(String text, java.util.List<Integer> box, boolean uncertain) {}
    public record NotebookRead(String kind, String problemText, java.util.List<NotebookLine> lines, boolean needsProblem) {}
    public record CoachRequest(
            @NotNull @Size(max = 4000) String problemText,
            @NotNull @Size(max = 6000) String workText,
            @NotNull @Pattern(regexp = "UNDERSTAND|PLAN|NEXT_STEP|CHECK_WORK") String stage,
            @NotNull @Size(max = 2000) String studentAttempt,
            @NotNull @Size(max = 500) String focusText,
            @NotNull @Min(0) @Max(2) Integer hintLevel,
            @NotNull @Size(max = 1200) String previousHint) {}

    public record LessonRequest(@NotBlank @Size(min = 3, max = 4000) String problemText,
                                @NotNull @Size(max = 6000) String workText) {}
    public record LessonAnswer(@NotBlank @Size(min = 20, max = 100) String sessionId,
                               @NotNull @Min(0) Integer revision,
                               @NotNull @Size(max = 500) String answer, @NotNull Boolean hint) {}
    public record LessonStep(String title, String explanation, String question, java.util.List<String> choices,
                             String expression, String unit, String workExcerpt) {}
    public record CompletedStep(String title, String expression, String answer, String unit, String explanation) {}
    public record LessonResponse(String sessionId, int revision, String topic, String goal, java.util.List<String> outline,
                                 int stepIndex, LessonStep step, java.util.List<CompletedStep> completed, String status, String feedback) {}
}

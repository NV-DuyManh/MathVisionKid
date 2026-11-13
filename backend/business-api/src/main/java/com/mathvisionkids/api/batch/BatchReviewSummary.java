package com.mathvisionkids.api.batch;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.mathvisionkids.api.analysis.AnalysisResult;
import com.mathvisionkids.api.submission.SubmissionRepository.BatchReviewRow;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record BatchReviewSummary(UUID submissionId, String status, String studentName, int maxScore,
                                 Map<String, Number> gradeProposal, Map<String, Number> confidenceBundle,
                                 Map<String, Object> evidence) {
    static BatchReviewSummary from(BatchReviewRow row) {
        boolean visible = AnalysisResult.isVisibleForTeacher(row.getJobId(), row.getJobStatus(), row.getReviewReasons());
        return new BatchReviewSummary(row.getSubmissionId(), row.getStatus(), row.getStudentName(),
                row.getMaxScore() != null && row.getMaxScore() > 0 ? row.getMaxScore() : 10,
                visible ? numbers(row.getGradeProposal(), "suggestedScore", "maxScore") : null,
                visible ? numbers(row.getReviewReasons(), "recognition", "diagnosis") : null,
                visible ? evidencePreview(row.getEvidence()) : null);
    }

    private static Map<String, Number> numbers(Map<String, Object> source, String... keys) {
        if (source == null) return null;
        Map<String, Number> values = new LinkedHashMap<>();
        for (String key : keys) {
            if (source.get(key) instanceof Number number && Double.isFinite(number.doubleValue())) {
                values.put(key, number);
            }
        }
        return values.isEmpty() ? null : values;
    }

    private static Map<String, Object> evidencePreview(Map<String, Object> evidence) {
        if (evidence == null) return null;
        Map<String, Object> preview = new LinkedHashMap<>();
        if (evidence.get("rule") instanceof String rule) preview.put("rule", rule);
        Object position = evidence.get("position");
        if (position instanceof String || position instanceof Number) preview.put("position", position);
        if (evidence.get("items") instanceof List<?> items && !items.isEmpty()
                && items.getFirst() instanceof Map<?, ?> item && item.get("description") instanceof String description) {
            preview.put("items", List.of(Map.of("description", description)));
        }
        return preview.isEmpty() ? null : preview;
    }
}

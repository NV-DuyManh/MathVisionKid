package com.mathvisionkids.api.ocr;

import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.Instant;
import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class OcrTrialResponse {
    private UUID trialId;
    private String status;
    private String recognizedText;
    private String predictedText;
    private String verifiedTextRaw;
    private String verdict;
    private String source;
    private boolean trainingEligible;
    private String modelName;
    private String modelVersion;
    private Instant createdAt;
    private Instant feedbackAt;

    public static OcrTrialResponse fromEntity(OcrTrial trial) {
        return OcrTrialResponse.builder()
                .trialId(trial.getTrialId())
                .status("COMPLETED")
                .recognizedText(trial.getPredictedText())
                .predictedText(trial.getPredictedText())
                .verifiedTextRaw(trial.getVerifiedTextRaw())
                .verdict(trial.getVerdict())
                .source(trial.getSource())
                .trainingEligible(trial.isTrainingEligible())
                .modelName(trial.getModelName())
                .modelVersion(trial.getModelVersion())
                .createdAt(trial.getCreatedAt())
                .feedbackAt(trial.getFeedbackAt())
                .build();
    }
}

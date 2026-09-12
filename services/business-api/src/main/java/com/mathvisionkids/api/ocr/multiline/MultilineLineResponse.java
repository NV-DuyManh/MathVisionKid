package com.mathvisionkids.api.ocr.multiline;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.UUID;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MultilineLineResponse {
    private UUID lineId;
    private int lineOrder;
    private int x;
    private int y;
    private int width;
    private int height;
    private String lineImageObjectKey;
    private String lineImageSha256;
    private String predictedText;
    private String verifiedTextRaw;
    private String verifiedTextNormalized;
    private String verdict;
    private boolean trainingEligible;
    private Instant feedbackAt;

    public static MultilineLineResponse fromEntity(OcrMultilineLine entity) {
        if (entity == null) return null;
        return MultilineLineResponse.builder()
                .lineId(entity.getLineId())
                .lineOrder(entity.getLineOrder())
                .x(entity.getX())
                .y(entity.getY())
                .width(entity.getWidth())
                .height(entity.getHeight())
                .lineImageObjectKey(entity.getLineImageObjectKey())
                .lineImageSha256(entity.getLineImageSha256())
                .predictedText(entity.getPredictedText())
                .verifiedTextRaw(entity.getVerifiedTextRaw())
                .verifiedTextNormalized(entity.getVerifiedTextNormalized())
                .verdict(entity.getVerdict())
                .trainingEligible(entity.isTrainingEligible())
                .feedbackAt(entity.getFeedbackAt())
                .build();
    }
}

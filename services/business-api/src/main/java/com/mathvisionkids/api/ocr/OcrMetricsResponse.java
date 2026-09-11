package com.mathvisionkids.api.ocr;

import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class OcrMetricsResponse {
    private long totalTrials;
    private long verifiedTrials;
    private long correctCount;
    private long correctedCount;
    private long skippedCount;
    private long unverifiedCount;
    private double exactMatchRate;
    private String exactMatchPercentage;
}

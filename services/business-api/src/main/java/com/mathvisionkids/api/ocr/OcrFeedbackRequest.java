package com.mathvisionkids.api.ocr;

import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class OcrFeedbackRequest {
    private String verdict;      // "CORRECT", "CORRECTED", "SKIPPED"
    private String verifiedText; // Required when verdict is CORRECTED
}

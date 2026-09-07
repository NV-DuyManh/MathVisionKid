package com.mathvisionkids.api.analysis;

import lombok.Data;
import java.util.UUID;

@Data
public class AiCallbackRequest {
    private String status;
    private int recognizedScore;
    private String recognizedExercise;
}

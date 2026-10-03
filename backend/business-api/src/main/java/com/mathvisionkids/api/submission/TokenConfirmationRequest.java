package com.mathvisionkids.api.submission;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import java.util.UUID;

@Data
public class TokenConfirmationRequest {
    @NotNull private UUID jobId;
    @NotBlank private String tokenId;
    @NotBlank private String newClass;
}

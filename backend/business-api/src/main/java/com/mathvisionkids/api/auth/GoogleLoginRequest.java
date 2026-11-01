package com.mathvisionkids.api.auth;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter @Setter @NoArgsConstructor
public class GoogleLoginRequest {
    @NotBlank @Size(max = 8192)
    private String credential;

    @Pattern(regexp = "^(STUDENT|TEACHER)$")
    private String role;

    @Min(1) @Max(5)
    private Integer gradeLevel;
}

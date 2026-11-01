package com.mathvisionkids.api.auth;

import jakarta.validation.constraints.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter @Setter @NoArgsConstructor
public class RegisterRequest {
    @NotBlank @Email @Size(max = 255) private String email;
    @NotBlank @Size(max = 255) private String displayName;
    @NotBlank @Size(min = 8, max = 72) private String password;
    @NotBlank private String role;
    @NotBlank @Pattern(regexp = "^(MALE|FEMALE|OTHER|PREFER_NOT_TO_SAY)$") private String gender;
    @NotBlank @Pattern(regexp = "^[+0-9() .-]{7,32}$") private String phoneNumber;
    @Min(1) @Max(5) private Integer gradeLevel;
}

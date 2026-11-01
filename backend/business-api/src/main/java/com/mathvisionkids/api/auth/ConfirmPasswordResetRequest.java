package com.mathvisionkids.api.auth;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter @Setter @NoArgsConstructor
public class ConfirmPasswordResetRequest {
    @NotBlank @Email @Size(max = 255) private String email;
    @NotBlank @Pattern(regexp = "^[0-9]{6}$") private String code;
    @NotBlank @Size(min = 8, max = 72) private String newPassword;
}

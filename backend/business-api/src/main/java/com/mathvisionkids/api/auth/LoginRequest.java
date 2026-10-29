package com.mathvisionkids.api.auth;

import lombok.Data;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

@Data
public class LoginRequest {
    @NotBlank(message = "Email is required")
    @Email(message = "Valid email is required")
    private String email;

    // Exactly three aliases for the existing demo accounts. Authentication still
    // checks the stored password, active status and database role normally.
    public void setEmail(String value) {
        this.email = value == null ? null : switch (value.trim().toLowerCase(java.util.Locale.ROOT)) {
            case "student" -> "minh.student@mathvision.local";
            case "teacher" -> "lan.teacher@mathvision.local";
            case "admin" -> "admin.demo@mathvision.local";
            default -> value.trim();
        };
    }

    @NotBlank(message = "Password is required")
    private String password;
}

package com.mathvisionkids.api.auth;

import com.mathvisionkids.api.common.ApiException;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/auth")
public class SelfServiceAuthController {
    private final SelfServiceAuthService service;
    private final GoogleAuthService googleAuthService;
    private final FacebookAuthService facebookAuthService;
    public SelfServiceAuthController(SelfServiceAuthService service, GoogleAuthService googleAuthService,
                                     FacebookAuthService facebookAuthService) {
        this.service = service; this.googleAuthService = googleAuthService; this.facebookAuthService = facebookAuthService;
    }

    @PostMapping("/google")
    public ResponseEntity<AuthResponse> googleLogin(@Valid @RequestBody GoogleLoginRequest request) {
        return ResponseEntity.ok(googleAuthService.login(request));
    }

    @PostMapping("/facebook")
    public ResponseEntity<AuthResponse> facebookLogin(@Valid @RequestBody FacebookLoginRequest request) {
        return ResponseEntity.ok(facebookAuthService.login(request));
    }

    @PostMapping("/register")
    public ResponseEntity<Map<String, String>> register(@Valid @RequestBody RegisterRequest request) {
        service.register(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(Map.of("message", "Account created. Please sign in."));
    }

    @PostMapping("/password-reset/request")
    public ResponseEntity<Map<String, String>> requestReset(@Valid @RequestBody PasswordResetRequest request) {
        service.requestPasswordReset(request.getEmail());
        return ResponseEntity.accepted().body(Map.of("message", "If the account exists, a verification code was sent."));
    }

    @PostMapping("/password-reset/confirm")
    public ResponseEntity<Map<String, String>> confirmReset(@Valid @RequestBody ConfirmPasswordResetRequest request) {
        if (!service.confirmPasswordReset(request)) {
            throw new ApiException("INVALID_RESET_CODE", "Invalid or expired password reset code", HttpStatus.BAD_REQUEST);
        }
        return ResponseEntity.ok(Map.of("message", "Password updated. Please sign in with the new password."));
    }
}

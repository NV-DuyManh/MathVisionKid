package com.mathvisionkids.api.auth;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import com.mathvisionkids.api.user.UserResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.web.bind.annotation.*;

import java.security.Principal;

@RestController
@RequestMapping("/api/v1")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final JwtUtil jwtUtil;
    private final UserRepository userRepository;
    private final StudentRepository studentRepository;
    private final RefreshTokenService refreshTokenService;
    private final WebSessionService webSessions;

    public AuthController(AuthenticationManager authenticationManager, JwtUtil jwtUtil, UserRepository userRepository, StudentRepository studentRepository, RefreshTokenService refreshTokenService, WebSessionService webSessions) {
        this.webSessions = webSessions;
        this.authenticationManager = authenticationManager;
        this.jwtUtil = jwtUtil;
        this.userRepository = userRepository;
        this.studentRepository = studentRepository;
        this.refreshTokenService = refreshTokenService;
    }

    @PostMapping("/auth/login")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest request) {
        String email = request.getEmail().trim().toLowerCase(java.util.Locale.ROOT);
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(email, request.getPassword())
        );

        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("User not found"));

        return ResponseEntity.ok(refreshTokenService.createSession(user.getId()));
    }

    @GetMapping("/me")
    public ResponseEntity<UserResponse> getMe(Principal principal) {
        User user = userRepository.findByEmail(principal.getName())
                .orElseThrow(() -> new RuntimeException("User not found"));

        UserResponse response = new UserResponse();
        response.setUserId(user.getId());
        response.setEmail(user.getEmail());
        response.setRole(user.getRole());
        response.setDisplayName(user.getDisplayName());
        response.setActive(user.getActive());
        response.setCreatedAt(user.getCreatedAt());
        response.setUpdatedAt(user.getUpdatedAt());

        if ("STUDENT".equals(user.getRole())) {
            studentRepository.findById(user.getId()).ifPresent(student -> {
                response.setGradeLevel(student.getGradeLevel());
            });
        }

        return ResponseEntity.ok(response);
    }

    @PostMapping("/auth/refresh")
    public ResponseEntity<AuthResponse> refreshtoken(@Valid @RequestBody TokenRefreshRequest request) {
        return ResponseEntity.ok(refreshTokenService.rotate(request.getRefreshToken()));
    }

    @PostMapping("/auth/logout")
    public ResponseEntity<Void> logoutUser(Principal principal, jakarta.servlet.http.HttpServletRequest request,
                                          @RequestBody(required = false) TokenRefreshRequest credentials) {
        var client = WebSessionService.client(request);
        if (client != null) {
            if (principal == null) throw new ApiException("UNAUTHORIZED", "Authentication required", HttpStatus.UNAUTHORIZED);
            webSessions.logout(principal.getName(), request, client);
            return ResponseEntity.ok().build();
        }
        String bearer = request.getHeader("Authorization");
        var nativeSession = principal != null && bearer != null && bearer.startsWith("Bearer ")
                ? jwtUtil.nativeSession(bearer.substring(7)) : null;
        if (!refreshTokenService.revokeForLogout(credentials == null ? null : credentials.getRefreshToken(),
                principal == null ? null : principal.getName(), nativeSession)) {
            throw new ApiException("UNAUTHORIZED", "Authentication required", HttpStatus.UNAUTHORIZED);
        }
        return ResponseEntity.ok().build();
    }
}

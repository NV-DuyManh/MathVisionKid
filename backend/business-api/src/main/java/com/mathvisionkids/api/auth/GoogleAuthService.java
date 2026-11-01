package com.mathvisionkids.api.auth;

import com.google.api.client.googleapis.auth.oauth2.GoogleIdToken;
import com.google.api.client.googleapis.auth.oauth2.GoogleIdTokenVerifier;
import com.google.api.client.http.javanet.NetHttpTransport;
import com.google.api.client.json.gson.GsonFactory;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.io.IOException;
import java.security.GeneralSecurityException;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

@Service
public class GoogleAuthService {
    private final UserRepository users;
    private final StudentRepository students;
    private final TeacherRepository teachers;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;
    private final RefreshTokenService refreshTokens;
    private final String clientIds;
    private final boolean enabled;
    private GoogleIdTokenVerifier verifier;

    public GoogleAuthService(UserRepository users, StudentRepository students, TeacherRepository teachers,
                             PasswordEncoder passwordEncoder, JwtUtil jwtUtil, RefreshTokenService refreshTokens,
                             @Value("${app.auth.google.enabled:false}") boolean enabled,
                             @Value("${app.auth.google.client-id:}") String clientIds) {
        this.users = users; this.students = students; this.teachers = teachers;
        this.passwordEncoder = passwordEncoder; this.jwtUtil = jwtUtil; this.refreshTokens = refreshTokens;
        this.enabled = enabled; this.clientIds = clientIds;
    }

    @jakarta.annotation.PostConstruct
    void initializeVerifier() {
        if (!enabled) return;
        List<String> audiences = java.util.Arrays.stream(clientIds.split(","))
                .map(String::trim).filter(value -> !value.isEmpty()).distinct().toList();
        if (audiences.isEmpty()) throw new IllegalStateException("Google login is enabled but GOOGLE_CLIENT_ID is missing.");
        verifier = new GoogleIdTokenVerifier.Builder(new NetHttpTransport(), GsonFactory.getDefaultInstance())
                .setAudience(audiences).build();
    }

    @Transactional
    public AuthResponse login(GoogleLoginRequest request) {
        if (!enabled || verifier == null) {
            throw new ApiException("GOOGLE_LOGIN_NOT_CONFIGURED", "Google login is not configured", HttpStatus.SERVICE_UNAVAILABLE);
        }
        GoogleIdToken token;
        try {
            token = verifier.verify(request.getCredential());
        } catch (GeneralSecurityException | IOException | IllegalArgumentException exception) {
            throw new ApiException("INVALID_GOOGLE_CREDENTIAL", "Google credential could not be verified", HttpStatus.UNAUTHORIZED);
        }
        if (token == null) throw new ApiException("INVALID_GOOGLE_CREDENTIAL", "Google credential could not be verified", HttpStatus.UNAUTHORIZED);

        GoogleIdToken.Payload payload = token.getPayload();
        String email = payload.getEmail();
        String subject = payload.getSubject();
        boolean trustedEmailDomain = email != null && (email.toLowerCase(Locale.ROOT).endsWith("@gmail.com")
                || payload.getHostedDomain() != null);
        if (!Boolean.TRUE.equals(payload.getEmailVerified()) || !trustedEmailDomain || subject == null || subject.isBlank()) {
            throw new ApiException("UNVERIFIED_GOOGLE_EMAIL", "A verified Google email is required", HttpStatus.UNAUTHORIZED);
        }

        String normalizedEmail = email.trim().toLowerCase(Locale.ROOT);
        User user = users.findByGoogleSubject(subject).orElse(null);
        if (user == null) {
            user = users.findByEmail(normalizedEmail).orElse(null);
            if (user != null) {
                if (user.getGoogleSubject() != null && !user.getGoogleSubject().equals(subject)) {
                    throw new ApiException("GOOGLE_ACCOUNT_CONFLICT", "This email is linked to a different Google account", HttpStatus.CONFLICT);
                }
                user.setGoogleSubject(subject);
                user = users.save(user);
            } else {
                user = createAccount(payload, normalizedEmail, subject, request);
            }
        } else if (!user.getEmail().equalsIgnoreCase(normalizedEmail)) {
            if (users.existsByEmail(normalizedEmail)) {
                throw new ApiException("GOOGLE_ACCOUNT_CONFLICT", "The Google account email belongs to another user", HttpStatus.CONFLICT);
            }
            user.setEmail(normalizedEmail);
            user = users.save(user);
        }
        if (!Boolean.TRUE.equals(user.getActive())) {
            throw new ApiException("ACCOUNT_INACTIVE", "Account is disabled", HttpStatus.FORBIDDEN);
        }
        return new AuthResponse(jwtUtil.generateToken(user.getEmail(), user.getRole()), refreshTokens.createRefreshToken(user.getId()));
    }

    private User createAccount(GoogleIdToken.Payload payload, String email, String subject, GoogleLoginRequest request) {
        String role = request.getRole() == null ? "STUDENT" : request.getRole().toUpperCase(Locale.ROOT);
        if (role.equals("STUDENT") && request.getGradeLevel() == null) {
            throw new ApiException("GOOGLE_STUDENT_GRADE_REQUIRED", "Choose a grade before creating a student account", HttpStatus.PRECONDITION_REQUIRED);
        }

        User user = role.equals("TEACHER") ? new Teacher() : new Student();
        user.setEmail(email);
        user.setGoogleSubject(subject);
        Object displayName = payload.get("name");
        String name = displayName instanceof String value && !value.isBlank()
                ? value.trim() : email.substring(0, email.indexOf('@'));
        user.setDisplayName(name);
        user.setPasswordHash(passwordEncoder.encode(UUID.randomUUID().toString()));
        user.setRole(role);
        user.setGender(googleGender(payload.get("gender")));
        user.setActive(true);
        if (user instanceof Student student) student.setGradeLevel(request.getGradeLevel());
        return user instanceof Student student ? students.save(student) : teachers.save((Teacher) user);
    }

    private String googleGender(Object claim) {
        if (!(claim instanceof String value)) return "PREFER_NOT_TO_SAY";
        return switch (value.toLowerCase(Locale.ROOT)) {
            case "male" -> "MALE";
            case "female" -> "FEMALE";
            case "other" -> "OTHER";
            default -> "PREFER_NOT_TO_SAY";
        };
    }
}

package com.mathvisionkids.api.auth;

import com.google.auth.oauth2.GoogleCredentials;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseAuthException;
import com.google.firebase.auth.FirebaseToken;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

@Service
public class FacebookAuthService {
    private final UserRepository users;
    private final StudentRepository students;
    private final TeacherRepository teachers;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;
    private final RefreshTokenService refreshTokens;
    private final boolean enabled;
    private final String projectId;
    private FirebaseAuth firebaseAuth;

    public FacebookAuthService(UserRepository users, StudentRepository students, TeacherRepository teachers,
                               PasswordEncoder passwordEncoder, JwtUtil jwtUtil, RefreshTokenService refreshTokens,
                               @Value("${app.auth.facebook.enabled:false}") boolean enabled,
                               @Value("${app.auth.facebook.firebase-project-id:}") String projectId) {
        this.users = users; this.students = students; this.teachers = teachers;
        this.passwordEncoder = passwordEncoder; this.jwtUtil = jwtUtil; this.refreshTokens = refreshTokens;
        this.enabled = enabled; this.projectId = projectId;
    }

    @PostConstruct
    void initializeVerifier() {
        if (!enabled) return;
        if (projectId.isBlank()) throw new IllegalStateException("Facebook login requires FIREBASE_PROJECT_ID.");
        try {
            FirebaseOptions options = FirebaseOptions.builder()
                    .setCredentials(GoogleCredentials.getApplicationDefault())
                    .setProjectId(projectId).build();
            FirebaseApp app = FirebaseApp.initializeApp(options, "mathvision-facebook-auth");
            firebaseAuth = FirebaseAuth.getInstance(app);
        } catch (IOException exception) {
            throw new IllegalStateException("Facebook login requires GOOGLE_APPLICATION_CREDENTIALS.", exception);
        }
    }

    @Transactional
    public AuthResponse login(FacebookLoginRequest request) {
        if (!enabled || firebaseAuth == null) {
            throw new ApiException("FACEBOOK_LOGIN_NOT_CONFIGURED", "Facebook login is not configured", HttpStatus.SERVICE_UNAVAILABLE);
        }
        FirebaseToken token;
        try {
            token = firebaseAuth.verifyIdToken(request.getCredential(), true);
        } catch (FirebaseAuthException | IllegalArgumentException exception) {
            throw new ApiException("INVALID_FACEBOOK_CREDENTIAL", "Facebook credential could not be verified", HttpStatus.UNAUTHORIZED);
        }
        Object firebaseClaim = token.getClaims().get("firebase");
        if (!(firebaseClaim instanceof Map<?, ?> provider) || !"facebook.com".equals(provider.get("sign_in_provider"))) {
            throw new ApiException("INVALID_FACEBOOK_CREDENTIAL", "A Facebook sign-in is required", HttpStatus.UNAUTHORIZED);
        }
        String email = token.getEmail();
        String subject = token.getUid();
        if (subject == null || subject.isBlank()) {
            throw new ApiException("INVALID_FACEBOOK_CREDENTIAL", "Facebook credential could not be verified", HttpStatus.UNAUTHORIZED);
        }
        User user = users.findByFacebookSubject(subject).orElse(null);
        if (user == null && (email == null || email.isBlank())) {
            throw new ApiException("FACEBOOK_EMAIL_REQUIRED", "A Facebook account with an email is required", HttpStatus.UNPROCESSABLE_ENTITY);
        }
        if (user == null) {
            String normalizedEmail = email.trim().toLowerCase(Locale.ROOT);
            user = users.findByEmail(normalizedEmail).orElse(null);
            if (user != null) {
                // An email match alone cannot prove ownership of an existing MathVision account.
                throw new ApiException("FACEBOOK_ACCOUNT_LINK_REQUIRED", "Sign in with the existing method before linking Facebook", HttpStatus.CONFLICT);
            }
            user = createAccount(token, normalizedEmail, subject, request);
        } else if (email != null && !user.getEmail().equalsIgnoreCase(email.trim())) {
            // Facebook email changes are not independently verified by this application.
            throw new ApiException("FACEBOOK_EMAIL_CHANGED", "Facebook email changed; contact support", HttpStatus.CONFLICT);
        }
        if (!Boolean.TRUE.equals(user.getActive())) {
            throw new ApiException("ACCOUNT_INACTIVE", "Account is disabled", HttpStatus.FORBIDDEN);
        }
        return new AuthResponse(jwtUtil.generateToken(user.getEmail(), user.getRole()), refreshTokens.createRefreshToken(user.getId()));
    }

    private User createAccount(FirebaseToken token, String email, String subject, FacebookLoginRequest request) {
        String role = request.getRole() == null ? "STUDENT" : request.getRole().toUpperCase(Locale.ROOT);
        if (role.equals("STUDENT") && request.getGradeLevel() == null) {
            throw new ApiException("FACEBOOK_STUDENT_GRADE_REQUIRED", "Choose a grade before creating a student account", HttpStatus.PRECONDITION_REQUIRED);
        }
        User user = role.equals("TEACHER") ? new Teacher() : new Student();
        user.setEmail(email);
        user.setFacebookSubject(subject);
        String name = token.getName();
        user.setDisplayName(name != null && !name.isBlank() ? name.trim() : email.substring(0, email.indexOf('@')));
        user.setPasswordHash(passwordEncoder.encode(UUID.randomUUID().toString()));
        user.setRole(role);
        user.setGender("PREFER_NOT_TO_SAY");
        user.setActive(true);
        if (user instanceof Student student) student.setGradeLevel(request.getGradeLevel());
        return user instanceof Student student ? students.save(student) : teachers.save((Teacher) user);
    }
}

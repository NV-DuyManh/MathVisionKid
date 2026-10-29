package com.mathvisionkids.api.auth;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.MailException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import jakarta.annotation.PostConstruct;
import java.security.SecureRandom;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Locale;
import java.util.UUID;

@Service
public class SelfServiceAuthService {
    private static final SecureRandom RANDOM = new SecureRandom();
    private final UserRepository users;
    private final StudentRepository students;
    private final TeacherRepository teachers;
    private final PasswordResetCodeRepository codes;
    private final PasswordEncoder encoder;
    private final RefreshTokenService refreshTokens;
    private final JavaMailSender mailSender;
    private final boolean emailEnabled;
    private final String fromAddress;
    private final String smtpHost;
    private final String smtpUsername;
    private final String smtpPassword;
    private final int smtpPort;
    private final boolean smtpAuth;
    private final boolean smtpStartTls;

    public SelfServiceAuthService(UserRepository users, StudentRepository students, TeacherRepository teachers,
                                  PasswordResetCodeRepository codes, PasswordEncoder encoder, RefreshTokenService refreshTokens, JavaMailSender mailSender,
                                  @Value("${app.auth.email.enabled:false}") boolean emailEnabled,
                                  @Value("${app.auth.email.from:}") String fromAddress,
                                  @Value("${spring.mail.host:}") String smtpHost,
                                  @Value("${spring.mail.port:0}") int smtpPort,
                                  @Value("${spring.mail.username:}") String smtpUsername,
                                  @Value("${spring.mail.password:}") String smtpPassword,
                                  @Value("${spring.mail.properties.mail.smtp.auth:false}") boolean smtpAuth,
                                  @Value("${spring.mail.properties.mail.smtp.starttls.enable:false}") boolean smtpStartTls) {
        this.users = users; this.students = students; this.teachers = teachers; this.codes = codes;
        this.encoder = encoder; this.refreshTokens = refreshTokens; this.mailSender = mailSender; this.emailEnabled = emailEnabled; this.fromAddress = fromAddress;
        this.smtpHost = smtpHost; this.smtpPort = smtpPort; this.smtpUsername = smtpUsername;
        this.smtpPassword = smtpPassword; this.smtpAuth = smtpAuth; this.smtpStartTls = smtpStartTls;
    }

    @PostConstruct
    void validateEmailConfiguration() {
        if (emailEnabled && (smtpHost.isBlank() || smtpPort < 1 || smtpPort > 65535 || smtpUsername.isBlank()
                || smtpPassword.isBlank() || fromAddress.isBlank() || !smtpAuth || !smtpStartTls)) {
            throw new IllegalStateException("Email password recovery is enabled but SMTP is incomplete. Configure MAIL_HOST, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, AUTH_EMAIL_FROM and enable SMTP auth/TLS.");
        }
    }

    @Transactional
    public void register(RegisterRequest request) {
        String email = request.getEmail().trim().toLowerCase(Locale.ROOT);
        String role = request.getRole().trim().toUpperCase(Locale.ROOT);
        if (!role.equals("STUDENT") && !role.equals("TEACHER")) {
            throw new ApiException("VALIDATION_ERROR", "Role must be STUDENT or TEACHER", HttpStatus.BAD_REQUEST);
        }
        if (users.existsByEmail(email)) throw new ApiException("CONFLICT", "Email is already registered", HttpStatus.CONFLICT);
        if (role.equals("STUDENT") && request.getGradeLevel() == null) {
            throw new ApiException("VALIDATION_ERROR", "gradeLevel is required for students", HttpStatus.BAD_REQUEST);
        }
        if (role.equals("TEACHER") && request.getGradeLevel() != null) {
            throw new ApiException("VALIDATION_ERROR", "gradeLevel is only valid for students", HttpStatus.BAD_REQUEST);
        }

        User user = role.equals("STUDENT") ? new Student() : new Teacher();
        user.setEmail(email);
        user.setDisplayName(request.getDisplayName().trim());
        user.setPasswordHash(encoder.encode(request.getPassword()));
        user.setRole(role);
        user.setGender(request.getGender());
        user.setPhoneNumber(request.getPhoneNumber() == null || request.getPhoneNumber().isBlank() ? null : request.getPhoneNumber().trim());
        user.setActive(true);
        if (user instanceof Student student) student.setGradeLevel(request.getGradeLevel());
        if (user instanceof Student student) students.save(student); else teachers.save((Teacher) user);
    }

    @Transactional
    public void requestPasswordReset(String rawEmail) {
        if (!emailEnabled) throw new ApiException("EMAIL_NOT_CONFIGURED", "Password recovery email is not configured", HttpStatus.SERVICE_UNAVAILABLE);
        String email = rawEmail.trim().toLowerCase(Locale.ROOT);
        User user = users.findByEmail(email).orElse(null);
        if (user == null || !Boolean.TRUE.equals(user.getActive())) return;

        Instant now = Instant.now();
        var latest = codes.findTopByUser_IdAndConsumedFalseOrderByCreatedAtDesc(user.getId());
        if (latest.isPresent() && latest.get().getCreatedAt().isAfter(now.minus(60, ChronoUnit.SECONDS))) return;
        if (codes.countByUser_IdAndCreatedAtAfter(user.getId(), now.minus(1, ChronoUnit.HOURS)) >= 3) return;

        String code = String.format("%06d", RANDOM.nextInt(1_000_000));
        PasswordResetCode reset = new PasswordResetCode();
        reset.setUser(user);
        reset.setCodeHash(encoder.encode(code));
        reset.setExpiresAt(now.plus(10, ChronoUnit.MINUTES));
        codes.save(reset);

        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(fromAddress);
        message.setTo(email);
        message.setSubject("Mã xác nhận đặt lại mật khẩu MathVision Kids");
        message.setText("Mã xác nhận của bạn là " + code + ". Mã có hiệu lực trong 10 phút. Nếu bạn không yêu cầu, hãy bỏ qua email này.");
        try {
            mailSender.send(message);
        } catch (MailException exception) {
            throw new ApiException("EMAIL_DELIVERY_FAILED", "The password reset email could not be delivered", HttpStatus.SERVICE_UNAVAILABLE);
        }
    }

    @Transactional
    public boolean confirmPasswordReset(ConfirmPasswordResetRequest request) {
        User user = users.findByEmail(request.getEmail().trim().toLowerCase(Locale.ROOT)).orElse(null);
        if (user == null) return false;
        PasswordResetCode reset = codes.findTopByUser_IdAndConsumedFalseOrderByCreatedAtDesc(user.getId())
                .orElse(null);
        if (reset == null || reset.isConsumed() || reset.getExpiresAt().isBefore(Instant.now()) || reset.getAttempts() >= 5) return false;
        if (!encoder.matches(request.getCode(), reset.getCodeHash())) {
            reset.setAttempts(reset.getAttempts() + 1);
            return false;
        }
        reset.setConsumed(true);
        user.setPasswordHash(encoder.encode(request.getNewPassword()));
        users.save(user);
        refreshTokens.deleteByUserId(user.getId());
        return true;
    }
}

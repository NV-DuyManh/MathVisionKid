package com.mathvisionkids.api.studentprofile;

import com.mathvisionkids.api.common.ApiException;
import jakarta.mail.MessagingException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mail.MailException;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.sql.Timestamp;
import java.time.Duration;
import java.time.Instant;
import java.util.Locale;
import java.util.UUID;

@Service
public class ParentPinRecoveryService {
    private static final SecureRandom RANDOM = new SecureRandom();
    private static final Duration LIFETIME = Duration.ofMinutes(10);
    private static final Duration COOLDOWN = Duration.ofMinutes(1);
    private static final Duration SEND_WINDOW = Duration.ofHours(1);
    private static final int SEND_LIMIT = 3;
    private static final int ATTEMPT_LIMIT = 5;
    private final JdbcTemplate db;
    private final StudentProfileService profiles;
    private final PasswordEncoder passwords;
    private final JavaMailSender mail;
    private final boolean emailEnabled;
    private final String from;

    ParentPinRecoveryService(JdbcTemplate db, StudentProfileService profiles, PasswordEncoder passwords,
            JavaMailSender mail, @Value("${app.auth.email.enabled:false}") boolean emailEnabled,
            @Value("${app.auth.email.from:}") String from) {
        this.db = db;
        this.profiles = profiles;
        this.passwords = passwords;
        this.mail = mail;
        this.emailEnabled = emailEnabled;
        this.from = from;
    }

    @Transactional(noRollbackFor = ApiException.class)
    public Destination request(String principal, Purpose purpose) {
        if (!emailEnabled) {
            throw error("EMAIL_NOT_CONFIGURED", "Chưa thể gửi email xác nhận. Vui lòng thử lại sau.", HttpStatus.SERVICE_UNAVAILABLE);
        }
        var student = profiles.student(principal);
        var id = student.getId();
        profiles.lockStudent(id);
        checkPurpose(id, purpose);
        var now = Instant.now();
        var previous = find(id);
        boolean newWindow = previous == null || !previous.windowStarted().plus(SEND_WINDOW).isAfter(now);
        if (previous != null && (previous.issuedAt().plus(COOLDOWN).isAfter(now)
                || (!newWindow && previous.sends() >= SEND_LIMIT))) {
            throw error("PARENT_PIN_CODE_RATE_LIMIT", "Bạn đã yêu cầu mã gần đây. Vui lòng chờ rồi thử lại.", HttpStatus.TOO_MANY_REQUESTS);
        }
        var code = String.format(Locale.ROOT, "%06d", RANDOM.nextInt(1_000_000));
        var hash = passwords.encode(code);
        var issued = Timestamp.from(now);
        var window = newWindow ? issued : Timestamp.from(previous.windowStarted());
        int sends = newWindow ? 1 : previous.sends() + 1;
        if (previous == null) {
            db.update("""
                    INSERT INTO student_parent_pin_challenge
                        (student_id, purpose, code_hash, issued_at, window_started_at, sends)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, id, purpose.name(), hash, issued, window, sends);
        } else {
            db.update("""
                    UPDATE student_parent_pin_challenge
                    SET purpose = ?, code_hash = ?, issued_at = ?, window_started_at = ?, sends = ?, attempts = 0
                    WHERE student_id = ?
                    """, purpose.name(), hash, issued, window, sends, id);
        }

        try {
            sendCode(student.getEmail(), purpose, code);
        } catch (MailException | MessagingException failure) {
            consume(id);
            org.slf4j.LoggerFactory.getLogger(ParentPinRecoveryService.class).warn("Parent PIN code delivery failed.");
            throw error("PARENT_PIN_EMAIL_UNAVAILABLE", "Chưa gửi được mã xác nhận. Vui lòng thử lại sau.", HttpStatus.SERVICE_UNAVAILABLE);
        }
        return new Destination(mask(student.getEmail()));
    }

    private void sendCode(String recipient, Purpose purpose, String code) throws MessagingException {
        String title = purpose == Purpose.SETUP ? "Thiết lập mã PIN" : "Đặt lại mã PIN";
        String instruction = "Nhập mã bên dưới vào Góc phụ huynh để "
                + (purpose == Purpose.SETUP ? "thiết lập" : "đặt lại") + " mã PIN.";
        String expiry = "Mã có hiệu lực trong " + LIFETIME.toMinutes() + " phút.";
        String footer = "Nếu bạn không yêu cầu mã, hãy bỏ qua email này.";

        var message = mail.createMimeMessage();
        var helper = new MimeMessageHelper(message, MimeMessageHelper.MULTIPART_MODE_MIXED, StandardCharsets.UTF_8.name());
        helper.setFrom(from);
        helper.setTo(recipient);
        helper.setSubject(title + " · Góc phụ huynh MathVision Kids");
        helper.setText(String.join("\n\n", title, instruction, code, expiry, "Không chia sẻ mã này.", footer), """
                <!doctype html>
                <html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
                <body style="margin:0;padding:0;background:#f3efff;color:#24184b;font-family:Arial,sans-serif">
                  <table role="presentation" width="100%%" cellspacing="0" cellpadding="0" bgcolor="#f3efff">
                    <tr><td align="center" style="padding:24px 12px">
                      <table role="presentation" width="100%%" cellspacing="0" cellpadding="0"
                             style="max-width:520px;background:#ffffff;border:1px solid #e5dbfa;border-radius:20px">
                        <tr><td bgcolor="#29165c" style="padding:22px 24px;border-radius:19px 19px 0 0;color:#ffffff">
                          <div style="font-size:20px;font-weight:bold;line-height:1.4">MathVision <span style="color:#ffda78">Kids</span></div>
                          <div style="margin-top:4px;color:#e5d9ff;font-size:13px;line-height:1.5">Góc phụ huynh</div>
                        </td></tr>
                        <tr><td style="padding:24px">
                          <h1 style="margin:0 0 10px;font-size:25px;line-height:1.25;color:#24184b">%s</h1>
                          <p style="margin:0 0 20px;color:#514567;font-size:16px;line-height:1.55">%s</p>
                          <table role="presentation" width="100%%" cellspacing="0" cellpadding="0">
                            <tr><td align="center" bgcolor="#f1eaff" style="padding:16px 8px;border:1px solid #d9c8fa;border-radius:14px">
                              <div style="color:#503788;font-size:13px;font-weight:bold;line-height:1.5">Mã xác nhận</div>
                              <div style="margin-top:4px;color:#5129ad;font-family:Consolas,monospace;font-size:34px;font-weight:bold;line-height:1.25;letter-spacing:4px;white-space:nowrap">%s</div>
                            </td></tr>
                          </table>
                          <p style="margin:16px 0 0;color:#514567;font-size:14px;line-height:1.55"><strong>%s</strong> Không chia sẻ mã này.</p>
                        </td></tr>
                        <tr><td style="padding:16px 24px;border-top:1px solid #ede5fa;color:#514567;font-size:13px;line-height:1.55">%s</td></tr>
                      </table>
                    </td></tr>
                  </table>
                </body></html>
                """.formatted(title, instruction, code, expiry, footer));
        mail.send(message);
    }

    @Transactional(noRollbackFor = ApiException.class)
    public void confirm(String principal, Purpose purpose, String code, String pin) {
        var id = profiles.student(principal).getId();
        profiles.lockStudent(id);
        checkPurpose(id, purpose);
        var challenge = find(id);
        if (challenge == null || challenge.purpose() != purpose || challenge.hash() == null
                || !challenge.issuedAt().plus(LIFETIME).isAfter(Instant.now())) {
            throw invalid();
        }
        if (challenge.attempts() >= ATTEMPT_LIMIT) {
            throw error("PARENT_PIN_CODE_ATTEMPTS", "Bạn đã nhập sai nhiều lần. Vui lòng yêu cầu mã mới.", HttpStatus.TOO_MANY_REQUESTS);
        }
        if (!passwords.matches(code, challenge.hash())) {
            db.update("UPDATE student_parent_pin_challenge SET attempts = attempts + 1 WHERE student_id = ?", id);
            throw invalid();
        }
        var pinHash = passwords.encode(pin);
        if (purpose == Purpose.SETUP) {
            db.update("INSERT INTO student_parent_control (student_id, pin_hash) VALUES (?, ?)", id, pinHash);
        } else {
            db.update("""
                    UPDATE student_parent_control
                    SET pin_hash = ?, failed_attempts = 0, locked_until = NULL, pin_revision = pin_revision + 1
                    WHERE student_id = ?
                    """, pinHash, id);
        }
        consume(id);
    }

    private void checkPurpose(UUID student, Purpose purpose) {
        int configured = db.queryForObject("SELECT COUNT(*) FROM student_parent_control WHERE student_id = ?", Integer.class, student);
        if ((configured > 0) != (purpose == Purpose.RESET)) {
            throw error("PARENT_PIN_STATE_CHANGED", "Trạng thái mã PIN đã thay đổi. Vui lòng mở lại Góc phụ huynh.", HttpStatus.CONFLICT);
        }
    }

    private Challenge find(UUID student) {
        return db.query("""
                SELECT purpose, code_hash, issued_at, window_started_at, sends, attempts
                FROM student_parent_pin_challenge WHERE student_id = ?
                """, (row, index) -> new Challenge(Purpose.valueOf(row.getString(1)), row.getString(2),
                row.getTimestamp(3).toInstant(), row.getTimestamp(4).toInstant(), row.getInt(5), row.getInt(6)),
                student).stream().findFirst().orElse(null);
    }

    private void consume(UUID student) {
        db.update("UPDATE student_parent_pin_challenge SET code_hash = NULL WHERE student_id = ?", student);
    }

    private static String mask(String email) {
        int at = email.lastIndexOf('@');
        return at > 0 ? email.substring(0, Math.min(2, at)) + "***" + email.substring(at) : "***";
    }

    private static ApiException invalid() {
        return error("PARENT_PIN_CODE_INVALID", "Mã xác nhận chưa đúng hoặc đã hết hạn.", HttpStatus.FORBIDDEN);
    }

    private static ApiException error(String code, String message, HttpStatus status) {
        return new ApiException(code, message, status);
    }

    public enum Purpose { SETUP, RESET }
    public record Destination(String maskedEmail) {}
    private record Challenge(Purpose purpose, String hash, Instant issuedAt, Instant windowStarted, int sends, int attempts) {}
}

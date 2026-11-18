package com.mathvisionkids.api.studentprofile;

import com.mathvisionkids.api.common.ApiException;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

@Service
public class ParentControlService {
    private static final int MAX_ATTEMPTS = 5;
    private static final int LOCK_SECONDS = 300;
    private final JdbcTemplate db;
    private final StudentProfileService profiles;
    private final PasswordEncoder passwords;

    ParentControlService(JdbcTemplate db, StudentProfileService profiles, PasswordEncoder passwords) {
        this.db = db;
        this.profiles = profiles;
        this.passwords = passwords;
    }

    @Transactional(readOnly = true)
    public Status status(String principal) {
        var today = LocalDate.now(StudentRewards.ZONE);
        return db.query("""
                SELECT c.daily_minutes, COALESCE(d.elapsed_millis, 0)
                FROM student_parent_control c
                JOIN users u ON u.id = c.student_id
                LEFT JOIN student_usage_day d ON d.student_id = c.student_id AND d.usage_day = ?
                WHERE u.email = ?
                """, (row, index) -> {
            var minutes = row.getObject(1, Integer.class);
            return new Status(true, minutes != null && row.getLong(2) >= minutes * 60_000L);
        }, today, principal).stream().findFirst().orElse(new Status(false, false));
    }

    @Transactional
    public Settings setup(String principal, String pin) {
        var student = lockedStudent(principal);
        if (find(student) != null) {
            throw new ApiException("PARENT_PIN_EXISTS", "Mã PIN đã được thiết lập.", HttpStatus.CONFLICT);
        }
        db.update("INSERT INTO student_parent_control (student_id, pin_hash) VALUES (?, ?)", student, passwords.encode(pin));
        return new Settings(null);
    }

    // Failed attempts must persist even when the controller returns an error.
    @Transactional(noRollbackFor = ApiException.class)
    public Settings unlock(String principal, String pin) {
        return new Settings(verify(lockedStudent(principal), pin).dailyMinutes());
    }

    @Transactional(noRollbackFor = ApiException.class)
    public Settings saveDailyLimit(String principal, String pin, Integer minutes) {
        var student = lockedStudent(principal);
        verify(student, pin);
        db.update("UPDATE student_parent_control SET daily_minutes = ? WHERE student_id = ?", minutes, student);
        return new Settings(minutes);
    }

    private UUID lockedStudent(String principal) {
        var student = profiles.student(principal).getId();
        profiles.lockStudent(student);
        return student;
    }

    private Control verify(UUID student, String pin) {
        var control = find(student);
        if (control == null) {
            throw new ApiException("PARENT_PIN_REQUIRED", "Chưa thiết lập mã PIN.", HttpStatus.CONFLICT);
        }
        var now = Instant.now();
        if (control.lockedUntil() != null && control.lockedUntil().isAfter(now)) throw locked();
        if (!passwords.matches(pin, control.hash())) {
            int attempts = control.lockedUntil() == null ? control.failedAttempts() + 1 : 1;
            if (attempts >= MAX_ATTEMPTS) {
                db.update("UPDATE student_parent_control SET failed_attempts = 0, locked_until = ? WHERE student_id = ?",
                        Timestamp.from(now.plusSeconds(LOCK_SECONDS)), student);
                throw locked();
            }
            db.update("UPDATE student_parent_control SET failed_attempts = ?, locked_until = NULL WHERE student_id = ?",
                    attempts, student);
            throw new ApiException("PARENT_PIN_INVALID", "Mã PIN chưa đúng. Vui lòng thử lại.", HttpStatus.FORBIDDEN);
        }
        if (control.failedAttempts() > 0 || control.lockedUntil() != null) {
            db.update("UPDATE student_parent_control SET failed_attempts = 0, locked_until = NULL WHERE student_id = ?", student);
        }
        return control;
    }

    private ApiException locked() {
        return new ApiException("PARENT_PIN_LOCKED", "Đã nhập sai nhiều lần. Vui lòng thử lại sau 5 phút.", HttpStatus.TOO_MANY_REQUESTS);
    }

    private Control find(UUID student) {
        return db.query("""
                SELECT pin_hash, daily_minutes, failed_attempts, locked_until FROM student_parent_control WHERE student_id = ?
                """, (row, index) -> {
            var lock = row.getTimestamp(4);
            return new Control(row.getString(1), row.getObject(2, Integer.class), row.getInt(3), lock == null ? null : lock.toInstant());
        }, student).stream().findFirst().orElse(null);
    }

    public record Status(boolean pinConfigured, boolean dailyLimitReached) {}
    public record Settings(Integer dailyMinutes) {}
    private record Control(String hash, Integer dailyMinutes, int failedAttempts, Instant lockedUntil) {}
}

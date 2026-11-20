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
    private final StudentUsageService usage;

    ParentControlService(JdbcTemplate db, StudentProfileService profiles, PasswordEncoder passwords, StudentUsageService usage) {
        this.db = db;
        this.profiles = profiles;
        this.passwords = passwords;
        this.usage = usage;
    }

    @Transactional
    public Status status(String principal) {
        var now = Instant.now();
        // Preserve the unconfigured response without requiring a student profile.
        // Only a configured control can have a limit that needs accounting.
        var configured = db.queryForObject("""
                SELECT EXISTS(SELECT 1 FROM student_parent_control c
                    JOIN users u ON u.id = c.student_id WHERE u.email = ?)
                """, Boolean.class, principal);
        if (!Boolean.TRUE.equals(configured)) return new Status(false, false, false, true);
        var student = lockedStudent(principal);
        usage.expireConnectionsLocked(student, now);
        var today = LocalDate.ofInstant(now, StudentRewards.ZONE);
        return db.query("""
                SELECT c.daily_minutes, COALESCE(d.elapsed_millis, 0),
                    EXISTS(SELECT 1 FROM student_usage_connection a
                        WHERE a.student_id = c.student_id AND a.last_seen_at >= ?)
                FROM student_parent_control c
                JOIN users u ON u.id = c.student_id
                LEFT JOIN student_usage_day d ON d.student_id = c.student_id AND d.usage_day = ?
                WHERE u.email = ?
                """, (row, index) -> {
            var minutes = row.getObject(1, Integer.class);
            return new Status(true, minutes != null && row.getLong(2) >= minutes * 60_000L,
                    minutes != null, minutes == null || row.getBoolean(3));
        }, Timestamp.from(now.minus(StudentUsageService.MAX_HEARTBEAT_GAP)), today, principal)
                .stream().findFirst().orElse(new Status(false, false, false, true));
    }

    @Transactional
    public Settings setup(String principal, String pin) {
        var student = lockedStudent(principal);
        if (find(student) != null) {
            throw new ApiException("PARENT_PIN_EXISTS", "Mã PIN đã được thiết lập.", HttpStatus.CONFLICT);
        }
        db.update("INSERT INTO student_parent_control (student_id, pin_hash) VALUES (?, ?)", student, passwords.encode(pin));
        return new Settings(null, null);
    }

    // Failed attempts must persist even when the controller returns an error.
    @Transactional(noRollbackFor = ApiException.class)
    public Settings unlock(String principal, String pin) {
        var control = verify(lockedStudent(principal), pin);
        return new Settings(control.dailyMinutes(), control.gameMinutes());
    }

    @Transactional(noRollbackFor = ApiException.class)
    public Settings saveDailyLimit(String principal, String pin, Integer minutes) {
        var student = lockedStudent(principal);
        var control = verify(student, pin);
        db.update("UPDATE student_parent_control SET daily_minutes = ? WHERE student_id = ?", minutes, student);
        return new Settings(minutes, control.gameMinutes());
    }

    @Transactional(noRollbackFor = ApiException.class)
    public Settings saveGameLimit(String principal, String pin, Integer minutes) {
        var student = lockedStudent(principal);
        var control = verify(student, pin);
        db.update("UPDATE student_parent_control SET game_minutes = ? WHERE student_id = ?", minutes, student);
        return new Settings(control.dailyMinutes(), minutes);
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
                SELECT pin_hash, daily_minutes, game_minutes, failed_attempts, locked_until
                FROM student_parent_control WHERE student_id = ?
                """, (row, index) -> {
            var lock = row.getTimestamp(5);
            return new Control(row.getString(1), row.getObject(2, Integer.class), row.getObject(3, Integer.class),
                    row.getInt(4), lock == null ? null : lock.toInstant());
        }, student).stream().findFirst().orElse(null);
    }

    public record Status(boolean pinConfigured, boolean dailyLimitReached, boolean dailyLimitConfigured, boolean activityVerified) {}
    public record Settings(Integer dailyMinutes, Integer gameMinutes) {}
    private record Control(String hash, Integer dailyMinutes, Integer gameMinutes, int failedAttempts, Instant lockedUntil) {}
}

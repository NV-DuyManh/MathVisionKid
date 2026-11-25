package com.mathvisionkids.api.studentprofile;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.sql.Timestamp;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.UUID;

@Service
public class StudentGameUsageService {
    private static final long LEASE_MILLIS = 10_000;
    private final JdbcTemplate db;
    private final StudentProfileService profiles;

    StudentGameUsageService(JdbcTemplate db, StudentProfileService profiles) {
        this.db = db;
        this.profiles = profiles;
    }

    @Transactional
    public Lease heartbeat(String principal, UUID connection, boolean active) {
        var student = profiles.student(principal).getId();
        profiles.lockStudent(student);
        return observeLocked(student, connection, active, currentTime());
    }

    @Transactional
    public GameTimeStatus status(String principal) {
        var student = profiles.student(principal).getId();
        profiles.lockStudent(student);
        var now = currentTime();
        accrueLocked(student, now);
        var remaining = remaining(student, LocalDate.ofInstant(now, StudentRewards.ZONE), gameLimit(student));
        return new GameTimeStatus(Long.valueOf(0).equals(remaining));
    }

    @Transactional
    public Access access(String principal) {
        var student = profiles.student(principal).getId();
        profiles.lockStudent(student);
        var limit = gameLimit(student);
        if (limit == null) return Access.ALLOWED;
        var now = currentTime();
        accrueLocked(student, now);
        if (remaining(student, LocalDate.ofInstant(now, StudentRewards.ZONE), limit) == 0) return Access.LIMIT_REACHED;
        var active = db.queryForObject("""
                SELECT COUNT(*) FROM student_game_usage_connection WHERE student_id = ? AND lease_until > ?
                """, Long.class, student, Timestamp.from(now));
        return active != null && active > 0 ? Access.ALLOWED : Access.LEASE_REQUIRED;
    }

    Lease observeLocked(UUID student, UUID connection, boolean active, Instant now) {
        accrueLocked(student, now);
        var day = LocalDate.ofInstant(now, StudentRewards.ZONE);
        var remaining = remaining(student, day, gameLimit(student));
        boolean reached = Long.valueOf(0).equals(remaining);
        if (!active || reached) {
            db.update("DELETE FROM student_game_usage_connection WHERE student_id = ? AND connection_id = ?",
                    student, connection);
            return new Lease(remaining, 0, reached);
        }

        var midnight = day.plusDays(1).atStartOfDay(StudentRewards.ZONE).toInstant();
        long lease = Math.min(LEASE_MILLIS, Duration.between(now, midnight).toMillis());
        if (remaining != null) lease = Math.min(lease, remaining);
        var until = Timestamp.from(now.plusMillis(lease));
        var accounted = Timestamp.from(now);
        int updated = db.update("""
                UPDATE student_game_usage_connection SET accounted_at = ?, lease_until = ?
                WHERE student_id = ? AND connection_id = ?
                """, accounted, until, student, connection);
        if (updated == 0) db.update("""
                INSERT INTO student_game_usage_connection(student_id, connection_id, accounted_at, lease_until)
                VALUES (?, ?, ?, ?)
                """, student, connection, accounted, until);
        return new Lease(remaining, lease, false);
    }

    // All cursor updates run under the existing per-student lock. Merge pending spans before charging
    // them so the same wall-clock interval across tabs and devices consumes only one budget.
    void accrueLocked(UUID student, Instant now) {
        var pending = db.query("""
                SELECT accounted_at, lease_until FROM student_game_usage_connection
                WHERE student_id = ? AND accounted_at < ?
                ORDER BY accounted_at
                """, (row, index) -> new Span(row.getTimestamp(1).toInstant(), row.getTimestamp(2).toInstant()),
                student, Timestamp.from(now));
        Span merged = null;
        for (var span : pending) {
            var end = span.end().isAfter(now) ? now : span.end();
            if (merged == null) {
                merged = new Span(span.start(), end);
            } else if (span.start().isAfter(merged.end())) {
                addTime(student, merged);
                merged = new Span(span.start(), end);
            } else if (end.isAfter(merged.end())) {
                merged = new Span(merged.start(), end);
            }
        }
        if (merged != null) addTime(student, merged);
        // A disconnected client never renews. At most the already granted lease is charged.
        db.update("DELETE FROM student_game_usage_connection WHERE student_id = ? AND lease_until <= ?",
                student, Timestamp.from(now));
        db.update("""
                UPDATE student_game_usage_connection SET accounted_at = ?
                WHERE student_id = ? AND accounted_at < ?
                """, Timestamp.from(now), student, Timestamp.from(now));
    }

    private void addTime(UUID student, Span span) {
        var start = span.start();
        while (start.isBefore(span.end())) {
            var day = LocalDate.ofInstant(start, StudentRewards.ZONE);
            var midnight = day.plusDays(1).atStartOfDay(StudentRewards.ZONE).toInstant();
            var end = span.end().isBefore(midnight) ? span.end() : midnight;
            long elapsed = Duration.between(start, end).toMillis();
            int changed = db.update("""
                    UPDATE student_game_usage_day SET elapsed_millis = elapsed_millis + ?
                    WHERE student_id = ? AND usage_day = ?
                    """, elapsed, student, day);
            if (changed == 0) db.update("""
                    INSERT INTO student_game_usage_day(student_id, usage_day, elapsed_millis) VALUES (?, ?, ?)
                    """, student, day, elapsed);
            start = end;
        }
    }

    private Integer gameLimit(UUID student) {
        return db.query("SELECT game_minutes FROM student_parent_control WHERE student_id = ?",
                rs -> rs.next() ? rs.getObject(1, Integer.class) : null, student);
    }

    private Long remaining(UUID student, LocalDate day, Integer limit) {
        if (limit == null) return null;
        Long used = db.queryForObject("""
                SELECT COALESCE(MAX(elapsed_millis), 0) FROM student_game_usage_day
                WHERE student_id = ? AND usage_day = ?
                """, Long.class, student, day);
        return Math.max(0, limit * 60_000L - (used == null ? 0 : used));
    }

    static Instant currentTime() {
        return Instant.now().truncatedTo(ChronoUnit.MILLIS);
    }

    public enum Access { ALLOWED, LIMIT_REACHED, LEASE_REQUIRED }
    public record Lease(Long remainingMillis, long leaseMillis, boolean gameLimitReached) {}
    public record GameTimeStatus(boolean gameLimitReached) {}
    private record Span(Instant start, Instant end) {}
}

package com.mathvisionkids.api.studentprofile;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.sql.Timestamp;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.UUID;
import java.util.stream.IntStream;

@Service
public class StudentUsageService {
    static final Duration MAX_HEARTBEAT_GAP = Duration.ofSeconds(30);
    private final JdbcTemplate db;
    private final StudentProfileService profiles;

    StudentUsageService(JdbcTemplate db, StudentProfileService profiles) {
        this.db = db;
        this.profiles = profiles;
    }

    @Transactional
    public void observe(String principal, UUID connection, boolean active) {
        var student = profiles.student(principal).getId();
        profiles.lockStudent(student);
        observeLocked(student, connection, active, Instant.now().truncatedTo(java.time.temporal.ChronoUnit.MILLIS));
    }

    @Transactional
    public boolean recordProtectedActivity(String principal) {
        var student = profiles.student(principal).getId();
        profiles.lockStudent(student);
        var now = Instant.now().truncatedTo(java.time.temporal.ChronoUnit.MILLIS);
        var lastSeen = db.queryForObject("""
                SELECT MIN(last_seen_at) FROM student_usage_connection
                WHERE student_id = ? AND last_seen_at >= ?
                """, Timestamp.class, student, Timestamp.from(now.minus(MAX_HEARTBEAT_GAP)));
        if (lastSeen == null) return false;
        if (lastSeen.toInstant().isBefore(now)) recordUncoveredTime(student, lastSeen.toInstant(), now);
        return true;
    }

    void observeLocked(UUID student, UUID connection, boolean active, Instant now) {
        var cutoff = now.minus(MAX_HEARTBEAT_GAP);
        db.update("DELETE FROM student_usage_connection WHERE student_id = ? AND last_seen_at < ?",
                student, Timestamp.from(cutoff));
        db.update("DELETE FROM student_usage_recent_span WHERE student_id = ? AND ends_at < ?",
                student, Timestamp.from(cutoff));
        Instant previous = db.query("""
                SELECT last_seen_at FROM student_usage_connection WHERE student_id = ? AND connection_id = ?
                """, (row, index) -> row.getTimestamp(1).toInstant(), student, connection)
                .stream().findFirst().orElse(null);

        if (previous != null && previous.isBefore(now)) {
            recordUncoveredTime(student, previous, now);
        }
        if (!active) {
            db.update("DELETE FROM student_usage_connection WHERE student_id = ? AND connection_id = ?", student, connection);
        } else if (previous == null) {
            db.update("INSERT INTO student_usage_connection(student_id, connection_id, last_seen_at) VALUES (?, ?, ?)",
                    student, connection, Timestamp.from(now));
        } else if (previous.isBefore(now)) {
            db.update("UPDATE student_usage_connection SET last_seen_at = ? WHERE student_id = ? AND connection_id = ?",
                    Timestamp.from(now), student, connection);
        }
    }

    private void recordUncoveredTime(UUID student, Instant start, Instant finish) {
        var overlaps = db.query("""
                SELECT starts_at, ends_at FROM student_usage_recent_span
                WHERE student_id = ? AND ends_at >= ? AND starts_at <= ?
                ORDER BY starts_at
                """, (row, index) -> new Span(row.getTimestamp(1).toInstant(), row.getTimestamp(2).toInstant()),
                student, Timestamp.from(start), Timestamp.from(finish));
        Instant cursor = start;
        Instant mergedStart = start;
        Instant mergedFinish = finish;
        for (var covered : overlaps) {
            if (covered.start().isAfter(cursor)) addInterval(student, cursor, covered.start());
            if (covered.finish().isAfter(cursor)) cursor = covered.finish();
            if (covered.start().isBefore(mergedStart)) mergedStart = covered.start();
            if (covered.finish().isAfter(mergedFinish)) mergedFinish = covered.finish();
        }
        addInterval(student, cursor, finish);
        db.update("DELETE FROM student_usage_recent_span WHERE student_id = ? AND ends_at >= ? AND starts_at <= ?",
                student, Timestamp.from(start), Timestamp.from(finish));
        db.update("INSERT INTO student_usage_recent_span(student_id, starts_at, ends_at) VALUES (?, ?, ?)",
                student, Timestamp.from(mergedStart), Timestamp.from(mergedFinish));
    }

    private void addInterval(UUID student, Instant start, Instant end) {
        while (start.isBefore(end)) {
            var day = LocalDate.ofInstant(start, StudentRewards.ZONE);
            var midnight = day.plusDays(1).atStartOfDay(StudentRewards.ZONE).toInstant();
            var through = end.isBefore(midnight) ? end : midnight;
            long elapsed = Duration.between(start, through).toMillis();
            int changed = db.update("""
                    UPDATE student_usage_day SET elapsed_millis = elapsed_millis + ?
                    WHERE student_id = ? AND usage_day = ?
                    """, elapsed, student, day);
            if (changed == 0) db.update("""
                    INSERT INTO student_usage_day(student_id, usage_day, elapsed_millis) VALUES (?, ?, ?)
                    """, student, day, elapsed);
            start = through;
        }
    }

    @Transactional(readOnly = true)
    public Week week(String principal) {
        return weekFor(profiles.student(principal).getId(), LocalDate.now(StudentRewards.ZONE));
    }

    Week weekFor(UUID student, LocalDate today) {
        LocalDate monday = today.minusDays(today.getDayOfWeek().getValue() - 1L);
        var totals = new HashMap<LocalDate, Long>();
        db.query("""
                SELECT usage_day, elapsed_millis FROM student_usage_day
                WHERE student_id = ? AND usage_day BETWEEN ? AND ?
                """, row -> {
            totals.put(row.getObject(1, LocalDate.class), row.getLong(2));
        }, student, monday, today);
        List<Day> days = IntStream.range(0, 7).mapToObj(i -> monday.plusDays(i))
                .map(day -> new Day(day.toString(), totals.getOrDefault(day, 0L))).toList();
        return new Week(today.toString(), days.stream().mapToLong(Day::elapsedMillis).sum(), days);
    }

    public record Day(String date, long elapsedMillis) {}
    public record Week(String today, long totalMillis, List<Day> days) {}
    private record Span(Instant start, Instant finish) {}
}

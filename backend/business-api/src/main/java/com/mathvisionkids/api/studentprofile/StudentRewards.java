package com.mathvisionkids.api.studentprofile;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.UUID;

@Service
public class StudentRewards {
    public enum Source { LESSON, QUIZ, GAME }
    static final ZoneId ZONE = ZoneId.of("Asia/Ho_Chi_Minh");
    private final JdbcTemplate db;
    private final int dailyLimit;
    private final int sourceLimit;

    public StudentRewards(JdbcTemplate db, @Value("${app.student-rewards.daily-limit:6}") int dailyLimit,
                          @Value("${app.student-rewards.source-limit:3}") int sourceLimit) {
        if (dailyLimit < 1 || sourceLimit < 1) throw new IllegalArgumentException("Reward limits must be positive");
        this.db = db;
        this.dailyLimit = dailyLimit;
        this.sourceLimit = sourceLimit;
    }

    void lock() {
        db.queryForObject("SELECT id FROM student_reward_lock WHERE id = 1 FOR UPDATE", Integer.class);
    }

    @Transactional
    public int record(UUID student, Source source, String eventId, String contentId) {
        lock();
        return recordLocked(student, source, eventId, contentId, Instant.now());
    }

    int recordLocked(UUID student, Source source, String eventId, String contentId, Instant now) {
        String kind = source.name();
        var existing = db.queryForList("""
                SELECT stars FROM student_verified_activities WHERE student_id = ? AND source = ? AND event_id = ?
                """, Integer.class, student, kind, eventId);
        if (!existing.isEmpty()) return existing.getFirst();
        boolean eligible = Boolean.TRUE.equals(db.queryForObject("""
                SELECT active AND role = 'STUDENT' AND LOWER(email) NOT LIKE '%@mathvision.local'
                FROM users WHERE id = ?
                """, Boolean.class, student));
        if (!eligible) return 0;
        LocalDate day = now.atZone(ZONE).toLocalDate();
        long daily = db.queryForObject("""
                SELECT COALESCE(SUM(stars), 0) FROM student_verified_activities WHERE student_id = ? AND activity_day = ?
                """, Long.class, student, day);
        long sourceTotal = db.queryForObject("""
                SELECT COALESCE(SUM(stars), 0) FROM student_verified_activities WHERE student_id = ? AND activity_day = ? AND source = ?
                """, Long.class, student, day, kind);
        // Record one verified result per lesson/quiz content, even when the daily star cap was reached.
        String query = """
                SELECT COUNT(*) FROM student_verified_activities WHERE student_id = ? AND source = ? AND content_id = ?
                """;
        long previous = source == Source.GAME
                ? db.queryForObject(query + " AND activity_day = ?", Long.class, student, kind, contentId, day)
                : db.queryForObject(query, Long.class, student, kind, contentId);
        if (source != Source.GAME && previous != 0) return 0;
        int stars = daily < dailyLimit && sourceTotal < sourceLimit && previous == 0 ? 1 : 0;
        db.update("""
                INSERT INTO student_verified_activities(student_id, source, event_id, content_id, completed_at, activity_day, stars)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, student, kind, eventId, contentId, Timestamp.from(now), day, stars);
        if (stars == 1 && db.queryForObject("""
                SELECT COALESCE(SUM(stars), 0) FROM student_verified_activities WHERE student_id = ?
                """, Long.class, student) >= StudentRank.CHALLENGER_MIN_STARS) rememberChallengers();
        return stars;
    }

    static final String GLOBAL_RANKING = """
            SELECT p.student_id, p.public_alias, p.avatar, SUM(a.stars) AS stars,
              ROW_NUMBER() OVER (ORDER BY SUM(a.stars) DESC, p.public_alias) AS position
            FROM student_profile_preferences p
            JOIN users u ON u.id = p.student_id
            JOIN student_verified_activities a ON a.student_id = p.student_id AND a.stars = 1
            WHERE p.leaderboard_visible = TRUE AND u.active = TRUE AND u.role = 'STUDENT'
              AND LOWER(u.email) NOT LIKE '%@mathvision.local'
            GROUP BY p.student_id, p.public_alias, p.avatar
            """;

    void rememberChallengers() {
        db.update("""
                UPDATE student_profile_preferences SET reached_challenger = TRUE
                WHERE reached_challenger = FALSE AND student_id IN (
                    SELECT student_id FROM (%s) ranking WHERE position <= ? AND stars >= ?
                )
                """.formatted(GLOBAL_RANKING), StudentRank.CHALLENGER_SIZE, StudentRank.CHALLENGER_MIN_STARS);
    }
}

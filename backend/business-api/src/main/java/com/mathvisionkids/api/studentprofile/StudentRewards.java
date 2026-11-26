package com.mathvisionkids.api.studentprofile;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.UUID;
import com.mathvisionkids.api.studentprofile.ProfileDtos.GameRewardStatus;

@Service
public class StudentRewards {
    public enum Source { LESSON, QUIZ, GAME }
    static final ZoneId ZONE = ZoneId.of("Asia/Ho_Chi_Minh");
    private final JdbcTemplate db;
    public StudentRewards(JdbcTemplate db) {
        this.db = db;
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
        return recordAward(student, source, eventId, contentId, now).stars();
    }

    record Award(int stars, GameRewardStatus status) {}

    Award recordAward(UUID student, Source source, String eventId, String contentId, Instant now) {
        String kind = source.name();
        var existing = db.queryForList("""
                SELECT stars FROM student_verified_activities WHERE student_id = ? AND source = ? AND event_id = ?
                """, Integer.class, student, kind, eventId);
        if (!existing.isEmpty()) return new Award(existing.getFirst(), null);
        boolean eligible = Boolean.TRUE.equals(db.queryForObject("""
                SELECT active AND role = 'STUDENT' AND LOWER(email) NOT LIKE '%@mathvision.local'
                FROM users WHERE id = ?
                """, Boolean.class, student));
        if (!eligible) return new Award(0, GameRewardStatus.UNAVAILABLE);
        LocalDate day = now.atZone(ZONE).toLocalDate();
        String query = """
                SELECT COUNT(*) FROM student_verified_activities WHERE student_id = ? AND source = ? AND content_id = ?
                """;
        long previous = source == Source.GAME
                ? db.queryForObject(query + " AND activity_day = ?", Long.class, student, kind, contentId, day)
                : db.queryForObject(query, Long.class, student, kind, contentId);
        if (source != Source.GAME && previous != 0) return new Award(0, GameRewardStatus.REPEAT);
        GameRewardStatus status = previous != 0 ? GameRewardStatus.REPEAT : GameRewardStatus.AWARDED;
        int stars = status == GameRewardStatus.AWARDED ? 1 : 0;
        db.update("""
                INSERT INTO student_verified_activities(student_id, source, event_id, content_id, completed_at, activity_day, stars)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, student, kind, eventId, contentId, Timestamp.from(now), day, stars);
        if (stars == 1 && db.queryForObject("""
                SELECT COALESCE(SUM(stars), 0) FROM student_verified_activities WHERE student_id = ?
                """, Long.class, student) >= StudentRank.CHALLENGER_MIN_STARS) rememberChallengers();
        return new Award(stars, status);
    }

    static final String GLOBAL_RANKING = """
            SELECT p.student_id, p.public_alias, p.avatar,
              CASE WHEN p.leaderboard_name_hidden = FALSE AND TRIM(u.display_name) <> '' AND u.display_name NOT LIKE '%@%'
                THEN u.display_name ELSE p.public_alias END AS board_name, SUM(a.stars) AS stars,
              ROW_NUMBER() OVER (ORDER BY SUM(a.stars) DESC, p.public_alias) AS position
            FROM student_profile_preferences p
            JOIN users u ON u.id = p.student_id
            JOIN student_verified_activities a ON a.student_id = p.student_id AND a.stars = 1
            WHERE p.leaderboard_visible = TRUE AND u.active = TRUE AND u.role = 'STUDENT'
              AND LOWER(u.email) NOT LIKE '%@mathvision.local'
            GROUP BY p.student_id, p.public_alias, p.avatar, p.leaderboard_name_hidden, u.display_name
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

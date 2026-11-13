package com.mathvisionkids.api.studentprofile;

import com.mathvisionkids.api.common.ApiException;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.sql.Timestamp;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.util.Random;
import java.util.UUID;

import static com.mathvisionkids.api.studentprofile.ProfileDtos.*;

@Service
public class StudentGameService {
    private static final int QUESTIONS = 5;
    private static final int MIN_CORRECT = 4;
    private static final Duration EXPIRY = Duration.ofMinutes(20);
    private final SecureRandom seeds = new SecureRandom();
    private final StudentProfileService profiles;
    private final StudentRewards rewards;
    private final JdbcTemplate db;

    private record Run(UUID id, int level, long seed, Instant startedAt, int answered, int correct, Integer lastAnswer) {}
    private record Problem(String prompt, int answer) {}

    public StudentGameService(StudentProfileService profiles, StudentRewards rewards, JdbcTemplate db) {
        this.profiles = profiles;
        this.rewards = rewards;
        this.db = db;
    }

    @Transactional
    public Game start(String principal) {
        var student = profiles.student(principal);
        var id = student.getId();
        if (student.getEmail().toLowerCase(java.util.Locale.ROOT).endsWith("@mathvision.local"))
            throw new ApiException("GAME_NOT_AVAILABLE", "Tài khoản này chưa mở được lượt chơi tính thành tích.", HttpStatus.FORBIDDEN);
        profiles.lockStudent(id);
        rewards.lock();
        Instant now = Instant.now();
        LocalDate day = now.atZone(StudentRewards.ZONE).toLocalDate();
        var current = db.query("""
                SELECT * FROM student_game_runs WHERE student_id = ? AND started_at > ? AND answered < 5
                ORDER BY started_at DESC LIMIT 1
                """, (r, n) -> run(r), id, Timestamp.from(now.minus(EXPIRY)));
        if (!current.isEmpty()) return view(current.getFirst(), 0);
        if (db.queryForObject("SELECT COUNT(*) FROM student_game_runs WHERE student_id = ? AND activity_day = ?",
                Long.class, id, day) >= 12) {
            throw new ApiException("GAME_LIMIT", "Hôm nay em đã chơi đủ lượt rồi.", HttpStatus.TOO_MANY_REQUESTS);
        }
        int level = student.getGradeLevel() == null ? 1 : Math.clamp(student.getGradeLevel(), 1, 5);
        Run run = new Run(UUID.randomUUID(), level, seeds.nextLong(), now, 0, 0, null);
        db.update("""
                INSERT INTO student_game_runs(id, student_id, level, started_at, activity_day, seed) VALUES (?, ?, ?, ?, ?, ?)
                """, run.id(), id, level, Timestamp.from(now), day, run.seed());
        return view(run, 0);
    }

    @Transactional
    public Game answer(String principal, UUID gameId, GameAnswer request) {
        var student = profiles.student(principal).getId();
        profiles.lockStudent(student);
        rewards.lock();
        Run run = db.query("SELECT * FROM student_game_runs WHERE id = ? AND student_id = ?", (r, n) -> run(r), gameId, student)
                .stream().findFirst().orElseThrow(() -> new ApiException("GAME_NOT_FOUND", "Em chưa có lượt chơi này.", HttpStatus.NOT_FOUND));
        if (request.question() == run.answered() - 1 && request.answer().equals(run.lastAnswer())) {
            int stars = db.queryForList("""
                    SELECT stars FROM student_verified_activities WHERE student_id = ? AND source = 'GAME' AND event_id = ?
                    """, Integer.class, student, gameId.toString()).stream().findFirst().orElse(0);
            return view(run, stars);
        }
        Instant now = Instant.now();
        if (run.answered() >= QUESTIONS || request.question() != run.answered() || !now.isBefore(run.startedAt().plus(EXPIRY))) {
            throw new ApiException("GAME_STEP_CHANGED", "Lượt chơi đã đổi bước hoặc hết giờ. Em mở lại trò chơi nhé.", HttpStatus.CONFLICT);
        }
        int correct = run.correct() + (question(run, run.answered()).answer() == request.answer() ? 1 : 0);
        int answered = run.answered() + 1;
        db.update("UPDATE student_game_runs SET answered = ?, correct = ?, last_answer = ? WHERE id = ?",
                answered, correct, request.answer(), gameId);
        int stars = answered == QUESTIONS && correct >= MIN_CORRECT
                ? rewards.recordLocked(student, StudentRewards.Source.GAME, gameId.toString(), "arithmetic-quest:" + run.level(), now)
                : 0;
        return view(new Run(gameId, run.level(), run.seed(), run.startedAt(), answered, correct, request.answer()), stars);
    }

    private Run run(java.sql.ResultSet row) throws java.sql.SQLException {
        return new Run(row.getObject("id", UUID.class), row.getInt("level"), row.getLong("seed"),
                row.getTimestamp("started_at").toInstant(), row.getInt("answered"), row.getInt("correct"),
                row.getObject("last_answer", Integer.class));
    }

    private Game view(Run run, int stars) {
        boolean complete = run.answered() == QUESTIONS;
        return new Game(run.id(), run.answered(), complete ? null : question(run, run.answered()).prompt(),
                run.correct(), QUESTIONS, complete, stars);
    }

    private Problem question(Run run, int index) {
        var random = new Random(run.seed() ^ Long.rotateLeft(0x9e3779b97f4a7c15L, index * 7));
        int bound = switch (run.level()) { case 1 -> 10; case 2 -> 50; case 3 -> 100; case 4 -> 500; default -> 1000; };
        int a = 1 + random.nextInt(bound), b = 1 + random.nextInt(bound);
        if (random.nextBoolean()) {
            int max = Math.max(a, b), min = Math.min(a, b);
            return new Problem(max + " − " + min, max - min);
        }
        return new Problem(a + " + " + b, a + b);
    }
}

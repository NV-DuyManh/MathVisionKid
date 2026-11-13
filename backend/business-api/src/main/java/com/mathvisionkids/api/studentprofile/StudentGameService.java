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
import java.util.Locale;

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

    private record Run(UUID id, int level, GameMode mode, long seed, Instant startedAt, int answered, int correct,
                       Integer lastAnswer, GameRewardStatus rewardStatus) {}
    private record Problem(String prompt, int answer) {}

    public StudentGameService(StudentProfileService profiles, StudentRewards rewards, JdbcTemplate db) {
        this.profiles = profiles;
        this.rewards = rewards;
        this.db = db;
    }

    @Transactional
    public Game start(String principal) {
        return start(principal, GameMode.ARITHMETIC_QUEST);
    }

    @Transactional
    public Game start(String principal, GameMode mode) {
        var student = profiles.student(principal);
        var id = student.getId();
        if (student.getEmail().toLowerCase(Locale.ROOT).endsWith("@mathvision.local"))
            throw new ApiException("GAME_NOT_AVAILABLE", "Tài khoản này chưa mở được lượt chơi tính thành tích.", HttpStatus.FORBIDDEN);
        profiles.lockStudent(id);
        rewards.lock();
        Instant now = Instant.now();
        LocalDate day = now.atZone(StudentRewards.ZONE).toLocalDate();
        var current = db.query("""
                SELECT * FROM student_game_runs WHERE student_id = ? AND mode = ? AND started_at > ? AND answered < 5
                ORDER BY started_at DESC LIMIT 1
                """, (r, n) -> run(r), id, mode.name(), Timestamp.from(now.minus(EXPIRY)));
        if (!current.isEmpty()) return view(current.getFirst(), 0);
        if (db.queryForObject("SELECT COUNT(*) FROM student_game_runs WHERE student_id = ? AND activity_day = ?",
                Long.class, id, day) >= 12) {
            throw new ApiException("GAME_LIMIT", "Hôm nay em đã chơi đủ lượt rồi.", HttpStatus.TOO_MANY_REQUESTS);
        }
        int level = student.getGradeLevel() == null ? 1 : Math.clamp(student.getGradeLevel(), 1, 5);
        Run run = new Run(UUID.randomUUID(), level, mode, seeds.nextLong(), now, 0, 0, null, null);
        db.update("""
                INSERT INTO student_game_runs(id, student_id, level, mode, started_at, activity_day, seed) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, run.id(), id, level, mode.name(), Timestamp.from(now), day, run.seed());
        return view(run, 0);
    }

    @Transactional(readOnly = true)
    public Game get(String principal, UUID gameId) {
        var student = profiles.student(principal).getId();
        Run run = ownedRun(student, gameId);
        requireCurrent(run, Instant.now());
        return view(run, storedStars(student, run));
    }

    @Transactional
    public Game answer(String principal, UUID gameId, GameAnswer request) {
        var student = profiles.student(principal).getId();
        profiles.lockStudent(student);
        rewards.lock();
        Run run = ownedRun(student, gameId);
        Instant now = Instant.now();
        requireCurrent(run, now);
        if (request.question() == run.answered() - 1 && request.answer().equals(run.lastAnswer())) {
            return view(run, storedStars(student, run));
        }
        if (run.answered() >= QUESTIONS || request.question() != run.answered()) {
            throw new ApiException("GAME_STEP_CHANGED", "Lượt chơi đã đổi bước hoặc hết giờ. Em mở lại trò chơi nhé.", HttpStatus.CONFLICT);
        }
        int correct = run.correct() + (question(run, run.answered()).answer() == request.answer() ? 1 : 0);
        int answered = run.answered() + 1;
        String modeKey = run.mode().name().toLowerCase(Locale.ROOT).replace('_', '-');
        String content = modeKey + (run.mode() == GameMode.ARITHMETIC_QUEST ? ":" + run.level() : ":math");
        StudentRewards.Award award = answered == QUESTIONS && correct >= MIN_CORRECT
                ? rewards.recordAward(student, StudentRewards.Source.GAME, gameId.toString(), content, now)
                : new StudentRewards.Award(0, null);
        db.update("UPDATE student_game_runs SET answered = ?, correct = ?, last_answer = ?, reward_status = ? WHERE id = ?",
                answered, correct, request.answer(), award.status() == null ? null : award.status().name(), gameId);
        return view(new Run(gameId, run.level(), run.mode(), run.seed(), run.startedAt(), answered, correct,
                request.answer(), award.status()), award.stars());
    }

    private Run ownedRun(UUID student, UUID gameId) {
        return db.query("SELECT * FROM student_game_runs WHERE id = ? AND student_id = ?", (r, n) -> run(r), gameId, student)
                .stream().findFirst().orElseThrow(() -> new ApiException("GAME_NOT_FOUND", "Em chưa có lượt chơi này.", HttpStatus.NOT_FOUND));
    }

    private void requireCurrent(Run run, Instant now) {
        if (run.answered() < QUESTIONS && !now.isBefore(run.startedAt().plus(EXPIRY)))
            throw new ApiException("GAME_EXPIRED", "Lượt chơi đã hết giờ. Em mở một lượt mới nhé.", HttpStatus.CONFLICT);
    }

    private int storedStars(UUID student, Run run) {
        if (run.answered() < QUESTIONS || run.correct() < MIN_CORRECT) return 0;
        return db.queryForList("""
                SELECT stars FROM student_verified_activities WHERE student_id = ? AND source = 'GAME' AND event_id = ?
                """, Integer.class, student, run.id().toString()).stream().findFirst().orElse(0);
    }

    private Run run(java.sql.ResultSet row) throws java.sql.SQLException {
        String rewardStatus = row.getString("reward_status");
        return new Run(row.getObject("id", UUID.class), row.getInt("level"), GameMode.valueOf(row.getString("mode")), row.getLong("seed"),
                row.getTimestamp("started_at").toInstant(), row.getInt("answered"), row.getInt("correct"),
                row.getObject("last_answer", Integer.class), rewardStatus == null ? null : GameRewardStatus.valueOf(rewardStatus));
    }

    private Game view(Run run, int stars) {
        boolean complete = run.answered() == QUESTIONS;
        GameRewardStatus status = run.rewardStatus() == null && stars > 0 ? GameRewardStatus.AWARDED : run.rewardStatus();
        return new Game(run.id(), run.answered(), complete ? null : question(run, run.answered()).prompt(),
                run.correct(), QUESTIONS, complete, stars, status);
    }

    private Problem question(Run run, int index) {
        var random = new Random(run.seed() ^ Long.rotateLeft(0x9e3779b97f4a7c15L, index * 7));
        if (run.mode() != GameMode.ARITHMETIC_QUEST) return trainingQuestion(run, index, random);
        int bound = switch (run.level()) { case 1 -> 10; case 2 -> 50; case 3 -> 100; case 4 -> 500; default -> 1000; };
        int a = 1 + random.nextInt(bound), b = 1 + random.nextInt(bound);
        if (random.nextBoolean()) {
            int max = Math.max(a, b), min = Math.min(a, b);
            return new Problem(max + " − " + min, max - min);
        }
        return new Problem(a + " + " + b, a + b);
    }

    private Problem trainingQuestion(Run run, int index, Random random) {
        int a = 2 + random.nextInt(11), b = 2 + random.nextInt(8);
        boolean even = index % 2 == 0;
        return switch (run.mode()) {
            case RACE_TO_FINISH -> run.level() >= 3
                    ? (even ? new Problem(a + " × " + b, a * b) : new Problem((a * b) + " ÷ " + b, a))
                    : (even ? new Problem(a + " + " + b, a + b) : new Problem((a + b) + " − " + b, a));
            case TERRAIN_RACING -> even
                    ? new Problem("Xe chạy " + a + " m mỗi giây trong " + b + " giây. Xe đi được bao nhiêu mét?", a * b)
                    : new Problem("Xe đi " + (a * b) + " m trong " + b + " giây. Vận tốc là bao nhiêu mét mỗi giây?", a);
            case ENERGY_DEFENSE -> {
                int charge = 1 + random.nextInt(9);
                yield even
                        ? new Problem("Pin có " + a + " phần và nạp thêm " + b + " phần. Tổng có bao nhiêu phần?", a + b)
                        : new Problem("Pin còn " + charge + "/10 năng lượng. Cần thêm bao nhiêu phần mười để đầy pin?", 10 - charge);
            }
            case PLANET_RESCUE -> even
                    ? new Problem("Viết 1/" + b + " thành phân số có mẫu " + (a * b) + ". Tử số mới là bao nhiêu?", a)
                    : new Problem("Rút gọn " + a + "/" + (a * b) + " về dạng tối giản. Mẫu số mới là bao nhiêu?", b);
            case BLOCK_ISLAND -> even
                    ? new Problem("Mảnh đất hình chữ nhật dài " + a + " m, rộng " + b + " m. Diện tích là bao nhiêu mét vuông?", a * b)
                    : new Problem("Mảnh đất hình chữ nhật dài " + a + " m, rộng " + b + " m. Chu vi là bao nhiêu mét?", 2 * (a + b));
            case ARITHMETIC_QUEST -> throw new IllegalStateException("Arithmetic quest has its own generator");
        };
    }
}

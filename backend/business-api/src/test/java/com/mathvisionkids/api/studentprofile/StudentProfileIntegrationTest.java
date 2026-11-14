package com.mathvisionkids.api.studentprofile;

import com.mathvisionkids.api.quiz.QuizSources;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.support.TransactionTemplate;
import static com.mathvisionkids.api.studentprofile.ProfileDtos.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class StudentProfileIntegrationTest {
    @Autowired StudentRepository students;
    @Autowired StudentRewards rewards;
    @Autowired StudentProfileService profiles;
    @Autowired StudentGameService games;
    @Autowired QuizSources lessons;
    @Autowired JdbcTemplate db;
    @Autowired MockMvc mvc;
    @Autowired TransactionTemplate transaction;
    Student pupil;
    Student other;

    @BeforeEach void createStudents() {
        pupil = createStudent("@profile.test");
        other = createStudent("@profile.test");
    }

    private Student createStudent(String suffix) {
        Student s = new Student();
        s.setDisplayName("Học Sinh");
        s.setEmail(UUID.randomUUID() + suffix);
        s.setPasswordHash("unused");
        s.setRole("STUDENT");
        s.setGradeLevel(3);
        return students.saveAndFlush(s);
    }

    @Test void onlyVerifiedInteractiveCompletionIsCountedAndCannotBeFarmed() {
        String email = pupil.getEmail();
        lessons.record(email, "LESSON", "read", "2 + 2", false);
        lessons.complete(email, "read", false);
        lessons.record(email, "WORK_REVIEW", "work", "2 + 2", true);
        assertEquals(0, profiles.get(email).stars());
        lessons.record(email, "LESSON", "verified", "2 + 2", false);
        lessons.complete(email, "verified", true);
        lessons.complete(email, "verified", true);
        lessons.record(email, "LESSON", "duplicate", "2  +  2", false);
        lessons.complete(email, "duplicate", true);
        assertEquals(1, profiles.get(email).stars());
        assertEquals(1, profiles.get(email).stats().lessons());
        assertEquals(0, profiles.get(other.getEmail()).stars());
    }

    @Test void concurrentRetriesAreOneLedgerRowAndRollbackLeavesNoReward() throws Exception {
        UUID id = pupil.getId();
        try (var pool = Executors.newFixedThreadPool(6)) {
            var gate = new CountDownLatch(1);
            List<Future<Integer>> responses = new java.util.ArrayList<>();
            for (int i = 0; i < 6; i++) responses.add(pool.submit(() -> {
                gate.await();
                return rewards.record(id, StudentRewards.Source.QUIZ, "one", "one-content");
            }));
            gate.countDown();
            for (var response : responses) assertEquals(1, response.get(15, TimeUnit.SECONDS));
        }
        assertThrows(IllegalStateException.class, () -> transaction.executeWithoutResult(status -> {
            rewards.record(id, StudentRewards.Source.QUIZ, "rollback", "other-content");
            throw new IllegalStateException("test rollback");
        }));
        assertEquals(1, profiles.get(pupil.getEmail()).stars());
        assertEquals(1, profiles.get(pupil.getEmail()).stats().quizzes());
        for (int i = 2; i <= 5; i++) rewards.record(id, StudentRewards.Source.QUIZ, "event-" + i, "quiz-" + i);
        assertEquals(3, profiles.get(pupil.getEmail()).stars());
        assertEquals(5, profiles.get(pupil.getEmail()).stats().quizzes());
    }

    @Test void gameGradesOnServerAndReplaysOnlyItsOwnResult() throws Exception {
        String owner = pupil.getEmail();
        Game game = games.start(owner);
        assertEquals(game.id(), games.start(owner).id());
        assertEquals(0, profiles.get(owner).stars());
        mvc.perform(post("/api/v1/student/game-runs/{id}/answers", game.id()).with(user(other.getEmail()).roles("STUDENT"))
                .contentType("application/json").content("{\"question\":0,\"answer\":1}")).andExpect(status().isNotFound());
        mvc.perform(post("/api/v1/student/game-runs/{id}/answers", game.id()).with(user(owner).roles("STUDENT"))
                .contentType("application/json").content("{\"question\":4,\"answer\":1}")).andExpect(status().isConflict());
        while (!game.completed()) {
            int answer = answer(game.prompt());
            var request = new GameAnswer(game.question(), answer);
            Game next = games.answer(owner, game.id(), request);
            assertEquals(next, games.answer(owner, game.id(), request));
            game = next;
        }
        assertEquals(5, game.correct());
        assertEquals(1, game.stars());
        assertEquals(1, profiles.get(owner).stats().games());
        Game next = games.start(owner);
        while (!next.completed()) next = games.answer(owner, next.id(), new GameAnswer(next.question(), answer(next.prompt())));
        assertEquals(0, next.stars());
        assertEquals(GameRewardStatus.REPEAT, next.rewardStatus());
        assertEquals(1, profiles.get(owner).stars());
    }

    @Test void raceChallengeResumesAndConcurrentFinalRetriesCannotAwardTwice() throws Exception {
        String owner = pupil.getEmail();
        Game first = games.start(owner, GameMode.RACE_TO_FINISH);
        assertNotEquals(first.id(), games.start(owner).id());
        Game game = first;
        while (game.question() < 4) {
            game = games.answer(owner, game.id(), new GameAnswer(game.question(), answer(game.prompt())));
        }
        assertEquals(game, games.start(owner, GameMode.RACE_TO_FINISH));
        assertEquals(game, games.get(owner, first.id()));
        mvc.perform(get("/api/v1/student/game-runs/{id}", first.id()).with(user(other.getEmail()).roles("STUDENT")))
                .andExpect(status().isNotFound());
        var last = new GameAnswer(game.question(), answer(game.prompt()));
        try (var pool = Executors.newFixedThreadPool(2)) {
            var gate = new CountDownLatch(1);
            Callable<Game> submit = () -> { gate.await(); return games.answer(owner, first.id(), last); };
            var a = pool.submit(submit);
            var b = pool.submit(submit);
            gate.countDown();
            Game completed = a.get(15, TimeUnit.SECONDS);
            assertEquals(completed, b.get(15, TimeUnit.SECONDS));
            assertEquals(completed, games.get(owner, first.id()));
            assertEquals(1, completed.stars());
            assertEquals(GameRewardStatus.AWARDED, completed.rewardStatus());
        }
        assertEquals(1, profiles.get(owner).stats().games());
        assertEquals(1, profiles.get(owner).stars());
    }

    @Test void raceChallengeReportsGameCapAndRecordsTheWin() {
        for (int i = 0; i < 3; i++) {
            rewards.record(pupil.getId(), StudentRewards.Source.GAME, "existing-" + i, "game-" + i);
        }
        String owner = pupil.getEmail();
        Game game = games.start(owner, GameMode.RACE_TO_FINISH);
        while (!game.completed()) {
            game = games.answer(owner, game.id(), new GameAnswer(game.question(), answer(game.prompt())));
        }
        assertEquals(0, game.stars());
        assertEquals(GameRewardStatus.GAME_LIMIT, game.rewardStatus());
        assertEquals(game, games.get(owner, game.id()));
        assertEquals(4, profiles.get(owner).stats().games());
    }

    @Test void expiredRaceChallengeCannotBeAnsweredAndCanStartAgain() throws Exception {
        String owner = pupil.getEmail();
        var player = user(owner).roles("STUDENT");
        Game game = games.start(owner, GameMode.RACE_TO_FINISH);
        db.update("UPDATE student_game_runs SET started_at = ? WHERE id = ?",
                java.sql.Timestamp.from(java.time.Instant.now().minusSeconds(1260)), game.id());
        mvc.perform(get("/api/v1/student/game-runs/{id}", game.id()).with(player))
                .andExpect(status().isConflict()).andExpect(jsonPath("$.error.code").value("GAME_EXPIRED"));
        mvc.perform(post("/api/v1/student/game-runs/{id}/answers", game.id()).with(player)
                        .contentType("application/json").content("{\"question\":0,\"answer\":1}"))
                .andExpect(status().isConflict()).andExpect(jsonPath("$.error.code").value("GAME_EXPIRED"));
        assertNotEquals(game.id(), games.start(owner, GameMode.RACE_TO_FINISH).id());
        assertEquals(0, profiles.get(owner).stars());
    }

    @Test void everyTrainingModeGradesItsOwnQuestionsAndSharesTheStarCap() {
        pupil.setGradeLevel(5);
        students.saveAndFlush(pupil);
        String owner = pupil.getEmail();
        GameMode[] modes = {GameMode.TERRAIN_RACING, GameMode.ENERGY_DEFENSE, GameMode.PLANET_RESCUE, GameMode.BLOCK_ISLAND};
        for (int mode = 0; mode < modes.length; mode++) {
            Game game = games.start(owner, modes[mode]);
            while (!game.completed()) {
                int expected = themedAnswer(modes[mode], game.prompt());
                game = games.answer(owner, game.id(), new GameAnswer(game.question(), expected));
            }
            assertEquals(5, game.correct(), modes[mode].name());
            assertEquals(mode < 3 ? GameRewardStatus.AWARDED : GameRewardStatus.GAME_LIMIT, game.rewardStatus());
        }
        var profile = profiles.get(owner);
        assertEquals(3, profile.stars());
        assertEquals(4, profile.stats().games());
    }

    @Test void trainingChallengesUseTheStoredGradeBeforeIntroducingFractionsOrSpeed() {
        for (int grade : new int[]{1, 2, 3, 4, 5}) {
            Student student = createStudent("@grade.profile.test");
            student.setGradeLevel(grade);
            students.saveAndFlush(student);
            for (GameMode mode : GameMode.values()) {
                if (mode == GameMode.ARITHMETIC_QUEST) continue;
                Game game = games.start(student.getEmail(), mode);
                assertEquals(grade, db.queryForObject("SELECT level FROM student_game_runs WHERE id = ?", Integer.class, game.id()));
                while (!game.completed()) {
                    boolean basic = grade <= 2 || mode == GameMode.RACE_TO_FINISH
                            || mode == GameMode.TERRAIN_RACING && grade < 5
                            || grade == 3 && (mode == GameMode.ENERGY_DEFENSE || mode == GameMode.PLANET_RESCUE);
                    if (grade <= 2) assertTrue(game.prompt().matches("\\d+ [+−] \\d+"), game.prompt());
                    if (grade == 1) {
                        var numbers = java.util.regex.Pattern.compile("\\d+").matcher(game.prompt()).results().toList();
                        for (var number : numbers) assertTrue(Integer.parseInt(number.group()) <= 18);
                    }
                    int expected = basic ? answer(game.prompt()) : themedAnswer(mode, game.prompt());
                    game = games.answer(student.getEmail(), game.id(), new GameAnswer(game.question(), expected));
                }
                assertEquals(5, game.correct(), "grade " + grade + " " + mode);
            }
        }
    }

    private int themedAnswer(GameMode mode, String prompt) {
        int[] values = java.util.regex.Pattern.compile("\\d+").matcher(prompt).results()
                .mapToInt(match -> Integer.parseInt(match.group())).toArray();
        int a = values[0], b = values[1];
        return switch (mode) {
            case TERRAIN_RACING -> prompt.contains("đi được") ? a * b : a / b;
            case ENERGY_DEFENSE -> prompt.contains("Tổng") ? a + b : b - a;
            case PLANET_RESCUE -> prompt.contains("Tử số") ? values[2] / b : b / a;
            case BLOCK_ISLAND -> prompt.contains("Diện tích") ? a * b : 2 * (a + b);
            default -> throw new IllegalArgumentException(prompt);
        };
    }

    private int answer(String prompt) {
        String[] parts = prompt.split(" ");
        int a = Integer.parseInt(parts[0]), b = Integer.parseInt(parts[2]);
        return switch (parts[1]) {
            case "+" -> a + b;
            case "×" -> a * b;
            case "÷" -> a / b;
            case "−" -> a - b;
            default -> throw new IllegalArgumentException(prompt);
        };
    }

    @Test void profileAndBoardUseAuthorizationAndPrivacyDefaults() throws Exception {
        rewards.record(pupil.getId(), StudentRewards.Source.LESSON, "one", "content");
        assertNull(profiles.get(pupil.getEmail()).position());
        assertFalse(profiles.leaderboard(other.getEmail(), null).entries().stream().anyMatch(e -> e.alias().equals("Học Sinh")));
        mvc.perform(get("/api/v1/student/profile")).andExpect(status().isUnauthorized());
        mvc.perform(get("/api/v1/student/profile").with(user("teacher").roles("TEACHER"))).andExpect(status().isForbidden());
        mvc.perform(get("/api/v1/student/leaderboard").with(user(other.getEmail()).roles("STUDENT")).param("classroom", UUID.randomUUID().toString()))
                .andExpect(status().isNotFound());
        mvc.perform(put("/api/v1/student/profile").with(user(pupil.getEmail()).roles("STUDENT")).contentType("application/json")
                .content("{\"displayName\":\"Học Sinh\",\"avatar\":\"moon\",\"leaderboardVisible\":true,\"selectedTitle\":\"master\"}"))
                .andExpect(status().isBadRequest());
        var profile = profiles.update(pupil.getEmail(), new Edit("Sao Sáng", "moon", true, "rookie"));
        assertEquals("Sao Sáng", students.findById(pupil.getId()).orElseThrow().getDisplayName());
        assertEquals("rookie", profile.selectedTitle());
        mvc.perform(get("/api/v1/student/leaderboard").with(user(other.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.entries[?(@.alias == '" + profile.publicAlias() + "')].avatar").value("moon"))
                .andExpect(jsonPath("$.entries[*].email").doesNotExist()).andExpect(jsonPath("$.entries[*].studentId").doesNotExist());
        profiles.update(pupil.getEmail(), new Edit("Sao Sáng", "moon", false, null));
        assertNull(profiles.get(pupil.getEmail()).position());
        assertFalse(profiles.leaderboard(other.getEmail(), null).entries().stream().anyMatch(e -> e.alias().equals(profile.publicAlias())));
    }

    @Test void tiedPositionsAreStableAndChallengerFallsBackWhenAnotherPupilPasses() {
        // Synthetic ranking history goes straight to the test database to exercise all 201 positions.
        transaction.executeWithoutResult(status -> {
            db.update("UPDATE student_profile_preferences SET leaderboard_visible = FALSE");
            for (int i = 1; i <= 201; i++) {
                Student ranked = i == 200 ? pupil : i == 201 ? other : createStudent("@ranking.test");
                UUID id = ranked.getId();
                db.update("INSERT INTO student_profile_preferences(student_id, public_alias, leaderboard_visible) VALUES (?, ?, TRUE)",
                        id, String.format("Rank %03d", i));
                for (int star = 0; star < 162; star++) db.update("""
                        INSERT INTO student_verified_activities VALUES (?, 'LESSON', ?, ?, CURRENT_TIMESTAMP, CURRENT_DATE, 1)
                        """, id, "rank-" + star, "rank-" + star);
            }
            rewards.rememberChallengers();
        });
        assertEquals(200L, profiles.get(pupil.getEmail()).position());
        assertEquals("Thách Đấu", profiles.get(pupil.getEmail()).rank().name());
        assertEquals(201L, profiles.get(other.getEmail()).position());
        assertEquals("Chiến Tướng", profiles.get(other.getEmail()).rank().name());
        db.update("""
                INSERT INTO student_verified_activities VALUES (?, 'QUIZ', 'rank-up', 'rank-up', CURRENT_TIMESTAMP, CURRENT_DATE, 1)
                """, other.getId());
        assertEquals(201L, profiles.get(pupil.getEmail()).position());
        assertEquals("Chiến Tướng", profiles.get(pupil.getEmail()).rank().name());
        assertEquals("Thách Đấu", profiles.get(pupil.getEmail()).highestRank());
    }

    @Test void developmentAccountNeverEarnsStarsOrStartsRankedGame() {
        Student demo = createStudent("@mathvision.local");
        assertEquals(0, rewards.record(demo.getId(), StudentRewards.Source.LESSON, "demo", "demo"));
        assertEquals(0, profiles.get(demo.getEmail()).stats().days());
        assertThrows(com.mathvisionkids.api.common.ApiException.class, () -> games.start(demo.getEmail()));
    }
}

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
        assertEquals(1, profiles.get(owner).stars());
    }

    private int answer(String prompt) {
        String[] parts = prompt.split(" ");
        int a = Integer.parseInt(parts[0]), b = Integer.parseInt(parts[2]);
        return parts[1].equals("+") ? a + b : a - b;
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

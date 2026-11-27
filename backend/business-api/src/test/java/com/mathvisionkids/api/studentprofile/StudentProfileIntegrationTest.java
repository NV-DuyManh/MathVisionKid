package com.mathvisionkids.api.studentprofile;

import com.mathvisionkids.api.quiz.QuizSources;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
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
    @Autowired com.mathvisionkids.api.user.UserRepository users;
    @Autowired StudentRewards rewards;
    @Autowired StudentProfileService profiles;
    @Autowired StudentGameService games;
    @Autowired StudentUsageService usage;
    @Autowired StudentGameUsageService gameUsage;
    @Autowired QuizSources lessons;
    @Autowired JdbcTemplate db;
    @Autowired com.mathvisionkids.api.auth.RefreshTokenService tokens;
    @Autowired com.fasterxml.jackson.databind.ObjectMapper json;
    @Autowired MockMvc mvc;
    @Autowired TransactionTemplate transaction;
    @Autowired PasswordEncoder passwords;
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

    private void configureParentControl(UUID studentId, String pin) {
        db.update("INSERT INTO student_parent_control(student_id, pin_hash) VALUES (?, ?)",
                studentId, passwords.encode(pin));
    }

    @Test void starHistoryPagesThroughOlderAwardsForTheSignedInStudent() throws Exception {
        String insert = """
                INSERT INTO student_verified_activities (student_id, source, event_id, content_id, completed_at, activity_day, stars)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """;
        for (int day = 1; day <= 24; day++) {
            String event = "star-history-" + day;
            db.update(insert, pupil.getId(), "QUIZ", event, event,
                    Timestamp.from(Instant.parse("2026-11-%02dT12:00:00Z".formatted(day))),
                    LocalDate.of(2026, 11, day), 1);
        }
        db.update(insert, pupil.getId(), "QUIZ", "no-star", "no-star",
                Timestamp.from(Instant.parse("2026-11-25T12:00:00Z")), LocalDate.of(2026, 11, 25), 0);
        db.update(insert, other.getId(), "GAME", "other-star", "other-star",
                Timestamp.from(Instant.parse("2026-11-25T12:00:00Z")), LocalDate.of(2026, 11, 25), 1);
        mvc.perform(get("/api/v1/student/star-history").with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.entries.length()").value(10))
                .andExpect(jsonPath("$.entries[0].completedAt").value("2026-11-24T12:00:00Z"))
                .andExpect(jsonPath("$.totalPages").value(3))
                .andExpect(jsonPath("$.page").value(1));
        mvc.perform(get("/api/v1/student/star-history").param("page", "3").with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.entries.length()").value(4))
                .andExpect(jsonPath("$.entries[3].completedAt").value("2026-11-01T12:00:00Z"));
        mvc.perform(get("/api/v1/student/star-history").param("page", "0").with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isBadRequest());
    }

    @Test void studentCannotEnrollParentPinWithoutGuardianVerification() throws Exception {
        mvc.perform(post("/api/v1/student/parent-control/pin")
                        .with(user(pupil.getEmail()).roles("STUDENT"))
                        .contentType("application/json")
                        .content("{\"pin\":\"716025\"}"))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.error.code").value("PARENT_ENROLLMENT_REQUIRED"));
        assertEquals(0, db.queryForObject("SELECT COUNT(*) FROM student_parent_control WHERE student_id = ?",
                Integer.class, pupil.getId()));
    }

    @Test void parentSettingsSyncAcrossRealWebAndNativeSessionsWithoutSharingTheirGrants() throws Exception {
        String base = "/api/v1/student/parent-control";
        String pin = "{\"pin\":\"716025\"}";
        String grantHeader = "X-MathVision-Parent-Grant";
        configureParentControl(pupil.getId(), "716025");
        pupil.setPasswordHash(passwords.encode("parent-control-test-password"));
        students.saveAndFlush(pupil);
        var web = mvc.perform(post("/api/v1/auth/login").secure(true).header("X-MathVision-Web", "portal")
                        .contentType("application/json").content(json.writeValueAsString(java.util.Map.of(
                                "email", pupil.getEmail(), "password", "parent-control-test-password"))))
                .andExpect(status().isOk()).andReturn().getResponse();
        var cookie = web.getCookie("__Host-mvk_portal_session");
        String webId = json.readTree(web.getContentAsString()).get("sessionId").asText();
        var nativeSession = tokens.createSession(pupil.getId());
        String bearer = "Bearer " + nativeSession.getAccessToken();
        var webRequest = (org.springframework.test.web.servlet.request.RequestPostProcessor) request -> {
            request.setSecure(true);
            request.setCookies(cookie);
            request.addHeader("X-MathVision-Web", "portal");
            request.addHeader("X-MathVision-Session", webId);
            return request;
        };
        mvc.perform(get(base + "/settings").with(webRequest))
                .andExpect(status().isForbidden()).andExpect(jsonPath("$.error.code").value("PARENT_GRANT_REQUIRED"));
        mvc.perform(post(base + "/unlock").header("Authorization", bearer).contentType("application/json")
                        .content("{\"pin\":\"000000\"}"))
                .andExpect(status().isForbidden()).andExpect(header().doesNotExist(grantHeader));
        String webGrant = mvc.perform(post(base + "/unlock").with(webRequest).contentType("application/json").content(pin))
                .andExpect(status().isOk()).andExpect(header().exists(grantHeader)).andReturn().getResponse().getHeader(grantHeader);
        String nativeGrant = mvc.perform(post(base + "/unlock").header("Authorization", bearer).contentType("application/json").content(pin))
                .andExpect(status().isOk()).andExpect(header().exists(grantHeader)).andReturn().getResponse().getHeader(grantHeader);
        mvc.perform(get(base + "/settings").header("Authorization", bearer).header(grantHeader, webGrant))
                .andExpect(status().isForbidden());
        mvc.perform(get(base + "/settings").with(webRequest).header(grantHeader, nativeGrant))
                .andExpect(status().isForbidden());
        mvc.perform(get(base + "/settings").header(grantHeader, nativeGrant)).andExpect(status().isUnauthorized());
        mvc.perform(get("/api/v1/me").header("Authorization", "Bearer " + nativeGrant)).andExpect(status().isUnauthorized());
        mvc.perform(put(base + "/daily-limit").header("Authorization", bearer).header(grantHeader, nativeGrant)
                        .contentType("application/json").content("{\"minutes\":1}"))
                .andExpect(status().isBadRequest());
        mvc.perform(put(base + "/daily-limit").with(webRequest).contentType("application/json")
                        .content("{\"pin\":\"716025\",\"minutes\":1}")).andExpect(status().isOk());
        mvc.perform(put(base + "/game-limit").header("Authorization", bearer).contentType("application/json")
                        .content("{\"pin\":\"716025\",\"minutes\":10}")).andExpect(status().isOk());
        var rotated = tokens.rotate(nativeSession.getRefreshToken());
        mvc.perform(get(base + "/settings").header("Authorization", "Bearer " + rotated.getAccessToken())
                        .header(grantHeader, nativeGrant))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control", "no-store"))
                .andExpect(jsonPath("$.dailyMinutes").value(1)).andExpect(jsonPath("$.gameMinutes").value(10));
        mvc.perform(get(base + "/settings").with(webRequest).header(grantHeader, webGrant))
                .andExpect(status().isOk()).andExpect(jsonPath("$.dailyMinutes").value(1))
                .andExpect(jsonPath("$.gameMinutes").value(10));
        var day = java.time.LocalDate.now(StudentRewards.ZONE);
        db.update("INSERT INTO student_usage_day (student_id, usage_day, elapsed_millis) VALUES (?, ?, 60000)", pupil.getId(), day);
        mvc.perform(get(base + "/status").header("Authorization", bearer)).andExpect(status().isOk())
                .andExpect(jsonPath("$.dailyLimitReached").value(true));
        mvc.perform(get(base + "/status").with(webRequest)).andExpect(status().isOk())
                .andExpect(jsonPath("$.dailyLimitReached").value(true));
        String webWeek = mvc.perform(get("/api/v1/student/app-usage/week").with(webRequest))
                .andExpect(status().isOk()).andReturn().getResponse().getContentAsString();
        String mobileWeek = mvc.perform(get("/api/v1/student/app-usage/week").header("Authorization", bearer))
                .andExpect(status().isOk()).andReturn().getResponse().getContentAsString();
        assertEquals(json.readTree(webWeek), json.readTree(mobileWeek));
    }

    @Test void statusWithoutParentControlPreservesUnconfiguredResponse() throws Exception {
        mvc.perform(get("/api/v1/student/parent-control/status").with(user("no-profile@example.test").roles("STUDENT")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.pinConfigured").value(false))
                .andExpect(jsonPath("$.dailyLimitConfigured").value(false));
    }

    @Test void expiredAppConnectionsAccountForBoundedTimeWithoutDoubleCounting() {
        var start = java.time.LocalDate.of(2026, 11, 16).atStartOfDay(StudentRewards.ZONE).toInstant();
        var id = pupil.getId();
        var first = UUID.randomUUID();
        var second = UUID.randomUUID();
        usage.observeLocked(id, first, true, start);
        usage.observeLocked(id, second, true, start.plusSeconds(5));
        // Both clients disappear without sending a stop or a second heartbeat.
        usage.observeLocked(id, UUID.randomUUID(), true, start.plusSeconds(50));
        assertEquals(15_000, usage.weekFor(id, java.time.LocalDate.of(2026, 11, 16)).totalMillis());
    }

    @Test void statusAccountsExpiredConnectionBeforeCheckingDailyLimit() throws Exception {
        var account = user(pupil.getEmail()).roles("STUDENT");
        configureParentControl(pupil.getId(), "716025");
        mvc.perform(put("/api/v1/student/parent-control/daily-limit").with(account).contentType("application/json")
                .content("{\"pin\":\"716025\",\"minutes\":1}")).andExpect(status().isOk());
        var day = java.time.LocalDate.now(StudentRewards.ZONE);
        db.update("INSERT INTO student_usage_day (student_id, usage_day, elapsed_millis) VALUES (?, ?, ?)", pupil.getId(), day, 55_000);
        db.update("INSERT INTO student_usage_connection (student_id, connection_id, last_seen_at) VALUES (?, ?, ?)", pupil.getId(), UUID.randomUUID(), java.sql.Timestamp.from(java.time.Instant.now().minusSeconds(50)));
        mvc.perform(get("/api/v1/student/parent-control/status").with(account))
                .andExpect(status().isOk()).andExpect(jsonPath("$.dailyLimitReached").value(true));
    }

    @Test void appUsageCountsOverlappingConnectionsOnceAndSplitsAtVietnamMidnight() throws Exception {
        var monday = java.time.LocalDate.of(2026, 11, 16);
        var midnight = monday.atStartOfDay(StudentRewards.ZONE).toInstant();
        UUID first = UUID.randomUUID(), second = UUID.randomUUID(), student = pupil.getId();
        usage.observeLocked(student, first, true, midnight.minusSeconds(8));
        usage.observeLocked(student, second, true, midnight.minusSeconds(4));
        usage.observeLocked(student, second, true, midnight.plusSeconds(4));
        usage.observeLocked(student, first, false, midnight.plusSeconds(8));
        usage.observeLocked(student, second, true, midnight.plusSeconds(60));
        usage.observeLocked(student, second, false, midnight.plusSeconds(65));

        assertEquals(8_000, usage.weekFor(student, monday.minusDays(1)).totalMillis());
        var week = usage.weekFor(student, monday);
        assertEquals(19_000, week.totalMillis());
        assertEquals(19_000, week.days().getFirst().elapsedMillis());
        assertEquals(7, week.days().size());
        assertEquals(0, usage.weekFor(other.getId(), monday).totalMillis());
        mvc.perform(get("/api/v1/student/app-usage/week")).andExpect(status().isUnauthorized());
        mvc.perform(get("/api/v1/student/app-usage/week").with(user(pupil.getEmail()).roles("TEACHER")))
                .andExpect(status().isForbidden());
        mvc.perform(get("/api/v1/student/app-usage/week").with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control", "no-store"))
                .andExpect(jsonPath("$.days.length()").value(7));
    }

    @Test void parentPinGuardsSharedLimitAndLearningApiStopsAtDailyThreshold() throws Exception {
        var account = user(pupil.getEmail()).roles("STUDENT");
        String base = "/api/v1/student/parent-control";
        String pin = "{\"pin\":\"716025\"}";
        String cap = "{\"pin\":\"716025\",\"minutes\":1}";
        configureParentControl(pupil.getId(), "716025");
        mvc.perform(put(base + "/daily-limit").with(account).contentType("application/json")
                        .content("{\"pin\":\"000000\",\"minutes\":1}"))
                .andExpect(status().isForbidden());
        mvc.perform(put(base + "/daily-limit").with(account).contentType("application/json").content(cap))
                .andExpect(status().isOk());
        mvc.perform(post("/api/v1/student/game-runs").with(account))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.error.code").value("STUDENT_ACTIVITY_REQUIRED"));
        UUID connection = UUID.randomUUID();
        mvc.perform(post("/api/v1/student/app-usage/heartbeat").with(account).contentType("application/json")
                        .content("{\"connectionId\":\"" + connection + "\",\"active\":true}"))
                .andExpect(status().isNoContent());
        mvc.perform(post("/api/v1/student/game-runs").with(account)).andExpect(status().isOk());
        db.update("UPDATE student_usage_connection SET last_seen_at = ? WHERE student_id = ?",
                java.sql.Timestamp.from(java.time.Instant.now().minusSeconds(60)), pupil.getId());
        mvc.perform(post("/api/v1/student/game-runs").with(account))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.error.code").value("STUDENT_ACTIVITY_REQUIRED"));
        String stored = db.queryForObject("SELECT pin_hash FROM student_parent_control WHERE student_id = ?", String.class, pupil.getId());
        assertNotEquals("716025", stored);
        var day = java.time.LocalDate.now(StudentRewards.ZONE);
        db.update("DELETE FROM student_usage_day WHERE student_id = ?", pupil.getId());
        db.update("INSERT INTO student_usage_day (student_id, usage_day, elapsed_millis) VALUES (?, ?, 59999)", pupil.getId(), day);
        mvc.perform(get(base + "/status").with(account)).andExpect(status().isOk())
                .andExpect(jsonPath("$.dailyLimitReached").value(false));
        db.update("UPDATE student_usage_day SET elapsed_millis = 60000 WHERE student_id = ? AND usage_day = ?", pupil.getId(), day);
        mvc.perform(get(base + "/status").with(account)).andExpect(status().isOk())
                .andExpect(jsonPath("$.dailyLimitReached").value(true));
        mvc.perform(get(base + "/status").with(user(other.getEmail()).roles("STUDENT"))).andExpect(status().isOk())
                .andExpect(jsonPath("$.pinConfigured").value(false));
        mvc.perform(post("/api/v1/student/game-runs").with(account)).andExpect(status().isTooManyRequests())
                .andExpect(jsonPath("$.error.code").value("STUDENT_DAILY_LIMIT"));
        mvc.perform(post(base + "/unlock").with(account).contentType("application/json").content(pin))
                .andExpect(status().isOk()).andExpect(jsonPath("$.dailyMinutes").value(1));
        mvc.perform(put(base + "/daily-limit").with(account).contentType("application/json")
                        .content("{\"pin\":\"716025\",\"minutes\":null}"))
                .andExpect(status().isOk());
        mvc.perform(post("/api/v1/student/game-runs").with(account)).andExpect(status().isOk());

        for (int attempt = 0; attempt < 4; attempt++) {
            mvc.perform(post(base + "/unlock").with(account).contentType("application/json").content("{\"pin\":\"000000\"}"))
                    .andExpect(status().isForbidden());
        }
        mvc.perform(post(base + "/unlock").with(account).contentType("application/json").content("{\"pin\":\"000000\"}"))
                .andExpect(status().isTooManyRequests());
        mvc.perform(post(base + "/unlock").with(account).contentType("application/json").content(pin))
                .andExpect(status().isTooManyRequests());
    }

    @Test void gameTimeLimitRequiresPinAndBlocksGameApiWithoutBlockingOtherStudentApis() throws Exception {
        var account = user(pupil.getEmail()).roles("STUDENT");
        var differentAccount = user(other.getEmail()).roles("STUDENT");
        String parent = "/api/v1/student/parent-control";
        String heartbeat = "/api/v1/student/app-usage/game-heartbeat";
        String gameStatus = "/api/v1/student/app-usage/game-status";
        String active = "{\"connectionId\":\"" + UUID.randomUUID() + "\",\"active\":true}";
        mvc.perform(post(heartbeat).contentType("application/json").content(active))
                .andExpect(status().isUnauthorized());
        mvc.perform(post(heartbeat).with(user(pupil.getEmail()).roles("TEACHER")).contentType("application/json").content(active))
                .andExpect(status().isForbidden());
        configureParentControl(pupil.getId(), "716025");
        mvc.perform(put(parent + "/game-limit").with(account).contentType("application/json")
                        .content("{\"pin\":\"000000\",\"minutes\":1}"))
                .andExpect(status().isForbidden());
        mvc.perform(put(parent + "/game-limit").with(account).contentType("application/json")
                        .content("{\"pin\":\"716025\",\"minutes\":0}"))
                .andExpect(status().isBadRequest());
        mvc.perform(put(parent + "/game-limit").with(account).contentType("application/json")
                        .content("{\"pin\":\"716025\",\"minutes\":1}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.gameMinutes").value(1))
                .andExpect(jsonPath("$.dailyMinutes").isEmpty());
        mvc.perform(post("/api/v1/student/game-runs").with(account))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.error.code").value("STUDENT_GAME_ACTIVITY_REQUIRED"));
        mvc.perform(get(gameStatus)).andExpect(status().isUnauthorized());
        mvc.perform(get(gameStatus).with(account)).andExpect(status().isOk())
                .andExpect(header().string("Cache-Control", "no-store"))
                .andExpect(jsonPath("$.gameLimitReached").value(false));
        mvc.perform(post("/api/v1/student/game-runs").with(account)).andExpect(status().isServiceUnavailable());
        mvc.perform(post(heartbeat).with(account).contentType("application/json").content(active))
                .andExpect(status().isOk())
                .andExpect(header().string("Cache-Control", "no-store"))
                .andExpect(jsonPath("$.remainingMillis").value(60000))
                .andExpect(jsonPath("$.leaseMillis").value(10000))
                .andExpect(jsonPath("$.gameLimitReached").value(false));
        mvc.perform(post("/api/v1/student/game-runs").with(account)).andExpect(status().isOk());
        var day = java.time.LocalDate.now(StudentRewards.ZONE);
        db.update("DELETE FROM student_game_usage_day WHERE student_id = ?", pupil.getId());
        db.update("INSERT INTO student_game_usage_day (student_id, usage_day, elapsed_millis) VALUES (?, ?, 60000)",
                pupil.getId(), day);
        mvc.perform(post(heartbeat).with(account).contentType("application/json").content(active))
                .andExpect(status().isOk()).andExpect(jsonPath("$.leaseMillis").value(0))
                .andExpect(jsonPath("$.gameLimitReached").value(true));
        mvc.perform(get(gameStatus).with(account)).andExpect(status().isOk())
                .andExpect(jsonPath("$.gameLimitReached").value(true));
        mvc.perform(get(gameStatus).with(differentAccount)).andExpect(status().isOk())
                .andExpect(jsonPath("$.gameLimitReached").value(false));
        mvc.perform(post("/api/v1/student/game-runs").with(account))
                .andExpect(status().isTooManyRequests())
                .andExpect(jsonPath("$.error.code").value("STUDENT_GAME_LIMIT"));
        mvc.perform(get("/api/v1/student/rank-milestones").with(account)).andExpect(status().isOk());
        mvc.perform(post("/api/v1/student/game-runs").with(differentAccount)).andExpect(status().isOk());
        mvc.perform(get("/api/v1/student/app-usage/week").with(account))
                .andExpect(status().isOk()).andExpect(jsonPath("$.days[" + (day.getDayOfWeek().getValue() - 1) + "].gameElapsedMillis")
                        .value(org.hamcrest.Matchers.greaterThanOrEqualTo(60000)));
        mvc.perform(put(parent + "/game-limit").with(account).contentType("application/json")
                        .content("{\"pin\":\"716025\",\"minutes\":null}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.gameMinutes").isEmpty());
        mvc.perform(post("/api/v1/student/game-runs").with(account)).andExpect(status().isOk());
    }

    @Test void gameTimeUsesServerLeasesAndCountsConcurrentDevicesOnlyOnce() {
        var day = java.time.LocalDate.of(2026, 11, 16);
        var midnight = day.atStartOfDay(StudentRewards.ZONE).toInstant();
        var id = pupil.getId();
        UUID first = UUID.randomUUID(), second = UUID.randomUUID();
        assertEquals(8_000, gameUsage.observeLocked(id, first, true, midnight.minusSeconds(8)).leaseMillis());
        assertEquals(4_000, gameUsage.observeLocked(id, second, true, midnight.minusSeconds(4)).leaseMillis());
        assertEquals(0, gameUsage.observeLocked(id, first, false, midnight.minusSeconds(2)).leaseMillis());
        gameUsage.observeLocked(id, first, true, midnight.plusSeconds(2));
        gameUsage.observeLocked(id, second, true, midnight.plusSeconds(6));
        gameUsage.observeLocked(id, first, false, midnight.plusSeconds(8));
        gameUsage.observeLocked(id, second, true, midnight.plusSeconds(60));
        gameUsage.observeLocked(id, second, false, midnight.plusSeconds(65));

        assertEquals(8_000, usage.weekFor(id, day.minusDays(1)).days().getLast().gameElapsedMillis());
        assertEquals(19_000, usage.weekFor(id, day).days().getFirst().gameElapsedMillis());
        assertEquals(0, usage.weekFor(id, day).totalMillis());
        assertEquals(0, usage.weekFor(other.getId(), day).days().getFirst().gameElapsedMillis());

        db.update("INSERT INTO student_parent_control(student_id, pin_hash, game_minutes) VALUES (?, ?, ?)",
                id, "unused-test-hash", 1);
        db.update("UPDATE student_game_usage_day SET elapsed_millis = 59500 WHERE student_id = ? AND usage_day = ?",
                id, day);
        assertEquals(500, gameUsage.observeLocked(id, first, true, midnight.plusSeconds(65)).leaseMillis());
        var reached = gameUsage.observeLocked(id, first, true, midnight.plusSeconds(66));
        assertEquals(0, reached.leaseMillis());
        assertEquals(0L, reached.remainingMillis());
        assertTrue(reached.gameLimitReached());
        assertEquals(60_000, usage.weekFor(id, day).days().getFirst().gameElapsedMillis());
    }

    @Test void initialAvatarIsPersistedOnceAndExistingChoicesArePreserved() {
        profiles.initialize(pupil.getId());
        String initial = profiles.get(pupil.getEmail()).avatar();
        assertTrue(StudentProfileService.AVATARS.contains(initial));
        for (int i = 0; i < 3; i++) {
            profiles.initialize(pupil.getId());
            assertEquals(initial, profiles.get(pupil.getEmail()).avatar());
        }
        String chosen = initial.equals("moon") ? "planet" : "moon";
        profiles.update(pupil.getEmail(), new Edit("Học Sinh", chosen, false, null));
        profiles.initialize(pupil.getId());
        assertEquals(chosen, profiles.get(pupil.getEmail()).avatar());
        assertEquals(1, db.queryForObject("SELECT COUNT(*) FROM student_profile_preferences WHERE student_id = ?", Integer.class, pupil.getId()));
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
        for (int i = 2; i <= 8; i++) {
            assertEquals(1, rewards.record(id, StudentRewards.Source.QUIZ, "event-" + i, "quiz-" + i));
        }
        var profile = profiles.get(pupil.getEmail());
        assertEquals(8, profile.stars());
        assertEquals(8, profile.stats().quizzes());
    }

    @Test void simultaneousLessonQuizAndGameRewardsShareTheDailyLimit() throws Exception {
        UUID id = pupil.getId();
        for (int i = 0; i < 9; i++) {
            assertEquals(1, rewards.record(id, StudentRewards.Source.LESSON, "lesson-" + i, "lesson-" + i));
        }

        try (var pool = Executors.newFixedThreadPool(3)) {
            var gate = new CountDownLatch(1);
            List<Future<Integer>> awards = new java.util.ArrayList<>();
            for (var source : StudentRewards.Source.values()) {
                awards.add(pool.submit(() -> {
                    gate.await();
                    return rewards.record(id, source, "last-star", "last-content");
                }));
            }
            gate.countDown();
            int granted = 0;
            for (var award : awards) granted += award.get(15, TimeUnit.SECONDS);
            assertEquals(1, granted);
        }

        var profile = profiles.get(pupil.getEmail());
        assertEquals(10, profile.stars());
        assertEquals(12, profile.stats().today());
        assertEquals(10, profile.stats().lessons());
        assertEquals(1, profile.stats().quizzes());
        assertEquals(1, profile.stats().games());
        assertEquals(1, rewards.record(other.getId(), StudentRewards.Source.QUIZ, "last-star", "last-content"));

        Game game = games.start(pupil.getEmail());
        while (!game.completed()) {
            var request = new GameAnswer(game.question(), answer(game.prompt()));
            Game result = games.answer(pupil.getEmail(), game.id(), request);
            assertEquals(result, games.answer(pupil.getEmail(), game.id(), request));
            game = result;
        }
        assertEquals(5, game.correct());
        assertEquals(0, game.stars());
        assertEquals(GameRewardStatus.DAILY_LIMIT, game.rewardStatus());
        assertEquals(game, games.get(pupil.getEmail(), game.id()));
        assertEquals(10, profiles.get(pupil.getEmail()).stars());
    }

    @Test void existingStarsStayIntactAndTheLimitResetsAtVietnamMidnight() {
        UUID id = pupil.getId();
        Instant beforeMidnight = Instant.parse("2026-11-26T16:59:59Z");
        Instant midnight = beforeMidnight.plusSeconds(1);
        for (int i = 0; i < 12; i++) {
            db.update("""
                    INSERT INTO student_verified_activities(student_id, source, event_id, content_id, completed_at, activity_day, stars)
                    VALUES (?, 'LESSON', ?, ?, ?, ?, 1)
                    """, id, "historical-" + i, "content-" + i, Timestamp.from(beforeMidnight), LocalDate.of(2026, 11, 26));
        }

        transaction.executeWithoutResult(tx -> {
            rewards.lock();
            var capped = rewards.recordAward(id, StudentRewards.Source.GAME, "capped-game", "game-content", beforeMidnight);
            assertEquals(new StudentRewards.Award(0, GameRewardStatus.DAILY_LIMIT), capped);
            assertEquals(12, profiles.get(pupil.getEmail()).stars());
            assertEquals(0, rewards.recordLocked(id, StudentRewards.Source.GAME, "capped-game", "game-content", midnight));
            assertEquals(new StudentRewards.Award(1, GameRewardStatus.AWARDED),
                    rewards.recordAward(id, StudentRewards.Source.GAME, "next-game", "game-content", midnight));
        });
        assertEquals(13, profiles.get(pupil.getEmail()).stars());
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

    @Test void raceChallengeAwardsAStarAfterThreeOtherWins() {
        for (int i = 0; i < 3; i++) {
            rewards.record(pupil.getId(), StudentRewards.Source.GAME, "existing-" + i, "game-" + i);
        }
        String owner = pupil.getEmail();
        Game game = games.start(owner, GameMode.RACE_TO_FINISH);
        while (!game.completed()) {
            game = games.answer(owner, game.id(), new GameAnswer(game.question(), answer(game.prompt())));
        }
        assertEquals(1, game.stars());
        assertEquals(GameRewardStatus.AWARDED, game.rewardStatus());
        assertEquals(game, games.get(owner, game.id()));
        assertEquals(4, profiles.get(owner).stats().games());
    }

    @Test void thirteenthRankedGameRunIsRejectedWithoutAffectingAnotherStudent() throws Exception {
        String owner = pupil.getEmail();
        for (int i = 0; i < 12; i++) {
            Game game = games.start(owner, GameMode.ARITHMETIC_QUEST);
            while (!game.completed()) {
                game = games.answer(owner, game.id(), new GameAnswer(game.question(), answer(game.prompt())));
            }
        }
        mvc.perform(post("/api/v1/student/game-runs").with(user(owner).roles("STUDENT")))
                .andExpect(status().isTooManyRequests()).andExpect(jsonPath("$.error.code").value("GAME_LIMIT"));
        assertFalse(games.start(other.getEmail(), GameMode.ARITHMETIC_QUEST).completed());
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

    @Test void everyTrainingModeGradesItsOwnQuestionsAndAwardsAStar() {
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
            assertEquals(GameRewardStatus.AWARDED, game.rewardStatus());
        }
        var profile = profiles.get(owner);
        assertEquals(4, profile.stars());
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

    @Test void singleRankPreservesProgressAndIgnoresRetiredTitle() throws Exception {
        var first = profiles.get(pupil.getEmail());
        assertEquals("Sắt III", first.rank().name());
        assertEquals(0, first.stars());
        rewards.record(pupil.getId(), StudentRewards.Source.LESSON, "single-rank-first", "content");
        var before = profiles.get(pupil.getEmail());
        assertEquals("Sắt III", before.rank().name());
        db.update("UPDATE student_profile_preferences SET selected_title = ? WHERE student_id = ?", "luyen-khi", pupil.getId());
        var after = profiles.update(pupil.getEmail(), new Edit("Sao Sáng", "moon", false, "rookie"));
        assertNull(after.selectedTitle());
        assertTrue(after.titles().isEmpty());
        assertEquals("luyen-khi", db.queryForObject("SELECT selected_title FROM student_profile_preferences WHERE student_id = ?", String.class, pupil.getId()));
        assertEquals(before.stars(), after.stars());
        assertEquals(before.history(), after.history());
        assertEquals(before.rank(), after.rank());
        mvc.perform(get("/api/v1/student/profile").header("X-MathVision-Client", "student-rank-v2").with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.achievement").doesNotExist())
                .andExpect(jsonPath("$.rank.name").value("Sắt III"));
        mvc.perform(get("/api/v1/student/rank-milestones").header("X-MathVision-Client", "student-rank-v2").with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.length()").value(26))
                .andExpect(jsonPath("$[0].scheme").value(2));
        mvc.perform(get("/api/v1/student/profile").with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.rank.name").value("Đồng III"))
                .andExpect(jsonPath("$.rank.scheme").value(1));
        mvc.perform(get("/api/v1/student/rank-milestones").with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$[0].name").value("Đồng"))
                .andExpect(jsonPath("$[0].scheme").value(1));
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
                .andExpect(status().isOk());
        var profile = profiles.update(pupil.getEmail(), new Edit("Sao Sáng", "moon", true, "rookie"));
        assertEquals("Sao Sáng", students.findById(pupil.getId()).orElseThrow().getDisplayName());
        assertNull(profile.selectedTitle());
        mvc.perform(get("/api/v1/student/leaderboard").with(user(other.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.entries[?(@.alias == '" + profile.publicAlias() + "')].avatar").value("moon"))
                .andExpect(jsonPath("$.entries[*].email").doesNotExist()).andExpect(jsonPath("$.entries[*].studentId").doesNotExist());
        profiles.update(pupil.getEmail(), new Edit("Sao Sáng", "moon", false, null));
        assertNull(profiles.get(pupil.getEmail()).position());
        assertFalse(profiles.leaderboard(other.getEmail(), null).entries().stream().anyMatch(e -> e.alias().equals(profile.publicAlias())));
    }

    @Test void displayNameAcceptsDigitsAndEnforcesFiftyWords() throws Exception {
        String maximum = String.join("  ", java.util.Collections.nCopies(50, "5Nguyễn"));
        for (String valid : List.of("123", maximum)) {
            mvc.perform(put("/api/v1/student/profile").with(user(pupil.getEmail()).roles("STUDENT"))
                            .contentType("application/json").content(json.writeValueAsString(new Edit(valid, "moon", false, null))))
                    .andExpect(status().isOk()).andExpect(jsonPath("$.displayName").value(valid));
        }
        for (String invalid : List.of(maximum + " 51", "Học sinh #5")) {
            mvc.perform(put("/api/v1/student/profile").with(user(pupil.getEmail()).roles("STUDENT"))
                            .contentType("application/json").content(json.writeValueAsString(new Edit(invalid, "moon", false, null))))
                    .andExpect(status().isBadRequest());
        }
        assertEquals(maximum, students.findById(pupil.getId()).orElseThrow().getDisplayName());
    }

    @Test void tiedPositionsAreStableAndChallengerFallsBackWhenAnotherPupilPasses() throws Exception {
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
        assertEquals("Huyền Thoại", profiles.get(pupil.getEmail()).rank().name());
        assertEquals(201L, profiles.get(other.getEmail()).position());
        assertEquals("Thách Đấu", profiles.get(other.getEmail()).rank().name());
        // Position 201 enters the Top 200 and then drops out without ever opening
        // their profile or making an award during that interval.
        var admin = new com.mathvisionkids.api.user.User();
        admin.setEmail(UUID.randomUUID() + "@admin-ranking.test");
        admin.setPasswordHash("unused");
        admin.setRole("ADMIN");
        admin.setDisplayName("Test Admin");
        users.saveAndFlush(admin);
        var adminRequest = user(admin.getEmail()).roles("ADMIN");
        mvc.perform(post("/api/v1/admin/users/" + pupil.getId() + "/disable").with(adminRequest))
                .andExpect(status().isOk());
        mvc.perform(post("/api/v1/admin/users/" + pupil.getId() + "/enable").with(adminRequest))
                .andExpect(status().isOk());
        var former = profiles.get(other.getEmail());
        assertEquals(201L, former.position());
        assertEquals("Thách Đấu", former.rank().name());
        assertEquals("Huyền Thoại", former.highestRank());
        mvc.perform(get("/api/v1/student/profile").with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.rank.name").value("Thách Đấu"));
        mvc.perform(get("/api/v1/student/profile").with(user(other.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.rank.name").value("Chiến Tướng"));
        mvc.perform(get("/api/v1/student/profile").header("X-MathVision-Client", "student-rank-v2")
                        .with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.rank.name").value("Huyền Thoại"));
        mvc.perform(get("/api/v1/student/leaderboard").param("allGrades", "true").with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.entries[199].rank.name").value("Thách Đấu"));
        mvc.perform(get("/api/v1/student/leaderboard").param("allGrades", "true").header("X-MathVision-Client", "student-rank-v2")
                        .with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.entries[199].rank.name").value("Huyền Thoại"));
        db.update("""
                INSERT INTO student_verified_activities VALUES (?, 'QUIZ', 'rank-up', 'rank-up', CURRENT_TIMESTAMP, CURRENT_DATE, 1)
                """, other.getId());
        assertEquals(201L, profiles.get(pupil.getEmail()).position());
        assertEquals("Thách Đấu", profiles.get(pupil.getEmail()).rank().name());
        assertEquals("Huyền Thoại", profiles.get(pupil.getEmail()).highestRank());
        mvc.perform(get("/api/v1/student/profile").with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.rank.name").value("Chiến Tướng"))
                .andExpect(jsonPath("$.highestRank").value("Thách Đấu"));
        var hidden = profiles.update(pupil.getEmail(), new Edit("Sao Sáng", "moon", false, null));
        assertNull(hidden.position());
        assertEquals("Thách Đấu", hidden.rank().name());
        assertEquals("Huyền Thoại", hidden.highestRank());
        assertFalse(hidden.leaderboardVisible());
    }

    @Test void explicitVisibleNameSurvivesHttpSaveAndSubsequentProfileReads() throws Exception {
        String body = "{\"displayName\":\"Minh Anh\",\"avatar\":\"moon\",\"leaderboardVisible\":true,\"leaderboardNameHidden\":false,\"selectedTitle\":null}";
        for (int i = 0; i < 2; i++) {
            mvc.perform(put("/api/v1/student/profile").with(user(pupil.getEmail()).roles("STUDENT")).contentType("application/json").content(body))
                    .andExpect(status().isOk()).andExpect(jsonPath("$.leaderboardVisible").value(true))
                    .andExpect(jsonPath("$.leaderboardNameHidden").value(false));
            mvc.perform(get("/api/v1/student/profile").with(user(pupil.getEmail()).roles("STUDENT")))
                    .andExpect(status().isOk()).andExpect(jsonPath("$.leaderboardNameHidden").value(false));
        }
        assertFalse(db.queryForObject("SELECT leaderboard_name_hidden FROM student_profile_preferences WHERE student_id = ?", Boolean.class, pupil.getId()));
    }

    @Test void nameOnlyHttpUpdatePreservesCurrentLeaderboardPrivacy() throws Exception {
        profiles.captureGoogleAvatar(pupil.getId(), "https://lh3.googleusercontent.com/a/synthetic-profile");
        profiles.update(pupil.getEmail(), new Edit("Minh Anh", "moon", true, null, false, false, true));
        String body = """
                {"displayName":"Sao Sáng","avatar":"moon"}
                """;
        mvc.perform(put("/api/v1/student/profile").with(user(pupil.getEmail()).roles("STUDENT")).contentType("application/json").content(body))
                .andExpect(status().isOk()).andExpect(jsonPath("$.displayName").value("Sao Sáng"))
                .andExpect(jsonPath("$.leaderboardVisible").value(true))
                .andExpect(jsonPath("$.leaderboardNameHidden").value(false))
                .andExpect(jsonPath("$.leaderboardPhotoVisible").value(true));

        profiles.update(pupil.getEmail(), new Edit("Sao Sáng", "moon", false, null, false, true, false));
        mvc.perform(put("/api/v1/student/profile").with(user(pupil.getEmail()).roles("STUDENT")).contentType("application/json").content(body))
                .andExpect(status().isOk()).andExpect(jsonPath("$.leaderboardVisible").value(false))
                .andExpect(jsonPath("$.leaderboardNameHidden").value(true))
                .andExpect(jsonPath("$.leaderboardPhotoVisible").value(false));
    }

    @Test void namePrivacyDoesNotRemoveEntryAndBoardUsesRegisteredGrade() {
        pupil.setGradeLevel(5);
        other.setGradeLevel(5);
        students.saveAndFlush(pupil);
        students.saveAndFlush(other);
        rewards.record(pupil.getId(), StudentRewards.Source.LESSON, "private", "private-content");
        var privateProfile = profiles.update(pupil.getEmail(), new Edit("Minh Anh", "moon", true, null));
        assertTrue(privateProfile.leaderboardNameHidden());
        assertTrue(StudentAnimalAliases.ANIMALS.contains(privateProfile.publicAlias())
                || privateProfile.publicAlias().matches(".+ \\d+"));
        var board = profiles.leaderboard(other.getEmail(), null);
        assertEquals(5, board.gradeLevel());
        assertTrue(board.entries().stream().anyMatch(entry -> entry.alias().equals(privateProfile.publicAlias())));
        profiles.update(pupil.getEmail(), new Edit("Minh Anh", "moon", true, null, false, false));
        assertTrue(profiles.leaderboard(other.getEmail(), null).entries().stream().anyMatch(entry -> entry.alias().equals("Minh Anh")));
        assertFalse(profiles.update(pupil.getEmail(), new Edit("Minh Anh", "moon", true, null)).leaderboardNameHidden());
        assertEquals(privateProfile.publicAlias(), profiles.get(pupil.getEmail()).publicAlias());
        db.update("UPDATE users SET display_name = ? WHERE id = ?", "old-account@example.com", pupil.getId());
        assertTrue(profiles.leaderboard(other.getEmail(), null).entries().stream().anyMatch(entry -> entry.alias().equals(privateProfile.publicAlias())));
        other.setGradeLevel(4);
        students.saveAndFlush(other);
        assertEquals(4, profiles.leaderboard(other.getEmail(), null).gradeLevel());
        assertFalse(profiles.leaderboard(other.getEmail(), null).entries().stream().anyMatch(entry -> entry.alias().equals("Minh Anh")));
    }

    @Test void ranksAcrossGradesAndHonorsPrivacy() throws Exception {
        pupil.setGradeLevel(5);
        students.saveAndFlush(pupil);
        rewards.record(pupil.getId(), StudentRewards.Source.LESSON, "rank-5", "rank-5");
        rewards.record(pupil.getId(), StudentRewards.Source.LESSON, "rank-5-extra", "rank-5-extra");
        rewards.record(other.getId(), StudentRewards.Source.LESSON, "rank-3", "rank-3");
        var gradeFive = profiles.update(pupil.getEmail(), new Edit("Tên lớp năm", "moon", true, null, false, true));
        var gradeThree = profiles.update(other.getEmail(), new Edit("Tên lớp ba", "star", true, null, false, true));

        var all = profiles.leaderboard(other.getEmail(), null, true);
        var firstStudent = all.entries().stream().filter(entry -> entry.alias().equals(gradeFive.publicAlias())).findFirst().orElseThrow();
        var own = all.entries().stream().filter(Entry::self).findFirst().orElseThrow();
        assertEquals(gradeThree.publicAlias(), own.alias());
        assertEquals(own.position(), all.ownPosition());
        assertTrue(firstStudent.position() < own.position());
        assertFalse(profiles.leaderboard(other.getEmail(), null).entries().contains(firstStudent));
        mvc.perform(get("/api/v1/student/leaderboard").param("allGrades", "true")
                        .with(user(other.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.ownPosition").value(own.position()))
                .andExpect(jsonPath("$.gradeLevel").doesNotExist())
                .andExpect(jsonPath("$.entries[?(@.alias == '%s')]".formatted(gradeFive.publicAlias())).isNotEmpty());
        mvc.perform(get("/api/v1/student/leaderboard").param("allGrades", "true")
                        .param("classroom", UUID.randomUUID().toString()).with(user(other.getEmail()).roles("STUDENT")))
                .andExpect(status().isBadRequest());

        profiles.update(pupil.getEmail(), new Edit("Tên lớp năm", "moon", false, null));
        assertFalse(profiles.leaderboard(other.getEmail(), null, true).entries().stream()
                .anyMatch(entry -> entry.alias().equals(gradeFive.publicAlias())));
        assertNull(profiles.leaderboard(pupil.getEmail(), null, true).ownPosition());
    }

    @Test void legacyAliasesAreReplacedOnFirstProfileReadAndConcurrentReadsKeepOneAlias() throws Exception {
        db.update("INSERT INTO student_profile_preferences(student_id, public_alias) VALUES (?, ?)", pupil.getId(), "Sao abcdef123456");
        String alias = profiles.get(pupil.getEmail()).publicAlias();
        assertFalse(alias.startsWith("Sao abcdef"));
        try (var pool = Executors.newFixedThreadPool(4)) {
            var gate = new CountDownLatch(1);
            var responses = new java.util.ArrayList<Future<String>>();
            for (int i = 0; i < 4; i++) responses.add(pool.submit(() -> {
                gate.await();
                return profiles.get(other.getEmail()).publicAlias();
            }));
            gate.countDown();
            String otherAlias = responses.getFirst().get(15, TimeUnit.SECONDS);
            assertNotEquals(alias, otherAlias);
            for (var response : responses) assertEquals(otherAlias, response.get(15, TimeUnit.SECONDS));
        }
    }

    @Test void concurrentNewProfilesAllocateDifferentAnimalNames() throws Exception {
        var emails = new java.util.ArrayList<String>();
        for (int i = 0; i < 6; i++) emails.add(createStudent("@alias.profile.test").getEmail());
        try (var pool = Executors.newFixedThreadPool(6)) {
            var gate = new CountDownLatch(1);
            var responses = emails.stream().map(email -> pool.submit(() -> {
                gate.await();
                return profiles.get(email).publicAlias();
            })).toList();
            gate.countDown();
            var aliases = new java.util.HashSet<String>();
            for (var response : responses) assertTrue(aliases.add(response.get(15, TimeUnit.SECONDS)));
        }
    }

    @Test void developmentAccountNeverEarnsStarsOrStartsRankedGame() {
        Student demo = createStudent("@mathvision.local");
        assertEquals(0, rewards.record(demo.getId(), StudentRewards.Source.LESSON, "demo", "demo"));
        assertEquals(0, profiles.get(demo.getEmail()).stats().days());
        assertThrows(com.mathvisionkids.api.common.ApiException.class, () -> games.start(demo.getEmail()));
    }
}

package com.mathvisionkids.api.studentprofile;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.sql.DriverManager;
import java.time.Duration;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.transaction.support.TransactionTemplate;

import static org.awaitility.Awaitility.await;
import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(properties = {
        "spring.datasource.driver-class-name=org.postgresql.Driver",
        "spring.jpa.hibernate.ddl-auto=validate",
        "spring.jpa.database-platform=org.hibernate.dialect.PostgreSQLDialect",
        "spring.jpa.defer-datasource-initialization=false",
        "spring.sql.init.mode=never",
        "spring.flyway.enabled=true",
        "spring.flyway.baseline-on-migrate=false"
})
@ActiveProfiles("test")
@EnabledIfEnvironmentVariable(named = "MATHVISION_POSTGRES_PROFILE_CONCURRENCY", matches = "true")
class StudentProfilePostgresConcurrencyTest {
    private static final String SCHEMA = "profile_test_" + UUID.randomUUID().toString().replace("-", "");
    private static final String ORIGINAL_PHOTO = "https://lh3.googleusercontent.com/a/previous-avatar";

    @Autowired StudentRepository students;
    @Autowired StudentProfileService profiles;
    @Autowired StudentAccountService account;
    @Autowired StudentRewards rewards;
    @Autowired JdbcTemplate db;
    @Autowired TransactionTemplate transactions;

    @DynamicPropertySource
    static void postgres(DynamicPropertyRegistry properties) {
        properties.add("spring.datasource.url", () -> jdbcUrl() + "?currentSchema=" + SCHEMA + ",public");
        properties.add("spring.datasource.username", () -> System.getenv("PGUSER"));
        properties.add("spring.datasource.password", () -> System.getenv("PGPASSWORD"));
        properties.add("spring.flyway.schemas", () -> SCHEMA);
    }

    private static String jdbcUrl() {
        String database = System.getenv("PGDATABASE");
        assertNotNull(database);
        assertTrue(database.endsWith("_test"), "Disposable *_test database required");
        String host = System.getenv().getOrDefault("PGHOST", "127.0.0.1");
        String port = System.getenv().getOrDefault("PGPORT", "5432");
        return "jdbc:postgresql://" + host + ":" + port + "/" + database;
    }

    @AfterAll
    static void dropTestSchema() throws Exception {
        try (var connection = DriverManager.getConnection(jdbcUrl(), System.getenv("PGUSER"), System.getenv("PGPASSWORD"));
             var sql = connection.createStatement()) {
            sql.execute("DROP SCHEMA IF EXISTS " + SCHEMA + " CASCADE");
        }
    }

    @Test
    void uploadCommittedWhileConsentWaitsRejectsTheOldDraftWithoutSavingItsName() throws Exception {
        var pupil = student("Synthetic Pupil");
        var peer = student("Synthetic Peer");
        String email = pupil.getEmail();
        profiles.captureGoogleAvatar(pupil.getId(), ORIGINAL_PHOTO);
        rewards.record(pupil.getId(), StudentRewards.Source.QUIZ, "privacy-concurrency", "privacy-concurrency");
        var before = profiles.update(email, new ProfileDtos.Edit(null, null, true, null,
                null, null, null, profiles.get(email).privacyRevision()));
        assertEquals(ORIGINAL_PHOTO, before.avatarPhoto());
        var consent = new ProfileDtos.Edit("Uncommitted Name", null, null, null,
                null, null, true, before.privacyRevision());

        var output = new ByteArrayOutputStream();
        ImageIO.write(new BufferedImage(40, 40, BufferedImage.TYPE_INT_RGB), "png", output);
        var photo = new MockMultipartFile("file", "replacement.png", "image/png", output.toByteArray());
        var consentPid = new CompletableFuture<Integer>();
        var executor = Executors.newSingleThreadExecutor();
        try {
            var pending = transactions.execute(uploadTransaction -> {
                db.execute("SET LOCAL lock_timeout = '20s'");
                int uploadPid = db.queryForObject("SELECT pg_backend_pid()", Integer.class);
                assertFalse(account.photo(email, photo).leaderboardPhotoVisible());

                var waiting = executor.submit(() -> transactions.execute(consentTransaction -> {
                    db.execute("SET LOCAL lock_timeout = '20s'");
                    consentPid.complete(db.queryForObject("SELECT pg_backend_pid()", Integer.class));
                    return profiles.update(email, consent);
                }));
                int blockedPid = consentPid.orTimeout(10, TimeUnit.SECONDS).join();
                assertNotEquals(uploadPid, blockedPid);
                awaitStudentLock(uploadPid, blockedPid);
                return waiting;
            });

            var failure = assertThrows(ExecutionException.class, () -> pending.get(10, TimeUnit.SECONDS));
            var conflict = assertInstanceOf(ApiException.class, failure.getCause());
            assertEquals(HttpStatus.CONFLICT, conflict.getStatus());
            assertEquals("PROFILE_PRIVACY_CONFLICT", conflict.getCode());
        } finally {
            executor.shutdownNow();
        }

        var current = profiles.get(email);
        assertEquals("Synthetic Pupil", current.displayName());
        assertNotEquals(before.privacyRevision(), current.privacyRevision());
        assertTrue(current.avatarPhoto().startsWith("data:image/jpeg;base64,"));
        assertFalse(current.leaderboardPhotoVisible());
        var entry = profiles.leaderboard(peer.getEmail(), null, true).entries().stream()
                .filter(row -> current.publicAlias().equals(row.alias())).findFirst().orElseThrow();
        assertNull(entry.avatarPhoto());
    }

    @Test
    void readWaitingForRenameReturnsTheNewNameWithItsRevision() throws Exception {
        var student = student("Before Rename");
        String email = student.getEmail();
        var before = profiles.get(email);
        var readerPid = new CompletableFuture<Integer>();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var pending = transactions.execute(renameTransaction -> {
                db.execute("SET LOCAL lock_timeout = '20s'");
                int renamePid = db.queryForObject("SELECT pg_backend_pid()", Integer.class);
                var renamed = profiles.update(email, new ProfileDtos.Edit("After Rename", null, null, null));
                var reader = executor.submit(() -> transactions.execute(readTransaction -> {
                    db.execute("SET LOCAL lock_timeout = '20s'");
                    readerPid.complete(db.queryForObject("SELECT pg_backend_pid()", Integer.class));
                    return profiles.get(email);
                }));
                awaitStudentLock(renamePid, readerPid.orTimeout(10, TimeUnit.SECONDS).join());
                assertNotEquals(before.privacyRevision(), renamed.privacyRevision());
                return reader;
            });

            var snapshot = pending.get(10, TimeUnit.SECONDS);
            assertEquals("After Rename", snapshot.displayName());
            assertEquals(profiles.get(email).privacyRevision(), snapshot.privacyRevision());
        }
    }

    private void awaitStudentLock(int holderPid, int waiterPid) {
        await().pollInSameThread().atMost(Duration.ofSeconds(10)).until(() -> Boolean.TRUE.equals(db.queryForObject("""
                SELECT ? = ANY(pg_blocking_pids(?)) AND EXISTS (
                    SELECT 1 FROM pg_locks WHERE pid = ? AND mode = 'RowShareLock'
                    AND relation IN ('users'::regclass, 'students'::regclass)
                )
                """, Boolean.class, holderPid, waiterPid, waiterPid)));
    }

    private Student student(String name) {
        var student = new Student();
        student.setEmail(UUID.randomUUID() + "@profile-concurrency.test");
        student.setDisplayName(name);
        student.setGradeLevel(3);
        student.setRole("STUDENT");
        student.setActive(true);
        student.setPasswordHash("unused");
        return students.saveAndFlush(student);
    }
}

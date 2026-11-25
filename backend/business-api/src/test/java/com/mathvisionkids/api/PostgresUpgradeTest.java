package com.mathvisionkids.api;

import java.sql.*;
import java.util.UUID;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import static org.junit.jupiter.api.Assertions.*;

/** Opt-in, real Flyway upgrade with existing data. Never touches the public app schema. */
@EnabledIfEnvironmentVariable(named = "MATHVISION_POSTGRES_UPGRADE", matches = "true")
class PostgresUpgradeTest {
    @Test void upgradeFrom40PreservesStarsAndRetiresSelectedTitle() throws Exception {
        verifyUpgrade("40");
    }

    @Test void validateVersion41AndPreserveAchievementPath() throws Exception {
        verifyUpgrade("41");
    }

    @Test void upgradeFrom39AddsRecoveryWithoutReplacingPinOrLimits() throws Exception {
        verifyUpgrade("39");
    }

    @Test void upgradeFrom38AddsGameTimeWithoutReplacingParentSettings() throws Exception {
        verifyUpgrade("38");
    }

    @Test void upgradeFrom34AddsNamePrivacyAndPreservesVisibleParticipation() throws Exception {
        verifyUpgrade("34");
    }

    @Test void upgradeFrom33PreservesExistingArithmeticRun() throws Exception {
        verifyUpgrade("33");
    }

    @Test void upgradeFrom32AddsPrivateAccountTablesAndPreservesExistingData() throws Exception {
        verifyUpgrade("32");
    }
    @Test void upgradeFrom28PreservesUsersQuizAndImageReferencesAndValidatesChecksums() throws Exception {
        verifyUpgrade("28");
    }

    @Test void upgradeFrom31PreservesDataWhenAssignmentAndBatchMigrationsArePresent() throws Exception {
        // The companion PR contributes V30 and V31. Exercise its already-applied schema when available.
        org.junit.jupiter.api.Assumptions.assumeTrue(getClass().getResource(
                "/db/migration/V31__batch_creation_idempotency.sql") != null);
        verifyUpgrade("31");
    }

    private void verifyUpgrade(String startingVersion) throws Exception {
        String database = System.getenv("PGDATABASE");
        assertNotNull(database); assertTrue(database.endsWith("_test"), "Disposable *_test database required");
        String host = System.getenv().getOrDefault("PGHOST", "127.0.0.1");
        String port = System.getenv().getOrDefault("PGPORT", "5432");
        String url = "jdbc:postgresql://" + host + ":" + port + "/" + database;
        String user = System.getenv("PGUSER"), password = System.getenv("PGPASSWORD");
        String schema = "upgrade_test_" + UUID.randomUUID().toString().replace("-", "");
        try (var connection = DriverManager.getConnection(url, user, password); var sql = connection.createStatement()) {
            sql.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\" WITH SCHEMA public");
            try {
                Flyway.configure().dataSource(url, user, password).schemas(schema).defaultSchema(schema)
                        .target(startingVersion).load().migrate();
                sql.execute("SET search_path TO " + schema + ", public");
                String id = UUID.randomUUID().toString(), source = UUID.randomUUID().toString(), quiz = UUID.randomUUID().toString();
                String game = UUID.randomUUID().toString();
                sql.execute("INSERT INTO users(id,email,password_hash,role,display_name) VALUES ('"+id+"','synthetic@upgrade.test','unused','STUDENT','Synthetic pupil')");
                sql.execute("INSERT INTO students(student_id,grade_level) VALUES ('"+id+"',5)");
                if (Integer.parseInt(startingVersion) >= 32) {
                    sql.execute("INSERT INTO student_profile_preferences(student_id,avatar,public_alias,leaderboard_visible)"
                            + " VALUES ('"+id+"','rocket','SyntheticStar',true)");
                    sql.execute("UPDATE student_profile_preferences SET selected_title='luyen-khi', reached_challenger=true WHERE student_id='"+id+"'");
                    sql.execute("INSERT INTO student_verified_activities(student_id,source,event_id,content_id,completed_at,activity_day,stars)"
                            + " VALUES ('"+id+"','LESSON','synthetic-rank-event','synthetic-rank-content',now(),CURRENT_DATE,1)");
                    if (Integer.parseInt(startingVersion) >= 41) {
                        sql.execute("UPDATE student_profile_preferences SET achievement_path='RANK', achievement_path_changed_at=now() WHERE student_id='"+id+"'");
                    }
                    sql.execute("INSERT INTO student_game_runs(id,student_id,level,started_at,activity_day,seed,answered,correct,last_answer)"
                            + " VALUES ('"+game+"','"+id+"',5,now(),CURRENT_DATE,12,2,1,10)");
                }
                if (Integer.parseInt(startingVersion) >= 38) {
                    sql.execute("INSERT INTO student_parent_control(student_id,pin_hash,daily_minutes,game_stars)"
                            + " VALUES ('"+id+"','synthetic-hash',45,2)");
                }
                sql.execute("INSERT INTO submissions(submission_id,student_id,status) VALUES ('"+source+"','"+id+"','REVIEW_REQUIRED')");
                sql.execute("INSERT INTO submission_images(submission_id,file_path,content_type,file_size) VALUES ('"+source+"','synthetic/retained.png','image/png',68)");
                sql.execute("INSERT INTO quiz_learning_sources(id,student_id,source_type,source_id,problem_text,fingerprint,completed,created_at) VALUES ('"+UUID.randomUUID()+"','"+id+"','LESSON','source','1 + 1 = ?',repeat('a',64),true,now())");
                sql.execute("INSERT INTO student_quizzes(id,student_id,source_type,source_id,source_fingerprint,topic_code,topic_name,skill_code,grade_level,question_text,unit,answer_spec,validated_solution,status,created_at,updated_at,generation_version) VALUES ('"+quiz+"','"+id+"','LESSON','source',repeat('a',64),'ADDITION','Addition','ADD',5,'2 + 2 = ?','','4','2 + 2 = 4','READY',now(),now(),'test')");
                var latest = Flyway.configure().dataSource(url, user, password).schemas(schema).defaultSchema(schema).load();
                var upgrade = latest.migrate();
                assertEquals(41 - Integer.parseInt(startingVersion), upgrade.migrationsExecuted);
                assertEquals("41", upgrade.targetSchemaVersion);
                assertTrue(latest.validateWithResult().validationSuccessful);
                if (Integer.parseInt(startingVersion) >= 38) {
                    try (var result = sql.executeQuery("SELECT pin_hash, pin_revision FROM student_parent_control WHERE student_id = '" + id + "'")) {
                        assertTrue(result.next());
                        assertEquals("synthetic-hash", result.getString("pin_hash"));
                        assertEquals(0, result.getLong("pin_revision"));
                    }
                }
                try (var result = sql.executeQuery("SELECT COUNT(*) FROM student_parent_pin_challenge")) {
                    assertTrue(result.next());
                    assertEquals(0, result.getInt(1));
                }
                assertEquals(0, latest.migrate().migrationsExecuted);
                if (Integer.parseInt(startingVersion) >= 32) {
                    try (var rows = sql.executeQuery("SELECT leaderboard_visible,leaderboard_name_hidden FROM student_profile_preferences WHERE student_id='"+id+"'")) {
                        assertTrue(rows.next()); assertTrue(rows.getBoolean(1)); assertTrue(rows.getBoolean(2));
                    }
                    try (var rows = sql.executeQuery("SELECT selected_title,avatar,public_alias,reached_challenger FROM student_profile_preferences WHERE student_id='"+id+"'")) {
                        assertTrue(rows.next()); assertEquals("luyen-khi", rows.getString(1)); assertEquals("rocket", rows.getString(2));
                        assertEquals("SyntheticStar", rows.getString(3)); assertTrue(rows.getBoolean(4));
                    }
                    try (var rows = sql.executeQuery("SELECT SUM(stars) FROM student_verified_activities WHERE student_id='"+id+"'")) {
                        assertTrue(rows.next()); assertEquals(1, rows.getLong(1));
                    }
                    try (var rows = sql.executeQuery("SELECT achievement_path,achievement_path_changed_at FROM student_profile_preferences WHERE student_id='"+id+"'")) {
                        assertTrue(rows.next());
                        if (Integer.parseInt(startingVersion) >= 41) {
                            assertEquals("RANK", rows.getString(1));
                            assertNotNull(rows.getObject(2));
                        } else {
                            assertNull(rows.getString(1));
                            assertNull(rows.getObject(2));
                        }
                    }
                    sql.execute("UPDATE student_profile_preferences SET leaderboard_name_hidden=false WHERE student_id='"+id+"'");
                }
                sql.execute("INSERT INTO student_profile_photos(student_id,image_bytes,updated_at) VALUES ('"+id+"',decode('ffd8ffe0','hex'),now())");
                if (Integer.parseInt(startingVersion) >= 38) {
                    try (var rows = sql.executeQuery("SELECT pin_hash,daily_minutes,game_stars,game_minutes FROM student_parent_control WHERE student_id='"+id+"'")) {
                        assertTrue(rows.next()); assertEquals("synthetic-hash", rows.getString(1));
                        assertEquals(45, rows.getInt(2)); assertEquals(2, rows.getInt(3)); assertNull(rows.getObject(4));
                    }
                    sql.execute("UPDATE student_parent_control SET game_minutes=15 WHERE student_id='"+id+"'");
                    sql.execute("INSERT INTO student_game_usage_day(student_id,usage_day,elapsed_millis) VALUES ('"+id+"',CURRENT_DATE,62000)");
                    sql.execute("INSERT INTO student_game_usage_connection(student_id,connection_id,accounted_at,lease_until)"
                            + " VALUES ('"+id+"','"+UUID.randomUUID()+"',now(),now()+interval '10 seconds')");
                }
                var dump = java.nio.file.Files.createTempFile("mathvision-upgrade-test-", ".dump");
                var diagnostics = java.nio.file.Files.createTempFile("mathvision-upgrade-test-", ".log");
                try {
                    var backup = tool("pg_dump", database, user, "--format=custom", "--no-owner", "--no-privileges", "--schema="+schema)
                            .redirectOutput(dump.toFile()).redirectError(diagnostics.toFile()).start();
                    assertCompleted(backup, "backup");
                    sql.execute("DROP SCHEMA " + schema + " CASCADE");
                    var restore = tool("pg_restore", database, user, "--exit-on-error", "--no-owner", "--no-privileges")
                            .redirectInput(dump.toFile()).redirectOutput(diagnostics.toFile()).redirectErrorStream(true).start();
                    assertCompleted(restore, "restore");
                    sql.execute("SET search_path TO " + schema + ", public");
                    assertTrue(latest.validateWithResult().validationSuccessful);
                } finally {
                    java.nio.file.Files.deleteIfExists(dump); java.nio.file.Files.deleteIfExists(diagnostics);
                }
                try (var rows = sql.executeQuery("SELECT u.token_version,q.answer_spec,i.file_path FROM users u JOIN student_quizzes q ON q.student_id=u.id JOIN submissions s ON s.student_id=u.id JOIN submission_images i ON i.submission_id=s.submission_id WHERE u.id='"+id+"'")) {
                    assertTrue(rows.next()); assertEquals(0, rows.getLong(1)); assertEquals("4", rows.getString(2));
                    assertEquals("synthetic/retained.png", rows.getString(3)); assertFalse(rows.next());
                }
                try (var rows = sql.executeQuery("SELECT id FROM student_reward_lock")) {
                    assertTrue(rows.next()); assertEquals(1, rows.getInt(1)); assertFalse(rows.next());
                }
                if (Integer.parseInt(startingVersion) >= 32) {
                    try (var rows = sql.executeQuery("SELECT leaderboard_visible,leaderboard_name_hidden FROM student_profile_preferences WHERE student_id='"+id+"'")) {
                        assertTrue(rows.next()); assertTrue(rows.getBoolean(1)); assertFalse(rows.getBoolean(2));
                    }
                    try (var rows = sql.executeQuery("SELECT SUM(stars) FROM student_verified_activities WHERE student_id='"+id+"'")) {
                        assertTrue(rows.next()); assertEquals(1, rows.getLong(1));
                    }
                    try (var rows = sql.executeQuery("SELECT mode,answered,correct,last_answer,reward_status FROM student_game_runs WHERE id='"+game+"'")) {
                        assertTrue(rows.next()); assertEquals("ARITHMETIC_QUEST", rows.getString(1));
                        assertEquals(2, rows.getInt(2)); assertEquals(1, rows.getInt(3));
                        assertEquals(10, rows.getInt(4)); assertNull(rows.getString(5)); assertFalse(rows.next());
                    }
                }
                try (var rows = sql.executeQuery("SELECT encode(image_bytes,'hex') FROM student_profile_photos WHERE student_id='"+id+"'")) {
                    assertTrue(rows.next()); assertEquals("ffd8ffe0", rows.getString(1)); assertFalse(rows.next());
                }
                if (Integer.parseInt(startingVersion) >= 38) {
                    try (var rows = sql.executeQuery("SELECT c.daily_minutes,c.game_stars,c.game_minutes,d.elapsed_millis"
                            + " FROM student_parent_control c JOIN student_game_usage_day d USING(student_id)"
                            + " WHERE c.student_id='"+id+"'")) {
                        assertTrue(rows.next()); assertEquals(45, rows.getInt(1)); assertEquals(2, rows.getInt(2));
                        assertEquals(15, rows.getInt(3)); assertEquals(62_000, rows.getLong(4)); assertFalse(rows.next());
                    }
                }
            } finally {
                // Only the generated test schema is disposable; no application data is removed.
                sql.execute("DROP SCHEMA IF EXISTS " + schema + " CASCADE");
            }
        }
    }

    private static void assertCompleted(Process process, String operation) throws Exception {
        try {
            assertTrue(process.waitFor(30, java.util.concurrent.TimeUnit.SECONDS), operation + " timed out");
            assertEquals(0, process.exitValue(), "Disposable database " + operation + " failed");
        } finally {
            if (process.isAlive()) {
                process.descendants().forEach(ProcessHandle::destroyForcibly);
                process.destroyForcibly();
                process.waitFor(5, java.util.concurrent.TimeUnit.SECONDS);
            }
        }
    }

    private static ProcessBuilder tool(String command, String database, String user, String... options) {
        var args = new java.util.ArrayList<String>();
        String container = System.getenv("PG_TOOLS_CONTAINER");
        if (container != null) {
            boolean ciService = "true".equals(System.getenv("GITHUB_ACTIONS")) && container.matches("[a-f0-9]{64}");
            if (!container.matches("mathvision-audit-[a-z0-9-]+") && !ciService) throw new IllegalArgumentException("Disposable audit container required");
            // Use the disposable server's matching pg_dump/pg_restore, not the runner's newer client.
            args.addAll(java.util.List.of("docker", "exec", "-i", container));
        }
        args.add(command); args.addAll(java.util.List.of("-U", user, "-d", database));
        args.addAll(java.util.List.of(options));
        return new ProcessBuilder(args);
    }
}

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
                sql.execute("INSERT INTO users(id,email,password_hash,role,display_name) VALUES ('"+id+"','synthetic@upgrade.test','unused','STUDENT','Synthetic pupil')");
                sql.execute("INSERT INTO students(student_id,grade_level) VALUES ('"+id+"',5)");
                sql.execute("INSERT INTO submissions(submission_id,student_id,status) VALUES ('"+source+"','"+id+"','REVIEW_REQUIRED')");
                sql.execute("INSERT INTO submission_images(submission_id,file_path,content_type,file_size) VALUES ('"+source+"','synthetic/retained.png','image/png',68)");
                sql.execute("INSERT INTO quiz_learning_sources(id,student_id,source_type,source_id,problem_text,fingerprint,completed,created_at) VALUES ('"+UUID.randomUUID()+"','"+id+"','LESSON','source','1 + 1 = ?',repeat('a',64),true,now())");
                sql.execute("INSERT INTO student_quizzes(id,student_id,source_type,source_id,source_fingerprint,topic_code,topic_name,skill_code,grade_level,question_text,unit,answer_spec,validated_solution,status,created_at,updated_at,generation_version) VALUES ('"+quiz+"','"+id+"','LESSON','source',repeat('a',64),'ADDITION','Addition','ADD',5,'2 + 2 = ?','','4','2 + 2 = 4','READY',now(),now(),'test')");
                var latest = Flyway.configure().dataSource(url, user, password).schemas(schema).defaultSchema(schema).load();
                var upgrade = latest.migrate();
                assertEquals(33 - Integer.parseInt(startingVersion), upgrade.migrationsExecuted);
                assertEquals("33", upgrade.targetSchemaVersion);
                assertTrue(latest.validateWithResult().validationSuccessful);
                assertEquals(0, latest.migrate().migrationsExecuted);
                sql.execute("INSERT INTO student_profile_photos(student_id,image_bytes,updated_at) VALUES ('"+id+"',decode('ffd8ffe0','hex'),now())");
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
                try (var rows = sql.executeQuery("SELECT encode(image_bytes,'hex') FROM student_profile_photos WHERE student_id='"+id+"'")) {
                    assertTrue(rows.next()); assertEquals("ffd8ffe0", rows.getString(1)); assertFalse(rows.next());
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

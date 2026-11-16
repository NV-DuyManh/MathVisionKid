package com.mathvisionkids.api.submission;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import java.sql.DriverManager;
import java.util.UUID;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.http.MediaType;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(properties = {
        "spring.jpa.hibernate.ddl-auto=validate", "spring.flyway.enabled=true", "spring.sql.init.mode=never",
        "spring.jpa.database-platform=org.hibernate.dialect.PostgreSQLDialect"
})
@AutoConfigureMockMvc
@EnabledIfEnvironmentVariable(named = "MATHVISION_POSTGRES_CONCURRENCY", matches = "true")
class PostgresAssignedResultsTest {
    private static final String SCHEMA = "assigned_results_" + UUID.randomUUID().toString().replace("-", "");
    @DynamicPropertySource
    static void postgresProperties(DynamicPropertyRegistry properties) throws Exception {
        if (!requiredEnv("PGDATABASE").endsWith("_test")) {
            throw new IllegalStateException("Disposable *_test database required");
        }
        try (var connection = DriverManager.getConnection(databaseUrl(), requiredEnv("PGUSER"), requiredEnv("PGPASSWORD"));
             var statement = connection.createStatement()) {
            statement.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\" WITH SCHEMA public");
            statement.execute("CREATE SCHEMA " + SCHEMA);
        }
        properties.add("spring.datasource.url", () -> databaseUrl() + "?currentSchema=" + SCHEMA + ",public");
        properties.add("spring.datasource.username", () -> requiredEnv("PGUSER"));
        properties.add("spring.datasource.password", () -> requiredEnv("PGPASSWORD"));
        properties.add("spring.datasource.driver-class-name", () -> "org.postgresql.Driver");
        properties.add("spring.flyway.schemas", () -> SCHEMA);
        properties.add("spring.flyway.default-schema", () -> SCHEMA);
    }

    @Autowired private MockMvc mvc;
    @Autowired private JdbcTemplate db;
    @Autowired private ObjectMapper json;

    @Test
    void conservesFiftyRecipientsAndSeparatesReleasedZeroFromMissingScoresAfterRemoval() throws Exception {
        UUID owner = actor("owner", "TEACHER");
        UUID other = actor("other", "TEACHER");
        UUID classroom = db.queryForObject("INSERT INTO classrooms(name, grade_level, teacher_id) VALUES ('Synthetic class', 3, ?) RETURNING class_id", UUID.class, owner);
        UUID assignment = db.queryForObject("""
                INSERT INTO assignments(class_id, teacher_id, title, prompt, operation_type, max_score, status)
                VALUES (?, ?, 'Synthetic addition', '2 + 3', 'VERTICAL_ADDITION', 10, 'PUBLISHED') RETURNING assignment_id
                """, UUID.class, classroom, owner);
        UUID publication = db.queryForObject("INSERT INTO assignment_publications(assignment_id) VALUES (?) RETURNING publication_id", UUID.class, assignment);
        for (int i = 0; i < 50; i++) {
            UUID pupil = actor(String.format(java.util.Locale.ROOT, "pupil%02d", i), "STUDENT");
            db.update("INSERT INTO assignment_recipients(publication_id, student_id) VALUES (?, ?)", publication, pupil);
            if (i != 0) db.update("INSERT INTO classroom_students(class_id, student_id) VALUES (?, ?)", classroom, pupil);
            if (i > 4) continue;
            String state = switch (i) {
                case 0, 4 -> "GRADE_RELEASED";
                case 1 -> "AWAITING_REVIEW";
                case 2 -> "RETAKE_REQUESTED";
                default -> "AWAITING_IMAGE";
            };
            UUID submission = db.queryForObject("""
                    INSERT INTO submissions(student_id, assignment_id, publication_id, status, source)
                    VALUES (?, ?, ?, ?, 'ASSIGNED_WEB') RETURNING submission_id
                    """, UUID.class, pupil, assignment, publication, state);
            if (i != 3) db.update("""
                    INSERT INTO submission_images(submission_id, file_path, content_type, file_size, image_version)
                    VALUES (?, ?, 'image/png', 100, 1)
                    """, submission, "synthetic/" + submission);
            if (i == 0 || i == 4) db.update("""
                    INSERT INTO teacher_decisions(submission_id, teacher_id, type, final_score, reason, assigned_request_id, assigned_image_version)
                    VALUES (?, ?, 'ASSIGNED_RELEASE', ?, 'Private feedback', ?, 1)
                    """, submission, owner, i == 0 ? 0 : 8, UUID.randomUUID());
            if (i == 2) db.update("""
                    INSERT INTO assigned_image_returns(submission_id, image_version, teacher_id, reason, instruction)
                    VALUES (?, 1, ?, 'UNREADABLE', 'Retake fixture')
                    """, submission, owner);
            if (i == 3) db.update("""
                    INSERT INTO assigned_upload_attempts(attempt_id, submission_id, request_id, expected_image_version, digest,
                      object_key, state, expires_at, stored_digest, stored_content_type, stored_size)
                    VALUES (?, ?, ?, 0, ?, ?, 'OPEN', CURRENT_TIMESTAMP - INTERVAL '1 minute', ?, 'image/png', 100)
                    """, UUID.randomUUID(), submission, UUID.randomUUID(), "a".repeat(64), "synthetic/" + submission, "a".repeat(64));
        }
        String url = "/api/v1/teacher/assignments/" + assignment + "/results";
        mvc.perform(get(url).with(user("owner@results.test").roles("TEACHER")))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control", "no-store"))
                .andExpect(jsonPath("$.recipientCount").value(50))
                .andExpect(jsonPath("$.recipients.length()").value(50))
                .andExpect(jsonPath("$.counts.AWAITING_IMAGE").value(45))
                .andExpect(jsonPath("$.counts.UPLOADING").value(1))
                .andExpect(jsonPath("$.counts.AWAITING_REVIEW").value(1))
                .andExpect(jsonPath("$.counts.RETAKE_REQUESTED").value(1))
                .andExpect(jsonPath("$.counts.GRADE_RELEASED").value(2))
                .andExpect(jsonPath("$.recipients[0].member").value(false))
                .andExpect(jsonPath("$.recipients[0].score").value(0))
                .andExpect(jsonPath("$.recipients[1].score").isEmpty())
                .andExpect(jsonPath("$.recipients[2].score").isEmpty())
                .andExpect(jsonPath("$.recipients[3].status").value("UPLOADING"))
                .andExpect(jsonPath("$.recipients[4].score").value(8))
                .andExpect(jsonPath("$.recipients[0].feedback").doesNotHaveJsonPath())
                .andExpect(jsonPath("$.recipients[0].imageUrl").doesNotHaveJsonPath());
        mvc.perform(get(url).with(user("other@results.test").roles("TEACHER"))).andExpect(status().isNotFound());
        mvc.perform(get(url).with(user("admin@results.test").roles("ADMIN"))).andExpect(status().isForbidden());
        String released = "/api/v1/teacher/assigned-submissions/" + db.queryForObject("""
                SELECT s.submission_id FROM submissions s JOIN teacher_decisions d USING (submission_id)
                WHERE s.publication_id = ? AND d.type = 'ASSIGNED_RELEASE' AND d.final_score = 0
                """, UUID.class, publication);
        mvc.perform(get(released).with(user("owner@results.test").roles("TEACHER")))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control", "no-store"))
                .andExpect(jsonPath("$.score").value(0)).andExpect(jsonPath("$.feedback").value("Private feedback"));
        String center = "/api/v1/teacher/assignments/action-center";
        UUID secondClass = db.queryForObject("""
                INSERT INTO classrooms(name, grade_level, teacher_id) VALUES ('Second class', 3, ?) RETURNING class_id
                """, UUID.class, owner);
        UUID empty = db.queryForObject("""
                INSERT INTO assignments(class_id, teacher_id, title, prompt, operation_type, max_score, status)
                VALUES (?, ?, 'Empty publication', '3 + 4', 'VERTICAL_ADDITION', 10, 'PUBLISHED') RETURNING assignment_id
                """, UUID.class, secondClass, owner);
        db.update("INSERT INTO assignment_publications(assignment_id) VALUES (?)", empty);
        db.update("""
                WITH extra AS (
                    INSERT INTO assignments(class_id, teacher_id, title, prompt, operation_type, max_score, status)
                    SELECT ?, ?, 'Pagination ' || n, '3 + 4', 'VERTICAL_ADDITION', 10, 'PUBLISHED'
                    FROM generate_series(1, 21) AS n
                    RETURNING assignment_id
                )
                INSERT INTO assignment_publications(assignment_id)
                SELECT assignment_id FROM extra
                """, secondClass, owner);
        UUID secondStudent = db.queryForObject("SELECT id FROM users WHERE email = 'pupil04@results.test'", UUID.class);
        db.update("INSERT INTO classroom_students(class_id, student_id) VALUES (?, ?)", secondClass, secondStudent);
        db.update("""
                INSERT INTO assignment_recipients(publication_id, student_id)
                SELECT p.publication_id, ? FROM assignment_publications p JOIN assignments a USING (assignment_id)
                WHERE a.class_id = ? AND a.title = 'Pagination 1'
                """, secondStudent, secondClass);
        mvc.perform(get("/api/v1/teacher/assignments/" + empty + "/results")
                .with(user("owner@results.test").roles("TEACHER")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.recipientCount").value(0));
        mvc.perform(get(center).param("filter", "PENDING").with(user("owner@results.test").roles("TEACHER")))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control", "no-store"))
                .andExpect(jsonPath("$.classCount").value(2))
                .andExpect(jsonPath("$.matchingAssignments").value(1))
                .andExpect(jsonPath("$.pendingSubmissions").value(1))
                .andExpect(jsonPath("$.retakeRecipients").value(1))
                .andExpect(jsonPath("$.assignmentsWithMissingWork").value(2))
                .andExpect(jsonPath("$.releasedSubmissions").value(2))
                .andExpect(jsonPath("$.assignments[0].assignmentId").value(assignment.toString()));
        mvc.perform(get(center).with(user("owner@results.test").roles("TEACHER")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.matchingAssignments").value(23))
                .andExpect(jsonPath("$.assignments.length()").value(20));
        mvc.perform(get(center).param("page", "1").with(user("owner@results.test").roles("TEACHER")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.assignments.length()").value(3))
                .andExpect(jsonPath("$.pendingSubmissions").value(1));
        mvc.perform(get(center).with(user("admin@results.test").roles("ADMIN"))).andExpect(status().isForbidden());
        mvc.perform(get(center).with(user("other@results.test").roles("TEACHER")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.assignments").isEmpty());
        String history = "/api/v1/student/assignments/history";
        mvc.perform(get(history).with(user("pupil04@results.test").roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control", "no-store"))
                .andExpect(jsonPath("$.length()").value(2))
                .andExpect(jsonPath("$[1].score").value(8))
                .andExpect(jsonPath("$[0].feedback").doesNotHaveJsonPath());
        mvc.perform(get(history).with(user("pupil00@results.test").roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$").isEmpty());
        mvc.perform(get(history).with(user("owner@results.test").roles("TEACHER")))
                .andExpect(status().isForbidden());
        db.update("UPDATE classrooms SET teacher_id = ? WHERE class_id = ?", other, classroom);
        mvc.perform(get(center).with(user("owner@results.test").roles("TEACHER")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.pendingSubmissions").value(0));
        mvc.perform(get(center).with(user("other@results.test").roles("TEACHER")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.pendingSubmissions").value(1));
        mvc.perform(get(url).with(user("owner@results.test").roles("TEACHER"))).andExpect(status().isNotFound());
        mvc.perform(get(released).with(user("owner@results.test").roles("TEACHER"))).andExpect(status().isNotFound());
        mvc.perform(get(released).with(user("other@results.test").roles("TEACHER")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.feedback").value("Private feedback"));
        mvc.perform(get(url).with(user("other@results.test").roles("TEACHER")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.teacherName").value("other"))
                .andExpect(jsonPath("$.recipients[0].score").value(0));
        assertEquals(2, db.queryForObject("SELECT count(*) FROM teacher_decisions", Integer.class));
        UUID pending = db.queryForObject("""
                SELECT submission_id FROM submissions WHERE assignment_id = ? AND status = 'AWAITING_REVIEW'
                """, UUID.class, assignment);
        String gradeBody = json.writeValueAsString(java.util.Map.of(
                "requestId", UUID.randomUUID(), "imageVersion", 1, "score", 0,
                "readable", true, "matchesAssignment", true, "feedback", "Checked after handover"));
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var grade = executor.submit(() -> mvc.perform(post("/api/v1/teacher/assigned-submissions/" + pending + "/release-grade")
                    .with(user("other@results.test").roles("TEACHER")).contentType(MediaType.APPLICATION_JSON)
                    .content(gradeBody)).andExpect(status().isNoContent()));
            mvc.perform(get(url).with(user("other@results.test").roles("TEACHER")))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.counts.GRADE_RELEASED").value(org.hamcrest.Matchers.anyOf(
                            org.hamcrest.Matchers.is(2), org.hamcrest.Matchers.is(3))))
                    .andExpect(jsonPath("$.recipients[1].status").value(org.hamcrest.Matchers.anyOf(
                            org.hamcrest.Matchers.is("AWAITING_REVIEW"), org.hamcrest.Matchers.is("GRADE_RELEASED"))));
            grade.get(10, TimeUnit.SECONDS);
        }
        mvc.perform(get(url).with(user("other@results.test").roles("TEACHER")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.counts.GRADE_RELEASED").value(3))
                .andExpect(jsonPath("$.counts.AWAITING_REVIEW").value(0))
                .andExpect(jsonPath("$.recipients[1].score").value(0));
        mvc.perform(get(center).param("filter", "PENDING").with(user("other@results.test").roles("TEACHER")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.pendingSubmissions").value(0))
                .andExpect(jsonPath("$.releasedSubmissions").value(3));
        mvc.perform(get(history).with(user("pupil01@results.test").roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$[0].score").value(0));
    }

    private UUID actor(String name, String role) {
        UUID id = db.queryForObject("""
                INSERT INTO users(email, password_hash, role, display_name) VALUES (?, 'unused', ?, ?) RETURNING id
                """, UUID.class, name + "@results.test", role, name);
        if ("TEACHER".equals(role)) db.update("INSERT INTO teachers(teacher_id) VALUES (?)", id);
        else db.update("INSERT INTO students(student_id, grade_level) VALUES (?, 3)", id);
        return id;
    }
    @AfterAll
    static void dropIsolatedSchema() throws Exception {
        try (var connection = DriverManager.getConnection(databaseUrl(), requiredEnv("PGUSER"), requiredEnv("PGPASSWORD"));
             var statement = connection.createStatement()) {
            statement.execute("DROP SCHEMA IF EXISTS " + SCHEMA + " CASCADE");
        }
    }

    private static String databaseUrl() {
        return "jdbc:postgresql://" + System.getenv().getOrDefault("PGHOST", "127.0.0.1") + ":"
                + System.getenv().getOrDefault("PGPORT", "5432") + "/" + requiredEnv("PGDATABASE");
    }

    private static String requiredEnv(String name) {
        String value = System.getenv(name);
        if (value == null || value.isBlank()) throw new IllegalStateException(name + " is required");
        return value;
    }
}

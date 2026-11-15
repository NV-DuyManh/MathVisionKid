package com.mathvisionkids.api.classroom;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import java.sql.DriverManager;
import java.util.UUID;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;

/** Opt-in HTTP quota contracts using real PostgreSQL and a disposable schema. */
@SpringBootTest(properties = {
        "spring.jpa.hibernate.ddl-auto=validate",
        "spring.flyway.enabled=true",
        "spring.sql.init.mode=never",
        "spring.jpa.database-platform=org.hibernate.dialect.PostgreSQLDialect"
})
@AutoConfigureMockMvc
@EnabledIfEnvironmentVariable(named = "MATHVISION_POSTGRES_CONCURRENCY", matches = "true")
class PostgresClassroomQuotaTest {
    private static final String SCHEMA = "classroom_quota_" + UUID.randomUUID().toString().replace("-", "");
    private static final String CODE = "123456";
    private static final String TOKEN = "a".repeat(64);

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

    @Autowired private MockMvc mockMvc;
    @Autowired private JdbcTemplate jdbc;
    @Autowired private StudentRepository students;
    @Autowired private TeacherRepository teachers;
    @Autowired private ClassroomRepository classrooms;
    private Student pupil;
    private UUID classroomId;
    private UUID generation;
    private long window;

    @BeforeEach
    void createFixture() {
        jdbc.update("DELETE FROM classroom_join_limits");
        jdbc.update("DELETE FROM classroom_code_limit");
        jdbc.update("DELETE FROM classroom_invitations");
        var owner = new Teacher();
        owner.setEmail("teacher-" + UUID.randomUUID() + "@quota.test.invalid");
        owner.setPasswordHash("unused");
        owner.setRole("TEACHER");
        owner.setActive(true);
        owner.setDisplayName("Quota teacher");
        owner = teachers.saveAndFlush(owner);
        pupil = new Student();
        pupil.setEmail("student-" + UUID.randomUUID() + "@quota.test.invalid");
        pupil.setPasswordHash("unused");
        pupil.setRole("STUDENT");
        pupil.setActive(true);
        pupil.setGradeLevel(3);
        pupil.setDisplayName("Quota student");
        pupil = students.saveAndFlush(pupil);
        var classroom = new Classroom();
        classroom.setName("Quota classroom");
        classroom.setGradeLevel(3);
        classroom.setTeacher(owner);
        classroomId = classrooms.saveAndFlush(classroom).getClassId();
        generation = UUID.randomUUID();
        jdbc.update("INSERT INTO classroom_invitations VALUES (?, ?, ?, ?, TRUE)", generation, classroomId, CODE, TOKEN);
        // The limiter preserves a future window with greatest(). Seed one minute
        // ahead so crossing a wall-clock minute cannot reset a near-cap fixture.
        window = jdbc.queryForObject("SELECT floor(extract(epoch from clock_timestamp()) / 60)::bigint + 1", Long.class);
    }

    @Test
    void accountLimitIsSharedByPreviewAndJoinAndReturnsPrivateRetryHeaders() throws Exception {
        seedAccount(19);
        seedShared(1);
        preview(CODE).andExpect(status().isOk());
        assertEquals(20, accountAttempts());
        expectLimited(join(CODE));
        assertEquals(20, accountAttempts());
        assertEquals(2, sharedAttempts(), "account rejection must not consume a shared attempt");
    }

    @Test
    void sharedLimitRollsBackAccountIncrementAndPreservesTokenFallback() throws Exception {
        seedAccount(18);
        seedShared(299);
        preview(CODE).andExpect(status().isOk());
        assertEquals(19, accountAttempts());
        assertEquals(300, sharedAttempts());
        expectLimited(join(CODE));
        assertEquals(19, accountAttempts(), "shared rejection must roll back its account increment");
        assertEquals(300, sharedAttempts());
        preview(TOKEN).andExpect(status().isOk());
        assertEquals(20, accountAttempts());
        assertEquals(300, sharedAttempts(), "token fallback consumes only the account quota");
        expectLimited(preview(TOKEN));
    }

    @Test
    void invalidCredentialsCommitQuotaBeforeBothLookupEndpointsFail() throws Exception {
        seedAccount(1);
        seedShared(1);
        preview("654321").andExpect(status().isNotFound());
        assertEquals(2, accountAttempts());
        assertEquals(2, sharedAttempts());
        join("b".repeat(64)).andExpect(status().isNotFound());
        assertEquals(3, accountAttempts());
        assertEquals(2, sharedAttempts());
    }

    private ResultActions preview(String credential) throws Exception {
        return mockMvc.perform(post("/api/v1/student/classes/invitation-preview")
                .with(user(pupil.getEmail()).roles("STUDENT"))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"credential\":\"" + credential + "\"}"));
    }

    private ResultActions join(String credential) throws Exception {
        return mockMvc.perform(post("/api/v1/student/classes/join")
                .with(user(pupil.getEmail()).roles("STUDENT"))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"credential\":\"" + credential + "\",\"classId\":\"" + classroomId
                        + "\",\"generation\":\"" + generation + "\"}"));
    }

    private void expectLimited(ResultActions response) throws Exception {
        response.andExpect(status().isTooManyRequests())
                .andExpect(header().string("Retry-After", "60"))
                .andExpect(header().string("Cache-Control", "no-store"))
                .andExpect(jsonPath("$.error.code").value("JOIN_LIMIT"));
    }

    private void seedAccount(int attempts) {
        jdbc.update("INSERT INTO classroom_join_limits VALUES (?, ?, ?)", pupil.getId(), window, attempts);
    }

    private void seedShared(int attempts) {
        jdbc.update("INSERT INTO classroom_code_limit VALUES (1, ?, ?)", window, attempts);
    }

    private int accountAttempts() {
        return jdbc.queryForObject("SELECT attempts FROM classroom_join_limits WHERE student_id = ?", Integer.class, pupil.getId());
    }

    private int sharedAttempts() {
        return jdbc.queryForObject("SELECT attempts FROM classroom_code_limit WHERE id = 1", Integer.class);
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

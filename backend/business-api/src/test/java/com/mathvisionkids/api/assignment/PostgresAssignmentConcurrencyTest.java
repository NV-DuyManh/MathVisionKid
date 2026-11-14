package com.mathvisionkids.api.assignment;

import static org.junit.jupiter.api.Assertions.*;

import com.mathvisionkids.api.admin.AdminService;
import com.mathvisionkids.api.classroom.Classroom;
import com.mathvisionkids.api.classroom.ClassroomRepository;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import java.sql.DriverManager;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

/** Opt-in end-to-end concurrency checks against an isolated PostgreSQL schema. */
@SpringBootTest(properties = {
        "spring.jpa.hibernate.ddl-auto=validate",
        "spring.flyway.enabled=true",
        "spring.sql.init.mode=never",
        "spring.jpa.database-platform=org.hibernate.dialect.PostgreSQLDialect"
})
@EnabledIfEnvironmentVariable(named = "MATHVISION_POSTGRES_CONCURRENCY", matches = "true")
class PostgresAssignmentConcurrencyTest {
    private static final String SCHEMA = "assignment_concurrency_" + UUID.randomUUID().toString().replace("-", "");

    @DynamicPropertySource
    static void postgresProperties(DynamicPropertyRegistry properties) throws Exception {
        String database = requiredEnv("PGDATABASE");
        if (!database.endsWith("_test")) throw new IllegalStateException("Disposable *_test database required");
        String host = System.getenv().getOrDefault("PGHOST", "127.0.0.1");
        String port = System.getenv().getOrDefault("PGPORT", "5432");
        String user = requiredEnv("PGUSER");
        String password = requiredEnv("PGPASSWORD");
        String url = "jdbc:postgresql://" + host + ":" + port + "/" + database + "?currentSchema=" + SCHEMA + ",public";
        try (var connection = DriverManager.getConnection("jdbc:postgresql://" + host + ":" + port + "/" + database, user, password);
             var statement = connection.createStatement()) {
            statement.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\" WITH SCHEMA public");
            statement.execute("CREATE SCHEMA " + SCHEMA);
        }
        properties.add("spring.datasource.url", () -> url);
        properties.add("spring.datasource.username", () -> user);
        properties.add("spring.datasource.password", () -> password);
        properties.add("spring.datasource.driver-class-name", () -> "org.postgresql.Driver");
        properties.add("spring.flyway.schemas", () -> SCHEMA);
        properties.add("spring.flyway.default-schema", () -> SCHEMA);
    }

    @Autowired private AssignmentWorkflowService workflow;
    @Autowired private AssignmentRepository assignments;
    @Autowired private AssignmentPublicationRepository publications;
    @Autowired private AssignmentRecipientRepository recipients;
    @Autowired private ClassroomRepository classrooms;
    @Autowired private TeacherRepository teachers;
    @Autowired private StudentRepository students;
    @Autowired private UserRepository users;
    @Autowired private AdminService adminService;
    @Autowired private JdbcTemplate jdbc;
    @Autowired private PlatformTransactionManager transactionManager;

    private Teacher owner;
    private Teacher successor;
    private User admin;
    private Student pupil;
    private Classroom classroom;

    @BeforeEach
    void createFixture() {
        String suffix = UUID.randomUUID().toString();
        owner = teacher("owner-" + suffix);
        successor = teacher("successor-" + suffix);
        admin = new User();
        admin.setEmail("admin-" + suffix + "@test.invalid");
        admin.setPasswordHash("unused");
        admin.setRole("ADMIN");
        admin.setDisplayName("Test Admin");
        admin = users.saveAndFlush(admin);
        pupil = new Student();
        pupil.setEmail("student-" + suffix + "@test.invalid");
        pupil.setPasswordHash("unused");
        pupil.setRole("STUDENT");
        pupil.setDisplayName("Test Student");
        pupil.setGradeLevel(3);
        pupil = students.saveAndFlush(pupil);
        classroom = new Classroom();
        classroom.setName("Concurrency fixture");
        classroom.setGradeLevel(3);
        classroom.setTeacher(owner);
        classroom.getStudents().add(pupil);
        classroom = classrooms.saveAndFlush(classroom);
    }

    @Test
    void concurrentPublishCreatesOnePublicationAndCompleteRecipientSnapshotWithoutPaperWork() throws Exception {
        AssignmentWorkflowService.AssignmentView draft = draft(owner, classroom, UUID.randomUUID());
        long submissionsBefore = count("submissions");
        long decisionsBefore = count("teacher_decisions");
        long jobsBefore = count("ai_jobs");

        var start = new CountDownLatch(1);
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            var first = workers.submit(() -> { start.await(); return workflow.publish(owner.getEmail(), draft.assignmentId()); });
            var second = workers.submit(() -> { start.await(); return workflow.publish(owner.getEmail(), draft.assignmentId()); });
            start.countDown();
            var a = first.get(10, TimeUnit.SECONDS);
            var b = second.get(10, TimeUnit.SECONDS);
            assertEquals("PUBLISHED", a.status());
            assertEquals("PUBLISHED", b.status());
            assertEquals(1, publicationCountFor(draft.assignmentId()));
            assertEquals(1, recipientCountFor(draft.assignmentId()));
            assertEquals(List.of(pupil.getId()), recipients.findRoster(publications.findByAssignmentId(draft.assignmentId()).orElseThrow().getPublicationId())
                    .stream().map(AssignmentWorkflowService.Recipient::studentId).toList());
            assertEquals(submissionsBefore, count("submissions"));
            assertEquals(decisionsBefore, count("teacher_decisions"));
            assertEquals(jobsBefore, count("ai_jobs"));
        }
    }

    @Test
    void publishWaitsForRosterMutationAndSnapshotsCommittedMembership() throws Exception {
        AssignmentWorkflowService.AssignmentView draft = draft(owner, classroom, UUID.randomUUID());
        CountDownLatch mutationLocked = new CountDownLatch(1);
        CountDownLatch commitMutation = new CountDownLatch(1);
        AtomicReference<Throwable> mutationFailure = new AtomicReference<>();
        TransactionTemplate transactions = new TransactionTemplate(transactionManager);
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            var mutation = workers.submit(() -> {
                try {
                    transactions.executeWithoutResult(status -> {
                        Classroom locked = classrooms.findForUpdate(classroom.getClassId()).orElseThrow();
                        locked.getStudents().removeIf(member -> member.getId().equals(pupil.getId()));
                        mutationLocked.countDown();
                        await(commitMutation);
                    });
                } catch (Throwable error) { mutationFailure.set(error); throw error; }
            });
            assertTrue(mutationLocked.await(5, TimeUnit.SECONDS));
            var publish = workers.submit(() -> workflow.publish(owner.getEmail(), draft.assignmentId()));
            try {
                assertThrows(java.util.concurrent.TimeoutException.class, () -> publish.get(300, TimeUnit.MILLISECONDS));
            } finally {
                commitMutation.countDown();
            }
            mutation.get(10, TimeUnit.SECONDS);
            assertNull(mutationFailure.get());
            assertEquals(0, publish.get(10, TimeUnit.SECONDS).recipientCount());
            assertEquals(0, recipientCountFor(draft.assignmentId()));
        }
    }

    @Test
    void publishWaitsForHandoverThenOldOwnerIsDeniedAndSuccessorCanPublish() throws Exception {
        AssignmentWorkflowService.AssignmentView draft = draft(owner, classroom, UUID.randomUUID());
        CountDownLatch handoverLocked = new CountDownLatch(1);
        CountDownLatch commitHandover = new CountDownLatch(1);
        TransactionTemplate transactions = new TransactionTemplate(transactionManager);
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            var handover = workers.submit(() -> transactions.executeWithoutResult(status -> {
                adminService.assignTeacher(classroom.getClassId(), successor.getId(), admin.getEmail());
                handoverLocked.countDown();
                await(commitHandover);
            }));
            assertTrue(handoverLocked.await(5, TimeUnit.SECONDS));
            var oldOwnerPublish = workers.submit(() -> workflow.publish(owner.getEmail(), draft.assignmentId()));
            try {
                assertThrows(java.util.concurrent.TimeoutException.class, () -> oldOwnerPublish.get(300, TimeUnit.MILLISECONDS));
            } finally {
                commitHandover.countDown();
            }
            handover.get(10, TimeUnit.SECONDS);
            ExecutionException denied = assertThrows(ExecutionException.class, () -> oldOwnerPublish.get(10, TimeUnit.SECONDS));
            assertInstanceOf(ApiException.class, denied.getCause());
            assertEquals(403, ((ApiException) denied.getCause()).getStatus().value());
        }

        assertEquals("PUBLISHED", workflow.publish(successor.getEmail(), draft.assignmentId()).status());
        assertEquals(1, recipientCountFor(draft.assignmentId()));
        assertEquals(0, count("submissions"));
        assertEquals(0, count("teacher_decisions"));
        assertEquals(0, count("ai_jobs"));
    }

    @AfterAll
    static void dropIsolatedSchema() throws Exception {
        String host = System.getenv().getOrDefault("PGHOST", "127.0.0.1");
        String port = System.getenv().getOrDefault("PGPORT", "5432");
        String url = "jdbc:postgresql://" + host + ":" + port + "/" + requiredEnv("PGDATABASE");
        try (var connection = DriverManager.getConnection(url, requiredEnv("PGUSER"), requiredEnv("PGPASSWORD"));
             var statement = connection.createStatement()) {
            statement.execute("DROP SCHEMA IF EXISTS " + SCHEMA + " CASCADE");
        }
    }

    private Teacher teacher(String localPart) {
        Teacher teacher = new Teacher();
        teacher.setEmail(localPart + "@test.invalid");
        teacher.setPasswordHash("unused");
        teacher.setRole("TEACHER");
        teacher.setDisplayName(localPart);
        return teachers.saveAndFlush(teacher);
    }

    private AssignmentWorkflowService.AssignmentView draft(Teacher teacher, Classroom target, UUID requestId) {
        return workflow.createDraft(teacher.getEmail(), new AssignmentWorkflowService.DraftRequest(
                target.getClassId(), "Concurrency assignment", "1 + 1 = ?", null,
                "ADDITION", 10, requestId)).assignment();
    }

    private long count(String table) {
        if (!List.of("submissions", "teacher_decisions", "ai_jobs").contains(table)) throw new IllegalArgumentException("Unexpected table");
        return jdbc.queryForObject("select count(*) from " + table, Long.class);
    }

    private long publicationCountFor(UUID assignmentId) {
        return jdbc.queryForObject("select count(*) from assignment_publications where assignment_id = ?", Long.class, assignmentId);
    }

    private long recipientCountFor(UUID assignmentId) {
        return jdbc.queryForObject("select count(*) from assignment_recipients r join assignment_publications p using (publication_id) where p.assignment_id = ?", Long.class, assignmentId);
    }

    private static String requiredEnv(String name) {
        String value = System.getenv(name);
        if (value == null || value.isBlank()) throw new IllegalStateException("Missing required environment variable " + name);
        return value;
    }

    private static void await(CountDownLatch latch) {
        try {
            if (!latch.await(10, TimeUnit.SECONDS)) throw new IllegalStateException("Timed out waiting for test synchronization");
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Interrupted while waiting for test synchronization", error);
        }
    }
}

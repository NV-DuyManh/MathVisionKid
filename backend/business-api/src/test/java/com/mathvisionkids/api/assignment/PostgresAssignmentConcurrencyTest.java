package com.mathvisionkids.api.assignment;

import static org.junit.jupiter.api.Assertions.*;

import com.mathvisionkids.api.admin.AdminService;
import com.mathvisionkids.api.classroom.Classroom;
import com.mathvisionkids.api.classroom.ClassroomRepository;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.submission.AssignedTeacherReview;
import com.fasterxml.jackson.databind.node.IntNode;
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
    @Autowired private TeacherAssignmentController legacyAssignments;
    @Autowired private AssignedTeacherReview review;
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

    @Test
    void legacyCreationLockDoesNotBlockAssignedGradeForeignKey() throws Exception {
        legacyCreationDuringReview(true);
    }

    @Test
    void legacyCreationLockDoesNotBlockAssignedImageReturnForeignKey() throws Exception {
        legacyCreationDuringReview(false);
    }

    private void legacyCreationDuringReview(boolean releaseGrade) throws Exception {
        var assigned = draft(owner, classroom, UUID.randomUUID());
        workflow.publish(owner.getEmail(), assigned.assignmentId());
        UUID publicationId = publications.findByAssignmentId(assigned.assignmentId()).orElseThrow().getPublicationId();
        UUID submissionId = UUID.randomUUID();
        jdbc.update("""
                INSERT INTO submissions(submission_id, assignment_id, publication_id, student_id, source, status)
                VALUES (?, ?, ?, ?, 'ASSIGNED_WEB', 'AWAITING_REVIEW')
                """, submissionId, assigned.assignmentId(), publicationId, pupil.getId());
        jdbc.update("""
                INSERT INTO submission_images(submission_id, file_path, content_type, file_size, source, image_version)
                VALUES (?, ?, 'image/png', 68, 'ASSIGNED_WEB', 1)
                """, submissionId, "synthetic/concurrency-" + submissionId);

        var classLocked = new CountDownLatch(1);
        var legacyWritten = new CountDownLatch(1);
        var commitLegacy = new CountDownLatch(1);
        var transactions = new TransactionTemplate(transactionManager);
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            var reviewing = workers.submit(() -> transactions.executeWithoutResult(status -> {
                classrooms.findForUpdate(classroom.getClassId()).orElseThrow();
                classLocked.countDown();
                await(legacyWritten);
                if (releaseGrade) {
                    review.releaseGrade(owner.getEmail(), submissionId, new AssignedTeacherReview.Grade(
                            UUID.randomUUID(), 1, true, true, IntNode.valueOf(0), "Reviewed"));
                } else {
                    review.returnImage(owner.getEmail(), submissionId,
                            new AssignedTeacherReview.ReturnImage(1, "UNREADABLE", "Please retake the image"));
                }
            }));
            assertTrue(classLocked.await(5, TimeUnit.SECONDS));
            var creating = workers.submit(() -> transactions.execute(status -> {
                var response = createLegacy(UUID.randomUUID());
                assignments.flush();
                legacyWritten.countDown();
                await(commitLegacy);
                return response;
            }));
            try {
                assertTrue(legacyWritten.await(5, TimeUnit.SECONDS));
                // The legacy controller's creation lock remains held here. The
                // review must commit its teacher FK before legacy creation commits.
                reviewing.get(5, TimeUnit.SECONDS);
            } finally {
                commitLegacy.countDown();
            }
            assertEquals(201, creating.get(10, TimeUnit.SECONDS).getStatusCode().value());
        }
        assertEquals(releaseGrade ? "GRADE_RELEASED" : "RETAKE_REQUESTED",
                jdbc.queryForObject("SELECT status FROM submissions WHERE submission_id = ?", String.class, submissionId));
        assertEquals(releaseGrade ? 1 : 0, jdbc.queryForObject(
                "SELECT count(*) FROM teacher_decisions WHERE submission_id = ?", Integer.class, submissionId));
        assertEquals(releaseGrade ? 0 : 1, jdbc.queryForObject(
                "SELECT count(*) FROM assigned_image_returns WHERE submission_id = ?", Integer.class, submissionId));
    }

    @Test
    void keyedDraftWaitsForLegacyCreationAndReturnsConflict() throws Exception {
        UUID key = UUID.randomUUID();
        var legacyWritten = new CountDownLatch(1);
        var commitLegacy = new CountDownLatch(1);
        var transactions = new TransactionTemplate(transactionManager);
        String marker = "legacy-draft-" + UUID.randomUUID();
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            var legacy = workers.submit(() -> transactions.execute(status -> {
                var response = createLegacy(key);
                assignments.flush();
                legacyWritten.countDown();
                await(commitLegacy);
                return response;
            }));
            assertTrue(legacyWritten.await(5, TimeUnit.SECONDS));
            var draft = workers.submit(() -> transactions.execute(status -> {
                jdbc.queryForObject("SELECT set_config('application_name', ?, true)", String.class, marker);
                return draft(owner, classroom, key);
            }));
            try {
                awaitDatabaseLock(marker, draft);
            } finally {
                commitLegacy.countDown();
            }
            assertEquals(201, legacy.get(10, TimeUnit.SECONDS).getStatusCode().value());
            var rejected = assertThrows(ExecutionException.class, () -> draft.get(10, TimeUnit.SECONDS));
            assertEquals("ASSIGNMENT_CONFLICT", assertInstanceOf(ApiException.class, rejected.getCause()).getCode());
            assertEquals(1, jdbc.queryForObject(
                    "SELECT count(*) FROM assignments WHERE teacher_id = ? AND creation_request_id = ?",
                    Integer.class, owner.getId(), key));
        }
    }

    private org.springframework.http.ResponseEntity<AssignmentResponse> createLegacy(UUID key) {
        var request = new AssignmentRequest();
        request.setClassId(classroom.getClassId());
        request.setCreationRequestId(key);
        request.setTitle("Legacy paper assignment");
        request.setOperationType("ADDITION");
        request.setMaxScore(10);
        return legacyAssignments.createAssignment(request, () -> owner.getEmail());
    }

    private void awaitDatabaseLock(String marker, java.util.concurrent.Future<?> operation) throws Exception {
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
        boolean waiting;
        do {
            waiting = Boolean.TRUE.equals(jdbc.queryForObject("""
                    SELECT EXISTS(SELECT 1 FROM pg_stat_activity
                        WHERE application_name = ? AND wait_event_type = 'Lock')
                    """, Boolean.class, marker));
            if (!waiting) Thread.sleep(25);
        } while (!waiting && !operation.isDone() && System.nanoTime() < deadline);
        assertTrue(waiting, "Expected an overlapping database lock wait");
    }

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
    void draftCreationKeyIsSerializedAcrossClassesOwnedByTheSameTeacher() throws Exception {
        Classroom other = new Classroom();
        other.setName("Second concurrency fixture");
        other.setGradeLevel(3);
        other.setTeacher(owner);
        classrooms.saveAndFlush(other);
        UUID key = UUID.randomUUID();
        var firstWritten = new CountDownLatch(1);
        var commitFirst = new CountDownLatch(1);
        var transactions = new TransactionTemplate(transactionManager);
        String marker = "draft-idempotency-" + UUID.randomUUID();
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            var first = workers.submit(() -> transactions.execute(status -> {
                var created = draft(owner, classroom, key);
                assignments.flush();
                firstWritten.countDown();
                await(commitFirst);
                return created;
            }));
            var second = workers.submit(() -> {
                await(firstWritten);
                return transactions.execute(status -> {
                    jdbc.queryForObject("SELECT set_config('application_name', ?, true)", String.class, marker);
                    return draft(owner, other, key);
                });
            });
            try {
                long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
                boolean waiting;
                do {
                    waiting = Boolean.TRUE.equals(jdbc.queryForObject("""
                            SELECT EXISTS(SELECT 1 FROM pg_stat_activity
                                WHERE application_name = ? AND wait_event_type = 'Lock')
                            """, Boolean.class, marker));
                    if (!waiting) Thread.sleep(25);
                } while (!waiting && !second.isDone() && System.nanoTime() < deadline);
                assertTrue(waiting, "The second create must overlap the first uncommitted transaction");
            } finally {
                commitFirst.countDown();
            }
            var created = first.get(10, TimeUnit.SECONDS);
            var rejected = assertThrows(ExecutionException.class, () -> second.get(10, TimeUnit.SECONDS));
            assertEquals("ASSIGNMENT_CONFLICT", assertInstanceOf(ApiException.class, rejected.getCause()).getCode());
            assertEquals(created.assignmentId(), draft(owner, classroom, key).assignmentId());
            assertEquals(1, jdbc.queryForObject("SELECT count(*) FROM assignments WHERE teacher_id = ? AND creation_request_id = ?",
                    Integer.class, owner.getId(), key));
        }
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
        long submissionsBefore = count("submissions");
        long decisionsBefore = count("teacher_decisions");
        long jobsBefore = count("ai_jobs");
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
        assertEquals(submissionsBefore, count("submissions"));
        assertEquals(decisionsBefore, count("teacher_decisions"));
        assertEquals(jobsBefore, count("ai_jobs"));
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

package com.mathvisionkids.api.submission;

import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.common.ApiException;
import com.fasterxml.jackson.databind.node.IntNode;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.UUID;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@EnabledIfEnvironmentVariable(named = "MATHVISION_ASSIGNED_RECOVERY_IT", matches = "true")
class AssignedUploadRecoveryIntegrationTest {
    private static final String SCHEMA = "assigned_recovery_it_" + UUID.randomUUID().toString().replace("-", "");

    @DynamicPropertySource
    static void configure(DynamicPropertyRegistry registry) {
        String base = System.getenv("ASSIGNED_IT_DB_URL");
        registry.add("spring.datasource.url", () -> base + "?currentSchema=" + SCHEMA + ",public");
        registry.add("spring.datasource.username", () -> System.getenv("ASSIGNED_IT_DB_USER"));
        registry.add("spring.datasource.password", () -> System.getenv("ASSIGNED_IT_DB_PASSWORD"));
        registry.add("spring.flyway.schemas", () -> SCHEMA);
        registry.add("spring.flyway.default-schema", () -> SCHEMA);
        registry.add("spring.jpa.properties.hibernate.default_schema", () -> SCHEMA);
        registry.add("app.assigned-upload.cleanup-delay-ms", () -> "3600000");
        registry.add("minio.bucket-name", () -> "mathvision-phase3-acceptance");
    }

    @Autowired JdbcTemplate jdbc;
    @Autowired AssignedUploadReservation reservations;
    @Autowired ObjectStorageService storage;
    @Autowired AssignedTeacherReview review;
    @Autowired com.mathvisionkids.api.admin.AdminService adminService;

    @Test
    void revokedStudentCannotConfirmStoredUploadAndExpiredObjectIsRemoved() throws Exception {
        String email = "student-" + UUID.randomUUID() + "@assigned-recovery.test";
        UUID assignment = seedAssignment(email);
        var output = new ByteArrayOutputStream();
        ImageIO.write(new BufferedImage(32, 32, BufferedImage.TYPE_INT_RGB), "png", output);
        var image = AssignedWebImage.read(
                new MockMultipartFile("image", "synthetic.png", "image/png", output.toByteArray()), true);
        UUID request = UUID.randomUUID();
        var attempt = reservations.reserve(email, assignment, request, 0, image.inputDigest(), image.storedDigest());
        var worker = new AssignedUploadCleanup(jdbc, storage, reservations);
        try {
            reservations.recordPreparedImage(attempt, image);
            storage.storeAssignedImage(attempt.objectKey(), image.bytes(), image.contentType());
            jdbc.update("""
                    DELETE FROM classroom_students
                    WHERE class_id = (SELECT class_id FROM assignments WHERE assignment_id = ?)
                      AND student_id = (SELECT id FROM users WHERE email = ?)
                    """, assignment, email);
            assertEquals("NOT_FOUND", assertThrows(ApiException.class,
                    () -> reservations.confirm(email, assignment, request, attempt, image)).getCode());
            jdbc.update("UPDATE assigned_upload_attempts SET recover_after = now() WHERE attempt_id = ?", attempt.id());
            worker.cleanExpired();
            assertEquals(0, jdbc.queryForObject("SELECT count(*) FROM submission_images WHERE submission_id = ?",
                    Integer.class, attempt.submissionId()));
            jdbc.update("UPDATE assigned_upload_attempts SET expires_at = now() - INTERVAL '1 hour', recover_after = now() WHERE attempt_id = ?",
                    attempt.id());
            worker.cleanExpired();
            assertEquals("EXPIRED", jdbc.queryForObject("SELECT state FROM assigned_upload_attempts WHERE attempt_id = ?",
                    String.class, attempt.id()));
            jdbc.update("UPDATE assigned_upload_attempts SET cleanup_after = now() WHERE attempt_id = ?", attempt.id());
            worker.cleanExpired();
            assertThrows(java.io.IOException.class, () -> storage.loadBytes(attempt.objectKey()));
            // Simulate a PUT that was already in flight when the first cleanup ran.
            storage.storeAssignedImage(attempt.objectKey(), image.bytes(), image.contentType());
            assertArrayEquals(image.bytes(), storage.loadBytes(attempt.objectKey()));
            jdbc.update("UPDATE assigned_upload_attempts SET cleanup_after = now() WHERE attempt_id = ?", attempt.id());
            var failingStorage = org.mockito.Mockito.mock(ObjectStorageService.class);
            org.mockito.Mockito.doThrow(new java.io.IOException("Fixture deletion failure"))
                    .when(failingStorage).delete(attempt.objectKey());
            new AssignedUploadCleanup(jdbc, failingStorage, reservations).cleanExpired();
            org.mockito.Mockito.verify(failingStorage).delete(attempt.objectKey());
            worker.cleanExpired();
            assertArrayEquals(image.bytes(), storage.loadBytes(attempt.objectKey()));
            jdbc.update("UPDATE assigned_upload_attempts SET cleanup_after = now() WHERE attempt_id = ?", attempt.id());
            worker.cleanExpired();
            assertThrows(java.io.IOException.class, () -> storage.loadBytes(attempt.objectKey()));
            assertEquals(0, jdbc.queryForObject("SELECT count(*) FROM submission_images WHERE submission_id = ?",
                    Integer.class, attempt.submissionId()));
        } finally {
            storage.delete(attempt.objectKey());
        }
    }

    @Test
    void privacyRejectionKeepsConfirmedImageAndCreatesNoReplacementAttempt() throws Exception {
        String email = "student-" + UUID.randomUUID() + "@assigned-recovery.test";
        UUID assignment = seedAssignment(email);
        var output = new ByteArrayOutputStream();
        ImageIO.write(new BufferedImage(32, 32, BufferedImage.TYPE_INT_RGB), "png", output);
        var image = new MockMultipartFile("image", "synthetic.png", "image/png", output.toByteArray());
        var privacy = org.mockito.Mockito.mock(AssignedImagePrivacy.class);
        var controller = new AssignedStudentUploadController(reservations, storage, privacy);
        UUID originalRequest = UUID.randomUUID();
        var receipt = controller.upload(() -> email, assignment, originalRequest, 0, true, image).getBody();
        assertNotNull(receipt);
        UUID submission = receipt.submissionId();
        String key = jdbc.queryForObject("SELECT file_path FROM submission_images WHERE submission_id = ?",
                String.class, submission);
        try {
            org.mockito.Mockito.doThrow(new ApiException("IMAGE_PRIVACY_REVIEW", "Fixture rejected image",
                    org.springframework.http.HttpStatus.UNPROCESSABLE_ENTITY))
                    .when(privacy).requireClear(org.mockito.ArgumentMatchers.any());
            assertEquals(receipt, controller.upload(() -> email, assignment, originalRequest, 0, true, image).getBody());
            var changed = new BufferedImage(32, 32, BufferedImage.TYPE_INT_RGB);
            changed.setRGB(0, 0, 0xffffff);
            var changedOutput = new ByteArrayOutputStream();
            ImageIO.write(changed, "png", changedOutput);
            var replacement = new MockMultipartFile("image", "changed.png", "image/png", changedOutput.toByteArray());
            assertEquals(org.springframework.http.HttpStatus.CONFLICT, assertThrows(ApiException.class,
                    () -> controller.upload(() -> email, assignment, originalRequest, 0, true, replacement)).getStatus());
            assertEquals("IMAGE_PRIVACY_REVIEW", assertThrows(ApiException.class,
                    () -> controller.upload(() -> email, assignment, UUID.randomUUID(), 1, true, image)).getCode());
            assertEquals(1, reservations.status(email, assignment).imageVersion());
            assertEquals(1, jdbc.queryForObject("SELECT count(*) FROM assigned_upload_attempts WHERE submission_id = ?",
                    Integer.class, submission));
            assertArrayEquals(AssignedWebImage.read(image, true).bytes(), storage.loadBytes(key));
            var download = controller.currentImage(() -> email, assignment);
            assertArrayEquals(storage.loadBytes(key), download.getBody());
            assertEquals("no-store", download.getHeaders().getCacheControl());
            assertEquals("NOT_FOUND", assertThrows(ApiException.class,
                    () -> controller.currentImage(() -> "other-student@assigned-recovery.test", assignment)).getCode());
            jdbc.update("""
                    DELETE FROM classroom_students
                    WHERE class_id = (SELECT class_id FROM assignments WHERE assignment_id = ?)
                      AND student_id = (SELECT id FROM users WHERE email = ?)
                    """, assignment, email);
            assertEquals("NOT_FOUND", assertThrows(ApiException.class,
                    () -> controller.upload(() -> email, assignment, originalRequest, 0, true, image)).getCode());
            assertEquals("NOT_FOUND", assertThrows(ApiException.class,
                    () -> controller.currentImage(() -> email, assignment)).getCode());
        } finally {
            storage.delete(key);
        }
    }

    @Test
    void twoWorkersRecoverAStoredUploadExactlyOnceAndDoNotOverwriteIt() throws Exception {
        recoverStoredUpload(false, false);
    }

    @Test
    void reconcilesStoredUploadAfterBackendDowntimePastReservationExpiry() throws Exception {
        recoverStoredUpload(false, true);
    }

    @Test
    @EnabledIfEnvironmentVariable(named = "ASSIGNED_IT_RESTART_JAR", matches = ".+")
    void freshBackendProcessRecoversAStoredUploadWithoutBrowserReplay() throws Exception {
        recoverStoredUpload(true, false);
    }

    private void recoverStoredUpload(boolean freshProcess, boolean expired) throws Exception {
        String email = "student-" + UUID.randomUUID() + "@assigned-recovery.test";
        UUID assignment = seedAssignment(email);
        var output = new ByteArrayOutputStream();
        ImageIO.write(new BufferedImage(32, 32, BufferedImage.TYPE_INT_RGB), "png", output);
        var image = AssignedWebImage.read(
                new MockMultipartFile("image", "synthetic.png", "image/png", output.toByteArray()), true);
        UUID request = UUID.randomUUID();
        var attempt = reservations.reserve(email, assignment, request, 0, image.inputDigest(), image.storedDigest());
        try {
            reservations.recordPreparedImage(attempt, image);
            storage.storeAssignedImage(attempt.objectKey(), image.bytes(), image.contentType());
            assertThrows(java.io.IOException.class, () ->
                    storage.storeAssignedImage(attempt.objectKey(), new byte[] {1, 2, 3}, image.contentType()));
            assertArrayEquals(image.bytes(), storage.loadBytes(attempt.objectKey()),
                    "MinIO must honor the create-only write");
            assertEquals(0, reservations.status(email, assignment).imageVersion());
            assertEquals("UPLOADING", reservations.status(email, assignment).status());
            jdbc.update("UPDATE assigned_upload_attempts SET recover_after = now() WHERE attempt_id = ?", attempt.id());
            new AssignedUploadCleanup(jdbc, storage, reservations).cleanExpired();
            assertEquals(0, reservations.status(email, assignment).imageVersion(),
                    "Recovery must leave a live upload to its client before inspecting it after the deadline");
            if (expired) {
                jdbc.update("UPDATE assigned_upload_attempts SET expires_at = now() - INTERVAL '2 hours' WHERE attempt_id = ?",
                        attempt.id());
            } else {
                jdbc.update("UPDATE assigned_upload_attempts SET expires_at = now() WHERE attempt_id = ?", attempt.id());
            }

            if (freshProcess) {
                recoverInFreshProcess(email, assignment);
            } else try (var pool = Executors.newFixedThreadPool(2)) {
                var first = pool.submit(new AssignedUploadCleanup(jdbc, storage, reservations)::cleanExpired);
                var second = pool.submit(new AssignedUploadCleanup(jdbc, storage, reservations)::cleanExpired);
                first.get(30, TimeUnit.SECONDS);
                second.get(30, TimeUnit.SECONDS);
            }

            var confirmed = reservations.status(email, assignment);
            assertEquals(1, confirmed.imageVersion());
            assertEquals("AWAITING_REVIEW", confirmed.status());
            assertEquals("CONFIRMED", reservations.reserve(email, assignment, request, 0, image.inputDigest(), image.storedDigest()).state());
            assertEquals(1, jdbc.queryForObject("SELECT count(*) FROM submission_images WHERE submission_id = ?",
                    Integer.class, attempt.submissionId()));
        } finally {
            storage.delete(attempt.objectKey());
        }
    }

    private void recoverInFreshProcess(String email, UUID assignment) throws Exception {
        var log = java.nio.file.Files.createTempFile("assigned-recovery-process-", ".log");
        String executable = java.nio.file.Path.of(System.getProperty("java.home"), "bin", "java.exe").toString();
        if (!java.nio.file.Files.exists(java.nio.file.Path.of(executable))) {
            executable = java.nio.file.Path.of(System.getProperty("java.home"), "bin", "java").toString();
        }
        var config = new ProcessBuilder(executable, "-jar", System.getenv("ASSIGNED_IT_RESTART_JAR"),
                "--server.port=0", "--server.address=127.0.0.1",
                "--spring.profiles.active=assigned-recovery",
                "--spring.flyway.default-schema=" + SCHEMA,
                "--spring.flyway.schemas=" + SCHEMA,
                "--spring.jpa.properties.hibernate.default_schema=" + SCHEMA,
                "--minio.bucket-name=mathvision-phase3-acceptance",
                "--app.assigned-upload.cleanup-delay-ms=250");
        config.environment().put("DB_URL", System.getenv("ASSIGNED_IT_DB_URL") + "?currentSchema=" + SCHEMA + ",public");
        config.environment().put("DB_USERNAME", System.getenv("ASSIGNED_IT_DB_USER"));
        config.environment().put("DB_PASSWORD", System.getenv("ASSIGNED_IT_DB_PASSWORD"));
        var process = config.redirectErrorStream(true).redirectOutput(log.toFile()).start();
        try {
            long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(75);
            while (process.isAlive() && System.nanoTime() < deadline) {
                if (reservations.status(email, assignment).imageVersion() == 1) return;
                Thread.sleep(250);
            }
            fail("Fresh backend did not recover the image. Process output: " + log);
        } finally {
            process.destroy();
            if (!process.waitFor(5, TimeUnit.SECONDS)) process.destroyForcibly().waitFor(5, TimeUnit.SECONDS);
        }
    }

    @Test
    void studentReplacesReturnedImageAndReceivesGradeForTheNewVersion() throws Exception {
        String email = "student-" + UUID.randomUUID() + "@assigned-recovery.test";
        UUID assignment = seedAssignment(email);
        var original = new ByteArrayOutputStream();
        var pixels = new BufferedImage(32, 32, BufferedImage.TYPE_INT_RGB);
        ImageIO.write(pixels, "png", original);
        var controller = new AssignedStudentUploadController(reservations, storage,
                org.mockito.Mockito.mock(AssignedImagePrivacy.class));
        var first = controller.upload(() -> email, assignment, UUID.randomUUID(), 0, true,
                new MockMultipartFile("image", "first.png", "image/png", original.toByteArray())).getBody();
        assertNotNull(first);
        String teacher = jdbc.queryForObject("""
                SELECT u.email FROM users u JOIN assignments a ON a.teacher_id = u.id WHERE a.assignment_id = ?
                """, String.class, assignment);
        try {
            review.returnImage(teacher, first.submissionId(),
                    new AssignedTeacherReview.ReturnImage(1, "UNREADABLE", "Chụp rõ phần bài giải."));
            var returned = reservations.status(email, assignment);
            assertEquals("RETAKE_REQUESTED", returned.status());
            assertNull(returned.score());
            assertEquals("Chụp rõ phần bài giải.", returned.retakeInstruction());
            assertEquals(0, jdbc.queryForObject("SELECT count(*) FROM teacher_decisions WHERE submission_id = ?",
                    Integer.class, first.submissionId()));

            pixels.setRGB(0, 0, 0xffffff);
            var replacement = new ByteArrayOutputStream();
            ImageIO.write(pixels, "png", replacement);
            var second = controller.upload(() -> email, assignment, UUID.randomUUID(), 1, true,
                    new MockMultipartFile("image", "second.png", "image/png", replacement.toByteArray())).getBody();
            assertNotNull(second);
            assertEquals(first.submissionId(), second.submissionId());
            assertEquals(2, second.imageVersion());
            assertThrows(ApiException.class, () -> review.image(teacher, first.submissionId(), 1));
            assertThrows(ApiException.class, () -> review.releaseGrade(teacher, first.submissionId(),
                    new AssignedTeacherReview.Grade(UUID.randomUUID(), 1, true, true, IntNode.valueOf(8), "Bài cũ")));

            review.releaseGrade(teacher, first.submissionId(),
                    new AssignedTeacherReview.Grade(UUID.randomUUID(), 2, true, true, IntNode.valueOf(8), "Làm tốt!"));
            var released = reservations.status(email, assignment);
            assertEquals("GRADE_RELEASED", released.status());
            assertEquals(8, released.score());
            assertEquals("Làm tốt!", released.feedback());
            assertEquals(2, released.imageVersion());
        } finally {
            for (String key : jdbc.queryForList("SELECT object_key FROM assigned_upload_attempts WHERE submission_id = ?",
                    String.class, first.submissionId())) storage.delete(key);
        }
    }

    @Test
    void currentTeacherAloneCanReleaseOneGradeAfterHandover() throws Exception {
        String email = "student-" + UUID.randomUUID() + "@assigned-recovery.test";
        UUID assignment = seedAssignment(email);
        var output = new ByteArrayOutputStream();
        ImageIO.write(new BufferedImage(32, 32, BufferedImage.TYPE_INT_RGB), "png", output);
        var image = new MockMultipartFile("image", "synthetic.png", "image/png", output.toByteArray());
        var receipt = new AssignedStudentUploadController(reservations, storage, org.mockito.Mockito.mock(AssignedImagePrivacy.class))
                .upload(() -> email, assignment, UUID.randomUUID(), 0, true, image).getBody();
        assertNotNull(receipt);
        UUID submission = receipt.submissionId();
        String oldTeacher = jdbc.queryForObject("""
                SELECT u.email FROM users u JOIN assignments a ON a.teacher_id = u.id WHERE a.assignment_id = ?
                """, String.class, assignment);
        String objectKey = review.image(oldTeacher, submission, 1).key();
        try {
            String newTeacher = "new-" + UUID.randomUUID() + "@assigned-recovery.test";
            UUID teacherId = seedTeacher(newTeacher);
            String adminEmail = "admin-" + UUID.randomUUID() + "@assigned-recovery.test";
            jdbc.update("""
                    INSERT INTO users(id,email,password_hash,role,display_name)
                    VALUES (?,?,'unused','ADMIN','Synthetic admin')
                    """, UUID.randomUUID(), adminEmail);
            UUID classroomId = jdbc.queryForObject("SELECT class_id FROM assignments WHERE assignment_id = ?",
                    UUID.class, assignment);
            adminService.assignTeacher(classroomId, teacherId, adminEmail);
            assertThrows(ApiException.class, () -> review.image(oldTeacher, submission, 1));
            assertThrows(ApiException.class, () -> reservations.status("other-student@assigned-recovery.test", assignment));
            assertEquals(objectKey, review.image(newTeacher, submission, 1).key());
            var zero = new AssignedTeacherReview.Grade(UUID.randomUUID(), 1, true, true, IntNode.valueOf(0), "Try again");
            var eight = new AssignedTeacherReview.Grade(UUID.randomUUID(), 1, true, true, IntNode.valueOf(8), "Good");
            assertThrows(ApiException.class, () -> review.releaseGrade(oldTeacher, submission, zero));
            assertThrows(ApiException.class, () -> review.releaseGrade(newTeacher, submission,
                    new AssignedTeacherReview.Grade(UUID.randomUUID(), 2, true, true, IntNode.valueOf(0), "")));
            assertThrows(ApiException.class, () -> review.releaseGrade(newTeacher, submission,
                    new AssignedTeacherReview.Grade(UUID.randomUUID(), 1, true, true, IntNode.valueOf(11), "")));

            boolean zeroWon;
            try (var pool = Executors.newFixedThreadPool(2)) {
                var first = pool.submit(() -> releaseOrConflict(newTeacher, submission, zero));
                var second = pool.submit(() -> releaseOrConflict(newTeacher, submission, eight));
                zeroWon = first.get(30, TimeUnit.SECONDS);
                assertNotEquals(zeroWon, second.get(30, TimeUnit.SECONDS));
            }
            review.releaseGrade(newTeacher, submission, zeroWon ? zero : eight);
            assertEquals(zeroWon ? 0 : 8, reservations.status(email, assignment).score());
            assertEquals(1, jdbc.queryForObject("SELECT count(*) FROM teacher_decisions WHERE submission_id = ?",
                    Integer.class, submission));
            assertThrows(ApiException.class, () -> new AssignedStudentUploadController(reservations, storage, org.mockito.Mockito.mock(AssignedImagePrivacy.class))
                    .upload(() -> email, assignment, UUID.randomUUID(), 1, true, image));
        } finally {
            storage.delete(objectKey);
        }
    }

    private boolean releaseOrConflict(String teacher, UUID submission, AssignedTeacherReview.Grade grade) {
        try {
            review.releaseGrade(teacher, submission, grade);
            return true;
        } catch (ApiException exception) {
            assertEquals("REVIEW_CONFLICT", exception.getCode());
            return false;
        }
    }

    private UUID seedAssignment(String email) {
        UUID student = UUID.randomUUID(), classroom = UUID.randomUUID();
        UUID assignment = UUID.randomUUID(), publication = UUID.randomUUID();
        jdbc.update("INSERT INTO users(id,email,password_hash,role,display_name) VALUES (?,?,'unused','STUDENT','Synthetic student')", student, email);
        jdbc.update("INSERT INTO students(student_id,grade_level) VALUES (?,3)", student);
        UUID teacher = seedTeacher("teacher-" + UUID.randomUUID() + "@assigned-recovery.test");
        jdbc.update("INSERT INTO classrooms(class_id,name,grade_level,teacher_id) VALUES (?,'Synthetic class',3,?)", classroom, teacher);
        jdbc.update("INSERT INTO classroom_students(class_id,student_id) VALUES (?,?)", classroom, student);
        jdbc.update("""
                INSERT INTO assignments(assignment_id,class_id,teacher_id,title,operation_type,max_score,status,prompt)
                VALUES (?,?,?,'Synthetic assignment','VERTICAL_ADDITION',10,'PUBLISHED','12 + 34')
                """, assignment, classroom, teacher);
        jdbc.update("INSERT INTO assignment_publications(publication_id,assignment_id) VALUES (?,?)", publication, assignment);
        jdbc.update("INSERT INTO assignment_recipients(publication_id,student_id) VALUES (?,?)", publication, student);
        return assignment;
    }

    private UUID seedTeacher(String email) {
        UUID teacher = UUID.randomUUID();
        jdbc.update("INSERT INTO users(id,email,password_hash,role,display_name) VALUES (?,?,'unused','TEACHER','Synthetic teacher')", teacher, email);
        jdbc.update("INSERT INTO teachers(teacher_id) VALUES (?)", teacher);
        return teacher;
    }
}

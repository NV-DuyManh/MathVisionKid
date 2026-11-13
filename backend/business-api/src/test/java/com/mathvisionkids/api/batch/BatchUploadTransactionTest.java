package com.mathvisionkids.api.batch;

import com.mathvisionkids.api.analysis.AiAnalysisGateway;
import com.mathvisionkids.api.assignment.*;
import com.mathvisionkids.api.classroom.*;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.submission.SubmissionRepository;
import com.mathvisionkids.api.user.*;
import java.io.IOException;
import java.util.*;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.support.TransactionTemplate;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@SpringBootTest
@ActiveProfiles("test")
class BatchUploadTransactionTest {
    @Autowired BatchService service;
    @Autowired BatchRepository batches;
    @Autowired TeacherRepository teachers;
    @Autowired StudentRepository students;
    @Autowired ClassroomRepository classrooms;
    @Autowired AssignmentRepository assignments;
    @Autowired SubmissionRepository submissions;
    @Autowired TransactionTemplate transactions;
    @MockBean ObjectStorageService storage;
    @MockBean AiAnalysisGateway gateway;
    String email;
    UUID batch, pupil;

    @BeforeEach void fixture() {
        transactions.executeWithoutResult(status -> {
            Teacher teacher = new Teacher(); teacher.setRole("TEACHER"); teacher.setDisplayName("Synthetic teacher");
            teacher.setEmail(UUID.randomUUID()+"@batch.test"); teacher.setPasswordHash("unused"); teacher = teachers.save(teacher);
            email = teacher.getEmail();
            Student student = new Student(); student.setRole("STUDENT"); student.setDisplayName("Synthetic pupil");
            student.setEmail(UUID.randomUUID()+"@batch.test"); student.setPasswordHash("unused"); student.setGradeLevel(5);
            student = students.save(student); pupil = student.getId();
            Classroom classroom = new Classroom(); classroom.setName("Synthetic class"); classroom.setGradeLevel(5); classroom.setTeacher(teacher);
            classroom.getStudents().add(student); classroom = classrooms.save(classroom);
            Assignment assignment = new Assignment(); assignment.setTitle("Synthetic batch"); assignment.setOperationType("ADDITION");
            assignment.setTeacher(teacher); assignment.setClassroom(classroom); assignment.setMaxScore(10);
            assignment = assignments.save(assignment);
            batch = service.createBatch(email, assignment.getAssignmentId()).getBatchId();
        });
    }
    MockMultipartFile image() {
        return new MockMultipartFile("images", "synthetic.png", "image/png", Base64.getDecoder().decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aBXsAAAAASUVORK5CYII="));
    }
    BatchImageMapping mapping(int index) {
        var mapping = new BatchImageMapping(); mapping.setFileIndex(index); mapping.setStudentId(pupil); return mapping;
    }
    @Test void concurrentCreationWithSameKeyReturnsOneBatch() throws Exception {
        UUID assignmentId = transactions.execute(status -> batches.findById(batch).orElseThrow().getAssignment().getAssignmentId());
        UUID key = UUID.randomUUID();
        var start = new java.util.concurrent.CountDownLatch(1);
        try (var workers = java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()) {
            var first = workers.submit(() -> { start.await(); return service.createBatch(email, assignmentId, key); });
            var second = workers.submit(() -> { start.await(); return service.createBatch(email, assignmentId, key); });
            start.countDown();
            var a = first.get(10, java.util.concurrent.TimeUnit.SECONDS);
            var b = second.get(10, java.util.concurrent.TimeUnit.SECONDS);
            assertNotEquals(a.created(), b.created());
            assertEquals(a.batch().getBatchId(), b.batch().getBatchId());
        }
    }
    @Test void failedSecondWriteRollsBackDatabaseAndFirstObjectAndAllowsRetry() throws Exception {
        when(storage.store(any(), anyString())).thenReturn("synthetic/first.png").thenThrow(new IOException("synthetic storage failure"));
        assertThrows(ApiException.class, () -> service.uploadImages(email, batch, List.of(image(), image()), List.of(mapping(0), mapping(1))));
        verify(storage).delete("synthetic/first.png");
        assertTrue(submissions.findByBatch_BatchId(batch).isEmpty());
        assertEquals("CREATED", batches.findById(batch).orElseThrow().getStatus());
        verifyNoInteractions(gateway);
        doReturn("synthetic/retry.png").when(storage).store(any(), anyString());
        service.uploadImages(email, batch, List.of(image()), List.of(mapping(0)));
        verify(gateway, timeout(3000)).analyze(any());
        assertEquals(1, submissions.findByBatch_BatchId(batch).size());
        assertThrows(ApiException.class, () -> service.uploadImages(email, batch, List.of(image()), List.of(mapping(0))));
        verify(storage, times(3)).store(any(), anyString());
    }
    @Test void invalidLaterMappingAndNullManifestNeverStartStorageWrites() {
        var invalid = mapping(1); invalid.setStudentId(UUID.randomUUID());
        assertThrows(ApiException.class, () -> service.uploadImages(email, batch, List.of(image(), image()), List.of(mapping(0), invalid)));
        assertThrows(ApiException.class, () -> service.uploadImages(email, batch, List.of(image()), null));
        verifyNoInteractions(storage, gateway);
        assertTrue(submissions.findByBatch_BatchId(batch).isEmpty());
    }
    @Test void dispatchFailureIsTerminalAndVisibleToTeacherRatherThanStuckProcessing() throws Exception {
        when(storage.store(any(), anyString())).thenReturn("synthetic/dispatch.png");
        doThrow(new IllegalStateException("synthetic dispatch failure")).when(gateway).analyze(any());
        service.uploadImages(email, batch, List.of(image()), List.of(mapping(0)));
        long deadline = System.nanoTime() + java.time.Duration.ofSeconds(3).toNanos();
        BatchResponse result;
        do { result = service.getBatch(email, batch); if (result.processedCount() == 1) break; Thread.sleep(20); }
        while (System.nanoTime() < deadline);
        assertEquals("FAILED", result.status());
        assertEquals(1, result.processedCount());
        assertEquals(1, result.failedCount());
        assertEquals("FAILED", result.submissions().getFirst().status());
        assertTrue(service.getBatchReviewQueue(email, batch).isEmpty());
    }
}

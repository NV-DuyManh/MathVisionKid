package com.mathvisionkids.api.dashboard;

import com.mathvisionkids.api.batch.Batch;
import com.mathvisionkids.api.batch.BatchRepository;
import com.mathvisionkids.api.submission.Submission;
import com.mathvisionkids.api.submission.SubmissionRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class DashboardServiceTest {
    @ParameterizedTest
    @CsvSource({
            "2026-11-10T16:59:59.999999Z, 0",
            "2026-11-10T17:00:00Z, 1",
            "2026-11-10T23:15:00Z, 1",
            "2026-11-11T16:59:59.999999Z, 1",
            "2026-11-11T17:00:00Z, 0"
    })
    void countsSubmissionsWithinTheVietnameseCalendarDay(String submittedAt, int expected) {
        var teacherRepository = mock(TeacherRepository.class);
        var batchRepository = mock(BatchRepository.class);
        var submissionRepository = mock(SubmissionRepository.class);
        var teacher = new Teacher();
        teacher.setId(UUID.randomUUID());
        var batch = new Batch();
        batch.setBatchId(UUID.randomUUID());
        var submission = new Submission();
        submission.setStatus("TEACHER_APPROVED");
        submission.setCreatedAt(Instant.parse(submittedAt));
        var email = "teacher@example.test";
        when(teacherRepository.findByEmail(email)).thenReturn(Optional.of(teacher));
        when(batchRepository.findOwnedByAssignedTeacherOrderByCreatedAtDesc(teacher.getId())).thenReturn(List.of(batch));
        when(submissionRepository.findByBatch_BatchId(batch.getBatchId())).thenReturn(List.of(submission));

        var service = new DashboardService(teacherRepository, batchRepository, submissionRepository);
        var dashboard = service.getDashboard(email, Instant.parse("2026-11-11T16:59:59.999999Z"));

        assertEquals(expected, dashboard.getTodayTotal());
        assertEquals(1, dashboard.getProcessedCount());
    }
}

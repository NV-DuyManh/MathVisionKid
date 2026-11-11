package com.mathvisionkids.api.dashboard;

import com.mathvisionkids.api.batch.Batch;
import com.mathvisionkids.api.batch.BatchRepository;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.submission.Submission;
import com.mathvisionkids.api.submission.SubmissionRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Set;

@Service
public class DashboardService {

    private final TeacherRepository teacherRepository;
    private final BatchRepository batchRepository;
    private final SubmissionRepository submissionRepository;

    public DashboardService(TeacherRepository teacherRepository,
                            BatchRepository batchRepository,
                            SubmissionRepository submissionRepository) {
        this.teacherRepository = teacherRepository;
        this.batchRepository = batchRepository;
        this.submissionRepository = submissionRepository;
    }

    private static final Set<String> TERMINAL_STATES = Set.of(
            "TEACHER_APPROVED", "TEACHER_OVERRIDDEN"
    );

    @Transactional(readOnly = true)
    public DashboardResponse getDashboard(String teacherEmail) {
        Teacher teacher = teacherRepository.findByEmail(teacherEmail)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Teacher not found", HttpStatus.NOT_FOUND));

        List<Batch> batches = batchRepository.findByTeacher_IdOrderByCreatedAtDesc(teacher.getId());

        Instant todayStart = LocalDate.now(ZoneOffset.UTC).atStartOfDay().toInstant(ZoneOffset.UTC);

        int todayTotal = 0;
        int processedCount = 0;
        int reviewRequiredCount = 0;
        var progressByBatch = new java.util.HashMap<java.util.UUID, com.mathvisionkids.api.batch.BatchResponse>();

        for (Batch batch : batches) {
            List<Submission> submissions = submissionRepository.findByBatch_BatchId(batch.getBatchId());
            var progress = com.mathvisionkids.api.batch.BatchResponse.from(batch, submissions);
            progressByBatch.put(batch.getBatchId(), progress);
            reviewRequiredCount += progress.pendingReviewCount();
            for (Submission s : submissions) {
                if (s.getCreatedAt() != null && s.getCreatedAt().isAfter(todayStart)) {
                    todayTotal++;
                }
                if (TERMINAL_STATES.contains(s.getStatus())) {
                    processedCount++;
                }
            }
        }

        List<DashboardResponse.RecentBatchSummary> recentBatches = batches.stream()
                .limit(10)
                .map(b -> {
                    DashboardResponse.RecentBatchSummary summary = new DashboardResponse.RecentBatchSummary();
                    summary.setBatchId(b.getBatchId());
                    var progress = progressByBatch.get(b.getBatchId());
                    summary.setAssignmentTitle(b.getAssignment() != null ? b.getAssignment().getTitle() : "");
                    summary.setStatus(progress.status());
                    summary.setTotalCount(progress.totalCount());
                    summary.setProcessedCount(progress.processedCount());
                    summary.setReviewRequiredCount(progress.reviewRequiredCount());
                    summary.setPendingReviewCount(progress.pendingReviewCount());
                    summary.setCreatedAt(b.getCreatedAt() != null ? b.getCreatedAt().toString() : "");
                    return summary;
                })
                .toList();

        DashboardResponse response = new DashboardResponse();
        response.setTodayTotal(todayTotal);
        response.setProcessedCount(processedCount);
        response.setReviewRequiredCount(reviewRequiredCount);
        response.setRecentBatches(recentBatches);
        return response;
    }
}

package com.mathvisionkids.api.dashboard;

import com.mathvisionkids.api.batch.BatchRepository;
import com.mathvisionkids.api.batch.BatchResponse;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;

@Service
public class DashboardService {

    private static final ZoneId SCHOOL_ZONE = ZoneId.of("Asia/Ho_Chi_Minh");

    private final TeacherRepository teacherRepository;
    private final BatchRepository batchRepository;

    public DashboardService(TeacherRepository teacherRepository,
                            BatchRepository batchRepository) {
        this.teacherRepository = teacherRepository;
        this.batchRepository = batchRepository;
    }

    @Transactional(readOnly = true)
    public DashboardResponse getDashboard(String teacherEmail) {
        return getDashboard(teacherEmail, Instant.now());
    }

    DashboardResponse getDashboard(String teacherEmail, Instant now) {
        Teacher teacher = teacherRepository.findByEmail(teacherEmail)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Teacher not found", HttpStatus.NOT_FOUND));

        LocalDate today = LocalDate.ofInstant(now, SCHOOL_ZONE);
        Instant todayStart = today.atStartOfDay(SCHOOL_ZONE).toInstant();
        Instant tomorrowStart = today.plusDays(1).atStartOfDay(SCHOOL_ZONE).toInstant();

        long todayTotal = 0;
        long processedCount = 0;
        long reviewRequiredCount = 0;
        var response = new DashboardResponse();
        var recentBatches = new ArrayList<DashboardResponse.RecentBatchSummary>(10);
        for (var batch : batchRepository.findDashboardProgress(teacher.getId(), todayStart, tomorrowStart)) {
            todayTotal += batch.getTodayCount();
            processedCount += batch.getFinalizedCount();
            reviewRequiredCount += batch.getPendingReviewCount();
            if (response.getNextReviewBatchId() == null && batch.getPendingReviewCount() > 0) {
                response.setNextReviewBatchId(batch.getBatchId());
            }
            if (recentBatches.size() < 10) {
                var summary = new DashboardResponse.RecentBatchSummary();
                summary.setBatchId(batch.getBatchId());
                summary.setAssignmentTitle(batch.getAssignmentTitle());
                summary.setStatus(BatchResponse.progressStatus(batch.getStoredStatus(), batch.getTotalCount(),
                        batch.getProcessedCount(), batch.getFailedCount()));
                summary.setTotalCount(Math.toIntExact(batch.getTotalCount()));
                summary.setProcessedCount(Math.toIntExact(batch.getProcessedCount()));
                summary.setReviewRequiredCount(Math.toIntExact(batch.getReviewRequiredCount()));
                summary.setPendingReviewCount(Math.toIntExact(batch.getPendingReviewCount()));
                summary.setCreatedAt(batch.getCreatedAt() != null ? batch.getCreatedAt().toString() : "");
                recentBatches.add(summary);
            }
        }
        response.setTodayTotal(Math.toIntExact(todayTotal));
        response.setProcessedCount(Math.toIntExact(processedCount));
        response.setReviewRequiredCount(Math.toIntExact(reviewRequiredCount));
        response.setRecentBatches(recentBatches);
        return response;
    }
}

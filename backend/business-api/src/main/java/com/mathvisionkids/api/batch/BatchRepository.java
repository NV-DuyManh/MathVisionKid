package com.mathvisionkids.api.batch;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.time.Instant;
import java.util.List;
import java.util.Set;
import java.util.UUID;

public interface BatchRepository extends JpaRepository<Batch, UUID> {
    java.util.Optional<Batch> findByTeacher_IdAndCreationRequestId(UUID teacherId, UUID creationRequestId);

    @org.springframework.data.jpa.repository.Lock(jakarta.persistence.LockModeType.PESSIMISTIC_WRITE)
    @org.springframework.data.jpa.repository.Query("select b from Batch b where b.batchId = :id")
    java.util.Optional<Batch> findForUpdate(@org.springframework.data.repository.query.Param("id") UUID id);
    default List<BatchProgress> findOwnedByAssignedTeacherProgress(UUID teacherId) {
        return summarizeOwnedByAssignedTeacher(teacherId, BatchResponse.TERMINAL, BatchResponse.REVIEW,
                BatchResponse.PENDING_REVIEW, BatchResponse.FINALIZED);
    }

    @Query("""
            select b.batchId as batchId, a.assignmentId as assignmentId, a.title as assignmentTitle,
                   c.name as className, b.status as storedStatus, b.createdAt as createdAt,
                   b.startedAt as startedAt, b.completedAt as completedAt,
                   count(s.submissionId) as totalCount,
                   sum(case when s.status in :terminal then 1 else 0 end) as processedCount,
                   sum(case when s.status in :review then 1 else 0 end) as reviewRequiredCount,
                   sum(case when s.status in :pending then 1 else 0 end) as pendingReviewCount,
                   sum(case when s.status in :finalized then 1 else 0 end) as finalizedCount,
                   sum(case when s.status = 'FAILED' then 1 else 0 end) as failedCount
            from Batch b
            join b.assignment a
            join a.classroom c
            left join Submission s on s.batch = b
            where b.teacher.id = :teacherId and c.teacher.id = :teacherId
            group by b.batchId, a.assignmentId, a.title, c.name, b.status, b.createdAt, b.startedAt, b.completedAt
            order by b.createdAt desc
            """)
    List<BatchProgress> summarizeOwnedByAssignedTeacher(@Param("teacherId") UUID teacherId,
            @Param("terminal") Set<String> terminal, @Param("review") Set<String> review,
            @Param("pending") Set<String> pending, @Param("finalized") Set<String> finalized);

    interface BatchProgress {
        UUID getBatchId();
        UUID getAssignmentId();
        String getAssignmentTitle();
        String getClassName();
        String getStoredStatus();
        Instant getCreatedAt();
        Instant getStartedAt();
        Instant getCompletedAt();
        long getTotalCount();
        long getProcessedCount();
        long getReviewRequiredCount();
        long getPendingReviewCount();
        long getFinalizedCount();
        long getFailedCount();
    }

    default List<DashboardBatch> findDashboardProgress(UUID teacherId, Instant dayStart, Instant nextDay) {
        return summarizeDashboard(teacherId, dayStart, nextDay, BatchResponse.TERMINAL, BatchResponse.REVIEW,
                BatchResponse.PENDING_REVIEW, BatchResponse.FINALIZED);
    }

    @Query("""
            select b.batchId as batchId, a.title as assignmentTitle, b.status as storedStatus, b.createdAt as createdAt,
                   count(s.submissionId) as totalCount,
                   sum(case when s.status in :terminal then 1 else 0 end) as processedCount,
                   sum(case when s.status in :review then 1 else 0 end) as reviewRequiredCount,
                   sum(case when s.status in :pending then 1 else 0 end) as pendingReviewCount,
                   sum(case when s.status in :finalized then 1 else 0 end) as finalizedCount,
                   sum(case when s.status = 'FAILED' then 1 else 0 end) as failedCount,
                   sum(case when s.createdAt >= :dayStart and s.createdAt < :nextDay then 1 else 0 end) as todayCount
            from Batch b
            join b.assignment a
            join a.classroom c
            left join Submission s on s.batch = b
            where b.teacher.id = :teacherId and c.teacher.id = :teacherId
            group by b.batchId, a.title, b.status, b.createdAt
            order by b.createdAt desc, b.batchId desc
            """)
    List<DashboardBatch> summarizeDashboard(@Param("teacherId") UUID teacherId,
            @Param("dayStart") Instant dayStart, @Param("nextDay") Instant nextDay,
            @Param("terminal") Set<String> terminal, @Param("review") Set<String> review,
            @Param("pending") Set<String> pending, @Param("finalized") Set<String> finalized);

    interface DashboardBatch {
        UUID getBatchId();
        String getAssignmentTitle();
        String getStoredStatus();
        Instant getCreatedAt();
        long getTotalCount();
        long getProcessedCount();
        long getReviewRequiredCount();
        long getPendingReviewCount();
        long getFinalizedCount();
        long getFailedCount();
        long getTodayCount();
    }
}

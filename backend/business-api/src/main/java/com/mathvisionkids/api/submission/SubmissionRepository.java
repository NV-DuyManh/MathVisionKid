package com.mathvisionkids.api.submission;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;
import java.util.Optional;
import java.util.Map;
import java.util.Set;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface SubmissionRepository extends JpaRepository<Submission, UUID> {
    @Query("""
            select distinct s.submissionId from Submission s join AuditEvent a on a.submission = s
            where s.status = 'PROCESSING' and a.eventType in :events and a.createdAt < :cutoff
            and not exists (select 1 from AuditEvent newer where newer.submission = s
                and newer.eventType in :events and newer.createdAt > a.createdAt)
            and not exists (select 1 from AiJob j where j.submission = s
                and j.submittedAt >= a.createdAt
                and j.status not in ('SUPERSEDED', 'FAILED')
                and (j.status <> 'PENDING' or j.submittedAt >= :cutoff))
            """)
    List<UUID> findInterruptedTeacherDispatches(@Param("events") Set<String> events,
            @Param("cutoff") java.time.Instant cutoff, org.springframework.data.domain.Pageable page);

    @org.springframework.data.jpa.repository.Modifying
    @Query("update Submission s set s.status = 'FAILED' where s.submissionId = :id and s.status = 'PROCESSING'")
    int markDispatchFailure(@Param("id") UUID submissionId);
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select s from Submission s where s.submissionId = :id")
    Optional<Submission> findForUpdate(@Param("id") UUID submissionId);
    List<Submission> findByStudent_Id(UUID studentId);
    List<Submission> findByBatch_BatchId(UUID batchId);
    List<Submission> findByBatch_BatchIdAndStatus(UUID batchId, String status);

    @Query("""
            select s.submissionId from Submission s
            where s.batch.batchId = :batchId and s.status in :statuses
            order by s.createdAt, s.submissionId
            """)
    List<UUID> findBatchReviewIds(@Param("batchId") UUID batchId, @Param("statuses") Set<String> statuses);

    @Query("""
            select s.submissionId as submissionId, s.status as status, student.displayName as studentName,
                   assignment.maxScore as maxScore, result.gradeProposal as gradeProposal,
                   result.reviewReasons as reviewReasons, result.evidence as evidence,
                   job.jobId as jobId, job.status as jobStatus
            from Submission s
            left join s.student student
            left join s.assignment assignment
            left join AnalysisResult result on result.submission = s
            left join AiJob job on job.submission = s and not exists (
                select 1 from AiJob newer where newer.submission = s
                and (newer.submittedAt > job.submittedAt
                    or (newer.submittedAt = job.submittedAt and newer.jobId > job.jobId))
            )
            where s.batch.batchId = :batchId and s.status in :statuses
            order by s.createdAt, s.submissionId
            """)
    List<BatchReviewRow> findBatchReviewRows(@Param("batchId") UUID batchId, @Param("statuses") Set<String> statuses);

    interface BatchReviewRow {
        UUID getSubmissionId();
        String getStatus();
        String getStudentName();
        Integer getMaxScore();
        Map<String, Object> getGradeProposal();
        Map<String, Object> getReviewReasons();
        Map<String, Object> getEvidence();
        UUID getJobId();
        String getJobStatus();
    }
}

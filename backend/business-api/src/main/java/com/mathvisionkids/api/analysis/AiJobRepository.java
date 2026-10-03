package com.mathvisionkids.api.analysis;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;
import java.util.Optional;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface AiJobRepository extends JpaRepository<AiJob, UUID> {
    List<AiJob> findBySubmission_SubmissionId(UUID submissionId);
    Optional<AiJob> findFirstBySubmission_SubmissionIdOrderBySubmittedAtDesc(UUID submissionId);
    @Query("select j.submission.submissionId from AiJob j where j.jobId = :id")
    Optional<UUID> findSubmissionIdByJobId(@Param("id") UUID jobId);
}

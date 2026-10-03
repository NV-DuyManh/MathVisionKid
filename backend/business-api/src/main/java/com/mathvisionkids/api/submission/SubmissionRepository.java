package com.mathvisionkids.api.submission;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;
import java.util.Optional;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface SubmissionRepository extends JpaRepository<Submission, UUID> {
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select s from Submission s where s.submissionId = :id")
    Optional<Submission> findForUpdate(@Param("id") UUID submissionId);
    List<Submission> findByStudent_Id(UUID studentId);
    List<Submission> findByBatch_BatchId(UUID batchId);
    List<Submission> findByBatch_BatchIdAndStatus(UUID batchId, String status);
}

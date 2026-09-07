package com.mathvisionkids.api.audit;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface AuditEventRepository extends JpaRepository<AuditEvent, UUID> {
    List<AuditEvent> findBySubmission_SubmissionIdOrderByCreatedAtDesc(UUID submissionId);
}

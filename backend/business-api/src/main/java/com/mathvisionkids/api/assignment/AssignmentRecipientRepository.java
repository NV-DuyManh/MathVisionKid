package com.mathvisionkids.api.assignment;

import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface AssignmentRecipientRepository extends JpaRepository<AssignmentRecipient, AssignmentRecipient.Key> {
    @Query("select count(r) from AssignmentRecipient r join AssignmentPublication p on p.publicationId = r.publicationId where p.assignmentId = :assignmentId")
    int countByAssignment(@Param("assignmentId") UUID assignmentId);

    @Query("select new com.mathvisionkids.api.assignment.AssignmentWorkflowService$Recipient(s.id, s.displayName) " +
            "from AssignmentRecipient r join AssignmentPublication p on p.publicationId = r.publicationId " +
            "join Student s on s.id = r.studentId where p.publicationId = :publicationId order by s.displayName")
    List<AssignmentWorkflowService.Recipient> findRoster(@Param("publicationId") UUID publicationId);
}

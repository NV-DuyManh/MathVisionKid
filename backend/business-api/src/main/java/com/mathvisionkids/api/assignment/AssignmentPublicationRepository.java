package com.mathvisionkids.api.assignment;

import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AssignmentPublicationRepository extends JpaRepository<AssignmentPublication, UUID> {
    Optional<AssignmentPublication> findByAssignmentId(UUID assignmentId);
}

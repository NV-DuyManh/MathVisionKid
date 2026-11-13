package com.mathvisionkids.api.user;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.util.Optional;
import java.util.UUID;

public interface TeacherRepository extends JpaRepository<Teacher, UUID> {
    Optional<Teacher> findByEmail(String email);

    @Query(value = "select teacher_id from teachers where teacher_id = :id for update", nativeQuery = true)
    Optional<UUID> lockForAssignmentCreation(@Param("id") UUID id);
}

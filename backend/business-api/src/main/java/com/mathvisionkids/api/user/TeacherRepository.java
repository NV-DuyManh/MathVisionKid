package com.mathvisionkids.api.user;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.util.Optional;
import java.util.UUID;

public interface TeacherRepository extends JpaRepository<Teacher, UUID> {
    Optional<Teacher> findByEmail(String email);

    // Creation keys are scoped to the teacher. Use the account row so the lock
    // does not conflict with foreign-key checks against the teachers row.
    @Query(value = "select id from users where id = :id and role = 'TEACHER' for update", nativeQuery = true)
    Optional<UUID> lockForCreation(@Param("id") UUID id);
}

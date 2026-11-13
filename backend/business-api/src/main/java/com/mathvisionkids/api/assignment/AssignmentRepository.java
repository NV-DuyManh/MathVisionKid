package com.mathvisionkids.api.assignment;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface AssignmentRepository extends JpaRepository<Assignment, UUID> {
    @Query("select a from Assignment a where a.teacher.id = :teacherId and a.classroom.teacher.id = :teacherId")
    List<Assignment> findOwnedByAssignedTeacher(@Param("teacherId") UUID teacherId);

    List<Assignment> findByClassroom_ClassId(UUID classId);

    Optional<Assignment> findByTeacher_IdAndCreationRequestId(UUID teacherId, UUID creationRequestId);
}

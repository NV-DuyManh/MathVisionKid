package com.mathvisionkids.api.classroom;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface ClassroomRepository extends JpaRepository<Classroom, UUID> {
    java.util.Optional<Classroom> findByCreatedByTeacherIdAndCreationRequestId(UUID teacherId, UUID requestId);

    @org.springframework.data.jpa.repository.Lock(jakarta.persistence.LockModeType.PESSIMISTIC_WRITE)
    @org.springframework.data.jpa.repository.Query("select c from Classroom c where c.classId = :id")
    java.util.Optional<Classroom> findForUpdate(@org.springframework.data.repository.query.Param("id") UUID id);

    List<Classroom> findByTeacher_Id(UUID teacherId);
    List<Classroom> findByStudents_Id(UUID studentId);
}

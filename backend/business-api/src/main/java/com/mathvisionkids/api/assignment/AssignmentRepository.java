package com.mathvisionkids.api.assignment;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.Lock;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface AssignmentRepository extends JpaRepository<Assignment, UUID> {
    @Query("select a from Assignment a where a.classroom.teacher.id = :teacherId")
    List<Assignment> findByAssignedTeacher(@Param("teacherId") UUID teacherId);

    List<Assignment> findByClassroom_ClassId(UUID classId);

    Optional<Assignment> findByTeacher_IdAndCreationRequestId(UUID teacherId, UUID creationRequestId);

    List<Assignment> findByClassroom_ClassIdOrderByCreatedAtDesc(UUID classId);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select a from Assignment a where a.assignmentId = :id")
    Optional<Assignment> findForUpdate(@Param("id") UUID id);

    @Query("select a.classroom.classId from Assignment a where a.assignmentId = :id")
    Optional<UUID> findClassId(@Param("id") UUID id);

    @Query("""
            select a as assignment, count(snapshotRecipient.studentId) as recipientCount, p.publishedAt as publishedAt
            from AssignmentPublication p join Assignment a on a.assignmentId = p.assignmentId
            join AssignmentRecipient r on r.publicationId = p.publicationId
            join AssignmentRecipient snapshotRecipient on snapshotRecipient.publicationId = p.publicationId
            join a.classroom c join c.students member
            join Student s on s.id = r.studentId
            where r.studentId = :studentId and member.id = :studentId and s.active = true and a.status = 'PUBLISHED'
            group by a, p.publishedAt
            order by p.publishedAt desc
            """)
    List<StudentAssignmentRow> findPublishedForCurrentMember(@Param("studentId") UUID studentId);

    interface StudentAssignmentRow {
        Assignment getAssignment();
        Long getRecipientCount();
        java.time.Instant getPublishedAt();
    }
}

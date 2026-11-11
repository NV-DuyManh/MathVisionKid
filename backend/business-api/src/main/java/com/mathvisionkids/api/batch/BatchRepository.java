package com.mathvisionkids.api.batch;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.util.List;
import java.util.UUID;

public interface BatchRepository extends JpaRepository<Batch, UUID> {
    @org.springframework.data.jpa.repository.Lock(jakarta.persistence.LockModeType.PESSIMISTIC_WRITE)
    @org.springframework.data.jpa.repository.Query("select b from Batch b where b.batchId = :id")
    java.util.Optional<Batch> findForUpdate(@org.springframework.data.repository.query.Param("id") UUID id);
    @Query("""
            select b from Batch b
            where b.teacher.id = :teacherId and b.assignment.classroom.teacher.id = :teacherId
            order by b.createdAt desc
            """)
    List<Batch> findOwnedByAssignedTeacherOrderByCreatedAtDesc(@Param("teacherId") UUID teacherId);
}

package com.mathvisionkids.api.quiz;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

/** Created only after the authenticated Tutor boundary validates a confirmed source. */
@Entity @Table(name="quiz_learning_sources", uniqueConstraints=@UniqueConstraint(columnNames={"student_id","source_type","source_id"}))
class QuizSource {
    @Id UUID id = UUID.randomUUID();
    @Column(nullable=false) UUID studentId;
    @Column(nullable=false, length=24) String sourceType;
    @Column(nullable=false, length=100) String sourceId;
    @Column(nullable=false, columnDefinition="text") String problemText;
    @Column(nullable=false, length=64) String fingerprint;
    @Column(nullable=false) boolean completed;
    UUID preparationId;
    @Column(nullable=false) Instant createdAt = Instant.now();
}

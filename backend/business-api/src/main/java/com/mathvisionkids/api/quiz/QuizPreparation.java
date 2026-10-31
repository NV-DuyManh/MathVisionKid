package com.mathvisionkids.api.quiz;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

/** Private cache: never returned as an entity or counted as a pending Quiz. */
@Entity @Table(name="quiz_preparations", uniqueConstraints=@UniqueConstraint(columnNames={"student_id","workflow_key"}))
class QuizPreparation {
    @Id UUID id=UUID.randomUUID();
    @Column(nullable=false) UUID studentId;
    @Column(nullable=false) UUID workflowKey;
    @Column(nullable=false) long revision;
    @Column(length=64) String fingerprint;
    @Column(nullable=false,length=20) String status;
    @Column(length=64) String errorCode;
    @Column(columnDefinition="text") String validatedDraft;
    @Column(columnDefinition="text") String confirmedProblemText;
    @Column(nullable=false) boolean problemConfirmed;
    @Column(length=64) String generatorVersion;
    Instant generatedAt;
    Long durationMs;
    @Column(nullable=false) Instant updatedAt=Instant.now();
}

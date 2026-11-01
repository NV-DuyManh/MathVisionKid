package com.mathvisionkids.api.quiz;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

/** Never serialize this entity. QuizView deliberately excludes all private solution fields. */
@Entity @Table(name="student_quizzes", uniqueConstraints=@UniqueConstraint(columnNames={"student_id","source_type","source_fingerprint"}))
class Quiz {
    @Id UUID id = UUID.randomUUID();
    @Column(nullable=false) UUID studentId;
    @Column(nullable=false, length=24) String sourceType;
    @Column(nullable=false, length=100) String sourceId;
    @Column(nullable=false, length=64) String sourceFingerprint;
    @Column(nullable=false, length=64) String topicCode;
    @Column(nullable=false, length=120) String topicName;
    @Column(nullable=false, length=80) String skillCode;
    @Column(nullable=false) int gradeLevel;
    @Column(nullable=false, columnDefinition="text") String questionText;
    @Column(nullable=false, length=30) String unit;
    @Column(nullable=false, length=100) String answerSpec;
    @Column(nullable=false, columnDefinition="text") String validatedSolution;
    @Column(nullable=false, length=20) String status = "READY";
    @Column(nullable=false) Instant createdAt = Instant.now();
    @Column(nullable=false) Instant updatedAt = Instant.now();
    Instant startedAt;
    Instant completedAt;
    @Column(nullable=false) int stars;
    @Column(nullable=false) int wrongAttempts;
    @Column(nullable=false) boolean solutionViewed;
    @Column(nullable=false) boolean completedWithSolution;
    @Column(nullable=false, length=32) String generationVersion = QuizMath.VERSION;
    @Column(nullable=false, length=32) String taxonomyVersion = QuizMath.VERSION;
    @Column(nullable=false, length=32) String verificationStatus = "DETERMINISTICALLY_VERIFIED";
    @Column(nullable=false) int confidencePercent = 100;
    Instant lastSubmittedAt;
    @Column(nullable=false) boolean replaying = false;
    Instant firstCompletedAt;
    @Column(nullable=false, length=20) String replayMode = "NONE";
    @Column(columnDefinition="text") String originalQuestionText;
    @Column(length=100) String originalAnswerSpec;
    @Column(columnDefinition="text") String originalValidatedSolution;
    @Column(length=30) String originalUnit;
    long elapsedMillis(Instant now) {
        if (startedAt == null) return 0;
        var duration = java.time.Duration.between(startedAt, completedAt == null ? now : completedAt);
        return Math.max(0, duration.toMillis() + (duration.getNano() % 1_000_000 == 0 ? 0 : 1));
    }
}

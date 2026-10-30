package com.mathvisionkids.api.quiz;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity @Table(name="quiz_attempts", uniqueConstraints={@UniqueConstraint(columnNames={"quiz_id","request_id"}), @UniqueConstraint(columnNames={"quiz_id","attempt_number"})})
class QuizAttempt {
    @Id UUID id = UUID.randomUUID();
    @Column(nullable=false) UUID quizId;
    @Column(nullable=false) UUID requestId;
    @Column(nullable=false) int attemptNumber;
    @Column(nullable=false, length=100) String answer;
    @Column(nullable=false) boolean correct;
    @Column(nullable=false) Instant submittedAt;
    @Column(nullable=false) long elapsedMillis;
    @Column(columnDefinition="text") String questionText;
    @Column(length=100) String answerSpec;
    Boolean solutionViewed;
    Instant runStartedAt;
    @Column(nullable=false) int stars = 0;
    @Column(nullable=false, length=20) String replayMode = "NONE";
}

package com.mathvisionkids.api.batch;

import com.mathvisionkids.api.assignment.Assignment;
import com.mathvisionkids.api.user.Teacher;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "batches")
@Getter
@Setter
@NoArgsConstructor
public class Batch {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID batchId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "assignment_id", nullable = false)
    private Assignment assignment;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "teacher_id", nullable = false)
    private Teacher teacher;

    @Column(nullable = false)
    private String status;

    private Integer totalCount = 0;
    private Integer processedCount = 0;
    private Integer reviewRequiredCount = 0;
    private Integer failedCount = 0;

    @Column(updatable = false)
    private Instant createdAt = Instant.now();
    
    private Instant startedAt;
    private Instant completedAt;
}

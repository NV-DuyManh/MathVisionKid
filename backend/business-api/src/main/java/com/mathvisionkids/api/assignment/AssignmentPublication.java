package com.mathvisionkids.api.assignment;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "assignment_publications")
@Getter
@NoArgsConstructor
public class AssignmentPublication {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "publication_id")
    private UUID publicationId;

    @Column(name = "assignment_id", nullable = false, unique = true)
    private UUID assignmentId;

    @Column(name = "published_at", nullable = false, updatable = false)
    private Instant publishedAt = Instant.now();

    public AssignmentPublication(UUID assignmentId) {
        this.assignmentId = assignmentId;
    }
}

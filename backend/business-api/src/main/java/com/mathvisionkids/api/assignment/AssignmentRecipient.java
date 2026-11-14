package com.mathvisionkids.api.assignment;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import java.io.Serializable;
import java.util.UUID;
import lombok.AllArgsConstructor;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "assignment_recipients")
@IdClass(AssignmentRecipient.Key.class)
@Getter
@Setter
@NoArgsConstructor
public class AssignmentRecipient {
    @Id
    @Column(name = "publication_id")
    private UUID publicationId;

    @Id
    @Column(name = "student_id")
    private UUID studentId;

    public AssignmentRecipient(UUID publicationId, UUID studentId) {
        this.publicationId = publicationId;
        this.studentId = studentId;
    }

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    @EqualsAndHashCode
    public static class Key implements Serializable {
        private UUID publicationId;
        private UUID studentId;
    }
}

package com.mathvisionkids.api.user;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "users")
@Inheritance(strategy = InheritanceType.JOINED)
@Getter
@Setter
@NoArgsConstructor
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(name = "google_subject", unique = true)
    private String googleSubject;

    @Column(name = "facebook_subject", unique = true)
    private String facebookSubject;

    @Column(nullable = false)
    private String passwordHash;

    @Column(nullable = false)
    private String role; // "STUDENT", "TEACHER"

    @Column(nullable = false)
    private String displayName;

    private String gender;

    private String phoneNumber;

    private Boolean active = true;

    @Column(updatable = false)
    private Instant createdAt = Instant.now();

    private Instant updatedAt = Instant.now();
    
    @PreUpdate
    public void preUpdate() {
        this.updatedAt = Instant.now();
    }
}

package com.mathvisionkids.api.auth;

import org.springframework.data.jpa.repository.JpaRepository;
import java.time.Instant;
import java.util.Optional;
import java.util.UUID;

public interface PasswordResetCodeRepository extends JpaRepository<PasswordResetCode, UUID> {
    Optional<PasswordResetCode> findTopByUser_IdAndConsumedFalseOrderByCreatedAtDesc(UUID userId);
    long countByUser_IdAndCreatedAtAfter(UUID userId, Instant after);
}

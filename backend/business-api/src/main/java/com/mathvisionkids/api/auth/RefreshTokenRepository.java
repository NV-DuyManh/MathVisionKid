package com.mathvisionkids.api.auth;

import com.mathvisionkids.api.user.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import java.time.Instant;
import java.util.Optional;
import java.util.UUID;

public interface RefreshTokenRepository extends JpaRepository<RefreshToken, UUID> {
    @org.springframework.data.jpa.repository.Query("select t.user.id from RefreshToken t where t.tokenHash = :hash")
    Optional<UUID> findOwnerId(@org.springframework.data.repository.query.Param("hash") String hash);
    Optional<RefreshToken> findByTokenHash(String tokenHash);

    @Modifying
    void deleteByUser(User user);

    void deleteByTokenHash(String tokenHash);
    boolean existsByUser_IdAndTokenHashStartingWithAndRevokedFalseAndExpiryDateAfter(UUID owner, String prefix, Instant now);
    void deleteByUser_IdAndTokenHashStartingWith(UUID owner, String prefix);

    @Modifying
    @org.springframework.data.jpa.repository.Query("delete from RefreshToken t where t.user.id = :owner and t.tokenHash like 'web:%'")
    void deleteWebSessions(@org.springframework.data.repository.query.Param("owner") UUID owner);

    @Modifying
    @org.springframework.data.jpa.repository.Query("delete from RefreshToken t where t.user.id = :owner and t.tokenHash like 'web:%' and t.expiryDate <= :now")
    void deleteExpiredWebSessions(@org.springframework.data.repository.query.Param("owner") UUID owner,
                                  @org.springframework.data.repository.query.Param("now") Instant now);
}

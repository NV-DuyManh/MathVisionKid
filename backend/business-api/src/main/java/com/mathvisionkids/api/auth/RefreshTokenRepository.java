package com.mathvisionkids.api.auth;

import com.mathvisionkids.api.user.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import java.util.Optional;
import java.util.UUID;

public interface RefreshTokenRepository extends JpaRepository<RefreshToken, UUID> {
    @org.springframework.data.jpa.repository.Query("select t.user.id from RefreshToken t where t.tokenHash = :hash")
    Optional<UUID> findOwnerId(@org.springframework.data.repository.query.Param("hash") String hash);
    Optional<RefreshToken> findByTokenHash(String tokenHash);

    @Modifying
    void deleteByUser(User user);
}

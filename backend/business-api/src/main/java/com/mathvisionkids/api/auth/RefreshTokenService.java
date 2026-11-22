package com.mathvisionkids.api.auth;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.Base64;
import java.util.UUID;

@Service
public class RefreshTokenService {
    private final RefreshTokenRepository refreshTokenRepository;
    private final UserRepository userRepository;
    private final JwtUtil jwtUtil;
    
    // Default 7 days
    private final long refreshTokenDurationMs = 7L * 24 * 60 * 60 * 1000;

    public RefreshTokenService(RefreshTokenRepository refreshTokenRepository, UserRepository userRepository, JwtUtil jwtUtil) {
        this.refreshTokenRepository = refreshTokenRepository;
        this.userRepository = userRepository;
        this.jwtUtil = jwtUtil;
    }

    @Transactional
    public boolean revokeForLogout(String rawToken, String principal, UUID authenticatedSession) {
        if (authenticatedSession != null) {
            var owner = userRepository.findByEmail(principal).orElseThrow();
            if (rawToken != null && !authenticatedSession.equals(sessionOf(rawToken))) return false;
            userRepository.lockSessions(owner.getId()).orElseThrow();
            refreshTokenRepository.deleteByUser_IdAndTokenHashStartingWith(owner.getId(), nativePrefix(authenticatedSession));
            return true;
        }
        if (rawToken == null || (rawToken.length() != 36 && sessionOf(rawToken) == null)) return false;
        String hash = storageHash(rawToken);
        var owner = refreshTokenRepository.findOwnerId(hash);
        if (owner.isEmpty() || userRepository.lockSessions(owner.get()).isEmpty()) return false;
        var active = refreshTokenRepository.findByTokenHash(hash)
                .filter(token -> (principal == null || principal.equals(token.getUser().getEmail()))
                        && token.getExpiryDate().isAfter(Instant.now()));
        UUID session = sessionOf(rawToken);
        if (active.isEmpty() || (session == null && active.get().isRevoked())) return false;
        if (session == null) refreshTokenRepository.delete(active.get());
        else refreshTokenRepository.deleteByUser_IdAndTokenHashStartingWith(owner.get(), nativePrefix(session));
        return true;
    }

    static String nativePrefix(UUID session) {
        return "native:" + session + ":";
    }

    private static UUID sessionOf(String rawToken) {
        if (rawToken == null || rawToken.length() != 73 || rawToken.charAt(36) != '.') return null;
        try {
            return UUID.fromString(rawToken.substring(0, 36));
        } catch (IllegalArgumentException invalid) {
            return null;
        }
    }

    static String storageHash(String rawToken) {
        UUID session = sessionOf(rawToken);
        return (session == null ? "" : nativePrefix(session)) + hashToken(rawToken);
    }

    static String hashToken(String token) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(token.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(hash);
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("Error hashing token", e);
        }
    }

    @Transactional
    public String createRefreshToken(UUID userId) {
        return createSession(userId).getRefreshToken();
    }

    @Transactional
    public AuthResponse createSession(UUID userId) {
        userRepository.lockSessions(userId).orElseThrow();
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "User not found", HttpStatus.NOT_FOUND));
        if (!Boolean.TRUE.equals(user.getActive())) {
            throw new ApiException("UNAUTHORIZED", "Account is disabled.", HttpStatus.UNAUTHORIZED);
        }
        return issueSession(user, UUID.randomUUID());
    }

    private AuthResponse issueSession(User user, UUID session) {
        String rawToken = session + "." + UUID.randomUUID();
        
        RefreshToken refreshToken = new RefreshToken();
        refreshToken.setUser(user);
        refreshToken.setExpiryDate(Instant.now().plusMillis(refreshTokenDurationMs));
        refreshToken.setTokenHash(storageHash(rawToken));
        refreshTokenRepository.save(refreshToken);

        return new AuthResponse(jwtUtil.generateToken(user.getEmail(), user.getRole(), session), rawToken);
    }

    @Transactional(noRollbackFor = ApiException.class)
    public AuthResponse rotate(String rawToken) {
        String tokenHash = storageHash(rawToken);
        UUID ownerId = refreshTokenRepository.findOwnerId(tokenHash)
                .orElseThrow(() -> new ApiException("UNAUTHORIZED", "Refresh token is not in database!", HttpStatus.UNAUTHORIZED));
        // Serialize rotation and revocation on the root user row before loading
        // the token. A second request must see the first committed rotation.
        userRepository.lockSessions(ownerId).orElseThrow();
        RefreshToken token = refreshTokenRepository.findByTokenHash(tokenHash)
                .orElseThrow(() -> new ApiException("UNAUTHORIZED", "Refresh token is not in database!", HttpStatus.UNAUTHORIZED));

        if (token.isRevoked()) {
            // Compromised token detected: revoke all tokens for this user
            refreshTokenRepository.deleteByUser(token.getUser());
            token.getUser().setTokenVersion(token.getUser().getTokenVersion() + 1);
            throw new ApiException("UNAUTHORIZED", "Compromised token detected. All sessions revoked.", HttpStatus.UNAUTHORIZED);
        }

        if (!Boolean.TRUE.equals(token.getUser().getActive())) {
            refreshTokenRepository.deleteByUser(token.getUser());
            throw new ApiException("UNAUTHORIZED", "Account is disabled.", HttpStatus.UNAUTHORIZED);
        }

        if (token.getExpiryDate().compareTo(Instant.now()) < 0) {
            refreshTokenRepository.delete(token);
            throw new ApiException("UNAUTHORIZED", "Refresh token was expired. Please make a new signin request", HttpStatus.UNAUTHORIZED);
        }

        // Mark as revoked (used) since it's being rotated
        token.setRevoked(true);
        refreshTokenRepository.save(token);

        User user = token.getUser();
        UUID session = sessionOf(rawToken);
        return issueSession(user, session == null ? UUID.randomUUID() : session);
    }
    
    @Transactional
    public void deleteByUserId(UUID userId) {
        userRepository.lockSessions(userId).orElseThrow();
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "User not found", HttpStatus.NOT_FOUND));
        refreshTokenRepository.deleteByUser(user);
        user.setTokenVersion(user.getTokenVersion() + 1);
    }
}

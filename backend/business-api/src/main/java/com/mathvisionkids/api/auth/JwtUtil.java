package com.mathvisionkids.api.auth;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.http.HttpServletRequest;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Component;
import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.UUID;
import java.time.Instant;
import java.util.function.Function;

@Component
public class JwtUtil {

    private final JwtProperties jwtProperties;
    private final com.mathvisionkids.api.user.UserRepository users;

    private final RefreshTokenRepository sessions;

    public JwtUtil(JwtProperties jwtProperties, com.mathvisionkids.api.user.UserRepository users, RefreshTokenRepository sessions) {
        this.jwtProperties = jwtProperties;
        this.users = users;
        this.sessions = sessions;
    }

    private SecretKey getSigningKey() {
        byte[] keyBytes = jwtProperties.getSecret().getBytes(StandardCharsets.UTF_8);
        return Keys.hmacShaKeyFor(keyBytes);
    }

    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    public String extractRole(String token) {
        return extractClaim(token, claims -> claims.get("role", String.class));
    }

    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        return claimsResolver.apply(claims);
    }

    private Claims extractAllClaims(String token) {
        return Jwts.parser()
                .verifyWith(getSigningKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    public Date extractExpiration(String token) {
        return extractClaim(token, Claims::getExpiration);
    }

    public String generateToken(String username, String role) {
        return generateToken(username, role, null);
    }

    String generateToken(String username, String role, UUID nativeSession) {
        long version = users.findByEmail(username).orElseThrow().getTokenVersion();
        return Jwts.builder()
                .subject(username)
                .claim("role", role)
                .claim("sessionVersion", version)
                .claim("nativeSession", nativeSession == null ? null : nativeSession.toString())
                .issuedAt(new Date(System.currentTimeMillis()))
                .expiration(new Date(System.currentTimeMillis() + jwtProperties.getExpirationMs()))
                .signWith(getSigningKey())
                .compact();
    }

    public UUID nativeSession(String token) {
        return extractClaim(token, JwtUtil::nativeSession);
    }

    private static UUID nativeSession(Claims claims) {
        String value = claims.get("nativeSession", String.class);
        return value == null ? null : UUID.fromString(value);
    }

    private static final String PARENT_GRANT_SUBJECT = "parent-control-settings";

    public String issueParentSettingsGrant(String principal, HttpServletRequest request, long pinRevision) {
        String binding = parentSessionBinding(request);
        if (binding == null) return null;
        var now = Instant.now();
        return Jwts.builder()
                .subject(PARENT_GRANT_SUBJECT)
                .claim("student", principal)
                .claim("pinRevision", pinRevision)
                .claim("binding", binding)
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plusSeconds(300)))
                .signWith(getSigningKey())
                .compact();
    }

    public boolean acceptsParentSettingsGrant(String token, String principal, HttpServletRequest request, long pinRevision) {
        if (token == null) return false;
        try {
            Claims claims = extractAllClaims(token);
            String binding = parentSessionBinding(request);
            return PARENT_GRANT_SUBJECT.equals(claims.getSubject()) && claims.getExpiration() != null
                    && principal.equals(claims.get("student", String.class))
                    && Long.valueOf(pinRevision).equals(claims.get("pinRevision", Long.class))
                    && binding != null && binding.equals(claims.get("binding", String.class));
        } catch (JwtException | IllegalArgumentException invalid) {
            return false;
        }
    }

    private String parentSessionBinding(HttpServletRequest request) {
        String session = parentSessionIdentity(request);
        return session == null ? null : RefreshTokenService.hashToken(session);
    }

    private String parentSessionIdentity(HttpServletRequest request) {
        if (request.getHeader(WebSessionService.CLIENT) != null) {
            String session = request.getHeader(WebSessionService.SESSION);
            return session == null ? null : "web:" + session;
        }
        String auth = request.getHeader("Authorization");
        if (auth == null || !auth.startsWith("Bearer ")) return null;
        String token = auth.substring(7);
        UUID session = nativeSession(token);
        // Legacy bearer tokens have no session claim. Bind to their signature until they rotate.
        return session == null ? "legacy:" + token.substring(token.lastIndexOf('.') + 1) : "native:" + session;
    }

    public Boolean validateToken(String token, String username) {
        Claims claims = extractAllClaims(token);
        if (PARENT_GRANT_SUBJECT.equals(claims.getSubject())) return false;
        Number version = claims.get("sessionVersion", Number.class);
        // Previously issued tokens belong to version zero until sessions are revoked.
        long issuedVersion = version == null ? 0 : version.longValue();
        UUID nativeSession = nativeSession(claims);
        return username.equals(claims.getSubject()) && claims.getExpiration().after(new Date())
                && users.findByEmail(username)
                .map(user -> user.getTokenVersion() == issuedVersion && (nativeSession == null ||
                        sessions.existsByUser_IdAndTokenHashStartingWithAndRevokedFalseAndExpiryDateAfter(
                                user.getId(), RefreshTokenService.nativePrefix(nativeSession), Instant.now())))
                .orElse(false);
    }
}

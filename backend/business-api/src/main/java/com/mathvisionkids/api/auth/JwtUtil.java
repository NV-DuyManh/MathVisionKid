package com.mathvisionkids.api.auth;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Component;
import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.function.Function;

@Component
public class JwtUtil {

    private final JwtProperties jwtProperties;
    private final com.mathvisionkids.api.user.UserRepository users;

    public JwtUtil(JwtProperties jwtProperties, com.mathvisionkids.api.user.UserRepository users) {
        this.jwtProperties = jwtProperties;
        this.users = users;
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
        long version = users.findByEmail(username).orElseThrow().getTokenVersion();
        return Jwts.builder()
                .subject(username)
                .claim("role", role)
                .claim("sessionVersion", version)
                .issuedAt(new Date(System.currentTimeMillis()))
                .expiration(new Date(System.currentTimeMillis() + jwtProperties.getExpirationMs()))
                .signWith(getSigningKey())
                .compact();
    }

    public Boolean validateToken(String token, String username) {
        Claims claims = extractAllClaims(token);
        Number version = claims.get("sessionVersion", Number.class);
        // Previously issued tokens belong to version zero until sessions are revoked.
        long issuedVersion = version == null ? 0 : version.longValue();
        return username.equals(claims.getSubject()) && claims.getExpiration().after(new Date())
                && users.findByEmail(username)
                .map(user -> user.getTokenVersion() == issuedVersion).orElse(false);
    }
}

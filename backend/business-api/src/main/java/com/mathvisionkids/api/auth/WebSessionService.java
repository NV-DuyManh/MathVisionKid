package com.mathvisionkids.api.auth;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.UserRepository;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.Locale;
import java.util.UUID;

@Service
public class WebSessionService {
    public static final String CLIENT = "X-MathVision-Web";
    public static final String SESSION = "X-MathVision-Session";
    private static final Duration LIFETIME = Duration.ofDays(7);

    private final RefreshTokenRepository tokens;
    private final UserRepository users;
    private final boolean secureCookie;

    public WebSessionService(RefreshTokenRepository tokens, UserRepository users,
                             @Value("${app.auth.web.secure-cookie:true}") boolean secureCookie) {
        this.tokens = tokens;
        this.users = users;
        this.secureCookie = secureCookie;
    }

    public enum Client {
        PORTAL, TEACHER, ADMIN;

        String cookieName() { return "mvk_" + name().toLowerCase(Locale.ROOT) + "_session"; }

        boolean acceptsRole(String role) {
            return this == PORTAL ? "STUDENT".equals(role) || "TEACHER".equals(role) || "ADMIN".equals(role)
                    : name().equals(role);
        }
    }

    public record Session(String sessionId) {}

    public static Client client(HttpServletRequest request) {
        String value = request.getHeader(CLIENT);
        return switch (value == null ? "" : value) {
            case "portal" -> Client.PORTAL;
            case "teacher" -> Client.TEACHER;
            case "admin" -> Client.ADMIN;
            default -> null;
        };
    }

    private String cookieName(HttpServletRequest request, Client client) {
        return secureCookie || request.isSecure() ? "__Host-" + client.cookieName() : client.cookieName();
    }

    private String cookie(HttpServletRequest request, Client client) {
        if (request.getCookies() == null) return null;
        String name = cookieName(request, client);
        var cookies = Arrays.stream(request.getCookies()).filter(c -> name.equals(c.getName())).toList();
        return cookies.size() == 1 && cookies.getFirst().getValue().length() == 73 ? cookies.getFirst().getValue() : null;
    }

    private static String hash(Client client, String secret, String id) {
        return "web:" + RefreshTokenService.hashToken(client.name() + ":" + secret + ":" + id);
    }

    private void writeCookie(HttpServletRequest request, HttpServletResponse response, Client client,
                             String value, Duration lifetime) {
        response.addHeader(HttpHeaders.SET_COOKIE, ResponseCookie.from(cookieName(request, client), value)
                .httpOnly(true).secure(secureCookie || request.isSecure()).sameSite("Strict")
                .path("/").maxAge(lifetime).build().toString());
        response.setHeader(HttpHeaders.CACHE_CONTROL, "no-store");
    }

    @Transactional(noRollbackFor = ApiException.class)
    public Session establish(AuthResponse credentials, Client client, HttpServletRequest request, HttpServletResponse response) {
        String mobileHash = RefreshTokenService.storageHash(credentials.getRefreshToken());
        var owner = tokens.findOwnerId(mobileHash).orElseThrow(WebSessionService::unauthorized);
        users.lockSessions(owner).orElseThrow(WebSessionService::unauthorized);
        var issued = tokens.findByTokenHash(mobileHash).filter(t -> valid(t, Instant.now()))
                .orElseThrow(WebSessionService::unauthorized);
        if (!client.acceptsRole(issued.getUser().getRole())) {
            tokens.delete(issued);
            throw new ApiException("FORBIDDEN", "Access Denied", HttpStatus.FORBIDDEN);
        }
        // Change the namespace of the newly issued credential before it can be returned to the browser.
        String previous = cookie(request, client);
        String secret = previous == null ? UUID.randomUUID() + "." + UUID.randomUUID() : previous;
        String id = issued.getTokenId().toString();
        issued.setTokenHash(hash(client, secret, id));
        Instant now = Instant.now();
        issued.setExpiryDate(now.plus(LIFETIME));
        String previousId = request.getHeader(SESSION);
        if (previous != null && previousId != null) tokens.deleteByTokenHash(hash(client, previous, previousId));
        tokens.deleteExpiredWebSessions(owner, now);
        writeCookie(request, response, client, secret, LIFETIME);
        return new Session(id);
    }

    @Transactional(readOnly = true)
    public String authenticate(HttpServletRequest request, Client client) {
        String secret = cookie(request, client);
        String id = request.getHeader(SESSION);
        if (secret == null || id == null) return null;
        return tokens.findByTokenHash(hash(client, secret, id))
                .filter(t -> valid(t, Instant.now()))
                .filter(t -> client.acceptsRole(t.getUser().getRole()))
                .map(t -> t.getUser().getEmail()).orElse(null);
    }

    @Transactional
    public void logout(String principal, HttpServletRequest request, Client client) {
        var owner = users.findByEmail(principal).orElseThrow(WebSessionService::unauthorized);
        users.lockSessions(owner.getId()).orElseThrow(WebSessionService::unauthorized);
        if (principal.equals(authenticate(request, client))) tokens.deleteWebSessions(owner.getId());
    }

    private static boolean valid(RefreshToken token, Instant now) {
        return !token.isRevoked() && token.getExpiryDate().isAfter(now) && Boolean.TRUE.equals(token.getUser().getActive());
    }

    private static ApiException unauthorized() {
        return new ApiException("UNAUTHORIZED", "Authentication required", HttpStatus.UNAUTHORIZED);
    }
}

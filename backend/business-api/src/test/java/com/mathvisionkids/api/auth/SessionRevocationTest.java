package com.mathvisionkids.api.auth;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import java.util.UUID;
import java.util.concurrent.Executors;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@ActiveProfiles("test")
class SessionRevocationTest {
    @Autowired UserRepository users;
    @Autowired RefreshTokenService sessions;
    @Autowired JwtUtil jwt;

    @Test void concurrentRefreshCannotCreateTwoUsableSessionsAndReplayRevocationCommits() throws Exception {
        User user = new User();
        user.setEmail(UUID.randomUUID() + "@session.test");
        user.setRole("STUDENT"); user.setDisplayName("Synthetic session"); user.setPasswordHash("unused");
        user = users.save(user);
        try {
            String refresh = sessions.createRefreshToken(user.getId());
            try (var threads = Executors.newFixedThreadPool(2)) {
                var start = new java.util.concurrent.CountDownLatch(1);
                java.util.concurrent.Callable<AuthResponse> request = () -> {
                    start.await();
                    try { return sessions.rotate(refresh); } catch (ApiException rejected) { return null; }
                };
                var first = threads.submit(request);
                var second = threads.submit(request);
                start.countDown();
                AuthResponse one = first.get(10, java.util.concurrent.TimeUnit.SECONDS);
                AuthResponse two = second.get(10, java.util.concurrent.TimeUnit.SECONDS);
                assertNotEquals(one == null, two == null);
                AuthResponse issued = one == null ? two : one;
                assertThrows(ApiException.class, () -> sessions.rotate(issued.getRefreshToken()));
                assertFalse(jwt.validateToken(issued.getAccessToken(), user.getEmail()));
            }
        } finally {
            sessions.deleteByUserId(user.getId()); users.deleteById(user.getId());
        }
    }
}

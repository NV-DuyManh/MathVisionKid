package com.mathvisionkids.api.submission;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.common.ApiException;
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import static org.junit.jupiter.api.Assertions.*;

class AssignedImagePrivacyTest {
    @ParameterizedTest
    @CsvSource(delimiter = '|', value = {
            "200 | {\"decision\":\"CLEAR\"} | ALLOW",
            "200 | {\"decision\":\"BLOCKED\"} | IMAGE_PRIVACY_REVIEW",
            "200 | {\"decision\":\"UNCERTAIN\"} | IMAGE_PRIVACY_REVIEW",
            "503 | {} | IMAGE_PRIVACY_UNAVAILABLE",
            "200 | malformed | IMAGE_PRIVACY_UNAVAILABLE",
            "200 | {\"decision\":\"CLEAR\",\"decision\":\"CLEAR\"} | IMAGE_PRIVACY_UNAVAILABLE",
            "200 | {\"decision\":\"CLEAR\"} {} | IMAGE_PRIVACY_UNAVAILABLE",
            "200 | {\"decision\":\"CLEAR\",\"extra\":true} | IMAGE_PRIVACY_UNAVAILABLE",
    })
    void acceptsOnlyExplicitValidVerdicts(int status, String body, String expected) throws Exception {
        var server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/privacy", exchange -> {
            try (exchange) {
                exchange.getRequestBody().readAllBytes();
                byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
                exchange.sendResponseHeaders(status, bytes.length);
                exchange.getResponseBody().write(bytes);
            }
        });
        server.start();
        try {
            var service = new AssignedImagePrivacy("http://127.0.0.1:" + server.getAddress().getPort()
                    + "/privacy", "test-key", new ObjectMapper());
            var image = new AssignedWebImage(new byte[] {1, 2, 3}, "image/png", "", "");
            if ("ALLOW".equals(expected)) {
                assertDoesNotThrow(() -> service.requireClear(image));
            } else {
                assertEquals(expected, assertThrows(ApiException.class, () -> service.requireClear(image)).getCode());
            }
        } finally {
            server.stop(0);
        }
    }
}

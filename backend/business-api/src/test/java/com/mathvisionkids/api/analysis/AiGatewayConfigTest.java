package com.mathvisionkids.api.analysis;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;

import java.util.Map;

import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class AiGatewayConfigTest {
    @Test void configuredJobClientSendsTheSharedInternalCredential() {
        var client = AiGatewayConfig.authenticatedRestTemplate("test-shared-internal-key");
        var server = MockRestServiceServer.bindTo(client).build();
        server.expect(requestTo("http://ai-service:8000/internal/v1/jobs"))
                .andExpect(header("X-Internal-API-Key", "test-shared-internal-key"))
                .andRespond(withSuccess("{\"status\":\"QUEUED\"}", MediaType.APPLICATION_JSON));
        client.postForEntity("http://ai-service:8000/internal/v1/jobs", Map.of("jobId", "example"), Map.class);
        server.verify();
    }
}

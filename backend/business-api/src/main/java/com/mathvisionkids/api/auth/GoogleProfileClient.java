package com.mathvisionkids.api.auth;

import com.fasterxml.jackson.databind.JsonNode;
import java.net.http.HttpClient;
import java.time.Duration;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Component
class GoogleProfileClient {
    private final RestClient client;

    GoogleProfileClient(RestClient.Builder builder) {
        var http = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(2))
                .followRedirects(HttpClient.Redirect.NEVER)
                .build();
        var requests = new JdkClientHttpRequestFactory(http);
        requests.setReadTimeout(Duration.ofSeconds(2));
        client = builder.requestFactory(requests).build();
    }

    String avatar(String accessToken, String verifiedSubject) {
        if (accessToken == null || accessToken.isBlank()) return null;
        try {
            JsonNode profile = client.get().uri("https://openidconnect.googleapis.com/v1/userinfo")
                    .headers(headers -> headers.setBearerAuth(accessToken))
                    .retrieve().body(JsonNode.class);
            if (profile != null && verifiedSubject.equals(profile.path("sub").textValue())) {
                return profile.path("picture").textValue();
            }
        } catch (RestClientException | IllegalArgumentException exception) {
            // Google profile data is optional. Keep login available if this lookup fails.
        }
        return null;
    }
}

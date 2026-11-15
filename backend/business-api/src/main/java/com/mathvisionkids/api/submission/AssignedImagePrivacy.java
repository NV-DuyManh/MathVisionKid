package com.mathvisionkids.api.submission;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.common.ApiException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

@Component
class AssignedImagePrivacy {
    private final String endpoint;
    private final String apiKey;
    private final ObjectMapper mapper;
    private final HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build();

    AssignedImagePrivacy(@Value("${app.assigned-upload.privacy-url:}") String endpoint,
            @Value("${app.assigned-upload.privacy-key:}") String apiKey, ObjectMapper mapper) {
        this.endpoint = endpoint;
        this.apiKey = apiKey;
        this.mapper = mapper;
    }

    void requireClear(AssignedWebImage image) {
        if (endpoint.isBlank() || apiKey.isBlank()) throw unavailable();
        JsonNode verdict;
        try {
            var request = HttpRequest.newBuilder(URI.create(endpoint))
                    .timeout(Duration.ofSeconds(8))
                    .header("Content-Type", image.contentType())
                    .header("X-API-Key", apiKey)
                    .POST(HttpRequest.BodyPublishers.ofByteArray(image.bytes())).build();
            var response = client.send(request, HttpResponse.BodyHandlers.ofByteArray());
            if (response.statusCode() != 200 || response.body().length > 1024) throw unavailable();
            verdict = mapper.readerFor(JsonNode.class)
                    .with(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
                    .with(DeserializationFeature.FAIL_ON_READING_DUP_TREE_KEY)
                    .readValue(response.body());
        } catch (InterruptedException failure) {
            Thread.currentThread().interrupt();
            throw unavailable();
        } catch (java.io.IOException | IllegalArgumentException failure) {
            throw unavailable();
        }
        if (verdict == null || !verdict.isObject() || verdict.size() != 1
                || !verdict.path("decision").isTextual()) throw unavailable();
        String decision = verdict.path("decision").textValue();
        switch (decision) {
            case "CLEAR" -> { }
            case "BLOCKED", "UNCERTAIN" -> throw new ApiException("IMAGE_PRIVACY_REVIEW",
                    "Em hãy cắt hoặc che thông tin riêng tư rồi gửi lại ảnh.", HttpStatus.UNPROCESSABLE_ENTITY);
            default -> throw unavailable();
        }
    }

    private static ApiException unavailable() {
        return new ApiException("IMAGE_PRIVACY_UNAVAILABLE", "Chưa kiểm tra được ảnh. Em hãy thử lại sau.",
                HttpStatus.SERVICE_UNAVAILABLE);
    }
}

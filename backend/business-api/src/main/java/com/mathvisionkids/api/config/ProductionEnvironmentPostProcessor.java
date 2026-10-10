package com.mathvisionkids.api.config;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.context.config.ConfigDataEnvironmentPostProcessor;
import org.springframework.boot.env.EnvironmentPostProcessor;
import org.springframework.core.Ordered;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.env.Profiles;

import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Locale;
import java.util.Set;

/** Rejects unsafe production settings before database initialization or demo seed runners. */
public class ProductionEnvironmentPostProcessor implements EnvironmentPostProcessor, Ordered {
    private static final Set<String> DEFAULT_PASSWORDS = Set.of(
            "password123", "mathvision_password", "minioadmin", "minioadmin123", "password", "changeme");

    @Override
    public int getOrder() {
        return ConfigDataEnvironmentPostProcessor.ORDER + 1;
    }

    @Override
    public void postProcessEnvironment(ConfigurableEnvironment environment, SpringApplication application) {
        if (!environment.acceptsProfiles(Profiles.of("prod"))) return;
        if (environment.acceptsProfiles(Profiles.of("dev", "test"))) {
            throw new IllegalStateException("The prod profile cannot be combined with dev or test.");
        }
        requireSecret(environment, "app.jwt.secret", "JWT_SECRET");
        requireSecret(environment, "ai.callback.api-key", "INTERNAL_API_KEY");
        requireValue(environment, "spring.datasource.url", "DB_URL");
        requireValue(environment, "spring.datasource.username", "DB_USERNAME");
        requirePassword(environment, "spring.datasource.password", "DB_PASSWORD");
        requireValue(environment, "minio.endpoint", "MINIO_ENDPOINT");
        String accessKey = requireValue(environment, "minio.access-key", "MINIO_ACCESS_KEY");
        if ("minioadmin".equalsIgnoreCase(accessKey)) {
            throw new IllegalStateException("MINIO_ACCESS_KEY must not use the development account in prod.");
        }
        requirePassword(environment, "minio.secret-key", "MINIO_SECRET_KEY");
        requireValue(environment, "ai.gateway.url", "AI_SERVICE_URL");
        requireValue(environment, "ai.service.base-url", "AI_SERVICE_BASE_URL");
        if (!"FASTAPI".equals(environment.getProperty("ai.gateway.mode"))) {
            throw new IllegalStateException("AI_GATEWAY_MODE must be FASTAPI in prod.");
        }
        validateOrigins(requireValue(environment, "app.cors.allowed-origins", "CORS_ALLOWED_ORIGINS"));
        if (!"never".equals(environment.getProperty("management.endpoint.health.show-details"))
                || !"never".equals(environment.getProperty("management.endpoint.health.show-components"))) {
            throw new IllegalStateException("Production health responses must not expose details or components.");
        }
    }

    private static String requireValue(ConfigurableEnvironment environment, String property, String variable) {
        String value = environment.getProperty(property, "");
        if (value.isBlank()) throw new IllegalStateException(variable + " is required in prod.");
        return value;
    }

    private static void requireSecret(ConfigurableEnvironment environment, String property, String variable) {
        String value = requireValue(environment, property, variable);
        String lower = value.toLowerCase(Locale.ROOT);
        if (value.getBytes(StandardCharsets.UTF_8).length < 32 || value.chars().distinct().count() < 8
                || lower.contains("development") || lower.contains("do_not_use")
                || lower.contains("changeme") || lower.contains("replace") || lower.contains("secret-key-default")) {
            throw new IllegalStateException(variable + " must be a newly generated random secret of at least 32 bytes in prod.");
        }
    }

    private static void requirePassword(ConfigurableEnvironment environment, String property, String variable) {
        String value = requireValue(environment, property, variable);
        if (value.length() < 16 || DEFAULT_PASSWORDS.contains(value.toLowerCase(Locale.ROOT))) {
            throw new IllegalStateException(variable + " must be a non-default password of at least 16 characters in prod.");
        }
    }

    private static void validateOrigins(String configured) {
        for (String origin : Arrays.stream(configured.split(",", -1)).map(String::trim).toList()) {
            URI uri;
            try {
                uri = URI.create(origin);
            } catch (IllegalArgumentException exception) {
                throw new IllegalStateException("CORS_ALLOWED_ORIGINS must contain exact HTTPS origins in prod.");
            }
            String host = uri.getHost();
            if (!"https".equals(uri.getScheme()) || host == null || origin.contains("*")
                    || uri.getRawUserInfo() != null || uri.getRawQuery() != null || uri.getRawFragment() != null
                    || !uri.getRawPath().isEmpty() || "localhost".equalsIgnoreCase(host)
                    || host.startsWith("127.") || "[::1]".equals(host)) {
                throw new IllegalStateException("CORS_ALLOWED_ORIGINS must contain exact public HTTPS origins in prod.");
            }
        }
    }
}

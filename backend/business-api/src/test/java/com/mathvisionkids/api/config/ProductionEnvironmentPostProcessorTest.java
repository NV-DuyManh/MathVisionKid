package com.mathvisionkids.api.config;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.boot.context.config.ConfigDataEnvironmentPostProcessor;
import org.springframework.boot.env.EnvironmentPostProcessor;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.core.io.support.SpringFactoriesLoader;
import org.springframework.mock.env.MockEnvironment;

import static org.junit.jupiter.api.Assertions.*;

class ProductionEnvironmentPostProcessorTest {
    private final ProductionEnvironmentPostProcessor processor = new ProductionEnvironmentPostProcessor();

    private MockEnvironment production() {
        var environment = new MockEnvironment()
                .withProperty("spring.profiles.active", "prod")
                .withProperty("app.jwt.secret", "8bf2fd6349c085e6178aef70d2394ad96736ac439481fe76c2d98e6e482058cf")
                .withProperty("ai.callback.api-key", "b85c4ce9613d202409770e5b83f01df9fba69386c4df3d7df5cad3aa0451754b")
                .withProperty("spring.datasource.url", "jdbc:postgresql://postgres:5432/mathvision")
                .withProperty("spring.datasource.username", "mathvision")
                .withProperty("spring.datasource.password", "db-production-test-password")
                .withProperty("minio.endpoint", "http://minio:9000")
                .withProperty("minio.access-key", "mathvision-storage")
                .withProperty("minio.secret-key", "storage-production-test-password")
                .withProperty("ai.gateway.url", "http://ai-service:8000/internal/v1/jobs")
                .withProperty("ai.service.base-url", "http://ai-service:8000")
                .withProperty("app.cors.allowed-origins", "https://student.example.com, https://teacher.example.com");
        ConfigDataEnvironmentPostProcessor.applyTo(environment);
        return environment;
    }

    @Test void safeProductionLoadsWithoutDevelopmentDefaults() {
        var environment = production();
        assertDoesNotThrow(() -> processor.postProcessEnvironment(environment, null));
        assertEquals("never", environment.getProperty("management.endpoint.health.show-details"));
        assertEquals("never", environment.getProperty("management.endpoint.health.show-components"));
        assertEquals("false", environment.getProperty("springdoc.api-docs.enabled"));
        assertEquals("false", environment.getProperty("springdoc.swagger-ui.enabled"));
        assertEquals("framework", environment.getProperty("server.forward-headers-strategy"));
        assertEquals("8080", environment.getProperty("server.port"));
        assertTrue(SpringFactoriesLoader.loadFactoryNames(EnvironmentPostProcessor.class, getClass().getClassLoader())
                .contains(ProductionEnvironmentPostProcessor.class.getName()));
    }

    @Test void localDevelopmentStillLoadsItsExistingDefaults() {
        var environment = new MockEnvironment();
        ConfigDataEnvironmentPostProcessor.applyTo(environment);
        assertDoesNotThrow(() -> processor.postProcessEnvironment(environment, null));
        assertEquals("dev", environment.getDefaultProfiles()[0]);
        assertEquals("jdbc:postgresql://localhost:5432/mathvision", environment.getProperty("spring.datasource.url"));
        assertTrue(environment.getProperty("app.jwt.secret").contains("development"));
        assertTrue(environment.getProperty("app.cors.allowed-origins").contains("http://localhost:8081"));
        assertEquals("always", environment.getProperty("management.endpoint.health.show-details"));
        assertEquals("always", environment.getProperty("management.endpoint.health.show-components"));
    }

    @Test void productionWithoutEnvironmentCredentialsFailsBeforeStartup() {
        var environment = new MockEnvironment().withProperty("spring.profiles.active", "prod");
        ConfigDataEnvironmentPostProcessor.applyTo(environment);
        var exception = assertThrows(IllegalStateException.class, () -> processor.postProcessEnvironment(environment, null));
        assertEquals("JWT_SECRET is required in prod.", exception.getMessage());
        assertEquals("", environment.getProperty("spring.datasource.password"));
        assertEquals("", environment.getProperty("minio.secret-key"));
    }

    @ParameterizedTest @ValueSource(strings = {"dev", "test"})
    void productionCannotLoadDevelopmentOrTestProfiles(String profile) {
        var environment = production();
        environment.setActiveProfiles("prod", profile);
        assertThrows(IllegalStateException.class, () -> processor.postProcessEnvironment(environment, null));
    }

    @Test void demoSeedBeanIsExcludedEvenIfDevAndProdAreCombined() {
        try (var context = new AnnotationConfigApplicationContext()) {
            context.getEnvironment().setActiveProfiles("dev", "prod");
            context.register(SeedDataInitializer.class);
            context.refresh();
            assertFalse(context.containsBean("initData"));
        }
    }

    @ParameterizedTest @ValueSource(strings = {"app.jwt.secret", "ai.callback.api-key"})
    void requiredSecretsRejectWeakAndPublishedValuesWithoutPrintingSecrets(String property) {
        for (String secret : new String[]{"", "secret-key-default", "a".repeat(64),
                "super_secret_development_jwt_key_do_not_use_in_production_1234567890"}) {
            var environment = production().withProperty(property, secret);
            var exception = assertThrows(IllegalStateException.class, () -> processor.postProcessEnvironment(environment, null));
            if (!secret.isEmpty()) assertFalse(exception.getMessage().contains(secret));
        }
    }

    @ParameterizedTest @ValueSource(strings = {"spring.datasource.password", "minio.secret-key"})
    void productionRequiresNonDefaultStoragePasswords(String property) {
        for (String password : new String[]{"", "password123", "mathvision_password", "minioadmin123"}) {
            assertThrows(IllegalStateException.class,
                    () -> processor.postProcessEnvironment(production().withProperty(property, password), null));
        }
    }

    @ParameterizedTest @ValueSource(strings = {"*", "https://*.example.com", "http://student.example.com",
            "https://localhost", "https://127.0.0.1", "https://[::1]", "https://student.example.com/",
            "https://student.example.com/path", "https://student.example.com?debug=true",
            "https://student.example.com#fragment", "https://user@student.example.com", "https://student.example.com,"})
    void productionRejectsWildcardAndNonOriginCorsEntries(String origins) {
        assertThrows(IllegalStateException.class,
                () -> processor.postProcessEnvironment(production().withProperty("app.cors.allowed-origins", origins), null));
    }

    @Test void productionRejectsStubAiAndHealthDetailOverrides() {
        assertThrows(IllegalStateException.class,
                () -> processor.postProcessEnvironment(production().withProperty("ai.gateway.mode", "STUB"), null));
        assertThrows(IllegalStateException.class,
                () -> processor.postProcessEnvironment(production().withProperty("management.endpoint.health.show-details", "always"), null));
        assertThrows(IllegalStateException.class,
                () -> processor.postProcessEnvironment(production().withProperty("management.endpoint.health.show-components", "always"), null));
    }

    @Test void serverPortCanBeProvidedByTheHost() {
        assertEquals("9090", production().withProperty("PORT", "9090").getProperty("server.port"));
    }
}

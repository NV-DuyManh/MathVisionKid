package com.mathvisionkids.api.config;

import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

import java.nio.charset.StandardCharsets;
import java.util.Locale;

@Configuration
@Profile("prod")
@ConditionalOnProperty(name = "app.bootstrap.admin.enabled", havingValue = "true")
public class ProductionAdminInitializer {
    private static final Logger log = LoggerFactory.getLogger(ProductionAdminInitializer.class);

    @Bean
    public CommandLineRunner bootstrapProductionAdmin(
            UserRepository users, PasswordEncoder encoder, PlatformTransactionManager transactionManager,
            @Value("${app.bootstrap.admin.email:}") String configuredEmail,
            @Value("${app.bootstrap.admin.password:}") String password,
            @Value("${app.bootstrap.admin.name:}") String configuredName) {
        return args -> new TransactionTemplate(transactionManager).executeWithoutResult(status -> {
            // ponytail: one backend replica; add a database lock before supporting parallel initializers.
            if (users.count() != 0) {
                log.info("Administrator bootstrap skipped because users exist. Disable BOOTSTRAP_ADMIN_ENABLED and remove bootstrap credentials.");
                return;
            }
            String email = configuredEmail.trim().toLowerCase(Locale.ROOT);
            String name = configuredName.trim();
            if (email.length() > 254 || !email.matches("[^\\s@]+@[^\\s@]+\\.[^\\s@]+")) {
                throw new IllegalStateException("BOOTSTRAP_ADMIN_EMAIL must be a valid email address.");
            }
            if (name.isEmpty() || name.length() > 255) {
                throw new IllegalStateException("BOOTSTRAP_ADMIN_NAME must contain 1 to 255 characters.");
            }
            int passwordBytes = password.getBytes(StandardCharsets.UTF_8).length;
            String lower = password.toLowerCase(Locale.ROOT);
            if (passwordBytes < 16 || passwordBytes > 72 || password.chars().distinct().count() < 8
                    || lower.contains("password") || lower.contains("changeme") || lower.contains("development")
                    || lower.contains("mathvision123")) {
                throw new IllegalStateException("BOOTSTRAP_ADMIN_PASSWORD must be a strong generated password of 16 to 72 UTF-8 bytes.");
            }
            User admin = new User();
            admin.setEmail(email);
            admin.setDisplayName(name);
            admin.setPasswordHash(encoder.encode(password));
            admin.setRole("ADMIN");
            admin.setActive(true);
            users.save(admin);
            log.info("Initial administrator created. Disable BOOTSTRAP_ADMIN_ENABLED and remove bootstrap credentials.");
        });
    }
}

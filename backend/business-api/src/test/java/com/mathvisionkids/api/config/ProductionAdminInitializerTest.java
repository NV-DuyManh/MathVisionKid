package com.mathvisionkids.api.config;

import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.mockito.ArgumentCaptor;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionStatus;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class ProductionAdminInitializerTest {
    private static final String GENERATED_PASSWORD = "Ft3Y6jR8Q2nH7bW5zL4xC9mP1sK0vD6g";
    private final ProductionAdminInitializer initializer = new ProductionAdminInitializer();
    private final UserRepository users = mock(UserRepository.class);
    private final PasswordEncoder encoder = new BCryptPasswordEncoder();
    private final PlatformTransactionManager transactionManager = mock(PlatformTransactionManager.class);

    ProductionAdminInitializerTest() {
        when(transactionManager.getTransaction(any())).thenReturn(mock(TransactionStatus.class));
    }

    @Test void emptyDatabaseReceivesOneActiveAdminWithTheExistingBcryptEncoder() throws Exception {
        initializer.bootstrapProductionAdmin(users, encoder, transactionManager,
                " Owner@Example.com ", GENERATED_PASSWORD, " School Owner ").run();
        var captured = ArgumentCaptor.forClass(User.class);
        verify(users).save(captured.capture());
        User admin = captured.getValue();
        assertEquals("owner@example.com", admin.getEmail());
        assertEquals("School Owner", admin.getDisplayName());
        assertEquals("ADMIN", admin.getRole());
        assertTrue(admin.getActive());
        assertNotEquals(GENERATED_PASSWORD, admin.getPasswordHash());
        assertTrue(encoder.matches(GENERATED_PASSWORD, admin.getPasswordHash()));
        verify(transactionManager).commit(any());
    }

    @Test void restartDoesNotCreateOrChangeAnAccount() throws Exception {
        when(users.count()).thenReturn(0L, 1L);
        var runner = initializer.bootstrapProductionAdmin(users, encoder, transactionManager,
                "owner@example.com", GENERATED_PASSWORD, "School Owner");
        runner.run();
        runner.run();
        verify(users, times(1)).save(any());
        verify(users, times(2)).count();
        verifyNoMoreInteractions(users);
    }

    @Test void anyExistingUserPreventsBootstrapEvenWithMissingCredentials() throws Exception {
        when(users.count()).thenReturn(1L);
        var unusedEncoder = mock(PasswordEncoder.class);
        initializer.bootstrapProductionAdmin(users, unusedEncoder, transactionManager, "", "", "").run();
        verify(users).count();
        verifyNoMoreInteractions(users);
        verifyNoInteractions(unusedEncoder);
    }

    @ParameterizedTest @ValueSource(strings = {"", "MathVision123!", "password1234567890!",
            "changeme0123456789", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "Ft3Y6jR8Q2nH7bW5zL4xC9mP1sK0vD6g"})
    void invalidPasswordsFailWithoutLeakingTheInputOrWritingAnAccount(String input) {
        String password = input.equals(GENERATED_PASSWORD) ? input.repeat(3) : input;
        var exception = assertThrows(IllegalStateException.class,
                () -> initializer.bootstrapProductionAdmin(users, encoder, transactionManager,
                        "owner@example.com", password, "School Owner").run());
        if (!password.isEmpty()) assertFalse(exception.getMessage().contains(password));
        verify(users, never()).save(any());
        verify(transactionManager).rollback(any());
    }

    @Test void missingOrInvalidIdentityFailsWithoutAnAccountWrite() {
        for (String email : new String[]{"", "owner", "owner@example", "owner@example.com extra"}) {
            assertThrows(IllegalStateException.class,
                    () -> initializer.bootstrapProductionAdmin(users, encoder, transactionManager,
                            email, GENERATED_PASSWORD, "School Owner").run());
        }
        for (String name : new String[]{"", " ", "n".repeat(256)}) {
            assertThrows(IllegalStateException.class,
                    () -> initializer.bootstrapProductionAdmin(users, encoder, transactionManager,
                            "owner@example.com", GENERATED_PASSWORD, name).run());
        }
        verify(users, never()).save(any());
    }

    @Test void bootstrapIsOffByDefaultAndUnavailableInDevelopment() {
        new ApplicationContextRunner().withUserConfiguration(ProductionAdminInitializer.class)
                .withPropertyValues("spring.profiles.active=prod")
                .run(context -> assertFalse(context.containsBean("bootstrapProductionAdmin")));
        new ApplicationContextRunner().withUserConfiguration(ProductionAdminInitializer.class)
                .withPropertyValues("spring.profiles.active=dev", "app.bootstrap.admin.enabled=true")
                .run(context -> assertFalse(context.containsBean("bootstrapProductionAdmin")));
    }

    @Test void onlyExplicitProductionOptInRegistersTheRunner() {
        new ApplicationContextRunner().withUserConfiguration(ProductionAdminInitializer.class)
                .withPropertyValues("spring.profiles.active=prod", "app.bootstrap.admin.enabled=true")
                .withBean(UserRepository.class, () -> users)
                .withBean(PasswordEncoder.class, () -> encoder)
                .withBean(PlatformTransactionManager.class, () -> transactionManager)
                .run(context -> assertTrue(context.containsBean("bootstrapProductionAdmin")));
    }
}

package com.mathvisionkids.api.auth;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.Map;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class DemoLoginAliasTest {
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;
    @Autowired UserRepository users;
    @Autowired RefreshTokenRepository refresh;
    @Autowired PasswordEncoder encoder;
    @Autowired PlatformTransactionManager transactions;
    private User account;

    private void account(String email, String role, boolean active) {
        account = new TransactionTemplate(transactions).execute(tx -> {
            User user = new User();
            user.setEmail(email); user.setRole(role); user.setDisplayName("Alias login test");
            user.setPasswordHash(encoder.encode("123")); user.setActive(active);
            return users.save(user);
        });
    }

    @AfterEach void cleanUp() {
        if (account != null) new TransactionTemplate(transactions).execute(tx -> {
            refresh.deleteByUser(account); users.deleteById(account.getId()); return null;
        });
    }

    @ParameterizedTest
    @CsvSource({"student,minh.student@mathvision.local,STUDENT", "teacher,lan.teacher@mathvision.local,TEACHER", "admin,admin.demo@mathvision.local,ADMIN"})
    void aliasesUseStoredPasswordAndDatabaseRole(String alias, String email, String role) throws Exception {
        account(email, role, true);
        mvc.perform(post("/api/v1/auth/login").contentType(MediaType.APPLICATION_JSON)
            .content(mapper.writeValueAsBytes(Map.of("email", alias, "password", "wrong"))))
            .andExpect(status().isUnauthorized());
        var response = mvc.perform(post("/api/v1/auth/login").contentType(MediaType.APPLICATION_JSON)
            .content(mapper.writeValueAsBytes(Map.of("email", " " + alias.toUpperCase() + " ", "password", "123", "role", "ADMIN"))))
            .andExpect(status().isOk()).andReturn();
        String token = mapper.readTree(response.getResponse().getContentAsString()).get("accessToken").asText();
        mvc.perform(get("/api/v1/me").header("Authorization", "Bearer " + token))
            .andExpect(status().isOk()).andExpect(jsonPath("$.email").value(email)).andExpect(jsonPath("$.role").value(role));
        String forbidden = role.equals("ADMIN") ? "/api/v1/student/submissions" : "/api/v1/admin/dashboard";
        mvc.perform(get(forbidden).header("Authorization", "Bearer " + token)).andExpect(status().isForbidden());
    }

    @ParameterizedTest @CsvSource({"root,400", "student1,400", "student@gmail,401", "demo,400"})
    void arbitraryUsernamesAreNotExpanded(String alias, int expectedStatus) throws Exception {
        mvc.perform(post("/api/v1/auth/login").contentType(MediaType.APPLICATION_JSON)
            .content(mapper.writeValueAsBytes(Map.of("email", alias, "password", "123"))))
            .andExpect(status().is(expectedStatus));
    }

    @Test void aliasCannotReactivateDisabledAccount() throws Exception {
        account("minh.student@mathvision.local", "STUDENT", false);
        mvc.perform(post("/api/v1/auth/login").contentType(MediaType.APPLICATION_JSON)
            .content(mapper.writeValueAsBytes(Map.of("email", "student", "password", "123"))))
            .andExpect(status().isUnauthorized());
    }
}

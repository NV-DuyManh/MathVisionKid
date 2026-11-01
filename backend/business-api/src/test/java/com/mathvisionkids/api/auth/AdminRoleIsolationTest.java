package com.mathvisionkids.api.auth;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.http.MediaType;
import java.util.Map;
import java.util.UUID;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class AdminRoleIsolationTest {
    @Autowired MockMvc mvc;
    @Autowired UserRepository users;
    @Autowired JwtUtil jwt;
    @Autowired RefreshTokenService refresh;
    @Autowired PasswordEncoder encoder;
    @Autowired ObjectMapper json;
    private User admin;
    private User student;
    private User teacher;
    private User create(String role) {
        User user = new User();
        user.setEmail(UUID.randomUUID() + "@overhaul.test");
        user.setRole(role);
        user.setDisplayName("Isolated " + role);
        user.setPasswordHash(encoder.encode(UUID.randomUUID().toString()));
        user.setActive(true);
        return users.saveAndFlush(user);
    }
    @BeforeEach void setup() { admin = create("ADMIN"); student = create("STUDENT"); teacher = create("TEACHER"); }
    private String token(User user) { return "Bearer " + jwt.generateToken(user.getEmail(), user.getRole()); }
    @Test void studentAndTeacherCannotReadAnyAdministrativeCollection() throws Exception {
        for (User user : new User[]{student, teacher}) {
            for (String path : new String[]{"dashboard", "users", "classes", "audit"}) {
                mvc.perform(get("/api/v1/admin/" + path).header("Authorization", token(user))).andExpect(status().isForbidden());
            }
            mvc.perform(post("/api/v1/admin/users").header("Authorization", token(user))
                .contentType(MediaType.APPLICATION_JSON).content("{}")).andExpect(status().isForbidden());
        }
    }
    @Test void disabledAdminCannotReuseAnIssuedAccessToken() throws Exception {
        String issued = token(admin);
        admin.setActive(false); users.saveAndFlush(admin);
        mvc.perform(get("/api/v1/admin/dashboard").header("Authorization", issued)).andExpect(status().isUnauthorized());
        mvc.perform(get("/api/v1/me").header("Authorization", issued)).andExpect(status().isUnauthorized());
    }
    @Test void disabledStudentCannotReuseAnIssuedAccessToken() throws Exception {
        String issued = token(student);
        student.setActive(false); users.saveAndFlush(student);
        mvc.perform(get("/api/v1/me").header("Authorization", issued)).andExpect(status().isUnauthorized());
    }
    @Test void currentDatabaseRoleOverridesPreviouslyIssuedAdminClaim() throws Exception {
        String issued = token(admin);
        admin.setRole("STUDENT"); users.saveAndFlush(admin);
        mvc.perform(get("/api/v1/admin/dashboard").header("Authorization", issued)).andExpect(status().isForbidden());
        mvc.perform(get("/api/v1/me").header("Authorization", issued)).andExpect(status().isOk()).andExpect(jsonPath("$.role").value("STUDENT"));
    }
    @Test void disabledAccountCannotRefresh() throws Exception {
        String issued = refresh.createRefreshToken(admin.getId());
        admin.setActive(false); users.saveAndFlush(admin);
        mvc.perform(post("/api/v1/auth/refresh").contentType(MediaType.APPLICATION_JSON)
            .content(json.writeValueAsString(Map.of("refreshToken", issued)))).andExpect(status().isUnauthorized());
    }
    @Test void fakeAdministrativeTokenHasNoAuthority() throws Exception {
        mvc.perform(get("/api/v1/admin/dashboard").header("Authorization", "Bearer mock-admin-access-token")).andExpect(status().isUnauthorized());
    }
}

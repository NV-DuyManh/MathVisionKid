package com.mathvisionkids.api.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(properties = "app.cors.allowed-origins=http://localhost:5173, https://student.example.com")
@AutoConfigureMockMvc
@ActiveProfiles("test")
class SecurityDeploymentTest {
    @Autowired MockMvc mvc;

    @Test void configuredWebAndLocalOriginsCanPreflightAuthentication() throws Exception {
        for (String origin : new String[]{"http://localhost:5173", "https://student.example.com"}) {
            mvc.perform(options("/api/v1/auth/login").header("Origin", origin)
                    .header("Access-Control-Request-Method", "POST")
                    .header("Access-Control-Request-Headers", "Content-Type"))
                    .andExpect(status().isOk()).andExpect(header().string("Access-Control-Allow-Origin", origin));
        }
    }

    @Test void unlistedOriginsAreRejected() throws Exception {
        mvc.perform(options("/api/v1/auth/login").header("Origin", "https://untrusted.example.com")
                .header("Access-Control-Request-Method", "POST"))
                .andExpect(status().isForbidden()).andExpect(header().doesNotExist("Access-Control-Allow-Origin"));
    }

    @Test void healthShowsOnlyStatusAndOtherActuatorPathsNeedAuthentication() throws Exception {
        mvc.perform(get("/actuator/health")).andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"))
                .andExpect(jsonPath("$.components").doesNotExist()).andExpect(jsonPath("$.details").doesNotExist());
        mvc.perform(get("/actuator/env")).andExpect(status().isUnauthorized());
    }

    @Test void anonymousCannotReachRoleProtectedRoutes() throws Exception {
        mvc.perform(get("/api/v1/admin/users")).andExpect(status().isUnauthorized());
    }

    @Test @WithMockUser(roles = "STUDENT") void studentCannotReachAdminRoutes() throws Exception {
        mvc.perform(get("/api/v1/admin/users")).andExpect(status().isForbidden());
    }
}

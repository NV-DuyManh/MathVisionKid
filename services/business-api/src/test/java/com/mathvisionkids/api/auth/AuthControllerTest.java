package com.mathvisionkids.api.auth;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@org.springframework.transaction.annotation.Transactional
public class AuthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private RefreshTokenRepository refreshTokenRepository;

    @Autowired
    private org.springframework.security.crypto.password.PasswordEncoder passwordEncoder;

    private User testUser;
    
    @BeforeEach
    public void setup() {
        refreshTokenRepository.deleteAll();
        userRepository.deleteAll();
        
        testUser = new User();
        testUser.setEmail("test" + UUID.randomUUID() + "@student.com");
        testUser.setPasswordHash(passwordEncoder.encode("password"));
        testUser.setRole("STUDENT");
        testUser.setDisplayName("Test Student");
        userRepository.save(testUser);
    }

    @Test
    public void testLoginReturnsRefreshToken() throws Exception {
        Map<String, String> loginRequest = new HashMap<>();
        loginRequest.put("email", testUser.getEmail());
        loginRequest.put("password", "password"); // Stub password

        mockMvc.perform(post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").exists())
                .andExpect(jsonPath("$.refreshToken").exists());
    }

    @Test
    public void testValidRefreshSucceedsAndRotates() throws Exception {
        // 1. Login
        Map<String, String> loginRequest = new HashMap<>();
        loginRequest.put("email", testUser.getEmail());
        loginRequest.put("password", "password");

        MvcResult loginResult = mockMvc.perform(post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest)))
                .andReturn();
                
        String loginResponse = loginResult.getResponse().getContentAsString();
        Map<String, String> authData = objectMapper.readValue(loginResponse, Map.class);
        String oldRefreshToken = authData.get("refreshToken");

        // 2. Refresh
        Map<String, String> refreshReq = new HashMap<>();
        refreshReq.put("refreshToken", oldRefreshToken);

        MvcResult refreshResult = mockMvc.perform(post("/api/v1/auth/refresh")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(refreshReq)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").exists())
                .andExpect(jsonPath("$.refreshToken").exists())
                .andReturn();
                
        String refreshResp = refreshResult.getResponse().getContentAsString();
        Map<String, String> refreshData = objectMapper.readValue(refreshResp, Map.class);
        String newRefreshToken = refreshData.get("refreshToken");
        
        // Ensure rotation happened
        assertNotEquals(oldRefreshToken, newRefreshToken);
    }

    @Test
    public void testReusedRotatedTokenIsRejected() throws Exception {
        // 1. Login
        Map<String, String> loginRequest = new HashMap<>();
        loginRequest.put("email", testUser.getEmail());
        loginRequest.put("password", "password");

        MvcResult loginResult = mockMvc.perform(post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest)))
                .andReturn();
                
        String loginResponse = loginResult.getResponse().getContentAsString();
        Map<String, String> authData = objectMapper.readValue(loginResponse, Map.class);
        String oldRefreshToken = authData.get("refreshToken");

        // 2. Refresh to rotate it
        Map<String, String> refreshReq = new HashMap<>();
        refreshReq.put("refreshToken", oldRefreshToken);
        mockMvc.perform(post("/api/v1/auth/refresh")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(refreshReq)))
                .andExpect(status().isOk());
                
        // 3. Attempt to use old token again (replay attack)
        mockMvc.perform(post("/api/v1/auth/refresh")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(refreshReq)))
                .andExpect(status().isUnauthorized()); // Should trigger compromise revocation
    }

    @Test
    public void testLogoutRevokesToken() throws Exception {
        // 1. Login
        Map<String, String> loginRequest = new HashMap<>();
        loginRequest.put("email", testUser.getEmail());
        loginRequest.put("password", "password");

        MvcResult loginResult = mockMvc.perform(post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest)))
                .andReturn();
                
        String loginResponse = loginResult.getResponse().getContentAsString();
        Map<String, String> authData = objectMapper.readValue(loginResponse, Map.class);
        String jwtToken = authData.get("token");
        String refreshToken = authData.get("refreshToken");

        // 2. Logout
        mockMvc.perform(post("/api/v1/auth/logout")
                .header("Authorization", "Bearer " + jwtToken))
                .andExpect(status().isOk());
                
        // 3. Attempt to refresh with revoked token
        Map<String, String> refreshReq = new HashMap<>();
        refreshReq.put("refreshToken", refreshToken);

        mockMvc.perform(post("/api/v1/auth/refresh")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(refreshReq)))
                .andExpect(status().isUnauthorized());
    }
}

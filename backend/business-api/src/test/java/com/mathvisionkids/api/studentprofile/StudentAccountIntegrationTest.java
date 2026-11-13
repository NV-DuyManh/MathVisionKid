package com.mathvisionkids.api.studentprofile;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.auth.JwtUtil;
import com.mathvisionkids.api.auth.RefreshTokenService;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.UUID;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class StudentAccountIntegrationTest {
    @Autowired StudentRepository students;
    @Autowired StudentProfileService profiles;
    @Autowired PasswordEncoder encoder;
    @Autowired JdbcTemplate db;
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;
    @Autowired JwtUtil jwt;
    @Autowired RefreshTokenService tokens;
    Student pupil, other;
    static final String PASSWORD = "CurrentSecret-12";

    @BeforeEach void setup() {
        pupil = student(); other = student();
    }
    Student student() {
        var student = new Student();
        student.setEmail(UUID.randomUUID() + "@account.test"); student.setDisplayName("Sao Nhỏ");
        student.setGradeLevel(3); student.setRole("STUDENT"); student.setActive(true);
        student.setPasswordHash(encoder.encode(PASSWORD));
        return students.saveAndFlush(student);
    }
    byte[] picture() throws Exception {
        var image = new BufferedImage(400, 300, BufferedImage.TYPE_INT_RGB);
        var output = new ByteArrayOutputStream(); ImageIO.write(image, "png", output);
        output.write("PRIVATE_METADATA_MARKER".getBytes(StandardCharsets.UTF_8));
        return output.toByteArray();
    }
    @Test void photoIsNormalizedOwnedPrivateAndCanReturnToPreset() throws Exception {
        var result = mvc.perform(multipart("/api/v1/student/profile/photo").file(new MockMultipartFile("file", "phone.png", "image/png", picture()))
                .with(request -> { request.setMethod("PUT"); return request; }).with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control", "no-store")).andReturn();
        var photo = mapper.readTree(result.getResponse().getContentAsString()).get("avatarPhoto").asText();
        byte[] bytes = Base64.getDecoder().decode(photo.substring(photo.indexOf(',') + 1));
        var normalized = ImageIO.read(new ByteArrayInputStream(bytes));
        assertEquals(256, normalized.getWidth()); assertEquals(256, normalized.getHeight());
        assertFalse(new String(bytes, StandardCharsets.ISO_8859_1).contains("PRIVATE_METADATA_MARKER"));
        assertEquals(photo, profiles.get(pupil.getEmail()).avatarPhoto());
        assertNull(profiles.get(other.getEmail()).avatarPhoto());
        profiles.update(pupil.getEmail(), new ProfileDtos.Edit("Sao Nhỏ", "moon", true, null));
        assertFalse(mapper.writeValueAsString(profiles.leaderboard(pupil.getEmail(), null)).contains("data:image"));
        profiles.update(pupil.getEmail(), new ProfileDtos.Edit("Sao Nhỏ", "moon", false, null, true));
        assertNull(profiles.get(pupil.getEmail()).avatarPhoto());
    }
    @Test void invalidPhotoAndWrongRoleCannotWrite() throws Exception {
        mvc.perform(multipart("/api/v1/student/profile/photo").file(new MockMultipartFile("file", "avatar.jpg", "image/jpeg", "<svg/>".getBytes()))
                .with(request -> { request.setMethod("PUT"); return request; }).with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isUnprocessableEntity());
        mvc.perform(multipart("/api/v1/student/profile/photo").file(new MockMultipartFile("file", picture()))
                .with(request -> { request.setMethod("PUT"); return request; }).with(user("teacher@account.test").roles("TEACHER")))
                .andExpect(status().isForbidden());
        mvc.perform(post("/api/v1/student/profile/password").contentType("application/json").content("{}"))
                .andExpect(status().isUnauthorized());
        assertNull(profiles.get(pupil.getEmail()).avatarPhoto());
    }
    @Test void passwordRequiresCurrentSecretRevokesOldSessionsAndKeepsFreshSession() throws Exception {
        String oldAccess = jwt.generateToken(pupil.getEmail(), "STUDENT"), oldRefresh = tokens.createRefreshToken(pupil.getId());
        var response = change(PASSWORD, "NewSecret-123").andExpect(status().isOk()).andReturn();
        var body = mapper.readTree(response.getResponse().getContentAsString());
        assertFalse(jwt.validateToken(oldAccess, pupil.getEmail()));
        assertTrue(jwt.validateToken(body.get("accessToken").asText(), pupil.getEmail()));
        assertTrue(encoder.matches("NewSecret-123", students.findById(pupil.getId()).orElseThrow().getPasswordHash()));
        assertTrue(encoder.matches(PASSWORD, students.findById(other.getId()).orElseThrow().getPasswordHash()));
        mvc.perform(get("/api/v1/student/profile").header("Authorization", "Bearer " + oldAccess)).andExpect(status().isUnauthorized());
        mvc.perform(post("/api/v1/auth/refresh").contentType("application/json").content(mapper.writeValueAsString(java.util.Map.of("refreshToken", oldRefresh))))
                .andExpect(status().isUnauthorized());
        mvc.perform(get("/api/v1/student/profile").header("Authorization", "Bearer " + body.get("accessToken").asText())).andExpect(status().isOk());
    }
    @Test void photoByteLimitAndPixelBombAreRejectedBeforeDecoding() throws Exception {
        byte[] dimensions = picture();
        var header = java.nio.ByteBuffer.wrap(dimensions);
        header.putInt(16, 10_000); header.putInt(20, 10_000);
        var crc = new java.util.zip.CRC32(); crc.update(dimensions, 12, 17); header.putInt(29, (int) crc.getValue());
        for (byte[] bytes : new byte[][] { dimensions, new byte[5 * 1024 * 1024 + 1] }) {
            mvc.perform(multipart("/api/v1/student/profile/photo").file(new MockMultipartFile("file", "avatar.png", "image/png", bytes))
                    .with(request -> { request.setMethod("PUT"); return request; }).with(user(pupil.getEmail()).roles("STUDENT")))
                    .andExpect(status().isUnprocessableEntity());
        }
        assertNull(profiles.get(pupil.getEmail()).avatarPhoto());
    }
    @Test void wrongPasswordAttemptsPersistAndAreBounded() throws Exception {
        for (int index = 0; index < 5; index++) change("incorrect", "NewSecret-123").andExpect(status().isBadRequest());
        change(PASSWORD, "NewSecret-123").andExpect(status().isTooManyRequests());
        assertTrue(encoder.matches(PASSWORD, students.findById(pupil.getId()).orElseThrow().getPasswordHash()));
        db.update("UPDATE student_password_attempts SET started_at = ? WHERE student_id = ?", java.sql.Timestamp.from(java.time.Instant.now().minusSeconds(901)), pupil.getId());
        change(PASSWORD, "NewSecret-123").andExpect(status().isOk());
    }
    @Test void socialAccountsAndOversizedUtf8PasswordsAreRejected() throws Exception {
        change(PASSWORD, "ế".repeat(40)).andExpect(status().isBadRequest());
        pupil.setGoogleSubject(UUID.randomUUID().toString()); students.saveAndFlush(pupil);
        assertFalse(profiles.get(pupil.getEmail()).passwordLoginAvailable());
        change(PASSWORD, "NewSecret-123").andExpect(status().isConflict());
    }
    org.springframework.test.web.servlet.ResultActions change(String current, String next) throws Exception {
        return mvc.perform(post("/api/v1/student/profile/password").with(user(pupil.getEmail()).roles("STUDENT"))
                .contentType("application/json").content(mapper.writeValueAsString(java.util.Map.of("currentPassword", current, "newPassword", next))));
    }
}

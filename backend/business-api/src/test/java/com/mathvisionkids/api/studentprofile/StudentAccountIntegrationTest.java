package com.mathvisionkids.api.studentprofile;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.auth.JwtUtil;
import com.mathvisionkids.api.auth.RefreshTokenService;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.UUID;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
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
    @Autowired UserRepository users;
    @Autowired StudentProfileService profiles;
    @Autowired StudentRewards rewards;
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

    ProfileDtos.Profile saveProfile(String email, ProfileDtos.Edit edit) {
        return profiles.update(email, new ProfileDtos.Edit(edit.displayName(), edit.avatar(), edit.leaderboardVisible(),
                edit.selectedTitle(), edit.removePhoto(), edit.leaderboardNameHidden(), edit.leaderboardPhotoVisible(),
                profiles.get(email).privacyRevision()));
    }

    @Test void photoIsNormalizedOwnedPrivateAndCanReturnToPreset() throws Exception {
        String googlePhoto = "https://lh3.googleusercontent.com/a/synthetic-avatar";
        profiles.captureGoogleAvatar(pupil.getId(), googlePhoto);
        profiles.captureGoogleAvatar(pupil.getId(), null);
        profiles.captureGoogleAvatar(pupil.getId(), "https://lh3.googleusercontent.com.example.test/other");
        assertEquals(googlePhoto, profiles.get(pupil.getEmail()).avatarPhoto());
        assertNull(profiles.get(other.getEmail()).avatarPhoto());
        saveProfile(pupil.getEmail(), new ProfileDtos.Edit("Sao Nhỏ", "moon", true, null));
        assertFalse(mapper.writeValueAsString(profiles.leaderboard(pupil.getEmail(), null)).contains(googlePhoto));

        var result = mvc.perform(multipart("/api/v1/student/profile/photo").file(new MockMultipartFile("file", "phone.png", "image/png", picture()))
                .with(request -> { request.setMethod("PUT"); return request; }).with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control", "no-store")).andReturn();
        var photo = mapper.readTree(result.getResponse().getContentAsString()).get("avatarPhoto").asText();
        byte[] bytes = Base64.getDecoder().decode(photo.substring(photo.indexOf(',') + 1));
        var normalized = ImageIO.read(new ByteArrayInputStream(bytes));
        assertEquals(256, normalized.getWidth()); assertEquals(256, normalized.getHeight());
        assertFalse(new String(bytes, StandardCharsets.ISO_8859_1).contains("PRIVATE_METADATA_MARKER"));
        profiles.captureGoogleAvatar(pupil.getId(), googlePhoto + "-updated");
        assertEquals(photo, profiles.get(pupil.getEmail()).avatarPhoto());
        assertNull(profiles.get(other.getEmail()).avatarPhoto());
        saveProfile(pupil.getEmail(), new ProfileDtos.Edit("Sao Nhỏ", "moon", true, null));
        assertFalse(mapper.writeValueAsString(profiles.leaderboard(pupil.getEmail(), null)).contains("data:image"));
        saveProfile(pupil.getEmail(), new ProfileDtos.Edit("Sao Nhỏ", "moon", false, null, true));
        profiles.captureGoogleAvatar(pupil.getId(), googlePhoto);
        assertNull(profiles.get(pupil.getEmail()).avatarPhoto());
    }
    @Test void leaderboardSharesOnlyTheCurrentPhotoWithExplicitConsent() throws Exception {
        String pictureUrl = "https://lh3.googleusercontent.com/a/synthetic-avatar";
        profiles.captureGoogleAvatar(pupil.getId(), pictureUrl);
        rewards.record(pupil.getId(), StudentRewards.Source.QUIZ, "avatar-test", "avatar-test");
        var visible = new ProfileDtos.Edit("Sao Nhỏ", "moon", true, null);
        var share = new ProfileDtos.Edit("Sao Nhỏ", "moon", true, null, false, true, true);
        var stop = new ProfileDtos.Edit("Sao Nhỏ", "moon", true, null, false, true, false);

        var profile = saveProfile(pupil.getEmail(), visible);
        String alias = profile.publicAlias();
        assertFalse(profile.leaderboardPhotoVisible());
        assertNull(peerAvatar(alias));
        assertTrue(saveProfile(pupil.getEmail(), share).leaderboardPhotoVisible());
        assertEquals(pictureUrl, peerAvatar(alias));
        assertNull(profiles.get(other.getEmail()).avatarPhoto());

        profiles.captureGoogleAvatar(pupil.getId(), pictureUrl);
        assertEquals(pictureUrl, peerAvatar(alias));
        profiles.captureGoogleAvatar(pupil.getId(), pictureUrl + "-new");
        assertNull(peerAvatar(alias));

        assertTrue(saveProfile(pupil.getEmail(), share).leaderboardPhotoVisible());
        mvc.perform(multipart("/api/v1/student/profile/photo").file(new MockMultipartFile("file", "phone.png", "image/png", picture()))
                .with(request -> { request.setMethod("PUT"); return request; }).with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.leaderboardPhotoVisible").value(false));
        assertNull(peerAvatar(alias));

        var shared = saveProfile(pupil.getEmail(), share);
        String thumbnail = peerAvatar(alias);
        assertNotNull(thumbnail);
        assertNotEquals(shared.avatarPhoto(), thumbnail);
        var image = ImageIO.read(new ByteArrayInputStream(Base64.getDecoder().decode(thumbnail.substring(thumbnail.indexOf(',') + 1))));
        assertEquals(64, image.getWidth());
        assertEquals(64, image.getHeight());
        assertTrue(saveProfile(pupil.getEmail(), visible).leaderboardPhotoVisible());
        assertEquals(thumbnail, peerAvatar(alias));
        assertFalse(saveProfile(pupil.getEmail(), stop).leaderboardPhotoVisible());
        assertNull(peerAvatar(alias));

        assertTrue(saveProfile(pupil.getEmail(), share).leaderboardPhotoVisible());
        saveProfile(pupil.getEmail(), new ProfileDtos.Edit("Sao Nhỏ", "moon", false, null));
        saveProfile(pupil.getEmail(), visible);
        assertNull(peerAvatar(alias));
    }

    @Test void staleConsentCannotShareAReplacementPhotoOrCommitAName() throws Exception {
        String oldPhoto = "https://lh3.googleusercontent.com/a/confirmed-photo";
        profiles.captureGoogleAvatar(pupil.getId(), oldPhoto);
        rewards.record(pupil.getId(), StudentRewards.Source.QUIZ, "replace-photo", "replace-photo");
        changeProfile("{\"leaderboardVisible\":true}", privacyRevision()).andExpect(status().isOk());
        String snapshot = privacyRevision();
        profiles.captureGoogleAvatar(pupil.getId(), oldPhoto + "-replacement");

        changeProfile("{\"displayName\":\"Tên bản nháp\",\"leaderboardPhotoVisible\":true}", snapshot)
                .andExpect(status().isConflict()).andExpect(jsonPath("$.error.code").value("PROFILE_PRIVACY_CONFLICT"));
        var current = profiles.get(pupil.getEmail());
        assertEquals("Sao Nhỏ", current.displayName());
        assertNull(peerAvatar(current.publicAlias()));
        assertFalse(current.leaderboardPhotoVisible());
    }

    @Test void revokingTheSamePhotoInvalidatesAnEarlierOptInDraft() throws Exception {
        String photo = "https://lh3.googleusercontent.com/a/unchanged-photo";
        profiles.captureGoogleAvatar(pupil.getId(), photo);
        rewards.record(pupil.getId(), StudentRewards.Source.QUIZ, "revoke-photo", "revoke-photo");
        changeProfile("{\"leaderboardVisible\":true}", privacyRevision()).andExpect(status().isOk());
        String snapshot = privacyRevision();
        changeProfile("{\"leaderboardPhotoVisible\":true}", snapshot).andExpect(status().isOk());
        changeProfile("{\"leaderboardPhotoVisible\":false}", privacyRevision()).andExpect(status().isOk());

        changeProfile("{\"leaderboardPhotoVisible\":true}", snapshot).andExpect(status().isConflict());
        changeProfile("{\"displayName\":\"Tên cũ\",\"avatar\":\"moon\",\"leaderboardPhotoVisible\":true}", null)
                .andExpect(status().isConflict());
        var current = profiles.get(pupil.getEmail());
        assertEquals(photo, current.avatarPhoto());
        assertEquals("Sao Nhỏ", current.displayName());
        assertNull(peerAvatar(current.publicAlias()));
    }

    @Test void privacyOnlyKeepsNewNameAndInvalidPhotoConsentIsAtomic() throws Exception {
        var initial = profiles.get(pupil.getEmail());
        String snapshot = privacyRevision();
        changeProfile("{\"displayName\":\"Tên mới\",\"avatar\":\"moon\"}", null).andExpect(status().isOk());
        changeProfile("{\"leaderboardVisible\":true}", snapshot).andExpect(status().isConflict());
        changeProfile("{\"leaderboardVisible\":true}", privacyRevision()).andExpect(status().isOk())
                .andExpect(jsonPath("$.displayName").value("Tên mới")).andExpect(jsonPath("$.avatar").value("moon"));
        String participating = privacyRevision();
        changeProfile("{\"leaderboardVisible\":false}", participating).andExpect(status().isOk());
        changeProfile("{\"displayName\":\"Tên bản nháp\",\"leaderboardPhotoVisible\":true}", participating)
                .andExpect(status().isConflict());
        changeProfile("{\"displayName\":\"Tên bản nháp\",\"leaderboardPhotoVisible\":true}", privacyRevision())
                .andExpect(status().isConflict());
        var current = profiles.get(pupil.getEmail());
        assertEquals("Tên mới", current.displayName());
        assertEquals(initial.publicAlias(), current.publicAlias());
        assertFalse(current.leaderboardVisible());
    }

    @Test void legacyPartialPrivacyEditsRequireAnUpdateForExpansionAndStillAllowRevocation() throws Exception {
        changeProfile("""
                {"displayName":"Tên bản nháp","avatar":"moon","leaderboardVisible":true,"removePhoto":false}
                """, null)
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.error.code").value("PROFILE_PRIVACY_CONFLICT"))
                .andExpect(jsonPath("$.error.message").value(
                        "Em cập nhật ứng dụng hoặc tải lại trang web để thay đổi quyền công khai nhé."));
        changeProfile("{\"leaderboardVisible\":true}", privacyRevision()).andExpect(status().isOk());
        changeProfile("{\"leaderboardNameHidden\":false}", null).andExpect(status().isConflict());
        changeProfile("{\"leaderboardVisible\":false}", null).andExpect(status().isOk())
                .andExpect(jsonPath("$.leaderboardVisible").value(false))
                .andExpect(jsonPath("$.leaderboardNameHidden").value(true))
                .andExpect(jsonPath("$.displayName").value("Sao Nhỏ"));
    }

    @Test void legacyFullPrivacyPayloadRevokesParticipationWithoutRestoringAStalePublicName() throws Exception {
        String photo = "https://lh3.googleusercontent.com/a/legacy-consent";
        profiles.captureGoogleAvatar(pupil.getId(), photo);
        changeProfile("""
                {"avatar":"moon","leaderboardVisible":true,"leaderboardNameHidden":false,"leaderboardPhotoVisible":true}
                """, privacyRevision()).andExpect(status().isOk());
        changeProfile("{\"leaderboardNameHidden\":true}", privacyRevision()).andExpect(status().isOk());
        String beforeRevocation = privacyRevision();

        changeProfile("""
                {"displayName":"Tên bản nháp","avatar":"rocket","leaderboardVisible":false,
                 "leaderboardNameHidden":false,"removePhoto":false}
                """, null).andExpect(status().isOk())
                .andExpect(jsonPath("$.leaderboardVisible").value(false))
                .andExpect(jsonPath("$.leaderboardNameHidden").value(true))
                .andExpect(jsonPath("$.leaderboardPhotoVisible").value(false))
                .andExpect(jsonPath("$.displayName").value("Sao Nhỏ"))
                .andExpect(jsonPath("$.avatar").value("moon"))
                .andExpect(jsonPath("$.avatarPhoto").value(photo));
        assertNotEquals(beforeRevocation, privacyRevision());
        changeProfile("{\"leaderboardVisible\":true,\"leaderboardNameHidden\":false}", beforeRevocation)
                .andExpect(status().isConflict());
    }

    private String privacyRevision() throws Exception {
        var json = mvc.perform(get("/api/v1/student/profile").with(user(pupil.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andReturn().getResponse().getContentAsString();
        return mapper.readTree(json).path("privacyRevision").textValue();
    }

    @ParameterizedTest
    @ValueSource(booleans = {false, true})
    void renamingWhileHiddenRequiresFreshConsentToShowTheNewName(boolean renamedByAdmin) throws Exception {
        rewards.record(pupil.getId(), StudentRewards.Source.QUIZ, "name-consent", "name-consent");
        var before = saveProfile(pupil.getEmail(),
                new ProfileDtos.Edit("Tên Ban Đầu", null, true, null, null, true, null));

        if (renamedByAdmin) {
            var admin = new User();
            admin.setDisplayName("Synthetic Admin");
            admin.setEmail(UUID.randomUUID() + "@admin.test");
            admin.setPasswordHash("unused");
            admin.setRole("ADMIN");
            users.saveAndFlush(admin);

            mvc.perform(patch("/api/v1/admin/users/" + pupil.getId()).with(user(admin.getEmail()).roles("ADMIN"))
                            .contentType("application/json").content("{\"displayName\":\"Tên Mới\",\"gradeLevel\":4}"))
                    .andExpect(status().isOk()).andExpect(jsonPath("$.gradeLevel").value(4));
        } else {
            changeProfile("{\"displayName\":\"Tên Mới\"}", null).andExpect(status().isOk());
        }

        var current = profiles.get(pupil.getEmail());
        assertEquals("Tên Mới", current.displayName());
        assertNotEquals(before.privacyRevision(), current.privacyRevision());
        assertTrue(current.leaderboardNameHidden());
        changeProfile("{\"displayName\":\"Tên Mới\"}", null)
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.privacyRevision").value(current.privacyRevision().toString()));

        changeProfile("{\"leaderboardNameHidden\":false}", before.privacyRevision().toString())
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.error.code").value("PROFILE_PRIVACY_CONFLICT"));
        assertNull(peerAvatar(before.publicAlias()));
        changeProfile("{\"leaderboardNameHidden\":false}", current.privacyRevision().toString())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.leaderboardNameHidden").value(false));
        assertNull(peerAvatar("Tên Mới"));
    }

    private org.springframework.test.web.servlet.ResultActions changeProfile(String json, String revision) throws Exception {
        var payload = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(json);
        if (revision != null) payload.put("privacyRevision", revision);
        return mvc.perform(put("/api/v1/student/profile").with(user(pupil.getEmail()).roles("STUDENT"))
                .contentType("application/json").content(payload.toString()));
    }

    private String peerAvatar(String alias) throws Exception {
        var response = mvc.perform(get("/api/v1/student/leaderboard").param("allGrades", "true")
                        .with(user(other.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control", "no-store")).andReturn();
        for (var entry : mapper.readTree(response.getResponse().getContentAsString()).get("entries")) {
            if (alias.equals(entry.path("alias").asText())) {
                assertFalse(entry.get("self").asBoolean());
                return entry.path("avatarPhoto").textValue();
            }
        }
        throw new AssertionError("Expected student entry in leaderboard");
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
        for (int index = 0; index < 5; index++) change(index == 0 ? "ế".repeat(100) : "incorrect", "NewSecret-123").andExpect(status().isBadRequest());
        change(PASSWORD, "NewSecret-123").andExpect(status().isTooManyRequests());
        assertTrue(encoder.matches(PASSWORD, students.findById(pupil.getId()).orElseThrow().getPasswordHash()));
        db.update("UPDATE student_password_attempts SET started_at = ? WHERE student_id = ?", java.sql.Timestamp.from(java.time.Instant.now().minusSeconds(901)), pupil.getId());
        change(PASSWORD, "NewSecret-123").andExpect(status().isOk());
    }
    @Test void socialAccountsAndOversizedUtf8PasswordsAreRejected() throws Exception {
        change(PASSWORD, "ế".repeat(40)).andExpect(status().isBadRequest());
        pupil.setGoogleSubject(UUID.randomUUID().toString()); students.saveAndFlush(pupil);
        assertFalse(profiles.get(pupil.getEmail()).passwordLoginAvailable());
        assertTrue(profiles.get(pupil.getEmail()).googleLinked());
        change(PASSWORD, "NewSecret-123").andExpect(status().isConflict());
    }
    org.springframework.test.web.servlet.ResultActions change(String current, String next) throws Exception {
        return mvc.perform(post("/api/v1/student/profile/password").with(user(pupil.getEmail()).roles("STUDENT"))
                .contentType("application/json").content(mapper.writeValueAsString(java.util.Map.of("currentPassword", current, "newPassword", next))));
    }
}

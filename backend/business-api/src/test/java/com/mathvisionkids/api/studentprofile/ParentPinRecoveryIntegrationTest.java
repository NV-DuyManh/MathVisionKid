package com.mathvisionkids.api.studentprofile;

import com.mathvisionkids.api.auth.RefreshTokenService;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.sql.Timestamp;
import java.time.Instant;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(properties = {
        "app.auth.email.enabled=true", "app.auth.email.from=sender@example.test",
        "spring.mail.host=example.test", "spring.mail.port=587",
        "spring.mail.username=test", "spring.mail.password=test",
        "spring.mail.properties.mail.smtp.auth=true", "spring.mail.properties.mail.smtp.starttls.enable=true"
})
@ActiveProfiles("test")
@AutoConfigureMockMvc
class ParentPinRecoveryIntegrationTest {
    private static final String BASE = "/api/v1/student/parent-control";
    private static final String HEADER = "X-MathVision-Parent-Grant";
    @Autowired MockMvc mvc;
    @Autowired StudentRepository students;
    @Autowired JdbcTemplate db;
    @Autowired RefreshTokenService sessions;
    @MockitoBean JavaMailSender mail;

    @Test
    void emailCodeSetsAndRecoversPinWhileKeepingLimitsAndInvalidatingOldAccess() throws Exception {
        var student = student();
        var other = student();
        String auth = bearer(student);
        mvc.perform(post(BASE + "/pin-code/request").contentType("application/json").content("{\"purpose\":\"SETUP\"}"))
                .andExpect(status().isUnauthorized());
        request(auth, "SETUP").andExpect(status().isOk())
                .andExpect(jsonPath("$.maskedEmail").value(student.getEmail().substring(0, 2) + "***@example.test"));
        String firstCode = lastCode(student);
        request(auth, "SETUP").andExpect(status().isTooManyRequests());
        request(bearer(other), "RESET").andExpect(status().isConflict());
        confirm(bearer(other), "SETUP", firstCode, "123456").andExpect(status().isForbidden());
        confirm(auth, "SETUP", firstCode, "123456").andExpect(status().isNoContent());
        confirm(auth, "SETUP", firstCode, "123456").andExpect(status().isConflict());

        mvc.perform(put(BASE + "/daily-limit").header("Authorization", auth).contentType("application/json")
                        .content("{\"pin\":\"123456\",\"minutes\":45}")).andExpect(status().isOk());
        mvc.perform(put(BASE + "/game-limit").header("Authorization", auth).contentType("application/json")
                        .content("{\"pin\":\"123456\",\"minutes\":15}")).andExpect(status().isOk());
        String oldGrant = unlock(auth, "123456").andExpect(status().isOk()).andReturn().getResponse().getHeader(HEADER);
        assertNotNull(oldGrant);
        db.update("UPDATE student_parent_control SET locked_until = ? WHERE student_id = ?",
                Timestamp.from(Instant.now().plusSeconds(300)), student.getId());
        unlock(auth, "123456").andExpect(status().isTooManyRequests());

        ageCode(student, 61);
        clearInvocations(mail);
        request(auth, "RESET").andExpect(status().isOk());
        String resetCode = lastCode(student);
        confirm(auth, "RESET", resetCode.equals("999999") ? "999998" : "999999", "654321").andExpect(status().isForbidden());
        confirm(auth, "RESET", resetCode, "654321").andExpect(status().isNoContent());
        confirm(auth, "RESET", resetCode, "234567").andExpect(status().isForbidden());

        mvc.perform(get(BASE + "/settings").header("Authorization", auth).header(HEADER, oldGrant))
                .andExpect(status().isForbidden()).andExpect(jsonPath("$.error.code").value("PARENT_GRANT_REQUIRED"));
        unlock(auth, "123456").andExpect(status().isForbidden());
        unlock(auth, "654321").andExpect(status().isOk())
                .andExpect(header().exists(HEADER))
                .andExpect(jsonPath("$.dailyMinutes").value(45)).andExpect(jsonPath("$.gameMinutes").value(15));
        mvc.perform(get("/api/v1/me").header("Authorization", auth)).andExpect(status().isOk());
    }

    @Test
    void expiryWrongAttemptsAndDeliveryFailureAreEnforced() throws Exception {
        var student = student();
        String auth = bearer(student);
        request(auth, "SETUP").andExpect(status().isOk());
        String code = lastCode(student);
        ageCode(student, 601);
        confirm(auth, "SETUP", code, "123456").andExpect(status().isForbidden());
        clearInvocations(mail);
        request(auth, "SETUP").andExpect(status().isOk());
        code = lastCode(student);
        String wrong = code.equals("999999") ? "999998" : "999999";
        for (int n = 0; n < 5; n++) confirm(auth, "SETUP", wrong, "123456").andExpect(status().isForbidden());
        confirm(auth, "SETUP", code, "123456").andExpect(status().isTooManyRequests());
        ageCode(student, 61);
        doThrow(new org.springframework.mail.MailSendException("fixture")).when(mail).send(any(SimpleMailMessage.class));
        request(auth, "SETUP").andExpect(status().isServiceUnavailable());
        assertNull(db.queryForObject("SELECT code_hash FROM student_parent_pin_challenge WHERE student_id = ?", String.class, student.getId()));
        ageCode(student, 61);
        request(auth, "SETUP").andExpect(status().isTooManyRequests());
    }

    private Student student() {
        var student = new Student();
        student.setEmail(UUID.randomUUID() + "@example.test");
        student.setDisplayName("Parent PIN fixture");
        student.setRole("STUDENT");
        student.setGradeLevel(3);
        student.setPasswordHash("unused");
        return students.saveAndFlush(student);
    }

    private String bearer(Student student) {
        return "Bearer " + sessions.createSession(student.getId()).getAccessToken();
    }

    private org.springframework.test.web.servlet.ResultActions request(String auth, String purpose) throws Exception {
        return mvc.perform(post(BASE + "/pin-code/request").header("Authorization", auth).contentType("application/json")
                .content("{\"purpose\":\"%s\"}".formatted(purpose)));
    }

    private org.springframework.test.web.servlet.ResultActions confirm(String auth, String purpose, String code, String pin) throws Exception {
        return mvc.perform(post(BASE + "/pin-code/confirm").header("Authorization", auth).contentType("application/json")
                .content("{\"purpose\":\"%s\",\"code\":\"%s\",\"pin\":\"%s\"}".formatted(purpose, code, pin)));
    }

    private org.springframework.test.web.servlet.ResultActions unlock(String auth, String pin) throws Exception {
        return mvc.perform(post(BASE + "/unlock").header("Authorization", auth).contentType("application/json")
                .content("{\"pin\":\"%s\"}".formatted(pin)));
    }

    private String lastCode(Student student) {
        var message = ArgumentCaptor.forClass(SimpleMailMessage.class);
        verify(mail).send(message.capture());
        assertArrayEquals(new String[]{ student.getEmail() }, message.getValue().getTo());
        var matcher = java.util.regex.Pattern.compile("\\b[0-9]{6}\\b").matcher(message.getValue().getText());
        assertTrue(matcher.find());
        return matcher.group();
    }

    private void ageCode(Student student, long seconds) {
        db.update("UPDATE student_parent_pin_challenge SET issued_at = ? WHERE student_id = ?",
                Timestamp.from(Instant.now().minusSeconds(seconds)), student.getId());
    }
}

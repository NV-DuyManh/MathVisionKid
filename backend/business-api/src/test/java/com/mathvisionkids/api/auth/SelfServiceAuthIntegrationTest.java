package com.mathvisionkids.api.auth;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.user.*;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.MailSendException;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.mockito.ArgumentCaptor;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;
import java.util.regex.Pattern;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(properties = {"app.auth.email.enabled=true", "app.auth.email.from=recovery@example.test",
    "spring.mail.host=smtp.example.test", "spring.mail.port=587", "spring.mail.username=test-only",
    "spring.mail.password=test-only", "spring.mail.properties.mail.smtp.auth=true",
    "spring.mail.properties.mail.smtp.starttls.enable=true"})
@ActiveProfiles("test") @AutoConfigureMockMvc
class SelfServiceAuthIntegrationTest {
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;
    @Autowired UserRepository users;
    @Autowired PasswordResetCodeRepository codes;
    @Autowired PasswordEncoder encoder;
    @Autowired SelfServiceAuthService service;
    @MockBean JavaMailSender mail;
    User pupil;
    @BeforeEach void createPupil() {
        Student item = new Student();
        item.setEmail(UUID.randomUUID()+"@example.test"); item.setDisplayName("Test pupil");
        item.setRole("STUDENT"); item.setGradeLevel(3); item.setPasswordHash(encoder.encode("old-password"));
        pupil=users.saveAndFlush(item);
    }
    Map<String,Object> registration(String role) {
        return new HashMap<>(Map.of("email",UUID.randomUUID()+"@example.test", "displayName","Test pupil",
            "password","test-password", "role",role, "gender","PREFER_NOT_TO_SAY", "phoneNumber","0123456789", "gradeLevel",3));
    }
    void submitRegistration(Map<String,Object> body, int expected) throws Exception {
        mvc.perform(post("/api/v1/auth/register").contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(body)))
            .andExpect(status().is(expected));
    }
    String issueCode() {
        service.requestPasswordReset(pupil.getEmail());
        var sent=ArgumentCaptor.forClass(SimpleMailMessage.class); verify(mail).send(sent.capture());
        var code=Pattern.compile("\\b[0-9]{6}\\b").matcher(sent.getValue().getText());
        assertTrue(code.find()); return code.group();
    }
    ConfirmPasswordResetRequest reset(String code) {
        var request=new ConfirmPasswordResetRequest(); request.setEmail(pupil.getEmail());
        request.setCode(code); request.setNewPassword("new-password"); return request;
    }
    @Test void studentRegistrationStoresAnEncodedPasswordAndCannotRequestAdmin() throws Exception {
        var body=registration("STUDENT"); submitRegistration(body,201);
        var saved=users.findByEmail((String)body.get("email")).orElseThrow();
        assertEquals("STUDENT",saved.getRole()); assertTrue(encoder.matches("test-password",saved.getPasswordHash()));
        submitRegistration(registration("ADMIN"),400);
    }
    @Test void studentGradeAndTeacherGradeAreValidated() throws Exception {
        var missing=registration("STUDENT"); missing.remove("gradeLevel"); submitRegistration(missing,400);
        submitRegistration(registration("TEACHER"),400);
        var teacher=registration("TEACHER"); teacher.remove("gradeLevel"); submitRegistration(teacher,201);
    }
    @Test void unicodePasswordsExceedingBcryptByteLimitAreRejectedBeforeEncoding() throws Exception {
        var body=registration("STUDENT"); body.put("password","ấ".repeat(30)); submitRegistration(body,400);
    }
    @Test void unknownResetAccountReturnsGenericAcceptedResponse() throws Exception {
        mvc.perform(post("/api/v1/auth/password-reset/request").contentType(MediaType.APPLICATION_JSON)
            .content("{\"email\":\"unknown@example.test\"}")).andExpect(status().isAccepted());
        verifyNoInteractions(mail);
    }
    @Test void resetCodeIsHashedAndCannotBeReused() {
        String code=issueCode(); var stored=codes.findTopByUser_IdAndConsumedFalseOrderByCreatedAtDesc(pupil.getId()).orElseThrow();
        assertNotEquals(code,stored.getCodeHash()); assertTrue(encoder.matches(code,stored.getCodeHash()));
        assertTrue(service.confirmPasswordReset(reset(code))); assertFalse(service.confirmPasswordReset(reset(code)));
        assertTrue(encoder.matches("new-password",users.findById(pupil.getId()).orElseThrow().getPasswordHash()));
    }
    @Test void fiveFailedAttemptsBlockEvenTheCorrectCode() {
        String code=issueCode(); String bad=code.equals("111111") ? "222222":"111111";
        for(int i=0;i<5;i++) assertFalse(service.confirmPasswordReset(reset(bad)));
        assertFalse(service.confirmPasswordReset(reset(code)));
        assertEquals(5,codes.findTopByUser_IdAndConsumedFalseOrderByCreatedAtDesc(pupil.getId()).orElseThrow().getAttempts());
    }
    @Test void expiredAndDisabledAccountsCannotResetPasswords() {
        String code=issueCode(); var stored=codes.findTopByUser_IdAndConsumedFalseOrderByCreatedAtDesc(pupil.getId()).orElseThrow();
        stored.setExpiresAt(Instant.now().minusSeconds(1)); codes.saveAndFlush(stored);
        assertFalse(service.confirmPasswordReset(reset(code)));
        stored.setExpiresAt(Instant.now().plusSeconds(60)); codes.saveAndFlush(stored);
        pupil.setActive(false); users.saveAndFlush(pupil);
        assertFalse(service.confirmPasswordReset(reset(code)));
    }
    @Test void simultaneousUseOfTheSameCodeSucceedsExactlyOnce() throws Exception {
        String code=issueCode(); var start=new CountDownLatch(1);
        try(var pool=Executors.newFixedThreadPool(2)) {
            Callable<Boolean> use=()->{start.await(); return service.confirmPasswordReset(reset(code));};
            var first=pool.submit(use); var second=pool.submit(use); start.countDown();
            assertEquals(1,(first.get(10,TimeUnit.SECONDS)?1:0)+(second.get(10,TimeUnit.SECONDS)?1:0));
        }
    }
    @Test void deliveryFailureDoesNotRevealAnAccountAndRetainsTheRateLimitRecord() throws Exception {
        doThrow(new MailSendException("test transport failure")).when(mail).send(any(SimpleMailMessage.class));
        mvc.perform(post("/api/v1/auth/password-reset/request").contentType(MediaType.APPLICATION_JSON)
            .content(mapper.writeValueAsString(Map.of("email",pupil.getEmail())))).andExpect(status().isAccepted());
        assertTrue(codes.findTopByUser_IdAndConsumedFalseOrderByCreatedAtDesc(pupil.getId()).isEmpty());
        assertEquals(1,codes.countByUser_IdAndCreatedAtAfter(pupil.getId(),Instant.now().minusSeconds(60)));
    }
    @Test void providerLoginIsUnavailableWithoutConfigurationRatherThanTrustingClientClaims() throws Exception {
        for(String provider:List.of("google","facebook"))
            mvc.perform(post("/api/v1/auth/"+provider).contentType(MediaType.APPLICATION_JSON)
                .content("{\"credential\":\"untrusted\",\"role\":\"STUDENT\",\"gradeLevel\":3}"))
                .andExpect(status().isServiceUnavailable());
    }
}

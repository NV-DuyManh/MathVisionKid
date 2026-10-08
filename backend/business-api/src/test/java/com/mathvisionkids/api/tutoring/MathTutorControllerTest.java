package com.mathvisionkids.api.tutoring;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.util.HashMap;
import java.util.Map;
import java.util.stream.Stream;

import static com.mathvisionkids.api.tutoring.MathTutorDtos.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/** Uses the production SecurityConfig and JWT filter, with only the external tutor service mocked. */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class MathTutorControllerTest {
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper json;
    @MockBean MathTutorService service;

    private static MockMultipartFile image() {
        return new MockMultipartFile("file", "page.png", "image/png", new byte[]{1});
    }

    private static String divisionRequest(boolean confirmed) {
        return """
                {"confirmed":%s,"division":{"dividend":"49572","divisor":"6","quotient":"8262","rows":["015","037","012","00"]}}
                """.formatted(confirmed);
    }

    @Test void anonymousCannotGradeDivision() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/division/check").contentType(MediaType.APPLICATION_JSON)
                .content(divisionRequest(true))).andExpect(status().isUnauthorized());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(roles = "TEACHER") void otherRoleCannotGradeDivision() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/division/check").contentType(MediaType.APPLICATION_JSON)
                .content(divisionRequest(true))).andExpect(status().isForbidden());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(roles = "STUDENT") void studentMustConfirmValidBoundedDivisionFields() throws Exception {
        for (String body : new String[]{divisionRequest(false), divisionRequest(true).replace("8262", "solve"),
                divisionRequest(true).replace("\"015\"", "null"), divisionRequest(true).replace("\"49572\"", "null")}) {
            mvc.perform(post("/api/v1/student/tutor/division/check").contentType(MediaType.APPLICATION_JSON)
                    .content(body)).andExpect(status().isBadRequest());
        }
        verifyNoInteractions(service);
        when(service.checkDivision(any())).thenCallRealMethod();
        mvc.perform(post("/api/v1/student/tutor/division/check").contentType(MediaType.APPLICATION_JSON)
                .content(divisionRequest(true))).andExpect(status().isOk()).andExpect(jsonPath("$.status").value("CORRECT"));
    }

    @Test @WithMockUser(roles = "STUDENT") void actualArithmeticReturnsRepairThenSuccessAfterStudentChanges() throws Exception {
        when(service.checkDivision(any())).thenCallRealMethod();
        String written = """
                {"confirmed":true,"division":{"dividend":"17843","divisor":"3","quotient":"59947","rows":["028","014","023","02"]}}
                """;
        mvc.perform(post("/api/v1/student/tutor/division/check").contentType(MediaType.APPLICATION_JSON).content(written))
                .andExpect(status().isOk()).andExpect(jsonPath("$.status").value("TRY_AGAIN"))
                .andExpect(jsonPath("$.field").value("quotient"));
        mvc.perform(post("/api/v1/student/tutor/division/check").contentType(MediaType.APPLICATION_JSON).content(written.replace("59947", "5947")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.status").value("CORRECT"));
    }

    private static Map<String, Object> validGuide() {
        Map<String, Object> request = new HashMap<>();
        request.put("problemText", "Lan có 12 bút, cho bạn 3 bút. Hỏi còn bao nhiêu bút?");
        request.put("problemConfirmed", true);
        request.put("stage", "PLAN");
        request.put("studentAttempt", "");
        request.put("hintLevel", 0);
        return request;
    }

    @Test void anonymousStudentRoutesRequireAuthentication() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/lesson").contentType(MediaType.APPLICATION_JSON)
                .content("{\"problemText\":\"Lan có 12 bút và 5 bút.\",\"workText\":\"\"}")).andExpect(status().isUnauthorized());
        mvc.perform(multipart("/api/v1/student/tutor/read").file(image()).param("privacyConfirmed", "true"))
                .andExpect(status().isUnauthorized());
        mvc.perform(post("/api/v1/student/tutor/guide").contentType(MediaType.APPLICATION_JSON)
                .content(json.writeValueAsBytes(validGuide()))).andExpect(status().isUnauthorized());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(roles = "TEACHER")
    void teacherCannotUseStudentTutoringEndpoints() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/lesson").contentType(MediaType.APPLICATION_JSON)
                .content("{\"problemText\":\"Lan có 12 bút và 5 bút.\",\"workText\":\"\"}")).andExpect(status().isForbidden());
        mvc.perform(multipart("/api/v1/student/tutor/read").file(image()).param("privacyConfirmed", "true"))
                .andExpect(status().isForbidden());
        mvc.perform(post("/api/v1/student/tutor/guide").contentType(MediaType.APPLICATION_JSON)
                .content(json.writeValueAsBytes(validGuide()))).andExpect(status().isForbidden());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(username = "student-a", roles = "STUDENT")
    void lessonOwnershipComesFromAuthenticationInsteadOfTheRequestBody() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/lesson").contentType(MediaType.APPLICATION_JSON)
                .content("{\"problemText\":\"Lan có 12 bút và 5 bút.\",\"workText\":\"\",\"problemConfirmed\":true,\"workConfirmed\":false,\"owner\":\"student-b\"}"))
                .andExpect(status().isOk());
        verify(service).lesson(any(LessonRequest.class), eq("student-a"));
    }

    @Test @WithMockUser(username = "student-a", roles = "STUDENT")
    void lessonAnswerUsesAuthenticatedOwnerAndRejectsInvalidRevision() throws Exception {
        String body = "{\"sessionId\":\"abcdefghijklmnopqrstuv\",\"revision\":0,\"answer\":\"12\",\"hint\":false,\"owner\":\"student-b\"}";
        mvc.perform(post("/api/v1/student/tutor/lesson/answer").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isOk());
        verify(service).answer(any(LessonAnswer.class), eq("student-a"));
        reset(service);
        mvc.perform(post("/api/v1/student/tutor/lesson/answer").contentType(MediaType.APPLICATION_JSON).content(body.replace("\"revision\":0", "\"revision\":-1")))
                .andExpect(status().isBadRequest());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(roles = "STUDENT") void lessonRejectsMissingAndFalseSourceConfirmation() throws Exception {
        for (String body : new String[]{
                "{\"problemText\":\"Lan có 12 bút.\",\"workText\":\"\"}",
                "{\"problemText\":\"Lan có 12 bút.\",\"workText\":\"\",\"problemConfirmed\":false,\"workConfirmed\":false}",
                "{\"problemText\":\"Lan có 12 bút.\",\"workText\":\"3/2 = 1\",\"problemConfirmed\":true,\"workConfirmed\":false}",
                "{\"problemText\":\"Lan có [?] bút.\",\"workText\":\"\",\"problemConfirmed\":true,\"workConfirmed\":false}"}) {
            mvc.perform(post("/api/v1/student/tutor/lesson").contentType(MediaType.APPLICATION_JSON)
                    .content(body)).andExpect(status().isBadRequest());
        }
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(roles = "STUDENT")
    void workedPhotoAloneCannotStartALesson() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/lesson").contentType(MediaType.APPLICATION_JSON)
                .content("{\"problemText\":\"\",\"workText\":\"90 × 2 ÷ 15 = 12\"}"))
                .andExpect(status().isBadRequest());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(roles = "ADMIN")
    void adminCannotBypassStudentRolePolicy() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/guide").contentType(MediaType.APPLICATION_JSON)
                .content(json.writeValueAsBytes(validGuide()))).andExpect(status().isForbidden());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(roles = "STUDENT")
    void studentCanReadAnImageWithExplicitPrivacyConsent() throws Exception {
        when(service.read(any(), eq(true))).thenReturn(new ReadResponse("Đề toán", true, "Em kiểm tra lại đề nhé."));
        mvc.perform(multipart("/api/v1/student/tutor/read").file(image()).param("privacyConfirmed", "true"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.problemText").value("Đề toán"))
                .andExpect(jsonPath("$.needsReview").value(true)).andExpect(jsonPath("$.apiKey").doesNotExist())
                .andExpect(jsonPath("$.provider").doesNotExist());
        verify(service).read(any(), eq(true));
    }

    @Test @WithMockUser(roles = "STUDENT")
    void missingPrivacyConsentRemainsFalse() throws Exception {
        when(service.read(any(), eq(false))).thenThrow(new com.mathvisionkids.api.common.ApiException(
                "PRIVACY_REQUIRED", "Em hãy đồng ý sử dụng ảnh.", org.springframework.http.HttpStatus.BAD_REQUEST));
        mvc.perform(multipart("/api/v1/student/tutor/read").file(image()))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error.code").value("PRIVACY_REQUIRED"));
        verify(service).read(any(), eq(false));
    }

    @Test @WithMockUser(roles = "STUDENT")
    void studentCanReceiveOnlyThePublicGuidanceFields() throws Exception {
        when(service.guide(any())).thenReturn(new GuideResponse("PLAN", "Số bút giảm khi cho bớt.",
                "Em chọn phép tính nào?", "", false));
        mvc.perform(post("/api/v1/student/tutor/guide").contentType(MediaType.APPLICATION_JSON)
                .content(json.writeValueAsBytes(validGuide())))
                .andExpect(status().isOk()).andExpect(jsonPath("$.stage").value("PLAN"))
                .andExpect(jsonPath("$.hint").exists()).andExpect(jsonPath("$.question").exists())
                .andExpect(jsonPath("$.guarded").value(false)).andExpect(jsonPath("$.provider").doesNotExist());
    }

    private Map<String, Object> validCoach() {
        return Map.of("problemText", "", "workText", "49 : 7 × 2 = 14 (con)", "stage", "CHECK_WORK",
                "studentAttempt", "", "focusText", "49 : 7 × 2 = 14 (con)", "hintLevel", 0, "previousHint", "");
    }

    @Test
    void notebookEndpointsRequireAuthentication() throws Exception {
        mvc.perform(multipart("/api/v1/student/tutor/inspect").file(image()).param("privacyConfirmed", "true"))
                .andExpect(status().isUnauthorized());
        mvc.perform(post("/api/v1/student/tutor/coach").contentType(MediaType.APPLICATION_JSON)
                .content(json.writeValueAsBytes(validCoach()))).andExpect(status().isUnauthorized());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(roles = "TEACHER")
    void notebookEndpointsKeepStudentRoleBoundaries() throws Exception {
        mvc.perform(multipart("/api/v1/student/tutor/inspect").file(image()).param("privacyConfirmed", "true"))
                .andExpect(status().isForbidden());
        mvc.perform(post("/api/v1/student/tutor/coach").contentType(MediaType.APPLICATION_JSON)
                .content(json.writeValueAsBytes(validCoach()))).andExpect(status().isForbidden());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(roles = "STUDENT")
    void invalidNotebookStageAndMissingFieldsAreRejectedBeforeProviderCalls() throws Exception {
        Map<String, Object> request = new HashMap<>(validCoach());
        request.put("stage", "SOLVE_ALL");
        mvc.perform(post("/api/v1/student/tutor/coach").contentType(MediaType.APPLICATION_JSON)
                .content(json.writeValueAsBytes(request))).andExpect(status().isBadRequest());
        mvc.perform(post("/api/v1/student/tutor/coach").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isBadRequest());
        verifyNoInteractions(service);
    }

    static Stream<Map<String, Object>> invalidGuideRequests() {
        return Stream.of(
                Map.of("problemText", ""), Map.of("problemText", "12"), Map.of("problemText", "a".repeat(4001)),
                Map.of("problemConfirmed", false), Map.of("stage", "SOLVE_ALL"),
                Map.of("hintLevel", -1), Map.of("hintLevel", 3),
                Map.of("studentAttempt", "a".repeat(2001)), Map.of("previousHint", "a".repeat(1201)))
                .map(change -> { Map<String, Object> request = validGuide(); request.putAll(change); return request; });
    }

    @ParameterizedTest @MethodSource("invalidGuideRequests") @WithMockUser(roles = "STUDENT")
    void invalidGuidanceRequestsDoNotReachTheAiService(Map<String, Object> request) throws Exception {
        mvc.perform(post("/api/v1/student/tutor/guide").contentType(MediaType.APPLICATION_JSON)
                .content(json.writeValueAsBytes(request)))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error.code").value("VALIDATION_ERROR"));
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(roles = "STUDENT")
    void missingRequiredFieldsAndMalformedJsonAreSafeValidationErrors() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/guide").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error.code").value("VALIDATION_ERROR"));
        mvc.perform(post("/api/v1/student/tutor/guide").contentType(MediaType.APPLICATION_JSON).content("{"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error.code").value("VALIDATION_ERROR"));
        mvc.perform(multipart("/api/v1/student/tutor/read").file(image()).param("privacyConfirmed", "banana"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error.code").value("VALIDATION_ERROR"));
        verifyNoInteractions(service);
    }
}

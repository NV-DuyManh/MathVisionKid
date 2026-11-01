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
    @Test @WithMockUser(username="real-pupil",roles="STUDENT") void privateDraftPreparationUsesAuthenticatedOwner() throws Exception {
        when(service.prepareLesson(any(),eq("real-pupil"))).thenReturn(new LessonPreparationStatus("preparing"));
        mvc.perform(post("/api/v1/student/tutor/lesson/prepare").contentType(MediaType.APPLICATION_JSON)
                .content("{\"problemText\":\"Có 7 hộp, mỗi hộp 9 bút.\",\"workText\":\"\",\"owner\":\"victim\"}"))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control","no-store"))
                .andExpect(jsonPath("$.phase").value("preparing")).andExpect(jsonPath("$.step").doesNotExist());
        verify(service).prepareLesson(any(),eq("real-pupil"));
        verify(service,never()).lesson(any(),anyString());
    }

    @Test void anonymousCannotPrepareADraft() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/lesson/prepare").contentType(MediaType.APPLICATION_JSON)
                .content("{\"problemText\":\"Có 7 hộp, mỗi hộp 9 bút.\",\"workText\":\"\"}"))
                .andExpect(status().isUnauthorized());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(username="teacher",roles="TEACHER") void teacherCannotUseStudentDraftPreparation() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/lesson/prepare").contentType(MediaType.APPLICATION_JSON)
                .content("{\"problemText\":\"Có 7 hộp, mỗi hộp 9 bút.\",\"workText\":\"\"}"))
                .andExpect(status().isForbidden());
        verifyNoInteractions(service);
    }
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper json;
    @MockBean MathTutorService service;

    @Test @WithMockUser(username="real-pupil",roles="STUDENT") void longNarrationPreparationIsPrivateAndReturnsOnlyProgress() throws Exception {
        when(service.prepareNarration(any(),eq("real-pupil"))).thenReturn(Map.of("phase","waiting","mode","online","percent",0,"elapsedMs",0,"completedChunks",0,"totalChunks",0));
        mvc.perform(post("/api/v1/student/tutor/lesson/narration/prepare").contentType(MediaType.APPLICATION_JSON)
                .content("{\"sessionId\":\"owned-long-narration-123\",\"revision\":0,\"paragraphs\":[\"Em đọc lại đề.\"],\"owner\":\"other\"}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.phase").value("waiting"));
        verify(service).prepareNarration(argThat(request -> !request.prefetch()),eq("real-pupil"));
    }

    @Test @WithMockUser(username="real-pupil",roles="STUDENT") void narrationPreparationAcceptsBackgroundPriorityWithoutTrustingOwner() throws Exception {
        when(service.prepareNarration(any(),eq("real-pupil"))).thenReturn(Map.of("phase","waiting","mode","online","percent",0,"elapsedMs",0,"completedChunks",0,"totalChunks",0));
        mvc.perform(post("/api/v1/student/tutor/lesson/narration/prepare").contentType(MediaType.APPLICATION_JSON)
                .content("{\"sessionId\":\"owned-long-narration-123\",\"revision\":0,\"paragraphs\":[\"Em đọc lại đề.\"],\"prefetch\":true,\"owner\":\"other\"}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.phase").value("waiting"));
        verify(service).prepareNarration(argThat(request -> request.prefetch() && !request.useFallback()),eq("real-pupil"));
    }

    @Test @WithMockUser(username="real-pupil",roles="STUDENT") void narrationPreparationCapacityRemainsRetryableForTheAuthenticatedPupil() throws Exception {
        when(service.prepareNarration(any(),eq("real-pupil"))).thenThrow(new com.mathvisionkids.api.common.ApiException(
                "NARRATION_BUSY","Đang chuẩn bị lời giảng. Em chờ một chút nhé.",org.springframework.http.HttpStatus.TOO_MANY_REQUESTS));
        mvc.perform(post("/api/v1/student/tutor/lesson/narration/prepare").contentType(MediaType.APPLICATION_JSON)
                .content("{\"sessionId\":\"owned-long-narration-123\",\"revision\":0,\"paragraphs\":[\"Em đọc lại đề.\"],\"owner\":\"other\"}"))
                .andExpect(status().isTooManyRequests()).andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error.code").value("NARRATION_BUSY"));
        verify(service).prepareNarration(any(),eq("real-pupil"));
    }

    @Test @WithMockUser(username="real-pupil",roles="STUDENT") void audioOnlyAcceptStillReceivesTheRealJsonErrorStatus() throws Exception {
        when(service.narration(any(),eq("real-pupil"))).thenThrow(new com.mathvisionkids.api.common.ApiException("NARRATION_UNAVAILABLE","Chưa tạo được giọng đọc.",org.springframework.http.HttpStatus.SERVICE_UNAVAILABLE));
        mvc.perform(post("/api/v1/student/tutor/lesson/narration").contentType(MediaType.APPLICATION_JSON).accept("audio/wav")
                .content(json.writeValueAsString(Map.of("sessionId","narration-session-12345","revision",0,"paragraphs",java.util.List.of("Em đọc đề.")))))
                .andExpect(status().isServiceUnavailable()).andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.error.code").value("NARRATION_UNAVAILABLE"));
    }

    @Test void anonymousCannotPreparePrivateFutureMedia() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/lesson/media/prepare").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isUnauthorized());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(username="real-pupil",roles="STUDENT") void prepareUsesAuthenticatedOwnerAndRejectsUnsupportedVoice() throws Exception {
        when(service.prepareMedia(any(),eq("real-pupil"))).thenReturn(Map.of("totalSteps",5,"preparedSteps",1,"preparedCharacters",300,"failedItems",0));
        mvc.perform(post("/api/v1/student/tutor/lesson/media/prepare").contentType(MediaType.APPLICATION_JSON)
                .content("{\"sessionId\":\"prepare-session-123456\",\"revision\":0,\"voice\":\"vi-VN-HoaiMyNeural\",\"owner\":\"victim\"}"))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control","no-store"));
        verify(service).prepareMedia(any(),eq("real-pupil"));
        mvc.perform(post("/api/v1/student/tutor/lesson/media/prepare").contentType(MediaType.APPLICATION_JSON)
                .content("{\"sessionId\":\"prepare-session-123456\",\"revision\":0,\"voice\":\"unknown\"}"))
                .andExpect(status().isBadRequest());
        verifyNoMoreInteractions(service);
    }







    @Test @WithMockUser(username="real-pupil",roles="STUDENT") void narrationIsPrivateAndUsesOnlyTheAuthenticatedOwner() throws Exception {
        when(service.narration(any(),eq("real-pupil"))).thenReturn(new byte[]{1,2,3});
        mvc.perform(post("/api/v1/student/tutor/lesson/narration").contentType(MediaType.APPLICATION_JSON)
                .content("{\"sessionId\":\"narration-session-12345\",\"revision\":0,\"paragraphs\":[\"Em gộp hai nhóm.\"],\"owner\":\"victim\"}"))
                .andExpect(status().isOk()).andExpect(content().contentType("audio/wav")).andExpect(header().string("Cache-Control","no-store"));
        verify(service).narration(argThat(request -> request.voice().equals("vi-VN-NamMinhNeural")),eq("real-pupil"));
    }

    @Test @WithMockUser(username="real-pupil",roles="STUDENT") void narrationAcceptsOnlyTheTwoVietnameseVoices() throws Exception {
        when(service.narration(any(),eq("real-pupil"))).thenReturn(new byte[]{1,2,3});
        for (String voice : new String[]{"vi-VN-NamMinhNeural", "vi-VN-HoaiMyNeural"}) {
            mvc.perform(post("/api/v1/student/tutor/lesson/narration").contentType(MediaType.APPLICATION_JSON)
                    .content(json.writeValueAsString(Map.of("sessionId","narration-session-12345","revision",0,"paragraphs",java.util.List.of("Em gộp hai nhóm."),"voice",voice))))
                    .andExpect(status().isOk());
            verify(service).narration(argThat(request -> request.voice().equals(voice)),eq("real-pupil"));
        }
        clearInvocations(service);
        for (String voice : new String[]{"en-US-EmmaMultilingualNeural", "", "vi-VN-NamMinhNeural-evil"})
            mvc.perform(post("/api/v1/student/tutor/lesson/narration").contentType(MediaType.APPLICATION_JSON)
                    .content(json.writeValueAsString(Map.of("sessionId","narration-session-12345","revision",0,"paragraphs",java.util.List.of("Em gộp hai nhóm."),"voice",voice))))
                    .andExpect(status().isBadRequest());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(roles="TEACHER") void teacherCannotDownloadStudentNarration() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/lesson/narration").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isForbidden()); verifyNoInteractions(service);
    }

    @Test @WithMockUser(username="real-pupil",roles="STUDENT") void narrationProgressDoesNotTrustOwnerFromBody() throws Exception {
        when(service.narrationStatus(any(),eq("real-pupil"))).thenReturn(Map.of("phase","fallback","mode","offline","percent",45));
        mvc.perform(post("/api/v1/student/tutor/lesson/narration/status").contentType(MediaType.APPLICATION_JSON)
                .content("{\"sessionId\":\"narration-session-12345\",\"revision\":0,\"paragraphs\":[\"Em gộp hai nhóm.\"],\"owner\":\"victim\"}"))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control","no-store")).andExpect(jsonPath("$.percent").value(45));
        verify(service).narrationStatus(any(),eq("real-pupil"));
    }

    @Test @WithMockUser(roles="TEACHER") void teacherCannotReadStudentNarrationProgress() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/lesson/narration/status").contentType(MediaType.APPLICATION_JSON)
                .content("{\"sessionId\":\"narration-session-12345\",\"revision\":0,\"paragraphs\":[\"Em gộp hai nhóm.\"]}"))
                .andExpect(status().isForbidden());
        verifyNoInteractions(service);
    }

    @Test void anonymousCannotDownloadStudentNarration() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/lesson/narration").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isUnauthorized()); verifyNoInteractions(service);
    }

    private static MockMultipartFile image() {
        return new MockMultipartFile("file", "page.png", "image/png", new byte[]{1});
    }

    @Test void anonymousCannotAskOrTranscribe() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/lesson/ask").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isUnauthorized());
        mvc.perform(multipart("/api/v1/student/tutor/transcribe").file(image())).andExpect(status().isUnauthorized());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(roles="TEACHER") void teacherCannotAskOrTranscribeThroughStudentEndpoints() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/lesson/ask").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isForbidden());
        mvc.perform(multipart("/api/v1/student/tutor/transcribe").file(image())).andExpect(status().isForbidden());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(username="real-pupil", roles="STUDENT") void questionOwnerComesFromAuthentication() throws Exception {
        when(service.ask(any(),eq("real-pupil"))).thenReturn(new LessonReply("Ta cần phần bằng nhau.", "Mình chia các phần bằng nhau nhé.", "Vì sao?", false));
        mvc.perform(post("/api/v1/student/tutor/lesson/ask").contentType(MediaType.APPLICATION_JSON)
                .content("{\"sessionId\":\"conversation-session-123456\",\"revision\":0,\"stepIndex\":0,\"question\":\"Vì sao?\",\"owner\":\"victim\"}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.answer").value("Ta cần phần bằng nhau."));
        verify(service).ask(any(),eq("real-pupil"));
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
                .andExpect(jsonPath("$.field").value("quotient"))
                .andExpect(jsonPath("$.hints.length()").value(2))
                .andExpect(jsonPath("$.hints[0]").value(org.hamcrest.Matchers.containsString("số đang chia là 14")));
        mvc.perform(post("/api/v1/student/tutor/division/check").contentType(MediaType.APPLICATION_JSON).content(written.replace("59947", "5947")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.status").value("CORRECT"))
                .andExpect(jsonPath("$.hints.length()").value(0));
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

    private static Map<String, Object> validWorkReview() {
        return new HashMap<>(Map.of("sourceId", "source-1234567890", "problemText", "Có 12 bút, thêm 5 bút.",
                "workText", "12+5=18", "problemConfirmed", true, "workConfirmed", true));
    }

    @Test void anonymousCannotReviewWork() throws Exception {
        mvc.perform(post("/api/v1/student/tutor/work-review").contentType(MediaType.APPLICATION_JSON)
                .content(json.writeValueAsBytes(validWorkReview()))).andExpect(status().isUnauthorized());
        verifyNoInteractions(service);
    }

    @ParameterizedTest @org.junit.jupiter.params.provider.ValueSource(strings = {"TEACHER", "ADMIN"})
    void nonStudentCannotReviewWork(String role) throws Exception {
        mvc.perform(post("/api/v1/student/tutor/work-review").with(org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user("other").roles(role))
                .contentType(MediaType.APPLICATION_JSON).content(json.writeValueAsBytes(validWorkReview())))
                .andExpect(status().isForbidden());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(username = "student-a", roles = "STUDENT")
    void studentCanReviewOnlyTheExplicitlySubmittedWork() throws Exception {
        var request = validWorkReview();
        request.put("owner", "student-b");
        mvc.perform(post("/api/v1/student/tutor/work-review").contentType(MediaType.APPLICATION_JSON)
                .content(json.writeValueAsBytes(request))).andExpect(status().isOk());
        verify(service).reviewWork(eq(new WorkReviewRequest("source-1234567890", "Có 12 bút, thêm 5 bút.", "12+5=18", true, true)));
    }

    @Test @WithMockUser(roles = "STUDENT")
    void workReviewRejectsMissingUncertainUnboundedAndCoercedConfirmations() throws Exception {
        for (Map<String, Object> change : java.util.List.<Map<String, Object>>of(
                Map.of("sourceId", "short"), Map.of("sourceId", "x".repeat(101)),
                Map.of("problemText", " "), Map.of("problemText", "a".repeat(4001)), Map.of("problemText", "Có [?] bút."),
                Map.of("workText", " [?] "), Map.of("workText", " "), Map.of("workText", "a".repeat(6001)),
                Map.of("workText", "a".repeat(501)), Map.of("workText", String.join("\n", java.util.Collections.nCopies(36, "dòng"))),
                Map.of("problemConfirmed", false), Map.of("workConfirmed", false),
                Map.of("problemConfirmed", "true"), Map.of("workConfirmed", "true"),
                Map.of("problemConfirmed", 1), Map.of("workConfirmed", 1))) {
            var request = validWorkReview();
            request.putAll(change);
            mvc.perform(post("/api/v1/student/tutor/work-review").contentType(MediaType.APPLICATION_JSON)
                    .content(json.writeValueAsBytes(request))).andExpect(status().isBadRequest());
        }
        for (String field : new String[]{"sourceId", "problemText", "workText", "problemConfirmed", "workConfirmed"}) {
            var request = validWorkReview();
            request.remove(field);
            mvc.perform(post("/api/v1/student/tutor/work-review").contentType(MediaType.APPLICATION_JSON)
                    .content(json.writeValueAsBytes(request))).andExpect(status().isBadRequest());
        }
        verifyNoInteractions(service);
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
    @Test @WithMockUser(username="real-pupil",roles="STUDENT")
    void followupUsesAuthenticatedOwnerAndHasNoPublicCaching() throws Exception {
        when(service.checkpoint(any(),eq("real-pupil"))).thenReturn(new LearningCheck("13 + 8","Thử tính nhé.",false,false,""));
        mvc.perform(post("/api/v1/student/tutor/lesson/checkpoint").contentType(MediaType.APPLICATION_JSON)
                .content("{\"sessionId\":\"owned-followup-session-123\",\"revision\":1,\"answer\":\"\",\"owner\":\"victim\"}"))
                .andExpect(status().isOk()).andExpect(header().string("Cache-Control","no-store"))
                .andExpect(jsonPath("$.correct").value(false)).andExpect(jsonPath("$.answer").doesNotExist());
        verify(service).checkpoint(any(),eq("real-pupil"));
    }

    @Test void anonymousCannotResumeOrCheckUnderstanding() throws Exception {
        for(String route:new String[]{"resume","checkpoint"})
            mvc.perform(post("/api/v1/student/tutor/lesson/"+route).contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isUnauthorized());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(username="teacher",roles="TEACHER") void teacherCannotResumeOrCheckAStudentLesson() throws Exception {
        for(String route:new String[]{"resume","checkpoint"})
            mvc.perform(post("/api/v1/student/tutor/lesson/"+route).contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isForbidden());
        verifyNoInteractions(service);
    }

    @Test @WithMockUser(username="real-pupil",roles="STUDENT")
    void retiredVideoEndpointsHaveNoHandler() throws Exception {
        for (String suffix : new String[]{"", "/status", "/content"})
            mvc.perform(post("/api/v1/student/tutor/lesson/video"+suffix)
                    .contentType(MediaType.APPLICATION_JSON).content("{}"))
                    .andExpect(status().isNotFound());
        verifyNoInteractions(service);
    }
}

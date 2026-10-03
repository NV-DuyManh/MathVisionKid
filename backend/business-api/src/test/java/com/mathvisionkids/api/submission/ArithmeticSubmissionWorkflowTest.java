package com.mathvisionkids.api.submission;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.analysis.*;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.user.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;
import java.time.Instant;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(properties = "ai.callback.api-key=workflow-key")
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class ArithmeticSubmissionWorkflowTest {
    @Autowired SubmissionRepository submissions;
    @Autowired SubmissionImageRepository images;
    @Autowired AnalysisResultRepository results;
    @Autowired AiJobRepository jobs;
    @Autowired StudentRepository students;
    @Autowired TeacherRepository teachers;
    @Autowired SubmissionService service;
    @Autowired InternalAiCallbackController callback;
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;
    @MockBean AiAnalysisGateway gateway;
    @MockBean ObjectStorageService storage;
    Student student;
    Submission submission;
    AiJob job;

    @BeforeEach void setup() throws Exception {
        student = new Student();
        student.setEmail("arithmetic-workflow@test.com"); student.setPasswordHash("test");
        student.setRole("STUDENT"); student.setDisplayName("Student"); student.setGradeLevel(2);
        students.save(student);
        submission = new Submission(); submission.setStudent(student); submission.setStatus("PROCESSING");
        submissions.save(submission);
        job = newJob();
        when(storage.store(any(), any())).thenReturn("submissions/new-image.jpg");
    }

    private AiJob newJob() {
        AiJob next = new AiJob(); next.setSubmission(submission); next.setStatus("QUEUED");
        return jobs.saveAndFlush(next);
    }

    private List<Map<String, Object>> tokens() {
        return List.of(token("a-tens", "1", 0, 1), token("a-units", "2", 0, 0),
                token("b-tens", "2", 1, 1), token("b-units", "2", 1, 0),
                Map.of("tokenId", "plus", "value", "+", "tokenClass", "operator", "boundingBox", List.of(.1, .3, .1, .1),
                        "row", 1, "column", 2, "confidence", .9, "ambiguity", false),
                token("r-tens", "3", 2, 1), token("r-units", "4", 2, 0));
    }
    private Map<String, Object> token(String id, String value, int row, int column) {
        return Map.of("tokenId", id, "value", value, "tokenClass", "digit", "row", row, "column", column,
                "boundingBox", List.of(.1, .1, .1, .1), "confidence", .8, "ambiguity", false);
    }
    private AiCallbackRequest payload(String expression) {
        AiCallbackRequest request = new AiCallbackRequest(); request.setStatus("FEEDBACK_READY");
        request.setRecognizedExercise(expression); request.setRecognizedTokens(tokens());
        request.setValidation(Map.of("isValid", true, "diagnosisState", "VALID", "evidence", List.of()));
        request.setStudentFeedback(Map.of("title", "Đã kiểm tra", "hint", "Phép tính khớp.", "revealAnswer", false));
        request.setModelVersion("MODEL:actual-model:1:abc");
        return request;
    }
    private TokenConfirmationRequest correction(String tokenId, String value) {
        TokenConfirmationRequest request = new TokenConfirmationRequest();
        request.setJobId(job.getJobId()); request.setTokenId(tokenId); request.setNewClass(value);
        return request;
    }

    @Test void realCallbackFieldsReachOnlyTheOwner() throws Exception {
        callback.aiJobCompleted(job.getJobId(), "workflow-key", payload("12 + 22 = 34"));
        mvc.perform(get("/api/v1/student/submissions/" + submission.getSubmissionId())
                .with(user(student.getEmail()).roles("STUDENT")))
                .andExpect(status().isOk()).andExpect(jsonPath("$.jobId").value(job.getJobId().toString()))
                .andExpect(jsonPath("$.recognizedExercise.expression").value("12 + 22 = 34"))
                .andExpect(jsonPath("$.recognizedExercise.tokens[0].tokenId").value("a-tens"))
                .andExpect(jsonPath("$.validation.isValid").value(true))
                .andExpect(jsonPath("$.studentFeedback.revealAnswer").value(false));
        Student other = new Student(); other.setEmail("other-arithmetic@test.com"); other.setPasswordHash("test");
        other.setDisplayName("Other"); other.setRole("STUDENT"); other.setGradeLevel(2); students.save(other);
        mvc.perform(get("/api/v1/student/submissions/" + submission.getSubmissionId())
                .with(user(other.getEmail()).roles("STUDENT"))).andExpect(status().isForbidden());
    }

    @Test void identifiedCorrectionRevalidatesAndPreservesOriginalTokensAndScores() throws Exception {
        callback.aiJobCompleted(job.getJobId(), "workflow-key", payload("12 + 22 = 34"));
        mvc.perform(post("/api/v1/student/submissions/" + submission.getSubmissionId() + "/confirm-token")
                .with(user(student.getEmail()).roles("STUDENT")).contentType("application/json")
                .content(mapper.writeValueAsString(correction("b-tens", "1"))))
                .andExpect(status().isOk()).andExpect(jsonPath("$.recognizedExercise.expression").value("12 + 12 = 34"))
                .andExpect(jsonPath("$.validation.isValid").value(false))
                .andExpect(jsonPath("$.validation.diagnosisState").value("INVALID"))
                .andExpect(jsonPath("$.evidence.items[0].tokenId").value("r-tens"))
                .andExpect(jsonPath("$.evidence.items[0].columnIndex").value(1))
                .andExpect(jsonPath("$.recognizedExercise.rawExpression").value("12 + 22 = 34"))
                .andExpect(jsonPath("$.recognizedExercise.rawTokens[2].value").value("2"))
                .andExpect(jsonPath("$.recognizedExercise.tokens[2].value").value("1"))
                .andExpect(jsonPath("$.recognizedExercise.tokens[3].value").value("2"))
                .andExpect(jsonPath("$.recognizedExercise.rawTokens[2].confidence").value(.8))
                .andExpect(jsonPath("$.studentFeedback.revealAnswer").value(false));
        SubmissionResponse valid = service.confirmToken(student.getEmail(), submission.getSubmissionId(), correction("r-tens", "2"));
        assertEquals("12 + 12 = 24", valid.getRecognizedExercise().get("expression"));
        assertEquals(true, valid.getValidation().get("isValid"));
        assertEquals(List.of(), valid.getEvidence().get("items"));
    }

    @Test void staleOrUnknownTokenConfirmationIsRejectedWithoutChangingRawWork() {
        callback.aiJobCompleted(job.getJobId(), "workflow-key", payload("12 + 22 = 34"));
        TokenConfirmationRequest stale = correction("b-tens", "1"); stale.setJobId(UUID.randomUUID());
        assertEquals("STALE_ATTEMPT", assertThrows(ApiException.class,
                () -> service.confirmToken(student.getEmail(), submission.getSubmissionId(), stale)).getCode());
        assertThrows(ApiException.class, () -> service.confirmToken(student.getEmail(), submission.getSubmissionId(), correction("missing", "1")));
        assertThrows(ApiException.class, () -> service.confirmToken(student.getEmail(), submission.getSubmissionId(), correction("b-tens", "+")));
        assertEquals("12 + 22 = 34", results.findBySubmission_SubmissionId(submission.getSubmissionId()).orElseThrow()
                .getRecognizedExercise().get("expression"));
    }

    @Test void retryUsesNewestImageDispatchesAfterCommitAndOldCallbackCannotReplaceNewResult() {
        SubmissionImage oldImage = new SubmissionImage(); oldImage.setSubmission(submission);
        oldImage.setFilePath("submissions/old.jpg"); oldImage.setContentType("image/jpeg"); oldImage.setFileSize(3L);
        oldImage.setCreatedAt(Instant.now().minusSeconds(60)); images.save(oldImage);
        submission.setStatus("NEEDS_CONFIRMATION"); submissions.save(submission);
        service.retrySubmission(student.getEmail(), submission.getSubmissionId(),
                new MockMultipartFile("image", "new.jpg", "image/jpeg", new byte[]{1, 2, 3}), "CAMERA");
        assertEquals("submissions/new-image.jpg", images.findFirstBySubmission_SubmissionIdOrderByCreatedAtDesc(submission.getSubmissionId()).orElseThrow().getFilePath());
        assertEquals("SUPERSEDED", jobs.findById(job.getJobId()).orElseThrow().getStatus());
        verify(gateway, never()).analyze(any());
        callback.aiJobCompleted(job.getJobId(), "workflow-key", payload("stale result"));
        assertEquals("PROCESSING", submission.getStatus());
        assertTrue(results.findBySubmission_SubmissionId(submission.getSubmissionId()).isEmpty());
        AiJob latest = newJob();
        callback.aiJobCompleted(latest.getJobId(), "workflow-key", payload("new result"));
        callback.aiJobCompleted(job.getJobId(), "workflow-key", payload("stale result"));
        assertEquals("new result", results.findBySubmission_SubmissionId(submission.getSubmissionId()).orElseThrow().getRecognizedExercise().get("expression"));
    }

    @Test void latestAttemptUpsertsTheResultAndClearsPreviousFeedback() {
        callback.aiJobCompleted(job.getJobId(), "workflow-key", payload("first result"));
        submission.setStatus("PROCESSING"); submissions.save(submission);
        AiJob latest = newJob();
        AiCallbackRequest uncertain = new AiCallbackRequest(); uncertain.setStatus("NEEDS_CONFIRMATION");
        uncertain.setReasonCode("OCR_LOW_CONFIDENCE"); uncertain.setRecognizedTokens(tokens());
        callback.aiJobCompleted(latest.getJobId(), "workflow-key", uncertain);
        AnalysisResult result = results.findBySubmission_SubmissionId(submission.getSubmissionId()).orElseThrow();
        assertEquals(1, results.findAll().size());
        assertNull(result.getStudentFeedback()); assertNull(result.getGradeProposal());
        assertFalse(result.getRecognizedExercise().containsKey("expression"));
        assertEquals(latest.getJobId().toString(), result.getReviewReasons().get("jobId"));
    }

    @Test void teacherCannotViewOrApproveAStudentSelfSubmission() {
        Teacher teacher = new Teacher(); teacher.setEmail("unrelated-teacher@test.com"); teacher.setPasswordHash("test");
        teacher.setRole("TEACHER"); teacher.setDisplayName("Teacher"); teachers.save(teacher);
        submission.setStatus("FEEDBACK_READY"); submissions.save(submission);
        assertEquals("FORBIDDEN", assertThrows(ApiException.class,
                () -> service.getTeacherSubmission(teacher.getEmail(), submission.getSubmissionId())).getCode());
        assertThrows(ApiException.class, () -> service.approveSubmission(teacher.getEmail(), submission.getSubmissionId()));
    }
}

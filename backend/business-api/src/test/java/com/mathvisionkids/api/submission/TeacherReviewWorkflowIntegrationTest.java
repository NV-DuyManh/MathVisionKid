package com.mathvisionkids.api.submission;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.analysis.AiAnalysisGateway;
import com.mathvisionkids.api.analysis.AnalysisResult;
import com.mathvisionkids.api.analysis.AnalysisResultRepository;
import com.mathvisionkids.api.analysis.TeacherDecision;
import com.mathvisionkids.api.analysis.TeacherDecisionRepository;
import com.mathvisionkids.api.assignment.Assignment;
import com.mathvisionkids.api.assignment.AssignmentRepository;
import com.mathvisionkids.api.audit.AuditEvent;
import com.mathvisionkids.api.audit.AuditEventRepository;
import com.mathvisionkids.api.batch.Batch;
import com.mathvisionkids.api.batch.BatchImageMapping;
import com.mathvisionkids.api.batch.BatchRepository;
import com.mathvisionkids.api.batch.BatchService;
import com.mathvisionkids.api.classroom.Classroom;
import com.mathvisionkids.api.classroom.ClassroomRepository;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.storage.LocalFileObjectStorageService;
import com.mathvisionkids.api.storage.MinioObjectStorageService;
import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.transaction.TestTransaction;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionTemplate;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.InputStream;
import java.nio.file.Files;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import static org.hamcrest.Matchers.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(properties = "ai.callback.api-key=teacher-review-workflow-test")
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class TeacherReviewWorkflowIntegrationTest {

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;
    @Autowired PasswordEncoder passwordEncoder;
    @Autowired TeacherRepository teachers;
    @Autowired StudentRepository students;
    @Autowired ClassroomRepository classrooms;
    @Autowired AssignmentRepository assignments;
    @Autowired BatchRepository batches;
    @Autowired BatchService batchService;
    @Autowired SubmissionRepository submissions;
    @Autowired SubmissionImageRepository images;
    @Autowired AnalysisResultRepository analysisResults;
    @Autowired TeacherDecisionRepository teacherDecisions;
    @Autowired AuditEventRepository auditEvents;
    @Autowired SubmissionService submissionService;
    @Autowired com.mathvisionkids.api.analysis.AiJobRepository aiJobs;
    @Autowired TransactionTemplate transactions;

    @Autowired LocalFileObjectStorageService localFileStorage;
    @MockBean MinioObjectStorageService minioStorage;
    @MockBean AiAnalysisGateway aiGateway;

    private Teacher authorizedTeacher;
    private Teacher unauthorizedTeacher;
    private Student pupil;
    private Classroom classroom;
    private Assignment assignment;
    private Batch batch;
    private byte[] realImageBytes;

    private static final String AUTH_TEACHER_PASSWORD = "AuthorizedTeacherPass123!";
    private static final String UNAUTH_TEACHER_PASSWORD = "UnauthorizedTeacherPass123!";

    @BeforeEach
    void setUp() throws Exception {
        // Wire primary storage to delegate genuinely to production LocalFileObjectStorageService
        when(minioStorage.store(any(), anyString()))
                .thenAnswer(inv -> localFileStorage.store(inv.getArgument(0), inv.getArgument(1)));
        when(minioStorage.loadBytes(anyString()))
                .thenAnswer(inv -> localFileStorage.loadBytes(inv.getArgument(0)));

        // Load genuine readable math worksheet image (no fake 4096 dummy byte fallback)
        InputStream is = getClass().getResourceAsStream("/fixtures/worksheet-addition.jpg");
        if (is != null) {
            realImageBytes = is.readAllBytes();
            is.close();
        } else {
            File fixtureFile = new File("../../ai/runtime/tests/fixtures/synthetic_addition.jpg");
            if (!fixtureFile.exists()) {
                fixtureFile = new File("src/test/resources/fixtures/worksheet-addition.jpg");
            }
            if (fixtureFile.exists()) {
                realImageBytes = Files.readAllBytes(fixtureFile.toPath());
            } else {
                fail("Readable math worksheet fixture not found. Test must fail when image evidence is missing.");
            }
        }

        assertNotNull(realImageBytes, "realImageBytes must not be null");
        assertTrue(realImageBytes.length > 1000, "Image must have real content bytes");

        // Genuinely decode image via ImageIO to verify it is non-empty, non-corrupt, and readable
        BufferedImage decoded = ImageIO.read(new ByteArrayInputStream(realImageBytes));
        assertNotNull(decoded, "Worksheet image must be a valid decodable image");
        assertTrue(decoded.getWidth() >= 100 && decoded.getHeight() >= 100, "Image resolution must be sufficient for reading");

        authorizedTeacher = new Teacher();
        authorizedTeacher.setEmail("authorized-teacher@test.com");
        authorizedTeacher.setDisplayName("Cô Lan GVCN");
        authorizedTeacher.setRole("TEACHER");
        authorizedTeacher.setPasswordHash(passwordEncoder.encode(AUTH_TEACHER_PASSWORD));
        teachers.saveAndFlush(authorizedTeacher);

        unauthorizedTeacher = new Teacher();
        unauthorizedTeacher.setEmail("unauthorized-teacher@test.com");
        unauthorizedTeacher.setDisplayName("Thầy Tuấn Khác Lớp");
        unauthorizedTeacher.setRole("TEACHER");
        unauthorizedTeacher.setPasswordHash(passwordEncoder.encode(UNAUTH_TEACHER_PASSWORD));
        teachers.saveAndFlush(unauthorizedTeacher);

        pupil = new Student();
        pupil.setEmail("student-an@test.com");
        pupil.setDisplayName("An kiểm thử");
        pupil.setRole("STUDENT");
        pupil.setGradeLevel(3);
        pupil.setPasswordHash(passwordEncoder.encode("StudentPass123!"));
        students.saveAndFlush(pupil);

        classroom = new Classroom();
        classroom.setName("Lớp 3A");
        classroom.setGradeLevel(3);
        classroom.setTeacher(authorizedTeacher);
        classroom.getStudents().add(pupil);
        classrooms.saveAndFlush(classroom);

        assignment = new Assignment();
        assignment.setTitle("Bài kiểm tra phép cộng cột");
        assignment.setOperationType("VERTICAL_ADDITION");
        assignment.setMaxScore(100);
        assignment.setClassroom(classroom);
        assignment.setTeacher(authorizedTeacher);
        assignments.saveAndFlush(assignment);

        batch = new Batch();
        batch.setAssignment(assignment);
        batch.setTeacher(authorizedTeacher);
        batch.setStatus("CREATED");
        batches.saveAndFlush(batch);
    }

    private String obtainJwtToken(String email, String rawPassword) throws Exception {
        Map<String, String> creds = Map.of("email", email, "password", rawPassword);
        String json = mvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(creds)))
                .andExpect(status().isOk())
                .andReturn()
                .getResponse()
                .getContentAsString();
        Map<?, ?> res = mapper.readValue(json, Map.class);
        String token = (String) res.get("accessToken");
        if (token == null) {
            token = (String) res.get("token");
        }
        return token;
    }

    @Test
    @DisplayName("Offline integration: real JWT and local storage with a stubbed AI proposal")
    void teacherReviewWithRealStorageAndJwtAuthentication() throws Exception {
        // Authenticate with real JWT token through /api/v1/auth/login
        String teacherToken = obtainJwtToken(authorizedTeacher.getEmail(), AUTH_TEACHER_PASSWORD);
        assertNotNull(teacherToken, "JWT token must be issued on successful login");

        // 1. Upload readable image into batch via batchService using real LocalFileObjectStorageService
        MockMultipartFile file = new MockMultipartFile(
                "images",
                "worksheet-addition.jpg",
                "image/jpeg",
                realImageBytes
        );
        BatchImageMapping mapping = new BatchImageMapping();
        mapping.setFileIndex(0);
        mapping.setStudentId(pupil.getId());

        batchService.uploadImages(
                authorizedTeacher.getEmail(),
                batch.getBatchId(),
                List.of(file),
                List.of(mapping)
        );

        // Verify submission created in database
        List<Submission> createdSubmissions = submissions.findByBatch_BatchId(batch.getBatchId());
        assertEquals(1, createdSubmissions.size());
        Submission submission = createdSubmissions.get(0);
        assertEquals(pupil.getId(), submission.getStudent().getId());
        assertEquals(assignment.getAssignmentId(), submission.getAssignment().getAssignmentId());

        // Verify SubmissionImage record persisted in database with real file path in storage
        SubmissionImage storedImage = images.findFirstBySubmission_SubmissionIdOrderByCreatedAtDesc(submission.getSubmissionId()).orElseThrow();
        assertEquals("image/jpeg", storedImage.getContentType());
        assertTrue(storedImage.getFileSize() > 0);
        assertNotNull(storedImage.getFilePath());

        // Verify the real storage service holds the genuine image bytes on disk
        byte[] loadedFromDisk = localFileStorage.loadBytes(storedImage.getFilePath());
        assertArrayEquals(realImageBytes, loadedFromDisk, "Real disk storage must match uploaded image bytes exactly");

        // Live inference is exercised separately by scripts/test/live_teacher_review.mjs.
        // This offline test supplies a proposal to isolate decision persistence.
        AnalysisResult analysisResult = new AnalysisResult();
        analysisResult.setSubmission(submission);
        analysisResult.setStatus("PROPOSED_GRADE");
        analysisResult.setGradeProposal(Map.of(
                "suggestedScore", 85,
                "maxScore", 100,
                "isOfficial", false
        ));
        analysisResult.setRecognizedExercise(Map.of("expression", "35 + 47 = 82"));
        analysisResult.setReviewReasons(Map.of("recognition", 0.95, "structure", 0.92, "diagnosis", 0.90));
        analysisResult.setValidation(Map.of("isValid", true, "diagnosisState", "VALID"));
        analysisResults.saveAndFlush(analysisResult);

        submission.setStatus("PROPOSED_GRADE");
        submissions.saveAndFlush(submission);

        String subUrl = "/api/v1/teacher/submissions/" + submission.getSubmissionId();
        String imgUrl = subUrl + "/image";

        // 3. Authorized teacher views submission metadata with real Bearer JWT
        mvc.perform(get(subUrl).header(HttpHeaders.AUTHORIZATION, "Bearer " + teacherToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.submissionId").value(submission.getSubmissionId().toString()))
                .andExpect(jsonPath("$.studentName").value("An kiểm thử"))
                .andExpect(jsonPath("$.maxScore").value(100))
                .andExpect(jsonPath("$.suggestedScore").value(85))
                .andExpect(jsonPath("$.imageUrl").value(imgUrl))
                .andExpect(jsonPath("$.recognizedText").value("35 + 47 = 82"));

        // 4. Authorized teacher loads full resolution image from real storage endpoint
        mvc.perform(get(imgUrl).header(HttpHeaders.AUTHORIZATION, "Bearer " + teacherToken))
                .andExpect(status().isOk())
                .andExpect(content().contentType("image/jpeg"))
                .andExpect(content().bytes(realImageBytes))
                .andExpect(header().string(HttpHeaders.CACHE_CONTROL, "no-store"));

        // 5. Authorized teacher overrides the score with a professional pedagogical note
        Map<String, Object> overrideRequest = Map.of(
                "score", 95,
                "reason", "Học sinh trình bày đặt tính thẳng cột đúng quy tắc và tính toán chính xác."
        );

        mvc.perform(post(subUrl + "/override")
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + teacherToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(overrideRequest)))
                .andExpect(status().isOk());

        // 6. Reload from backend and verify persistence
        mvc.perform(get(subUrl).header(HttpHeaders.AUTHORIZATION, "Bearer " + teacherToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("TEACHER_OVERRIDDEN"))
                .andExpect(jsonPath("$.teacherScore").value(95))
                .andExpect(jsonPath("$.teacherReason").value("Học sinh trình bày đặt tính thẳng cột đúng quy tắc và tính toán chính xác."));

        // Verify DB record
        TeacherDecision decision = teacherDecisions.findBySubmission_SubmissionId(submission.getSubmissionId()).orElseThrow();
        assertEquals(95, decision.getFinalScore());
        assertEquals("Học sinh trình bày đặt tính thẳng cột đúng quy tắc và tính toán chính xác.", decision.getReason());
        assertEquals(authorizedTeacher.getId(), decision.getTeacher().getId());
    }

    @Test
    @DisplayName("RBAC check: unauthorized teacher cannot view or grade submission image")
    void unauthorizedTeacherIsDeniedAccessToSubmissionImageAndDecision() throws Exception {
        // Authenticate foreign teacher to obtain real JWT token
        String unauthorizedToken = obtainJwtToken(unauthorizedTeacher.getEmail(), UNAUTH_TEACHER_PASSWORD);

        Submission submission = new Submission();
        submission.setBatch(batch);
        submission.setAssignment(assignment);
        submission.setStudent(pupil);
        submission.setStatus("REVIEW_REQUIRED");
        submissions.saveAndFlush(submission);

        SubmissionImage image = new SubmissionImage();
        image.setSubmission(submission);
        image.setFilePath("submissions/real-worksheet.jpg");
        image.setContentType("image/jpeg");
        image.setFileSize((long) realImageBytes.length);
        images.saveAndFlush(image);

        String subUrl = "/api/v1/teacher/submissions/" + submission.getSubmissionId();
        String imgUrl = subUrl + "/image";

        // Unauthorized teacher from another class cannot view metadata (HTTP 403)
        mvc.perform(get(subUrl).header(HttpHeaders.AUTHORIZATION, "Bearer " + unauthorizedToken))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.error.code").value("FORBIDDEN"));

        // Unauthorized teacher cannot fetch private image bytes (HTTP 403)
        mvc.perform(get(imgUrl).header(HttpHeaders.AUTHORIZATION, "Bearer " + unauthorizedToken))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.error.code").value("FORBIDDEN"));

        // Unauthorized teacher cannot override or approve (HTTP 403)
        mvc.perform(post(subUrl + "/approve").header(HttpHeaders.AUTHORIZATION, "Bearer " + unauthorizedToken))
                .andExpect(status().isForbidden());

        mvc.perform(post(subUrl + "/override")
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + unauthorizedToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("score", 100, "reason", "Hack"))))
                .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("Approval flow: authorized teacher approves proposed score directly")
    void authorizedTeacherApprovesProposedGradeSuccessfully() throws Exception {
        String authorizedToken = obtainJwtToken(authorizedTeacher.getEmail(), AUTH_TEACHER_PASSWORD);

        Submission submission = new Submission();
        submission.setBatch(batch);
        submission.setAssignment(assignment);
        submission.setStudent(pupil);
        submission.setStatus("PROPOSED_GRADE");
        submissions.saveAndFlush(submission);

        AnalysisResult result = new AnalysisResult();
        result.setSubmission(submission);
        result.setStatus("PROPOSED_GRADE");
        result.setGradeProposal(Map.of("suggestedScore", 90, "maxScore", 100, "isOfficial", false));
        analysisResults.saveAndFlush(result);

        String subUrl = "/api/v1/teacher/submissions/" + submission.getSubmissionId();

        mvc.perform(post(subUrl + "/approve")
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + authorizedToken))
                .andExpect(status().isOk());

        // Reload submission and verify status is TEACHER_APPROVED
        mvc.perform(get(subUrl).header(HttpHeaders.AUTHORIZATION, "Bearer " + authorizedToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("TEACHER_APPROVED"))
                .andExpect(jsonPath("$.teacherScore").value(90));

        TeacherDecision decision = teacherDecisions.findBySubmission_SubmissionId(submission.getSubmissionId()).orElseThrow();
        assertEquals(90, decision.getFinalScore());
        assertEquals("APPROVED", decision.getType());
    }

    @Test
    void finalizedGradeCannotBeApprovedOrOverriddenAgain() throws Exception {
        String token = obtainJwtToken(authorizedTeacher.getEmail(), AUTH_TEACHER_PASSWORD);
        Submission submission = saveSubmission("PROPOSED_GRADE");
        AnalysisResult result = new AnalysisResult();
        result.setSubmission(submission);
        result.setStatus("PROPOSED_GRADE");
        result.setGradeProposal(Map.of("suggestedScore", 73, "maxScore", 100));
        analysisResults.saveAndFlush(result);
        String submissionUrl = "/api/v1/teacher/submissions/" + submission.getSubmissionId();

        mvc.perform(post(submissionUrl + "/approve").header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isOk());

        TeacherDecision originalDecision = teacherDecisions.findBySubmission_SubmissionId(submission.getSubmissionId()).orElseThrow();
        AuditEvent originalAuditEvent = auditEvents.findBySubmission_SubmissionIdOrderByCreatedAtDesc(submission.getSubmissionId()).getFirst();
        assertEquals(73, originalDecision.getFinalScore());
        assertEquals("APPROVED", originalDecision.getType());
        assertEquals("TEACHER_APPROVED", originalAuditEvent.getEventType());

        mvc.perform(post(submissionUrl + "/approve").header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.code").value("INVALID_STATE"));
        mvc.perform(post(submissionUrl + "/override")
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("score", 10, "reason", "Second decision"))))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.code").value("INVALID_STATE"));

        mvc.perform(get(submissionUrl).header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("TEACHER_APPROVED"))
                .andExpect(jsonPath("$.teacherScore").value(73));
        TeacherDecision unchangedDecision = teacherDecisions.findBySubmission_SubmissionId(submission.getSubmissionId()).orElseThrow();
        List<AuditEvent> unchangedEvents = auditEvents.findBySubmission_SubmissionIdOrderByCreatedAtDesc(submission.getSubmissionId());
        assertEquals(originalDecision.getDecisionId(), unchangedDecision.getDecisionId());
        assertEquals(originalDecision.getFinalScore(), unchangedDecision.getFinalScore());
        assertEquals(originalDecision.getType(), unchangedDecision.getType());
        assertEquals(List.of(originalAuditEvent.getAuditEventId()), unchangedEvents.stream()
                .map(AuditEvent::getAuditEventId).toList());
        assertEquals(originalAuditEvent.getEventType(), unchangedEvents.getFirst().getEventType());
        assertEquals(originalAuditEvent.getMetadata(), unchangedEvents.getFirst().getMetadata());
    }

    @Test
    void teacherCanManuallyGradeAnUncertainSubmissionWithoutAProposal() throws Exception {
        String token = obtainJwtToken(authorizedTeacher.getEmail(), AUTH_TEACHER_PASSWORD);
        Submission submission = saveSubmission("NEEDS_CONFIRMATION");
        String submissionUrl = "/api/v1/teacher/submissions/" + submission.getSubmissionId();
        String batchUrl = "/api/v1/teacher/batches/" + batch.getBatchId();
        String reason = "Ảnh đủ rõ để đối chiếu. Kết quả phép cộng chưa đúng.";

        mvc.perform(post(submissionUrl + "/approve").header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isBadRequest());
        mvc.perform(post(submissionUrl + "/override")
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("score", 0, "reason", reason, "imageLegible", true))))
                .andExpect(status().isOk());
        mvc.perform(get(submissionUrl).header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("TEACHER_OVERRIDDEN"))
                .andExpect(jsonPath("$.teacherScore").value(0))
                .andExpect(jsonPath("$.teacherReason").value(reason));
        mvc.perform(get(batchUrl).header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.pendingReviewCount").value(0))
                .andExpect(jsonPath("$.finalizedCount").value(1));
        List<AuditEvent> events = auditEvents.findBySubmission_SubmissionIdOrderByCreatedAtDesc(submission.getSubmissionId());
        assertEquals(List.of("TEACHER_OVERRIDDEN"), events.stream().map(AuditEvent::getEventType).toList());
        assertEquals(true, events.get(0).getMetadata().get("imageLegible"));
    }

    @Test
    void teacherMustAffirmEvidenceIsLegibleBeforeGradingAnUncertainSubmission() throws Exception {
        String token = obtainJwtToken(authorizedTeacher.getEmail(), AUTH_TEACHER_PASSWORD);
        Submission submission = saveSubmission("NEEDS_CONFIRMATION");
        String submissionUrl = "/api/v1/teacher/submissions/" + submission.getSubmissionId();

        for (Map<String, Object> body : List.<Map<String, Object>>of(
                Map.of("score", 0, "reason", "Đã đối chiếu bài làm"),
                Map.of("score", 0, "reason", "Đã đối chiếu bài làm", "imageLegible", false),
                Map.of("score", 0, "reason", "Đã đối chiếu bài làm", "imageLegible", "true"))) {
            mvc.perform(post(submissionUrl + "/override")
                            .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(mapper.writeValueAsString(body)))
                    .andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.error.code").value("VALIDATION_ERROR"));
        }
        mvc.perform(get(submissionUrl).header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("NEEDS_CONFIRMATION"))
                .andExpect(jsonPath("$.teacherScore").doesNotExist());
        assertTrue(auditEvents.findBySubmission_SubmissionIdOrderByCreatedAtDesc(submission.getSubmissionId()).isEmpty());
    }

    @Test
    void submissionRequiringRetakeRemainsInReviewWithoutAnOfficialGrade() throws Exception {
        String token = obtainJwtToken(authorizedTeacher.getEmail(), AUTH_TEACHER_PASSWORD);
        Submission submission = saveSubmission("NEEDS_RETAKE");
        String submissionUrl = "/api/v1/teacher/submissions/" + submission.getSubmissionId();
        String reviewUrl = "/api/v1/teacher/batches/" + batch.getBatchId() + "/review";

        mvc.perform(post(submissionUrl + "/override")
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("score", 50, "reason", "Ảnh cần chụp lại"))))
                .andExpect(status().isBadRequest());
        mvc.perform(get(reviewUrl).header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0]").value(submission.getSubmissionId().toString()));
        assertTrue(teacherDecisions.findBySubmission_SubmissionId(submission.getSubmissionId()).isEmpty());
    }

    @Test
    void batchReviewSummaryReturnsOnlyCurrentPendingCardFieldsToTheOwningTeacher() throws Exception {
        String owner = obtainJwtToken(authorizedTeacher.getEmail(), AUTH_TEACHER_PASSWORD);
        String other = obtainJwtToken(unauthorizedTeacher.getEmail(), UNAUTH_TEACHER_PASSWORD);
        var first = java.time.Instant.parse("2026-11-11T00:00:00Z");
        Submission current = saveSubmission("PROPOSED_GRADE", first);
        Submission stale = saveSubmission("NEEDS_RETAKE", first.plusSeconds(1));
        saveSubmission("TEACHER_APPROVED");

        var originalJob = new com.mathvisionkids.api.analysis.AiJob();
        originalJob.setSubmission(stale);
        originalJob.setStatus("COMPLETED");
        originalJob.setSubmittedAt(first.plusSeconds(2));
        aiJobs.saveAndFlush(originalJob);

        for (Submission submission : List.of(current, stale)) {
            AnalysisResult result = new AnalysisResult();
            result.setSubmission(submission);
            result.setStatus(submission.getStatus());
            result.setRecognizedExercise(Map.of("expression", "private expression"));
            result.setGradeProposal(Map.of("suggestedScore", 7, "maxScore", 10, "details", "private"));
            result.setReviewReasons(Map.of("recognition", 0.9, "diagnosis", 0.8, "structure", 0.7,
                    "jobId", originalJob.getJobId().toString()));
            result.setEvidence(Map.of("rule", "PLACE_VALUE", "position", "Tens",
                    "items", List.of(Map.of("description", "Check the tens column", "source", "private"),
                            Map.of("description", "Second detail"))));
            analysisResults.saveAndFlush(result);
        }
        var retry = new com.mathvisionkids.api.analysis.AiJob();
        retry.setSubmission(stale);
        retry.setStatus("COMPLETED");
        retry.setSubmittedAt(first.plusSeconds(3));
        aiJobs.saveAndFlush(retry);

        String url = "/api/v1/teacher/batches/" + batch.getBatchId() + "/review-summary";
        mvc.perform(get("/api/v1/teacher/batches/" + batch.getBatchId() + "/review")
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + owner))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", contains(current.getSubmissionId().toString(), stale.getSubmissionId().toString())));
        mvc.perform(get(url).header(HttpHeaders.AUTHORIZATION, "Bearer " + other))
                .andExpect(status().isForbidden());
        mvc.perform(get(url).header(HttpHeaders.AUTHORIZATION, "Bearer " + owner))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)))
                .andExpect(jsonPath("$[0].submissionId").value(current.getSubmissionId().toString()))
                .andExpect(jsonPath("$[0].status").value("PROPOSED_GRADE"))
                .andExpect(jsonPath("$[0].studentName").value(pupil.getDisplayName()))
                .andExpect(jsonPath("$[0].maxScore").value(100))
                .andExpect(jsonPath("$[0].gradeProposal.suggestedScore").value(7))
                .andExpect(jsonPath("$[0].gradeProposal.maxScore").value(10))
                .andExpect(jsonPath("$[0].gradeProposal.details").doesNotExist())
                .andExpect(jsonPath("$[0].confidenceBundle.recognition").value(0.9))
                .andExpect(jsonPath("$[0].confidenceBundle.diagnosis").value(0.8))
                .andExpect(jsonPath("$[0].confidenceBundle.structure").doesNotExist())
                .andExpect(jsonPath("$[0].evidence.rule").value("PLACE_VALUE"))
                .andExpect(jsonPath("$[0].evidence.position").value("Tens"))
                .andExpect(jsonPath("$[0].evidence.items", hasSize(1)))
                .andExpect(jsonPath("$[0].evidence.items[0].description").value("Check the tens column"))
                .andExpect(jsonPath("$[0].evidence.items[0].source").doesNotExist())
                .andExpect(jsonPath("$[0].recognizedText").doesNotExist())
                .andExpect(jsonPath("$[0].studentId").doesNotExist())
                .andExpect(jsonPath("$[0].imageUrl").doesNotExist())
                .andExpect(jsonPath("$[1].submissionId").value(stale.getSubmissionId().toString()))
                .andExpect(jsonPath("$[1].gradeProposal").doesNotExist())
                .andExpect(jsonPath("$[1].confidenceBundle").doesNotExist())
                .andExpect(jsonPath("$[1].evidence").doesNotExist());
    }

    @Test
    void changingClassroomTeacherRemovesHistoricalWorkFromTeacherWorkspace() throws Exception {
        String formerTeacherToken = obtainJwtToken(authorizedTeacher.getEmail(), AUTH_TEACHER_PASSWORD);
        String currentTeacherToken = obtainJwtToken(unauthorizedTeacher.getEmail(), UNAUTH_TEACHER_PASSWORD);
        Submission submission = saveSubmission("REVIEW_REQUIRED");
        String submissionUrl = "/api/v1/teacher/submissions/" + submission.getSubmissionId();
        String batchUrl = "/api/v1/teacher/batches/" + batch.getBatchId();
        String assignmentUrl = "/api/v1/teacher/assignments/" + assignment.getAssignmentId();

        classroom.setTeacher(unauthorizedTeacher);
        classrooms.saveAndFlush(classroom);

        mvc.perform(get("/api/v1/teacher/batches").header(HttpHeaders.AUTHORIZATION, "Bearer " + formerTeacherToken))
                .andExpect(status().isOk()).andExpect(jsonPath("$").isEmpty());
        mvc.perform(get("/api/v1/teacher/assignments").header(HttpHeaders.AUTHORIZATION, "Bearer " + formerTeacherToken))
                .andExpect(status().isOk()).andExpect(jsonPath("$").isEmpty());
        mvc.perform(get("/api/v1/teacher/dashboard").header(HttpHeaders.AUTHORIZATION, "Bearer " + formerTeacherToken))
                .andExpect(status().isOk()).andExpect(jsonPath("$.recentBatches").isEmpty());

        for (String token : List.of(formerTeacherToken, currentTeacherToken)) {
            for (String url : List.of(assignmentUrl, batchUrl, batchUrl + "/review", batchUrl + "/review-summary",
                    submissionUrl, submissionUrl + "/image")) {
                mvc.perform(get(url).header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                        .andExpect(status().isForbidden());
            }
            mvc.perform(post(submissionUrl + "/approve").header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                    .andExpect(status().isForbidden());
            mvc.perform(post(submissionUrl + "/override")
                            .header(HttpHeaders.AUTHORIZATION, "Bearer " + token)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(mapper.writeValueAsString(Map.of("score", 50, "reason", "Kiểm tra quyền chấm"))))
                    .andExpect(status().isForbidden());
        }
        assertTrue(teacherDecisions.findBySubmission_SubmissionId(submission.getSubmissionId()).isEmpty());
    }

    @Test
    void concurrentManualDecisionsRecordOneGradeAndAuditEvent() throws Exception {
        UUID submissionId = saveSubmission("NEEDS_CONFIRMATION").getSubmissionId();
        String teacherEmail = authorizedTeacher.getEmail();
        TestTransaction.flagForCommit();
        TestTransaction.end();

        var start = new CountDownLatch(1);
        try (var executor = Executors.newFixedThreadPool(2)) {
            var first = executor.submit(() -> tryGrade(start, teacherEmail, submissionId, 0));
            var second = executor.submit(() -> tryGrade(start, teacherEmail, submissionId, 75));
            start.countDown();
            String firstResult = first.get(10, TimeUnit.SECONDS);
            String secondResult = second.get(10, TimeUnit.SECONDS);

            assertEquals(List.of("INVALID_STATE", "SAVED"), List.of(firstResult, secondResult).stream().sorted().toList());
            int winningScore = "SAVED".equals(firstResult) ? 0 : 75;
            assertEquals(winningScore, teacherDecisions.findBySubmission_SubmissionId(submissionId).orElseThrow().getFinalScore());
            assertEquals(List.of("TEACHER_OVERRIDDEN"), auditEvents
                    .findBySubmission_SubmissionIdOrderByCreatedAtDesc(submissionId).stream()
                    .map(AuditEvent::getEventType).toList());
        } finally {
            transactions.executeWithoutResult(status -> {
                auditEvents.deleteAll(auditEvents.findBySubmission_SubmissionIdOrderByCreatedAtDesc(submissionId));
                teacherDecisions.findBySubmission_SubmissionId(submissionId).ifPresent(teacherDecisions::delete);
                submissions.deleteById(submissionId);
                batches.deleteById(batch.getBatchId());
                assignments.deleteById(assignment.getAssignmentId());
                classrooms.deleteById(classroom.getClassId());
                students.deleteById(pupil.getId());
                teachers.deleteById(authorizedTeacher.getId());
                teachers.deleteById(unauthorizedTeacher.getId());
            });
        }
    }

    @Test
    void teacherRetakeReplacesTheCurrentImageAndIgnoresLateCallbacks() throws Exception {
        Submission submission = saveSubmission("NEEDS_RETAKE");
        UUID id = submission.getSubmissionId();
        SubmissionImage original = new SubmissionImage();
        original.setSubmission(submission);
        original.setContentType("image/jpeg");
        original.setFileSize((long) realImageBytes.length);
        original.setFilePath("original-image-reference");
        original.setCreatedAt(java.time.Instant.now().minusSeconds(60));
        images.saveAndFlush(original);
        var job = new com.mathvisionkids.api.analysis.AiJob();
        job.setSubmission(submission);
        job.setStatus("QUEUED");
        UUID oldJob = aiJobs.saveAndFlush(job).getJobId();

        String url = "/api/v1/teacher/submissions/" + id;
        String token = obtainJwtToken(authorizedTeacher.getEmail(), AUTH_TEACHER_PASSWORD);
        String outsider = obtainJwtToken(unauthorizedTeacher.getEmail(), UNAUTH_TEACHER_PASSWORD);
        String student = obtainJwtToken(pupil.getEmail(), "StudentPass123!");
        var replacement = new MockMultipartFile("image", "redacted.jpg", "image/jpeg", realImageBytes);
        mvc.perform(multipart(url + "/retake").file(replacement)
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + outsider))
                .andExpect(status().isForbidden());
        mvc.perform(multipart("/api/v1/student/submissions/" + id + "/retry").file(replacement)
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + student))
                .andExpect(status().isForbidden());
        mvc.perform(multipart(url + "/retake")
                        .file(new MockMultipartFile("image", "invalid.jpg", "image/jpeg", new byte[]{1, 2, 3}))
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isBadRequest());
        mvc.perform(multipart(url + "/retake").file(replacement)
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isAccepted()).andExpect(content().string(""));
        mvc.perform(multipart(url + "/retake").file(replacement)
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isConflict());
        mvc.perform(post("/internal/v1/ai/jobs/" + oldJob + "/callback")
                        .header("X-Internal-API-Key", "teacher-review-workflow-test")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"status\":\"PROPOSED_GRADE\"}"))
                .andExpect(status().isOk());
        assertEquals("SUPERSEDED", aiJobs.findById(oldJob).orElseThrow().getStatus());
        assertTrue(analysisResults.findBySubmission_SubmissionId(id).isEmpty());
        UUID version = images.findFirstBySubmission_SubmissionIdOrderByCreatedAtDesc(id).orElseThrow().getImageId();
        assertNotEquals(original.getImageId(), version);
        assertTrue(images.existsById(original.getImageId()));
        assertEquals(List.of("TEACHER_RETAKE_UPLOADED"), auditEvents
                .findBySubmission_SubmissionIdOrderByCreatedAtDesc(id).stream().map(AuditEvent::getEventType).toList());
        mvc.perform(get(url).header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.submissionId").value(id.toString()))
                .andExpect(jsonPath("$.imageVersion").value(version.toString()))
                .andExpect(jsonPath("$.status").value("PROCESSING"));
        mvc.perform(get(url + "/image").header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isOk()).andExpect(content().bytes(realImageBytes));
    }

    @Test
    void teacherRetakeRollbackRemovesReplacementAndSkipsDispatch() throws Exception {
        doAnswer(invocation -> {
            localFileStorage.delete(invocation.getArgument(0));
            return null;
        }).when(minioStorage).delete(anyString());
        UUID id = saveSubmission("NEEDS_RETAKE").getSubmissionId();
        submissionService.retakeTeacherSubmission(authorizedTeacher.getEmail(), id,
                new MockMultipartFile("image", "redacted.jpg", "image/jpeg", realImageBytes));
        String path = images.findFirstBySubmission_SubmissionIdOrderByCreatedAtDesc(id).orElseThrow().getFilePath();
        assertArrayEquals(realImageBytes, localFileStorage.loadBytes(path));

        TestTransaction.flagForRollback();
        TestTransaction.end();

        assertThrows(java.io.IOException.class, () -> localFileStorage.loadBytes(path));
        assertTrue(images.findFirstBySubmission_SubmissionIdOrderByCreatedAtDesc(id).isEmpty());
        verifyNoInteractions(aiGateway);
    }

    @Test
    void teacherRetriesTechnicalFailureUsingTheSameImage() throws Exception {
        Submission submission = saveSubmission("REVIEW_REQUIRED");
        UUID id = submission.getSubmissionId();
        SubmissionImage image = new SubmissionImage();
        image.setSubmission(submission);
        image.setContentType("image/jpeg");
        image.setFileSize((long) realImageBytes.length);
        image.setFilePath("original-image-reference");
        UUID imageId = images.saveAndFlush(image).getImageId();
        var job = new com.mathvisionkids.api.analysis.AiJob();
        job.setSubmission(submission);
        job.setStatus("FAILED");
        UUID failedJobId = aiJobs.saveAndFlush(job).getJobId();

        String url = "/api/v1/teacher/submissions/" + id;
        String token = obtainJwtToken(authorizedTeacher.getEmail(), AUTH_TEACHER_PASSWORD);
        String outsider = obtainJwtToken(unauthorizedTeacher.getEmail(), UNAUTH_TEACHER_PASSWORD);
        mvc.perform(get(url).header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isOk()).andExpect(jsonPath("$.canRetryProcessing").value(true));
        mvc.perform(post(url + "/retry-processing").header(HttpHeaders.AUTHORIZATION, "Bearer " + outsider))
                .andExpect(status().isForbidden());
        mvc.perform(post(url + "/retry-processing").header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isAccepted()).andExpect(content().string(""));
        mvc.perform(post(url + "/retry-processing").header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isConflict());
        assertEquals("SUPERSEDED", aiJobs.findById(failedJobId).orElseThrow().getStatus());
        assertEquals(List.of("TEACHER_PROCESSING_RETRY_REQUESTED"), auditEvents
                .findBySubmission_SubmissionIdOrderByCreatedAtDesc(id).stream().map(AuditEvent::getEventType).toList());
        mvc.perform(get(url).header(HttpHeaders.AUTHORIZATION, "Bearer " + token))
                .andExpect(status().isOk()).andExpect(jsonPath("$.status").value("PROCESSING"))
                .andExpect(jsonPath("$.canRetryProcessing").value(false))
                .andExpect(jsonPath("$.imageVersion").value(imageId.toString()));
    }

    @Test
    void interruptedTeacherDispatchBecomesRetryableWithoutDispatchingAgain() {
        UUID id = saveSubmission("PROCESSING").getSubmissionId();
        var attempt = new AuditEvent();
        attempt.setSubmission(submissions.findById(id).orElseThrow());
        attempt.setEventType("TEACHER_PROCESSING_RETRY_REQUESTED");
        attempt.setCreatedAt(java.time.Instant.now().minusSeconds(300));
        auditEvents.save(attempt);
        var pending = new com.mathvisionkids.api.analysis.AiJob();
        pending.setSubmission(attempt.getSubmission());
        pending.setStatus("PENDING");
        pending.setSubmittedAt(java.time.Instant.now().minusSeconds(290));
        UUID jobId = aiJobs.saveAndFlush(pending).getJobId();

        var cutoff = java.time.Instant.now().minusSeconds(120);
        submissionService.recoverInterruptedTeacherDispatches(cutoff);
        submissionService.recoverInterruptedTeacherDispatches(cutoff);

        assertEquals("FAILED", submissions.findById(id).orElseThrow().getStatus());
        assertEquals("SUPERSEDED", aiJobs.findById(jobId).orElseThrow().getStatus());
        assertEquals(1L, auditEvents.findBySubmission_SubmissionIdOrderByCreatedAtDesc(id).stream()
                .filter(event -> "TEACHER_DISPATCH_INTERRUPTED".equals(event.getEventType())).count());
        verifyNoInteractions(aiGateway);
    }

    private Submission saveSubmission(String status) {
        return saveSubmission(status, java.time.Instant.now());
    }

    private Submission saveSubmission(String status, java.time.Instant createdAt) {
        Submission submission = new Submission();
        submission.setBatch(batch);
        submission.setAssignment(assignment);
        submission.setStudent(pupil);
        submission.setStatus(status);
        submission.setCreatedAt(createdAt);
        return submissions.saveAndFlush(submission);
    }

    private String tryGrade(CountDownLatch start, String email, UUID submissionId, int score) throws InterruptedException {
        assertTrue(start.await(5, TimeUnit.SECONDS));
        try {
            submissionService.overrideSubmission(email, submissionId,
                    Map.of("score", score, "reason", "Đã đối chiếu bài làm", "imageLegible", true));
            return "SAVED";
        } catch (ApiException error) {
            return error.getCode();
        }
    }
}

package com.mathvisionkids.api.submission;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.analysis.AiAnalysisGateway;
import com.mathvisionkids.api.analysis.AnalysisResult;
import com.mathvisionkids.api.analysis.AnalysisResultRepository;
import com.mathvisionkids.api.analysis.TeacherDecision;
import com.mathvisionkids.api.analysis.TeacherDecisionRepository;
import com.mathvisionkids.api.assignment.Assignment;
import com.mathvisionkids.api.assignment.AssignmentRepository;
import com.mathvisionkids.api.batch.Batch;
import com.mathvisionkids.api.batch.BatchImageMapping;
import com.mathvisionkids.api.batch.BatchRepository;
import com.mathvisionkids.api.batch.BatchService;
import com.mathvisionkids.api.classroom.Classroom;
import com.mathvisionkids.api.classroom.ClassroomRepository;
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
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.InputStream;
import java.nio.file.Files;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.hamcrest.Matchers.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
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
}

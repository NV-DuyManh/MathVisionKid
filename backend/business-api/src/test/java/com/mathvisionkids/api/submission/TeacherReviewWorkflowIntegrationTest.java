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
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
import java.nio.file.Files;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.hamcrest.Matchers.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
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

    @MockBean ObjectStorageService storage;
    @MockBean AiAnalysisGateway aiGateway;

    private Teacher authorizedTeacher;
    private Teacher unauthorizedTeacher;
    private Student pupil;
    private Classroom classroom;
    private Assignment assignment;
    private Batch batch;
    private byte[] realImageBytes;

    @BeforeEach
    void setUp() throws Exception {
        // Load real readable math worksheet image (640x640 JPEG)
        File fixtureFile = new File("../../ai/runtime/tests/fixtures/synthetic_addition.jpg");
        if (fixtureFile.exists()) {
            realImageBytes = Files.readAllBytes(fixtureFile.toPath());
        } else {
            // Fallback to high-res synthetic header if path differs in CI runner
            realImageBytes = new byte[4096];
            realImageBytes[0] = (byte) 0xFF;
            realImageBytes[1] = (byte) 0xD8;
            realImageBytes[2] = (byte) 0xFF;
            realImageBytes[3] = (byte) 0xE0;
        }

        authorizedTeacher = new Teacher();
        authorizedTeacher.setEmail("authorized-teacher@test.com");
        authorizedTeacher.setDisplayName("Cô Lan GVCN");
        authorizedTeacher.setRole("TEACHER");
        authorizedTeacher.setPasswordHash("hash");
        teachers.save(authorizedTeacher);

        unauthorizedTeacher = new Teacher();
        unauthorizedTeacher.setEmail("unauthorized-teacher@test.com");
        unauthorizedTeacher.setDisplayName("Thầy Tuấn Khác Lớp");
        unauthorizedTeacher.setRole("TEACHER");
        unauthorizedTeacher.setPasswordHash("hash");
        teachers.save(unauthorizedTeacher);

        pupil = new Student();
        pupil.setEmail("student-an@test.com");
        pupil.setDisplayName("An kiểm thử");
        pupil.setRole("STUDENT");
        pupil.setGradeLevel(3);
        pupil.setPasswordHash("hash");
        students.save(pupil);

        classroom = new Classroom();
        classroom.setName("Lớp 3A");
        classroom.setGradeLevel(3);
        classroom.setTeacher(authorizedTeacher);
        classroom.getStudents().add(pupil);
        classrooms.save(classroom);

        assignment = new Assignment();
        assignment.setTitle("Bài kiểm tra phép cộng cột");
        assignment.setOperationType("VERTICAL_ADDITION");
        assignment.setMaxScore(100);
        assignment.setClassroom(classroom);
        assignment.setTeacher(authorizedTeacher);
        assignments.save(assignment);

        batch = new Batch();
        batch.setAssignment(assignment);
        batch.setTeacher(authorizedTeacher);
        batch.setStatus("CREATED");
        batches.save(batch);

        when(storage.store(any(), anyString())).thenReturn("submissions/real-worksheet.jpg");
        when(storage.loadBytes("submissions/real-worksheet.jpg")).thenReturn(realImageBytes);
    }

    @Test
    @DisplayName("Full real flow: upload real image -> AI grade proposal -> authorized review -> reload confirms backend persistence")
    void fullRealReviewWorkflowWithReadableWorksheetImage() throws Exception {
        // 1. Upload readable image into batch
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

        // Verify SubmissionImage record
        SubmissionImage storedImage = images.findFirstBySubmission_SubmissionIdOrderByCreatedAtDesc(submission.getSubmissionId()).orElseThrow();
        assertEquals("image/jpeg", storedImage.getContentType());
        assertTrue(storedImage.getFileSize() > 0);

        // 2. Simulate AI Analysis result with proposed grade
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

        // 3. Authorized teacher views submission metadata
        mvc.perform(get(subUrl).with(user(authorizedTeacher.getEmail()).roles("TEACHER")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.submissionId").value(submission.getSubmissionId().toString()))
                .andExpect(jsonPath("$.studentName").value("An kiểm thử"))
                .andExpect(jsonPath("$.maxScore").value(100))
                .andExpect(jsonPath("$.suggestedScore").value(85))
                .andExpect(jsonPath("$.imageUrl").value(imgUrl))
                .andExpect(jsonPath("$.recognizedText").value("35 + 47 = 82"));

        // 4. Authorized teacher loads full resolution image
        mvc.perform(get(imgUrl).with(user(authorizedTeacher.getEmail()).roles("TEACHER")))
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
                        .with(user(authorizedTeacher.getEmail()).roles("TEACHER"))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(overrideRequest)))
                .andExpect(status().isOk());

        // 6. Reload from backend and verify persistence
        mvc.perform(get(subUrl).with(user(authorizedTeacher.getEmail()).roles("TEACHER")))
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
        Submission submission = new Submission();
        submission.setBatch(batch);
        submission.setAssignment(assignment);
        submission.setStudent(pupil);
        submission.setStatus("REVIEW_REQUIRED");
        submissions.save(submission);

        SubmissionImage image = new SubmissionImage();
        image.setSubmission(submission);
        image.setFilePath("submissions/real-worksheet.jpg");
        image.setContentType("image/jpeg");
        image.setFileSize((long) realImageBytes.length);
        images.save(image);

        String subUrl = "/api/v1/teacher/submissions/" + submission.getSubmissionId();
        String imgUrl = subUrl + "/image";

        // Unauthorized teacher from another class cannot view metadata
        mvc.perform(get(subUrl).with(user(unauthorizedTeacher.getEmail()).roles("TEACHER")))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.error.code").value("FORBIDDEN"));

        // Unauthorized teacher cannot fetch private image bytes
        mvc.perform(get(imgUrl).with(user(unauthorizedTeacher.getEmail()).roles("TEACHER")))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.error.code").value("FORBIDDEN"));

        // Unauthorized teacher cannot override or approve
        mvc.perform(post(subUrl + "/approve").with(user(unauthorizedTeacher.getEmail()).roles("TEACHER")))
                .andExpect(status().isForbidden());

        mvc.perform(post(subUrl + "/override")
                        .with(user(unauthorizedTeacher.getEmail()).roles("TEACHER"))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("score", 100, "reason", "Hack"))))
                .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("Approval flow: authorized teacher approves proposed score directly")
    void authorizedTeacherApprovesProposedGradeSuccessfully() throws Exception {
        Submission submission = new Submission();
        submission.setBatch(batch);
        submission.setAssignment(assignment);
        submission.setStudent(pupil);
        submission.setStatus("PROPOSED_GRADE");
        submissions.save(submission);

        AnalysisResult result = new AnalysisResult();
        result.setSubmission(submission);
        result.setStatus("PROPOSED_GRADE");
        result.setGradeProposal(Map.of("suggestedScore", 90, "maxScore", 100, "isOfficial", false));
        analysisResults.saveAndFlush(result);

        String subUrl = "/api/v1/teacher/submissions/" + submission.getSubmissionId();

        mvc.perform(post(subUrl + "/approve")
                        .with(user(authorizedTeacher.getEmail()).roles("TEACHER")))
                .andExpect(status().isOk());

        // Reload submission and verify status is TEACHER_APPROVED
        mvc.perform(get(subUrl).with(user(authorizedTeacher.getEmail()).roles("TEACHER")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("TEACHER_APPROVED"))
                .andExpect(jsonPath("$.teacherScore").value(90));

        TeacherDecision decision = teacherDecisions.findBySubmission_SubmissionId(submission.getSubmissionId()).orElseThrow();
        assertEquals(90, decision.getFinalScore());
        assertEquals("APPROVED", decision.getType());
    }
}

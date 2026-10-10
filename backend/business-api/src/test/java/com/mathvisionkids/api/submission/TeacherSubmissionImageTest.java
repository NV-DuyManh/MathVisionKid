package com.mathvisionkids.api.submission;

import com.mathvisionkids.api.analysis.AiJob;
import com.mathvisionkids.api.analysis.AiJobRepository;
import com.mathvisionkids.api.analysis.AnalysisResult;
import com.mathvisionkids.api.analysis.AnalysisResultRepository;
import com.mathvisionkids.api.assignment.Assignment;
import com.mathvisionkids.api.assignment.AssignmentRepository;
import com.mathvisionkids.api.batch.Batch;
import com.mathvisionkids.api.batch.BatchRepository;
import com.mathvisionkids.api.classroom.Classroom;
import com.mathvisionkids.api.classroom.ClassroomRepository;
import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.HttpHeaders;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.hamcrest.Matchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class TeacherSubmissionImageTest {
    private static final String OLDER_PATH = "submissions/private-older-image.jpg";
    private static final String LATEST_PATH = "submissions/private-latest-image";
    private static final byte[] IMAGE_BYTES = {1, 2, 3, 4};

    @Autowired MockMvc mvc;
    @Autowired TeacherRepository teachers;
    @Autowired StudentRepository students;
    @Autowired ClassroomRepository classrooms;
    @Autowired AssignmentRepository assignments;
    @Autowired BatchRepository batches;
    @Autowired SubmissionRepository submissions;
    @Autowired SubmissionImageRepository images;
    @Autowired AnalysisResultRepository results;
    @Autowired AiJobRepository jobs;
    @MockBean ObjectStorageService storage;

    private Teacher owner;
    private Teacher other;
    private Student student;
    private Submission submission;
    private SubmissionImage latest;

    @BeforeEach void setup() {
        owner = teacher("image-owner@test.com");
        other = teacher("image-other@test.com");
        student = new Student();
        student.setEmail("image-student@test.com");
        student.setPasswordHash("private-student-password-hash");
        student.setRole("STUDENT");
        student.setDisplayName("Image student");
        student.setGradeLevel(3);
        students.save(student);

        Classroom classroom = new Classroom();
        classroom.setName("Image review class");
        classroom.setGradeLevel(3);
        classroom.setTeacher(owner);
        classrooms.save(classroom);

        Assignment assignment = new Assignment();
        assignment.setClassroom(classroom);
        assignment.setTeacher(owner);
        assignment.setTitle("Image review assignment");
        assignment.setOperationType("ADDITION");
        assignment.setMaxScore(10);
        assignments.save(assignment);

        Batch batch = new Batch();
        batch.setAssignment(assignment);
        batch.setTeacher(owner);
        batch.setStatus("CREATED");
        batches.save(batch);

        submission = new Submission();
        submission.setBatch(batch);
        submission.setAssignment(assignment);
        submission.setStudent(student);
        submission.setStatus("REVIEW_REQUIRED");
        submissions.save(submission);

        image(OLDER_PATH, "image/jpeg", Instant.parse("2026-01-01T00:00:00Z"));
        latest = image(LATEST_PATH, "image/png", Instant.parse("2026-01-02T00:00:00Z"));
        images.flush();
    }

    private Teacher teacher(String email) {
        Teacher teacher = new Teacher();
        teacher.setEmail(email);
        teacher.setPasswordHash("unused-test-hash");
        teacher.setRole("TEACHER");
        teacher.setDisplayName("Image reviewer");
        return teachers.save(teacher);
    }

    private SubmissionImage image(String path, String contentType, Instant createdAt) {
        SubmissionImage image = new SubmissionImage();
        image.setSubmission(submission);
        image.setFilePath(path);
        image.setContentType(contentType);
        image.setFileSize((long) IMAGE_BYTES.length);
        image.setCreatedAt(createdAt);
        return images.save(image);
    }

    private String imageUrl() {
        return submissionUrl() + "/image";
    }

    private String submissionUrl() {
        return "/api/v1/teacher/submissions/" + submission.getSubmissionId();
    }

    private AnalysisResult analysis() {
        AnalysisResult result = new AnalysisResult();
        result.setSubmission(submission);
        result.setStatus("PROPOSED_GRADE");
        result.setGradeProposal(Map.of("suggestedScore", 0, "maxScore", 10, "isOfficial", false));
        result.setRecognizedExercise(Map.of("expression", "12 + 22 = 34"));
        result.setReviewReasons(Map.of("recognition", .92, "structure", .73, "diagnosis", .81));
        result.setValidation(Map.of("isValid", true, "diagnosisState", "VALID"));
        result.setEvidence(Map.of("items", List.of(Map.of("type", "CARRY"))));
        return results.saveAndFlush(result);
    }

    @ParameterizedTest @ValueSource(strings = {"image/jpeg", "image/png", "image/webp"})
    void ownerReceivesOnlyTheLatestImageWithItsStoredMediaTypeAndNoCaching(String contentType) throws Exception {
        latest.setContentType(contentType);
        images.saveAndFlush(latest);
        when(storage.loadBytes(LATEST_PATH)).thenReturn(IMAGE_BYTES);

        mvc.perform(get(imageUrl()).with(user(owner.getEmail()).roles("TEACHER")))
                .andExpect(status().isOk())
                .andExpect(content().bytes(IMAGE_BYTES))
                .andExpect(content().contentType(contentType))
                .andExpect(header().string(HttpHeaders.CACHE_CONTROL, "no-store"));

        verify(storage).loadBytes(LATEST_PATH);
        verifyNoMoreInteractions(storage);
    }

    @Test void foreignTeacherIsRejectedWithoutLoadingOrDisclosingImagePaths() throws Exception {
        mvc.perform(get(imageUrl()).with(user(other.getEmail()).roles("TEACHER")))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.error.code").value("FORBIDDEN"))
                .andExpect(content().string(allOf(not(containsString(OLDER_PATH)),
                        not(containsString(LATEST_PATH)), not(containsString("filePath")))));

        verifyNoInteractions(storage);
    }

    @Test void foreignTeacherIsRejectedEvenWhenTheSubmissionHasNoImage() throws Exception {
        images.deleteAll();
        images.flush();

        mvc.perform(get(imageUrl()).with(user(other.getEmail()).roles("TEACHER")))
                .andExpect(status().isForbidden());

        verifyNoInteractions(storage);
    }

    @Test void anonymousRequestRequiresAuthenticationBeforeStorageAccess() throws Exception {
        mvc.perform(get(imageUrl())).andExpect(status().isUnauthorized());
        verifyNoInteractions(storage);
    }

    @Test void studentCannotReadTeacherSubmissionImages() throws Exception {
        mvc.perform(get(imageUrl()).with(user("image-student@test.com").roles("STUDENT")))
                .andExpect(status().isForbidden());
        verifyNoInteractions(storage);
    }

    @Test void ownerGetsNotFoundWhenThereIsNoImage() throws Exception {
        images.deleteAll();
        images.flush();

        mvc.perform(get(imageUrl()).with(user(owner.getEmail()).roles("TEACHER")))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error.code").value("NOT_FOUND"));

        verifyNoInteractions(storage);
    }

    @Test void ownerReceivesActualAnalysisAndSafeStudentMetadataWithoutPrivateEntitiesOrPaths() throws Exception {
        analysis();

        mvc.perform(get(submissionUrl()).with(user(owner.getEmail()).roles("TEACHER")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.submissionId").value(submission.getSubmissionId().toString()))
                .andExpect(jsonPath("$.status").value("REVIEW_REQUIRED"))
                .andExpect(jsonPath("$.createdAt").isString())
                .andExpect(jsonPath("$.studentId").value(student.getId().toString()))
                .andExpect(jsonPath("$.studentName").value(student.getDisplayName()))
                .andExpect(jsonPath("$.assignmentId").value(submission.getAssignment().getAssignmentId().toString()))
                .andExpect(jsonPath("$.batchId").value(submission.getBatch().getBatchId().toString()))
                .andExpect(jsonPath("$.maxScore").value(10))
                .andExpect(jsonPath("$.imageUrl").value(imageUrl()))
                .andExpect(jsonPath("$.analysisStatus").value("PROPOSED_GRADE"))
                .andExpect(jsonPath("$.gradeProposal.suggestedScore").value(0))
                .andExpect(jsonPath("$.gradeProposal.maxScore").value(10))
                .andExpect(jsonPath("$.gradeProposal.isOfficial").value(false))
                .andExpect(jsonPath("$.suggestedScore").value(0))
                .andExpect(jsonPath("$.confidenceBundle.recognition").value(.92))
                .andExpect(jsonPath("$.confidenceBundle.structure").value(.73))
                .andExpect(jsonPath("$.confidenceBundle.diagnosis").value(.81))
                .andExpect(jsonPath("$.recognizedText").value("12 + 22 = 34"))
                .andExpect(jsonPath("$.validation.isValid").value(true))
                .andExpect(jsonPath("$.validation.diagnosisState").value("VALID"))
                .andExpect(jsonPath("$.evidence.items[0].type").value("CARRY"))
                .andExpect(jsonPath("$.student").doesNotExist())
                .andExpect(jsonPath("$.assignment").doesNotExist())
                .andExpect(jsonPath("$.batch").doesNotExist())
                .andExpect(content().string(allOf(not(containsString(OLDER_PATH)),
                        not(containsString(LATEST_PATH)), not(containsString("passwordHash")),
                        not(containsString("private-student-password-hash")),
                        not(containsString(student.getEmail())), not(containsString(owner.getEmail())))));

        verifyNoInteractions(storage);
    }

    @Test void absentAnalysisLeavesScoreConfidenceAndRecognizedTextUnavailable() throws Exception {
        mvc.perform(get(submissionUrl()).with(user(owner.getEmail()).roles("TEACHER")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.studentName").value(student.getDisplayName()))
                .andExpect(jsonPath("$.analysisStatus").doesNotExist())
                .andExpect(jsonPath("$.gradeProposal").doesNotExist())
                .andExpect(jsonPath("$.suggestedScore").doesNotExist())
                .andExpect(jsonPath("$.confidenceBundle").doesNotExist())
                .andExpect(jsonPath("$.recognizedText").doesNotExist());

        verifyNoInteractions(storage);
    }

    @Test void foreignTeacherCannotReadStudentOrAnalysisMetadata() throws Exception {
        analysis();

        mvc.perform(get(submissionUrl()).with(user(other.getEmail()).roles("TEACHER")))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.error.code").value("FORBIDDEN"))
                .andExpect(jsonPath("$.studentName").doesNotExist())
                .andExpect(jsonPath("$.gradeProposal").doesNotExist())
                .andExpect(content().string(allOf(not(containsString(student.getDisplayName())),
                        not(containsString("12 + 22 = 34")), not(containsString(OLDER_PATH)),
                        not(containsString(LATEST_PATH)))));

        verifyNoInteractions(storage);
    }

    @Test void malformedAnalysisValuesAreNotCoercedIntoMeasuredFields() throws Exception {
        AnalysisResult result = analysis();
        result.setGradeProposal(Map.of("suggestedScore", "unknown"));
        result.setReviewReasons(Map.of("recognition", .6, "structure", "0.7", "diagnosis", false));
        result.setRecognizedExercise(Map.of("expression", List.of("unrecognized")));
        results.saveAndFlush(result);

        mvc.perform(get(submissionUrl()).with(user(owner.getEmail()).roles("TEACHER")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.suggestedScore").doesNotExist())
                .andExpect(jsonPath("$.confidenceBundle.recognition").value(.6))
                .andExpect(jsonPath("$.confidenceBundle.structure").doesNotExist())
                .andExpect(jsonPath("$.confidenceBundle.diagnosis").doesNotExist())
                .andExpect(jsonPath("$.recognizedText").doesNotExist());

        verifyNoInteractions(storage);
    }

    @ParameterizedTest @ValueSource(strings = {"PROCESSING", "FAILED", "MISMATCH"})
    void incompleteFailedOrOlderAttemptsDoNotExposeStaleAnalysis(String state) throws Exception {
        AnalysisResult result = analysis();
        AiJob job = new AiJob();
        job.setSubmission(submission);
        job.setStatus(state.equals("FAILED") ? "FAILED" : "COMPLETED");
        jobs.saveAndFlush(job);
        result.setReviewReasons(Map.of("recognition", .92, "jobId",
                state.equals("MISMATCH") ? UUID.randomUUID().toString() : job.getJobId().toString()));
        results.saveAndFlush(result);
        if (state.equals("PROCESSING")) {
            submission.setStatus("PROCESSING");
            submissions.saveAndFlush(submission);
        }

        mvc.perform(get(submissionUrl()).with(user(owner.getEmail()).roles("TEACHER")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.analysisStatus").doesNotExist())
                .andExpect(jsonPath("$.gradeProposal").doesNotExist())
                .andExpect(jsonPath("$.suggestedScore").doesNotExist())
                .andExpect(jsonPath("$.confidenceBundle").doesNotExist())
                .andExpect(jsonPath("$.recognizedText").doesNotExist())
                .andExpect(jsonPath("$.validation").doesNotExist())
                .andExpect(jsonPath("$.evidence").doesNotExist());

        verifyNoInteractions(storage);
    }
}

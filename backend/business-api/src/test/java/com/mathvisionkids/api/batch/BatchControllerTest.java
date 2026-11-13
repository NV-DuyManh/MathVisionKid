package com.mathvisionkids.api.batch;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.assignment.Assignment;
import com.mathvisionkids.api.assignment.AssignmentRepository;
import com.mathvisionkids.api.classroom.Classroom;
import com.mathvisionkids.api.classroom.ClassroomRepository;
import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@org.springframework.transaction.annotation.Transactional
public class BatchControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private TeacherRepository teacherRepository;

    @Autowired
    private StudentRepository studentRepository;

    @Autowired
    private ClassroomRepository classroomRepository;

    @Autowired
    private AssignmentRepository assignmentRepository;

    @Autowired
    private BatchRepository batchRepository;

    @Autowired
    private BatchService batchService;

    @Autowired
    private jakarta.persistence.EntityManager entityManager;

    @MockBean
    private ObjectStorageService objectStorageService;

    private Teacher teacher1;
    private Teacher teacher2;
    private Student studentInClass;
    private Student studentOutsideClass;
    private Assignment assignment;
    private Batch testBatch;
    private static final byte[] IMAGE = java.util.Base64.getDecoder().decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aBXsAAAAASUVORK5CYII=");

    @Autowired private com.mathvisionkids.api.submission.SubmissionRepository submissions;

    @org.springframework.test.context.transaction.AfterTransaction
    void clearRollbackCleanupInvocations() {
        // Spring rolls test transactions back after Mockito's AFTER reset.
        // Object cleanup belongs to this test, never to the next context user.
        org.mockito.Mockito.clearInvocations(objectStorageService);
    }

    @BeforeEach
    public void setup() throws Exception {
        teacher1 = new Teacher();
        teacher1.setEmail("teacher1@test.com");
        teacher1.setPasswordHash("pass");
        teacher1.setRole("TEACHER");
        teacher1.setDisplayName("Teacher 1");
        teacher1 = teacherRepository.save(teacher1);

        teacher2 = new Teacher();
        teacher2.setEmail("teacher2@test.com");
        teacher2.setPasswordHash("pass");
        teacher2.setRole("TEACHER");
        teacher2.setDisplayName("Teacher 2");
        teacher2 = teacherRepository.save(teacher2);

        studentInClass = new Student();
        studentInClass.setEmail("student1@test.com");
        studentInClass.setPasswordHash("pass");
        studentInClass.setRole("STUDENT");
        studentInClass.setGradeLevel(3);
        studentInClass.setDisplayName("Student 1");
        studentInClass = studentRepository.save(studentInClass);

        studentOutsideClass = new Student();
        studentOutsideClass.setEmail("student2@test.com");
        studentOutsideClass.setPasswordHash("pass");
        studentOutsideClass.setRole("STUDENT");
        studentOutsideClass.setGradeLevel(3);
        studentOutsideClass.setDisplayName("Student 2");
        studentOutsideClass = studentRepository.save(studentOutsideClass);

        Classroom classroom = new Classroom();
        classroom.setName("Math 101");
        classroom.setGradeLevel(3);
        classroom.setTeacher(teacher1);
        classroom.getStudents().add(studentInClass);
        classroom = classroomRepository.save(classroom);

        assignment = new Assignment();
        assignment.setTitle("Test Assignment");
        assignment.setOperationType("ADDITION");
        assignment.setTeacher(teacher1);
        assignment.setClassroom(classroom);
        assignment.setMaxScore(100);
        assignment = assignmentRepository.save(assignment);

        testBatch = new Batch();
        testBatch.setTeacher(teacher1);
        testBatch.setAssignment(assignment);
        testBatch.setStatus("CREATED");
        testBatch = batchRepository.save(testBatch);

        when(objectStorageService.store(any(), anyString())).thenReturn("test/path.jpg");
    }

    @Test
    @WithMockUser(username = "teacher1@test.com", roles = "TEACHER")
    void creationKeyReplaysAfterUploadAndChecksCurrentOwnership() throws Exception {
        var key = java.util.UUID.randomUUID();
        var payload = java.util.Map.of("assignmentId", assignment.getAssignmentId().toString(), "creationRequestId", key.toString());
        String body = objectMapper.writeValueAsString(payload);
        var first = mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post("/api/v1/teacher/batches")
                .contentType("application/json").content(body)).andExpect(status().isCreated()).andReturn();
        String id = objectMapper.readTree(first.getResponse().getContentAsString()).get("batchId").asText();
        BatchImageMapping mapping = new BatchImageMapping(); mapping.setFileIndex(0); mapping.setStudentId(studentInClass.getId());
        mockMvc.perform(multipart("/api/v1/teacher/batches/" + id + "/submissions")
                .file(new MockMultipartFile("images", "synthetic.png", "image/png", IMAGE))
                .param("manifest", objectMapper.writeValueAsString(List.of(mapping)))).andExpect(status().isAccepted());
        mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post("/api/v1/teacher/batches")
                .contentType("application/json").content(body)).andExpect(status().isOk())
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.batchId").value(id))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.status").value("PROCESSING"));
        Assignment other = new Assignment(); other.setTeacher(teacher1); other.setClassroom(assignment.getClassroom());
        other.setTitle("Other"); other.setOperationType("ADDITION"); other.setMaxScore(10); other = assignmentRepository.save(other);
        var conflict = java.util.Map.of("assignmentId", other.getAssignmentId().toString(), "creationRequestId", key.toString());
        mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post("/api/v1/teacher/batches")
                .contentType("application/json").content(objectMapper.writeValueAsString(conflict))).andExpect(status().isConflict());
        assignment.getClassroom().setTeacher(teacher2); classroomRepository.saveAndFlush(assignment.getClassroom());
        mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post("/api/v1/teacher/batches")
                .contentType("application/json").content(body)).andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(username = "teacher1@test.com", roles = "TEACHER")
    void creationWithoutKeyRemainsSupportedAndInvalidKeyIsRejected() throws Exception {
        String body = objectMapper.writeValueAsString(java.util.Map.of("assignmentId", assignment.getAssignmentId().toString()));
        for (int i = 0; i < 2; i++) mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post("/api/v1/teacher/batches")
                .contentType("application/json").content(body)).andExpect(status().isCreated());
        mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post("/api/v1/teacher/batches")
                .contentType("application/json").content(objectMapper.writeValueAsString(java.util.Map.of(
                        "assignmentId", assignment.getAssignmentId().toString(), "creationRequestId", "bad"))))
                .andExpect(status().isBadRequest());
    }

    @Test
    void batchListKeepsProgressAndMetadataWithConstantQueriesForOneAndTwentyOneBatches() {
        List<Student> students = new ArrayList<>(List.of(studentInClass));
        for (int i = 1; i < 4; i++) {
            Student student = new Student();
            student.setEmail("progress-student" + i + "@test.com");
            student.setPasswordHash("pass");
            student.setRole("STUDENT");
            student.setGradeLevel(3);
            student.setDisplayName("Progress Student " + i);
            students.add(studentRepository.save(student));
        }
        assignment.getClassroom().getStudents().addAll(students);
        classroomRepository.save(assignment.getClassroom());

        int studentIndex = 0;
        for (String state : List.of("PROPOSED_GRADE", "NEEDS_RETAKE", "TEACHER_APPROVED", "FAILED")) {
            var submission = new com.mathvisionkids.api.submission.Submission();
            submission.setBatch(testBatch);
            submission.setAssignment(assignment);
            submission.setStudent(students.get(studentIndex++));
            submission.setStatus(state);
            submissions.save(submission);
        }
        entityManager.flush();

        var statistics = entityManager.getEntityManagerFactory().unwrap(org.hibernate.SessionFactory.class).getStatistics();
        boolean wasEnabled = statistics.isStatisticsEnabled();
        statistics.setStatisticsEnabled(true);
        try {
            entityManager.clear();
            long before = statistics.getPrepareStatementCount();
            var shortList = batchService.getBatches(teacher1.getEmail());
            long shortHistory = statistics.getPrepareStatementCount() - before;

            for (int i = 0; i < 20; i++) {
                Batch batch = new Batch();
                batch.setTeacher(teacher1);
                batch.setAssignment(assignment);
                batch.setStatus("CREATED");
                batchRepository.save(batch);
            }
            entityManager.flush();
            entityManager.clear();

            before = statistics.getPrepareStatementCount();
            var longList = batchService.getBatches(teacher1.getEmail());
            long longHistory = statistics.getPrepareStatementCount() - before;

            assertEquals(1, shortList.size());
            var summarized = shortList.getFirst();
            assertEquals(testBatch.getBatchId(), summarized.batchId());
            assertEquals(assignment.getAssignmentId(), summarized.assignmentId());
            assertEquals("Test Assignment", summarized.assignmentTitle());
            assertEquals("Math 101", summarized.className());
            assertEquals("PARTIAL", summarized.status());
            assertEquals(4, summarized.totalCount());
            assertEquals(4, summarized.processedCount());
            assertEquals(1, summarized.reviewRequiredCount());
            assertEquals(2, summarized.pendingReviewCount());
            assertEquals(1, summarized.finalizedCount());
            assertEquals(1, summarized.failedCount());
            assertNull(summarized.submissions());
            assertEquals(21, longList.size());
            assertEquals(shortHistory, longHistory, "Queries for 1 versus 21 batches");
            assertEquals(2, longHistory, "Teacher lookup and aggregate batch list");
            for (int i = 1; i < longList.size(); i++) {
                assertFalse(longList.get(i - 1).createdAt().isBefore(longList.get(i).createdAt()),
                        "Batch list remains ordered newest first");
            }

            var reassignedClass = new Classroom();
            reassignedClass.setName("Reassigned class");
            reassignedClass.setGradeLevel(3);
            reassignedClass.setTeacher(teacher2);
            reassignedClass = classroomRepository.save(reassignedClass);
            var reassignedAssignment = new Assignment();
            reassignedAssignment.setTitle("Old teacher batch");
            reassignedAssignment.setOperationType("ADDITION");
            reassignedAssignment.setTeacher(teacher1);
            reassignedAssignment.setClassroom(reassignedClass);
            reassignedAssignment.setMaxScore(100);
            reassignedAssignment = assignmentRepository.save(reassignedAssignment);
            Batch reassignedBatch = new Batch();
            reassignedBatch.setTeacher(teacher1);
            reassignedBatch.setAssignment(reassignedAssignment);
            reassignedBatch.setStatus("CREATED");
            batchRepository.saveAndFlush(reassignedBatch);
            assertEquals(21, batchService.getBatches(teacher1.getEmail()).size(),
                    "Batch access still requires ownership and current class assignment");
        } finally {
            statistics.setStatisticsEnabled(wasEnabled);
        }
    }

    @Test
    @WithMockUser(username = "teacher1@test.com", roles = "TEACHER")
    void completedAndReviewRequiredSubmissionsDriveRealBatchProgress() throws Exception {
        for (String state : List.of("PROPOSED_GRADE", "NEEDS_RETAKE", "FEEDBACK_READY", "TEACHER_APPROVED")) {
            var submission = new com.mathvisionkids.api.submission.Submission();
            submission.setBatch(testBatch);
            submission.setAssignment(assignment);
            submission.setStudent(studentInClass);
            submission.setStatus(state);
            submissions.save(submission);
        }
        testBatch.setStatus("PROCESSING");
        batchRepository.saveAndFlush(testBatch);
        mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get("/api/v1/teacher/batches/" + testBatch.getBatchId()))
                .andExpect(status().isOk())
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.status").value("COMPLETED"))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.processedCount").value(4))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.totalCount").value(4))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.reviewRequiredCount").value(1))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.pendingReviewCount").value(3))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.finalizedCount").value(1))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.assignmentId").value(assignment.getAssignmentId().toString()))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.assignmentTitle").value("Test Assignment"))
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.submissions.length()").value(4));
        mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get("/api/v1/teacher/batches/" + testBatch.getBatchId() + "/review"))
                .andExpect(status().isOk())
                .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath("$.length()").value(3));
    }

    @Test
    @WithMockUser(username = "teacher1@test.com", roles = "TEACHER")
    void spoofedImageAndNullManifestNeverStoreFiles() throws Exception {
        BatchImageMapping mapping = new BatchImageMapping();
        mapping.setFileIndex(0);
        mapping.setStudentId(studentInClass.getId());
        mockMvc.perform(multipart("/api/v1/teacher/batches/" + testBatch.getBatchId() + "/submissions")
                .file(new MockMultipartFile("images", "fake.jpg", "image/jpeg", "not an image".getBytes()))
                .param("manifest", objectMapper.writeValueAsString(List.of(mapping))))
                .andExpect(status().isUnprocessableEntity());
        org.mockito.Mockito.verify(objectStorageService, org.mockito.Mockito.never()).store(any(), anyString());
    }

    @Test
    @WithMockUser(username = "teacher1@test.com", roles = "TEACHER")
    public void testUpload10ValidFiles() throws Exception {
        List<BatchImageMapping> mappings = new ArrayList<>();
        var builder = multipart("/api/v1/teacher/batches/" + testBatch.getBatchId() + "/submissions");
        
        for (int i = 0; i < 10; i++) {
            MockMultipartFile file = new MockMultipartFile("images", "file" + i + ".jpg", "image/png", IMAGE);
            builder.file(file);
            
            BatchImageMapping mapping = new BatchImageMapping();
            mapping.setFileIndex(i);
            mapping.setStudentId(studentInClass.getId());
            mappings.add(mapping);
        }

        builder.param("manifest", objectMapper.writeValueAsString(mappings));

        mockMvc.perform(builder)
               .andExpect(status().isAccepted());
    }

    @Test
    @WithMockUser(username = "teacher1@test.com", roles = "TEACHER")
    public void testUpload30ValidFiles() throws Exception {
        List<BatchImageMapping> mappings = new ArrayList<>();
        var builder = multipart("/api/v1/teacher/batches/" + testBatch.getBatchId() + "/submissions");
        
        for (int i = 0; i < 30; i++) {
            MockMultipartFile file = new MockMultipartFile("images", "file" + i + ".jpg", "image/png", IMAGE);
            builder.file(file);
            
            BatchImageMapping mapping = new BatchImageMapping();
            mapping.setFileIndex(i);
            mapping.setStudentId(studentInClass.getId());
            mappings.add(mapping);
        }

        builder.param("manifest", objectMapper.writeValueAsString(mappings));

        mockMvc.perform(builder)
               .andExpect(status().isAccepted());
    }

    @Test
    @WithMockUser(username = "teacher1@test.com", roles = "TEACHER")
    public void testUpload0FilesRejected() throws Exception {
        List<BatchImageMapping> mappings = new ArrayList<>();
        var builder = multipart("/api/v1/teacher/batches/" + testBatch.getBatchId() + "/submissions");
        builder.param("manifest", objectMapper.writeValueAsString(mappings));

        mockMvc.perform(builder)
               .andExpect(status().isBadRequest());
    }

    @Test
    @WithMockUser(username = "teacher1@test.com", roles = "TEACHER")
    public void testUpload1ValidFile() throws Exception {
        List<BatchImageMapping> mappings = new ArrayList<>();
        var builder = multipart("/api/v1/teacher/batches/" + testBatch.getBatchId() + "/submissions");
        
        MockMultipartFile file = new MockMultipartFile("images", "file0.jpg", "image/png", IMAGE);
        builder.file(file);
        
        BatchImageMapping mapping = new BatchImageMapping();
        mapping.setFileIndex(0);
        mapping.setStudentId(studentInClass.getId());
        mappings.add(mapping);

        builder.param("manifest", objectMapper.writeValueAsString(mappings));

        mockMvc.perform(builder)
               .andExpect(status().isAccepted());
    }

    @Test
    @WithMockUser(username = "teacher1@test.com", roles = "TEACHER")
    public void testUpload9ValidFiles() throws Exception {
        List<BatchImageMapping> mappings = new ArrayList<>();
        var builder = multipart("/api/v1/teacher/batches/" + testBatch.getBatchId() + "/submissions");
        
        for (int i = 0; i < 9; i++) {
            MockMultipartFile file = new MockMultipartFile("images", "file" + i + ".jpg", "image/png", IMAGE);
            builder.file(file);
            
            BatchImageMapping mapping = new BatchImageMapping();
            mapping.setFileIndex(i);
            mapping.setStudentId(studentInClass.getId());
            mappings.add(mapping);
        }

        builder.param("manifest", objectMapper.writeValueAsString(mappings));

        mockMvc.perform(builder)
               .andExpect(status().isAccepted());
    }

    @Test
    @WithMockUser(username = "teacher1@test.com", roles = "TEACHER")
    public void testUpload31FilesRejected() throws Exception {
        List<BatchImageMapping> mappings = new ArrayList<>();
        var builder = multipart("/api/v1/teacher/batches/" + testBatch.getBatchId() + "/submissions");
        
        for (int i = 0; i < 31; i++) {
            MockMultipartFile file = new MockMultipartFile("images", "file" + i + ".jpg", "image/png", IMAGE);
            builder.file(file);
            
            BatchImageMapping mapping = new BatchImageMapping();
            mapping.setFileIndex(i);
            mapping.setStudentId(studentInClass.getId());
            mappings.add(mapping);
        }

        builder.param("manifest", objectMapper.writeValueAsString(mappings));

        mockMvc.perform(builder)
               .andExpect(status().isBadRequest());
    }

    @Test
    @WithMockUser(username = "teacher1@test.com", roles = "TEACHER")
    public void testMissingStudentMapping() throws Exception {
        List<BatchImageMapping> mappings = new ArrayList<>();
        var builder = multipart("/api/v1/teacher/batches/" + testBatch.getBatchId() + "/submissions");
        
        for (int i = 0; i < 10; i++) {
            MockMultipartFile file = new MockMultipartFile("images", "file" + i + ".jpg", "image/png", IMAGE);
            builder.file(file);
            
            BatchImageMapping mapping = new BatchImageMapping();
            mapping.setFileIndex(i);
            // Missing student ID
            mappings.add(mapping);
        }

        builder.param("manifest", objectMapper.writeValueAsString(mappings));

        mockMvc.perform(builder)
               .andExpect(status().isBadRequest());
    }

    @Test
    @WithMockUser(username = "teacher1@test.com", roles = "TEACHER")
    public void testStudentOutsideClassroom() throws Exception {
        List<BatchImageMapping> mappings = new ArrayList<>();
        var builder = multipart("/api/v1/teacher/batches/" + testBatch.getBatchId() + "/submissions");
        
        for (int i = 0; i < 10; i++) {
            MockMultipartFile file = new MockMultipartFile("images", "file" + i + ".jpg", "image/png", IMAGE);
            builder.file(file);
            
            BatchImageMapping mapping = new BatchImageMapping();
            mapping.setFileIndex(i);
            mapping.setStudentId(studentOutsideClass.getId()); // Not in class
            mappings.add(mapping);
        }

        builder.param("manifest", objectMapper.writeValueAsString(mappings));

        mockMvc.perform(builder)
               .andExpect(status().isBadRequest());
    }

    @Test
    @WithMockUser(username = "teacher2@test.com", roles = "TEACHER")
    public void testUnauthorizedTeacher() throws Exception {
        List<BatchImageMapping> mappings = new ArrayList<>();
        var builder = multipart("/api/v1/teacher/batches/" + testBatch.getBatchId() + "/submissions");
        
        for (int i = 0; i < 10; i++) {
            MockMultipartFile file = new MockMultipartFile("images", "file" + i + ".jpg", "image/png", IMAGE);
            builder.file(file);
            
            BatchImageMapping mapping = new BatchImageMapping();
            mapping.setFileIndex(i);
            mapping.setStudentId(studentInClass.getId());
            mappings.add(mapping);
        }

        builder.param("manifest", objectMapper.writeValueAsString(mappings));

        // teacher2 does not own testBatch
        mockMvc.perform(builder)
               .andExpect(status().isForbidden());
        var get = org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get("/api/v1/teacher/batches/" + testBatch.getBatchId());
        mockMvc.perform(get).andExpect(status().isForbidden());
        mockMvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get("/api/v1/teacher/batches/" + testBatch.getBatchId() + "/review"))
                .andExpect(status().isForbidden());
    }
}

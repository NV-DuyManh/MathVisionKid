package com.mathvisionkids.api.assignment;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.auth.JwtUtil;
import com.mathvisionkids.api.classroom.Classroom;
import com.mathvisionkids.api.classroom.ClassroomRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import com.mathvisionkids.api.user.UserRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.util.UUID;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
public class TeacherAssignmentControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private TeacherRepository teacherRepository;

    @Autowired
    private ClassroomRepository classroomRepository;

    @Autowired
    private AssignmentRepository assignmentRepository;

    @Autowired
    private JwtUtil jwtUtil;

    private Teacher teacher1;
    private Teacher teacher2;
    private Classroom classroom1;
    private String teacher1Token;
    private String teacher2Token;

    @BeforeEach
    public void setup() {
        tearDown();

        teacher1 = new Teacher();
        teacher1.setEmail("teacher1@test.com");
        teacher1.setPasswordHash("hash");
        teacher1.setDisplayName("Teacher One");
        teacher1.setRole("TEACHER");
        teacher1 = teacherRepository.save(teacher1);

        teacher2 = new Teacher();
        teacher2.setEmail("teacher2@test.com");
        teacher2.setPasswordHash("hash");
        teacher2.setDisplayName("Teacher Two");
        teacher2.setRole("TEACHER");
        teacher2 = teacherRepository.save(teacher2);

        classroom1 = new Classroom();
        classroom1.setName("Lớp 3A");
        classroom1.setGradeLevel(3);
        classroom1.setTeacher(teacher1);
        classroom1 = classroomRepository.save(classroom1);

        teacher1Token = jwtUtil.generateToken(teacher1.getEmail(), "TEACHER");
        teacher2Token = jwtUtil.generateToken(teacher2.getEmail(), "TEACHER");
    }

    @AfterEach
    public void tearDown() {
        assignmentRepository.deleteAll();
        classroomRepository.deleteAll();
        teacherRepository.deleteAll();
        userRepository.deleteAll();
    }

    @Test
    public void testCreateAssignmentSuccess() throws Exception {
        AssignmentRequest request = new AssignmentRequest();
        request.setClassId(classroom1.getClassId());
        request.setTitle("Phép cộng trong phạm vi 1000");
        request.setOperationType("VERTICAL_ADDITION");
        request.setMaxScore(10);

        mockMvc.perform(post("/api/v1/teacher/assignments")
                        .header("Authorization", "Bearer " + teacher1Token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.assignmentId", notNullValue()))
                .andExpect(jsonPath("$.title", is("Phép cộng trong phạm vi 1000")))
                .andExpect(jsonPath("$.maxScore", is(10)))
                .andExpect(jsonPath("$.status", is("ACTIVE")));
    }

    @Test
    public void testCreateAssignmentWithMaxScore100Success() throws Exception {
        AssignmentRequest request = new AssignmentRequest();
        request.setClassId(classroom1.getClassId());
        request.setTitle("Bài kiểm tra 100 điểm");
        request.setOperationType("VERTICAL_SUBTRACTION");
        request.setMaxScore(100);

        mockMvc.perform(post("/api/v1/teacher/assignments")
                        .header("Authorization", "Bearer " + teacher1Token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.maxScore", is(100)));
    }

    @Test
    public void testCreateAssignmentMaxScoreZeroRejected() throws Exception {
        AssignmentRequest request = new AssignmentRequest();
        request.setClassId(classroom1.getClassId());
        request.setTitle("Điểm 0 không hợp lệ");
        request.setOperationType("VERTICAL_ADDITION");
        request.setMaxScore(0);

        mockMvc.perform(post("/api/v1/teacher/assignments")
                        .header("Authorization", "Bearer " + teacher1Token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void testCreateAssignmentMaxScoreNegativeRejected() throws Exception {
        AssignmentRequest request = new AssignmentRequest();
        request.setClassId(classroom1.getClassId());
        request.setTitle("Điểm âm không hợp lệ");
        request.setOperationType("VERTICAL_ADDITION");
        request.setMaxScore(-10);

        mockMvc.perform(post("/api/v1/teacher/assignments")
                        .header("Authorization", "Bearer " + teacher1Token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void testCreateAssignmentMaxScoreOver100Rejected() throws Exception {
        AssignmentRequest request = new AssignmentRequest();
        request.setClassId(classroom1.getClassId());
        request.setTitle("Điểm vượt quá 100 không hợp lệ");
        request.setOperationType("VERTICAL_ADDITION");
        request.setMaxScore(101);

        mockMvc.perform(post("/api/v1/teacher/assignments")
                        .header("Authorization", "Bearer " + teacher1Token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void testCreateAssignmentNullMaxScoreRejected() throws Exception {
        AssignmentRequest request = new AssignmentRequest();
        request.setClassId(classroom1.getClassId());
        request.setTitle("Thiếu điểm tối đa");
        request.setOperationType("VERTICAL_ADDITION");
        request.setMaxScore(null);

        mockMvc.perform(post("/api/v1/teacher/assignments")
                        .header("Authorization", "Bearer " + teacher1Token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void testCreateAssignmentForbiddenForOtherTeacherClassroom() throws Exception {
        AssignmentRequest request = new AssignmentRequest();
        request.setClassId(classroom1.getClassId());
        request.setTitle("Bài tập lớp giáo viên khác");
        request.setOperationType("VERTICAL_ADDITION");
        request.setMaxScore(10);

        // Teacher 2 tries to create assignment in Teacher 1's classroom
        mockMvc.perform(post("/api/v1/teacher/assignments")
                        .header("Authorization", "Bearer " + teacher2Token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isForbidden());
    }

    @Test
    public void testCreateAssignmentClassNotFound() throws Exception {
        AssignmentRequest request = new AssignmentRequest();
        request.setClassId(UUID.randomUUID());
        request.setTitle("Lớp không tồn tại");
        request.setOperationType("VERTICAL_ADDITION");
        request.setMaxScore(10);

        mockMvc.perform(post("/api/v1/teacher/assignments")
                        .header("Authorization", "Bearer " + teacher1Token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isNotFound());
    }

    @Test
    public void testGetAssignmentsOnlyReturnsOwnAssignments() throws Exception {
        Assignment a1 = new Assignment();
        a1.setTeacher(teacher1);
        a1.setClassroom(classroom1);
        a1.setTitle("Bài 1 của Teacher 1");
        a1.setOperationType("VERTICAL_ADDITION");
        a1.setMaxScore(10);
        a1.setStatus("ACTIVE");
        assignmentRepository.save(a1);

        mockMvc.perform(get("/api/v1/teacher/assignments")
                        .header("Authorization", "Bearer " + teacher1Token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].title", is("Bài 1 của Teacher 1")));

        mockMvc.perform(get("/api/v1/teacher/assignments")
                        .header("Authorization", "Bearer " + teacher2Token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    public void testCreateAssignmentUnauthorizedWithoutToken() throws Exception {
        AssignmentRequest request = new AssignmentRequest();
        request.setClassId(classroom1.getClassId());
        request.setTitle("Không token");
        request.setOperationType("VERTICAL_ADDITION");
        request.setMaxScore(10);

        mockMvc.perform(post("/api/v1/teacher/assignments")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized());
    }

    @Test
    public void testCreateAssignmentFractionalMaxScoreRejectedWithoutSaving() throws Exception {
        long initialCount = assignmentRepository.count();

        for (String fractionalScore : new String[]{"1.5", "99.9", "100.9"}) {
            String jsonPayload = String.format(
                    "{\"classId\":\"%s\",\"title\":\"Fractional test %s\",\"operationType\":\"VERTICAL_ADDITION\",\"maxScore\":%s}",
                    classroom1.getClassId(), fractionalScore, fractionalScore
            );

            mockMvc.perform(post("/api/v1/teacher/assignments")
                            .header("Authorization", "Bearer " + teacher1Token)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(jsonPayload))
                    .andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.error.code", is("VALIDATION_ERROR")));
        }

        // Verify zero assignments were saved
        org.junit.jupiter.api.Assertions.assertEquals(initialCount, assignmentRepository.count(),
                "No assignment must be created or saved when maxScore is fractional");
    }

    @Test
    public void testCreateAssignmentIntegerBoundariesOneAndOneHundred() throws Exception {
        // Boundary 1
        String payload1 = String.format(
                "{\"classId\":\"%s\",\"title\":\"Boundary 1\",\"operationType\":\"VERTICAL_ADDITION\",\"maxScore\":1}",
                classroom1.getClassId()
        );
        mockMvc.perform(post("/api/v1/teacher/assignments")
                        .header("Authorization", "Bearer " + teacher1Token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload1))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.maxScore", is(1)));

        // Boundary 100
        String payload100 = String.format(
                "{\"classId\":\"%s\",\"title\":\"Boundary 100\",\"operationType\":\"VERTICAL_ADDITION\",\"maxScore\":100}",
                classroom1.getClassId()
        );
        mockMvc.perform(post("/api/v1/teacher/assignments")
                        .header("Authorization", "Bearer " + teacher1Token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload100))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.maxScore", is(100)));
    }

    @Test
    public void testCreateAssignmentMalformedMaxScoreTypesRejectedWithoutSaving() throws Exception {
        long initialCount = assignmentRepository.count();

        String[] malformedValues = new String[]{"true", "{}", "[]", "\"abc\"", "\"\""};
        for (String malformed : malformedValues) {
            String jsonPayload = String.format(
                    "{\"classId\":\"%s\",\"title\":\"Malformed test\",\"operationType\":\"VERTICAL_ADDITION\",\"maxScore\":%s}",
                    classroom1.getClassId(), malformed
            );

            mockMvc.perform(post("/api/v1/teacher/assignments")
                            .header("Authorization", "Bearer " + teacher1Token)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(jsonPayload))
                    .andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.error.code", is("VALIDATION_ERROR")));
        }

        // Verify zero assignments were saved
        org.junit.jupiter.api.Assertions.assertEquals(initialCount, assignmentRepository.count(),
                "No assignment must be created or saved when maxScore is of malformed type");
    }

    @Test
    public void testCreateAssignmentNumericStringMaxScoreAccepted() throws Exception {
        String payload = String.format(
                "{\"classId\":\"%s\",\"title\":\"String numeric test\",\"operationType\":\"VERTICAL_ADDITION\",\"maxScore\":\"10\"}",
                classroom1.getClassId()
        );

        mockMvc.perform(post("/api/v1/teacher/assignments")
                        .header("Authorization", "Bearer " + teacher1Token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.maxScore", is(10)));
    }

    @Test
    public void testCreateAssignmentPrecisionLossAndExponentOverflowRejectedWithoutSaving() throws Exception {
        long initialCount = assignmentRepository.count();

        String[] invalidValues = new String[]{"100.000000000000001", "1.00000000000000001", "1e309"};
        for (String val : invalidValues) {
            String jsonPayload = String.format(
                    "{\"classId\":\"%s\",\"title\":\"Precision test %s\",\"operationType\":\"VERTICAL_ADDITION\",\"maxScore\":%s}",
                    classroom1.getClassId(), val, val
            );

            mockMvc.perform(post("/api/v1/teacher/assignments")
                            .header("Authorization", "Bearer " + teacher1Token)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(jsonPayload))
                    .andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.error.code", is("VALIDATION_ERROR")));
        }

        // Verify zero assignments were saved
        org.junit.jupiter.api.Assertions.assertEquals(initialCount, assignmentRepository.count(),
                "No assignment must be created or saved when maxScore suffers precision loss or exponent overflow");
    }
}

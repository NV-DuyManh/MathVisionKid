package com.mathvisionkids.api.dashboard;

import com.mathvisionkids.api.assignment.Assignment;
import com.mathvisionkids.api.assignment.AssignmentRepository;
import com.mathvisionkids.api.batch.Batch;
import com.mathvisionkids.api.batch.BatchRepository;
import com.mathvisionkids.api.classroom.Classroom;
import com.mathvisionkids.api.classroom.ClassroomRepository;
import com.mathvisionkids.api.submission.Submission;
import com.mathvisionkids.api.submission.SubmissionRepository;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import jakarta.persistence.EntityManager;
import org.hibernate.SessionFactory;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.junit.jupiter.api.Assertions.assertEquals;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
public class TeacherDashboardControllerTest {

    @Autowired
    private MockMvc mockMvc;

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
    private SubmissionRepository submissionRepository;

    @Autowired
    private DashboardService dashboardService;

    @Autowired
    private EntityManager entityManager;

    private Teacher teacherA;
    private Teacher teacherB;
    private Assignment assignment;
    private Submission approvedSubmission;

    @BeforeEach
    public void setup() {
        teacherA = new Teacher();
        teacherA.setEmail("dashteachera@test.com");
        teacherA.setPasswordHash("pass");
        teacherA.setRole("TEACHER");
        teacherA.setDisplayName("Dashboard Teacher A");
        teacherA = teacherRepository.save(teacherA);

        teacherB = new Teacher();
        teacherB.setEmail("dashteacherb@test.com");
        teacherB.setPasswordHash("pass");
        teacherB.setRole("TEACHER");
        teacherB.setDisplayName("Dashboard Teacher B");
        teacherB = teacherRepository.save(teacherB);

        Student student = new Student();
        student.setEmail("dashstudent@test.com");
        student.setPasswordHash("pass");
        student.setRole("STUDENT");
        student.setGradeLevel(3);
        student.setDisplayName("Dashboard Student");
        student = studentRepository.save(student);

        Classroom classroom = new Classroom();
        classroom.setName("Dashboard Class");
        classroom.setGradeLevel(3);
        classroom.setTeacher(teacherA);
        classroom.getStudents().add(student);
        classroom = classroomRepository.save(classroom);

        assignment = new Assignment();
        assignment.setTitle("Dashboard Assignment");
        assignment.setOperationType("ADDITION");
        assignment.setTeacher(teacherA);
        assignment.setClassroom(classroom);
        assignment.setMaxScore(100);
        assignment = assignmentRepository.save(assignment);

        Batch batch = new Batch();
        batch.setTeacher(teacherA);
        batch.setAssignment(assignment);
        batch.setStatus("PROCESSING");
        batch.setTotalCount(2);
        batch = batchRepository.save(batch);

        Submission sub1 = new Submission();
        sub1.setBatch(batch);
        sub1.setAssignment(assignment);
        sub1.setStudent(student);
        sub1.setStatus("PROPOSED_GRADE");
        sub1.setCreatedAt(Instant.parse("2026-11-01T00:00:00Z"));
        submissionRepository.save(sub1);

        Submission sub2 = new Submission();
        sub2.setBatch(batch);
        sub2.setAssignment(assignment);
        sub2.setStudent(student);
        sub2.setStatus("TEACHER_APPROVED");
        approvedSubmission = submissionRepository.save(sub2);
    }

    @ParameterizedTest
    @CsvSource({
            "2026-11-10T16:59:59.999999Z, 0",
            "2026-11-10T17:00:00Z, 1",
            "2026-11-10T23:15:00Z, 1",
            "2026-11-11T16:59:59.999999Z, 1",
            "2026-11-11T17:00:00Z, 0"
    })
    void countsSubmissionsWithinTheVietnameseCalendarDay(String submittedAt, int expected) {
        entityManager.flush();
        entityManager.createQuery("update Submission s set s.createdAt = :createdAt where s.submissionId = :id")
                .setParameter("createdAt", Instant.parse(submittedAt))
                .setParameter("id", approvedSubmission.getSubmissionId())
                .executeUpdate();
        var dashboard = dashboardService.getDashboard(teacherA.getEmail(), Instant.parse("2026-11-11T16:59:59.999999Z"));
        assertEquals(expected, dashboard.getTodayTotal());
        assertEquals(1, dashboard.getProcessedCount());
    }

    @Test
    void dashboardKeepsQueryCountFixedAndIncludesOlderWorkInTotals() {
        entityManager.flush();
        var statistics = entityManager.getEntityManagerFactory().unwrap(SessionFactory.class).getStatistics();
        boolean wasEnabled = statistics.isStatisticsEnabled();
        statistics.setStatisticsEnabled(true);
        try {
            entityManager.clear();
            long before = statistics.getPrepareStatementCount();
            dashboardService.getDashboard(teacherA.getEmail());
            long shortHistory = statistics.getPrepareStatementCount() - before;

            for (int i = 0; i < 20; i++) {
                Batch batch = new Batch();
                batch.setTeacher(teacherA);
                batch.setAssignment(assignment);
                batch.setStatus("CREATED");
                batchRepository.save(batch);
            }
            entityManager.flush();
            entityManager.clear();

            before = statistics.getPrepareStatementCount();
            var dashboard = dashboardService.getDashboard(teacherA.getEmail());
            long longHistory = statistics.getPrepareStatementCount() - before;
            assertEquals(1, dashboard.getProcessedCount());
            assertEquals(1, dashboard.getReviewRequiredCount());
            assertEquals(10, dashboard.getRecentBatches().size());
            assertEquals(approvedSubmission.getBatch().getBatchId(), dashboard.getNextReviewBatchId());
            assertEquals("CREATED", dashboard.getRecentBatches().getFirst().getStatus());
            assertEquals(shortHistory, longHistory, "Queries for 1 versus 21 batches");
            assertEquals(2, longHistory, "Teacher lookup and dashboard aggregate");
        } finally {
            statistics.setStatisticsEnabled(wasEnabled);
        }
    }

    @Test
    @WithMockUser(username = "dashteachera@test.com", roles = "TEACHER")
    public void testTeacherReceivesOwnDashboard() throws Exception {
        mockMvc.perform(get("/api/v1/teacher/dashboard"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.processedCount").value(1))
                .andExpect(jsonPath("$.reviewRequiredCount").value(1))
                .andExpect(jsonPath("$.recentBatches").isArray())
                .andExpect(jsonPath("$.recentBatches[0].status").value("COMPLETED"))
                .andExpect(jsonPath("$.recentBatches[0].processedCount").value(2))
                .andExpect(jsonPath("$.recentBatches[0].totalCount").value(2));
    }

    @Test
    @WithMockUser(username = "dashteacherb@test.com", roles = "TEACHER")
    public void testTeacherBDoesNotSeeTeacherAData() throws Exception {
        mockMvc.perform(get("/api/v1/teacher/dashboard"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.processedCount").value(0))
                .andExpect(jsonPath("$.reviewRequiredCount").value(0))
                .andExpect(jsonPath("$.nextReviewBatchId").doesNotExist())
                .andExpect(jsonPath("$.recentBatches").isEmpty());
    }

    @Test
    @WithMockUser(username = "dashstudent@test.com", roles = "STUDENT")
    public void testStudentCannotAccessDashboard() throws Exception {
        mockMvc.perform(get("/api/v1/teacher/dashboard"))
                .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(username = "emptyteacher@test.com", roles = "TEACHER")
    public void testEmptyDashboard() throws Exception {
        Teacher emptyTeacher = new Teacher();
        emptyTeacher.setEmail("emptyteacher@test.com");
        emptyTeacher.setPasswordHash("pass");
        emptyTeacher.setRole("TEACHER");
        emptyTeacher.setDisplayName("Empty Teacher");
        teacherRepository.save(emptyTeacher);

        mockMvc.perform(get("/api/v1/teacher/dashboard"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.todayTotal").value(0))
                .andExpect(jsonPath("$.processedCount").value(0))
                .andExpect(jsonPath("$.reviewRequiredCount").value(0))
                .andExpect(jsonPath("$.recentBatches").isEmpty());
    }
}

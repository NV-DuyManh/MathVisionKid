package com.mathvisionkids.api.audit;

import com.mathvisionkids.api.analysis.AnalysisResult;
import com.mathvisionkids.api.analysis.AnalysisResultRepository;
import com.mathvisionkids.api.analysis.TeacherDecision;
import com.mathvisionkids.api.analysis.TeacherDecisionRepository;
import com.mathvisionkids.api.assignment.Assignment;
import com.mathvisionkids.api.assignment.AssignmentRepository;
import com.mathvisionkids.api.batch.Batch;
import com.mathvisionkids.api.batch.BatchRepository;
import com.mathvisionkids.api.classroom.Classroom;
import com.mathvisionkids.api.classroom.ClassroomRepository;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.submission.Submission;
import com.mathvisionkids.api.submission.SubmissionRepository;
import com.mathvisionkids.api.submission.SubmissionService;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Isolated regression tests for manual grading validation and audit persistence (R1 & R7 / PB19).
 * Exercises the production SubmissionService against local H2 test repository instances.
 *
 * POLICY NOTICE: Real data retention duration remains an Owner policy decision (currently PENDING / BLOCKED).
 * The synthetic deletion example uses isolated test fixtures only and does NOT alter production records.
 */
@SpringBootTest
@ActiveProfiles("test")
public class AuditRetentionTest {

    @Autowired
    private SubmissionService submissionService;

    @Autowired
    private AuditEventRepository auditEventRepository;

    @Autowired
    private SubmissionRepository submissionRepository;

    @Autowired
    private AssignmentRepository assignmentRepository;

    @Autowired
    private ClassroomRepository classroomRepository;

    @Autowired
    private TeacherRepository teacherRepository;

    @Autowired
    private BatchRepository batchRepository;

    @Autowired
    private TeacherDecisionRepository teacherDecisionRepository;

    @Autowired
    private AnalysisResultRepository analysisResultRepository;

    private Teacher testTeacher;
    private Teacher otherTeacher;
    private Classroom testClassroom;
    private Assignment testAssignment;
    private Batch testBatch;
    private Submission testSubmission;

    @BeforeEach
    public void setup() {
        tearDown();

        testTeacher = new Teacher();
        testTeacher.setEmail("audit_teacher@example.com");
        testTeacher.setPasswordHash("hash");
        testTeacher.setDisplayName("Audit Teacher");
        testTeacher.setRole("TEACHER");
        testTeacher = teacherRepository.save(testTeacher);

        otherTeacher = new Teacher();
        otherTeacher.setEmail("other_teacher@example.com");
        otherTeacher.setPasswordHash("hash");
        otherTeacher.setDisplayName("Other Teacher");
        otherTeacher.setRole("TEACHER");
        otherTeacher = teacherRepository.save(otherTeacher);

        testClassroom = new Classroom();
        testClassroom.setName("Lớp 4A");
        testClassroom.setGradeLevel(4);
        testClassroom.setTeacher(testTeacher);
        testClassroom = classroomRepository.save(testClassroom);

        testAssignment = new Assignment();
        testAssignment.setTeacher(testTeacher);
        testAssignment.setClassroom(testClassroom);
        testAssignment.setTitle("Bài kiểm tra audit");
        testAssignment.setOperationType("VERTICAL_ADDITION");
        testAssignment.setMaxScore(10);
        testAssignment.setStatus("ACTIVE");
        testAssignment = assignmentRepository.save(testAssignment);

        testBatch = new Batch();
        testBatch.setAssignment(testAssignment);
        testBatch.setTeacher(testTeacher);
        testBatch.setStatus("COMPLETED");
        testBatch = batchRepository.save(testBatch);

        testSubmission = new Submission();
        testSubmission.setAssignment(testAssignment);
        testSubmission.setBatch(testBatch);
        testSubmission.setStatus("PROPOSED_GRADE");
        testSubmission = submissionRepository.save(testSubmission);
    }

    @AfterEach
    public void tearDown() {
        auditEventRepository.deleteAll();
        teacherDecisionRepository.deleteAll();
        analysisResultRepository.deleteAll();
        submissionRepository.deleteAll();
        batchRepository.deleteAll();
        assignmentRepository.deleteAll();
        classroomRepository.deleteAll();
        teacherRepository.deleteAll();
    }

    @Test
    @Transactional
    public void testApproveSubmissionProducesDecisionAndAuditWithMetadata() {
        // Arrange grade proposal in AnalysisResult
        AnalysisResult analysisResult = new AnalysisResult();
        analysisResult.setSubmission(testSubmission);
        analysisResult.setStatus("COMPLETED");
        Map<String, Object> proposal = new HashMap<>();
        proposal.put("suggestedScore", 8);
        proposal.put("maxScore", 10);
        analysisResult.setGradeProposal(proposal);
        analysisResultRepository.save(analysisResult);

        // Act: invoke production approveSubmission
        submissionService.approveSubmission(testTeacher.getEmail(), testSubmission.getSubmissionId());

        // Assert: submission status transitioned to TEACHER_APPROVED
        Submission reloaded = submissionRepository.findById(testSubmission.getSubmissionId()).orElseThrow();
        assertEquals("TEACHER_APPROVED", reloaded.getStatus());

        // Assert: TeacherDecision created and persisted
        TeacherDecision decision = teacherDecisionRepository.findBySubmission_SubmissionId(testSubmission.getSubmissionId()).orElseThrow();
        assertEquals("APPROVED", decision.getType());
        assertEquals(8, decision.getFinalScore());
        assertEquals(testTeacher.getId(), decision.getTeacher().getId());

        // Assert: AuditEvent created with enriched metadata
        List<AuditEvent> events = auditEventRepository.findBySubmission_SubmissionIdOrderByCreatedAtDesc(testSubmission.getSubmissionId());
        assertFalse(events.isEmpty());
        AuditEvent approveEvent = events.get(0);
        assertEquals("TEACHER_APPROVED", approveEvent.getEventType());
        assertEquals(testTeacher.getId(), approveEvent.getUser().getId());
        assertNotNull(approveEvent.getMetadata());
        assertEquals(8, approveEvent.getMetadata().get("finalScore"));
        assertEquals("APPROVED", approveEvent.getMetadata().get("decisionType"));
        assertEquals(testSubmission.getSubmissionId().toString(), approveEvent.getMetadata().get("submissionId"));
    }

    @Test
    @Transactional
    public void testOverrideSubmissionProducesDecisionAndAuditWithMetadata() {
        // Act: invoke production overrideSubmission with valid score and reason
        Map<String, Object> overrideData = new HashMap<>();
        overrideData.put("score", 9);
        overrideData.put("reason", "Chấm lại bước đặt tính");
        submissionService.overrideSubmission(testTeacher.getEmail(), testSubmission.getSubmissionId(), overrideData);

        // Assert: status transitioned to TEACHER_OVERRIDDEN
        Submission reloaded = submissionRepository.findById(testSubmission.getSubmissionId()).orElseThrow();
        assertEquals("TEACHER_OVERRIDDEN", reloaded.getStatus());

        // Assert: decision persisted
        TeacherDecision decision = teacherDecisionRepository.findBySubmission_SubmissionId(testSubmission.getSubmissionId()).orElseThrow();
        assertEquals("OVERRIDDEN", decision.getType());
        assertEquals(9, decision.getFinalScore());
        assertEquals("Chấm lại bước đặt tính", decision.getReason());
        assertEquals(testTeacher.getId(), decision.getTeacher().getId());

        // Assert: audit event persisted with enriched metadata
        List<AuditEvent> events = auditEventRepository.findBySubmission_SubmissionIdOrderByCreatedAtDesc(testSubmission.getSubmissionId());
        assertFalse(events.isEmpty());
        AuditEvent overrideEvent = events.get(0);
        assertEquals("TEACHER_OVERRIDDEN", overrideEvent.getEventType());
        assertEquals(testTeacher.getId(), overrideEvent.getUser().getId());
        assertEquals(9, overrideEvent.getMetadata().get("finalScore"));
        assertEquals("OVERRIDDEN", overrideEvent.getMetadata().get("decisionType"));
        assertEquals("Chấm lại bước đặt tính", overrideEvent.getMetadata().get("reason"));
        assertEquals(testSubmission.getSubmissionId().toString(), overrideEvent.getMetadata().get("submissionId"));
    }

    @Test
    @Transactional
    public void testOverrideRejectsInvalidScoresWithoutModifyingStateOrSavingAudit() {
        List<Map<String, Object>> invalidPayloads = List.of(
                Map.of("score", -1, "reason", "Negative score"),
                Map.of("score", 101, "reason", "Exceeds max score"),
                Map.of("score", "invalid_string", "reason", "Non-numeric string"),
                Map.of("reason", "Missing score"),
                Map.of("score", 5, "reason", 123),
                Map.of("score", 5, "reason", true),
                Map.of("score", 5, "reason", Map.of()),
                Map.of("score", 5, "reason", "   ")
        );

        for (Map<String, Object> payload : invalidPayloads) {
            assertThrows(ApiException.class, () -> {
                submissionService.overrideSubmission(testTeacher.getEmail(), testSubmission.getSubmissionId(), payload);
            }, "Expected rejection for payload: " + payload);

            // Verify submission status was NOT mutated
            Submission current = submissionRepository.findById(testSubmission.getSubmissionId()).orElseThrow();
            assertEquals("PROPOSED_GRADE", current.getStatus(), "Status must not change on validation failure");

            // Verify no decisions or audit events were persisted
            assertTrue(teacherDecisionRepository.findBySubmission_SubmissionId(testSubmission.getSubmissionId()).isEmpty(),
                    "No decision should be saved on rejection");
            assertTrue(auditEventRepository.findBySubmission_SubmissionIdOrderByCreatedAtDesc(testSubmission.getSubmissionId()).isEmpty(),
                    "No audit event should be saved on rejection");
        }
    }

    @Test
    @Transactional
    public void testOverrideRejectsWrongOwnerAndWrongState() {
        // 1. Wrong owner rejection
        Map<String, Object> validPayload = Map.of("score", 7, "reason", "Valid reason");
        assertThrows(ApiException.class, () -> {
            submissionService.overrideSubmission(otherTeacher.getEmail(), testSubmission.getSubmissionId(), validPayload);
        });
        Submission current = submissionRepository.findById(testSubmission.getSubmissionId()).orElseThrow();
        assertEquals("PROPOSED_GRADE", current.getStatus());
        assertTrue(teacherDecisionRepository.findBySubmission_SubmissionId(testSubmission.getSubmissionId()).isEmpty());

        // 2. Wrong state rejection (e.g. FAILED)
        testSubmission.setStatus("FAILED");
        submissionRepository.save(testSubmission);

        assertThrows(ApiException.class, () -> {
            submissionService.overrideSubmission(testTeacher.getEmail(), testSubmission.getSubmissionId(), validPayload);
        });
        current = submissionRepository.findById(testSubmission.getSubmissionId()).orElseThrow();
        assertEquals("FAILED", current.getStatus());
    }

    @Test
    @Transactional
    public void testOverrideAcceptsBoundaryScoresAndValidRoundingAndAliases() {
        // Legitimate zero
        submissionService.overrideSubmission(testTeacher.getEmail(), testSubmission.getSubmissionId(),
                Map.of("score", 0, "reason", "Zero points"));
        TeacherDecision d0 = teacherDecisionRepository.findBySubmission_SubmissionId(testSubmission.getSubmissionId()).orElseThrow();
        assertEquals(0, d0.getFinalScore());

        // Reset for next test
        teacherDecisionRepository.deleteAll();
        auditEventRepository.deleteAll();
        testSubmission.setStatus("PROPOSED_GRADE");
        submissionRepository.save(testSubmission);

        // Max boundary
        submissionService.overrideSubmission(testTeacher.getEmail(), testSubmission.getSubmissionId(),
                Map.of("score", 10, "reason", "Full score"));
        TeacherDecision d10 = teacherDecisionRepository.findBySubmission_SubmissionId(testSubmission.getSubmissionId()).orElseThrow();
        assertEquals(10, d10.getFinalScore());

        // Reset for next test
        teacherDecisionRepository.deleteAll();
        auditEventRepository.deleteAll();
        testSubmission.setStatus("PROPOSED_GRADE");
        submissionRepository.save(testSubmission);

        // Valid rounding (8.6 -> 9)
        submissionService.overrideSubmission(testTeacher.getEmail(), testSubmission.getSubmissionId(),
                Map.of("score", 8.6, "reason", "Rounded score"));
        TeacherDecision dRound = teacherDecisionRepository.findBySubmission_SubmissionId(testSubmission.getSubmissionId()).orElseThrow();
        assertEquals(9, dRound.getFinalScore());

        // Reset for next test
        teacherDecisionRepository.deleteAll();
        auditEventRepository.deleteAll();
        testSubmission.setStatus("PROPOSED_GRADE");
        submissionRepository.save(testSubmission);

        // Legacy alias "finalScore"
        submissionService.overrideSubmission(testTeacher.getEmail(), testSubmission.getSubmissionId(),
                Map.of("finalScore", 7, "reason", "Legacy alias"));
        TeacherDecision dAlias = teacherDecisionRepository.findBySubmission_SubmissionId(testSubmission.getSubmissionId()).orElseThrow();
        assertEquals(7, dAlias.getFinalScore());
    }

    @Test
    @Transactional
    public void testSyntheticRetentionPurgeWorkflow() {
        // Isolated synthetic demonstration of cutoff calculation.
        // NOTE: Real retention duration is subject to Owner policy decision (currently PENDING / BLOCKED).
        Instant now = Instant.now();

        AuditEvent oldEvent = new AuditEvent();
        oldEvent.setSubmission(testSubmission);
        oldEvent.setUser(testTeacher);
        oldEvent.setEventType("SYNTHETIC_OLD");
        oldEvent.setCreatedAt(now.minus(120, ChronoUnit.DAYS)); // 120 days old
        oldEvent.setMetadata(Map.of("synthetic", true));
        auditEventRepository.save(oldEvent);

        AuditEvent recentEvent = new AuditEvent();
        recentEvent.setSubmission(testSubmission);
        recentEvent.setUser(testTeacher);
        recentEvent.setEventType("SYNTHETIC_RECENT");
        recentEvent.setCreatedAt(now.minus(10, ChronoUnit.DAYS)); // 10 days old
        recentEvent.setMetadata(Map.of("synthetic", true));
        auditEventRepository.save(recentEvent);

        Instant cutoff = now.minus(90, ChronoUnit.DAYS);
        List<AuditEvent> allEvents = auditEventRepository.findAll();
        List<AuditEvent> expiredSynthetic = allEvents.stream()
                .filter(e -> e.getCreatedAt().isBefore(cutoff) && "SYNTHETIC_OLD".equals(e.getEventType()))
                .toList();

        assertEquals(1, expiredSynthetic.size());
        assertEquals("SYNTHETIC_OLD", expiredSynthetic.get(0).getEventType());

        // Purge synthetic demo items only
        auditEventRepository.deleteAll(expiredSynthetic);

        List<AuditEvent> remaining = auditEventRepository.findAll();
        assertTrue(remaining.stream().noneMatch(e -> "SYNTHETIC_OLD".equals(e.getEventType())));
        assertTrue(remaining.stream().anyMatch(e -> "SYNTHETIC_RECENT".equals(e.getEventType())));
    }
}

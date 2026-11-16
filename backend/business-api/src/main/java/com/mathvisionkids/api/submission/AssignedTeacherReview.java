package com.mathvisionkids.api.submission;

import com.mathvisionkids.api.assignment.AssignmentRepository;
import com.mathvisionkids.api.classroom.ClassroomRepository;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.TeacherRepository;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AssignedTeacherReview {
    public record ReturnImage(int imageVersion, String reason, String instruction) {}
    public record Grade(UUID requestId, int imageVersion, boolean readable, boolean matchesAssignment,
                        com.fasterxml.jackson.databind.JsonNode score, String feedback) {}
    private record ReviewTarget(Submission submission, UUID teacherId, int maxScore, int imageVersion) {}
    public record Detail(UUID submissionId, UUID assignmentId, String studentName, String prompt,
                         String status, int maxScore, int imageVersion, Integer score, String feedback) {}
    record ImageReference(String key, String contentType) {}

    public record RecipientStatus(UUID studentId, String studentName, UUID submissionId, String status) {}

    @Transactional(readOnly = true)
    public java.util.List<RecipientStatus> queue(String email, UUID assignmentId) {
        var teacher = teachers.findByEmail(email).filter(t -> Boolean.TRUE.equals(t.getActive()))
                .orElseThrow(AssignedTeacherReview::unavailable);
        var assignment = assignments.findById(assignmentId)
                .filter(a -> "PUBLISHED".equals(a.getStatus())
                        && a.getClassroom().getTeacher().getId().equals(teacher.getId()))
                .orElseThrow(AssignedTeacherReview::unavailable);
        return jdbc.query("""
                SELECT r.student_id, pupil.display_name, s.submission_id,
                       CASE WHEN EXISTS (
                           SELECT 1 FROM assigned_upload_attempts u WHERE u.submission_id = s.submission_id
                           AND u.state = 'OPEN'
                           AND (u.expires_at > clock_timestamp() OR u.stored_digest IS NOT NULL)
                       ) AND s.status <> 'GRADE_RELEASED' THEN 'UPLOADING'
                       ELSE COALESCE(s.status, 'AWAITING_IMAGE') END AS review_status
                FROM assignments a JOIN classrooms c ON c.class_id = a.class_id
                JOIN assignment_publications p ON p.assignment_id = a.assignment_id
                JOIN assignment_recipients r ON r.publication_id = p.publication_id
                JOIN users pupil ON pupil.id = r.student_id
                LEFT JOIN submissions s ON s.publication_id = p.publication_id AND s.student_id = r.student_id
                WHERE a.assignment_id = ? AND c.teacher_id = ?
                ORDER BY pupil.display_name, r.student_id
                """, (row, index) -> new RecipientStatus(row.getObject(1, UUID.class), row.getString(2),
                row.getObject(3, UUID.class), row.getString(4)), assignment.getAssignmentId(), teacher.getId());
    }

    public Detail detail(String email, UUID submissionId) {
        var rows = jdbc.query("""
                SELECT s.submission_id, a.assignment_id, pupil.display_name, a.prompt, s.status, a.max_score,
                       (SELECT COALESCE(MAX(i.image_version), 0) FROM submission_images i
                        WHERE i.submission_id = s.submission_id) AS image_version, d.final_score, d.reason
                FROM submissions s JOIN assignments a ON a.assignment_id = s.assignment_id
                JOIN classrooms c ON c.class_id = a.class_id
                JOIN users owner ON owner.id = c.teacher_id AND owner.active = TRUE
                JOIN users pupil ON pupil.id = s.student_id
                LEFT JOIN teacher_decisions d ON d.submission_id = s.submission_id
                    AND s.status = 'GRADE_RELEASED' AND d.type = 'ASSIGNED_RELEASE'
                WHERE s.submission_id = ? AND s.source = 'ASSIGNED_WEB' AND owner.email = ?
                """, (row, index) -> new Detail(row.getObject(1, UUID.class), row.getObject(2, UUID.class),
                row.getString(3), row.getString(4), row.getString(5), row.getInt(6), row.getInt(7),
                row.getObject(8, Integer.class), row.getString(9)), submissionId, email);
        if (rows.isEmpty()) throw unavailable();
        return rows.getFirst();
    }

    ImageReference image(String email, UUID submissionId, int version) {
        var rows = jdbc.query("""
                SELECT i.file_path, i.content_type FROM submission_images i
                JOIN submissions s ON s.submission_id = i.submission_id
                JOIN assignments a ON a.assignment_id = s.assignment_id
                JOIN classrooms c ON c.class_id = a.class_id
                JOIN users owner ON owner.id = c.teacher_id AND owner.active = TRUE
                WHERE s.submission_id = ? AND s.source = 'ASSIGNED_WEB' AND owner.email = ?
                  AND i.image_version = ?
                  AND i.image_version = (SELECT MAX(current_image.image_version) FROM submission_images current_image
                                         WHERE current_image.submission_id = s.submission_id)
                """, (row, index) -> new ImageReference(row.getString(1), row.getString(2)), submissionId, email, version);
        if (rows.isEmpty()) throw unavailable();
        return rows.getFirst();
    }

    private final JdbcTemplate jdbc;
    private final ClassroomRepository classrooms;
    private final AssignmentRepository assignments;
    private final SubmissionRepository submissions;
    private final TeacherRepository teachers;

    public AssignedTeacherReview(JdbcTemplate jdbc, ClassroomRepository classrooms, AssignmentRepository assignments,
            SubmissionRepository submissions, TeacherRepository teachers) {
        this.jdbc = jdbc;
        this.classrooms = classrooms;
        this.assignments = assignments;
        this.submissions = submissions;
        this.teachers = teachers;
    }

    @Transactional
    public void returnImage(String email, UUID submissionId, ReturnImage request) {
        if (request.imageVersion() < 1
                || !("UNREADABLE".equals(request.reason()) || "WRONG_ASSIGNMENT".equals(request.reason()))
                || request.instruction() == null || request.instruction().isBlank() || request.instruction().length() > 500) {
            throw new ApiException("RETURN_INVALID", "Hãy chọn lý do và ghi hướng dẫn chụp lại.", HttpStatus.BAD_REQUEST);
        }
        ReviewTarget target = lockTarget(email, submissionId);
        requireReviewable(target, request.imageVersion());
        jdbc.update("""
                INSERT INTO assigned_image_returns(submission_id, image_version, teacher_id, reason, instruction)
                VALUES (?, ?, ?, ?, ?)
                """, submissionId, target.imageVersion(), target.teacherId(), request.reason(), request.instruction().strip());
        target.submission().setStatus("RETAKE_REQUESTED");
    }

    @Transactional
    public void releaseGrade(String email, UUID submissionId, Grade request) {
        ReviewTarget target = lockTarget(email, submissionId);
        String feedback = request.feedback() == null ? "" : request.feedback().strip();
        if (request.requestId() == null || !request.readable() || !request.matchesAssignment()
                || request.score() == null || !request.score().isIntegralNumber() || !request.score().canConvertToInt()
                || request.score().intValue() < 0 || request.score().intValue() > target.maxScore()
                || request.imageVersion() < 1 || feedback.length() > 2000) {
            throw new ApiException("GRADE_INVALID", "Hãy kiểm tra ảnh, đề bài và điểm trước khi trả bài.", HttpStatus.BAD_REQUEST);
        }
        int score = request.score().intValue();
        if ("GRADE_RELEASED".equals(target.submission().getStatus())) {
            boolean matches = Boolean.TRUE.equals(jdbc.queryForObject("""
                    SELECT EXISTS(SELECT 1 FROM teacher_decisions WHERE submission_id = ?
                        AND assigned_request_id = ? AND assigned_image_version = ?
                        AND final_score = ? AND reason = ?)
                    """, Boolean.class, submissionId, request.requestId(), request.imageVersion(), score, feedback));
            if (matches) return;
            throw conflict();
        }
        requireReviewable(target, request.imageVersion());
        jdbc.update("""
                INSERT INTO teacher_decisions(decision_id, submission_id, teacher_id, type,
                    final_score, reason, assigned_request_id, assigned_image_version)
                VALUES (?, ?, ?, 'ASSIGNED_RELEASE', ?, ?, ?, ?)
                """, UUID.randomUUID(), submissionId, target.teacherId(), score, feedback,
                request.requestId(), request.imageVersion());
        jdbc.update("""
                UPDATE assigned_upload_attempts SET state = 'EXPIRED',
                    cleanup_after = CURRENT_TIMESTAMP + INTERVAL '15 minutes'
                WHERE submission_id = ? AND state = 'OPEN'
                """, submissionId);
        target.submission().setStatus("GRADE_RELEASED");
    }

    private ReviewTarget lockTarget(String email, UUID submissionId) {
        var teacher = teachers.findByEmail(email).filter(t -> Boolean.TRUE.equals(t.getActive()))
                .orElseThrow(AssignedTeacherReview::unavailable);
        var ids = jdbc.query("""
                SELECT s.assignment_id, a.class_id FROM submissions s JOIN assignments a ON a.assignment_id = s.assignment_id
                WHERE s.submission_id = ? AND s.source = 'ASSIGNED_WEB'
                """, (row, index) -> new UUID[] {row.getObject(1, UUID.class), row.getObject(2, UUID.class)}, submissionId);
        if (ids.isEmpty()) throw unavailable();
        UUID assignmentId = ids.getFirst()[0], classId = ids.getFirst()[1];
        var classroom = classrooms.findForUpdate(classId).orElseThrow(AssignedTeacherReview::unavailable);
        if (!classroom.getTeacher().getId().equals(teacher.getId())) throw unavailable();
        var assignment = assignments.findForUpdate(assignmentId).orElseThrow(AssignedTeacherReview::unavailable);
        var submission = submissions.findForUpdate(submissionId).filter(Submission::isAssignedWeb)
                .orElseThrow(AssignedTeacherReview::unavailable);
        int version = jdbc.queryForObject(
                "SELECT COALESCE(MAX(image_version), 0) FROM submission_images WHERE submission_id = ?", Integer.class, submissionId);
        return new ReviewTarget(submission, teacher.getId(), assignment.getMaxScore(), version);
    }

    private static void requireReviewable(ReviewTarget target, int expectedVersion) {
        if (target.imageVersion() != expectedVersion || !"AWAITING_REVIEW".equals(target.submission().getStatus())) {
            throw conflict();
        }
    }

    private static ApiException conflict() {
        return new ApiException("REVIEW_CONFLICT", "Bài nộp đã thay đổi. Hãy tải lại ảnh hiện hành.", HttpStatus.CONFLICT);
    }

    private static ApiException unavailable() {
        return new ApiException("NOT_FOUND", "Không tìm thấy bài nộp.", HttpStatus.NOT_FOUND);
    }
}

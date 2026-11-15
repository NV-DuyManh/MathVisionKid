package com.mathvisionkids.api.submission;

import com.mathvisionkids.api.assignment.AssignmentPublicationRepository;
import com.mathvisionkids.api.assignment.AssignmentRecipientRepository;
import com.mathvisionkids.api.assignment.AssignmentRepository;
import com.mathvisionkids.api.classroom.ClassroomRepository;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.StudentRepository;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AssignedUploadReservation {
    record Attempt(UUID id, UUID submissionId, String objectKey, String digest, int expectedVersion, String state) {}
    record Recovery(String email, UUID assignmentId, UUID requestId, Attempt attempt,
                    String storedDigest, String contentType, int size) {}
    public record Status(UUID submissionId, String status, int imageVersion, Integer score, String feedback,
                         String retakeReason, String retakeInstruction) {}
    record StudentImage(String key, String contentType, int version) {}

    private final AssignmentRepository assignments;
    private final ClassroomRepository classrooms;
    private final AssignmentPublicationRepository publications;
    private final AssignmentRecipientRepository recipients;
    private final StudentRepository students;
    private final SubmissionRepository submissions;
    private final JdbcTemplate jdbc;

    public AssignedUploadReservation(AssignmentRepository assignments, ClassroomRepository classrooms,
            AssignmentPublicationRepository publications, AssignmentRecipientRepository recipients,
            StudentRepository students, SubmissionRepository submissions, JdbcTemplate jdbc) {
        this.assignments = assignments;
        this.classrooms = classrooms;
        this.publications = publications;
        this.recipients = recipients;
        this.students = students;
        this.submissions = submissions;
        this.jdbc = jdbc;
    }

    @Transactional
    public Attempt reserve(String email, UUID assignmentId, UUID requestId, int expectedVersion, String digest,
            String storedDigest) {
        if (requestId == null || expectedVersion < 0 || digest == null || !digest.matches("[0-9a-f]{64}")
                || storedDigest == null || !storedDigest.matches("[0-9a-f]{64}")) {
            throw new ApiException("UPLOAD_INVALID", "Thông tin gửi ảnh chưa hợp lệ.", HttpStatus.BAD_REQUEST);
        }
        var student = students.findByEmail(email).filter(s -> Boolean.TRUE.equals(s.getActive()))
                .orElseThrow(AssignedUploadReservation::unavailable);
        UUID classId = assignments.findClassId(assignmentId).orElseThrow(AssignedUploadReservation::unavailable);
        var classroom = classrooms.findForUpdate(classId).orElseThrow(AssignedUploadReservation::unavailable);
        if (classroom.getStudents().stream().noneMatch(s -> s.getId().equals(student.getId()))) throw unavailable();
        var assignment = assignments.findForUpdate(assignmentId).filter(a -> "PUBLISHED".equals(a.getStatus()))
                .orElseThrow(AssignedUploadReservation::unavailable);
        UUID publicationId = publications.findByAssignmentId(assignmentId)
                .orElseThrow(AssignedUploadReservation::unavailable).getPublicationId();
        if (!recipients.existsById(new com.mathvisionkids.api.assignment.AssignmentRecipient.Key(publicationId, student.getId()))) {
            throw unavailable();
        }

        var submission = submissions.findAssignedForUpdate(publicationId, student.getId()).orElseGet(() -> {
            var created = new Submission();
            created.setSource(Submission.Source.ASSIGNED_WEB);
            created.setPublicationId(publicationId);
            created.setAssignment(assignment);
            created.setStudent(student);
            created.setStatus("AWAITING_IMAGE");
            return submissions.saveAndFlush(created);
        });
        UUID submissionId = submission.getSubmissionId();
        jdbc.update("""
                UPDATE assigned_upload_attempts SET state = 'EXPIRED',
                    cleanup_after = CURRENT_TIMESTAMP + INTERVAL '15 minutes'
                WHERE submission_id = ? AND state = 'OPEN' AND expires_at <= clock_timestamp()
                  AND stored_digest IS NULL
                """, submissionId);
        var prior = jdbc.query("""
                SELECT attempt_id, object_key, digest, expected_image_version, state
                FROM assigned_upload_attempts WHERE submission_id = ? AND request_id = ? FOR UPDATE
                """, (row, index) -> new Attempt(row.getObject("attempt_id", UUID.class), submissionId,
                row.getString("object_key"), row.getString("digest"), row.getInt("expected_image_version"),
                row.getString("state")), submissionId, requestId);
        if (!prior.isEmpty()) {
            Attempt attempt = prior.getFirst();
            if (!attempt.digest().equals(digest) || attempt.expectedVersion() != expectedVersion) throw conflict();
            if ("OPEN".equals(attempt.state()) && "GRADE_RELEASED".equals(submission.getStatus())) throw conflict();
            return attempt;
        }
        int currentVersion = jdbc.queryForObject(
                "SELECT COALESCE(MAX(image_version), 0) FROM submission_images WHERE submission_id = ?",
                Integer.class, submissionId);
        if (currentVersion != expectedVersion || !java.util.Set.of("AWAITING_IMAGE", "AWAITING_REVIEW", "RETAKE_REQUESTED")
                .contains(submission.getStatus())) throw conflict();
        if (Boolean.TRUE.equals(jdbc.queryForObject(
                "SELECT EXISTS(SELECT 1 FROM assigned_upload_attempts WHERE submission_id = ? AND state = 'OPEN')",
                Boolean.class, submissionId))) throw conflict();

        UUID attemptId = UUID.randomUUID();
        String objectKey = "assigned-work/" + UUID.randomUUID() + "/" + storedDigest;
        jdbc.update("""
                INSERT INTO assigned_upload_attempts(attempt_id, submission_id, request_id, expected_image_version,
                    digest, object_key, state, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, 'OPEN', clock_timestamp() + INTERVAL '15 minutes')
                """, attemptId, submissionId, requestId, expectedVersion, digest, objectKey);
        return new Attempt(attemptId, submissionId, objectKey, digest, expectedVersion, "OPEN");
    }

    @Transactional(readOnly = true)
    public java.util.Optional<Attempt> confirmedReplay(String email, UUID assignmentId, UUID requestId,
            int expectedVersion, String digest) {
        var attempts = jdbc.query("""
                SELECT attempt.attempt_id, s.submission_id, attempt.object_key,
                       attempt.digest, attempt.expected_image_version
                FROM assigned_upload_attempts attempt
                JOIN submissions s ON s.submission_id = attempt.submission_id
                JOIN assignments a ON a.assignment_id = s.assignment_id
                JOIN classroom_students m ON m.class_id = a.class_id AND m.student_id = s.student_id
                JOIN users u ON u.id = s.student_id AND u.active = TRUE
                WHERE a.assignment_id = ? AND u.email = ? AND a.status = 'PUBLISHED'
                  AND s.source = 'ASSIGNED_WEB' AND attempt.request_id = ? AND attempt.state = 'CONFIRMED'
                """, (row, index) -> new Attempt(row.getObject(1, UUID.class), row.getObject(2, UUID.class),
                row.getString(3), row.getString(4), row.getInt(5), "CONFIRMED"), assignmentId, email, requestId);
        if (attempts.isEmpty()) return java.util.Optional.empty();
        var attempt = attempts.getFirst();
        if (attempt.expectedVersion() != expectedVersion || !attempt.digest().equals(digest)) throw conflict();
        return java.util.Optional.of(attempt);
    }

    @Transactional(readOnly = true)
    public StudentImage currentImage(String email, UUID assignmentId) {
        var images = jdbc.query("""
                SELECT i.file_path, i.content_type, i.image_version
                FROM assignments a
                JOIN assignment_publications p ON p.assignment_id = a.assignment_id
                JOIN submissions s ON s.publication_id = p.publication_id AND s.source = 'ASSIGNED_WEB'
                JOIN classroom_students m ON m.class_id = a.class_id AND m.student_id = s.student_id
                JOIN users u ON u.id = s.student_id AND u.active = TRUE
                JOIN submission_images i ON i.submission_id = s.submission_id AND i.image_version IS NOT NULL
                WHERE a.assignment_id = ? AND a.status = 'PUBLISHED' AND u.email = ?
                ORDER BY i.image_version DESC LIMIT 1
                """, (row, index) -> new StudentImage(row.getString(1), row.getString(2), row.getInt(3)),
                assignmentId, email);
        if (images.isEmpty()) throw unavailable();
        return images.getFirst();
    }

    @Transactional(readOnly = true)
    public Status status(String email, UUID assignmentId) {
        var rows = jdbc.query("""
                SELECT s.submission_id, s.status,
                       EXISTS (SELECT 1 FROM assigned_upload_attempts pending
                               WHERE pending.submission_id = s.submission_id AND pending.state = 'OPEN'
                                 AND pending.expires_at > clock_timestamp()) AS uploading,
                       (SELECT COALESCE(MAX(i.image_version), 0) FROM submission_images i
                        WHERE i.submission_id = s.submission_id) AS image_version,
                       d.final_score, d.reason, retake.reason AS retake_reason, retake.instruction
                FROM assignments a JOIN assignment_publications p ON p.assignment_id = a.assignment_id
                JOIN assignment_recipients r ON r.publication_id = p.publication_id
                JOIN classroom_students m ON m.class_id = a.class_id AND m.student_id = r.student_id
                JOIN users u ON u.id = r.student_id AND u.active = TRUE
                LEFT JOIN submissions s ON s.publication_id = p.publication_id AND s.student_id = r.student_id
                LEFT JOIN teacher_decisions d ON d.submission_id = s.submission_id AND s.status = 'GRADE_RELEASED'
                LEFT JOIN assigned_image_returns retake ON retake.submission_id = s.submission_id
                    AND s.status = 'RETAKE_REQUESTED'
                    AND retake.image_version = (SELECT MAX(i.image_version) FROM submission_images i
                                                WHERE i.submission_id = s.submission_id)
                WHERE a.assignment_id = ? AND a.status = 'PUBLISHED' AND u.email = ?
                """, (row, index) -> {
            UUID submissionId = row.getObject("submission_id", UUID.class);
            String status = submissionId == null ? "AWAITING_IMAGE" : row.getString("status");
            if (!"GRADE_RELEASED".equals(status) && row.getBoolean("uploading")) status = "UPLOADING";
            return new Status(submissionId, status,
                    row.getInt("image_version"), row.getObject("final_score", Integer.class), row.getString("reason"),
                    row.getString("retake_reason"), row.getString("instruction"));
        }, assignmentId, email);
        if (rows.isEmpty()) throw unavailable();
        return rows.getFirst();
    }

    @Transactional
    public void recordPreparedImage(Attempt attempt, AssignedWebImage image) {
        int changed = jdbc.update("""
                UPDATE assigned_upload_attempts
                SET stored_digest = ?, stored_content_type = ?, stored_size = ?,
                    recover_after = COALESCE(recover_after, clock_timestamp() + INTERVAL '1 minute')
                WHERE attempt_id = ? AND state = 'OPEN' AND expires_at > clock_timestamp()
                  AND (stored_digest IS NULL OR (stored_digest = ? AND stored_content_type = ? AND stored_size = ?))
                """, image.storedDigest(), image.contentType(), image.bytes().length, attempt.id(),
                image.storedDigest(), image.contentType(), image.bytes().length);
        if (changed != 1) throw conflict();
    }

    public java.util.List<Recovery> recoveryCandidates() {
        return jdbc.query("""
                WITH claimed AS (
                    UPDATE assigned_upload_attempts SET recover_after = clock_timestamp() + INTERVAL '1 minute'
                    WHERE attempt_id IN (
                        SELECT attempt_id FROM assigned_upload_attempts
                        WHERE state = 'OPEN' AND recover_after <= clock_timestamp()
                          AND stored_digest IS NOT NULL
                          AND expires_at <= clock_timestamp()
                        ORDER BY recover_after LIMIT 50 FOR UPDATE SKIP LOCKED
                    )
                    RETURNING *
                )
                SELECT u.email, s.assignment_id, a.request_id, a.attempt_id, a.submission_id,
                       a.object_key, a.digest, a.expected_image_version, a.state,
                       a.stored_digest, a.stored_content_type, a.stored_size
                FROM claimed a
                JOIN submissions s ON s.submission_id = a.submission_id
                JOIN users u ON u.id = s.student_id
                """, (row, index) -> new Recovery(row.getString(1), row.getObject(2, UUID.class),
                row.getObject(3, UUID.class), new Attempt(row.getObject(4, UUID.class),
                row.getObject(5, UUID.class), row.getString(6), row.getString(7), row.getInt(8),
                row.getString(9)), row.getString(10), row.getString(11), row.getInt(12)));
    }

    @Transactional
    public int confirm(String email, UUID assignmentId, UUID requestId, Attempt stored, AssignedWebImage image) {
        return confirm(email, assignmentId, requestId, stored, image, false);
    }

    @Transactional
    public int confirmRecovered(String email, UUID assignmentId, UUID requestId, Attempt stored,
            AssignedWebImage image) {
        return confirm(email, assignmentId, requestId, stored, image, true);
    }

    private int confirm(String email, UUID assignmentId, UUID requestId, Attempt stored, AssignedWebImage image,
            boolean recovery) {
        Attempt current = reserve(email, assignmentId, requestId, stored.expectedVersion(), image.inputDigest(),
                image.storedDigest());
        if (!current.equals(stored) && !"CONFIRMED".equals(current.state())) throw conflict();
        if ("CONFIRMED".equals(current.state())) return current.expectedVersion() + 1;
        if (!"OPEN".equals(current.state())) throw conflict();
        int version = current.expectedVersion() + 1;
        int changed = jdbc.update("""
                UPDATE assigned_upload_attempts SET state = 'CONFIRMED'
                WHERE attempt_id = ? AND state = 'OPEN'
                  AND (? OR expires_at > clock_timestamp())
                  AND stored_digest = ? AND stored_content_type = ? AND stored_size = ?
                """, current.id(), recovery, image.storedDigest(), image.contentType(), image.bytes().length);
        if (changed != 1) throw conflict();
        changed = jdbc.update("""
                UPDATE submissions SET status = 'AWAITING_REVIEW'
                WHERE submission_id = ? AND status IN ('AWAITING_IMAGE', 'AWAITING_REVIEW', 'RETAKE_REQUESTED')
                AND ? = (SELECT COALESCE(MAX(image_version), 0) FROM submission_images WHERE submission_id = ?)
                """, current.submissionId(), current.expectedVersion(), current.submissionId());
        if (changed != 1) throw conflict();
        jdbc.update("""
                INSERT INTO submission_images(image_id, submission_id, file_path, content_type, file_size, source, image_version)
                VALUES (?, ?, ?, ?, ?, 'ASSIGNED_WEB', ?)
                """, UUID.randomUUID(), current.submissionId(), current.objectKey(), image.contentType(),
                image.bytes().length, version);
        return version;
    }

    private static ApiException unavailable() {
        return new ApiException("NOT_FOUND", "Không tìm thấy bài được giao.", HttpStatus.NOT_FOUND);
    }

    private static ApiException conflict() {
        return new ApiException("UPLOAD_CONFLICT", "Bài đã thay đổi hoặc đang gửi ảnh. Em hãy tải lại.", HttpStatus.CONFLICT);
    }
}

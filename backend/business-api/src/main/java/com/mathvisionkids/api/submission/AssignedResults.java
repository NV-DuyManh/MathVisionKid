package com.mathvisionkids.api.submission;

import com.mathvisionkids.api.common.ApiException;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

/** Private read models for published assigned work; never loads images or writes grades. */
@Service
class AssignedResults {
    enum Status {
        AWAITING_IMAGE, UPLOADING, AWAITING_REVIEW, RETAKE_REQUESTED, GRADE_RELEASED
    }

    enum WorkFilter { ALL, PENDING, RETAKE, MISSING, RELEASED }
    private static final int PAGE_SIZE = 20;

    record Recipient(UUID studentId, String studentName, boolean member, boolean activeMember,
                     Status status, UUID submissionId, Integer score) {}
    record Publication(UUID assignmentId, UUID classId, String className, String teacherName, String title,
                       Instant publishedAt, int maxScore, int recipientCount, Map<Status, Integer> counts,
                       List<Recipient> recipients) {}
    record AssignmentWork(UUID assignmentId, UUID classId, String className, String title, Instant publishedAt,
                          int pendingSubmissions, int retakeRecipients, int missingRecipients, int releasedSubmissions) {}
    record ActionCenter(int classCount, int pendingSubmissions, int retakeRecipients, int assignmentsWithMissingWork,
                        int releasedSubmissions, int matchingAssignments, int page, int pageSize,
                        List<AssignmentWork> assignments) {}
    record HistoryItem(UUID assignmentId, String title, String className, String teacherName, Instant publishedAt,
                       int maxScore, Status status, Integer score) {}

    private static final String STATUS_SQL = """
            CASE
                WHEN s.status = 'GRADE_RELEASED' THEN 'GRADE_RELEASED'
                WHEN EXISTS (
                    SELECT 1 FROM assigned_upload_attempts u
                    WHERE u.submission_id = s.submission_id AND u.state = 'OPEN'
                      AND (u.expires_at > statement_timestamp() OR u.stored_digest IS NOT NULL)
                ) THEN 'UPLOADING'
                ELSE COALESCE(s.status, 'AWAITING_IMAGE')
            END
            """;
    private static final String SUBMISSION_JOIN = """
            LEFT JOIN submissions s ON s.publication_id = p.publication_id AND s.student_id = r.student_id
                                    AND s.source = 'ASSIGNED_WEB'
            """;
    private static final String DECISION_JOIN = """
            LEFT JOIN teacher_decisions d ON d.submission_id = s.submission_id
                                          AND s.status = 'GRADE_RELEASED' AND d.type = 'ASSIGNED_RELEASE'
            """;
    private static final String PUBLICATION_SQL = """
            SELECT a.assignment_id, c.class_id, c.name AS class_name, owner.display_name AS teacher_name,
                   a.title, p.published_at, a.max_score, r.student_id, pupil.display_name AS student_name,
                   m.student_id IS NOT NULL AS member, m.student_id IS NOT NULL AND pupil.active AS active_member,
                   s.submission_id, d.final_score,
            """ + STATUS_SQL + """
                   AS review_status
            FROM assignment_publications p
            JOIN assignments a ON a.assignment_id = p.assignment_id AND a.status = 'PUBLISHED'
            JOIN classrooms c ON c.class_id = a.class_id
            JOIN users owner ON owner.id = c.teacher_id AND owner.active AND owner.role = 'TEACHER'
            LEFT JOIN assignment_recipients r ON r.publication_id = p.publication_id
            LEFT JOIN users pupil ON pupil.id = r.student_id
            LEFT JOIN classroom_students m ON m.class_id = c.class_id AND m.student_id = r.student_id
            """ + SUBMISSION_JOIN + DECISION_JOIN + """
            WHERE p.assignment_id = ? AND owner.email = ?
            ORDER BY pupil.display_name, r.student_id
            """;
    private static final String ACTION_CENTER_SQL = """
            WITH owned AS (
                SELECT c.class_id, c.name
                FROM classrooms c JOIN users owner ON owner.id = c.teacher_id
                WHERE owner.email = ? AND owner.active AND owner.role = 'TEACHER'
            ), classified AS (
                SELECT a.assignment_id, c.class_id, c.name AS class_name, a.title, p.published_at,
                       r.student_id, m.student_id IS NOT NULL AND pupil.active AS active_member,
            """ + STATUS_SQL + """
                       AS review_status
                FROM owned c
                JOIN assignments a ON a.class_id = c.class_id AND a.status = 'PUBLISHED'
                JOIN assignment_publications p ON p.assignment_id = a.assignment_id
                LEFT JOIN assignment_recipients r ON r.publication_id = p.publication_id
                LEFT JOIN users pupil ON pupil.id = r.student_id
                LEFT JOIN classroom_students m ON m.class_id = c.class_id AND m.student_id = r.student_id
            """ + SUBMISSION_JOIN + """
            ), work AS (
                SELECT assignment_id, class_id, class_name, title, published_at,
                       count(*) FILTER (WHERE review_status = 'AWAITING_REVIEW') AS pending,
                       count(*) FILTER (WHERE active_member AND review_status = 'RETAKE_REQUESTED') AS retake,
                       count(*) FILTER (WHERE active_member AND review_status = 'AWAITING_IMAGE') AS missing,
                       count(*) FILTER (WHERE review_status = 'GRADE_RELEASED') AS released
                FROM classified
                GROUP BY assignment_id, class_id, class_name, title, published_at
            ), matching AS (
                SELECT * FROM work WHERE CASE ?
                    WHEN 'PENDING' THEN pending > 0
                    WHEN 'RETAKE' THEN retake > 0
                    WHEN 'MISSING' THEN missing > 0
                    WHEN 'RELEASED' THEN released > 0
                    ELSE TRUE END
            ), totals AS (
                SELECT (SELECT count(*) FROM owned) AS class_count,
                       COALESCE(sum(pending), 0) AS total_pending,
                       COALESCE(sum(retake), 0) AS total_retake,
                       count(*) FILTER (WHERE missing > 0) AS total_missing,
                       COALESCE(sum(released), 0) AS total_released,
                       (SELECT count(*) FROM matching) AS matching_count
                FROM work
            ), page AS (
                SELECT * FROM matching ORDER BY published_at DESC, assignment_id DESC LIMIT ? OFFSET ?
            )
            SELECT totals.*, page.* FROM totals LEFT JOIN page ON TRUE
            ORDER BY page.published_at DESC, page.assignment_id DESC
            """;
    private static final String STUDENT_HISTORY_SQL = """
            SELECT a.assignment_id, a.title, c.name AS class_name, owner.display_name AS teacher_name,
                   p.published_at, a.max_score, d.final_score,
            """ + STATUS_SQL + """
                   AS review_status
            FROM users pupil
            JOIN assignment_recipients r ON r.student_id = pupil.id
            JOIN assignment_publications p ON p.publication_id = r.publication_id
            JOIN assignments a ON a.assignment_id = p.assignment_id AND a.status = 'PUBLISHED'
            JOIN classrooms c ON c.class_id = a.class_id
            JOIN classroom_students m ON m.class_id = c.class_id AND m.student_id = pupil.id
            JOIN users owner ON owner.id = c.teacher_id
            """ + SUBMISSION_JOIN + DECISION_JOIN + """
            WHERE pupil.email = ? AND pupil.active AND pupil.role = 'STUDENT'
            ORDER BY p.published_at DESC, a.assignment_id DESC
            """;

    private final JdbcTemplate db;

    AssignedResults(JdbcTemplate db) {
        this.db = db;
    }

    Publication publication(String email, UUID assignmentId) {
        return db.query(PUBLICATION_SQL, rows -> {
            if (!rows.next()) {
                throw new ApiException("NOT_FOUND", "Không tìm thấy kết quả bài tập.", HttpStatus.NOT_FOUND);
            }
            UUID classId = rows.getObject("class_id", UUID.class);
            String className = rows.getString("class_name");
            String teacherName = rows.getString("teacher_name");
            String title = rows.getString("title");
            Instant publishedAt = rows.getObject("published_at", OffsetDateTime.class).toInstant();
            int maxScore = rows.getInt("max_score");
            List<Recipient> recipients = new ArrayList<>();
            Map<Status, Integer> counts = new EnumMap<>(Status.class);
            for (Status status : Status.values()) counts.put(status, 0);
            do {
                UUID studentId = rows.getObject("student_id", UUID.class);
                if (studentId == null) continue; // Header row for a valid empty publication.
                Status status = readStatus(rows);
                Integer score = rows.getObject("final_score", Integer.class);
                if (status == Status.GRADE_RELEASED && score == null) {
                    throw new IllegalStateException("Released assigned submission has no official decision");
                }
                recipients.add(new Recipient(studentId, rows.getString("student_name"), rows.getBoolean("member"),
                        rows.getBoolean("active_member"),
                        status, rows.getObject("submission_id", UUID.class), score));
                counts.merge(status, 1, Integer::sum);
            } while (rows.next());
            return new Publication(assignmentId, classId, className, teacherName, title, publishedAt, maxScore,
                    recipients.size(), counts, List.copyOf(recipients));
        }, assignmentId, email);
    }

    ActionCenter actionCenter(String email, WorkFilter filter, int page) {
        if (page < 0) throw new ApiException("INVALID_PAGE", "Số trang không hợp lệ.", HttpStatus.BAD_REQUEST);
        return db.query(ACTION_CENTER_SQL, rows -> {
            rows.next(); // The aggregate header exists even with an empty assignment page.
            int classes = rows.getInt("class_count");
            int pending = rows.getInt("total_pending");
            int retake = rows.getInt("total_retake");
            int missing = rows.getInt("total_missing");
            int released = rows.getInt("total_released");
            int matching = rows.getInt("matching_count");
            List<AssignmentWork> assignments = new ArrayList<>();
            do {
                UUID id = rows.getObject("assignment_id", UUID.class);
                if (id == null) continue;
                assignments.add(new AssignmentWork(id, rows.getObject("class_id", UUID.class),
                        rows.getString("class_name"), rows.getString("title"),
                        rows.getObject("published_at", OffsetDateTime.class).toInstant(),
                        rows.getInt("pending"), rows.getInt("retake"), rows.getInt("missing"), rows.getInt("released")));
            } while (rows.next());
            return new ActionCenter(classes, pending, retake, missing, released, matching, page, PAGE_SIZE,
                    List.copyOf(assignments));
        }, email, filter.name(), PAGE_SIZE, (long) page * PAGE_SIZE);
    }

    List<HistoryItem> history(String email) {
        return db.query(STUDENT_HISTORY_SQL, (row, index) -> new HistoryItem(
                row.getObject("assignment_id", UUID.class), row.getString("title"), row.getString("class_name"),
                row.getString("teacher_name"), row.getObject("published_at", OffsetDateTime.class).toInstant(),
                row.getInt("max_score"), readStatus(row), row.getObject("final_score", Integer.class)), email);
    }

    private static Status readStatus(ResultSet rows) throws SQLException {
        return Status.valueOf(rows.getString("review_status"));
    }
}

package com.mathvisionkids.api.submission;

import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.common.ApiException;
import java.io.IOException;
import java.time.OffsetDateTime;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@org.springframework.context.annotation.Profile("!test")
class AssignedUploadCleanup {
    private record Deletion(String key, OffsetDateTime leaseUntil) {}
    private final JdbcTemplate jdbc;
    private final ObjectStorageService storage;
    private final AssignedUploadReservation reservations;

    AssignedUploadCleanup(JdbcTemplate jdbc, ObjectStorageService storage, AssignedUploadReservation reservations) {
        this.jdbc = jdbc;
        this.storage = storage;
        this.reservations = reservations;
    }

    @Scheduled(fixedDelayString = "${app.assigned-upload.cleanup-delay-ms:60000}")
    void cleanExpired() {
        for (var candidate : reservations.recoveryCandidates()) {
            reconcile(candidate);
        }
        jdbc.update("""
                UPDATE assigned_upload_attempts SET state = 'EXPIRED',
                    cleanup_after = CURRENT_TIMESTAMP + INTERVAL '15 minutes'
                WHERE attempt_id IN (
                    SELECT attempt_id FROM assigned_upload_attempts
                    WHERE state = 'OPEN' AND expires_at <= CURRENT_TIMESTAMP
                      AND stored_digest IS NULL
                    ORDER BY expires_at LIMIT 50 FOR UPDATE SKIP LOCKED
                )
                """);
        // Lease the deletion work before releasing DB locks. Expired attempts
        // cannot be confirmed, and deleting their unique key is idempotent.
        var deletions = jdbc.query("""
                UPDATE assigned_upload_attempts SET cleanup_after = CURRENT_TIMESTAMP + INTERVAL '5 minutes'
                WHERE attempt_id IN (
                    SELECT attempt_id FROM assigned_upload_attempts
                    WHERE state = 'EXPIRED' AND cleanup_after <= CURRENT_TIMESTAMP
                    ORDER BY cleanup_after LIMIT 50 FOR UPDATE SKIP LOCKED
                )
                RETURNING object_key, cleanup_after
                """, (row, index) -> new Deletion(row.getString(1), row.getObject(2, OffsetDateTime.class)));
        for (var deletion : deletions) {
            try {
                storage.delete(deletion.key());
                // Allow one delayed sweep for a PUT that was already in flight.
                // Only the current lease can advance or finish the schedule.
                jdbc.update("""
                        UPDATE assigned_upload_attempts
                        SET cleanup_after = CASE WHEN cleanup_first_deleted THEN NULL
                            ELSE clock_timestamp() + INTERVAL '1 day' END,
                            cleanup_first_deleted = TRUE
                        WHERE state = 'EXPIRED' AND object_key = ? AND cleanup_after = ?
                        """, deletion.key(), deletion.leaseUntil());
            } catch (IOException failure) {
                // The lease expiry schedules another attempt.
            }
        }
    }

    void reconcile(AssignedUploadReservation.Recovery candidate) {
        var attempt = candidate.attempt();
        try {
            byte[] bytes = storage.loadBytes(attempt.objectKey());
            if (bytes.length != candidate.size()
                    || !candidate.storedDigest().equals(AssignedWebImage.sha256(bytes))) {
                expireReconciled(attempt.id());
                return;
            }
            reservations.confirmRecovered(candidate.email(), candidate.assignmentId(), candidate.requestId(), attempt,
                    new AssignedWebImage(bytes, candidate.contentType(), attempt.digest(), candidate.storedDigest()));
        } catch (java.io.FileNotFoundException | ApiException failure) {
            expireReconciled(attempt.id());
        } catch (IOException failure) {
            // A storage outage does not establish whether the prepared object exists.
        }
    }

    private void expireReconciled(java.util.UUID attemptId) {
        jdbc.update("""
                UPDATE assigned_upload_attempts SET state = 'EXPIRED',
                    cleanup_after = clock_timestamp() + INTERVAL '15 minutes'
                WHERE attempt_id = ? AND state = 'OPEN' AND expires_at <= clock_timestamp()
                """, attemptId);
    }
}

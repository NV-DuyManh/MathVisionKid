package com.mathvisionkids.api.submission;

import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.common.ApiException;
import java.io.IOException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@org.springframework.context.annotation.Profile("!test")
class AssignedUploadCleanup {
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
        var keys = jdbc.queryForList("""
                UPDATE assigned_upload_attempts SET cleanup_after = CURRENT_TIMESTAMP + INTERVAL '5 minutes'
                WHERE attempt_id IN (
                    SELECT attempt_id FROM assigned_upload_attempts
                    WHERE state = 'EXPIRED' AND cleanup_after <= CURRENT_TIMESTAMP
                    ORDER BY cleanup_after LIMIT 50 FOR UPDATE SKIP LOCKED
                )
                RETURNING object_key
                """, String.class);
        for (String key : keys) {
            try {
                storage.delete(key);
                // Recheck later because a PUT already in flight may finish after deletion.
                jdbc.update("""
                        UPDATE assigned_upload_attempts SET cleanup_after = CURRENT_TIMESTAMP + INTERVAL '1 day'
                        WHERE state = 'EXPIRED' AND object_key = ?
                        """, key);
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

ALTER TABLE assigned_upload_attempts
    ADD COLUMN stored_digest CHAR(64) CHECK (stored_digest ~ '^[0-9a-f]{64}$'),
    ADD COLUMN stored_content_type VARCHAR(20) CHECK (stored_content_type IN ('image/jpeg', 'image/png')),
    ADD COLUMN stored_size INTEGER CHECK (stored_size BETWEEN 1 AND 8388608),
    ADD COLUMN recover_after TIMESTAMPTZ,
    ADD CONSTRAINT ck_assigned_upload_recovery_metadata CHECK (
        (stored_digest IS NULL AND stored_content_type IS NULL AND stored_size IS NULL)
        OR (stored_digest IS NOT NULL AND stored_content_type IS NOT NULL AND stored_size IS NOT NULL)
    );

CREATE INDEX idx_assigned_upload_recover_after
    ON assigned_upload_attempts(recover_after) WHERE state = 'OPEN';

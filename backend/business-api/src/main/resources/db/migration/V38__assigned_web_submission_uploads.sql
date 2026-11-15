ALTER TABLE assignment_publications ADD CONSTRAINT uq_publication_assignment
    UNIQUE (publication_id, assignment_id);

ALTER TABLE submissions ADD COLUMN source VARCHAR(20);
UPDATE submissions SET source = CASE WHEN batch_id IS NULL THEN 'SELF_PRACTICE' ELSE 'BATCH' END;
ALTER TABLE submissions ALTER COLUMN source SET DEFAULT 'SELF_PRACTICE';
ALTER TABLE submissions ALTER COLUMN source SET NOT NULL;
ALTER TABLE submissions ADD COLUMN publication_id UUID;
ALTER TABLE submissions ADD CONSTRAINT ck_submission_source CHECK (
    (source IN ('BATCH', 'SELF_PRACTICE') AND publication_id IS NULL)
    OR (source = 'ASSIGNED_WEB' AND publication_id IS NOT NULL
        AND assignment_id IS NOT NULL AND student_id IS NOT NULL AND batch_id IS NULL)
);
ALTER TABLE submissions ADD CONSTRAINT fk_submission_recipient
    FOREIGN KEY (publication_id, student_id) REFERENCES assignment_recipients(publication_id, student_id);
ALTER TABLE submissions ADD CONSTRAINT fk_submission_publication_assignment
    FOREIGN KEY (publication_id, assignment_id) REFERENCES assignment_publications(publication_id, assignment_id);
ALTER TABLE submissions ADD CONSTRAINT uq_submission_recipient UNIQUE (publication_id, student_id);

ALTER TABLE submission_images ADD COLUMN image_version INTEGER CHECK (image_version > 0);
ALTER TABLE submission_images ADD CONSTRAINT uq_submission_image_version UNIQUE (submission_id, image_version);

CREATE TABLE assigned_upload_attempts (
    attempt_id UUID PRIMARY KEY,
    submission_id UUID NOT NULL REFERENCES submissions(submission_id),
    request_id UUID NOT NULL,
    expected_image_version INTEGER NOT NULL CHECK (expected_image_version >= 0),
    digest CHAR(64) NOT NULL CHECK (digest ~ '^[0-9a-f]{64}$'),
    object_key VARCHAR(512) NOT NULL UNIQUE,
    state VARCHAR(20) NOT NULL CHECK (state IN ('OPEN', 'CONFIRMED', 'EXPIRED')),
    expires_at TIMESTAMPTZ NOT NULL,
    cleanup_after TIMESTAMPTZ,
    UNIQUE (submission_id, request_id)
);
CREATE UNIQUE INDEX uq_assigned_upload_open
    ON assigned_upload_attempts(submission_id) WHERE state = 'OPEN';
CREATE INDEX idx_assigned_upload_expiry ON assigned_upload_attempts(expires_at) WHERE state = 'OPEN';
CREATE INDEX idx_assigned_upload_cleanup ON assigned_upload_attempts(cleanup_after) WHERE state = 'EXPIRED';

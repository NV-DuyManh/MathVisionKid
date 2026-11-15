CREATE TABLE assigned_image_returns (
    submission_id UUID NOT NULL,
    image_version INTEGER NOT NULL,
    teacher_id UUID NOT NULL REFERENCES teachers(teacher_id),
    reason VARCHAR(20) NOT NULL CHECK (reason IN ('UNREADABLE', 'WRONG_ASSIGNMENT')),
    instruction VARCHAR(500) NOT NULL,
    returned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (submission_id, image_version),
    FOREIGN KEY (submission_id, image_version) REFERENCES submission_images(submission_id, image_version)
);

ALTER TABLE teacher_decisions ADD COLUMN assigned_request_id UUID;
ALTER TABLE teacher_decisions ADD COLUMN assigned_image_version INTEGER;
ALTER TABLE teacher_decisions ADD CONSTRAINT fk_decision_assigned_image
    FOREIGN KEY (submission_id, assigned_image_version) REFERENCES submission_images(submission_id, image_version);

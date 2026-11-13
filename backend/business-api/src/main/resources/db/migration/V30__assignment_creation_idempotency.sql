ALTER TABLE assignments ADD COLUMN creation_request_id UUID;
ALTER TABLE assignments ADD CONSTRAINT uq_assignment_teacher_creation_request
    UNIQUE (teacher_id, creation_request_id);

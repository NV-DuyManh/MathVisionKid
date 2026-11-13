ALTER TABLE batches ADD COLUMN creation_request_id UUID;
ALTER TABLE batches ADD CONSTRAINT uq_batch_teacher_creation_request
    UNIQUE (teacher_id, creation_request_id);

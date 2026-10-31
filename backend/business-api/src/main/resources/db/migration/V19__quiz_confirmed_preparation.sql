-- Additive: existing Quiz history, rewards and immutable source texts remain intact.
CREATE TABLE quiz_preparations (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(student_id),
    workflow_key UUID NOT NULL,
    revision BIGINT NOT NULL CHECK (revision >= 0),
    fingerprint VARCHAR(64),
    status VARCHAR(20) NOT NULL CHECK (status IN ('READY','INVALIDATED','UNSUPPORTED','FAILED')),
    error_code VARCHAR(64), validated_draft TEXT, updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE(student_id, workflow_key),
    CHECK ((status='READY') = (validated_draft IS NOT NULL))
);
CREATE INDEX idx_quiz_preparation_source ON quiz_preparations(student_id,fingerprint,updated_at DESC);
ALTER TABLE quiz_learning_sources ADD COLUMN preparation_id UUID REFERENCES quiz_preparations(id);
ALTER TABLE student_quizzes DROP CONSTRAINT student_quizzes_status_check;
ALTER TABLE student_quizzes ADD CONSTRAINT student_quizzes_status_check
    CHECK (status IN ('READY','DEFERRED','IN_PROGRESS','COMPLETED','INVALIDATED'));

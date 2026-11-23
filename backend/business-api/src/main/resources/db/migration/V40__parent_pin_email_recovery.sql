ALTER TABLE student_parent_control ADD COLUMN pin_revision BIGINT NOT NULL DEFAULT 0;

CREATE TABLE student_parent_pin_challenge (
    student_id UUID PRIMARY KEY REFERENCES students(student_id) ON DELETE CASCADE,
    purpose VARCHAR(8) NOT NULL CHECK (purpose IN ('SETUP', 'RESET')),
    code_hash VARCHAR(100),
    issued_at TIMESTAMP WITH TIME ZONE NOT NULL,
    window_started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    sends INT NOT NULL CHECK (sends BETWEEN 1 AND 3),
    attempts INT NOT NULL DEFAULT 0 CHECK (attempts BETWEEN 0 AND 5)
);

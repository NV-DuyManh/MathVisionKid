CREATE TABLE student_parent_control (
    student_id UUID PRIMARY KEY REFERENCES students(student_id) ON DELETE CASCADE,
    pin_hash VARCHAR(100) NOT NULL,
    failed_attempts INT NOT NULL DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    daily_minutes INT CHECK (daily_minutes BETWEEN 1 AND 1440)
);

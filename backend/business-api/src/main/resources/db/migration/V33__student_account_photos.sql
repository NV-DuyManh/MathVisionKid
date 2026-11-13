CREATE TABLE student_profile_photos (
    student_id UUID PRIMARY KEY REFERENCES students(student_id),
    image_bytes BYTEA NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE student_password_attempts (
    student_id UUID PRIMARY KEY REFERENCES students(student_id),
    attempts INTEGER NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL
);

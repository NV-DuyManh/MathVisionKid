CREATE TABLE student_usage_connection (
    student_id UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    connection_id UUID NOT NULL,
    last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (student_id, connection_id)
);

CREATE TABLE student_usage_day (
    student_id UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    usage_day DATE NOT NULL,
    elapsed_millis BIGINT NOT NULL CHECK (elapsed_millis >= 0),
    PRIMARY KEY (student_id, usage_day)
);

CREATE TABLE student_usage_recent_span (
    student_id UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    starts_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ends_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (student_id, starts_at),
    CHECK (ends_at > starts_at)
);

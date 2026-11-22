ALTER TABLE student_parent_control
    ADD COLUMN game_minutes INT CHECK (game_minutes BETWEEN 1 AND 1440);

CREATE TABLE student_game_usage_connection (
    student_id UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    connection_id UUID NOT NULL,
    accounted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    lease_until TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (student_id, connection_id),
    CHECK (lease_until >= accounted_at)
);

CREATE TABLE student_game_usage_day (
    student_id UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    usage_day DATE NOT NULL,
    elapsed_millis BIGINT NOT NULL CHECK (elapsed_millis >= 0),
    PRIMARY KEY (student_id, usage_day)
);

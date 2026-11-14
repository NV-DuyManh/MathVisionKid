CREATE TABLE classroom_code_limit (
    id SMALLINT PRIMARY KEY CHECK (id = 1),
    window_start BIGINT NOT NULL,
    attempts INTEGER NOT NULL CHECK (attempts BETWEEN 1 AND 300)
);

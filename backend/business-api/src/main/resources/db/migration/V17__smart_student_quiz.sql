-- Additive migration. Source events come only from successful, authenticated Tutor operations.
CREATE TABLE quiz_learning_sources (
    id UUID PRIMARY KEY, student_id UUID NOT NULL REFERENCES students(student_id),
    source_type VARCHAR(24) NOT NULL CHECK (source_type IN ('LESSON','WORK_REVIEW')),
    source_id VARCHAR(100) NOT NULL, problem_text TEXT NOT NULL, fingerprint VARCHAR(64) NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ NOT NULL,
    UNIQUE(student_id, source_type, source_id)
);
CREATE TABLE student_quizzes (
    id UUID PRIMARY KEY, student_id UUID NOT NULL REFERENCES students(student_id),
    source_type VARCHAR(24) NOT NULL, source_id VARCHAR(100) NOT NULL, source_fingerprint VARCHAR(64) NOT NULL,
    topic_code VARCHAR(64) NOT NULL, topic_name VARCHAR(120) NOT NULL, skill_code VARCHAR(80) NOT NULL,
    grade_level INTEGER NOT NULL CHECK (grade_level BETWEEN 1 AND 5), question_text TEXT NOT NULL,
    unit VARCHAR(30) NOT NULL, answer_spec VARCHAR(100) NOT NULL, validated_solution TEXT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('READY','DEFERRED','IN_PROGRESS','COMPLETED')),
    created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL, started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ, stars INTEGER NOT NULL DEFAULT 0 CHECK(stars BETWEEN 0 AND 3),
    wrong_attempts INTEGER NOT NULL DEFAULT 0 CHECK(wrong_attempts >= 0),
    solution_viewed BOOLEAN NOT NULL DEFAULT FALSE, completed_with_solution BOOLEAN NOT NULL DEFAULT FALSE,
    generation_version VARCHAR(32) NOT NULL, last_submitted_at TIMESTAMPTZ,
    UNIQUE(student_id, source_type, source_fingerprint),
    FOREIGN KEY(student_id, source_type, source_id) REFERENCES quiz_learning_sources(student_id, source_type, source_id),
    CHECK (NOT completed_with_solution OR (solution_viewed AND stars=0)),
    CHECK (stars=0 OR (status='COMPLETED' AND NOT solution_viewed)),
    CHECK ((status='COMPLETED') = (completed_at IS NOT NULL))
);
CREATE INDEX idx_student_quizzes_library ON student_quizzes(student_id, status, created_at DESC, id);
CREATE TABLE quiz_attempts (
    id UUID PRIMARY KEY, quiz_id UUID NOT NULL REFERENCES student_quizzes(id), request_id UUID NOT NULL,
    attempt_number INTEGER NOT NULL CHECK(attempt_number > 0), answer VARCHAR(100) NOT NULL,
    correct BOOLEAN NOT NULL, submitted_at TIMESTAMPTZ NOT NULL,
    elapsed_millis BIGINT NOT NULL CHECK(elapsed_millis >= 0),
    UNIQUE(quiz_id, request_id), UNIQUE(quiz_id, attempt_number)
);

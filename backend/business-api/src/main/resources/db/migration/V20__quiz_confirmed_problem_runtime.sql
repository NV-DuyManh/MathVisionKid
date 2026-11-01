-- Additive and backwards compatible. Never rewrite a confirmed source or Quiz history.
ALTER TABLE quiz_preparations ADD COLUMN confirmed_problem_text TEXT;
ALTER TABLE quiz_preparations ADD COLUMN problem_confirmed BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE quiz_preparations ADD COLUMN generator_version VARCHAR(64);
ALTER TABLE quiz_preparations ADD COLUMN generated_at TIMESTAMPTZ;
ALTER TABLE quiz_preparations ADD COLUMN duration_ms BIGINT;
UPDATE quiz_preparations p SET confirmed_problem_text=s.problem_text, problem_confirmed=TRUE
FROM quiz_learning_sources s WHERE s.preparation_id=p.id AND s.fingerprint=p.fingerprint;
ALTER TABLE quiz_preparations DROP CONSTRAINT quiz_preparations_status_check;
ALTER TABLE quiz_preparations ADD CONSTRAINT quiz_preparations_status_check
    CHECK (status IN ('GENERATING','READY','INVALIDATED','UNSUPPORTED','FAILED'));
ALTER TABLE quiz_preparations ADD CONSTRAINT quiz_confirmed_text_check
    CHECK (NOT problem_confirmed OR (confirmed_problem_text IS NOT NULL AND length(confirmed_problem_text) BETWEEN 3 AND 4000));

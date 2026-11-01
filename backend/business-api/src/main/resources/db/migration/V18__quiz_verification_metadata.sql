-- Keep V17 immutable after the first QA/application migration.
-- Every existing Quiz was produced by the deterministic validator in smart-quiz-v1.
-- Confidence describes an accepted rule/validator match, not an ML probability.
ALTER TABLE student_quizzes
    ADD COLUMN taxonomy_version VARCHAR(32) NOT NULL DEFAULT 'smart-quiz-v1',
    ADD COLUMN verification_status VARCHAR(32) NOT NULL DEFAULT 'DETERMINISTICALLY_VERIFIED',
    ADD COLUMN confidence_percent INTEGER NOT NULL DEFAULT 100 CHECK(confidence_percent BETWEEN 0 AND 100);

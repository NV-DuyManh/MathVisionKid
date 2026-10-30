-- V22: Support Quiz Replay Modes (Practice vs Challenge) and Preserve Original Problem
ALTER TABLE student_quizzes ADD COLUMN IF NOT EXISTS replay_mode VARCHAR(20) NOT NULL DEFAULT 'NONE';
ALTER TABLE student_quizzes ADD COLUMN IF NOT EXISTS original_question_text TEXT;
ALTER TABLE student_quizzes ADD COLUMN IF NOT EXISTS original_answer_spec VARCHAR(100);
ALTER TABLE student_quizzes ADD COLUMN IF NOT EXISTS original_validated_solution TEXT;
ALTER TABLE student_quizzes ADD COLUMN IF NOT EXISTS original_unit VARCHAR(30);

UPDATE student_quizzes
SET original_question_text = question_text,
    original_answer_spec = answer_spec,
    original_validated_solution = validated_solution,
    original_unit = unit
WHERE original_question_text IS NULL;

ALTER TABLE quiz_attempts ADD COLUMN IF NOT EXISTS replay_mode VARCHAR(20) NOT NULL DEFAULT 'NONE';

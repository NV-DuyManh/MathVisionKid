-- Additive: Replay support with best stars preservation and attempt scoring.
ALTER TABLE student_quizzes ADD COLUMN IF NOT EXISTS replaying BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE student_quizzes ADD COLUMN IF NOT EXISTS first_completed_at TIMESTAMPTZ;

-- Backfill first_completed_at for already completed quizzes
UPDATE student_quizzes SET first_completed_at = completed_at WHERE status = 'COMPLETED' AND completed_at IS NOT NULL AND first_completed_at IS NULL;

-- Relax checks to permit in-progress replay while preserving previous best stars and first completion timestamp
ALTER TABLE student_quizzes DROP CONSTRAINT IF EXISTS student_quizzes_check;
ALTER TABLE student_quizzes ADD CONSTRAINT student_quizzes_check
    CHECK (NOT completed_with_solution OR (solution_viewed AND stars = 0) OR replaying = TRUE);

ALTER TABLE student_quizzes DROP CONSTRAINT IF EXISTS student_quizzes_check1;
ALTER TABLE student_quizzes ADD CONSTRAINT student_quizzes_check1
    CHECK (stars = 0 OR status = 'COMPLETED' OR replaying = TRUE);

ALTER TABLE student_quizzes DROP CONSTRAINT IF EXISTS student_quizzes_check2;
ALTER TABLE student_quizzes ADD CONSTRAINT student_quizzes_check2
    CHECK (((status = 'COMPLETED') = (completed_at IS NOT NULL)) OR replaying = TRUE);

-- Add stars column to quiz_attempts to record stars achieved on each attempt
ALTER TABLE quiz_attempts ADD COLUMN IF NOT EXISTS stars INTEGER NOT NULL DEFAULT 0 CHECK (stars BETWEEN 0 AND 3);

-- Backfill attempts stars: correct attempt gets quiz stars
UPDATE quiz_attempts a SET stars = q.stars FROM student_quizzes q WHERE a.quiz_id = q.id AND a.correct = TRUE AND q.stars > 0;


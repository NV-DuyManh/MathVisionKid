-- Additive correction; V21/V22 checksums and existing attempts remain intact.
ALTER TABLE quiz_attempts ADD COLUMN question_text TEXT;
ALTER TABLE quiz_attempts ADD COLUMN answer_spec VARCHAR(100);
ALTER TABLE quiz_attempts ADD COLUMN solution_viewed BOOLEAN;
ALTER TABLE quiz_attempts ADD COLUMN run_started_at TIMESTAMPTZ;

-- Only the current run can be reconstructed reliably. Older replay snapshots stay unknown.
UPDATE quiz_attempts a SET question_text=q.question_text, answer_spec=q.answer_spec,
    solution_viewed=q.solution_viewed, run_started_at=q.started_at
FROM student_quizzes q WHERE a.quiz_id=q.id AND q.started_at IS NOT NULL AND a.submitted_at>=q.started_at;

-- stars is the all-time best; assisted completion describes the current run even if best > 0.
ALTER TABLE student_quizzes DROP CONSTRAINT IF EXISTS student_quizzes_check;
ALTER TABLE student_quizzes ADD CONSTRAINT student_quizzes_check CHECK (NOT completed_with_solution OR solution_viewed);

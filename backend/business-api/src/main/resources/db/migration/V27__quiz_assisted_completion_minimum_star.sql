-- Apply the new assisted-completion award without losing the original reward.
-- Attempt IDs, answers, question snapshots, modes, and timing remain unchanged.
CREATE TABLE quiz_star_policy_adjustments (
    attempt_id UUID PRIMARY KEY REFERENCES quiz_attempts(id),
    previous_stars INTEGER NOT NULL,
    awarded_stars INTEGER NOT NULL,
    policy VARCHAR(64) NOT NULL,
    adjusted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO quiz_star_policy_adjustments(attempt_id, previous_stars, awarded_stars, policy)
SELECT a.id, a.stars, 1, 'ASSISTED_COMPLETION_MINIMUM_ONE'
FROM quiz_attempts a JOIN student_quizzes q ON q.id=a.quiz_id
WHERE a.correct AND a.stars=0 AND a.replay_mode IN ('NONE','CHALLENGE')
  AND (a.solution_viewed IS TRUE OR
       (a.solution_viewed IS NULL AND q.status='COMPLETED'
        AND q.completed_with_solution AND q.solution_viewed
        AND a.run_started_at=q.started_at AND a.submitted_at=q.completed_at));

UPDATE quiz_attempts a SET stars=p.awarded_stars
FROM quiz_star_policy_adjustments p WHERE p.attempt_id=a.id;

UPDATE student_quizzes q SET stars=GREATEST(q.stars, earned.best)
FROM (SELECT quiz_id, MAX(stars) AS best FROM quiz_attempts
      WHERE correct AND replay_mode IN ('NONE','CHALLENGE') GROUP BY quiz_id) earned
WHERE q.id=earned.quiz_id AND q.stars<earned.best;

-- An ambiguous legacy completion is not silently awarded points. A failed check
-- rolls back this migration for inspection instead of guessing from stars=0.
ALTER TABLE student_quizzes ADD CONSTRAINT quiz_scored_completion_minimum_star
    CHECK (status<>'COMPLETED' OR replay_mode='PRACTICE' OR stars>=1);

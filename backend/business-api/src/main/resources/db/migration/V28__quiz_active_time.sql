-- Only foreground Quiz work is timed. Existing attempts/rewards stay immutable.
ALTER TABLE student_quizzes
    ADD COLUMN active_elapsed_millis BIGINT NOT NULL DEFAULT 0 CHECK(active_elapsed_millis >= 0),
    ADD COLUMN active_since TIMESTAMPTZ,
    ADD COLUMN active_until TIMESTAMPTZ;

-- Completed historical runs retain their recorded duration. The active time of
-- an unfinished legacy run cannot be reconstructed from wall time: start paused
-- at zero rather than count hours spent outside the app as solving time.
UPDATE student_quizzes SET active_elapsed_millis=GREATEST(0,
    CEIL(EXTRACT(EPOCH FROM (completed_at-started_at))*1000)::BIGINT)
WHERE status='COMPLETED' AND started_at IS NOT NULL AND completed_at IS NOT NULL;

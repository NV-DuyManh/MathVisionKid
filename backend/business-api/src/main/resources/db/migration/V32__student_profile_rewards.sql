CREATE TABLE student_profile_preferences (
    student_id UUID PRIMARY KEY REFERENCES students(student_id),
    avatar VARCHAR(16) NOT NULL DEFAULT 'star',
    public_alias VARCHAR(32) NOT NULL UNIQUE,
    leaderboard_visible BOOLEAN NOT NULL DEFAULT FALSE,
    selected_title VARCHAR(32),
    reached_challenger BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE student_reward_lock (
    id INTEGER PRIMARY KEY CHECK (id = 1)
);
INSERT INTO student_reward_lock (id) VALUES (1);

CREATE TABLE student_verified_activities (
    student_id UUID NOT NULL REFERENCES students(student_id),
    source VARCHAR(12) NOT NULL CHECK (source IN ('LESSON','QUIZ','GAME')),
    event_id VARCHAR(100) NOT NULL,
    content_id VARCHAR(100) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    activity_day DATE NOT NULL,
    stars INTEGER NOT NULL CHECK (stars IN (0, 1)),
    PRIMARY KEY (student_id, source, event_id)
);
CREATE INDEX student_activity_day_idx ON student_verified_activities(student_id, activity_day);
CREATE INDEX student_activity_content_idx ON student_verified_activities(student_id, source, content_id, activity_day);

CREATE TABLE student_game_runs (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(student_id),
    level INTEGER NOT NULL CHECK (level BETWEEN 1 AND 5),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    activity_day DATE NOT NULL,
    seed BIGINT NOT NULL,
    answered INTEGER NOT NULL DEFAULT 0 CHECK (answered BETWEEN 0 AND 5),
    correct INTEGER NOT NULL DEFAULT 0 CHECK (correct BETWEEN 0 AND 5),
    last_answer INTEGER
);
CREATE INDEX student_game_day_idx ON student_game_runs(student_id, activity_day);

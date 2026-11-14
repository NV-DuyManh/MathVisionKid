ALTER TABLE student_game_runs ADD COLUMN mode VARCHAR(24) NOT NULL DEFAULT 'ARITHMETIC_QUEST';
ALTER TABLE student_game_runs ADD CONSTRAINT student_game_runs_mode_check
    CHECK (mode IN ('ARITHMETIC_QUEST', 'RACE_TO_FINISH', 'TERRAIN_RACING', 'ENERGY_DEFENSE', 'PLANET_RESCUE', 'BLOCK_ISLAND'));
ALTER TABLE student_game_runs ADD COLUMN reward_status VARCHAR(24);
ALTER TABLE student_game_runs ADD CONSTRAINT student_game_runs_reward_status_check
    CHECK (reward_status IN ('AWARDED', 'REPEAT', 'DAILY_LIMIT', 'GAME_LIMIT', 'UNAVAILABLE'));

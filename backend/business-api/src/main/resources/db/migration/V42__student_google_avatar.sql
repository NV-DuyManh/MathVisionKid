ALTER TABLE student_profile_preferences ADD COLUMN google_avatar_url VARCHAR(2048);
ALTER TABLE student_profile_preferences ADD COLUMN google_avatar_enabled BOOLEAN NOT NULL DEFAULT TRUE;

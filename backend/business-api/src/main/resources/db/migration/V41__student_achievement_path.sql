ALTER TABLE student_profile_preferences ADD COLUMN achievement_path VARCHAR(16);
ALTER TABLE student_profile_preferences ADD COLUMN achievement_path_changed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE student_profile_preferences ADD CONSTRAINT student_achievement_path_valid CHECK (
    (achievement_path IS NULL AND achievement_path_changed_at IS NULL)
    OR (achievement_path IS NOT NULL AND achievement_path IN ('RANK', 'CULTIVATION') AND achievement_path_changed_at IS NOT NULL)
);

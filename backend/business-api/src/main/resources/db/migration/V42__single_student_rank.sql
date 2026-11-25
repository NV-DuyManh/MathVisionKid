UPDATE student_profile_preferences SET selected_title = NULL WHERE selected_title IS NOT NULL;
ALTER TABLE student_profile_preferences DROP CONSTRAINT student_achievement_path_valid;
ALTER TABLE student_profile_preferences DROP COLUMN achievement_path;
ALTER TABLE student_profile_preferences DROP COLUMN achievement_path_changed_at;

ALTER TABLE student_profile_preferences
    ADD COLUMN privacy_revision UUID NOT NULL DEFAULT gen_random_uuid();

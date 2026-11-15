ALTER TABLE assigned_upload_attempts
    ADD COLUMN cleanup_first_deleted BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE users ADD COLUMN facebook_subject VARCHAR(255);
CREATE UNIQUE INDEX uq_users_facebook_subject ON users(facebook_subject) WHERE facebook_subject IS NOT NULL;

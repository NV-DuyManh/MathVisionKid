ALTER TABLE users ADD COLUMN gender VARCHAR(30);
ALTER TABLE users ADD COLUMN phone_number VARCHAR(32);

CREATE TABLE password_reset_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    attempts INTEGER NOT NULL DEFAULT 0,
    consumed BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX idx_password_reset_codes_user_created ON password_reset_codes(user_id, created_at DESC);

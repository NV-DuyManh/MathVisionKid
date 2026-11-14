ALTER TABLE classrooms ADD COLUMN creation_request_id UUID;
ALTER TABLE classrooms ADD COLUMN created_by_teacher_id UUID REFERENCES teachers(teacher_id);
ALTER TABLE classrooms ADD CONSTRAINT uq_classroom_teacher_creation_request
    UNIQUE (created_by_teacher_id, creation_request_id);
ALTER TABLE classrooms ADD COLUMN join_mode VARCHAR(20) NOT NULL DEFAULT 'APPROVAL_REQUIRED'
    CHECK (join_mode IN ('AUTO_JOIN', 'APPROVAL_REQUIRED'));

CREATE TABLE classroom_invitations (
    id UUID PRIMARY KEY,
    class_id UUID NOT NULL REFERENCES classrooms(class_id),
    code VARCHAR(6) NOT NULL UNIQUE,
    token VARCHAR(64) NOT NULL UNIQUE,
    enabled BOOLEAN NOT NULL
);
CREATE UNIQUE INDEX uq_classroom_active_invitation ON classroom_invitations(class_id) WHERE enabled;

CREATE TABLE classroom_join_requests (
    class_id UUID NOT NULL REFERENCES classrooms(class_id),
    student_id UUID NOT NULL REFERENCES students(student_id),
    status VARCHAR(12) NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'DECLINED', 'REMOVED')),
    request_id UUID NOT NULL,
    PRIMARY KEY (class_id, student_id)
);

CREATE TABLE classroom_join_limits (
    student_id UUID PRIMARY KEY REFERENCES students(student_id),
    window_start BIGINT NOT NULL,
    attempts INTEGER NOT NULL
);

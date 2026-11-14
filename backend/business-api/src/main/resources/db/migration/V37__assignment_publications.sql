ALTER TABLE assignments ADD COLUMN prompt TEXT;
ALTER TABLE assignments ADD COLUMN instructions TEXT;

CREATE TABLE assignment_publications (
    publication_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_id UUID NOT NULL UNIQUE REFERENCES assignments(assignment_id),
    published_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE assignment_recipients (
    publication_id UUID NOT NULL REFERENCES assignment_publications(publication_id),
    student_id UUID NOT NULL REFERENCES students(student_id),
    PRIMARY KEY (publication_id, student_id)
);

CREATE INDEX idx_assignment_recipients_student ON assignment_recipients(student_id, publication_id);

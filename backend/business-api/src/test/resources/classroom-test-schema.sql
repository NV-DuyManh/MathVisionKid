-- Hibernate creates the mapped entities in H2. Admin also uses this V34 JDBC table.
CREATE TABLE classroom_join_requests (
    class_id UUID NOT NULL REFERENCES classrooms(class_id),
    student_id UUID NOT NULL REFERENCES students(student_id),
    status VARCHAR(12) NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'DECLINED', 'REMOVED')),
    request_id UUID NOT NULL,
    PRIMARY KEY (class_id, student_id)
);

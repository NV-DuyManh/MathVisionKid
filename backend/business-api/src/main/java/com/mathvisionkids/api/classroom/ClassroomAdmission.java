package com.mathvisionkids.api.classroom;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.user.TeacherRepository;
import java.security.SecureRandom;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class ClassroomAdmission {
    private static final SecureRandom RANDOM = new SecureRandom();
    private final ClassroomRepository classes;
    private final StudentRepository students;
    private final TeacherRepository teachers;
    private final JdbcTemplate jdbc;
    private final ClassroomJoinLimit limit;

    ClassroomAdmission(ClassroomRepository classes, StudentRepository students, TeacherRepository teachers,
                       JdbcTemplate jdbc, ClassroomJoinLimit limit) {
        this.classes = classes;
        this.students = students;
        this.teachers = teachers;
        this.jdbc = jdbc;
        this.limit = limit;
    }

    record Invitation(UUID generation, UUID classId, String code, String token) {}
    record Preview(UUID classId, String name, int gradeLevel, UUID generation) {}
    record Admission(UUID classId, String name, int gradeLevel, String status) {}
    record Request(UUID studentId, String displayName, UUID requestId) {}
    private record JoinRecord(UUID requestId, String status) {}

    private Classroom owned(String email, UUID id) {
        var teacher = teachers.findByEmail(email).filter(t -> Boolean.TRUE.equals(t.getActive()))
                .orElseThrow(ClassroomAdmission::forbidden);
        var classroom = classes.findForUpdate(id).orElseThrow(ClassroomAdmission::unavailable);
        if (!classroom.getTeacher().getId().equals(teacher.getId())) throw forbidden();
        return classroom;
    }

    private Student student(String email) {
        return students.findByEmail(email).filter(s -> Boolean.TRUE.equals(s.getActive()))
                .orElseThrow(ClassroomAdmission::forbidden);
    }

    private List<Invitation> invitations(String condition, Object value) {
        return jdbc.query("select id, class_id, code, token from classroom_invitations where enabled and " + condition,
                (row, index) -> new Invitation(row.getObject(1, UUID.class), row.getObject(2, UUID.class),
                        row.getString(3), row.getString(4)), value);
    }

    Invitation invitation(String email, UUID id) {
        owned(email, id);
        return invitations("class_id = ?", id).stream().findFirst().orElse(null);
    }

    Invitation rotate(String email, UUID id) {
        owned(email, id);
        jdbc.update("update classroom_invitations set enabled = false where class_id = ? and enabled", id);
        for (int i = 0; i < 32; i++) {
            String code = String.format(Locale.ROOT, "%06d", RANDOM.nextInt(1_000_000));
            String token = HexFormat.of().formatHex(RANDOM.generateSeed(32));
            UUID generation = UUID.randomUUID();
            if (jdbc.update("insert into classroom_invitations values (?, ?, ?, ?, true) on conflict do nothing",
                    generation, id, code, token) == 1) return new Invitation(generation, id, code, token);
        }
        throw new ApiException("INVITATION_UNAVAILABLE", "Chưa tạo được mã lớp. Hãy thử lại.", HttpStatus.SERVICE_UNAVAILABLE);
    }

    void disable(String email, UUID id) {
        owned(email, id);
        jdbc.update("update classroom_invitations set enabled = false where class_id = ? and enabled", id);
    }

    void update(String email, UUID id, String name, Integer gradeLevel, String mode) {
        Classroom classroom = owned(email, id);
        if (name != null) classroom.setName(name.strip());
        if (gradeLevel != null) classroom.setGradeLevel(gradeLevel);
        if (mode != null) classroom.setJoinMode(mode);
    }

    private Invitation resolve(String credential) {
        if (credential == null) throw unavailable();
        String condition = credential.matches("[0-9]{6}") ? "code = ?" : "token = ?";
        return invitations(condition, credential).stream().findFirst().orElseThrow(ClassroomAdmission::unavailable);
    }

    @Transactional(propagation = org.springframework.transaction.annotation.Propagation.NOT_SUPPORTED)
    public void checkJoinLimit(String email) {
        limit.check(student(email).getId());
    }

    Preview preview(String email, String credential) {
        var student = student(email);

        var invite = resolve(credential);
        var classroom = classes.findById(invite.classId()).orElseThrow(ClassroomAdmission::unavailable);
        return new Preview(classroom.getClassId(), classroom.getName(), classroom.getGradeLevel(), invite.generation());
    }

    Admission join(String email, String credential, UUID id, UUID generation) {
        Student student = student(email);

        Classroom classroom = classes.findForUpdate(id).orElseThrow(ClassroomAdmission::unavailable);
        requireActiveStudentForUpdate(student.getId());
        Invitation invite = resolve(credential);
        if (!id.equals(invite.classId()) || !generation.equals(invite.generation())) throw unavailable();
        if (isMember(classroom, student.getId())) return admission(classroom, "JOINED");
        var prior = record(id, student.getId());
        if (prior != null && prior.status().equals("PENDING")) return admission(classroom, "PENDING");
        if (prior == null && classroom.getJoinMode().equals("AUTO_JOIN")) {
            classroom.getStudents().add(student);
            return admission(classroom, "JOINED");
        }
        writeRecord(id, student.getId(), UUID.randomUUID(), "PENDING");
        return admission(classroom, "PENDING");
    }

    List<Admission> myClasses(String email) {
        var student = student(email);
        var result = new java.util.ArrayList<>(classes.findByStudents_Id(student.getId()).stream()
                .map(c -> admission(c, "JOINED")).toList());
        result.addAll(jdbc.query("""
                select c.class_id, c.name, c.grade_level, r.status
                from classroom_join_requests r join classrooms c on c.class_id = r.class_id
                where r.student_id = ? and r.status in ('PENDING', 'DECLINED', 'REMOVED')
                and not exists (select 1 from classroom_students m where m.class_id = r.class_id and m.student_id = r.student_id)
                order by c.name, c.class_id
                """, (row, index) -> new Admission(row.getObject(1, UUID.class), row.getString(2), row.getInt(3),
                row.getString(4)), student.getId()));
        return result;
    }

    List<Request> requests(String email, UUID id) {
        owned(email, id);
        return jdbc.query("""
                select r.student_id, u.display_name, r.request_id from classroom_join_requests r
                join users u on u.id = r.student_id where r.class_id = ? and r.status = 'PENDING'
                order by u.display_name, r.student_id
                """, (row, index) -> new Request(row.getObject(1, UUID.class), row.getString(2),
                row.getObject(3, UUID.class)), id);
    }

    void decide(String email, UUID id, UUID studentId, UUID requestId, boolean approve) {
        Classroom classroom = owned(email, id);
        var prior = record(id, studentId);
        String status = approve ? "APPROVED" : "DECLINED";
        if (prior == null || !prior.requestId().equals(requestId)) throw conflict();
        if (prior.status().equals(status)) return;
        if (!prior.status().equals("PENDING")) throw conflict();
        if (approve) {
            var student = students.findById(studentId).filter(s -> Boolean.TRUE.equals(s.getActive()))
                    .orElseThrow(ClassroomAdmission::conflict);
            requireActiveStudentForUpdate(studentId);
            if (!isMember(classroom, studentId)) classroom.getStudents().add(student);
        }
        writeRecord(id, studentId, requestId, status);
    }

    void remove(String email, UUID id, UUID studentId) {
        Classroom classroom = owned(email, id);
        if (classroom.getStudents().removeIf(s -> s.getId().equals(studentId))) markRemoved(id, studentId);
    }

    public void markRemoved(UUID id, UUID studentId) {
        writeRecord(id, studentId, UUID.randomUUID(), "REMOVED");
    }

    public void resolveAdminAddition(UUID id, UUID studentId) {
        jdbc.update("update classroom_join_requests set status = 'APPROVED' where class_id = ? and student_id = ?",
                id, studentId);
    }

    private void requireActiveStudentForUpdate(UUID studentId) {
        var active = jdbc.query("select active from users where id = ? and role = 'STUDENT' for update",
                (row, index) -> row.getBoolean(1), studentId);
        if (active.isEmpty() || !active.getFirst()) throw forbidden();
    }

    private JoinRecord record(UUID id, UUID studentId) {
        return jdbc.query("select request_id, status from classroom_join_requests where class_id = ? and student_id = ?",
                (row, index) -> new JoinRecord(row.getObject(1, UUID.class), row.getString(2)), id, studentId)
                .stream().findFirst().orElse(null);
    }

    private void writeRecord(UUID id, UUID studentId, UUID requestId, String status) {
        int changed = jdbc.update("update classroom_join_requests set request_id = ?, status = ? where class_id = ? and student_id = ?",
                requestId, status, id, studentId);
        if (changed == 0) jdbc.update("insert into classroom_join_requests values (?, ?, ?, ?)",
                id, studentId, status, requestId);
    }

    private static boolean isMember(Classroom classroom, UUID studentId) {
        return classroom.getStudents().stream().anyMatch(s -> s.getId().equals(studentId));
    }

    private static Admission admission(Classroom classroom, String status) {
        return new Admission(classroom.getClassId(), classroom.getName(), classroom.getGradeLevel(), status);
    }

    private static ApiException forbidden() {
        return new ApiException("FORBIDDEN", "Không có quyền thực hiện thao tác này.", HttpStatus.FORBIDDEN);
    }

    private static ApiException unavailable() {
        return new ApiException("INVITATION_UNAVAILABLE", "Em xin cô hoặc thầy mã lớp mới nhé.", HttpStatus.NOT_FOUND);
    }

    private static ApiException conflict() {
        return new ApiException("JOIN_REQUEST_CHANGED", "Yêu cầu đã thay đổi. Hãy tải lại danh sách.", HttpStatus.CONFLICT);
    }
}

package com.mathvisionkids.api.assignment;

import com.mathvisionkids.api.classroom.Classroom;
import com.mathvisionkids.api.classroom.ClassroomRepository;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AssignmentWorkflowService {
    public record DraftRequest(UUID classId, String title, String prompt, String instructions,
                               String operationType, Integer maxScore, UUID creationRequestId) {}
    public record DraftCreationResult(AssignmentView assignment, boolean created) {}
    public record AssignmentView(UUID assignmentId, UUID classId, String className, String teacherName,
                                 String title, String prompt, String instructions, String operationType,
                                 Integer maxScore, String status, int recipientCount, Instant publishedAt) {}
    public record Recipient(UUID studentId, String displayName) {}

    private final AssignmentRepository assignments;
    private final ClassroomRepository classrooms;
    private final TeacherRepository teachers;
    private final StudentRepository students;
    private final AssignmentPublicationRepository publications;
    private final AssignmentRecipientRepository recipients;

    public AssignmentWorkflowService(AssignmentRepository assignments, ClassroomRepository classrooms,
            TeacherRepository teachers, StudentRepository students,
            AssignmentPublicationRepository publications, AssignmentRecipientRepository recipients) {
        this.assignments = assignments;
        this.classrooms = classrooms;
        this.teachers = teachers;
        this.students = students;
        this.publications = publications;
        this.recipients = recipients;
    }

    @Transactional
    public DraftCreationResult createDraft(String email, DraftRequest request) {
        validate(request);
        Teacher teacher = teacher(email);
        Classroom classroom = ownedClassroomForUpdate(request.classId(), teacher.getId());
        if (request.creationRequestId() != null) {
            Assignment previous = assignments.findByTeacher_IdAndCreationRequestId(teacher.getId(), request.creationRequestId()).orElse(null);
            if (previous != null) {
                requireSameRequest(previous, request);
                AssignmentPublication publication = publications.findByAssignmentId(previous.getAssignmentId()).orElse(null);
                int recipientCount = publication == null ? 0 : recipients.countByAssignment(previous.getAssignmentId());
                return new DraftCreationResult(view(previous, recipientCount,
                        publication == null ? null : publication.getPublishedAt()), false);
            }
        }
        Assignment assignment = new Assignment();
        assignment.setTeacher(teacher);
        assignment.setClassroom(classroom);
        assignment.setCreationRequestId(request.creationRequestId());
        assignment.setTitle(request.title().trim());
        assignment.setPrompt(request.prompt().trim());
        assignment.setInstructions(clean(request.instructions()));
        assignment.setOperationType(request.operationType());
        assignment.setMaxScore(request.maxScore());
        assignment.setStatus("DRAFT");
        return new DraftCreationResult(view(assignments.save(assignment), 0, null), true);
    }

    @Transactional
    public AssignmentView updateDraft(String email, UUID id, DraftRequest request) {
        validate(request);
        Teacher teacher = teacher(email);
        Classroom classroom = ownedClassroomForUpdate(request.classId(), teacher.getId());
        Assignment assignment = assignments.findForUpdate(id).orElseThrow(AssignmentWorkflowService::notFound);
        if (!assignment.getClassroom().getClassId().equals(classroom.getClassId())) throw forbidden();
        if (!"DRAFT".equals(assignment.getStatus())) throw conflict("Bài đã giao không thể chỉnh sửa.");
        assignment.setTitle(request.title().trim());
        assignment.setPrompt(request.prompt().trim());
        assignment.setInstructions(clean(request.instructions()));
        assignment.setOperationType(request.operationType());
        assignment.setMaxScore(request.maxScore());
        return view(assignments.save(assignment), 0, null);
    }

    @Transactional(readOnly = true)
    public List<AssignmentView> listForTeacher(String email, UUID classId) {
        Teacher teacher = teacher(email);
        ownedClassroomForRead(classId, teacher.getId());
        return assignments.findByClassroom_ClassIdOrderByCreatedAtDesc(classId).stream()
                .filter(a -> "DRAFT".equals(a.getStatus()) || "PUBLISHED".equals(a.getStatus()))
                .map(a -> view(a, recipients.countByAssignment(a.getAssignmentId()), publications.findByAssignmentId(a.getAssignmentId()).map(AssignmentPublication::getPublishedAt).orElse(null)))
                .toList();
    }

    @Transactional(readOnly = true)
    public AssignmentView teacherDetail(String email, UUID id) {
        Teacher teacher = teacher(email);
        Assignment assignment = assignments.findById(id).orElseThrow(AssignmentWorkflowService::notFound);
        ownedClassroomForRead(assignment.getClassroom().getClassId(), teacher.getId());
        return view(assignment, recipients.countByAssignment(id), publications.findByAssignmentId(id).map(AssignmentPublication::getPublishedAt).orElse(null));
    }

    @Transactional
    public AssignmentView publish(String email, UUID id) {
        Teacher teacher = teacher(email);
        UUID classId = assignments.findClassId(id).orElseThrow(AssignmentWorkflowService::notFound);
        Classroom classroom = ownedClassroomForUpdate(classId, teacher.getId());
        Assignment assignment = assignments.findForUpdate(id).orElseThrow(AssignmentWorkflowService::notFound);
        if (!assignment.getClassroom().getClassId().equals(classroom.getClassId())) throw forbidden();
        var existing = publications.findByAssignmentId(id);
        if (existing.isPresent()) return view(assignment, recipients.countByAssignment(id), existing.get().getPublishedAt());
        if (!"DRAFT".equals(assignment.getStatus())) throw conflict("Chỉ có thể giao bài đang ở trạng thái nháp.");
        List<Student> roster = classroom.getStudents().stream().filter(s -> Boolean.TRUE.equals(s.getActive())).toList();
        if (roster.size() > 50) throw new ApiException("ROSTER_LIMIT", "Lớp vượt quá giới hạn 50 học sinh cho một lần giao bài.", HttpStatus.UNPROCESSABLE_ENTITY);
        AssignmentPublication publication = publications.saveAndFlush(new AssignmentPublication(id));
        recipients.saveAll(roster.stream().map(student -> new AssignmentRecipient(publication.getPublicationId(), student.getId())).toList());
        assignment.setStatus("PUBLISHED");
        assignments.save(assignment);
        return view(assignment, roster.size(), publication.getPublishedAt());
    }

    @Transactional(readOnly = true)
    public List<Recipient> recipientList(String email, UUID id) {
        Teacher teacher = teacher(email);
        Assignment assignment = assignments.findById(id).orElseThrow(AssignmentWorkflowService::notFound);
        ownedClassroomForRead(assignment.getClassroom().getClassId(), teacher.getId());
        AssignmentPublication publication = publications.findByAssignmentId(id).orElseThrow(AssignmentWorkflowService::notFound);
        return recipients.findRoster(publication.getPublicationId());
    }

    @Transactional(readOnly = true)
    public List<AssignmentView> listForStudent(String email) {
        Student student = student(email);
        return assignments.findPublishedForCurrentMember(student.getId()).stream()
                .map(row -> view(row.getAssignment(), Math.toIntExact(row.getRecipientCount()), row.getPublishedAt())).toList();
    }

    @Transactional(readOnly = true)
    public AssignmentView studentDetail(String email, UUID id) {
        Student student = student(email);
        return assignments.findPublishedForCurrentMember(student.getId()).stream()
                .filter(row -> row.getAssignment().getAssignmentId().equals(id))
                .findFirst().map(row -> view(row.getAssignment(), Math.toIntExact(row.getRecipientCount()), row.getPublishedAt()))
                .orElseThrow(AssignmentWorkflowService::notFound);
    }

    private Teacher teacher(String email) {
        return teachers.findByEmail(email).filter(t -> Boolean.TRUE.equals(t.getActive())).orElseThrow(AssignmentWorkflowService::forbidden);
    }

    private Student student(String email) {
        return students.findByEmail(email).filter(s -> Boolean.TRUE.equals(s.getActive())).orElseThrow(AssignmentWorkflowService::notFound);
    }

    private Classroom ownedClassroomForUpdate(UUID id, UUID teacherId) {
        Classroom classroom = classrooms.findForUpdate(id).orElseThrow(AssignmentWorkflowService::notFound);
        if (!classroom.getTeacher().getId().equals(teacherId)) throw forbidden();
        return classroom;
    }

    private Classroom ownedClassroomForRead(UUID id, UUID teacherId) {
        Classroom classroom = classrooms.findById(id).orElseThrow(AssignmentWorkflowService::notFound);
        if (!classroom.getTeacher().getId().equals(teacherId)) throw forbidden();
        return classroom;
    }

    private static AssignmentView view(Assignment a, int count, Instant publishedAt) {
        return new AssignmentView(a.getAssignmentId(), a.getClassroom().getClassId(), a.getClassroom().getName(),
                a.getClassroom().getTeacher().getDisplayName(), a.getTitle(), a.getPrompt(), a.getInstructions(),
                a.getOperationType(), a.getMaxScore(), a.getStatus(), count, publishedAt);
    }

    private static void validate(DraftRequest r) {
        if (r.classId() == null || r.title() == null || r.title().isBlank() || r.title().length() > 255
                || r.prompt() == null || r.prompt().isBlank() || r.prompt().length() > 10000
                || r.instructions() != null && r.instructions().length() > 3000
                || r.operationType() == null || !List.of("VERTICAL_ADDITION", "VERTICAL_SUBTRACTION", "ADDITION", "SUBTRACTION").contains(r.operationType())
                || r.maxScore() == null || r.maxScore() < 1 || r.maxScore() > 100) {
            throw new ApiException("VALIDATION_ERROR", "Thông tin bài tập chưa hợp lệ.", HttpStatus.BAD_REQUEST);
        }
    }

    private static String clean(String value) { return value == null || value.isBlank() ? null : value.trim(); }

    private static void requireSameRequest(Assignment a, DraftRequest r) {
        if (!a.getClassroom().getClassId().equals(r.classId()) || !a.getTitle().equals(r.title().trim())
                || !a.getPrompt().equals(r.prompt().trim()) || !java.util.Objects.equals(a.getInstructions(), clean(r.instructions()))
                || !a.getOperationType().equals(r.operationType()) || !a.getMaxScore().equals(r.maxScore())) {
            throw conflict("Yêu cầu tạo này đã được dùng với nội dung khác.");
        }
    }

    private static ApiException notFound() { return new ApiException("NOT_FOUND", "Không tìm thấy bài tập.", HttpStatus.NOT_FOUND); }
    private static ApiException forbidden() { return new ApiException("FORBIDDEN", "Không có quyền truy cập lớp học này.", HttpStatus.FORBIDDEN); }
    private static ApiException conflict(String message) { return new ApiException("ASSIGNMENT_CONFLICT", message, HttpStatus.CONFLICT); }
}

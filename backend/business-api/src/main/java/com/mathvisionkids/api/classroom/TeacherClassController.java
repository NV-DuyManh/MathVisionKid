package com.mathvisionkids.api.classroom;

import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import com.mathvisionkids.api.user.UserResponse;
import com.mathvisionkids.api.common.ApiException;
import org.springframework.http.HttpStatus;

import java.security.Principal;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/teacher/classes")
@Transactional(readOnly = true)
public class TeacherClassController {
    
    private final ClassroomRepository classroomRepository;
    private final TeacherRepository teacherRepository;

    public TeacherClassController(ClassroomRepository classroomRepository, TeacherRepository teacherRepository) {
        this.classroomRepository = classroomRepository;
        this.teacherRepository = teacherRepository;
    }

    private ClassroomResponse toResponse(Classroom classroom, boolean includeStudents) {
        ClassroomResponse response = new ClassroomResponse();
        response.setClassId(classroom.getClassId());
        response.setName(classroom.getName());
        response.setGradeLevel(classroom.getGradeLevel());
        response.setJoinMode(classroom.getJoinMode());
        response.setAcademicYear(classroom.getAcademicYear());
        response.setStudentCount(classroom.getStudents().size());

        if (includeStudents && classroom.getStudents() != null) {
            List<UserResponse> students = classroom.getStudents().stream().map(student -> {
                UserResponse ur = new UserResponse();
                ur.setUserId(student.getId());
                ur.setEmail(student.getEmail());
                ur.setDisplayName(student.getDisplayName());
                ur.setGradeLevel(student.getGradeLevel());
                return ur;
            }).collect(Collectors.toList());
            response.setStudents(students);
        }

        return response;
    }

    public record CreateClassRequest(
            @jakarta.validation.constraints.NotBlank @jakarta.validation.constraints.Size(max = 120) String name,
            @jakarta.validation.constraints.NotNull @jakarta.validation.constraints.Min(1)
            @jakarta.validation.constraints.Max(5) Integer gradeLevel,
            @jakarta.validation.constraints.NotNull UUID requestId) {}

    @PostMapping
    @Transactional
    public ResponseEntity<ClassroomResponse> createClass(
            @jakarta.validation.Valid @RequestBody CreateClassRequest request, Principal principal) {
        Teacher teacher = teacherRepository.findByEmail(principal.getName())
                .filter(value -> Boolean.TRUE.equals(value.getActive()))
                .orElseThrow(() -> new ApiException("FORBIDDEN", "Không có quyền tạo lớp.", HttpStatus.FORBIDDEN));
        teacherRepository.lockForCreation(teacher.getId()).orElseThrow();
        String name = request.name().strip();
        var previous = classroomRepository.findByCreatedByTeacherIdAndCreationRequestId(teacher.getId(), request.requestId());
        if (previous.isPresent()) {
            Classroom classroom = previous.get();
            if (!classroom.getTeacher().getId().equals(teacher.getId())) {
                throw new ApiException("FORBIDDEN", "Lớp đã được bàn giao.", HttpStatus.FORBIDDEN);
            }
            if (!classroom.getName().equals(name) || !classroom.getGradeLevel().equals(request.gradeLevel())) {
                throw new ApiException("CLASSROOM_REQUEST_CONFLICT", "Yêu cầu đã được dùng để tạo lớp khác.", HttpStatus.CONFLICT);
            }
            return ResponseEntity.ok(toResponse(classroom, false));
        }
        Classroom classroom = new Classroom();
        classroom.setTeacher(teacher);
        classroom.setName(name);
        classroom.setGradeLevel(request.gradeLevel());
        classroom.setCreatedByTeacherId(teacher.getId());
        classroom.setCreationRequestId(request.requestId());
        return ResponseEntity.status(HttpStatus.CREATED).body(toResponse(classroomRepository.save(classroom), false));
    }

    @GetMapping
    public ResponseEntity<List<ClassroomResponse>> getClasses(Principal principal) {
        Teacher teacher = teacherRepository.findByEmail(principal.getName()).orElseThrow();
        List<ClassroomResponse> responses = classroomRepository.findByTeacher_Id(teacher.getId())
                .stream()
                .map(c -> toResponse(c, false))
                .collect(Collectors.toList());
        return ResponseEntity.ok(responses);
    }

    @GetMapping("/{classId}")
    public ResponseEntity<ClassroomResponse> getClassroom(@PathVariable UUID classId, Principal principal) {
        Teacher teacher = teacherRepository.findByEmail(principal.getName()).orElseThrow();
        Classroom classroom = classroomRepository.findById(classId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Classroom not found", HttpStatus.NOT_FOUND));

        if (!classroom.getTeacher().getId().equals(teacher.getId())) {
            throw new ApiException("FORBIDDEN", "Not authorized to view this classroom", HttpStatus.FORBIDDEN);
        }

        return ResponseEntity.ok(toResponse(classroom, true));
    }
}

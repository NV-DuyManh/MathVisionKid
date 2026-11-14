package com.mathvisionkids.api.classroom;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.security.Principal;
import java.util.List;
import java.util.UUID;
import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1")
class ClassroomAdmissionController {
    private final ClassroomAdmission admission;

    ClassroomAdmissionController(ClassroomAdmission admission) {
        this.admission = admission;
    }

    record Credential(@NotBlank @Size(max = 64) String credential) {}
    record Join(@NotBlank @Size(max = 64) String credential, @NotNull UUID classId, @NotNull UUID generation) {}
    record Decision(@NotNull UUID requestId, @NotNull Boolean approve) {}
    record Update(@Pattern(regexp = "(?s).*\\S.*") @Size(max = 120) String name,
                  @Min(1) @Max(5) Integer gradeLevel,
                  @Pattern(regexp = "AUTO_JOIN|APPROVAL_REQUIRED") String joinMode) {}

    @PatchMapping("/teacher/classes/{id}")
    ResponseEntity<Void> update(Principal actor, @PathVariable UUID id, @Valid @RequestBody Update request) {
        admission.update(actor.getName(), id, request.name(), request.gradeLevel(), request.joinMode());
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/teacher/classes/{id}/invitation")
    ResponseEntity<ClassroomAdmission.Invitation> invitation(Principal actor, @PathVariable UUID id) {
        var result = admission.invitation(actor.getName(), id);
        return result == null ? ResponseEntity.noContent().build() : privateResponse(result);
    }

    @PostMapping("/teacher/classes/{id}/invitation")
    ResponseEntity<ClassroomAdmission.Invitation> rotate(Principal actor, @PathVariable UUID id) {
        return privateResponse(admission.rotate(actor.getName(), id));
    }

    @DeleteMapping("/teacher/classes/{id}/invitation")
    ResponseEntity<Void> disable(Principal actor, @PathVariable UUID id) {
        admission.disable(actor.getName(), id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/teacher/classes/{id}/join-requests")
    ResponseEntity<List<ClassroomAdmission.Request>> requests(Principal actor, @PathVariable UUID id) {
        return privateResponse(admission.requests(actor.getName(), id));
    }

    @PutMapping("/teacher/classes/{id}/join-requests/{studentId}")
    ResponseEntity<Void> decide(Principal actor, @PathVariable UUID id, @PathVariable UUID studentId,
                                @Valid @RequestBody Decision request) {
        admission.decide(actor.getName(), id, studentId, request.requestId(), request.approve());
        return ResponseEntity.noContent().build();
    }

    @DeleteMapping("/teacher/classes/{id}/students/{studentId}")
    ResponseEntity<Void> remove(Principal actor, @PathVariable UUID id, @PathVariable UUID studentId) {
        admission.remove(actor.getName(), id, studentId);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/student/classes")
    ResponseEntity<List<ClassroomAdmission.Admission>> myClasses(Principal actor) {
        return privateResponse(admission.myClasses(actor.getName()));
    }

    @PostMapping("/student/classes/invitation-preview")
    ResponseEntity<ClassroomAdmission.Preview> preview(Principal actor, @Valid @RequestBody Credential request) {
        admission.checkJoinLimit(actor.getName());
        return privateResponse(admission.preview(actor.getName(), request.credential()));
    }

    @PostMapping("/student/classes/join")
    ResponseEntity<ClassroomAdmission.Admission> join(Principal actor, @Valid @RequestBody Join request) {
        admission.checkJoinLimit(actor.getName());
        return privateResponse(admission.join(actor.getName(), request.credential(), request.classId(), request.generation()));
    }

    private static <T> ResponseEntity<T> privateResponse(T body) {
        return ResponseEntity.ok().cacheControl(CacheControl.noStore()).body(body);
    }
}

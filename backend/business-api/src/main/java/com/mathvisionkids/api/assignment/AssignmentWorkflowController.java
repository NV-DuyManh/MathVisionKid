package com.mathvisionkids.api.assignment;

import java.security.Principal;
import java.util.List;
import java.util.UUID;
import org.springframework.http.CacheControl;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
public class AssignmentWorkflowController {
    private final AssignmentWorkflowService workflow;

    public AssignmentWorkflowController(AssignmentWorkflowService workflow) {
        this.workflow = workflow;
    }

    @GetMapping("/teacher/classes/{classId}/assignments")
    public ResponseEntity<List<AssignmentWorkflowService.AssignmentView>> teacherList(
            Principal actor, @PathVariable UUID classId) {
        return privateResponse(workflow.listForTeacher(actor.getName(), classId));
    }

    @PostMapping("/teacher/assignments/drafts")
    public ResponseEntity<AssignmentWorkflowService.AssignmentView> createDraft(
            Principal actor, @RequestBody AssignmentWorkflowService.DraftRequest request) {
        var result = workflow.createDraft(actor.getName(), request);
        return privateResponse(result.assignment(), result.created() ? HttpStatus.CREATED : HttpStatus.OK);
    }

    @GetMapping("/teacher/assignments/{id}/workflow")
    public ResponseEntity<AssignmentWorkflowService.AssignmentView> teacherDetail(
            Principal actor, @PathVariable UUID id) {
        return privateResponse(workflow.teacherDetail(actor.getName(), id));
    }

    @PutMapping("/teacher/assignments/{id}/draft")
    public ResponseEntity<AssignmentWorkflowService.AssignmentView> updateDraft(
            Principal actor, @PathVariable UUID id, @RequestBody AssignmentWorkflowService.DraftRequest request) {
        return privateResponse(workflow.updateDraft(actor.getName(), id, request));
    }

    @PostMapping("/teacher/assignments/{id}/publish")
    public ResponseEntity<AssignmentWorkflowService.AssignmentView> publish(
            Principal actor, @PathVariable UUID id) {
        return privateResponse(workflow.publish(actor.getName(), id));
    }

    @GetMapping("/teacher/assignments/{id}/recipients")
    public ResponseEntity<List<AssignmentWorkflowService.Recipient>> recipients(
            Principal actor, @PathVariable UUID id) {
        return privateResponse(workflow.recipientList(actor.getName(), id));
    }

    @GetMapping("/student/assignments")
    public ResponseEntity<List<AssignmentWorkflowService.AssignmentView>> studentList(Principal actor) {
        return privateResponse(workflow.listForStudent(actor.getName()));
    }

    @GetMapping("/student/assignments/{id}")
    public ResponseEntity<AssignmentWorkflowService.AssignmentView> studentDetail(
            Principal actor, @PathVariable UUID id) {
        return privateResponse(workflow.studentDetail(actor.getName(), id));
    }

    private static <T> ResponseEntity<T> privateResponse(T body) {
        return ResponseEntity.ok().cacheControl(CacheControl.noStore()).body(body);
    }

    private static <T> ResponseEntity<T> privateResponse(T body, HttpStatus status) {
        return ResponseEntity.status(status).cacheControl(CacheControl.noStore()).body(body);
    }
}

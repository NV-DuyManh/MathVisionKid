package com.mathvisionkids.api.submission;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.security.Principal;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/student/submissions")
public class StudentSubmissionController {

    private final SubmissionService submissionService;

    public StudentSubmissionController(SubmissionService submissionService) {
        this.submissionService = submissionService;
    }

    @PostMapping
    public ResponseEntity<SubmissionResponse> createSubmission(
            @RequestParam("image") MultipartFile image,
            @RequestParam(value = "source", required = false) String source,
            Principal principal) {
        
        SubmissionResponse response = submissionService.createStudentSubmission(principal.getName(), image, source);
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(response);
    }

    @GetMapping("/{submissionId}")
    public ResponseEntity<SubmissionResponse> getSubmission(@PathVariable UUID submissionId, Principal principal) {
        Submission submission = submissionService.getStudentSubmission(principal.getName(), submissionId);
        SubmissionResponse response = new SubmissionResponse();
        response.setSubmissionId(submission.getSubmissionId());
        response.setStatus(submission.getStatus());
        response.setCreatedAt(submission.getCreatedAt());
        return ResponseEntity.ok(response);
    }

    @PostMapping("/{submissionId}/confirm-token")
    public ResponseEntity<Void> confirmToken(@PathVariable UUID submissionId, 
                                             @RequestParam String tokenClass, 
                                             @RequestParam String newClass, 
                                             Principal principal) {
        submissionService.confirmToken(principal.getName(), submissionId, tokenClass, newClass);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/{submissionId}/retry")
    public ResponseEntity<Void> retrySubmission(@PathVariable UUID submissionId, 
                                                @RequestParam("image") MultipartFile image,
                                                @RequestParam(value = "source", required = false) String source,
                                                Principal principal) {
        submissionService.retrySubmission(principal.getName(), submissionId, image, source);
        return ResponseEntity.ok().build();
    }
}

package com.mathvisionkids.api.submission;

import com.mathvisionkids.api.analysis.AnalysisResultRepository;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.security.Principal;
import java.util.UUID;
import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1/student/submissions")
public class StudentSubmissionController {

    private final SubmissionService submissionService;
    private final AnalysisResultRepository analysisResultRepository;

    public StudentSubmissionController(SubmissionService submissionService,
                                       AnalysisResultRepository analysisResultRepository) {
        this.submissionService = submissionService;
        this.analysisResultRepository = analysisResultRepository;
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
        return ResponseEntity.ok(submissionService.getStudentSubmissionResponse(principal.getName(), submissionId));
    }

    @PostMapping("/{submissionId}/confirm-token")
    public ResponseEntity<SubmissionResponse> confirmToken(@PathVariable UUID submissionId,
                                             @Valid @RequestBody TokenConfirmationRequest request,
                                             Principal principal) {
        return ResponseEntity.ok(submissionService.confirmToken(principal.getName(), submissionId, request));
    }

    @PostMapping("/{submissionId}/retry")
    public ResponseEntity<SubmissionResponse> retrySubmission(@PathVariable UUID submissionId,
                                                @RequestParam("image") MultipartFile image,
                                                @RequestParam(value = "source", required = false) String source,
                                                Principal principal) {
        submissionService.retrySubmission(principal.getName(), submissionId, image, source);
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(submissionService.getStudentSubmissionResponse(principal.getName(), submissionId));
    }
}

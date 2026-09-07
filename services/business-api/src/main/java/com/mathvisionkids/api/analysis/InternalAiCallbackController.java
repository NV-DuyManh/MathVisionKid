package com.mathvisionkids.api.analysis;

import com.mathvisionkids.api.submission.Submission;
import com.mathvisionkids.api.submission.SubmissionRepository;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/internal/v1/ai/jobs")
public class InternalAiCallbackController {

    private final AiJobRepository aiJobRepository;
    private final SubmissionRepository submissionRepository;
    private final AnalysisResultRepository analysisResultRepository;
    private final String internalApiKey;

    public InternalAiCallbackController(AiJobRepository aiJobRepository, 
                                        SubmissionRepository submissionRepository, 
                                        AnalysisResultRepository analysisResultRepository,
                                        @org.springframework.beans.factory.annotation.Value("${ai.callback.api-key:secret-key-default}") String internalApiKey) {
        this.aiJobRepository = aiJobRepository;
        this.submissionRepository = submissionRepository;
        this.analysisResultRepository = analysisResultRepository;
        this.internalApiKey = internalApiKey;
    }

    @PostMapping("/{jobId}/callback")
    public ResponseEntity<Void> aiJobCompleted(@PathVariable("jobId") UUID jobId,
                                               @RequestHeader(value = "X-Internal-API-Key", required = false) String apiKey,
                                               @RequestBody AiCallbackRequest request) {
        if (apiKey == null || !apiKey.equals(internalApiKey)) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        AiJob job = aiJobRepository.findById(jobId).orElseThrow(() -> new com.mathvisionkids.api.common.ApiException("NOT_FOUND", "Job not found", HttpStatus.NOT_FOUND));
        
        if ("COMPLETED".equals(job.getStatus())) {
            // Idempotent return
            return ResponseEntity.ok().build();
        }

        job.setStatus("COMPLETED");
        job.setCompletedAt(Instant.now());
        aiJobRepository.save(job);
        
        Submission submission = job.getSubmission();
        
        if (!"PROCESSING".equals(submission.getStatus())) {
             return ResponseEntity.status(HttpStatus.CONFLICT).build();
        }
        
        submission.setStatus("PROPOSED_GRADE");
        submissionRepository.save(submission);
        
        // Processing result data would go here
        
        return ResponseEntity.ok().build();
    }
}

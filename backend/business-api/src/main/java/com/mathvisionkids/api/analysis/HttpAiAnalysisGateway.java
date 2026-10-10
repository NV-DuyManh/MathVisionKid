package com.mathvisionkids.api.analysis;

import com.mathvisionkids.api.submission.Submission;
import com.mathvisionkids.api.submission.SubmissionRepository;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public class HttpAiAnalysisGateway implements AiAnalysisGateway {
    public static final int MAX_DIGITS = 6;

    private final SubmissionRepository submissionRepository;
    private final AiJobRepository aiJobRepository;
    private final com.mathvisionkids.api.submission.SubmissionImageRepository submissionImageRepository;
    private final String aiServiceUrl;
    private final RestTemplate restTemplate;

    private final org.springframework.transaction.support.TransactionTemplate transactionTemplate;

    public HttpAiAnalysisGateway(
            SubmissionRepository submissionRepository,
            AiJobRepository aiJobRepository,
            com.mathvisionkids.api.submission.SubmissionImageRepository submissionImageRepository,
            String aiServiceUrl) {
        this(submissionRepository, aiJobRepository, submissionImageRepository, aiServiceUrl, createDefaultRestTemplate(), null);
    }

    public HttpAiAnalysisGateway(
            SubmissionRepository submissionRepository,
            AiJobRepository aiJobRepository,
            com.mathvisionkids.api.submission.SubmissionImageRepository submissionImageRepository,
            String aiServiceUrl,
            RestTemplate restTemplate) {
        this(submissionRepository, aiJobRepository, submissionImageRepository, aiServiceUrl, restTemplate, null);
    }

    public HttpAiAnalysisGateway(
            SubmissionRepository submissionRepository,
            AiJobRepository aiJobRepository,
            com.mathvisionkids.api.submission.SubmissionImageRepository submissionImageRepository,
            String aiServiceUrl,
            RestTemplate restTemplate,
            org.springframework.transaction.support.TransactionTemplate transactionTemplate) {
        this.submissionRepository = submissionRepository;
        this.aiJobRepository = aiJobRepository;
        this.submissionImageRepository = submissionImageRepository;
        this.aiServiceUrl = aiServiceUrl;
        this.restTemplate = restTemplate != null ? restTemplate : createDefaultRestTemplate();
        this.transactionTemplate = transactionTemplate;
    }

    static RestTemplate createDefaultRestTemplate() {
        org.springframework.http.client.SimpleClientHttpRequestFactory factory =
                new org.springframework.http.client.SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);
        factory.setReadTimeout(10000);
        return new RestTemplate(factory);
    }

    private static final org.slf4j.Logger logger = org.slf4j.LoggerFactory.getLogger(HttpAiAnalysisGateway.class);

    private static class JobCreationResult {
        final UUID jobId;
        final String submissionId;
        final String imageRef;
        final List<String> allowedOps;
        final String policyMode;
        final AiJob job;

        JobCreationResult(UUID jobId, String submissionId, String imageRef, List<String> allowedOps, String policyMode, AiJob job) {
            this.jobId = jobId;
            this.submissionId = submissionId;
            this.imageRef = imageRef;
            this.allowedOps = allowedOps;
            this.policyMode = policyMode;
            this.job = job;
        }
    }

    @Override
    public void analyze(UUID submissionId) {
        logger.info("HttpAiAnalysisGateway analyze called for submissionId: {}", submissionId);

        java.util.function.Supplier<JobCreationResult> creationSupplier = () -> {
            Submission submission = (transactionTemplate != null
                    ? submissionRepository.findForUpdate(submissionId)
                    : submissionRepository.findById(submissionId)).orElseThrow();
            if (!"PROCESSING".equals(submission.getStatus())) return null;

            // ── 1. Spring creates AiJob first → Spring owns the jobId ──────────
            AiJob job = new AiJob();
            job.setSubmission(submission);
            job.setStatus("PENDING");
            job = aiJobRepository.save(job);
            UUID springJobId = job.getJobId();

            // ── 2. Resolve image reference ──────────────────────────────────────
            String imageRef = submissionImageRepository.findFirstBySubmission_SubmissionIdOrderByCreatedAtDesc(submissionId)
                    .map(com.mathvisionkids.api.submission.SubmissionImage::getFilePath)
                    .map(path -> {
                        if (path.startsWith("fixture://") || path.startsWith("minio://")) {
                            return path;
                        }
                        return "minio://mathvision/" + path;
                    })
                    .orElse(null);

            // ── 3. Determine policyMode explicitly ──────────────────────────────
            String policyMode = determinePolicyMode(submission);

            // ── 4. Determine allowed operations ────────────────────────────────
            List<String> allowedOps = new ArrayList<>();
            if (submission.getAssignment() != null && submission.getAssignment().getOperationType() != null) {
                String operation = submission.getAssignment().getOperationType();
                allowedOps.add("ADDITION".equals(operation) ? "VERTICAL_ADDITION"
                        : "SUBTRACTION".equals(operation) ? "VERTICAL_SUBTRACTION" : operation);
            } else {
                allowedOps.add("VERTICAL_ADDITION");
                allowedOps.add("VERTICAL_SUBTRACTION");
            }

            return new JobCreationResult(springJobId, submissionId.toString(), imageRef, allowedOps, policyMode, job);
        };

        JobCreationResult result;
        if (transactionTemplate != null) {
            result = transactionTemplate.execute(status -> creationSupplier.get());
        } else {
            result = creationSupplier.get();
        }
        if (result == null) return;

        // ── 5. Build canonical job request including Spring's jobId ─────────
        Map<String, Object> request = new HashMap<>();
        request.put("jobId", result.jobId.toString());    // Spring-owned jobId must survive full pipeline
        request.put("submissionId", result.submissionId);
        request.put("imageReference", result.imageRef);
        request.put("allowedOperations", result.allowedOps);
        request.put("maxDigits", MAX_DIGITS);
        request.put("oneExerciseOnly", true);
        request.put("policyVersion", "v1.2");
        request.put("policyMode", result.policyMode);           // Always explicit — never rely on FastAPI default

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);

        try {
            if (result.imageRef == null) throw new IllegalStateException("Submission image is missing");
            logger.info("Calling AI service at {} for jobId: {} submissionId: {} policyMode: {}",
                    aiServiceUrl, result.jobId, result.submissionId, result.policyMode);
            ResponseEntity<?> response = restTemplate.postForEntity(aiServiceUrl, entity, Map.class);
            final boolean success = response.getStatusCode().is2xxSuccessful();
            if (!success) throw new IllegalStateException("AI service rejected the job");

            if (transactionTemplate != null) {
                transactionTemplate.executeWithoutResult(status -> {
                    submissionRepository.findForUpdate(submissionId).orElseThrow();
                    AiJob currentJob = aiJobRepository.findById(result.jobId).orElse(result.job);
                    if (!java.util.Set.of("COMPLETED", "SUPERSEDED").contains(currentJob.getStatus())) {
                        currentJob.setStatus(success ? "QUEUED" : "FAILED");
                        aiJobRepository.save(currentJob);
                    }
                });
            } else {
                AiJob currentJob = aiJobRepository.findById(result.jobId).orElse(result.job);
                if (!java.util.Set.of("COMPLETED", "SUPERSEDED").contains(currentJob.getStatus())) {
                    currentJob.setStatus(success ? "QUEUED" : "FAILED");
                    aiJobRepository.save(currentJob);
                }
            }
            logger.info("AI service response: {} for jobId: {}", response.getStatusCode(), result.jobId);
        } catch (Exception e) {
            logger.error("Failed calling AI service for jobId: {}", result.jobId, e);
            if (transactionTemplate != null) {
                transactionTemplate.executeWithoutResult(status -> {
                    Submission currentSubmission = submissionRepository.findForUpdate(submissionId).orElseThrow();
                    AiJob currentJob = aiJobRepository.findById(result.jobId).orElse(result.job);
                    if (!java.util.Set.of("COMPLETED", "SUPERSEDED").contains(currentJob.getStatus())) {
                        currentJob.setStatus("FAILED");
                        aiJobRepository.save(currentJob);
                        settleDispatchFailure(currentSubmission, currentJob);
                    }
                });
            } else {
                AiJob currentJob = aiJobRepository.findById(result.jobId).orElse(result.job);
                if (!java.util.Set.of("COMPLETED", "SUPERSEDED").contains(currentJob.getStatus())) {
                    currentJob.setStatus("FAILED");
                    aiJobRepository.save(currentJob);
                    settleDispatchFailure(submissionRepository.findById(submissionId).orElseThrow(), currentJob);
                }
            }
        }
    }

    private void settleDispatchFailure(Submission submission, AiJob failedJob) {
        AiJob latest = aiJobRepository.findFirstBySubmission_SubmissionIdOrderBySubmittedAtDesc(submission.getSubmissionId())
                .orElse(failedJob);
        if (latest.getJobId().equals(failedJob.getJobId()) && "PROCESSING".equals(submission.getStatus())) {
            submission.setStatus("REVIEW_REQUIRED");
            submissionRepository.save(submission);
        }
    }

    /**
     * Determines policyMode based on the submission batch context.
     * All Batch records are teacher-initiated grading batches (they have a teacher FK).
     * Absence of a batch means student self-submission flow → STUDENT.
     */
    String determinePolicyMode(Submission submission) {
        if (submission.getBatch() != null) {
            return "TEACHER";
        }
        return "STUDENT";
    }
}

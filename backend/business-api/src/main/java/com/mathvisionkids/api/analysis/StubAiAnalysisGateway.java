package com.mathvisionkids.api.analysis;

import com.mathvisionkids.api.audit.AuditEvent;
import com.mathvisionkids.api.audit.AuditEventRepository;
import com.mathvisionkids.api.submission.Submission;
import com.mathvisionkids.api.submission.SubmissionRepository;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.HashMap;
import java.util.UUID;


public class StubAiAnalysisGateway implements AiAnalysisGateway {

    private final SubmissionRepository submissionRepository;
    private final AnalysisResultRepository analysisResultRepository;
    private final AuditEventRepository auditEventRepository;
    private final AiJobRepository aiJobRepository;
    private final TransactionTemplate transactions;

    public StubAiAnalysisGateway(SubmissionRepository submissionRepository, AnalysisResultRepository analysisResultRepository,
                                 AuditEventRepository auditEventRepository, AiJobRepository aiJobRepository,
                                 TransactionTemplate transactions) {
        this.submissionRepository = submissionRepository;
        this.analysisResultRepository = analysisResultRepository;
        this.auditEventRepository = auditEventRepository;
        this.aiJobRepository = aiJobRepository;
        this.transactions = transactions;
    }

    @Override
    public void analyze(UUID submissionId) {
        UUID jobId = transactions.execute(status -> {
            Submission submission = submissionRepository.findForUpdate(submissionId).orElseThrow();
            if (!"PROCESSING".equals(submission.getStatus())) return null;
            AiJob job = new AiJob();
            job.setSubmission(submission);
            job.setStatus("PENDING");
            return aiJobRepository.save(job).getJobId();
        });
        if (jobId == null) return;
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Stub analysis interrupted", e);
        }

        transactions.executeWithoutResult(status -> {
            Submission submission = submissionRepository.findForUpdate(submissionId).orElseThrow();
            AiJob latest = aiJobRepository.findFirstBySubmission_SubmissionIdOrderBySubmittedAtDesc(submissionId).orElseThrow();
            if (!"PROCESSING".equals(submission.getStatus()) || !jobId.equals(latest.getJobId())
                    || "SUPERSEDED".equals(latest.getStatus())) {
                return;
            }

            // Create fake analysis result
            AnalysisResult result = analysisResultRepository.findBySubmission_SubmissionId(submissionId)
                    .orElseGet(AnalysisResult::new);
            result.setSubmission(submission);
            result.setStatus("SUCCESS");
            
            // Example stubbed outcome - normally depends on fixture, but we'll default to FEEDBACK_READY for simple flow
            result.setConfidence(0.95);
            result.setGradeProposal(new HashMap<>() {{
                put("score", 95);
                put("isOfficial", false);
            }});
            result.setModelVersion("stub-v1");
            
            analysisResultRepository.save(result);
            
            latest.setStatus("COMPLETED");
            aiJobRepository.save(latest);

            submission.setStatus("PROPOSED_GRADE"); // Teacher batch grading: PROPOSED_GRADE. Student tutoring: FEEDBACK_READY.
            submissionRepository.save(submission);

            AuditEvent auditEvent = new AuditEvent();
            auditEvent.setSubmission(submission);
            auditEvent.setEventType("AI_RESULT_CREATED");
            auditEventRepository.save(auditEvent);

        });
    }
}

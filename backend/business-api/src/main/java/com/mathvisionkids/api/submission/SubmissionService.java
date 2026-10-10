package com.mathvisionkids.api.submission;

import com.mathvisionkids.api.analysis.AiAnalysisGateway;
import com.mathvisionkids.api.audit.AuditEvent;
import com.mathvisionkids.api.audit.AuditEventRepository;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.analysis.TeacherDecision;
import com.mathvisionkids.api.analysis.TeacherDecisionRepository;
import com.mathvisionkids.api.analysis.AnalysisResult;
import com.mathvisionkids.api.analysis.AnalysisResultRepository;
import com.mathvisionkids.api.analysis.AiJob;
import com.mathvisionkids.api.analysis.AiJobRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Map;
import java.util.UUID;

@Service
public class SubmissionService {
    private final SubmissionRepository submissionRepository;
    private final SubmissionImageRepository submissionImageRepository;
    private final ObjectStorageService objectStorageService;
    private final AiAnalysisGateway aiAnalysisGateway;
    private final AuditEventRepository auditEventRepository;
    private final StudentRepository studentRepository;
    private final TeacherRepository teacherRepository;
    private final TeacherDecisionRepository teacherDecisionRepository;
    private final AnalysisResultRepository analysisResultRepository;
    private final AiJobRepository aiJobRepository;

    public SubmissionService(SubmissionRepository submissionRepository,
                             SubmissionImageRepository submissionImageRepository,
                             ObjectStorageService objectStorageService,
                             AiAnalysisGateway aiAnalysisGateway,
                             AuditEventRepository auditEventRepository,
                             StudentRepository studentRepository,
                             TeacherRepository teacherRepository,
                             TeacherDecisionRepository teacherDecisionRepository,
                             AnalysisResultRepository analysisResultRepository,
                             AiJobRepository aiJobRepository) {
        this.submissionRepository = submissionRepository;
        this.submissionImageRepository = submissionImageRepository;
        this.objectStorageService = objectStorageService;
        this.aiAnalysisGateway = aiAnalysisGateway;
        this.auditEventRepository = auditEventRepository;
        this.studentRepository = studentRepository;
        this.teacherRepository = teacherRepository;
        this.teacherDecisionRepository = teacherDecisionRepository;
        this.analysisResultRepository = analysisResultRepository;
        this.aiJobRepository = aiJobRepository;
    }

    @Transactional
    public SubmissionResponse createStudentSubmission(String email, MultipartFile file, String source) {
        Student student = studentRepository.findByEmail(email)
                .map(u -> studentRepository.findById(u.getId()).orElse(null))
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Student not found", HttpStatus.NOT_FOUND));
        
        if (file == null || file.isEmpty()) {
            throw new ApiException("VALIDATION_ERROR", "Image is missing", HttpStatus.BAD_REQUEST);
        }

        String contentType = file.getContentType();
        if (contentType == null || (!contentType.equals("image/jpeg") && !contentType.equals("image/png") && !contentType.equals("image/webp"))) {
            throw new ApiException("UNSUPPORTED_MEDIA_TYPE", "Only JPEG, PNG, and WebP are supported", HttpStatus.UNSUPPORTED_MEDIA_TYPE);
        }

        try {
            String filePath = objectStorageService.store(file, "submissions");

            Submission submission = new Submission();
            submission.setStudent(student);
            submission.setStatus("IMAGE_UPLOADED");
            submissionRepository.save(submission);

            SubmissionImage image = new SubmissionImage();
            image.setSubmission(submission);
            image.setFilePath(filePath);
            image.setContentType(contentType);
            image.setFileSize(file.getSize());
            image.setSource(source);
            submissionImageRepository.save(image);

            AuditEvent auditEvent = new AuditEvent();
            auditEvent.setSubmission(submission);
            auditEvent.setUser(student);
            auditEvent.setEventType("SUBMISSION_CREATED");
            auditEventRepository.save(auditEvent);

            // Transition to PROCESSING
            submission.setStatus("PROCESSING");
            submissionRepository.save(submission);

            AuditEvent auditEvent2 = new AuditEvent();
            auditEvent2.setSubmission(submission);
            auditEvent2.setUser(student);
            auditEvent2.setEventType("AI_PROCESSING_STARTED");
            auditEventRepository.save(auditEvent2);
            final UUID studentSubmissionId = submission.getSubmissionId();
            dispatchAfterCommit(studentSubmissionId);

            SubmissionResponse response = new SubmissionResponse();
            response.setSubmissionId(submission.getSubmissionId());
            response.setStatus(submission.getStatus());
            response.setCreatedAt(submission.getCreatedAt());
            return response;
        } catch (IOException e) {
            throw new ApiException("INTERNAL_ERROR", "Failed to store image", HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @Transactional(readOnly = true)
    public Submission getStudentSubmission(String email, UUID submissionId) {
        Student student = studentRepository.findByEmail(email)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Student not found", HttpStatus.NOT_FOUND));
        
        Submission submission = submissionRepository.findById(submissionId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Submission not found", HttpStatus.NOT_FOUND));

        if (submission.getStudent() == null || !submission.getStudent().getId().equals(student.getId())) {
            throw new ApiException("FORBIDDEN", "Not authorized", HttpStatus.FORBIDDEN);
        }
        
        return submission;
    }

    @Transactional(readOnly = true)
    public SubmissionResponse getStudentSubmissionResponse(String email, UUID submissionId) {
        return toResponse(getStudentSubmission(email, submissionId));
    }

    private SubmissionResponse toResponse(Submission submission) {
        SubmissionResponse response = new SubmissionResponse();
        response.setSubmissionId(submission.getSubmissionId());
        response.setStatus(submission.getStatus());
        response.setCreatedAt(submission.getCreatedAt());
        AiJob latest = aiJobRepository.findFirstBySubmission_SubmissionIdOrderBySubmittedAtDesc(submission.getSubmissionId()).orElse(null);
        if (latest != null && !"SUPERSEDED".equals(latest.getStatus())) response.setJobId(latest.getJobId());
        if ("PROCESSING".equals(submission.getStatus())) return response;
        if (latest != null && "FAILED".equals(latest.getStatus())) {
            response.setReasonCode("AI_RUNTIME_ERROR");
            response.setStudentFeedback(Map.of("title", "Chưa thể kiểm tra bài", "hint",
                    "Em có thể thử lại ảnh bài làm. MathVision chưa có đủ kết quả để kết luận.", "revealAnswer", false));
            return response;
        }
        analysisResultRepository.findBySubmission_SubmissionId(submission.getSubmissionId()).ifPresent(result -> {
            Map<String, Object> reasons = result.getReviewReasons();
            if (latest != null && reasons != null && reasons.get("jobId") != null &&
                    !latest.getJobId().toString().equals(reasons.get("jobId"))) return;
            response.setRecognizedExercise(result.getRecognizedExercise());
            response.setValidation(result.getValidation());
            response.setEvidence(result.getEvidence());
            response.setStudentFeedback(result.getStudentFeedback());
            response.setModelVersion(result.getModelVersion());
            if (reasons != null) {
                if (reasons.get("reasonCode") != null) response.setReasonCode(String.valueOf(reasons.get("reasonCode")));
                java.util.Map<String, Object> confidence = new java.util.HashMap<>();
                for (String key : java.util.List.of("recognition", "structure", "diagnosis")) {
                    if (reasons.get(key) instanceof Number) confidence.put(key, reasons.get(key));
                }
                response.setConfidenceBundle(confidence.isEmpty() ? null : confidence);
                if (reasons.get("diagnostics") instanceof Map<?, ?> diagnostics) {
                    @SuppressWarnings("unchecked") Map<String, Object> typed = (Map<String, Object>) diagnostics;
                    response.setDiagnostics(typed);
                }
            }
            if (result.getRecognizedExercise() != null && result.getRecognizedExercise().get("tokens") instanceof java.util.List<?> tokens) {
                response.setUncertainTokenIds(tokens.stream().filter(token -> token instanceof Map<?, ?> map && Boolean.TRUE.equals(map.get("ambiguity")))
                        .map(token -> String.valueOf(((Map<?, ?>) token).get("tokenId"))).toList());
            }
        });
        return response;
    }

    @Transactional
    public SubmissionResponse confirmToken(String email, UUID submissionId, TokenConfirmationRequest request) {
        Submission submission = ownedStudentForUpdate(email, submissionId);
        if (submission.getBatch() != null || !java.util.Set.of("FEEDBACK_READY", "NEEDS_CONFIRMATION", "REVIEW_REQUIRED").contains(submission.getStatus())) {
            throw new ApiException("INVALID_STATE", "Submission not in valid state for confirmation", HttpStatus.BAD_REQUEST);
        }
        AiJob latest = aiJobRepository.findFirstBySubmission_SubmissionIdOrderBySubmittedAtDesc(submissionId)
                .orElseThrow(() -> new ApiException("RESULT_NOT_AVAILABLE", "No recognized attempt to confirm", HttpStatus.CONFLICT));
        if (!latest.getJobId().equals(request.getJobId()) || !"COMPLETED".equals(latest.getStatus())) {
            throw new ApiException("STALE_ATTEMPT", "Reload the latest result before confirming", HttpStatus.CONFLICT);
        }
        AnalysisResult result = analysisResultRepository.findBySubmission_SubmissionId(submissionId)
                .orElseThrow(() -> new ApiException("RESULT_NOT_AVAILABLE", "No recognized result", HttpStatus.CONFLICT));
        Map<String, Object> recognized = result.getRecognizedExercise();
        if (recognized == null || !(recognized.get("tokens") instanceof java.util.List<?> rawTokens)) {
            throw new ApiException("RESULT_NOT_AVAILABLE", "No identified tokens to confirm", HttpStatus.CONFLICT);
        }
        java.util.List<Map<String, Object>> tokens = new java.util.ArrayList<>();
        for (Object item : rawTokens) {
            if (!(item instanceof Map<?, ?>)) throw new ApiException("RESULT_NOT_AVAILABLE", "Invalid token payload", HttpStatus.CONFLICT);
            @SuppressWarnings("unchecked") Map<String, Object> token = (Map<String, Object>) item;
            tokens.add(new java.util.HashMap<>(token));
        }
        Map<String, Object> target = tokens.stream().filter(t -> request.getTokenId().equals(t.get("tokenId"))).findFirst()
                .orElseThrow(() -> new ApiException("VALIDATION_ERROR", "Unknown token", HttpStatus.BAD_REQUEST));
        String value = request.getNewClass();
        if (!("digit".equals(target.get("tokenClass")) && value.matches("[0-9]")) &&
                !("operator".equals(target.get("tokenClass")) && java.util.List.of("+", "-").contains(value))) {
            throw new ApiException("VALIDATION_ERROR", "Invalid value for this identified token", HttpStatus.BAD_REQUEST);
        }
        Map<String, Object> correction = new java.util.HashMap<>();
        correction.put("tokenId", request.getTokenId());
        correction.put("originalValue", target.get("value"));
        correction.put("confirmedValue", value);
        correction.put("confirmedAt", java.time.Instant.now().toString());
        target.put("value", value);
        target.put("ambiguity", false);
        target.put("humanConfirmed", true);
        Map<String, Object> updated = new java.util.HashMap<>(recognized);
        if (!updated.containsKey("rawTokens")) updated.put("rawTokens", rawTokens);
        if (!updated.containsKey("rawExpression") && recognized.get("expression") != null) updated.put("rawExpression", recognized.get("expression"));
        updated.put("tokens", tokens);
        java.util.List<Object> corrections = new java.util.ArrayList<>();
        if (recognized.get("corrections") instanceof java.util.List<?> history) corrections.addAll(history);
        corrections.add(correction);
        updated.put("corrections", corrections);
        java.util.List<String> allowedOperations = java.util.List.of("VERTICAL_ADDITION", "VERTICAL_SUBTRACTION");
        if (submission.getAssignment() != null && submission.getAssignment().getOperationType() != null) {
            String operation = submission.getAssignment().getOperationType();
            allowedOperations = java.util.List.of("ADDITION".equals(operation) ? "VERTICAL_ADDITION"
                    : "SUBTRACTION".equals(operation) ? "VERTICAL_SUBTRACTION" : operation);
        }
        ArithmeticTokenValidator.Result checked = ArithmeticTokenValidator.validate(tokens,
                com.mathvisionkids.api.analysis.HttpAiAnalysisGateway.MAX_DIGITS, allowedOperations);
        if (checked.expression() != null) updated.put("expression", checked.expression());
        result.setRecognizedExercise(updated);
        result.setValidation(checked.validation());
        result.setEvidence(Map.of("items", checked.evidence()));
        result.setStudentFeedback(checked.feedback());
        result.setStatus(checked.status());
        submission.setStatus(checked.status());
        analysisResultRepository.save(result);
        submissionRepository.save(submission);
        AuditEvent audit = new AuditEvent();
        audit.setSubmission(submission);
        audit.setUser(submission.getStudent());
        audit.setEventType("TOKEN_CONFIRMED");
        audit.setMetadata(correction);
        auditEventRepository.save(audit);
        return toResponse(submission);
    }

    private static final java.util.Set<String> APPROVABLE_STATES = java.util.Set.of(
            "PROPOSED_GRADE", "REVIEW_REQUIRED", "FEEDBACK_READY"
    );

    private static final java.util.Set<String> RETRYABLE_STATES = java.util.Set.of(
            "NEEDS_RETAKE", "CROP_REQUIRED", "NEEDS_CONFIRMATION", "FEEDBACK_READY", "REVIEW_REQUIRED"
    );

    @Transactional
    public void retrySubmission(String email, UUID submissionId, MultipartFile file, String source) {
        Submission submission = ownedStudentForUpdate(email, submissionId);
        if (!RETRYABLE_STATES.contains(submission.getStatus())) {
            throw new ApiException("INVALID_STATE", "Submission cannot be retried at this state", HttpStatus.BAD_REQUEST);
        }
        
        if (file == null || file.isEmpty()) {
            throw new ApiException("VALIDATION_ERROR", "Image is missing", HttpStatus.BAD_REQUEST);
        }

        String contentType = file.getContentType();
        if (contentType == null || (!contentType.equals("image/jpeg") && !contentType.equals("image/png") && !contentType.equals("image/webp"))) {
            throw new ApiException("UNSUPPORTED_MEDIA_TYPE", "Only JPEG, PNG, and WebP are supported", HttpStatus.UNSUPPORTED_MEDIA_TYPE);
        }

        String filePath = null;
        try {
            filePath = objectStorageService.store(file, "submissions");

            SubmissionImage image = new SubmissionImage();
            image.setSubmission(submission);
            image.setFilePath(filePath);
            image.setContentType(contentType);
            image.setFileSize(file.getSize());
            image.setSource(source);
            submissionImageRepository.save(image);
        } catch (Exception e) {
            e.printStackTrace();
            if (filePath != null) {
                try {
                    objectStorageService.delete(filePath);
                } catch (IOException ignored) {}
            }
            throw new ApiException("INTERNAL_ERROR", "Failed to store retry image", HttpStatus.INTERNAL_SERVER_ERROR);
        }

        submission.setStatus("PROCESSING");
        submissionRepository.save(submission);
        for (AiJob job : aiJobRepository.findBySubmission_SubmissionId(submissionId)) {
            if (!"COMPLETED".equals(job.getStatus())) {
                job.setStatus("SUPERSEDED");
                aiJobRepository.save(job);
            }
        }
        
        AuditEvent auditEvent = new AuditEvent();
        auditEvent.setSubmission(submission);
        auditEvent.setUser(studentRepository.findByEmail(email).orElseThrow());
        auditEvent.setEventType("RETRY_REQUESTED");
        auditEventRepository.save(auditEvent);

        AuditEvent auditEvent1 = new AuditEvent();
        auditEvent1.setSubmission(submission);
        auditEvent1.setUser(studentRepository.findByEmail(email).orElseThrow());
        auditEvent1.setEventType("IMAGE_UPLOADED");
        auditEventRepository.save(auditEvent1);

        AuditEvent auditEvent2 = new AuditEvent();
        auditEvent2.setSubmission(submission);
        auditEvent2.setUser(studentRepository.findByEmail(email).orElseThrow());
        auditEvent2.setEventType("AI_PROCESSING_STARTED");
        auditEventRepository.save(auditEvent2);

        dispatchAfterCommit(submission.getSubmissionId());
    }

    private Submission ownedStudentForUpdate(String email, UUID submissionId) {
        Student student = studentRepository.findByEmail(email)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Student not found", HttpStatus.NOT_FOUND));
        Submission submission = submissionRepository.findForUpdate(submissionId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Submission not found", HttpStatus.NOT_FOUND));
        if (submission.getStudent() == null || !submission.getStudent().getId().equals(student.getId())) {
            throw new ApiException("FORBIDDEN", "Not authorized", HttpStatus.FORBIDDEN);
        }
        return submission;
    }

    private void dispatchAfterCommit(UUID submissionId) {
        Runnable dispatch = () -> aiAnalysisGateway.analyze(submissionId);
        if (org.springframework.transaction.support.TransactionSynchronizationManager.isSynchronizationActive()) {
            org.springframework.transaction.support.TransactionSynchronizationManager.registerSynchronization(
                new org.springframework.transaction.support.TransactionSynchronization() {
                    @Override public void afterCommit() { java.util.concurrent.CompletableFuture.runAsync(dispatch); }
                });
        } else {
            dispatch.run();
        }
    }
    
    @Transactional(readOnly = true)
    public Submission getTeacherSubmission(String email, UUID submissionId) {
        Teacher teacher = teacherRepository.findByEmail(email)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Teacher not found", HttpStatus.NOT_FOUND));
        
        Submission submission = submissionRepository.findById(submissionId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Submission not found", HttpStatus.NOT_FOUND));

        if (submission.getBatch() == null || !submission.getBatch().getTeacher().getId().equals(teacher.getId())) {
             throw new ApiException("FORBIDDEN", "Not authorized", HttpStatus.FORBIDDEN);
        }
        
        return submission;
    }

    @Transactional(readOnly = true)
    public Map<String, Object> getTeacherSubmissionDetail(String email, UUID submissionId) {
        Submission submission = getTeacherSubmission(email, submissionId);
        Map<String, Object> detail = new java.util.LinkedHashMap<>();
        detail.put("submissionId", submission.getSubmissionId());
        detail.put("status", submission.getStatus());
        detail.put("createdAt", submission.getCreatedAt());
        detail.put("studentId", submission.getStudentId());
        detail.put("assignmentId", submission.getAssignmentId());
        detail.put("batchId", submission.getBatchId());
        if (submission.getAssignment() != null) detail.put("maxScore", submission.getAssignment().getMaxScore());
        if (submission.getStudent() != null) detail.put("studentName", submission.getStudent().getDisplayName());
        detail.put("imageUrl", "/api/v1/teacher/submissions/" + submissionId + "/image");
        if ("PROCESSING".equals(submission.getStatus())) return detail;
        AiJob latest = aiJobRepository.findFirstBySubmission_SubmissionIdOrderBySubmittedAtDesc(submissionId).orElse(null);
        if (latest != null && "FAILED".equals(latest.getStatus())) return detail;
        analysisResultRepository.findBySubmission_SubmissionId(submissionId).ifPresent(result -> {
            Map<String, Object> reasons = result.getReviewReasons();
            if (latest != null && reasons != null && reasons.get("jobId") != null
                    && !latest.getJobId().toString().equals(reasons.get("jobId"))) return;
            detail.put("analysisStatus", result.getStatus());
            if (result.getGradeProposal() != null) {
                detail.put("gradeProposal", result.getGradeProposal());
                Object score = result.getGradeProposal().get("suggestedScore");
                if (score instanceof Number number && Double.isFinite(number.doubleValue())) detail.put("suggestedScore", score);
            }
            if (reasons != null) {
                Map<String, Object> confidence = new java.util.LinkedHashMap<>();
                for (String key : java.util.List.of("recognition", "structure", "diagnosis")) {
                    if (reasons.get(key) instanceof Number number && Double.isFinite(number.doubleValue())) {
                        confidence.put(key, number);
                    }
                }
                if (!confidence.isEmpty()) detail.put("confidenceBundle", confidence);
                if (reasons.get("reasonCode") instanceof String reasonCode) detail.put("reasonCode", reasonCode);
            }
            if (result.getRecognizedExercise() != null && result.getRecognizedExercise().get("expression") instanceof String expression) {
                detail.put("recognizedText", expression);
            }
            if (result.getValidation() != null) detail.put("validation", result.getValidation());
            if (result.getEvidence() != null) detail.put("evidence", result.getEvidence());
        });
        return detail;
    }
    
    @Transactional
    public void approveSubmission(String email, UUID submissionId) {
        Submission submission = submissionRepository.findForUpdate(submissionId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Submission not found", HttpStatus.NOT_FOUND));
        getTeacherSubmission(email, submissionId);

        if (!APPROVABLE_STATES.contains(submission.getStatus())) {
            throw new ApiException("INVALID_STATE", "Submission not in approvable state", HttpStatus.BAD_REQUEST);
        }
        
        AnalysisResult result = analysisResultRepository.findBySubmission_SubmissionId(submissionId)
                .orElseThrow(() -> new ApiException("VALIDATION_ERROR", "No grade proposal to approve", HttpStatus.BAD_REQUEST));
        Map<String, Object> proposal = result.getGradeProposal();
        if (proposal == null || !(proposal.get("suggestedScore") instanceof Number score) ||
                !(proposal.get("maxScore") instanceof Number scale) || scale.doubleValue() <= 0 ||
                !Double.isFinite(score.doubleValue()) || !Double.isFinite(scale.doubleValue()) ||
                score.doubleValue() < 0 || score.doubleValue() > scale.doubleValue()) {
            throw new ApiException("VALIDATION_ERROR", "Invalid grade proposal; use a manual override", HttpStatus.BAD_REQUEST);
        }
        int maxScore = submission.getAssignment() != null ? submission.getAssignment().getMaxScore() : 10;
        int finalScore = (int) Math.round(score.doubleValue() / scale.doubleValue() * maxScore);
        submission.setStatus("TEACHER_APPROVED");
        submissionRepository.save(submission);
        
        TeacherDecision decision = new TeacherDecision();
        decision.setSubmission(submission);
        decision.setTeacher(teacherRepository.findByEmail(email).orElseThrow());
        decision.setType("APPROVED");
        decision.setFinalScore(finalScore);
        teacherDecisionRepository.save(decision);
        
        AuditEvent auditEvent = new AuditEvent();
        auditEvent.setSubmission(submission);
        auditEvent.setUser(teacherRepository.findByEmail(email).orElseThrow());
        auditEvent.setEventType("TEACHER_APPROVED");
        auditEventRepository.save(auditEvent);
    }
    
    @Transactional
    public void overrideSubmission(String email, UUID submissionId, Map<String, Object> overrideData) {
        Submission submission = submissionRepository.findForUpdate(submissionId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Submission not found", HttpStatus.NOT_FOUND));
        getTeacherSubmission(email, submissionId);

        if (!APPROVABLE_STATES.contains(submission.getStatus())) {
            throw new ApiException("INVALID_STATE", "Submission not in overridable state", HttpStatus.BAD_REQUEST);
        }

        String reason = (String) overrideData.get("reason");
        if (reason == null || reason.isBlank()) {
            throw new ApiException("VALIDATION_ERROR", "Reason is required for override", HttpStatus.BAD_REQUEST);
        }
        
        submission.setStatus("TEACHER_OVERRIDDEN");
        submissionRepository.save(submission);
        
        TeacherDecision decision = new TeacherDecision();
        decision.setSubmission(submission);
        decision.setTeacher(teacherRepository.findByEmail(email).orElseThrow());
        decision.setType("OVERRIDDEN");
        Number scoreNum = null;
        if (overrideData.containsKey("score")) {
            Object s = overrideData.get("score");
            if (s instanceof Number) {
                scoreNum = (Number) s;
            }
        }
        if (scoreNum == null && overrideData.containsKey("finalScore")) {
            Object fs = overrideData.get("finalScore");
            if (fs instanceof Number) {
                scoreNum = (Number) fs;
            }
        }
        decision.setFinalScore(scoreNum != null ? (int) Math.round(scoreNum.doubleValue()) : 0);
        decision.setReason(reason);
        teacherDecisionRepository.save(decision);
        
        AuditEvent auditEvent = new AuditEvent();
        auditEvent.setSubmission(submission);
        auditEvent.setUser(teacherRepository.findByEmail(email).orElseThrow());
        auditEvent.setEventType("TEACHER_OVERRIDDEN");
        auditEventRepository.save(auditEvent);
    }
}

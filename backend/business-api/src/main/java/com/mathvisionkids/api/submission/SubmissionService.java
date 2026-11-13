package com.mathvisionkids.api.submission;

import com.mathvisionkids.api.analysis.AiAnalysisGateway;
import com.mathvisionkids.api.audit.AuditEvent;
import com.mathvisionkids.api.audit.AuditEventRepository;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.storage.ImageContentType;
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
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;

@Service
public class SubmissionService {
    private static final java.util.Set<String> TEACHER_DISPATCH_EVENTS =
            java.util.Set.of("TEACHER_PROCESSING_RETRY_REQUESTED", "TEACHER_RETAKE_UPLOADED");
    private static final org.slf4j.Logger logger = org.slf4j.LoggerFactory.getLogger(SubmissionService.class);
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
    private final TransactionTemplate transactions;

    public SubmissionService(SubmissionRepository submissionRepository,
                             SubmissionImageRepository submissionImageRepository,
                             ObjectStorageService objectStorageService,
                             AiAnalysisGateway aiAnalysisGateway,
                             AuditEventRepository auditEventRepository,
                             StudentRepository studentRepository,
                             TeacherRepository teacherRepository,
                             TeacherDecisionRepository teacherDecisionRepository,
                             AnalysisResultRepository analysisResultRepository,
                             AiJobRepository aiJobRepository,
                             PlatformTransactionManager transactionManager) {
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
        this.transactions = new TransactionTemplate(transactionManager);
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
        if (submission.getBatch() != null) {
            throw new ApiException("FORBIDDEN", "Not authorized", HttpStatus.FORBIDDEN);
        }
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
        supersedeIncompleteJobs(submissionId);

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

    private void supersedeIncompleteJobs(UUID submissionId) {
        for (AiJob job : aiJobRepository.findBySubmission_SubmissionId(submissionId)) {
            if (!"COMPLETED".equals(job.getStatus()) && !"SUPERSEDED".equals(job.getStatus())) {
                job.setStatus("SUPERSEDED");
                aiJobRepository.save(job);
            }
        }
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
        Submission submission = submissionRepository.findById(submissionId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Submission not found", HttpStatus.NOT_FOUND));
        requireTeacherSubmissionAccess(email, submission);
        return submission;
    }

    private Teacher requireTeacherSubmissionAccess(String email, Submission submission) {
        Teacher teacher = teacherRepository.findByEmail(email)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Teacher not found", HttpStatus.NOT_FOUND));
        if (submission.getBatch() == null || !submission.getBatch().isOwnedByAssignedTeacher(teacher.getId())) {
            throw new ApiException("FORBIDDEN", "Not authorized", HttpStatus.FORBIDDEN);
        }
        return teacher;
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
        detail.put("maxScore", getGradingScale(submission));
        if (submission.getStudent() != null) detail.put("studentName", submission.getStudent().getDisplayName());
        if ("TEACHER_APPROVED".equals(submission.getStatus()) || "TEACHER_OVERRIDDEN".equals(submission.getStatus())) {
            teacherDecisionRepository.findBySubmission_SubmissionId(submissionId).ifPresent(decision -> {
                detail.put("teacherScore", decision.getFinalScore());
                if (decision.getReason() != null) detail.put("teacherReason", decision.getReason());
            });
        }
        detail.put("imageUrl", "/api/v1/teacher/submissions/" + submissionId + "/image");
        var image = submissionImageRepository.findFirstBySubmission_SubmissionIdOrderByCreatedAtDesc(submissionId);
        image.ifPresent(value -> detail.put("imageVersion", value.getImageId().toString()));
        detail.put("canRetryProcessing", false);
        if ("PROCESSING".equals(submission.getStatus())) return detail;
        AiJob latest = aiJobRepository.findFirstBySubmission_SubmissionIdOrderBySubmittedAtDescJobIdDesc(submissionId).orElse(null);
        var analysis = analysisResultRepository.findBySubmission_SubmissionId(submissionId);
        detail.put("canRetryProcessing", image.isPresent()
                && isTeacherProcessingRetryable(submission, latest, analysis.orElse(null)));
        analysis.ifPresent(result -> {
            Map<String, Object> reasons = result.getReviewReasons();
            if (latest != null && !AnalysisResult.isVisibleForTeacher(latest.getJobId(), latest.getStatus(), reasons)) return;
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

    private boolean isTeacherProcessingRetryable(Submission submission, AiJob latest, AnalysisResult analysis) {
        if (latest != null && !java.util.Set.of("FAILED", "COMPLETED", "SUPERSEDED").contains(latest.getStatus())) {
            return false;
        }
        if ("FAILED".equals(submission.getStatus())) return true;
        if (!java.util.Set.of("REVIEW_REQUIRED", "NEEDS_RETAKE").contains(submission.getStatus())) return false;
        if (latest != null && "FAILED".equals(latest.getStatus())) return true;
        if (analysis == null || !"MODEL_NOT_AVAILABLE".equals(analysis.getStatus())) return false;
        Map<String, Object> reasons = analysis.getReviewReasons();
        return latest == null || ("COMPLETED".equals(latest.getStatus())
                && (reasons == null || reasons.get("jobId") == null
                || latest.getJobId().toString().equals(reasons.get("jobId"))));
    }

    @Transactional
    public void retryTeacherProcessing(String email, UUID submissionId) {
        Submission submission = submissionRepository.findForUpdate(submissionId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Submission not found", HttpStatus.NOT_FOUND));
        Teacher teacher = requireTeacherSubmissionAccess(email, submission);
        var image = submissionImageRepository.findFirstBySubmission_SubmissionIdOrderByCreatedAtDesc(submissionId);
        AiJob latest = aiJobRepository.findFirstBySubmission_SubmissionIdOrderBySubmittedAtDesc(submissionId).orElse(null);
        AnalysisResult analysis = analysisResultRepository.findBySubmission_SubmissionId(submissionId).orElse(null);
        if (image.isEmpty() || !isTeacherProcessingRetryable(submission, latest, analysis)) {
            throw new ApiException("INVALID_STATE", "Bài làm hiện không thể xử lý lại.", HttpStatus.CONFLICT);
        }
        queueTeacherProcessing(submission, teacher, image.get(), "TEACHER_PROCESSING_RETRY_REQUESTED");
    }

    @Transactional
    public void retakeTeacherSubmission(String email, UUID submissionId, MultipartFile file) {
        Submission submission = submissionRepository.findForUpdate(submissionId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Submission not found", HttpStatus.NOT_FOUND));
        Teacher teacher = requireTeacherSubmissionAccess(email, submission);
        if (!"NEEDS_RETAKE".equals(submission.getStatus())) {
            throw new ApiException("INVALID_STATE", "Bài làm hiện không cần thay ảnh.", HttpStatus.CONFLICT);
        }
        validateTeacherRetakeImage(file);

        String path;
        try {
            path = objectStorageService.store(file, "batches/" + submission.getBatchId());
        } catch (IOException error) {
            throw new ApiException("STORAGE_UNAVAILABLE", "Chưa lưu được ảnh. Hãy thử lại.", HttpStatus.SERVICE_UNAVAILABLE);
        }

        SubmissionImage image = new SubmissionImage();
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCompletion(int status) {
                if (status == STATUS_ROLLED_BACK) {
                    try {
                        objectStorageService.delete(path);
                    } catch (IOException error) {
                        logger.error("Could not remove rolled back retake image for submission {}", submissionId);
                    }
                }
            }

        });
        image.setSubmission(submission);
        image.setFilePath(path);
        image.setContentType(MediaType.IMAGE_JPEG_VALUE);
        image.setFileSize(file.getSize());
        image.setSource(SubmissionImage.TEACHER_RETAKE_SOURCE);
        submissionImageRepository.save(image);

        queueTeacherProcessing(submission, teacher, image, "TEACHER_RETAKE_UPLOADED");
    }

    private void queueTeacherProcessing(Submission submission, Teacher teacher, SubmissionImage image, String eventType) {
        UUID submissionId = submission.getSubmissionId();
        UUID imageId = image.getImageId();
        submission.setStatus("PROCESSING");
        supersedeIncompleteJobs(submissionId);
        analysisResultRepository.findBySubmission_SubmissionId(submissionId).ifPresent(analysisResultRepository::delete);

        AuditEvent audit = new AuditEvent();
        audit.setSubmission(submission);
        audit.setUser(teacher);
        audit.setEventType(eventType);
        audit.setMetadata(Map.of("imageId", imageId.toString()));
        auditEventRepository.save(audit);
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                CompletableFuture.runAsync(() -> dispatchTeacherProcessing(submissionId, imageId));
            }
        });
    }

    private void validateTeacherRetakeImage(MultipartFile file) {
        if (file.isEmpty() || file.getSize() > SubmissionImage.TEACHER_UPLOAD_MAX_BYTES) {
            throw new ApiException("VALIDATION_ERROR", "Ảnh phải có nội dung và không vượt quá 8 MB.", HttpStatus.BAD_REQUEST);
        }
        try (var stream = file.getInputStream()) {
            if (MediaType.IMAGE_JPEG_VALUE.equals(file.getContentType())
                    && MediaType.IMAGE_JPEG.equals(ImageContentType.detect(stream.readNBytes(12)))) {
                return;
            }
        } catch (IOException error) {
            throw new ApiException("IMAGE_INVALID", "Chưa đọc được ảnh. Hãy chọn lại ảnh.", HttpStatus.BAD_REQUEST);
        } catch (ApiException error) {
            // Use the retake-specific validation message for unrecognized file signatures.
        }
        throw new ApiException("IMAGE_UNSUPPORTED", "Hãy chọn ảnh JPG đã che thông tin học sinh.", HttpStatus.BAD_REQUEST);
    }

    private void dispatchTeacherProcessing(UUID submissionId, UUID imageId) {
        try {
            aiAnalysisGateway.analyze(submissionId);
        } catch (RuntimeException error) {
            logger.error("Could not dispatch teacher processing for submission {}", submissionId);
            transactions.executeWithoutResult(status -> {
                Submission submission = submissionRepository.findForUpdate(submissionId).orElseThrow();
                boolean isCurrentImage = submissionImageRepository.findFirstBySubmission_SubmissionIdOrderByCreatedAtDesc(submissionId)
                        .map(image -> imageId.equals(image.getImageId())).orElse(false);
                if ("PROCESSING".equals(submission.getStatus()) && isCurrentImage) {
                    supersedeIncompleteJobs(submissionId);
                    submission.setStatus("FAILED");
                }
            });
        }
    }

    @org.springframework.scheduling.annotation.Scheduled(fixedDelayString = "${mathvision.teacher-dispatch-recovery-ms:30000}")
    public void recoverInterruptedTeacherDispatches() {
        recoverInterruptedTeacherDispatches(java.time.Instant.now().minusSeconds(120));
    }

    void recoverInterruptedTeacherDispatches(java.time.Instant cutoff) {
        for (UUID id : submissionRepository.findInterruptedTeacherDispatches(
                TEACHER_DISPATCH_EVENTS, cutoff, org.springframework.data.domain.PageRequest.of(0, 50))) {
            transactions.executeWithoutResult(transaction -> {
                Submission submission = submissionRepository.findForUpdate(id).orElse(null);
                if (submission == null || !"PROCESSING".equals(submission.getStatus())) return;
                var attempt = auditEventRepository.findBySubmission_SubmissionIdOrderByCreatedAtDesc(id).stream()
                        .filter(event -> TEACHER_DISPATCH_EVENTS.contains(event.getEventType())).findFirst();
                if (attempt.isEmpty() || !attempt.get().getCreatedAt().isBefore(cutoff)) return;
                var latest = aiJobRepository.findFirstBySubmission_SubmissionIdOrderBySubmittedAtDescJobIdDesc(id);
                if (latest.isPresent() && !latest.get().getSubmittedAt().isBefore(attempt.get().getCreatedAt())) {
                    var job = latest.get();
                    if (!java.util.Set.of("SUPERSEDED", "FAILED", "PENDING").contains(job.getStatus())
                            || ("PENDING".equals(job.getStatus()) && !job.getSubmittedAt().isBefore(cutoff))) return;
                }
                // Delivery of a PENDING job is uncertain. Retire it before offering an explicit retry.
                supersedeIncompleteJobs(id);
                submission.setStatus("FAILED");
                AuditEvent recovered = new AuditEvent();
                recovered.setSubmission(submission);
                recovered.setEventType("TEACHER_DISPATCH_INTERRUPTED");
                auditEventRepository.save(recovered);
            });
        }
    }
    
    @Transactional
    public void approveSubmission(String email, UUID submissionId) {
        Submission submission = submissionRepository.findForUpdate(submissionId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Submission not found", HttpStatus.NOT_FOUND));
        Teacher teacher = requireTeacherSubmissionAccess(email, submission);

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
        int maxScore = getGradingScale(submission);
        int finalScore = (int) Math.round(score.doubleValue() / scale.doubleValue() * maxScore);
        submission.setStatus("TEACHER_APPROVED");
        submissionRepository.save(submission);
        
        TeacherDecision decision = new TeacherDecision();
        decision.setSubmission(submission);
        decision.setTeacher(teacher);
        decision.setType("APPROVED");
        decision.setFinalScore(finalScore);
        teacherDecisionRepository.save(decision);
        
        AuditEvent auditEvent = new AuditEvent();
        auditEvent.setSubmission(submission);
        auditEvent.setUser(teacher);
        auditEvent.setEventType("TEACHER_APPROVED");
        Map<String, Object> meta = new HashMap<>();
        meta.put("finalScore", finalScore);
        meta.put("decisionType", "APPROVED");
        meta.put("submissionId", submission.getSubmissionId().toString());
        auditEvent.setMetadata(meta);
        auditEventRepository.save(auditEvent);
    }
    
    @Transactional
    public void overrideSubmission(String email, UUID submissionId, Map<String, Object> overrideData) {
        Submission submission = submissionRepository.findForUpdate(submissionId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Submission not found", HttpStatus.NOT_FOUND));
        Teacher teacher = requireTeacherSubmissionAccess(email, submission);

        boolean needsConfirmation = "NEEDS_CONFIRMATION".equals(submission.getStatus());
        if (!APPROVABLE_STATES.contains(submission.getStatus()) && !needsConfirmation) {
            throw new ApiException("INVALID_STATE", "Submission not in overridable state", HttpStatus.BAD_REQUEST);
        }

        if (overrideData == null) {
            throw new ApiException("VALIDATION_ERROR", "Override data is required", HttpStatus.BAD_REQUEST);
        }

        Object imageLegibility = overrideData.get("imageLegible");
        if (needsConfirmation && !Boolean.TRUE.equals(imageLegibility)) {
            throw new ApiException("VALIDATION_ERROR", "Hãy xác nhận ảnh đủ rõ để chấm điểm.", HttpStatus.BAD_REQUEST);
        }

        Object rawReason = overrideData.get("reason");
        if (rawReason == null) {
            throw new ApiException("VALIDATION_ERROR", "Reason is required for override", HttpStatus.BAD_REQUEST);
        }
        if (!(rawReason instanceof String reason) || reason.isBlank()) {
            throw new ApiException("VALIDATION_ERROR", "Reason must be a non-blank string", HttpStatus.BAD_REQUEST);
        }

        int maxScore = getGradingScale(submission);

        Object rawScore = overrideData.getOrDefault("score", overrideData.get("finalScore"));

        if (rawScore == null) {
            throw new ApiException("VALIDATION_ERROR", "Score is required for override", HttpStatus.BAD_REQUEST);
        }

        if (!(rawScore instanceof Number scoreNum)) {
            throw new ApiException("VALIDATION_ERROR", "Score must be a finite numeric value", HttpStatus.BAD_REQUEST);
        }

        double scoreVal = scoreNum.doubleValue();
        if (!Double.isFinite(scoreVal) || scoreVal < 0.0 || scoreVal > (double) maxScore) {
            throw new ApiException("VALIDATION_ERROR",
                    "Score must be between 0 and " + maxScore + " (received: " + scoreVal + ")",
                    HttpStatus.BAD_REQUEST);
        }

        int finalScore = (int) Math.round(scoreVal);

        submission.setStatus("TEACHER_OVERRIDDEN");
        submissionRepository.save(submission);

        TeacherDecision decision = new TeacherDecision();
        decision.setSubmission(submission);
        decision.setTeacher(teacher);
        decision.setType("OVERRIDDEN");
        decision.setFinalScore(finalScore);
        decision.setReason(reason);
        teacherDecisionRepository.save(decision);

        AuditEvent auditEvent = new AuditEvent();
        auditEvent.setSubmission(submission);
        auditEvent.setUser(teacher);
        auditEvent.setEventType("TEACHER_OVERRIDDEN");
        Map<String, Object> meta = new HashMap<>();
        meta.put("finalScore", decision.getFinalScore());
        meta.put("decisionType", "OVERRIDDEN");
        meta.put("reason", reason);
        if (imageLegibility instanceof Boolean imageLegible) {
            meta.put("imageLegible", imageLegible);
        }
        meta.put("submissionId", submission.getSubmissionId().toString());
        auditEvent.setMetadata(meta);
        auditEventRepository.save(auditEvent);
    }

    private static int getGradingScale(Submission submission) {
        Integer scale = submission.getAssignment() == null ? null : submission.getAssignment().getMaxScore();
        return scale != null && scale > 0 ? scale : 10;
    }
}

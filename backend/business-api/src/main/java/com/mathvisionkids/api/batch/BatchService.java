package com.mathvisionkids.api.batch;

import com.mathvisionkids.api.analysis.AiAnalysisGateway;
import com.mathvisionkids.api.assignment.Assignment;
import com.mathvisionkids.api.assignment.AssignmentRepository;
import com.mathvisionkids.api.audit.AuditEvent;
import com.mathvisionkids.api.audit.AuditEventRepository;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.submission.Submission;
import com.mathvisionkids.api.submission.SubmissionImage;
import com.mathvisionkids.api.submission.SubmissionImageRepository;
import com.mathvisionkids.api.submission.SubmissionRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Service
public class BatchService {
    private static final org.slf4j.Logger logger = org.slf4j.LoggerFactory.getLogger(BatchService.class);
    private final BatchRepository batchRepository;
    private final AssignmentRepository assignmentRepository;
    private final TeacherRepository teacherRepository;
    private final SubmissionRepository submissionRepository;
    private final SubmissionImageRepository submissionImageRepository;
    private final AuditEventRepository auditEventRepository;
    private final ObjectStorageService objectStorageService;
    private final AiAnalysisGateway aiAnalysisGateway;
    private final com.mathvisionkids.api.user.StudentRepository studentRepository;
    private final org.springframework.transaction.support.TransactionTemplate transactions;

    public BatchService(BatchRepository batchRepository, AssignmentRepository assignmentRepository, TeacherRepository teacherRepository, SubmissionRepository submissionRepository, SubmissionImageRepository submissionImageRepository, AuditEventRepository auditEventRepository, ObjectStorageService objectStorageService, AiAnalysisGateway aiAnalysisGateway, com.mathvisionkids.api.user.StudentRepository studentRepository, org.springframework.transaction.PlatformTransactionManager transactionManager) {
        this.batchRepository = batchRepository;
        this.assignmentRepository = assignmentRepository;
        this.teacherRepository = teacherRepository;
        this.submissionRepository = submissionRepository;
        this.submissionImageRepository = submissionImageRepository;
        this.auditEventRepository = auditEventRepository;
        this.objectStorageService = objectStorageService;
        this.aiAnalysisGateway = aiAnalysisGateway;
        this.studentRepository = studentRepository;
        this.transactions = new org.springframework.transaction.support.TransactionTemplate(transactionManager);
    }

    @Transactional
    public Batch createBatch(String teacherEmail, UUID assignmentId) {
        Teacher teacher = teacherRepository.findByEmail(teacherEmail)
                .map(u -> teacherRepository.findById(u.getId()).orElse(null))
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Teacher not found", HttpStatus.NOT_FOUND));

        Assignment assignment = assignmentRepository.findById(assignmentId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Assignment not found", HttpStatus.NOT_FOUND));

        if (!assignment.getTeacher().getId().equals(teacher.getId())) {
            throw new ApiException("FORBIDDEN", "Not authorized for this assignment", HttpStatus.FORBIDDEN);
        }

        Batch batch = new Batch();
        batch.setAssignment(assignment);
        batch.setTeacher(teacher);
        batch.setStatus("CREATED");
        return batchRepository.save(batch);
    }

    @Transactional
    public void uploadImages(String teacherEmail, UUID batchId, List<MultipartFile> images, List<BatchImageMapping> mappings) {
        Teacher teacher = teacherRepository.findByEmail(teacherEmail)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Teacher not found", HttpStatus.NOT_FOUND));
        Batch batch = batchRepository.findForUpdate(batchId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Batch not found", HttpStatus.NOT_FOUND));
        if (!batch.getTeacher().getId().equals(teacher.getId())) {
            throw new ApiException("FORBIDDEN", "Not authorized for this batch", HttpStatus.FORBIDDEN);
        }
        if (!"CREATED".equals(batch.getStatus()) || !submissionRepository.findByBatch_BatchId(batchId).isEmpty()) {
            throw new ApiException("BATCH_ALREADY_UPLOADED", "Đợt chấm đã nhận ảnh. Hãy mở đợt chấm để xem kết quả.", HttpStatus.CONFLICT);
        }
        if (images == null || images.isEmpty() || images.size() > 30) {
            throw new ApiException("VALIDATION_ERROR", "Image count must be between 1 and 30", HttpStatus.BAD_REQUEST);
        }
        if (mappings == null || mappings.size() != images.size()) {
            throw new ApiException("VALIDATION_ERROR", "Mappings count must match images count", HttpStatus.BAD_REQUEST);
        }

        // Check every mapping and image before creating storage objects or submissions.
        List<com.mathvisionkids.api.user.Student> students = new ArrayList<>();
        long totalBytes = 0;
        for (int i = 0; i < images.size(); i++) {
            BatchImageMapping mapping = mappings.get(i);
            MultipartFile file = images.get(i);
            if (mapping == null || mapping.getStudentId() == null || mapping.getFileIndex() == null || mapping.getFileIndex() != i) {
                throw new ApiException("VALIDATION_ERROR", "Invalid student mapping at index " + i, HttpStatus.BAD_REQUEST);
            }
            var student = studentRepository.findById(mapping.getStudentId())
                    .orElseThrow(() -> new ApiException("VALIDATION_ERROR", "Unknown student", HttpStatus.BAD_REQUEST));
            if (batch.getAssignment().getClassroom() == null || batch.getAssignment().getClassroom().getStudents().stream()
                    .noneMatch(s -> s.getId().equals(student.getId()))) {
                throw new ApiException("VALIDATION_ERROR", "Student outside classroom", HttpStatus.BAD_REQUEST);
            }
            if (file == null || file.isEmpty() || file.getSize() > 8L * 1024 * 1024) {
                throw new ApiException("VALIDATION_ERROR", "Mỗi ảnh phải có nội dung và nhỏ hơn 8 MB.", HttpStatus.BAD_REQUEST);
            }
            totalBytes += file.getSize();
            if (totalBytes > 95L * 1024 * 1024) {
                throw new ApiException("IMAGE_TOO_LARGE", "Hãy chia đợt chấm nhỏ hơn 95 MB.", HttpStatus.PAYLOAD_TOO_LARGE);
            }
            try (var stream = file.getInputStream()) {
                String detected = com.mathvisionkids.api.storage.ImageContentType.detect(stream.readNBytes(12)).toString();
                if (!detected.equals(file.getContentType())) {
                    throw new ApiException("IMAGE_UNSUPPORTED", "Định dạng ảnh không khớp nội dung.", HttpStatus.BAD_REQUEST);
                }
            } catch (IOException error) {
                throw new ApiException("IMAGE_INVALID", "Chưa đọc được ảnh. Hãy chọn lại ảnh.", HttpStatus.BAD_REQUEST);
            }
            students.add(student);
        }

        List<String> storedPaths = new ArrayList<>();
        List<UUID> submissionIds = new ArrayList<>();
        org.springframework.transaction.support.TransactionSynchronizationManager.registerSynchronization(
                new org.springframework.transaction.support.TransactionSynchronization() {
                    @Override
                    public void afterCompletion(int status) {
                        if (status != STATUS_COMMITTED) {
                            for (String path : storedPaths) {
                                try {
                                    objectStorageService.delete(path);
                                } catch (IOException error) {
                                    logger.error("Batch upload rollback could not remove an object for batch {}", batchId);
                                }
                            }
                        }
                    }
                    @Override
                    public void afterCommit() {
                        java.util.concurrent.CompletableFuture.runAsync(() -> {
                            for (UUID id : submissionIds) {
                                try {
                                    aiAnalysisGateway.analyze(id);
                                } catch (Exception error) {
                                    logger.error("Could not dispatch submission {} for analysis", id);
                                    transactions.executeWithoutResult(status -> submissionRepository.markDispatchFailure(id));
                                }
                            }
                        });
                    }
                });
        for (int i = 0; i < images.size(); i++) {
            MultipartFile file = images.get(i);
            String path;
            try {
                path = objectStorageService.store(file, "batches/" + batchId);
            } catch (IOException error) {
                throw new ApiException("STORAGE_UNAVAILABLE", "Chưa lưu được ảnh. Em hãy thử lại đợt chấm.", HttpStatus.SERVICE_UNAVAILABLE);
            }
            storedPaths.add(path);
            Submission submission = new Submission();
            submission.setBatch(batch);
            submission.setAssignment(batch.getAssignment());
            submission.setStudent(students.get(i));
            submission.setStatus("PROCESSING");
            submissionRepository.save(submission);
            SubmissionImage image = new SubmissionImage();
            image.setSubmission(submission);
            image.setFilePath(path);
            image.setContentType(file.getContentType());
            image.setFileSize(file.getSize());
            image.setSource("CAMERA");
            submissionImageRepository.save(image);
            AuditEvent audit = new AuditEvent();
            audit.setSubmission(submission);
            audit.setUser(teacher);
            audit.setEventType("AI_PROCESSING_STARTED");
            auditEventRepository.save(audit);
            submissionIds.add(submission.getSubmissionId());
        }
        batch.setTotalCount(images.size());
        batch.setStatus("PROCESSING");
        batch.setStartedAt(java.time.Instant.now());
        batchRepository.save(batch);
    }

    @Transactional(readOnly = true)
    public List<BatchResponse> getBatches(String teacherEmail) {
        Teacher teacher = teacherRepository.findByEmail(teacherEmail).orElseThrow();
        return batchRepository.findByTeacher_IdOrderByCreatedAtDesc(teacher.getId()).stream()
                .map(batch -> BatchResponse.from(batch, submissionRepository.findByBatch_BatchId(batch.getBatchId())))
                .toList();
    }
    
    @Transactional(readOnly = true)
    public BatchResponse getBatch(String teacherEmail, UUID batchId) {
        Teacher teacher = teacherRepository.findByEmail(teacherEmail).orElseThrow();
        Batch batch = batchRepository.findById(batchId).orElseThrow();
        if (!batch.getTeacher().getId().equals(teacher.getId())) throw new ApiException("FORBIDDEN", "Forbidden", HttpStatus.FORBIDDEN);
        return BatchResponse.from(batch, submissionRepository.findByBatch_BatchId(batchId));
    }

    @Transactional(readOnly = true)
    public List<UUID> getBatchReviewQueue(String teacherEmail, UUID batchId) {
        Teacher teacher = teacherRepository.findByEmail(teacherEmail).orElseThrow();
        Batch batch = batchRepository.findById(batchId).orElseThrow();
        if (!batch.getTeacher().getId().equals(teacher.getId())) throw new ApiException("FORBIDDEN", "Forbidden", HttpStatus.FORBIDDEN);
        
        return submissionRepository.findByBatch_BatchId(batchId).stream()
                .filter(s -> java.util.Set.of("REVIEW_REQUIRED", "PROPOSED_GRADE", "NEEDS_CONFIRMATION", "NEEDS_RETAKE").contains(s.getStatus()))
                .map(Submission::getSubmissionId)
                .toList();
    }
}

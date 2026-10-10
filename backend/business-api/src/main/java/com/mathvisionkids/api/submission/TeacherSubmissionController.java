package com.mathvisionkids.api.submission;

import org.springframework.http.ResponseEntity;
import org.springframework.http.CacheControl;
import org.springframework.http.MediaType;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.storage.ObjectStorageService;

import java.io.IOException;
import java.security.Principal;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/teacher/submissions")
public class TeacherSubmissionController {

    private final SubmissionService submissionService;
    private final SubmissionImageRepository images;
    private final ObjectStorageService storage;

    public TeacherSubmissionController(SubmissionService submissionService, SubmissionImageRepository images, ObjectStorageService storage) {
        this.submissionService = submissionService;
        this.images = images;
        this.storage = storage;
    }

    @GetMapping("/{submissionId}")
    public ResponseEntity<Map<String, Object>> getSubmission(@PathVariable UUID submissionId, Principal principal) {
        return ResponseEntity.ok(submissionService.getTeacherSubmissionDetail(principal.getName(), submissionId));
    }

    @GetMapping("/{submissionId}/image")
    public ResponseEntity<byte[]> getSubmissionImage(@PathVariable UUID submissionId, Principal principal) throws IOException {
        submissionService.getTeacherSubmission(principal.getName(), submissionId);
        SubmissionImage image = images.findFirstBySubmission_SubmissionIdOrderByCreatedAtDesc(submissionId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Submission image not found", HttpStatus.NOT_FOUND));
        return ResponseEntity.ok().cacheControl(CacheControl.noStore())
                .contentType(MediaType.parseMediaType(image.getContentType()))
                .body(storage.loadBytes(image.getFilePath()));
    }

    @PostMapping("/{submissionId}/approve")
    public ResponseEntity<Void> approveSubmission(@PathVariable UUID submissionId, Principal principal) {
        submissionService.approveSubmission(principal.getName(), submissionId);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/{submissionId}/override")
    public ResponseEntity<Void> overrideSubmission(@PathVariable UUID submissionId, @RequestBody Map<String, Object> overrideData, Principal principal) {
        submissionService.overrideSubmission(principal.getName(), submissionId, overrideData);
        return ResponseEntity.ok().build();
    }
}

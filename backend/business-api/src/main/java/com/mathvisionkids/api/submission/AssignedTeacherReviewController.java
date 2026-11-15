package com.mathvisionkids.api.submission;

import java.security.Principal;
import java.util.UUID;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/teacher/assigned-submissions")
public class AssignedTeacherReviewController {
    private final AssignedTeacherReview review;
    private final com.mathvisionkids.api.storage.ObjectStorageService storage;

    public AssignedTeacherReviewController(AssignedTeacherReview review,
            com.mathvisionkids.api.storage.ObjectStorageService storage) {
        this.review = review;
        this.storage = storage;
    }

    @GetMapping("/{id}")
    public ResponseEntity<AssignedTeacherReview.Detail> detail(Principal principal, @PathVariable UUID id) {
        return ResponseEntity.ok().cacheControl(org.springframework.http.CacheControl.noStore())
                .body(review.detail(principal.getName(), id));
    }

    @GetMapping("/queue/{assignmentId}")
    public ResponseEntity<java.util.List<AssignedTeacherReview.RecipientStatus>> queue(
            Principal principal, @PathVariable UUID assignmentId) {
        return ResponseEntity.ok().cacheControl(org.springframework.http.CacheControl.noStore())
                .body(review.queue(principal.getName(), assignmentId));
    }

    @GetMapping("/{id}/image")
    public ResponseEntity<byte[]> image(Principal principal, @PathVariable UUID id, @RequestParam int imageVersion) {
        var reference = review.image(principal.getName(), id, imageVersion);
        byte[] bytes;
        try {
            bytes = storage.loadBytes(reference.key());
        } catch (java.io.IOException failure) {
            throw new com.mathvisionkids.api.common.ApiException("IMAGE_UNAVAILABLE", "Chưa tải được ảnh bài làm.",
                    org.springframework.http.HttpStatus.SERVICE_UNAVAILABLE);
        }
        review.image(principal.getName(), id, imageVersion);
        return ResponseEntity.ok().cacheControl(org.springframework.http.CacheControl.noStore())
                .header("X-Content-Type-Options", "nosniff")
                .contentType(org.springframework.http.MediaType.parseMediaType(reference.contentType())).body(bytes);
    }

    @PostMapping("/{id}/release-grade")
    public ResponseEntity<Void> releaseGrade(Principal principal, @PathVariable UUID id,
            @RequestBody AssignedTeacherReview.Grade request) {
        review.releaseGrade(principal.getName(), id, request);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/{id}/return-image")
    public ResponseEntity<Void> returnImage(Principal principal, @PathVariable UUID id,
            @RequestBody AssignedTeacherReview.ReturnImage request) {
        review.returnImage(principal.getName(), id, request);
        return ResponseEntity.noContent().build();
    }
}

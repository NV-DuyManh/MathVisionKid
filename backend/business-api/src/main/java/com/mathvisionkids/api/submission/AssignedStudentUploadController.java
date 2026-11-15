package com.mathvisionkids.api.submission;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.storage.ObjectStorageService;
import java.io.IOException;
import java.security.Principal;
import java.util.UUID;
import org.springframework.http.CacheControl;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/student/assignments")
public class AssignedStudentUploadController {
    public record Receipt(UUID submissionId, int imageVersion) {}

    private final AssignedUploadReservation reservations;
    private final ObjectStorageService storage;
    private final AssignedImagePrivacy privacy;

    public AssignedStudentUploadController(AssignedUploadReservation reservations, ObjectStorageService storage,
            AssignedImagePrivacy privacy) {
        this.reservations = reservations;
        this.storage = storage;
        this.privacy = privacy;
    }

    @GetMapping("/{assignmentId}/submission")
    public ResponseEntity<AssignedUploadReservation.Status> status(Principal principal, @PathVariable UUID assignmentId) {
        return ResponseEntity.ok().cacheControl(CacheControl.noStore())
                .body(reservations.status(principal.getName(), assignmentId));
    }

    @GetMapping("/{assignmentId}/submission/image")
    public ResponseEntity<byte[]> currentImage(Principal principal, @PathVariable UUID assignmentId) {
        String email = principal.getName();
        var image = reservations.currentImage(email, assignmentId);
        byte[] bytes;
        try {
            bytes = storage.loadBytes(image.key());
        } catch (IOException failure) {
            throw new ApiException("IMAGE_UNAVAILABLE", "Chưa tải được ảnh bài làm.", HttpStatus.SERVICE_UNAVAILABLE);
        }
        if (!image.equals(reservations.currentImage(email, assignmentId))) {
            throw new ApiException("UPLOAD_CONFLICT", "Ảnh đã thay đổi. Em hãy tải lại.", HttpStatus.CONFLICT);
        }
        return ResponseEntity.ok().cacheControl(CacheControl.noStore())
                .header("X-Content-Type-Options", "nosniff")
                .contentType(MediaType.parseMediaType(image.contentType())).body(bytes);
    }

    @PostMapping(value = "/{assignmentId}/submission", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Receipt> upload(Principal principal, @PathVariable UUID assignmentId,
            @RequestHeader("Idempotency-Key") UUID requestId, @RequestParam int expectedImageVersion,
            @RequestParam boolean privacyConfirmed, @RequestParam MultipartFile image) {
        var validated = AssignedWebImage.read(image, privacyConfirmed);
        var replay = reservations.confirmedReplay(principal.getName(), assignmentId, requestId,
                expectedImageVersion, validated.inputDigest());
        if (replay.isPresent()) return receipt(replay.get(), replay.get().expectedVersion() + 1);
        reservations.status(principal.getName(), assignmentId);
        privacy.requireClear(validated);
        var attempt = reservations.reserve(principal.getName(), assignmentId, requestId,
                expectedImageVersion, validated.inputDigest(), validated.storedDigest());
        if ("CONFIRMED".equals(attempt.state())) return receipt(attempt, attempt.expectedVersion() + 1);
        if (!"OPEN".equals(attempt.state())) {
            throw new ApiException("UPLOAD_EXPIRED", "Lượt gửi đã hết hạn. Em hãy gửi lại ảnh.", HttpStatus.CONFLICT);
        }
        try {
            reservations.recordPreparedImage(attempt, validated);
        } catch (ApiException failure) {
            if (!"UPLOAD_CONFLICT".equals(failure.getCode())) throw failure;
            var confirmed = reservations.confirmedReplay(principal.getName(), assignmentId, requestId,
                    expectedImageVersion, validated.inputDigest()).orElseThrow(() -> failure);
            return receipt(confirmed, confirmed.expectedVersion() + 1);
        }
        try {
            storage.storeAssignedImage(attempt.objectKey(), validated.bytes(), validated.contentType());
            byte[] stored = storage.loadBytes(attempt.objectKey());
            if (!validated.storedDigest().equals(AssignedWebImage.sha256(stored))) throw new IOException("Digest mismatch");
        } catch (IOException e) {
            throw new ApiException("UPLOAD_UNAVAILABLE", "Chưa lưu được ảnh. Em hãy thử lại.", HttpStatus.SERVICE_UNAVAILABLE);
        }
        return receipt(attempt, reservations.confirm(principal.getName(), assignmentId, requestId, attempt, validated));
    }

    @PostMapping(value = "/{assignmentId}/submission/privacy-check", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Void> checkPrivacy(Principal principal, @PathVariable UUID assignmentId,
            @RequestParam MultipartFile image) {
        reservations.status(principal.getName(), assignmentId);
        privacy.requireClear(AssignedWebImage.read(image, true));
        return ResponseEntity.noContent().cacheControl(CacheControl.noStore()).build();
    }

    private static ResponseEntity<Receipt> receipt(AssignedUploadReservation.Attempt attempt, int version) {
        return ResponseEntity.ok().cacheControl(CacheControl.noStore()).body(new Receipt(attempt.submissionId(), version));
    }
}

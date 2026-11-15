package com.mathvisionkids.api.submission;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.storage.MinioObjectStorageService;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.UUID;
import javax.imageio.ImageIO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.jdbc.core.JdbcTemplate;

class AssignedStudentUploadControllerTest {
    private final AssignedUploadReservation reservations = mock(AssignedUploadReservation.class);
    private final MinioObjectStorageService storage = mock(MinioObjectStorageService.class);
    private final AssignedImagePrivacy privacy = mock(AssignedImagePrivacy.class);
    private final AssignedStudentUploadController controller = new AssignedStudentUploadController(reservations, storage, privacy);
    private final UUID assignment = UUID.randomUUID(), request = UUID.randomUUID(), submission = UUID.randomUUID();
    private MockMultipartFile image;
    private AssignedWebImage validated;

    @BeforeEach
    void prepareImage() throws IOException {
        var output = new ByteArrayOutputStream();
        ImageIO.write(new BufferedImage(32, 32, BufferedImage.TYPE_INT_RGB), "png", output);
        image = new MockMultipartFile("image", "work.png", "image/png", output.toByteArray());
        validated = AssignedWebImage.read(image, true);
    }

    @Test
    void privacyPreviewChecksMembershipAndCreatesNoSubmissionOrObject() {
        var response = controller.checkPrivacy(() -> "student", assignment, image);

        assertEquals(204, response.getStatusCode().value());
        assertEquals("no-store", response.getHeaders().getCacheControl());
        verify(reservations).status("student", assignment);
        verifyNoMoreInteractions(reservations);
        verify(privacy).requireClear(any());
        verifyNoInteractions(storage);
    }

    @Test
    void privacyPreviewRejectsUnrelatedStudentBeforeInspection() {
        doThrow(new ApiException("NOT_FOUND", "Missing", org.springframework.http.HttpStatus.NOT_FOUND))
                .when(reservations).status("student", assignment);

        assertEquals("NOT_FOUND", assertThrows(ApiException.class,
                () -> controller.checkPrivacy(() -> "student", assignment, image)).getCode());
        verifyNoInteractions(privacy, storage);
    }

    @Test
    void privacyPreviewRejectionDoesNotCreateAttemptOrObject() {
        doThrow(new ApiException("IMAGE_PRIVACY_REVIEW", "Fixture rejection",
                org.springframework.http.HttpStatus.UNPROCESSABLE_ENTITY)).when(privacy).requireClear(any());

        assertEquals("IMAGE_PRIVACY_REVIEW", assertThrows(ApiException.class,
                () -> controller.checkPrivacy(() -> "student", assignment, image)).getCode());
        verify(reservations).status("student", assignment);
        verifyNoMoreInteractions(reservations);
        verifyNoInteractions(storage);
    }

    @Test
    void returnsExistingReceiptWhenSameRequestConfirmsBeforePreparation() {
        var open = attempt("OPEN");
        var confirmed = new AssignedUploadReservation.Attempt(open.id(), submission, open.objectKey(),
                open.digest(), open.expectedVersion(), "CONFIRMED");
        when(reservations.confirmedReplay("student", assignment, request, 0, validated.inputDigest()))
                .thenReturn(java.util.Optional.empty(), java.util.Optional.of(confirmed));
        when(reservations.reserve("student", assignment, request, 0, validated.inputDigest(), validated.storedDigest()))
                .thenReturn(open);
        doThrow(new ApiException("UPLOAD_CONFLICT", "Conflict", org.springframework.http.HttpStatus.CONFLICT))
                .when(reservations).recordPreparedImage(eq(open), any());

        assertEquals(new AssignedStudentUploadController.Receipt(submission, 1),
                controller.upload(() -> "student", assignment, request, 0, true, image).getBody());
        verifyNoInteractions(storage);
    }

    @Test
    void jpegCommentIsRemovedFromTheStoredImage() throws IOException {
        var jpeg = new ByteArrayOutputStream();
        ImageIO.write(new BufferedImage(32, 32, BufferedImage.TYPE_INT_RGB), "jpeg", jpeg);
        byte[] original = jpeg.toByteArray();
        String comment = "synthetic-private-marker";
        byte[] payload = comment.getBytes(java.nio.charset.StandardCharsets.US_ASCII);
        var decorated = new ByteArrayOutputStream();
        decorated.write(original, 0, 2);
        decorated.write(new byte[] {(byte) 0xff, (byte) 0xfe, 0, (byte) (payload.length + 2)});
        decorated.write(payload);
        decorated.write(original, 2, original.length - 2);
        var image = AssignedWebImage.read(
                new MockMultipartFile("image", "work.jpg", "image/jpeg", decorated.toByteArray()), true);
        assertFalse(new String(image.bytes(), java.nio.charset.StandardCharsets.ISO_8859_1).contains(comment));
        assertNotEquals(image.inputDigest(), image.storedDigest());
        assertEquals(32, ImageIO.read(new java.io.ByteArrayInputStream(image.bytes())).getWidth());
    }

    @Test
    void unconfirmedPrivacyDoesNotCreateAnAttemptOrTouchStorage() {
        var error = assertThrows(ApiException.class,
                () -> controller.upload(() -> "student", assignment, request, 0, false, image));
        assertEquals("PRIVACY_REQUIRED", error.getCode());
        verifyNoInteractions(reservations, storage);
    }

    @Test
    void mismatchedImageContentTypeDoesNotCreateAnAttemptOrTouchStorage() {
        var mismatched = new MockMultipartFile("image", "work.jpg", "image/jpeg", validated.bytes());
        var error = assertThrows(ApiException.class,
                () -> controller.upload(() -> "student", assignment, request, 0, true, mismatched));
        assertEquals("IMAGE_INVALID", error.getCode());
        verifyNoInteractions(reservations, storage);
    }

    @Test
    void unavailablePrivacyCheckDoesNotCreateAnAttemptOrWriteAnObject() {
        var unavailable = new AssignedImagePrivacy("", "", new com.fasterxml.jackson.databind.ObjectMapper());
        var closedController = new AssignedStudentUploadController(reservations, storage, unavailable);

        var failure = assertThrows(ApiException.class,
                () -> closedController.upload(() -> "student", assignment, request, 0, true, image));

        assertEquals("IMAGE_PRIVACY_UNAVAILABLE", failure.getCode());
        verify(reservations).confirmedReplay("student", assignment, request, 0, validated.inputDigest());
        verify(reservations).status("student", assignment);
        verifyNoMoreInteractions(reservations);
        verifyNoInteractions(storage);
    }

    @Test
    void confirmedReplayDoesNotWriteToStorage() {
        var attempt = attempt("CONFIRMED");
        when(reservations.confirmedReplay("student", assignment, request, 0, validated.inputDigest()))
                .thenReturn(java.util.Optional.of(attempt));
        assertEquals(new AssignedStudentUploadController.Receipt(submission, 1),
                controller.upload(() -> "student", assignment, request, 0, true, image).getBody());
        verifyNoInteractions(storage, privacy);
    }

    @Test
    void storageFailureDoesNotConfirmImage() throws IOException {
        when(reservations.reserve("student", assignment, request, 0, validated.inputDigest(), validated.storedDigest())).thenReturn(attempt("OPEN"));
        doThrow(new IOException("storage unavailable")).when(storage).storeAssignedImage(anyString(), any(), anyString());
        assertThrows(ApiException.class, () -> controller.upload(() -> "student", assignment, request, 0, true, image));
        verify(reservations, never()).confirm(anyString(), any(), any(), any(), any());
    }

    @Test
    void confirmsOnlyAfterMatchingStoredBytes() throws IOException {
        var attempt = attempt("OPEN");
        when(reservations.reserve("student", assignment, request, 0, validated.inputDigest(), validated.storedDigest())).thenReturn(attempt);
        when(storage.loadBytes(attempt.objectKey())).thenReturn(validated.bytes());
        when(reservations.confirm(eq("student"), eq(assignment), eq(request), eq(attempt), any())).thenReturn(1);
        assertEquals(1, controller.upload(() -> "student", assignment, request, 0, true, image).getBody().imageVersion());
        var order = inOrder(storage, reservations);
        order.verify(reservations).recordPreparedImage(eq(attempt), any());
        order.verify(storage).storeAssignedImage(eq(attempt.objectKey()), any(), eq("image/png"));
        order.verify(storage).loadBytes(attempt.objectKey());
        order.verify(reservations).confirm(eq("student"), eq(assignment), eq(request), eq(attempt), any());
    }

    @Test
    void restartCanConfirmMatchingPreparedObjectWithoutOriginalUpload() throws IOException {
        var attempt = attempt("OPEN");
        var recovery = new AssignedUploadReservation.Recovery("student", assignment, request, attempt,
                validated.storedDigest(), validated.contentType(), validated.bytes().length);
        var worker = new AssignedUploadCleanup(mock(JdbcTemplate.class), storage, reservations);
        when(storage.loadBytes(attempt.objectKey())).thenReturn(validated.bytes());

        worker.reconcile(recovery);

        verify(reservations).confirmRecovered(eq("student"), eq(assignment), eq(request), eq(attempt),
                argThat(image -> image.inputDigest().equals(attempt.digest())
                        && image.storedDigest().equals(validated.storedDigest())));
        verify(storage, never()).storeAssignedImage(anyString(), any(), anyString());
    }

    @Test
    void recoveryStorageOutageDoesNotExpirePreparedAttempt() throws IOException {
        var attempt = attempt("OPEN");
        var recovery = new AssignedUploadReservation.Recovery("student", assignment, request, attempt,
                validated.storedDigest(), validated.contentType(), validated.bytes().length);
        var jdbc = mock(JdbcTemplate.class);
        when(storage.loadBytes(attempt.objectKey())).thenThrow(new IOException("Fixture storage outage"));

        new AssignedUploadCleanup(jdbc, storage, reservations).reconcile(recovery);

        verifyNoInteractions(jdbc, reservations);
    }

    @Test
    void recoveryConfirmedMissingObjectSchedulesExpiryAfterDeadline() throws IOException {
        var attempt = attempt("OPEN");
        var recovery = new AssignedUploadReservation.Recovery("student", assignment, request, attempt,
                validated.storedDigest(), validated.contentType(), validated.bytes().length);
        var jdbc = mock(JdbcTemplate.class);
        when(storage.loadBytes(attempt.objectKey())).thenThrow(new java.io.FileNotFoundException("Fixture missing object"));

        new AssignedUploadCleanup(jdbc, storage, reservations).reconcile(recovery);

        verify(jdbc).update(argThat((String sql) -> sql.contains("state = 'OPEN'")
                && sql.contains("expires_at <= clock_timestamp()")), eq(attempt.id()));
        verifyNoInteractions(reservations);
    }

    @Test
    void recoveryRejectsObjectWithWrongBytes() throws IOException {
        var attempt = attempt("OPEN");
        var recovery = new AssignedUploadReservation.Recovery("student", assignment, request, attempt,
                validated.storedDigest(), validated.contentType(), validated.bytes().length);
        when(storage.loadBytes(attempt.objectKey())).thenReturn(new byte[validated.bytes().length]);

        new AssignedUploadCleanup(mock(JdbcTemplate.class), storage, reservations).reconcile(recovery);

        verifyNoInteractions(reservations);
    }

    private AssignedUploadReservation.Attempt attempt(String state) {
        return new AssignedUploadReservation.Attempt(UUID.randomUUID(), submission, "assigned-work/test",
                validated.inputDigest(), 0, state);
    }
}

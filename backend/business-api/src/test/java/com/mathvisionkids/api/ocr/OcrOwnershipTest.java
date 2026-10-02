package com.mathvisionkids.api.ocr;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.User;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import java.util.Optional;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class OcrOwnershipTest {
    @Test void readingAndEditingRequireTheActualOwner() {
        OcrTrialRepository trials = mock(OcrTrialRepository.class);
        OcrService service = new OcrService(trials, null, null, null, "http://test.invalid", "test-key");
        User owner = new User();
        owner.setEmail("owner@example.test");
        OcrTrial trial = new OcrTrial();
        trial.setTrialId(UUID.randomUUID());
        trial.setUser(owner);
        when(trials.findById(trial.getTrialId())).thenReturn(Optional.of(trial));
        assertEquals(trial.getTrialId(), service.getTrial(trial.getTrialId(), owner.getEmail()).getTrialId());
        assertEquals(HttpStatus.NOT_FOUND, assertThrows(ApiException.class,
                () -> service.getTrial(trial.getTrialId(), "other@example.test")).getStatus());
        assertEquals(HttpStatus.NOT_FOUND, assertThrows(ApiException.class,
                () -> service.recordFeedback(trial.getTrialId(), "other@example.test", new OcrFeedbackRequest("CORRECT", null, false))).getStatus());
    }
}

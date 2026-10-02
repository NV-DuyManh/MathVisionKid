package com.mathvisionkids.api.ocr.multiline;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.ocr.OcrStorageVerifier;
import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class OcrMultilineOwnershipTest {
    private final OcrMultilineTrialRepository trials = mock(OcrMultilineTrialRepository.class);
    private final OcrMultilineLineRepository lines = mock(OcrMultilineLineRepository.class);
    private OcrMultilineService service;
    private OcrMultilineTrial trial;

    @BeforeEach void setup() {
        service = new OcrMultilineService(trials, lines, mock(ObjectStorageService.class),
                mock(OcrStorageVerifier.class), mock(UserRepository.class), new ObjectMapper(),
                "http://test.invalid", "test-key", "REAL_FEEDBACK");
        User owner = new User();
        owner.setEmail("owner@example.test");
        trial = new OcrMultilineTrial();
        trial.setTrialId(UUID.randomUUID());
        trial.setUser(owner);
        when(trials.findById(trial.getTrialId())).thenReturn(Optional.of(trial));
        when(lines.findByTrialOrderByLineOrderAsc(trial)).thenReturn(List.of());
    }
    @Test void ownerCanReadTrial() {
        assertEquals(trial.getTrialId(), service.getTrial(trial.getTrialId(), "owner@example.test").getTrialId());
    }
    @Test void otherStudentCannotReadTrial() {
        ApiException error = assertThrows(ApiException.class, () -> service.getTrial(trial.getTrialId(), "other@example.test"));
        assertEquals(HttpStatus.NOT_FOUND, error.getStatus());
        verifyNoInteractions(lines);
    }
    @Test void otherStudentCannotChangeFeedback() {
        ApiException error = assertThrows(ApiException.class, () -> service.recordLineFeedback(trial.getTrialId(), UUID.randomUUID(), "other@example.test", new MultilineFeedbackRequest()));
        assertEquals(HttpStatus.NOT_FOUND, error.getStatus());
        verifyNoInteractions(lines);
    }
    @Test void oldGuestTrialIsNotAutomaticallyAssignedToAStudent() {
        trial.setUser(null);
        assertThrows(ApiException.class, () -> service.getTrial(trial.getTrialId(), "owner@example.test"));
        verifyNoInteractions(lines);
    }
}

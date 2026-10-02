package com.mathvisionkids.api.ocr.multiline;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import java.util.List;
import java.util.UUID;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class OcrMultilineSecurityTest {
    @Autowired MockMvc mvc;
    @MockBean OcrMultilineService service;

    private MockMultipartFile image() {
        return new MockMultipartFile("image", "page.jpg", "image/jpeg", new byte[]{1,2,3});
    }

    @Test void anonymousDetectionRequiresAuthentication() throws Exception {
        mvc.perform(multipart("/api/v1/ocr/multiline/detect").file(image()))
                .andExpect(status().isUnauthorized());
        verifyNoInteractions(service);
    }
    @Test void anonymousTrialReadRequiresAuthentication() throws Exception {
        mvc.perform(get("/api/v1/ocr/multiline/trials/" + UUID.randomUUID()))
                .andExpect(status().isUnauthorized());
        verifyNoInteractions(service);
    }
    @Test @WithMockUser(roles = "TEACHER")
    void detectionRequiresStudentRole() throws Exception {
        mvc.perform(multipart("/api/v1/ocr/multiline/detect").file(image()))
                .andExpect(status().isForbidden());
        verifyNoInteractions(service);
    }
    @Test @WithMockUser(username = "student@example.test", roles = "STUDENT")
    void studentUsesCanonicalDetectorWithExplicitPrivacyConsent() throws Exception {
        when(service.detectLines(any(), eq(true), eq(false), any()))
                .thenReturn(MultilineDetectResponse.builder().width(800).height(600).lines(List.of()).build());
        mvc.perform(multipart("/api/v1/ocr/multiline/detect").file(image()).param("privacyConfirmed", "true"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.width").value(800));
        verify(service).detectLines(any(), eq(true), eq(false), any());
    }
    @Test @WithMockUser(roles = "STUDENT")
    void missingPrivacyConsentDefaultsToFalse() throws Exception {
        when(service.detectLines(any(), eq(false), eq(false), any()))
                .thenReturn(MultilineDetectResponse.builder().lines(List.of()).build());
        mvc.perform(multipart("/api/v1/ocr/multiline/detect").file(image())).andExpect(status().isOk());
        verify(service).detectLines(any(), eq(false), eq(false), any());
    }
    @Test @WithMockUser(username = "student@example.test", roles = "STUDENT")
    void trialReadPassesAuthenticatedOwnerToService() throws Exception {
        UUID id = UUID.randomUUID();
        when(service.getTrial(id, "student@example.test")).thenReturn(MultilineTrialResponse.builder().trialId(id).lines(List.of()).build());
        mvc.perform(get("/api/v1/ocr/multiline/trials/" + id)).andExpect(status().isOk());
        verify(service).getTrial(id, "student@example.test");
    }
}

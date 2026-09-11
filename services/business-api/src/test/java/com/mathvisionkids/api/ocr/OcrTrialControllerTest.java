package com.mathvisionkids.api.ocr;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
public class OcrTrialControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private OcrTrialRepository ocrTrialRepository;

    private OcrTrial testTrial;

    @BeforeEach
    void setUp() {
        testTrial = new OcrTrial();
        testTrial.setSource("CAMERA");
        testTrial.setLineImageObjectKey("ocr-trials/test.jpg");
        testTrial.setLineImageSha256("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
        testTrial.setPredictedText("hôm nay trôi nắng");
        testTrial.setVerdict("UNVERIFIED");
        testTrial.setModelName("Vietnamese-Handwriting-OCR-Full");
        testTrial.setModelVersion("1.0.0");
        testTrial.setCheckpointSha256("a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941");
        testTrial.setVocabSha256("6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d");
        testTrial.setTrainingEligible(false);
        testTrial.setPrivacyConfirmed(true);
        testTrial = ocrTrialRepository.save(testTrial);
    }

    @Test
    @WithMockUser(username = "student@test.com", roles = {"STUDENT"})
    void testGetTrialSuccess() throws Exception {
        mockMvc.perform(get("/api/v1/ocr/trials/" + testTrial.getTrialId()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.trialId").value(testTrial.getTrialId().toString()))
                .andExpect(jsonPath("$.predictedText").value("hôm nay trôi nắng"))
                .andExpect(jsonPath("$.verdict").value("UNVERIFIED"))
                .andExpect(jsonPath("$.trainingEligible").value(false));
    }

    @Test
    @WithMockUser(username = "student@test.com", roles = {"STUDENT"})
    void testRecordFeedbackCorrect() throws Exception {
        OcrFeedbackRequest request = new OcrFeedbackRequest("CORRECT", null);

        mockMvc.perform(post("/api/v1/ocr/trials/" + testTrial.getTrialId() + "/feedback")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.verdict").value("CORRECT"))
                .andExpect(jsonPath("$.verifiedTextRaw").value("hôm nay trôi nắng"))
                .andExpect(jsonPath("$.trainingEligible").value(true));

        OcrTrial updated = ocrTrialRepository.findById(testTrial.getTrialId()).orElseThrow();
        assertEquals("CORRECT", updated.getVerdict());
        assertTrue(updated.isTrainingEligible());
        assertEquals("hôm nay trôi nắng", updated.getVerifiedTextRaw());
    }

    @Test
    @WithMockUser(username = "student@test.com", roles = {"STUDENT"})
    void testRecordFeedbackCorrected() throws Exception {
        OcrFeedbackRequest request = new OcrFeedbackRequest("CORRECTED", "hôm nay trời nắng");

        mockMvc.perform(post("/api/v1/ocr/trials/" + testTrial.getTrialId() + "/feedback")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.verdict").value("CORRECTED"))
                .andExpect(jsonPath("$.verifiedTextRaw").value("hôm nay trời nắng"))
                .andExpect(jsonPath("$.trainingEligible").value(true));

        OcrTrial updated = ocrTrialRepository.findById(testTrial.getTrialId()).orElseThrow();
        assertEquals("CORRECTED", updated.getVerdict());
        assertTrue(updated.isTrainingEligible());
        assertEquals("hôm nay trời nắng", updated.getVerifiedTextRaw());
    }

    @Test
    @WithMockUser(username = "student@test.com", roles = {"STUDENT"})
    void testRecordFeedbackCorrectedEmptyTextFails() throws Exception {
        OcrFeedbackRequest request = new OcrFeedbackRequest("CORRECTED", "   ");

        mockMvc.perform(post("/api/v1/ocr/trials/" + testTrial.getTrialId() + "/feedback")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    @WithMockUser(username = "student@test.com", roles = {"STUDENT"})
    void testRecordFeedbackSkipped() throws Exception {
        OcrFeedbackRequest request = new OcrFeedbackRequest("SKIPPED", null);

        mockMvc.perform(post("/api/v1/ocr/trials/" + testTrial.getTrialId() + "/feedback")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.verdict").value("SKIPPED"))
                .andExpect(jsonPath("$.trainingEligible").value(false));

        OcrTrial updated = ocrTrialRepository.findById(testTrial.getTrialId()).orElseThrow();
        assertEquals("SKIPPED", updated.getVerdict());
        assertFalse(updated.isTrainingEligible());
        assertNull(updated.getVerifiedTextRaw());
    }

    @Test
    @WithMockUser(username = "student@test.com", roles = {"STUDENT"})
    void testGetMetrics() throws Exception {
        mockMvc.perform(get("/api/v1/ocr/trials/metrics"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalTrials").isNumber())
                .andExpect(jsonPath("$.exactMatchRate").isNumber());
    }

    @Test
    void testUnauthenticatedAccessFails() throws Exception {
        mockMvc.perform(get("/api/v1/ocr/trials/" + testTrial.getTrialId()))
                .andExpect(status().isUnauthorized());
    }
}

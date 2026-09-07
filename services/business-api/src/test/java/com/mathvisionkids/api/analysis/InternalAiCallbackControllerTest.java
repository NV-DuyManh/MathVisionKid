package com.mathvisionkids.api.analysis;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.submission.Submission;
import com.mathvisionkids.api.submission.SubmissionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(properties = {"ai.callback.api-key=test-secret-key"})
@AutoConfigureMockMvc
@ActiveProfiles("test")
@org.springframework.transaction.annotation.Transactional
public class InternalAiCallbackControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private AiJobRepository aiJobRepository;

    @Autowired
    private SubmissionRepository submissionRepository;

    private AiJob testJob;
    private Submission testSubmission;

    @BeforeEach
    public void setup() {

        testSubmission = new Submission();
        testSubmission.setStatus("PROCESSING");
        submissionRepository.save(testSubmission);

        testJob = new AiJob();
        testJob.setSubmission(testSubmission);
        testJob.setStatus("PENDING");
        aiJobRepository.save(testJob);
    }

    @Test
    public void testValidCallback() throws Exception {
        String url = "/internal/v1/ai/jobs/" + testJob.getJobId() + "/callback";

        AiCallbackRequest payload = new AiCallbackRequest();
        payload.setStatus("COMPLETED");

        mockMvc.perform(post(url)
                .header("X-Internal-API-Key", "test-secret-key")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isOk());
                
        AiJob updatedJob = aiJobRepository.findById(testJob.getJobId()).orElseThrow();
        assert "COMPLETED".equals(updatedJob.getStatus());
        
        Submission updatedSubmission = submissionRepository.findById(testSubmission.getSubmissionId()).orElseThrow();
        assert "PROPOSED_GRADE".equals(updatedSubmission.getStatus());
    }

    @Test
    public void testMissingApiKey() throws Exception {
        AiCallbackRequest payload = new AiCallbackRequest();
        payload.setStatus("COMPLETED");

        mockMvc.perform(post("/internal/v1/ai/jobs/" + testJob.getJobId() + "/callback")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isUnauthorized());
    }

    @Test
    public void testInvalidApiKey() throws Exception {
        AiCallbackRequest payload = new AiCallbackRequest();
        payload.setStatus("COMPLETED");

        mockMvc.perform(post("/internal/v1/ai/jobs/" + testJob.getJobId() + "/callback")
                .header("X-Internal-API-Key", "wrong-key")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isUnauthorized());
    }

    @Test
    public void testIdempotency() throws Exception {
        // Set to COMPLETED manually
        testJob.setStatus("COMPLETED");
        aiJobRepository.save(testJob);
        
        // This should normally conflict because submission is PROCESSING, but since job is COMPLETED, 
        // it returns OK immediately and doesn't try to transition.
        AiCallbackRequest payload = new AiCallbackRequest();
        payload.setStatus("COMPLETED");

        mockMvc.perform(post("/internal/v1/ai/jobs/" + testJob.getJobId() + "/callback")
                .header("X-Internal-API-Key", "test-secret-key")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isOk());
    }
}

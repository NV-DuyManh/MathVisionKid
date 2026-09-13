package com.mathvisionkids.api.ocr.multiline;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.user.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.ResponseEntity;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

public class OcrMultilineServiceTest {

    @Mock
    private OcrMultilineTrialRepository trialRepository;

    @Mock
    private OcrMultilineLineRepository lineRepository;

    @Mock
    private UserRepository userRepository;

    @Mock
    private ObjectStorageService objectStorageService;

    @Mock
    private ObjectMapper objectMapper;

    @Mock
    private RestTemplate restTemplate;

    @Mock
    private com.mathvisionkids.api.ocr.OcrStorageVerifier ocrStorageVerifier;

    private OcrMultilineService service;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        service = new OcrMultilineService(
                trialRepository,
                lineRepository,
                objectStorageService,
                ocrStorageVerifier,
                userRepository,
                objectMapper,
                "http://localhost:8000",
                "secret-key-default",
                "REAL_FEEDBACK"
        );
        // Inject the mocked RestTemplate into the service
        ReflectionTestUtils.setField(service, "restTemplate", restTemplate);
    }

    @Test
    @SuppressWarnings("unchecked")
    void testManualLineSerialization_exactBoxesProcessed() throws Exception {
        // Simulating the user discarding auto-boxes and creating exactly 4 manual boxes
        String manualLinesJson = "[" +
                "{\"line_id\": \"manual_1\", \"x\": 10, \"y\": 100, \"width\": 200, \"height\": 50, \"order\": 1}," +
                "{\"line_id\": \"manual_2\", \"x\": 10, \"y\": 160, \"width\": 200, \"height\": 50, \"order\": 2}," +
                "{\"line_id\": \"manual_3\", \"x\": 10, \"y\": 220, \"width\": 200, \"height\": 50, \"order\": 3}," +
                "{\"line_id\": \"manual_4\", \"x\": 10, \"y\": 280, \"width\": 200, \"height\": 50, \"order\": 4}" +
                "]";

        // Provide a real JSON mapper for this test
        ReflectionTestUtils.setField(service, "objectMapper", new ObjectMapper());

        java.awt.image.BufferedImage img = new java.awt.image.BufferedImage(300, 400, java.awt.image.BufferedImage.TYPE_INT_RGB);
        java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();
        javax.imageio.ImageIO.write(img, "jpg", baos);
        byte[] fakeImageBytes = baos.toByteArray();
        MockMultipartFile file = new MockMultipartFile("image", "manual.jpg", "image/jpeg", fakeImageBytes);

        OcrMultilineTrial mockTrial = new OcrMultilineTrial();
        mockTrial.setTrialId(java.util.UUID.randomUUID());
        when(trialRepository.save(any())).thenReturn(mockTrial);

        when(lineRepository.save(any(OcrMultilineLine.class))).thenAnswer(i -> i.getArguments()[0]);
        
        when(restTemplate.exchange(anyString(), any(), any(), any(org.springframework.core.ParameterizedTypeReference.class))).thenReturn(
                ResponseEntity.ok(Map.of("recognized_text", "detected"))
        );

        MultilineTrialResponse response = service.createTrialAndRecognize(
                file, "test@example.com", "CAMERA", true, manualLinesJson
        );

        assertEquals(4, response.getLines().size());
        assertEquals(1, response.getLines().get(0).getLineOrder());
        assertEquals(100, response.getLines().get(0).getY());
        assertEquals(4, response.getLines().get(3).getLineOrder());
        assertEquals(280, response.getLines().get(3).getY());

        // Verify exactly 4 network calls to AI service were made
        verify(restTemplate, times(4)).exchange(anyString(), any(), any(), any(org.springframework.core.ParameterizedTypeReference.class));
    }
}

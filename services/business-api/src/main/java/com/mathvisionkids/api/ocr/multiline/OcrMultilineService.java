package com.mathvisionkids.api.ocr.multiline;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.ocr.OcrStorageVerifier;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.*;

@Service
public class OcrMultilineService {

    private final OcrMultilineTrialRepository trialRepository;
    private final OcrMultilineLineRepository lineRepository;
    private final ObjectStorageService objectStorageService;
    private final OcrStorageVerifier ocrStorageVerifier;
    private final UserRepository userRepository;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final String aiServiceBaseUrl;
    private final String internalApiKey;
    private final String collectionMode;

    public OcrMultilineService(
            OcrMultilineTrialRepository trialRepository,
            OcrMultilineLineRepository lineRepository,
            ObjectStorageService objectStorageService,
            OcrStorageVerifier ocrStorageVerifier,
            UserRepository userRepository,
            ObjectMapper objectMapper,
            @Value("${ai.service.base-url:${AI_SERVICE_URL:http://localhost:8000}}") String aiServiceBaseUrl,
            @Value("${ai.callback.api-key:${INTERNAL_API_KEY:secret-key-default}}") String internalApiKey,
            @Value("${app.ocr.pilot.collection-mode:${OCR_PILOT_COLLECTION_MODE:TEST}}") String collectionMode) {
        this.trialRepository = trialRepository;
        this.lineRepository = lineRepository;
        this.objectStorageService = objectStorageService;
        this.ocrStorageVerifier = ocrStorageVerifier;
        this.userRepository = userRepository;
        this.objectMapper = objectMapper;
        this.aiServiceBaseUrl = aiServiceBaseUrl.replaceAll("/+$", "");
        this.internalApiKey = internalApiKey;
        this.collectionMode = collectionMode != null ? collectionMode.trim() : "TEST";
        this.restTemplate = new RestTemplate();
    }

    public MultilineDetectResponse detectLines(MultipartFile file, Boolean privacyConfirmed) {
        if (Boolean.FALSE.equals(privacyConfirmed) || privacyConfirmed == null || !privacyConfirmed) {
            throw new ApiException("PRIVACY_REQUIRED", "Privacy confirmation is required for multi-line detection", HttpStatus.BAD_REQUEST);
        }

        if (file == null || file.isEmpty()) {
            throw new ApiException("VALIDATION_ERROR", "Page image file is required", HttpStatus.BAD_REQUEST);
        }

        try {
            byte[] imageBytes = file.getBytes();
            String contentType = file.getContentType() != null ? file.getContentType() : "image/jpeg";

            String targetUrl = aiServiceBaseUrl + "/internal/v1/ocr/detect-lines";
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.parseMediaType(contentType.startsWith("image/") ? contentType : "image/jpeg"));
            headers.set("X-Internal-API-Key", internalApiKey);
            HttpEntity<byte[]> requestEntity = new HttpEntity<>(imageBytes, headers);

            ResponseEntity<MultilineDetectResponse> response = restTemplate.exchange(
                    targetUrl,
                    HttpMethod.POST,
                    requestEntity,
                    MultilineDetectResponse.class
            );

            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                throw new ApiException("AI_SERVICE_ERROR", "Failed to detect lines from page", HttpStatus.BAD_GATEWAY);
            }

            return response.getBody();

        } catch (IOException e) {
            throw new ApiException("STORAGE_ERROR", "Failed to read image bytes: " + e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        } catch (Exception e) {
            if (e instanceof ApiException) throw (ApiException) e;
            throw new ApiException("AI_SERVICE_ERROR", "Detection service unreachable: " + e.getMessage(), HttpStatus.BAD_GATEWAY);
        }
    }

    @Transactional
    public MultilineTrialResponse createTrialAndRecognize(
            MultipartFile file,
            String userEmail,
            String source,
            Boolean privacyConfirmed,
            String confirmedLinesJson) {
        if (privacyConfirmed == null || !privacyConfirmed) {
            throw new ApiException("PRIVACY_REQUIRED", "Privacy confirmation is required to create a trial", HttpStatus.BAD_REQUEST);
        }

        if (file == null || file.isEmpty()) {
            throw new ApiException("VALIDATION_ERROR", "Page image file is required", HttpStatus.BAD_REQUEST);
        }

        List<LineBoxDto> confirmedLines;
        try {
            confirmedLines = objectMapper.readValue(confirmedLinesJson, new TypeReference<List<LineBoxDto>>() {});
        } catch (Exception e) {
            throw new ApiException("VALIDATION_ERROR", "Invalid confirmedLines JSON format: " + e.getMessage(), HttpStatus.BAD_REQUEST);
        }

        if (confirmedLines == null || confirmedLines.isEmpty()) {
            throw new ApiException("VALIDATION_ERROR", "At least one line box must be confirmed", HttpStatus.BAD_REQUEST);
        }

        User user = null;
        if (userEmail != null && !userEmail.isBlank()) {
            user = userRepository.findByEmail(userEmail).orElse(null);
        }

        try {
            byte[] pageBytes = file.getBytes();
            String pageSha256 = computeSha256(pageBytes);

            // Read image dimensions
            BufferedImage fullImage = ImageIO.read(new ByteArrayInputStream(pageBytes));
            if (fullImage == null) {
                throw new ApiException("VALIDATION_ERROR", "Cannot decode image file", HttpStatus.BAD_REQUEST);
            }
            int pageWidth = fullImage.getWidth();
            int pageHeight = fullImage.getHeight();

            // Store full page in MinIO
            String pageObjectKey = objectStorageService.store(file, "ocr-trials/multiline");

            // Server-controlled collection mode
            boolean isReal = "REAL_FEEDBACK".equalsIgnoreCase(collectionMode.trim());
            boolean isTest = !isReal;
            String dataOrigin = isReal ? "OWNER_PHYSICAL" : "DEVELOPER_TEST";

            // Persist parent trial
            OcrMultilineTrial trial = new OcrMultilineTrial();
            trial.setUser(user);
            trial.setSource(source != null && !source.isBlank() ? source : "CAMERA");
            trial.setPageImageObjectKey(pageObjectKey);
            trial.setPageImageSha256(pageSha256);
            trial.setPageWidth(pageWidth);
            trial.setPageHeight(pageHeight);
            trial.setPrivacyConfirmed(Boolean.TRUE.equals(privacyConfirmed));
            trial.setTestData(isTest);
            trial.setDataOrigin(dataOrigin);
            trial.setDomain("HANDWRITING_TEXT");
            trial.setStatus("COMPLETED");

            OcrMultilineTrial savedTrial = trialRepository.save(trial);

            // Sort confirmed boxes top-to-bottom
            confirmedLines.sort(Comparator.comparingInt(LineBoxDto::getOrder));
            int maxLines = Math.min(confirmedLines.size(), 30);

            List<OcrMultilineLine> savedLines = new ArrayList<>();

            for (int i = 0; i < maxLines; i++) {
                LineBoxDto box = confirmedLines.get(i);
                int x = Math.max(0, Math.min(box.getX(), pageWidth - 1));
                int y = Math.max(0, Math.min(box.getY(), pageHeight - 1));
                int w = Math.max(10, Math.min(box.getWidth(), pageWidth - x));
                int h = Math.max(10, Math.min(box.getHeight(), pageHeight - y));

                BufferedImage sub = fullImage.getSubimage(x, y, w, h);
                ByteArrayOutputStream baos = new ByteArrayOutputStream();
                ImageIO.write(sub, "jpg", baos);
                byte[] lineCropBytes = baos.toByteArray();
                String lineSha256 = computeSha256(lineCropBytes);

                // Store line crop in MinIO
                MultipartFile lineMultipart = new com.mathvisionkids.api.storage.ByteArrayMultipartFile(
                        lineCropBytes,
                        "line_crop",
                        "line_" + lineSha256.substring(0, 16) + ".jpg",
                        "image/jpeg"
                );
                String lineCropKey = objectStorageService.store(lineMultipart, "ocr-trials/multiline/crops");

                // Call internal CRNN endpoint
                String targetUrl = aiServiceBaseUrl + "/internal/v1/ocr/recognize-line";
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.IMAGE_JPEG);
                headers.set("X-Internal-API-Key", internalApiKey);
                HttpEntity<byte[]> requestEntity = new HttpEntity<>(lineCropBytes, headers);

                ResponseEntity<Map<String, Object>> aiResponse = restTemplate.exchange(
                        targetUrl,
                        HttpMethod.POST,
                        requestEntity,
                        new ParameterizedTypeReference<Map<String, Object>>() {}
                );

                Map<String, Object> aiData = aiResponse.getBody();
                String recognizedText = aiData != null ? String.valueOf(aiData.getOrDefault("recognized_text", "")) : "";
                String modelName = aiData != null ? String.valueOf(aiData.getOrDefault("model_name", "Vietnamese-Handwriting-OCR-Full")) : "Vietnamese-Handwriting-OCR-Full";
                String modelVersion = aiData != null ? String.valueOf(aiData.getOrDefault("model_version", "1.0.0")) : "1.0.0";
                String checkpointSha = aiData != null ? String.valueOf(aiData.getOrDefault("checkpoint_sha256", "")) : "";
                String vocabSha = aiData != null ? String.valueOf(aiData.getOrDefault("vocab_sha256", "")) : "";
                String prepVersion = aiData != null ? String.valueOf(aiData.getOrDefault("preprocessing_version", "v1_resize_64x1024_imagenet")) : "v1_resize_64x1024_imagenet";

                OcrMultilineLine lineEntity = new OcrMultilineLine();
                lineEntity.setTrial(savedTrial);
                lineEntity.setLineOrder(i + 1);
                lineEntity.setX(x);
                lineEntity.setY(y);
                lineEntity.setWidth(w);
                lineEntity.setHeight(h);
                lineEntity.setLineImageObjectKey(lineCropKey);
                lineEntity.setLineImageSha256(lineSha256);
                lineEntity.setPredictedText(recognizedText);
                lineEntity.setVerdict("UNVERIFIED");
                lineEntity.setTrainingEligible(false);
                lineEntity.setModelName(modelName);
                lineEntity.setModelVersion(modelVersion);
                lineEntity.setCheckpointSha256(checkpointSha);
                lineEntity.setVocabSha256(vocabSha);
                lineEntity.setPreprocessingVersion(prepVersion);

                savedLines.add(lineRepository.save(lineEntity));
            }

            savedTrial.setLines(savedLines);
            return MultilineTrialResponse.fromEntity(savedTrial);

        } catch (IOException e) {
            throw new ApiException("STORAGE_ERROR", "Failed to process image: " + e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        } catch (Exception e) {
            if (e instanceof ApiException) throw (ApiException) e;
            throw new ApiException("AI_SERVICE_ERROR", "Multi-line recognition error: " + e.getMessage(), HttpStatus.BAD_GATEWAY);
        }
    }

    @Transactional(readOnly = true)
    public MultilineTrialResponse getTrial(UUID trialId) {
        OcrMultilineTrial trial = trialRepository.findById(trialId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Multi-line OCR trial not found: " + trialId, HttpStatus.NOT_FOUND));
        List<OcrMultilineLine> lines = lineRepository.findByTrialOrderByLineOrderAsc(trial);
        trial.setLines(lines);
        return MultilineTrialResponse.fromEntity(trial);
    }

    @Transactional
    public MultilineLineResponse recordLineFeedback(UUID trialId, UUID lineId, String userEmail, MultilineFeedbackRequest request) {
        OcrMultilineTrial trial = trialRepository.findById(trialId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Multi-line OCR trial not found: " + trialId, HttpStatus.NOT_FOUND));

        OcrMultilineLine line = lineRepository.findByLineIdAndTrial(lineId, trial)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Line not found: " + lineId, HttpStatus.NOT_FOUND));

        if (request.getVerdict() == null || request.getVerdict().isBlank()) {
            throw new ApiException("VALIDATION_ERROR", "Verdict is required (CORRECT, CORRECTED, SKIPPED)", HttpStatus.BAD_REQUEST);
        }

        String verdictUpper = request.getVerdict().trim().toUpperCase();
        if (!Set.of("CORRECT", "CORRECTED", "SKIPPED").contains(verdictUpper)) {
            throw new ApiException("VALIDATION_ERROR", "Verdict must be CORRECT, CORRECTED, or SKIPPED", HttpStatus.BAD_REQUEST);
        }

        if ("CORRECTED".equals(verdictUpper)) {
            if (request.getVerifiedText() == null || request.getVerifiedText().trim().isEmpty()) {
                throw new ApiException("VALIDATION_ERROR", "Verified text cannot be empty for CORRECTED verdict", HttpStatus.BAD_REQUEST);
            }
            // Preserve exact raw input
            line.setVerifiedTextRaw(request.getVerifiedText());
            line.setVerifiedTextNormalized(request.getVerifiedText().trim());
            line.setVerdict("CORRECTED");

        } else if ("CORRECT".equals(verdictUpper)) {
            if (request.getVerifiedText() != null && !request.getVerifiedText().isEmpty()) {
                if (!request.getVerifiedText().equals(line.getPredictedText())) {
                    throw new ApiException(
                            "DATA_INTEGRITY_ERROR",
                            "CORRECT verdict cannot contradict predicted text. If text differs, use CORRECTED verdict.",
                            HttpStatus.BAD_REQUEST
                    );
                }
            }
            line.setVerifiedTextRaw(line.getPredictedText());
            line.setVerifiedTextNormalized(line.getPredictedText() != null ? line.getPredictedText().trim() : null);
            line.setVerdict("CORRECT");

        } else { // SKIPPED
            line.setVerifiedTextRaw(null);
            line.setVerifiedTextNormalized(null);
            line.setVerdict("SKIPPED");
            line.setTrainingEligible(false);
        }

        // Complete training eligibility formula
        boolean eligible = trial.isPrivacyConfirmed()
                && !trial.isTestData()
                && "HANDWRITING_TEXT".equals(trial.getDomain())
                && "COMPLETED".equals(trial.getStatus())
                && ("CORRECT".equals(verdictUpper) || "CORRECTED".equals(verdictUpper))
                && line.getVerifiedTextRaw() != null
                && !line.getVerifiedTextRaw().trim().isEmpty()
                && line.getLineImageObjectKey() != null
                && !line.getLineImageObjectKey().trim().isEmpty()
                && line.getLineImageSha256() != null
                && line.getLineImageSha256().length() == 64;

        if ("CORRECT".equals(verdictUpper)) {
            eligible = eligible && line.getVerifiedTextRaw().equals(line.getPredictedText());
        }

        if (eligible) {
            eligible = ocrStorageVerifier.verifyStorageIntegrity(
                    line.getLineImageObjectKey(),
                    line.getLineImageSha256()
            );
        }

        line.setTrainingEligible(eligible);

        line.setFeedbackAt(Instant.now());
        OcrMultilineLine updated = lineRepository.save(line);
        return MultilineLineResponse.fromEntity(updated);
    }

    private String computeSha256(byte[] data) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(data);
            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 algorithm missing", e);
        }
    }
}

package com.mathvisionkids.api.ocr;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.*;

@Service
public class OcrPilotService {

    private final OcrTrialRepository ocrTrialRepository;
    private final ObjectStorageService objectStorageService;
    private final UserRepository userRepository;
    private final RestTemplate restTemplate;
    private final String aiServiceBaseUrl;

    public OcrPilotService(
            OcrTrialRepository ocrTrialRepository,
            ObjectStorageService objectStorageService,
            UserRepository userRepository,
            @Value("${ai.service.base-url:${AI_SERVICE_URL:http://localhost:8000}}") String aiServiceBaseUrl) {
        this.ocrTrialRepository = ocrTrialRepository;
        this.objectStorageService = objectStorageService;
        this.userRepository = userRepository;
        this.restTemplate = new RestTemplate();
        this.aiServiceBaseUrl = aiServiceBaseUrl.replaceAll("/+$", "");
    }

    @Transactional
    public OcrTrialResponse createTrial(String userEmail, MultipartFile file, String source) {
        if (file == null || file.isEmpty()) {
            throw new ApiException("VALIDATION_ERROR", "Image file is required", HttpStatus.BAD_REQUEST);
        }

        String contentType = file.getContentType();
        if (contentType == null || (!contentType.startsWith("image/") && !contentType.equals("application/octet-stream"))) {
            throw new ApiException("UNSUPPORTED_MEDIA_TYPE", "Only image files are supported", HttpStatus.UNSUPPORTED_MEDIA_TYPE);
        }

        User user = null;
        if (userEmail != null) {
            user = userRepository.findByEmail(userEmail).orElse(null);
        }

        try {
            byte[] imageBytes = file.getBytes();
            String sha256Hex = computeSha256(imageBytes);

            // 1. Store in MinIO
            String objectKey = objectStorageService.store(file, "ocr-trials");

            // 2. Synchronous internal call to CRNN OCR
            String targetUrl = aiServiceBaseUrl + "/internal/v1/ocr/recognize-line";
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.parseMediaType(contentType.startsWith("image/") ? contentType : "image/jpeg"));
            HttpEntity<byte[]> requestEntity = new HttpEntity<>(imageBytes, headers);

            ResponseEntity<Map<String, Object>> responseEntity = restTemplate.exchange(
                    targetUrl,
                    HttpMethod.POST,
                    requestEntity,
                    new ParameterizedTypeReference<Map<String, Object>>() {}
            );
            if (!responseEntity.getStatusCode().is2xxSuccessful() || responseEntity.getBody() == null) {
                throw new ApiException("AI_SERVICE_ERROR", "Failed to recognize handwriting line", HttpStatus.BAD_GATEWAY);
            }

            Map<String, Object> aiData = responseEntity.getBody();
            String recognizedText = String.valueOf(aiData.getOrDefault("recognized_text", ""));
            String modelName = String.valueOf(aiData.getOrDefault("model_name", "Vietnamese-Handwriting-OCR-Full"));
            String modelVersion = String.valueOf(aiData.getOrDefault("model_version", "1.0.0"));
            String checkpointSha256 = String.valueOf(aiData.getOrDefault("checkpoint_sha256", ""));
            String vocabSha256 = String.valueOf(aiData.getOrDefault("vocab_sha256", ""));
            String prepVersion = String.valueOf(aiData.getOrDefault("preprocessing_version", "v1_resize_64x1024_imagenet"));

            // 3. Persist OcrTrial entity
            OcrTrial trial = new OcrTrial();
            trial.setUser(user);
            trial.setSource(source != null && !source.isBlank() ? source : "CAMERA");
            trial.setLineImageObjectKey(objectKey);
            trial.setLineImageSha256(sha256Hex);
            trial.setPredictedText(recognizedText);
            trial.setVerdict("UNVERIFIED");
            trial.setModelName(modelName);
            trial.setModelVersion(modelVersion);
            trial.setCheckpointSha256(checkpointSha256);
            trial.setVocabSha256(vocabSha256);
            trial.setPreprocessingVersion(prepVersion);
            trial.setTrainingEligible(false);
            trial.setPrivacyConfirmed(true);

            OcrTrial saved = ocrTrialRepository.save(trial);
            return OcrTrialResponse.fromEntity(saved);

        } catch (IOException e) {
            throw new ApiException("STORAGE_ERROR", "Failed to store image: " + e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        } catch (Exception e) {
            if (e instanceof ApiException) throw (ApiException) e;
            throw new ApiException("AI_SERVICE_ERROR", "CRNN service unreachable: " + e.getMessage(), HttpStatus.BAD_GATEWAY);
        }
    }

    @Transactional(readOnly = true)
    public OcrTrialResponse getTrial(UUID trialId) {
        OcrTrial trial = ocrTrialRepository.findById(trialId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "OCR trial not found: " + trialId, HttpStatus.NOT_FOUND));
        return OcrTrialResponse.fromEntity(trial);
    }

    @Transactional
    public OcrTrialResponse recordFeedback(UUID trialId, String userEmail, OcrFeedbackRequest request) {
        OcrTrial trial = ocrTrialRepository.findById(trialId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "OCR trial not found: " + trialId, HttpStatus.NOT_FOUND));

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
            trial.setVerifiedTextRaw(request.getVerifiedText().trim());
            trial.setVerdict("CORRECTED");
            trial.setTrainingEligible(true);
        } else if ("CORRECT".equals(verdictUpper)) {
            String verified = (request.getVerifiedText() != null && !request.getVerifiedText().trim().isEmpty())
                    ? request.getVerifiedText().trim()
                    : trial.getPredictedText();
            trial.setVerifiedTextRaw(verified);
            trial.setVerdict("CORRECT");
            trial.setTrainingEligible(true);
        } else { // SKIPPED
            trial.setVerifiedTextRaw(null);
            trial.setVerdict("SKIPPED");
            trial.setTrainingEligible(false);
        }

        trial.setFeedbackAt(Instant.now());
        OcrTrial updated = ocrTrialRepository.save(trial);
        return OcrTrialResponse.fromEntity(updated);
    }

    @Transactional(readOnly = true)
    public OcrMetricsResponse getMetrics() {
        long total = ocrTrialRepository.count();
        long correct = ocrTrialRepository.countByVerdict("CORRECT");
        long corrected = ocrTrialRepository.countByVerdict("CORRECTED");
        long skipped = ocrTrialRepository.countByVerdict("SKIPPED");
        long unverified = ocrTrialRepository.countByVerdict("UNVERIFIED");
        long verifiedTotal = correct + corrected;

        double exactMatchRate = verifiedTotal > 0 ? (double) correct / verifiedTotal : 0.0;
        String percentageStr = String.format(Locale.US, "%.1f%%", exactMatchRate * 100.0);

        return OcrMetricsResponse.builder()
                .totalTrials(total)
                .verifiedTrials(verifiedTotal)
                .correctCount(correct)
                .correctedCount(corrected)
                .skippedCount(skipped)
                .unverifiedCount(unverified)
                .exactMatchRate(exactMatchRate)
                .exactMatchPercentage(percentageStr)
                .build();
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
            throw new RuntimeException("SHA-256 algorithm not available", e);
        }
    }
}

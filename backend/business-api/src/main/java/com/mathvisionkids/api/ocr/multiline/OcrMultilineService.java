package com.mathvisionkids.api.ocr.multiline;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.storage.ObjectStorageService;
import com.mathvisionkids.api.ocr.OcrStorageVerifier;
import com.mathvisionkids.api.ocr.OcrConfidence;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.transaction.support.TransactionTemplate;
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

    private static final Logger log = LoggerFactory.getLogger(OcrMultilineService.class);
    private static final int MAX_CONFIRMED_LINES = 200;

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
    private final TransactionTemplate advisorTransaction;

    public OcrMultilineService(
            OcrMultilineTrialRepository trialRepository,
            OcrMultilineLineRepository lineRepository,
            ObjectStorageService objectStorageService,
            OcrStorageVerifier ocrStorageVerifier,
            UserRepository userRepository,
            ObjectMapper objectMapper,
            PlatformTransactionManager transactionManager,
            @Value("${ai.service.base-url:${AI_SERVICE_BASE_URL:http://localhost:8000}}") String aiServiceBaseUrl,
            @Value("${ai.callback.api-key:${INTERNAL_API_KEY:secret-key-default}}") String internalApiKey,
            @Value("${app.ocr.pilot.collection-mode:${OCR_PILOT_COLLECTION_MODE:TEST}}") String collectionMode) {
        this.trialRepository = trialRepository;
        this.lineRepository = lineRepository;
        this.objectStorageService = objectStorageService;
        this.ocrStorageVerifier = ocrStorageVerifier;
        this.userRepository = userRepository;
        this.objectMapper = objectMapper;
        this.advisorTransaction = new TransactionTemplate(transactionManager);
        this.aiServiceBaseUrl = aiServiceBaseUrl.replaceAll("/+$", "");
        this.internalApiKey = internalApiKey;
        this.collectionMode = collectionMode != null ? collectionMode.trim() : "TEST";
        this.restTemplate = new RestTemplate();
        log.info("[OCR_MULTILINE_INIT] Resolved aiServiceBaseUrl: {}", this.aiServiceBaseUrl);
    }

    public MultilineDetectResponse detectLines(MultipartFile file, Boolean privacyConfirmed) {
        return detectLines(file, privacyConfirmed, false, null);
    }

    public MultilineDetectResponse detectLines(MultipartFile file, Boolean privacyConfirmed, String requestId) {
        return detectLines(file, privacyConfirmed, false, requestId);
    }

    public MultilineDetectResponse detectLines(MultipartFile file, Boolean privacyConfirmed, Boolean forceRedetect, String requestId) {
        if (Boolean.FALSE.equals(privacyConfirmed) || privacyConfirmed == null || !privacyConfirmed) {
            throw new ApiException("PRIVACY_REQUIRED", "Privacy confirmation is required for multi-line detection", HttpStatus.BAD_REQUEST);
        }

        if (file == null || file.isEmpty()) {
            throw new ApiException("VALIDATION_ERROR", "Page image file is required", HttpStatus.BAD_REQUEST);
        }

        try {
            byte[] imageBytes = file.getBytes();
            String receivedSha256 = computeSha256(imageBytes);
            String filename = file.getOriginalFilename();
            String contentType = file.getContentType() != null ? file.getContentType() : "image/jpeg";

            log.info("[OCR_MULTILINE_TRANSPORT] RECEIVED: file='{}', type='{}', bytes={}, SHA256={}, forceRedetect={}, requestId={}",
                    filename, contentType, imageBytes.length, receivedSha256, forceRedetect, requestId);

            String targetUrl = aiServiceBaseUrl + "/internal/v1/ocr/detect-lines";
            log.info("[OCR_MULTILINE_TARGET] Forwarding /detect-lines to targetUrl: {}", targetUrl);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.parseMediaType(contentType.startsWith("image/") ? contentType : "image/jpeg"));
            headers.set("X-Internal-API-Key", internalApiKey);
            // Return segmentation + CRNN first; document advisors run after the trial is saved.
            headers.set("X-Fast-Path", "true");
            if (requestId != null && !requestId.isBlank()) {
                headers.set("X-Request-ID", requestId);
                log.info("[OCR-PHYSICAL] Spring Boot forwarding requestId: {} to AI service", requestId);
            }
            if (Boolean.TRUE.equals(forceRedetect)) {
                headers.set("X-Force-Redetect", "true");
                log.info("[OCR-PHYSICAL] Spring Boot forwarding forceRedetect=true to AI service");
            }
            HttpEntity<byte[]> requestEntity = new HttpEntity<>(imageBytes, headers);

            byte[] forwardedBytes = requestEntity.getBody();
            String forwardedSha256 = forwardedBytes != null ? computeSha256(forwardedBytes) : "null";
            boolean shaMatches = receivedSha256.equals(forwardedSha256);
            log.info("[OCR_MULTILINE_TRANSPORT] FORWARDED: bytes={}, SHA256={}, match={}",
                    forwardedBytes != null ? forwardedBytes.length : 0, forwardedSha256, shaMatches);

            ResponseEntity<MultilineDetectResponse> response = restTemplate.exchange(
                    targetUrl,
                    HttpMethod.POST,
                    requestEntity,
                    MultilineDetectResponse.class
            );

            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                log.error("[OCR_MULTILINE_TARGET] AI service returned error status: {}", response.getStatusCode());
                throw new ApiException("AI_SERVICE_ERROR", "Failed to detect lines from page", HttpStatus.BAD_GATEWAY);
            }

            MultilineDetectResponse result = response.getBody();
            if (result.getLines() != null) {
                result.getLines().forEach(LineBoxDto::sanitizeConfidence);
            }
            int lineCount = result.getLines() != null ? result.getLines().size() : 0;
            log.info("[OCR_MULTILINE_RESPONSE] Status={}, lines={}, detectorVersion={}",
                    response.getStatusCode(), lineCount, result.getDetectorVersion());

            return result;

        } catch (IOException e) {
            log.error("[OCR_MULTILINE_ERROR] Failed to read image bytes: {}", e.getMessage(), e);
            throw new ApiException("STORAGE_ERROR", "Failed to read image bytes: " + e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        } catch (Exception e) {
            if (e instanceof ApiException) throw (ApiException) e;
            log.error("[OCR_MULTILINE_ERROR] Detection service unreachable or error: {}", e.getMessage(), e);
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
        return createTrialAndRecognize(file, userEmail, source, privacyConfirmed, confirmedLinesJson, null);
    }

    @Transactional
    public MultilineTrialResponse createTrialAndRecognize(
            MultipartFile file,
            String userEmail,
            String source,
            Boolean privacyConfirmed,
            String confirmedLinesJson,
            String requestId) {
        if (confirmedLinesJson == null || confirmedLinesJson.isBlank()) {
            throw new ApiException("VALIDATION_ERROR", "confirmedLines is required", HttpStatus.BAD_REQUEST);
        }
        List<LineBoxDto> confirmedLines;
        try {
            confirmedLines = objectMapper.readValue(confirmedLinesJson, new TypeReference<List<LineBoxDto>>() {});
        } catch (Exception e) {
            throw new ApiException("VALIDATION_ERROR", "Invalid confirmedLines JSON format: " + e.getMessage(), HttpStatus.BAD_REQUEST);
        }
        return createTrialAndRecognize(file, userEmail, source, privacyConfirmed, confirmedLines, requestId);
    }

    @Transactional
    public MultilineTrialResponse createTrialAndRecognize(
            MultipartFile file,
            String userEmail,
            String source,
            Boolean privacyConfirmed,
            List<LineBoxDto> confirmedLines,
            String requestId) {
        if (privacyConfirmed == null || !privacyConfirmed) {
            throw new ApiException("PRIVACY_REQUIRED", "Privacy confirmation is required to create a trial", HttpStatus.BAD_REQUEST);
        }

        if (file == null || file.isEmpty()) {
            throw new ApiException("VALIDATION_ERROR", "Page image file is required", HttpStatus.BAD_REQUEST);
        }

        if (confirmedLines == null || confirmedLines.isEmpty()) {
            throw new ApiException("VALIDATION_ERROR", "At least one line box must be confirmed", HttpStatus.BAD_REQUEST);
        }
        if (confirmedLines.size() > MAX_CONFIRMED_LINES) {
            throw new ApiException("LINE_LIMIT_EXCEEDED", "Crop a smaller part of the page to read every line",
                    HttpStatus.BAD_REQUEST, Map.of("lineLimit", MAX_CONFIRMED_LINES,
                    "submittedLineCount", confirmedLines.size()));
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
            trial.setRequestId(requestId);

            OcrMultilineTrial savedTrial = trialRepository.save(trial);

            // Sort confirmed boxes top-to-bottom
            confirmedLines.sort(Comparator.comparingInt(LineBoxDto::getOrder));

            List<OcrMultilineLine> savedLines = new ArrayList<>();

            for (int i = 0; i < confirmedLines.size(); i++) {
                LineBoxDto box = confirmedLines.get(i);
                box.sanitizeConfidence();
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

                String recognizedText = "";
                String modelName = "Vietnamese-Handwriting-OCR-Full";
                String modelVersion = "1.0.0";
                String checkpointSha = "";
                String vocabSha = "";
                String prepVersion = "v1_resize_64x1024_imagenet";
                Double rawOcrConfidence = null;
                String rawOcrConfidenceSource = null;

                if (box.getRawOcrText() != null && !box.getRawOcrText().trim().isEmpty()) {
                    // Reuse OCR already recognized during detection to prevent slice-induced corruptions
                    recognizedText = box.getRawOcrText().trim();
                    modelName = "Vietnamese-Handwriting-OCR-Full";
                    modelVersion = "1.0.0";
                    rawOcrConfidence = box.getRawOcrConfidence();
                    rawOcrConfidenceSource = box.getRawOcrConfidenceSource();
                } else if (box.getText() != null && !box.getText().trim().isEmpty()) {
                    // Text-only canonical matches have no measured CRNN score.
                    recognizedText = box.getText().trim();
                    modelName = "CANONICAL_EXACT";
                    modelVersion = "poem_block_matched";
                } else {
                    // Call internal CRNN endpoint
                    String targetUrl = aiServiceBaseUrl + "/internal/v1/ocr/recognize-line";
                    HttpHeaders headers = new HttpHeaders();
                    headers.setContentType(MediaType.IMAGE_JPEG);
                    headers.set("X-Internal-API-Key", internalApiKey);
                    if (requestId != null && !requestId.isBlank()) {
                        headers.set("X-Request-ID", requestId);
                    }
                    HttpEntity<byte[]> requestEntity = new HttpEntity<>(lineCropBytes, headers);

                    ResponseEntity<Map<String, Object>> aiResponse = restTemplate.exchange(
                            targetUrl,
                            HttpMethod.POST,
                            requestEntity,
                            new ParameterizedTypeReference<Map<String, Object>>() {}
                    );

                    Map<String, Object> aiData = aiResponse.getBody();
                    if (!aiResponse.getStatusCode().is2xxSuccessful() || aiData == null) {
                        throw new ApiException("AI_SERVICE_ERROR", "Failed to recognize handwriting line", HttpStatus.BAD_GATEWAY);
                    }
                    recognizedText = aiData != null ? String.valueOf(aiData.getOrDefault("recognized_text", "")) : "";
                    modelName = aiData != null ? String.valueOf(aiData.getOrDefault("model_name", "Vietnamese-Handwriting-OCR-Full")) : "Vietnamese-Handwriting-OCR-Full";
                    modelVersion = aiData != null ? String.valueOf(aiData.getOrDefault("model_version", "1.0.0")) : "1.0.0";
                    checkpointSha = aiData != null ? String.valueOf(aiData.getOrDefault("checkpoint_sha256", "")) : "";
                    vocabSha = aiData != null ? String.valueOf(aiData.getOrDefault("vocab_sha256", "")) : "";
                    prepVersion = aiData != null ? String.valueOf(aiData.getOrDefault("preprocessing_version", "v1_resize_64x1024_imagenet")) : "v1_resize_64x1024_imagenet";
                    rawOcrConfidence = OcrConfidence.rawScore(aiData.get("confidence"), aiData.get("confidence_source"));
                    rawOcrConfidenceSource = rawOcrConfidence != null ? OcrConfidence.CRNN_CTC_SOFTMAX : null;
                }

                // Preserve finalText if passed from detect-lines, otherwise fallback to recognizedText
                String effectivePredicted = (box.getFinalText() != null && !box.getFinalText().trim().isEmpty())
                        ? box.getFinalText().trim()
                        : recognizedText;

                // Variables already set above
                OcrMultilineLine lineEntity = new OcrMultilineLine();
                lineEntity.setTrial(savedTrial);
                lineEntity.setLineOrder(i + 1);
                lineEntity.setX(x);
                lineEntity.setY(y);
                lineEntity.setWidth(w);
                lineEntity.setHeight(h);
                lineEntity.setLineImageObjectKey(lineCropKey);
                lineEntity.setLineImageSha256(lineSha256);
                lineEntity.setPredictedText(effectivePredicted);
                lineEntity.setVerdict("UNVERIFIED");
                lineEntity.setTrainingEligible(false);
                lineEntity.setModelName(modelName);
                lineEntity.setModelVersion(modelVersion);
                lineEntity.setCheckpointSha256(checkpointSha);
                lineEntity.setVocabSha256(vocabSha);
                lineEntity.setPreprocessingVersion(prepVersion);
                lineEntity.setRawOcrConfidence(rawOcrConfidence);
                lineEntity.setRawOcrConfidenceSource(rawOcrConfidenceSource);

                // Populate OCR-First audit fields from confirmed box if present
                if (box.getRawOcrText() != null && !box.getRawOcrText().trim().isEmpty()) {
                    lineEntity.setRawOcrText(box.getRawOcrText());
                    lineEntity.setCorrectedText(box.getCorrectedText());
                    lineEntity.setCorrectionConfidence(box.getCorrectionConfidence());
                    lineEntity.setCorrectionApplied(box.getCorrectionApplied());
                    lineEntity.setCorrectionDecision(box.getCorrectionDecision());
                } else {
                    lineEntity.setRawOcrText(recognizedText);
                }

                lineEntity.setGroqSuggestion(box.getGroqSuggestion());
                lineEntity.setGroqConfidence(box.getGroqConfidence());
                lineEntity.setGroqConfidenceSource(box.getGroqConfidenceSource());
                lineEntity.setGroqDecision(box.getGroqDecision());
                lineEntity.setGroqStatus(box.getGroqStatus());
                lineEntity.setGroqModel(box.getGroqModel());

                lineEntity.setGeminiSuggestion(box.getGeminiSuggestion());
                lineEntity.setGeminiConfidence(box.getGeminiConfidence());
                lineEntity.setGeminiConfidenceSource(box.getGeminiConfidenceSource());
                lineEntity.setGeminiDecision(box.getGeminiDecision());
                lineEntity.setGeminiStatus(box.getGeminiStatus());
                lineEntity.setGeminiModel(box.getGeminiModel());

                if (box.getSuggestions() != null && !box.getSuggestions().isEmpty()) {
                    try {
                        lineEntity.setSuggestionsJson(objectMapper.writeValueAsString(box.getSuggestions()));
                    } catch (Exception ignored) {}
                }

                savedLines.add(lineRepository.save(lineEntity));
            }

            // Populate trial-level audit fields
            boolean anyCorrected = savedLines.stream().anyMatch(l -> Boolean.TRUE.equals(l.getCorrectionApplied()));
            savedTrial.setRecognitionEngine("CRNN");
            savedTrial.setSegmentationSource("LOCAL_CV");
            savedTrial.setCorrectionSource(anyCorrected ? "GROQ_POST_CORRECTION" : "NONE");
            savedTrial.setFinalTextSource(anyCorrected ? "CRNN_PLUS_GROQ_CORRECTION" : "CRNN_RAW");
            savedTrial = trialRepository.save(savedTrial);

            savedTrial.setLines(savedLines);
            
            // BACKGROUND ADVISOR PATH
            final UUID finalTrialId = savedTrial.getTrialId();
            final String finalRequestId = requestId;
            Runnable startAdvisors = () -> java.util.concurrent.CompletableFuture.runAsync(
                    () -> runBackgroundAdvisors(finalTrialId, finalRequestId));
            if (TransactionSynchronizationManager.isSynchronizationActive()) {
                TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                    @Override
                    public void afterCommit() {
                        startAdvisors.run();
                    }
                });
            } else {
                startAdvisors.run();
            }

            return MultilineTrialResponse.fromEntity(savedTrial);


        } catch (IOException e) {
            throw new ApiException("STORAGE_ERROR", "Failed to process image: " + e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        } catch (Exception e) {
            if (e instanceof ApiException) throw (ApiException) e;
            throw new ApiException("AI_SERVICE_ERROR", "Multi-line recognition error: " + e.getMessage(), HttpStatus.BAD_GATEWAY);
        }
    }

    @Transactional(readOnly = true)
    public MultilineTrialResponse getTrial(UUID trialId, String userEmail) {
        OcrMultilineTrial trial = trialRepository.findById(trialId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Multi-line OCR trial not found: " + trialId, HttpStatus.NOT_FOUND));
        requireOwner(trial, userEmail);
        List<OcrMultilineLine> lines = lineRepository.findByTrialOrderByLineOrderAsc(trial);
        trial.setLines(lines);
        return MultilineTrialResponse.fromEntity(trial);
    }

    @Transactional
    public MultilineLineResponse recordLineFeedback(UUID trialId, UUID lineId, String userEmail, MultilineFeedbackRequest request) {
        OcrMultilineTrial trial = trialRepository.findById(trialId)
                .orElseThrow(() -> new ApiException("NOT_FOUND", "Multi-line OCR trial not found: " + trialId, HttpStatus.NOT_FOUND));
        requireOwner(trial, userEmail);

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
                && line.getLineImageSha256().matches("^[a-fA-F0-9]{64}$");

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

    private void requireOwner(OcrMultilineTrial trial, String userEmail) {
        if (userEmail == null || trial.getUser() == null || !userEmail.equals(trial.getUser().getEmail())) {
            throw new ApiException("NOT_FOUND", "Multi-line OCR trial not found", HttpStatus.NOT_FOUND);
        }
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

    private void runBackgroundAdvisors(UUID trialId, String requestId) {
        try {
            OcrMultilineTrial trial = trialRepository.findById(trialId).orElse(null);
            if (trial == null) return;
            
            List<OcrMultilineLine> lines = lineRepository.findByTrialOrderByLineOrderAsc(trial);
            if (lines.isEmpty()) return;
            
            List<Map<String, Object>> requestLines = new ArrayList<>();
            for (OcrMultilineLine line : lines) {
                Map<String, Object> reqLine = new HashMap<>();
                reqLine.put("x", line.getX());
                reqLine.put("y", line.getY());
                reqLine.put("width", line.getWidth());
                reqLine.put("height", line.getHeight());
                reqLine.put("rawOcrText", line.getRawOcrText());
                reqLine.put("rawOcrConfidence", line.getRawOcrConfidence());
                reqLine.put("rawOcrConfidenceSource", line.getRawOcrConfidenceSource());
                requestLines.add(reqLine);
            }
            
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("lines", requestLines);
            byte[] pageBytes = objectStorageService.loadBytes(trial.getPageImageObjectKey());
            if (pageBytes != null && pageBytes.length > 0
                    && computeSha256(pageBytes).equals(trial.getPageImageSha256())) {
                requestBody.put("imageBase64", Base64.getEncoder().encodeToString(pageBytes));
            }
            
            String targetUrl = aiServiceBaseUrl + "/internal/v1/ocr/advise-lines";
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("X-Internal-API-Key", internalApiKey);
            if (requestId != null && !requestId.isBlank()) {
                headers.set("X-Request-ID", requestId);
            }
            
            HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(requestBody, headers);
            
            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    targetUrl,
                    HttpMethod.POST,
                    requestEntity,
                    new ParameterizedTypeReference<Map<String, Object>>() {}
            );

            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                throw new IllegalStateException("Background advisor returned no successful response");
            }
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> respLines = (List<Map<String, Object>>) response.getBody().get("lines");
                if (respLines == null || respLines.size() != lines.size()) {
                    throw new IllegalStateException("Background advisor returned an invalid line count");
                }
                if (respLines != null && respLines.size() == lines.size()) {
                    // Cloud waiting stays outside the transaction. Reload under the same row lock
                    // used by feedback so a late advisor cannot merge stale student corrections.
                    advisorTransaction.executeWithoutResult(status -> {
                        boolean anyCorrected = false;
                        for (int i = 0; i < lines.size(); i++) {
                            OcrMultilineLine line = lineRepository.findByLineIdAndTrial(lines.get(i).getLineId(), trial)
                                    .orElse(null);
                            if (line == null) continue;
                            Map<String, Object> respLine = respLines.get(i);

                            line.setGroqSuggestion((String) respLine.get("groqSuggestion"));
                            Double groqScore = OcrConfidence.advisorScore(respLine.get("groqConfidence"),
                                    respLine.get("groqStatus"), respLine.get("groqConfidenceSource"));
                            line.setGroqConfidence(groqScore);
                            line.setGroqConfidenceSource(groqScore != null ? OcrConfidence.AI_SELF_REPORTED : null);
                            line.setGroqDecision((String) respLine.get("groqDecision"));
                            line.setGroqStatus((String) respLine.get("groqStatus"));
                            line.setGroqModel((String) respLine.get("groqModel"));

                            line.setGeminiSuggestion((String) respLine.get("geminiSuggestion"));
                            Double geminiScore = OcrConfidence.advisorScore(respLine.get("geminiConfidence"),
                                    respLine.get("geminiStatus"), respLine.get("geminiConfidenceSource"));
                            line.setGeminiConfidence(geminiScore);
                            line.setGeminiConfidenceSource(geminiScore != null ? OcrConfidence.AI_SELF_REPORTED : null);
                            line.setGeminiDecision((String) respLine.get("geminiDecision"));
                            line.setGeminiStatus((String) respLine.get("geminiStatus"));
                            line.setGeminiModel((String) respLine.get("geminiModel"));
                            if (respLine.get("suggestions") instanceof List<?>) {
                                @SuppressWarnings("unchecked")
                                List<Map<String, Object>> suggestions = (List<Map<String, Object>>) respLine.get("suggestions");
                                try {
                                    line.setSuggestionsJson(objectMapper.writeValueAsString(OcrConfidence.suggestions(suggestions)));
                                } catch (IOException e) {
                                    throw new java.io.UncheckedIOException(e);
                                }
                            } else {
                                line.setSuggestionsJson(null);
                            }
                            line.setCorrectionConfidence(null);

                            if ("UNVERIFIED".equals(line.getVerdict())
                                    && Boolean.TRUE.equals(respLine.get("correctionApplied"))) {
                                line.setPredictedText((String) respLine.get("finalText"));
                                line.setCorrectedText((String) respLine.get("correctedText"));
                                line.setCorrectionApplied(true);
                                line.setCorrectionDecision((String) respLine.get("correctionDecision"));
                                anyCorrected = true;
                            }
                            lineRepository.save(line);
                        }
                        if (anyCorrected) {
                            OcrMultilineTrial currentTrial = trialRepository.findById(trialId).orElseThrow();
                            currentTrial.setCorrectionSource("GROQ_POST_CORRECTION");
                            currentTrial.setFinalTextSource("CRNN_PLUS_GROQ_CORRECTION");
                            trialRepository.save(currentTrial);
                        }
                    });
                }
            }
        } catch (Exception e) {
            log.error("[OCR_MULTILINE_ADVISOR] Background advisor failed for trial {}: {}", trialId, e.getMessage(), e);
            try {
                OcrMultilineTrial trial = trialRepository.findById(trialId).orElse(null);
                if (trial == null) return;
                List<UUID> lineIds = lineRepository.findByTrialOrderByLineOrderAsc(trial).stream()
                        .map(OcrMultilineLine::getLineId).toList();
                advisorTransaction.executeWithoutResult(status -> {
                    for (UUID lineId : lineIds) {
                        OcrMultilineLine current = lineRepository.findByLineIdAndTrial(lineId, trial).orElse(null);
                        if (current == null) continue;
                        boolean changed = false;
                        if (current.getGroqStatus() == null || current.getGroqStatus().isBlank()) {
                            current.setGroqStatus("UNAVAILABLE");
                            current.setGroqSuggestion(null);
                            current.setGroqConfidence(null);
                            current.setGroqConfidenceSource(null);
                            current.setGroqDecision("KEEP_RAW");
                            changed = true;
                        }
                        if (current.getGeminiStatus() == null || current.getGeminiStatus().isBlank()) {
                            current.setGeminiStatus("UNAVAILABLE");
                            current.setGeminiSuggestion(null);
                            current.setGeminiConfidence(null);
                            current.setGeminiConfidenceSource(null);
                            current.setGeminiDecision("KEEP_RAW");
                            changed = true;
                        }
                        if (changed) lineRepository.save(current);
                    }
                });
            } catch (Exception stateError) {
                log.error("[OCR_MULTILINE_ADVISOR] Failed to persist unavailable status for trial {}: {}",
                        trialId, stateError.getMessage(), stateError);
            }
        }
    }

}

package com.mathvisionkids.api.ocr;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.security.Principal;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/ocr/trials")
public class OcrTrialController {

    private final OcrService ocrService;

    public OcrTrialController(OcrService ocrService) {
        this.ocrService = ocrService;
    }

    @PostMapping
    public ResponseEntity<OcrTrialResponse> createTrial(
            @RequestParam("image") MultipartFile image,
            @RequestParam(value = "source", required = false) String source,
            @RequestParam(value = "isTestData", required = false, defaultValue = "false") Boolean isTestData,
            @RequestParam(value = "privacyConfirmed", required = false, defaultValue = "false") Boolean privacyConfirmed,
            Principal principal) {
        String email = principal != null ? principal.getName() : null;
        OcrTrialResponse response = ocrService.createTrial(image, email, source, isTestData, privacyConfirmed);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/{trialId}")
    public ResponseEntity<OcrTrialResponse> getTrial(@PathVariable UUID trialId, Principal principal) {
        OcrTrialResponse response = ocrService.getTrial(trialId, principal.getName());
        return ResponseEntity.ok(response);
    }

    @PostMapping("/{trialId}/feedback")
    public ResponseEntity<OcrTrialResponse> recordFeedback(
            @PathVariable UUID trialId,
            @RequestBody OcrFeedbackRequest request,
            Principal principal) {
        String email = principal != null ? principal.getName() : null;
        OcrTrialResponse response = ocrService.recordFeedback(trialId, email, request);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/metrics")
    public ResponseEntity<OcrMetricsResponse> getMetrics() {
        OcrMetricsResponse metrics = ocrService.getMetrics();
        return ResponseEntity.ok(metrics);
    }
}

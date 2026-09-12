package com.mathvisionkids.api.ocr.multiline;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.security.Principal;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/ocr/multiline")
public class OcrMultilineController {

    private final OcrMultilineService multilineService;

    public OcrMultilineController(OcrMultilineService multilineService) {
        this.multilineService = multilineService;
    }

    @PostMapping("/detect")
    public ResponseEntity<MultilineDetectResponse> detectLines(
            @RequestParam("image") MultipartFile image,
            @RequestParam(value = "privacyConfirmed", required = false, defaultValue = "false") Boolean privacyConfirmed) {
        MultilineDetectResponse response = multilineService.detectLines(image, privacyConfirmed);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/trials")
    public ResponseEntity<MultilineTrialResponse> createTrial(
            @RequestParam("image") MultipartFile image,
            @RequestParam(value = "source", required = false) String source,
            @RequestParam(value = "privacyConfirmed", required = false, defaultValue = "false") Boolean privacyConfirmed,
            @RequestParam("confirmedLines") String confirmedLinesJson,
            Principal principal) {
        String email = principal != null ? principal.getName() : null;
        MultilineTrialResponse response = multilineService.createTrialAndRecognize(
                image, email, source, privacyConfirmed, confirmedLinesJson
        );
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/trials/{trialId}")
    public ResponseEntity<MultilineTrialResponse> getTrial(@PathVariable UUID trialId) {
        MultilineTrialResponse response = multilineService.getTrial(trialId);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/trials/{trialId}/lines/{lineId}/feedback")
    public ResponseEntity<MultilineLineResponse> recordLineFeedback(
            @PathVariable UUID trialId,
            @PathVariable UUID lineId,
            @RequestBody MultilineFeedbackRequest request,
            Principal principal) {
        String email = principal != null ? principal.getName() : null;
        MultilineLineResponse response = multilineService.recordLineFeedback(trialId, lineId, email, request);
        return ResponseEntity.ok(response);
    }
}

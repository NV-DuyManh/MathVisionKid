package com.mathvisionkids.api.ocr.multiline;

import jakarta.servlet.http.HttpServletRequest;
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
            @RequestParam(value = "privacyConfirmed", required = false, defaultValue = "false") Boolean privacyConfirmed,
            HttpServletRequest request) {
        String requestId = resolveRequestId(request);
        MultilineDetectResponse response = multilineService.detectLines(image, privacyConfirmed, requestId);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/trials")
    public ResponseEntity<MultilineTrialResponse> createTrial(
            @RequestParam("image") MultipartFile image,
            @RequestParam(value = "source", required = false) String source,
            @RequestParam(value = "privacyConfirmed", required = false, defaultValue = "false") Boolean privacyConfirmed,
            @RequestParam("confirmedLines") String confirmedLinesJson,
            Principal principal,
            HttpServletRequest request) {
        String email = principal != null ? principal.getName() : null;
        String requestId = resolveRequestId(request);
        MultilineTrialResponse response = multilineService.createTrialAndRecognize(
                image, email, source, privacyConfirmed, confirmedLinesJson, requestId
        );
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    private String resolveRequestId(HttpServletRequest request) {
        if (request == null) return null;
        String reqId = (String) request.getAttribute("X-Request-ID");
        if (reqId == null || reqId.isBlank()) {
            reqId = request.getHeader("X-Request-ID");
        }
        return reqId;
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

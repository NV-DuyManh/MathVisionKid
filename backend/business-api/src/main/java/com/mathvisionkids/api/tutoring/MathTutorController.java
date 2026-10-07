package com.mathvisionkids.api.tutoring;

import com.mathvisionkids.api.common.ApiErrorResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.security.core.Authentication;

import static com.mathvisionkids.api.tutoring.MathTutorDtos.*;

/** Student role is enforced by the existing /api/v1/student/** security rule. */
@RestController
@RequestMapping("/api/v1/student/tutor")
public class MathTutorController {
    private final MathTutorService service;

    public MathTutorController(MathTutorService service) {
        this.service = service;
    }

    @PostMapping(value = "/read", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ReadResponse read(@RequestParam(value = "file", required = false) MultipartFile file,
                             @RequestParam(value = "privacyConfirmed", defaultValue = "false") boolean privacyConfirmed) {
        return service.read(file, privacyConfirmed);
    }

    @PostMapping(value = "/guide", consumes = MediaType.APPLICATION_JSON_VALUE)
    public GuideResponse guide(@Valid @RequestBody GuideRequest request) {
        return service.guide(request);
    }

    @PostMapping(value = "/inspect", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public NotebookRead inspect(@RequestParam(value = "file", required = false) MultipartFile file,
                                @RequestParam(value = "privacyConfirmed", defaultValue = "false") boolean privacyConfirmed) {
        return service.inspect(file, privacyConfirmed);
    }

    @PostMapping(value = "/coach", consumes = MediaType.APPLICATION_JSON_VALUE)
    public GuideResponse coach(@Valid @RequestBody CoachRequest request) {
        return service.coach(request);
    }

    @PostMapping(value = "/division/check", consumes = MediaType.APPLICATION_JSON_VALUE)
    public DivisionCheckResponse checkDivision(@Valid @RequestBody DivisionCheckRequest request) {
        return service.checkDivision(request);
    }

    @PostMapping(value = "/lesson", consumes = MediaType.APPLICATION_JSON_VALUE)
    public LessonResponse lesson(@Valid @RequestBody LessonRequest request, Authentication authentication) {
        return service.lesson(request, authentication.getName());
    }

    @PostMapping(value = "/lesson/answer", consumes = MediaType.APPLICATION_JSON_VALUE)
    public LessonResponse answer(@Valid @RequestBody LessonAnswer request, Authentication authentication) {
        return service.answer(request, authentication.getName());
    }

    @ExceptionHandler({HttpMessageNotReadableException.class, MethodArgumentTypeMismatchException.class,
            MethodArgumentNotValidException.class})
    public ResponseEntity<ApiErrorResponse> invalidInput() {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(new ApiErrorResponse(
                new ApiErrorResponse.ErrorDetail("VALIDATION_ERROR", "Em hãy kiểm tra lại thông tin bài toán.", null, null)));
    }
}

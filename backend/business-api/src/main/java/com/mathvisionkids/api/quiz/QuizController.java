package com.mathvisionkids.api.quiz;

import com.mathvisionkids.api.common.ApiErrorResponse;
import jakarta.validation.Valid;
import org.springframework.http.*;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import java.util.UUID;
import static com.mathvisionkids.api.quiz.QuizDtos.*;

@RestController @RequestMapping("/api/v1/student/quizzes")
public class QuizController {
    private final QuizService service;
    private final QuizNarration narration;
    private final QuizPreparations preparations;
    QuizController(QuizService service, QuizNarration narration, QuizPreparations preparations) { this.service=service; this.narration=narration; this.preparations=preparations; }
    @PostMapping("/prepare") public Preparation prepare(Authentication auth,@Valid @RequestBody Prepare body) { return preparations.prepare(auth.getName(),body); }
    @GetMapping("/preparations/{id}") public Preparation preparationStatus(Authentication auth,@PathVariable UUID id) { return preparations.status(auth.getName(),id); }
    @GetMapping("/runtime") public java.util.Map<String,Object> runtime(Authentication auth) {
        return QuizRuntimeIdentity.view();
    }
    @PostMapping("/from-learning") public Invitation create(Authentication auth,@Valid @RequestBody FromLearning body) { return service.fromLearning(auth.getName(),body); }
    @GetMapping public Library list(Authentication auth,@RequestParam(defaultValue="PENDING") String group,
                                    @RequestParam(defaultValue="0") int page,@RequestParam(defaultValue="20") int size) { return service.list(auth.getName(),group,page,size); }
    @GetMapping("/pending-count") public Counts counts(Authentication auth) { return service.counts(auth.getName()); }
    @GetMapping("/{id}") public View get(Authentication auth,@PathVariable UUID id) { return service.get(auth.getName(),id); }
    @PostMapping({"/{id}/start","/{id}/resume"}) public View start(Authentication auth,@PathVariable UUID id) { return service.start(auth.getName(),id); }
    @PostMapping("/{id}/replay") public View replay(Authentication auth,@PathVariable UUID id,
                                                    @RequestParam(value="mode", required=false) String queryMode,
                                                    @RequestBody(required=false) ReplayRequest body) {
        String mode = (body != null && body.mode() != null && !body.mode().isBlank())
                ? body.mode()
                : (queryMode != null && !queryMode.isBlank()) ? queryMode : "CHALLENGE";
        return service.replay(auth.getName(), id, mode);
    }
    @PostMapping({"/{id}/defer","/{id}/pause"}) public View defer(Authentication auth,@PathVariable UUID id) { return service.defer(auth.getName(),id); }
    @PostMapping("/{id}/submit") public Graded submit(Authentication auth,@PathVariable UUID id,@Valid @RequestBody Submission body) { return service.submit(auth.getName(),id,body); }
    @PostMapping("/{id}/reveal-solution") public View reveal(Authentication auth,@PathVariable UUID id) { return service.reveal(auth.getName(),id); }
    @PostMapping("/{id}/narration") public ResponseEntity<byte[]> narrate(Authentication auth,@PathVariable UUID id,@Valid @RequestBody Voice body) {
        return ResponseEntity.ok().contentType(MediaType.parseMediaType("audio/wav")).cacheControl(CacheControl.noStore()).body(narration.narrate(auth.getName(),id,body.voice()));
    }
    @ModelAttribute public void privateResponses(jakarta.servlet.http.HttpServletResponse response) { response.setHeader("Cache-Control","no-store"); }
    @ExceptionHandler({HttpMessageNotReadableException.class,MethodArgumentTypeMismatchException.class})
    ResponseEntity<ApiErrorResponse> invalid() { return ResponseEntity.badRequest().body(new ApiErrorResponse(new ApiErrorResponse.ErrorDetail("QUIZ_INPUT_INVALID","Em kiểm tra lại thông tin Quiz nhé.",null,null))); }
}

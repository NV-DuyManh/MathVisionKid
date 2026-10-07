package com.mathvisionkids.api.tutoring;

import com.fasterxml.jackson.databind.JsonNode;
import com.mathvisionkids.api.common.ApiException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;

import static com.mathvisionkids.api.tutoring.MathTutorDtos.*;

@Service
public class MathTutorService {
    static final long MAX_IMAGE_BYTES = 8L * 1024 * 1024;
    private final RestTemplate http;
    private final String baseUrl;
    private final String internalKey;

    @Autowired
    public MathTutorService(RestTemplateBuilder builder,
                            @Value("${ai.service.base-url}") String baseUrl,
                            @Value("${ai.callback.api-key}") String internalKey) {
        this(builder.setConnectTimeout(Duration.ofSeconds(5)).setReadTimeout(Duration.ofSeconds(40)).build(),
                baseUrl, internalKey);
    }

    MathTutorService(RestTemplate http, String baseUrl, String internalKey) {
        this.http = http;
        this.baseUrl = baseUrl == null ? "" : baseUrl.replaceAll("/+$", "");
        this.internalKey = internalKey;
    }

    public ReadResponse read(MultipartFile file, boolean privacyConfirmed) {
        byte[] image = validatedImage(file, privacyConfirmed);
        JsonNode body = call("/internal/v1/tutor/read", image, imageType(image));
        String problem = text(body, "problemText", 4000, true);
        String notes = text(body, "notes", 500, true);
        boolean review = flag(body, "needsReview");
        if (problem.isBlank() && !review) throw unavailable();
        return new ReadResponse(problem, review, notes);
    }

    private byte[] validatedImage(MultipartFile file, boolean privacyConfirmed) {
        if (!privacyConfirmed) {
            throw invalid("PRIVACY_REQUIRED", "Em hãy đồng ý sử dụng ảnh trước khi đọc đề.");
        }
        if (file == null || file.isEmpty()) {
            throw invalid("IMAGE_REQUIRED", "Em hãy chọn ảnh bài toán.");
        }
        if (file.getSize() > MAX_IMAGE_BYTES) {
            throw new ApiException("IMAGE_TOO_LARGE", "Ảnh quá lớn. Em hãy chọn ảnh nhỏ hơn 8 MB.", HttpStatus.PAYLOAD_TOO_LARGE);
        }
        byte[] image;
        try {
            image = file.getBytes();
        } catch (IOException ex) {
            throw invalid("IMAGE_INVALID", "Chưa đọc được ảnh. Em hãy chọn lại ảnh bài toán.");
        }
        if (image.length > MAX_IMAGE_BYTES) {
            throw new ApiException("IMAGE_TOO_LARGE", "Ảnh quá lớn. Em hãy chọn ảnh nhỏ hơn 8 MB.", HttpStatus.PAYLOAD_TOO_LARGE);
        }
        return image;
    }

    public NotebookRead inspect(MultipartFile file, boolean privacyConfirmed) {
        byte[] image = validatedImage(file, privacyConfirmed);
        JsonNode body = call("/internal/v1/tutor/inspect", image, imageType(image));
        String kind = text(body, "kind", 16, false);
        if (!List.of("PROBLEM", "WORK", "MIXED", "MULTIPLE", "UNREADABLE").contains(kind)) throw unavailable();
        JsonNode rows = body.get("lines");
        if (rows == null || !rows.isArray() || rows.size() > 35) throw unavailable();
        java.util.ArrayList<NotebookLine> lines = new java.util.ArrayList<>();
        for (JsonNode row : rows) {
            List<Integer> box = null;
            JsonNode coords = row.get("box");
            if (coords != null && !coords.isNull()) {
                if (!coords.isArray() || coords.size() != 4) throw unavailable();
                for (JsonNode n : coords) if (!n.isIntegralNumber() || n.asInt() < 0 || n.asInt() > 1000) throw unavailable();
                box = List.of(coords.get(0).asInt(), coords.get(1).asInt(), coords.get(2).asInt(), coords.get(3).asInt());
                if (box.get(0) >= box.get(2) || box.get(1) >= box.get(3)) throw unavailable();
            }
            lines.add(new NotebookLine(text(row, "text", 500, false), box, flag(row, "uncertain"), writtenDivision(row.get("division"))));
        }
        String problem = text(body, "problemText", 4000, true);
        boolean needsCrop = body.has("needsCrop") && flag(body, "needsCrop");
        if (needsCrop && (!kind.equals("UNREADABLE") || !problem.isEmpty() || !lines.isEmpty())) throw unavailable();
        return new NotebookRead(kind, problem, lines, flag(body, "needsProblem"), needsCrop);
    }

    private WrittenDivision writtenDivision(JsonNode value) {
        if (value == null || value.isNull()) return null;
        if (!value.isObject()) throw unavailable();
        String dividend = text(value, "dividend", 24, false), divisor = text(value, "divisor", 24, false);
        String quotient = value.hasNonNull("quotient") ? text(value, "quotient", 24, false) : null;
        String numberPattern = "(?:[0-9]|\\[\\?\\])+";
        if (!dividend.matches(numberPattern) || !divisor.matches(numberPattern)
                || (quotient != null && !quotient.matches(numberPattern))) throw unavailable();
        JsonNode rows = value.get("rows");
        if (rows == null || !rows.isArray() || rows.size() > 30) throw unavailable();
        java.util.ArrayList<String> written = new java.util.ArrayList<>();
        for (JsonNode row : rows) {
            if (!row.isTextual() || row.asText().length() > 40 || !row.asText().matches("(?:[0-9 +\\-−]|\\[\\?\\])+")) throw unavailable();
            written.add(row.asText());
        }
        return new WrittenDivision(dividend, divisor, quotient, written);
    }

    public DivisionCheckResponse checkDivision(DivisionCheckRequest request) {
        if (!Boolean.TRUE.equals(request.confirmed()))
            throw invalid("TRANSCRIPTION_CONFIRMATION_REQUIRED", "Em đối chiếu các số với ảnh trước nhé.");
        return DivisionChecker.check(request.division());
    }

    public GuideResponse coach(CoachRequest request) {
        if ((request.problemText() + request.workText()).trim().length() < 3)
            throw invalid("TUTOR_INPUT_INVALID", "Em hãy chụp bài toán hoặc nhập đề bài.");
        if (!request.focusText().isBlank() && !request.workText().contains(request.focusText()))
            throw invalid("TUTOR_INPUT_INVALID", "Em hãy chọn một bước trong bài đã đọc.");
        JsonNode body = call("/internal/v1/tutor/coach", request, MediaType.APPLICATION_JSON);
        String stage = text(body, "stage", 20, false);
        if (!stage.equals(request.stage())) throw unavailable();
        return new GuideResponse(stage, text(body, "hint", 800, false), text(body, "question", 300, false),
                text(body, "feedback", 500, true), flag(body, "guarded"));
    }

    public LessonResponse lesson(LessonRequest request, String owner) {
        return lessonResponse(call("/internal/v1/tutor/lesson", java.util.Map.of("owner", owner,
                "problemText", request.problemText(), "workText", request.workText()), MediaType.APPLICATION_JSON));
    }

    public LessonResponse answer(LessonAnswer request, String owner) {
        return lessonResponse(call("/internal/v1/tutor/lesson/answer", java.util.Map.of("owner", owner,
                "sessionId", request.sessionId(), "revision", request.revision(), "answer", request.answer(), "hint", request.hint()), MediaType.APPLICATION_JSON));
    }

    private LessonResponse lessonResponse(JsonNode body) {
        JsonNode outline = body.get("outline"), completed = body.get("completed"), step = body.get("step");
        if (outline == null || !outline.isArray() || outline.size() < 2 || outline.size() > 6
                || completed == null || !completed.isArray() || completed.size() > outline.size()) throw unavailable();
        java.util.ArrayList<String> titles = new java.util.ArrayList<>();
        for (JsonNode title : outline) {
            if (!title.isTextual() || title.asText().isBlank() || title.asText().length() > 100) throw unavailable();
            titles.add(title.asText());
        }
        java.util.ArrayList<CompletedStep> done = new java.util.ArrayList<>();
        for (JsonNode row : completed) done.add(new CompletedStep(text(row, "title", 100, false), text(row, "expression", 220, true),
                text(row, "answer", 100, false), text(row, "unit", 20, true), text(row, "explanation", 500, false)));
        LessonStep current = null;
        if (step != null && !step.isNull()) {
            JsonNode choices = step.get("choices");
            if (!step.isObject() || choices == null || !choices.isArray() || choices.size() > 4) throw unavailable();
            java.util.ArrayList<String> labels = new java.util.ArrayList<>();
            for (JsonNode choice : choices) {
                if (!choice.isTextual() || choice.asText().isBlank() || choice.asText().length() > 100) throw unavailable();
                labels.add(choice.asText());
            }
            current = new LessonStep(text(step, "title", 100, false), text(step, "explanation", 500, false),
                    text(step, "question", 220, false), labels, text(step, "expression", 220, true), text(step, "unit", 20, true), text(step, "workExcerpt", 500, true));
        }
        JsonNode revision = body.get("revision"), index = body.get("stepIndex");
        if (revision == null || !revision.isIntegralNumber() || revision.asInt() < 0 || index == null || !index.isIntegralNumber()
                || index.asInt() != done.size() || index.asInt() > titles.size()) throw unavailable();
        String status = text(body, "status", 20, false);
        if (!List.of("READY", "HINT", "TRY_AGAIN", "CORRECT", "COMPLETE").contains(status)
                || (current == null) != status.equals("COMPLETE")) throw unavailable();
        return new LessonResponse(text(body, "sessionId", 100, false), revision.asInt(), text(body, "topic", 120, false),
                text(body, "goal", 220, false), titles, index.asInt(), current, done, status, text(body, "feedback", 500, true));
    }

    public GuideResponse guide(GuideRequest request) {
        if (!Boolean.TRUE.equals(request.problemConfirmed())) {
            throw invalid("PROBLEM_CONFIRMATION_REQUIRED", "Em hãy kiểm tra và xác nhận đề trước khi nhận gợi ý.");
        }
        String problem = request.problemText() == null ? "" : request.problemText().trim();
        if (problem.length() < 3 || problem.length() > 4000) {
            throw invalid("TUTOR_INPUT_INVALID", "Em hãy nhập đầy đủ đề bài để cùng tìm hướng giải nhé.");
        }
        if ("CHECK_WORK".equals(request.stage())
                && (request.studentAttempt() == null || request.studentAttempt().isBlank())) {
            throw invalid("STUDENT_ATTEMPT_REQUIRED", "Em hãy viết bước em đã làm để cùng kiểm tra nhé.");
        }
        GuideRequest normalized = new GuideRequest(problem, request.problemConfirmed(), request.stage(),
                request.studentAttempt() == null ? "" : request.studentAttempt().trim(), request.hintLevel(),
                request.previousHint() == null ? "" : request.previousHint());
        JsonNode body = call("/internal/v1/tutor/guide", normalized, MediaType.APPLICATION_JSON);
        String stage = text(body, "stage", 20, false);
        if (!stage.equals(request.stage())) throw unavailable();
        return new GuideResponse(stage, text(body, "hint", 800, false), text(body, "question", 300, false),
                text(body, "feedback", 500, true), flag(body, "guarded"));
    }

    private JsonNode call(String path, Object payload, MediaType contentType) {
        if (baseUrl.isBlank() || internalKey == null || internalKey.isBlank()) throw unavailable();
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(contentType);
        headers.setAccept(List.of(MediaType.APPLICATION_JSON));
        headers.set("X-Internal-API-Key", internalKey);
        try {
            JsonNode result = http.postForObject(baseUrl + path, new HttpEntity<>(payload, headers), JsonNode.class);
            if (result == null || !result.isObject()) throw unavailable();
            return result;
        } catch (HttpStatusCodeException ex) {
            if (ex.getStatusCode().value() == 409 || ex.getStatusCode().value() == 410) {
                throw new ApiException("LESSON_EXPIRED", "Em mở lại bài học để tiếp tục nhé.", HttpStatus.valueOf(ex.getStatusCode().value()));
            }
            if (ex.getStatusCode().value() == 400 || ex.getStatusCode().value() == 422) {
                throw new ApiException("TUTOR_INPUT_INVALID", "Chưa đọc rõ bài toán. Em hãy kiểm tra lại đề hoặc chọn ảnh rõ hơn.",
                        HttpStatus.valueOf(ex.getStatusCode().value()));
            }
            if (ex.getStatusCode().value() == 413) {
                throw new ApiException("IMAGE_TOO_LARGE", "Ảnh quá lớn. Em hãy chọn ảnh nhỏ hơn 8 MB.", HttpStatus.PAYLOAD_TOO_LARGE);
            }
            throw unavailable();
        } catch (RestClientException ex) {
            throw unavailable();
        }
    }

    private static MediaType imageType(byte[] image) {
        if (image.length >= 8 && image[0] == (byte) 0x89 && image[1] == 'P' && image[2] == 'N'
                && image[3] == 'G' && image[4] == 13 && image[5] == 10 && image[6] == 26 && image[7] == 10) {
            return MediaType.IMAGE_PNG;
        }
        if (image.length >= 3 && image[0] == (byte) 0xff && image[1] == (byte) 0xd8 && image[2] == (byte) 0xff) {
            return MediaType.IMAGE_JPEG;
        }
        if (image.length >= 12 && new String(image, 0, 4, StandardCharsets.US_ASCII).equals("RIFF")
                && new String(image, 8, 4, StandardCharsets.US_ASCII).equals("WEBP")) {
            return MediaType.parseMediaType("image/webp");
        }
        throw new ApiException("IMAGE_UNSUPPORTED", "Em hãy chọn ảnh PNG, JPG hoặc WebP.", HttpStatus.UNPROCESSABLE_ENTITY);
    }

    private static String text(JsonNode body, String field, int limit, boolean allowBlank) {
        JsonNode value = body.get(field);
        if (value == null || !value.isTextual() || value.asText().length() > limit
                || (!allowBlank && value.asText().isBlank())) throw unavailable();
        return value.asText();
    }

    private static boolean flag(JsonNode body, String field) {
        JsonNode value = body.get(field);
        if (value == null || !value.isBoolean()) throw unavailable();
        return value.asBoolean();
    }

    private static ApiException invalid(String code, String message) {
        return new ApiException(code, message, HttpStatus.BAD_REQUEST);
    }

    private static ApiException unavailable() {
        return new ApiException("TUTOR_UNAVAILABLE", "Chưa thể tạo gợi ý lúc này. Em hãy thử lại sau nhé.", HttpStatus.SERVICE_UNAVAILABLE);
    }
}

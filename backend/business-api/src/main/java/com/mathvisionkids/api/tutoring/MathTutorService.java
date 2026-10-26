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
    private final java.util.Map<String, java.util.ArrayDeque<Long>> audioRequests = new java.util.HashMap<>();

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
        if (!request.isSourceConfirmed())
            throw invalid("TRANSCRIPTION_CONFIRMATION_REQUIRED", "Em kiểm tra lại đề và các số với ảnh trước nhé.");
        return lessonResponse(call("/internal/v1/tutor/lesson", java.util.Map.of("owner", owner,
                "problemText", request.problemText(), "workText", request.workText(),
                "problemConfirmed", true, "workConfirmed", Boolean.TRUE.equals(request.workConfirmed()),
                "guidedUnderstanding", Boolean.TRUE.equals(request.guidedUnderstanding())), MediaType.APPLICATION_JSON));
    }

    public LessonResponse answer(LessonAnswer request, String owner) {
        return lessonResponse(call("/internal/v1/tutor/lesson/answer", java.util.Map.of("owner", owner,
                "sessionId", request.sessionId(), "revision", request.revision(), "answer", request.answer(), "hint", request.hint()), MediaType.APPLICATION_JSON));
    }

    public LessonReply ask(LessonQuestion request, String owner) {
        JsonNode body = call("/internal/v1/tutor/lesson/ask", java.util.Map.of("owner", owner,
                "sessionId", request.sessionId(), "revision", request.revision(),
                "stepIndex", request.stepIndex(), "question", request.question()), MediaType.APPLICATION_JSON);
        return new LessonReply(text(body, "answer", 650, false), text(body, "spokenExplanation", 1600, false),
                text(body, "followUp", 200, true), flag(body, "guarded"));
    }

    public VideoStatus video(VideoRequest request, String owner) {
        return videoResponse(call("/internal/v1/tutor/lesson/video",java.util.Map.of("owner",owner,
                "sessionId",request.sessionId(),"revision",request.revision()),MediaType.APPLICATION_JSON));
    }

    public VideoStatus videoStatus(VideoLookup request, String owner) {
        VideoStatus result=videoResponse(call("/internal/v1/tutor/lesson/video/status",java.util.Map.of("owner",owner,"videoId",request.videoId()),MediaType.APPLICATION_JSON));
        if (!result.videoId().equals(request.videoId())) throw unavailable();
        return result;
    }

    private VideoStatus videoResponse(JsonNode body) {
        String id=text(body,"videoId",64,false), status=text(body,"status",16,false);
        JsonNode progress=body.get("progress"), duration=body.get("durationSeconds");
        boolean audio=flag(body,"hasAudio");
        if (!id.matches("[A-Za-z0-9_-]{24,64}") || !List.of("RENDERING","READY","FAILED").contains(status)
                || progress==null || !progress.isIntegralNumber() || !progress.canConvertToInt() || progress.asInt()<0 || progress.asInt()>100
                || duration==null || !duration.isIntegralNumber() || !duration.canConvertToInt() || duration.asInt()<0 || duration.asInt()>242
                || (status.equals("READY") && (!audio || duration.asInt()==0 || progress.asInt()!=100))) throw unavailable();
        return new VideoStatus(id,status,progress.asInt(),duration.asInt(),audio,text(body,"title",220,false));
    }

    public byte[] videoContent(VideoLookup request, String owner) {
        if (baseUrl.isBlank() || internalKey==null || internalKey.isBlank()) throw unavailable();
        HttpHeaders headers=new HttpHeaders();headers.setContentType(MediaType.APPLICATION_JSON);
        MediaType video=MediaType.parseMediaType("video/mp4");headers.setAccept(List.of(video));headers.set("X-Internal-API-Key",internalKey);
        try {
            var response=http.postForEntity(baseUrl+"/internal/v1/tutor/lesson/video/content",
                    new HttpEntity<>(java.util.Map.of("owner",owner,"videoId",request.videoId()),headers),byte[].class);
            byte[] bytes=response.getBody();
            if (bytes==null || bytes.length<12 || bytes.length>16*1024*1024 || response.getHeaders().getContentType()==null
                    || !video.isCompatibleWith(response.getHeaders().getContentType())
                    || bytes[4]!='f' || bytes[5]!='t' || bytes[6]!='y' || bytes[7]!='p') throw unavailable();
            return bytes;
        } catch (HttpStatusCodeException ex) {
            if (List.of(409,410,429).contains(ex.getStatusCode().value()))
                throw new ApiException("VIDEO_UNAVAILABLE","Em mở lại video từ bài đang học nhé.",HttpStatus.valueOf(ex.getStatusCode().value()));
            throw unavailable();
        } catch (RestClientException ex) {throw unavailable();}
    }

    public byte[] speech(SpeechRequest request) {
        if (baseUrl.isBlank() || internalKey == null || internalKey.isBlank()) throw unavailable();
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setAccept(List.of(MediaType.parseMediaType("audio/mpeg")));
        headers.set("X-Internal-API-Key", internalKey);
        try {
            var response = http.postForEntity(baseUrl + "/internal/v1/tutor/speech",
                    new HttpEntity<>(request, headers), byte[].class);
            byte[] bytes = response.getBody();
            MediaType type = response.getHeaders().getContentType();
            if (type == null || !type.isCompatibleWith(MediaType.parseMediaType("audio/mpeg"))
                    || bytes == null || bytes.length < 128 || bytes.length > 2 * 1024 * 1024
                    || !((bytes[0] == 'I' && bytes[1] == 'D' && bytes[2] == '3')
                        || ((bytes[0] & 0xff) == 0xff && (bytes[1] & 0xe0) == 0xe0))) throw unavailable();
            return bytes;
        } catch (RestClientException ex) {
            throw unavailable();
        }
    }

    public Transcript transcribe(MultipartFile file, boolean consent, String owner) {
        if (!consent) throw invalid("AUDIO_CONSENT_REQUIRED", "Em đồng ý gửi câu hỏi ghi âm trước nhé.");
        if (file == null || file.isEmpty() || file.getSize() > 3L * 1024 * 1024)
            throw invalid("AUDIO_INVALID", "Em ghi một câu hỏi ngắn, tối đa 30 giây nhé.");
        byte[] audio;
        try { audio = file.getBytes(); } catch (IOException ex) { throw unavailable(); }
        if (audio.length < 12 || audio.length > 3L * 1024 * 1024)
            throw invalid("AUDIO_INVALID", "Em thử ghi lại câu hỏi nhé.");
        boolean mp4 = audio[4]=='f' && audio[5]=='t' && audio[6]=='y' && audio[7]=='p';
        boolean webm = audio[0]==0x1a && audio[1]==0x45 && audio[2]==(byte)0xdf && audio[3]==(byte)0xa3;
        boolean wav = audio[0]=='R' && audio[1]=='I' && audio[2]=='F' && audio[3]=='F'
                && audio[8]=='W' && audio[9]=='A' && audio[10]=='V' && audio[11]=='E';
        boolean ogg = audio[0]=='O' && audio[1]=='g' && audio[2]=='g' && audio[3]=='S';
        if (!mp4 && !webm && !wav && !ogg) throw invalid("AUDIO_INVALID", "Chưa đọc được bản ghi âm. Em thử ghi lại nhé.");
        reserveAudio(owner);
        return new Transcript(text(call("/internal/v1/tutor/transcribe", audio,
                MediaType.APPLICATION_OCTET_STREAM), "text", 500, false));
    }

    private synchronized void reserveAudio(String owner) {
        long now = System.nanoTime(), window = Duration.ofMinutes(1).toNanos();
        audioRequests.entrySet().removeIf(entry -> entry.getValue().isEmpty() || now - entry.getValue().getLast() >= window);
        if (!audioRequests.containsKey(owner) && audioRequests.size() >= 1024) throw unavailable();
        var recent = audioRequests.computeIfAbsent(owner, key -> new java.util.ArrayDeque<>());
        while (!recent.isEmpty() && now - recent.getFirst() >= window) recent.removeFirst();
        if (recent.size() >= 4) throw new ApiException("AUDIO_BUSY", "Em chờ một chút rồi ghi câu tiếp nhé.", HttpStatus.TOO_MANY_REQUESTS);
        recent.addLast(now);
    }

    public WorkReviewResponse reviewWork(WorkReviewRequest request) {
        if (request == null || !request.isSourceConfirmed())
            throw invalid("TUTOR_INPUT_INVALID", "Em kiểm tra lại đề và từng dòng bài làm trước khi xác nhận nhé.");
        List<String> source = request.sourceRows();
        var normalized = new WorkReviewRequest(request.sourceId(), request.problemText().strip(),
                String.join("\n", source), true, true);
        JsonNode body = call("/internal/v1/tutor/work-review", normalized, MediaType.APPLICATION_JSON);
        String sourceId = text(body, "sourceId", 100, false), status = text(body, "status", 20, false);
        String summary = text(body, "summary", 500, false), praise = text(body, "praise", 300, true);
        String nextAction = text(body, "nextAction", 300, false), alternative = text(body, "alternative", 600, true);
        JsonNode rows = body.get("rows");
        if (!sourceId.equals(request.sourceId()) || !List.of("CORRECT", "NEEDS_REVISION", "NEEDS_REVIEW").contains(status)
                || rows == null || !rows.isArray() || rows.size() != source.size()) throw unavailable();
        java.util.ArrayList<WorkReviewRow> result = new java.util.ArrayList<>();
        for (int index = 0; index < source.size(); index++) {
            JsonNode row = rows.get(index), lineIndex = row.get("lineIndex"), hints = row.get("hints");
            String sourceText = text(row, "sourceText", 500, false), rowStatus = text(row, "status", 10, false);
            if (lineIndex == null || !lineIndex.isIntegralNumber() || !lineIndex.canConvertToInt() || lineIndex.intValue() != index
                    || !sourceText.equals(source.get(index)) || !List.of("OK", "FIX", "UNSURE").contains(rowStatus)
                    || hints == null || !hints.isArray() || hints.size() > 2
                    || (rowStatus.equals("OK") && !hints.isEmpty())) throw unavailable();
            java.util.ArrayList<String> help = new java.util.ArrayList<>();
            for (JsonNode hint : hints) {
                if (!hint.isTextual() || hint.asText().isBlank() || hint.asText().length() > 300) throw unavailable();
                help.add(hint.asText());
            }
            result.add(new WorkReviewRow(index, sourceText, rowStatus, text(row, "feedback", 400, false), help));
        }
        if (status.equals("CORRECT") ? praise.isBlank() || result.stream().anyMatch(row -> !row.status().equals("OK"))
                : !praise.isBlank() || !alternative.isBlank()) throw unavailable();
        if (status.equals("NEEDS_REVISION") && result.stream().noneMatch(row -> row.status().equals("FIX"))) throw unavailable();
        return new WorkReviewResponse(sourceId, status, summary, praise, result, nextAction, alternative);
    }

    private LessonResponse lessonResponse(JsonNode body) {
        JsonNode outline = body.get("outline"), completed = body.get("completed"), step = body.get("step");
        JsonNode count = body.get("understandingSteps");
        if (count != null && (!count.isIntegralNumber() || !count.canConvertToInt() || (count.asInt() != 0 && count.asInt() != 3))) throw unavailable();
        int understanding = count == null ? 0 : count.asInt();
        if (outline == null || !outline.isArray() || outline.size() - understanding < 2 || outline.size() - understanding > 6
                || completed == null || !completed.isArray() || completed.size() > outline.size()) throw unavailable();
        java.util.ArrayList<String> titles = new java.util.ArrayList<>();
        for (JsonNode title : outline) {
            if (!title.isTextual() || title.asText().isBlank() || title.asText().length() > 100) throw unavailable();
            titles.add(title.asText());
        }
        java.util.ArrayList<CompletedStep> done = new java.util.ArrayList<>();
        for (JsonNode row : completed) {
            String kind = stepKind(row, done.size() < understanding);
            java.util.ArrayList<String> details = new java.util.ArrayList<>();
            if (row.has("calculationDetails")) {
                JsonNode values = row.get("calculationDetails");
                if (!values.isArray() || values.size() > 5) throw unavailable();
                for (JsonNode detail : values) {
                    if (!detail.isTextual() || detail.asText().isBlank() || detail.asText().length() > 500) throw unavailable();
                    details.add(detail.asText());
                }
            }
            done.add(new CompletedStep(text(row, "title", 100, false), text(row, "expression", 220, true),
                text(row, "answer", 100, false), text(row, "unit", 20, true), text(row, "explanation", 500, false),
                row.has("solutionSentence") ? text(row, "solutionSentence", 220, true) : "", details, guidance(row), kind));
        }
        LessonStep current = null;
        if (step != null && !step.isNull()) {
            String kind = stepKind(step, done.size() < understanding);
            JsonNode choices = step.get("choices");
            if (!step.isObject() || choices == null || !choices.isArray() || choices.size() > 4
                    || (kind.equals("UNDERSTAND") && choices.size() < 2)) throw unavailable();
            java.util.ArrayList<String> labels = new java.util.ArrayList<>();
            for (JsonNode choice : choices) {
                if (!choice.isTextual() || choice.asText().isBlank() || choice.asText().length() > 100) throw unavailable();
                labels.add(choice.asText());
            }
            current = new LessonStep(text(step, "title", 100, false), text(step, "explanation", 500, false),
                    text(step, "question", 220, false), labels, text(step, "expression", 220, true), text(step, "unit", 20, true), text(step, "workExcerpt", 500, true),
                    step.has("solutionSentence") ? text(step, "solutionSentence", 220, true) : "", guidance(step), kind);
        }
        JsonNode revision = body.get("revision"), index = body.get("stepIndex");
        if (revision == null || !revision.isIntegralNumber() || revision.asInt() < 0 || index == null || !index.isIntegralNumber()
                || index.asInt() != done.size() || index.asInt() > titles.size()) throw unavailable();
        String status = text(body, "status", 20, false);
        if (!List.of("READY", "HINT", "TRY_AGAIN", "CORRECT", "COMPLETE").contains(status)
                || (current == null) != status.equals("COMPLETE")
                || (current == null ? done.size() != titles.size() : done.size() >= titles.size())) throw unavailable();
        String conclusion = body.has("conclusion") ? text(body, "conclusion", 150, true) : "";
        if (!status.equals("COMPLETE") && !conclusion.isBlank()) throw unavailable();
        LessonSummary summary = null;
        JsonNode quoted = body.get("summary");
        if (quoted != null && !quoted.isNull()) {
            if (understanding != 3 || index.asInt() < 2 || !quoted.isObject()) throw unavailable();
            JsonNode values = quoted.get("givens");
            if (values == null || !values.isArray() || values.isEmpty() || values.size() > 12) throw unavailable();
            java.util.ArrayList<String> givens = new java.util.ArrayList<>();
            for (JsonNode value : values) {
                if (!value.isTextual() || value.asText().isBlank() || value.asText().length() > 200) throw unavailable();
                givens.add(value.asText());
            }
            summary = new LessonSummary(givens, text(quoted, "question", 100, false));
        }
        return new LessonResponse(text(body, "sessionId", 100, false), revision.asInt(), text(body, "topic", 120, false),
                text(body, "goal", 220, false), titles, index.asInt(), current, done, status, text(body, "feedback", 500, true), conclusion, understanding, summary);
    }

    private static String stepKind(JsonNode step, boolean understanding) {
        String kind = step.has("kind") ? text(step, "kind", 10, false) : "MATH";
        if (!kind.equals(understanding ? "UNDERSTAND" : "MATH")) throw unavailable();
        if (understanding && (!text(step, "expression", 220, true).isEmpty()
                || !text(step, "unit", 20, true).isEmpty()
                || (step.has("solutionSentence") && !text(step, "solutionSentence", 220, true).isEmpty()))) throw unavailable();
        return kind;
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

    private static List<String> guidance(JsonNode body) {
        JsonNode values = body.get("guidance");
        if (values == null) return List.of();
        if (!values.isArray() || values.size() > 6) throw unavailable();
        java.util.ArrayList<String> result = new java.util.ArrayList<>();
        for (JsonNode value : values) {
            if (!value.isTextual() || value.asText().isBlank() || value.asText().length() > 500) throw unavailable();
            result.add(value.asText());
        }
        return result;
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

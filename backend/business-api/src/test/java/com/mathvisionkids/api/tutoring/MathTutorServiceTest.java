package com.mathvisionkids.api.tutoring;

import com.mathvisionkids.api.common.ApiException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;

import static com.mathvisionkids.api.tutoring.MathTutorDtos.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;

class MathTutorServiceTest {
    private static final String URL = "http://tutor.internal";
    private static final String READ = "{\"problemText\":\"Lan có 12 bút, cho bạn 3 bút. Hỏi còn bao nhiêu bút?\",\"needsReview\":true,\"notes\":\"Em hãy kiểm tra lại đề nhé.\"}";
    private static final String GUIDE = "{\"stage\":\"PLAN\",\"hint\":\"Khi cho bớt bút, số bút giảm đi.\",\"question\":\"Em chọn phép tính nào?\",\"feedback\":\"\",\"guarded\":false}";
    private static final String INSPECT = "{\"kind\":\"WORK\",\"problemText\":\"\",\"needsProblem\":true,\"lines\":[{\"text\":\"49 : 7 × 2 = 14 (con)\",\"box\":[120,300,700,410],\"uncertain\":false}]}";
    private MockRestServiceServer server;
    private MathTutorService service;

    @Test void preparationForwardsOnlyAuthenticatedOwnerAndValidatesBoundedCounters() {
        server.expect(requestTo(URL+"/internal/v1/tutor/lesson/media/prepare"))
                .andExpect(jsonPath("$.owner").value("real-pupil"))
                .andExpect(jsonPath("$.voice").value("vi-VN-HoaiMyNeural"))
                .andExpect(header("X-Internal-API-Key","test-only-internal-key"))
                .andRespond(withSuccess("{\"totalSteps\":5,\"preparedSteps\":2,\"preparedCharacters\":1200,\"failedItems\":0}",MediaType.APPLICATION_JSON));
        assertEquals(2,service.prepareMedia(new MediaPrepareRequest("prepare-session-123456",0,"vi-VN-HoaiMyNeural"),"real-pupil").get("preparedSteps"));
        server.verify();server.reset();
        server.expect(requestTo(URL+"/internal/v1/tutor/lesson/media/prepare"))
                .andRespond(withSuccess("{\"totalSteps\":5,\"preparedSteps\":6,\"preparedCharacters\":1200,\"failedItems\":0}",MediaType.APPLICATION_JSON));
        assertThrows(ApiException.class,()->service.prepareMedia(new MediaPrepareRequest("prepare-session-123456",0,null),"real-pupil"));
    }

    @ParameterizedTest @ValueSource(strings = {"prepare", "status"})
    void narrationProgressPreservesRetryableCapacityStatus(String action) {
        server.expect(requestTo(URL+"/internal/v1/tutor/lesson/narration/"+action))
                .andExpect(jsonPath("$.owner").value("real-pupil"))
                .andExpect(header("X-Internal-API-Key","test-only-internal-key"))
                .andRespond(withStatus(HttpStatus.TOO_MANY_REQUESTS).body("private upstream details"));
        var request=new NarrationRequest("narration-session-12345",2,java.util.List.of("Em đọc lại đề."),null);
        error("NARRATION_BUSY",HttpStatus.TOO_MANY_REQUESTS,()->{
            if (action.equals("prepare")) service.prepareNarration(request,"real-pupil");
            else service.narrationStatus(request,"real-pupil");
        });
        server.verify();
    }

    @ParameterizedTest @ValueSource(strings = {"prepare", "status"})
    void narrationProgressForwardsBackgroundPrioritySeparatelyFromOwner(String action) {
        server.expect(requestTo(URL+"/internal/v1/tutor/lesson/narration/"+action))
                .andExpect(jsonPath("$.owner").value("real-pupil"))
                .andExpect(jsonPath("$.voice").value("vi-VN-HoaiMyNeural"))
                .andExpect(jsonPath("$.useFallback").value(false))
                .andExpect(jsonPath("$.prefetch").value(true))
                .andRespond(withSuccess("{\"phase\":\"waiting\",\"mode\":\"online\",\"percent\":0,\"elapsedMs\":0,\"completedChunks\":0,\"totalChunks\":0}",MediaType.APPLICATION_JSON));
        var request=new NarrationRequest("narration-session-12345",2,java.util.List.of("Em đọc lại đề."),"vi-VN-HoaiMyNeural",false,true);
        var result=action.equals("prepare")?service.prepareNarration(request,"real-pupil"):service.narrationStatus(request,"real-pupil");
        assertEquals("waiting",result.get("phase"));server.verify();
    }

    @Test void narrationPriorityDefaultsPreserveExistingConstructors() {
        var parts=java.util.List.of("Em đọc lại đề.");
        var oldFour=new NarrationRequest("narration-session-12345",2,parts,null);
        var oldFive=new NarrationRequest("narration-session-12345",2,parts,null,true);
        var explicitNull=new NarrationRequest("narration-session-12345",2,parts,null,null,null);
        assertFalse(oldFour.prefetch());assertFalse(oldFour.useFallback());
        assertFalse(oldFive.prefetch());assertTrue(oldFive.useFallback());
        assertFalse(explicitNull.prefetch());assertFalse(explicitNull.useFallback());
        assertEquals("vi-VN-NamMinhNeural",oldFour.voice());
    }

    @Test void narrationUsesAuthenticatedOwnerAndRejectsWrongBinaryFormat() {
        byte[] wav=new byte[46]; wav[0]='R';wav[1]='I';wav[2]='F';wav[3]='F';wav[8]='W';wav[9]='A';wav[10]='V';wav[11]='E';
        server.expect(requestTo(URL+"/internal/v1/tutor/lesson/narration"))
                .andExpect(jsonPath("$.owner").value("pupil-a"))
                .andExpect(jsonPath("$.paragraphs[0]").value("Em gộp hai nhóm."))
                .andExpect(jsonPath("$.voice").value("vi-VN-HoaiMyNeural"))
                .andExpect(jsonPath("$.useFallback").value(false))
                .andExpect(jsonPath("$.prefetch").doesNotExist())
                .andExpect(header("X-Internal-API-Key","test-only-internal-key"))
                .andRespond(withSuccess(wav,MediaType.parseMediaType("audio/wav")));
        assertArrayEquals(wav,service.narration(new NarrationRequest("narration-session-12345",2,java.util.List.of("Em gộp hai nhóm."),"vi-VN-HoaiMyNeural"),"pupil-a"));
        server.verify(); server.reset();
        server.expect(requestTo(URL+"/internal/v1/tutor/lesson/narration")).andRespond(withSuccess(new byte[50],MediaType.APPLICATION_JSON));
        assertThrows(ApiException.class,()->service.narration(new NarrationRequest("narration-session-12345",2,java.util.List.of("Em gộp hai nhóm."),null),"pupil-a"));
    }

    @Test void narrationPreservesRetryableCapacityStatus() {
        server.expect(requestTo(URL+"/internal/v1/tutor/lesson/narration"))
                .andExpect(jsonPath("$.owner").value("pupil-a"))
                .andRespond(withStatus(HttpStatus.TOO_MANY_REQUESTS));
        var error=assertThrows(ApiException.class,()->service.narration(
                new NarrationRequest("narration-session-12345",2,java.util.List.of("Em gộp hai nhóm."),null),"pupil-a"));
        assertEquals(HttpStatus.TOO_MANY_REQUESTS,error.getStatus());
        server.verify();
    }

    @Test void narrationProgressIsBoundToOwnerAndRejectsInvalidPercent() {
        var request=new NarrationRequest("narration-session-12345",2,java.util.List.of("Em gộp hai nhóm."),null,true);
        server.expect(requestTo(URL+"/internal/v1/tutor/lesson/narration/status"))
                .andExpect(jsonPath("$.owner").value("pupil-a"))
                .andExpect(jsonPath("$.useFallback").value(true))
                .andRespond(withSuccess("{\"phase\":\"fallback\",\"mode\":\"offline\",\"percent\":45,\"elapsedMs\":12345,\"completedChunks\":1,\"totalChunks\":2}",MediaType.APPLICATION_JSON));
        assertEquals("offline",service.narrationStatus(request,"pupil-a").get("mode"));
        server.verify();server.reset();
        server.expect(requestTo(URL+"/internal/v1/tutor/lesson/narration/status"))
                .andRespond(withSuccess("{\"phase\":\"ready\",\"mode\":\"online\",\"percent\":101,\"elapsedMs\":0,\"completedChunks\":0,\"totalChunks\":0}",MediaType.APPLICATION_JSON));
        assertThrows(ApiException.class,()->service.narrationStatus(request,"pupil-a"));
    }







    @BeforeEach void setUp() {
        RestTemplate http = new RestTemplate();
        server = MockRestServiceServer.bindTo(http).build();
        service = new MathTutorService(http, URL + "/", "test-only-internal-key");
    }

    private static MockMultipartFile png() {
        return new MockMultipartFile("file", "page.jpg", "image/jpeg",
                new byte[]{(byte) 0x89, 'P', 'N', 'G', 13, 10, 26, 10, 1});
    }

    @Test void questionUsesAuthenticatedOwnerAndReturnsOnlyStudentFacingFields() {
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson/ask"))
                .andExpect(jsonPath("$.owner").value("pupil-a"))
                .andExpect(jsonPath("$.stepIndex").value(0))
                .andExpect(header("X-Internal-API-Key", "test-only-internal-key"))
                .andRespond(withSuccess("""
                    {"answer":"Ta cần các phần bằng nhau.","spokenExplanation":"Các phần cùng kích thước mới gộp được.",
                     "followUp":"Em thử giải thích nhé?","guarded":false,"providerSecret":"never-return-this"}
                    """, MediaType.APPLICATION_JSON));
        var reply = service.ask(new LessonQuestion("conversation-session-123456",0,0,"Vì sao quy đồng?"), "pupil-a");
        assertEquals("Ta cần các phần bằng nhau.", reply.answer());
        assertFalse(reply.toString().contains("providerSecret"));
        server.verify();
    }

    @Test void recordingRequiresConsentAndRealAudioHeader() {
        assertThrows(ApiException.class, () -> service.transcribe(png(), false, "pupil-a"));
        assertThrows(ApiException.class, () -> service.transcribe(png(), true, "pupil-a"));
        server.verify();
    }

    @Test void acceptsNativeM4aAndWebmWithoutForwardingFileNames() {
        for (byte[] audio : new byte[][] {new byte[]{0,0,0,24,'f','t','y','p','M','4','A',' '},
                new byte[]{0x1a,0x45,(byte)0xdf,(byte)0xa3,0,0,0,0,0,0,0,0}}) {
            server.expect(requestTo(URL + "/internal/v1/tutor/transcribe"))
                    .andExpect(content().bytes(audio))
                    .andRespond(withSuccess("{\"text\":\"Vì sao phải quy đồng?\"}", MediaType.APPLICATION_JSON));
        }
        for (byte[] audio : new byte[][] {new byte[]{0,0,0,24,'f','t','y','p','M','4','A',' '},
                new byte[]{0x1a,0x45,(byte)0xdf,(byte)0xa3,0,0,0,0,0,0,0,0}}) {
            assertEquals("Vì sao phải quy đồng?", service.transcribe(new MockMultipartFile("file", "private-name", "application/octet-stream", audio), true, "pupil-a").text());
        }
        server.verify();
    }

    private static GuideRequest request() {
        return new GuideRequest("Lan có 12 bút, cho bạn 3 bút. Hỏi còn bao nhiêu bút?", true, "PLAN", "", 0, null);
    }

    private static WorkReviewRequest workReviewRequest() {
        return new WorkReviewRequest("source-1234567890", "Có 12 bút, thêm 5 bút. Hỏi có tất cả bao nhiêu bút?",
                " 12 + 5 = 18 \r\n\r\n\u00a0Đáp số: 18 bút.\u00a0\u2028", true, true);
    }

    private static String workReviewBody() {
        return """
            {"sourceId":"source-1234567890","status":"NEEDS_REVISION","summary":"Em xem lại phép cộng nhé.",
             "praise":"","rows":[
              {"lineIndex":0,"sourceText":"12 + 5 = 18","status":"FIX","feedback":"Em cộng lại hai nhóm.","hints":["Đếm tiếp từ 12."]},
              {"lineIndex":1,"sourceText":"Đáp số: 18 bút.","status":"UNSURE","feedback":"Em đối chiếu sau khi sửa phép tính.","hints":[]}],
             "nextAction":"Em tự sửa rồi kiểm tra lại.","alternative":"","apiKey":"provider-secret"}
            """;
    }

    @Test void workReviewForwardsOnlyConfirmedNormalizedSourceAndPreservesAllRows() {
        server.expect(requestTo(URL + "/internal/v1/tutor/work-review"))
                .andExpect(header("X-Internal-API-Key", "test-only-internal-key"))
                .andExpect(jsonPath("$.sourceId").value("source-1234567890"))
                .andExpect(jsonPath("$.workText").value("12 + 5 = 18\nĐáp số: 18 bút."))
                .andExpect(jsonPath("$.problemConfirmed").value(true))
                .andExpect(jsonPath("$.workConfirmed").value(true))
                .andExpect(jsonPath("$.owner").doesNotExist())
                .andExpect(jsonPath("$.sourceConfirmed").doesNotExist())
                .andRespond(withSuccess(workReviewBody(), MediaType.APPLICATION_JSON));
        var result = service.reviewWork(workReviewRequest());
        assertEquals("source-1234567890", result.sourceId());
        assertEquals("NEEDS_REVISION", result.status());
        assertEquals(java.util.List.of("12 + 5 = 18", "Đáp số: 18 bút."), result.rows().stream().map(WorkReviewRow::sourceText).toList());
        assertFalse(result.toString().contains("provider-secret"));
        server.verify();
    }

    @Test void workReviewRejectsInvalidSourcesBeforeCallingUpstream() {
        for (WorkReviewRequest request : java.util.List.of(
                new WorkReviewRequest("short", "Có 12 bút.", "12+5=18", true, true),
                new WorkReviewRequest("a".repeat(101), "Có 12 bút.", "12+5=18", true, true),
                new WorkReviewRequest("source-1234567890", " [?] ", "12+5=18", true, true),
                new WorkReviewRequest("source-1234567890", "Có 12 bút.", "12+[?]=18", true, true),
                new WorkReviewRequest("source-1234567890", " a ", "12+5=18", true, true),
                new WorkReviewRequest("source-1234567890", "a".repeat(4001), "12+5=18", true, true),
                new WorkReviewRequest("source-1234567890", "Có 12 bút.", "a".repeat(6001), true, true),
                new WorkReviewRequest("source-1234567890", "Có 12 bút.", "   \n  ", true, true),
                new WorkReviewRequest("source-1234567890", "Có 12 bút.", "a".repeat(501), true, true),
                new WorkReviewRequest("source-1234567890", "Có 12 bút.", String.join("\n", java.util.Collections.nCopies(36, "dòng")), true, true),
                new WorkReviewRequest("source-1234567890", "Có 12 bút.", "12+5=18", false, true),
                new WorkReviewRequest("source-1234567890", "Có 12 bút.", "12+5=18", true, false))) {
            error("TUTOR_INPUT_INVALID", HttpStatus.BAD_REQUEST, () -> service.reviewWork(request));
        }
        server.verify();
    }

    @Test void workReviewRejectsUntrustedRowsTypesBoundsAndPrematurePraise() throws Exception {
        var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        java.util.List<java.util.function.Consumer<com.fasterxml.jackson.databind.node.ObjectNode>> corruptions = java.util.List.of(
                body -> body.put("sourceId", "another-source-1234"),
                body -> body.put("status", "READY"),
                body -> body.put("summary", " "), body -> body.put("summary", "x".repeat(501)),
                body -> body.put("praise", "Đúng rồi!"), body -> body.put("praise", "x".repeat(301)),
                body -> body.put("alternative", "12+5=17"), body -> body.put("alternative", "x".repeat(601)),
                body -> body.put("nextAction", " "), body -> body.put("nextAction", "x".repeat(301)),
                body -> body.remove("rows"), body -> body.putArray("rows"),
                body -> body.putNull("rows"),
                body -> ((com.fasterxml.jackson.databind.node.ArrayNode) body.get("rows")).remove(1),
                body -> ((com.fasterxml.jackson.databind.node.ArrayNode) body.get("rows")).add(body.get("rows").get(0).deepCopy()),
                body -> ((com.fasterxml.jackson.databind.node.ObjectNode) body.get("rows").get(0)).put("lineIndex", "0"),
                body -> ((com.fasterxml.jackson.databind.node.ObjectNode) body.get("rows").get(0)).put("lineIndex", 4294967296L),
                body -> ((com.fasterxml.jackson.databind.node.ObjectNode) body.get("rows").get(0)).put("lineIndex", 1),
                body -> ((com.fasterxml.jackson.databind.node.ObjectNode) body.get("rows").get(0)).put("sourceText", "12 + 5 = 17"),
                body -> ((com.fasterxml.jackson.databind.node.ObjectNode) body.get("rows").get(0)).put("status", "CORRECT"),
                body -> ((com.fasterxml.jackson.databind.node.ObjectNode) body.get("rows").get(0)).put("status", "OK"),
                body -> ((com.fasterxml.jackson.databind.node.ObjectNode) body.get("rows").get(0)).put("feedback", " "),
                body -> ((com.fasterxml.jackson.databind.node.ObjectNode) body.get("rows").get(0)).put("feedback", "x".repeat(401)),
                body -> ((com.fasterxml.jackson.databind.node.ObjectNode) body.get("rows").get(0)).putArray("hints").add(" "),
                body -> ((com.fasterxml.jackson.databind.node.ObjectNode) body.get("rows").get(0)).putArray("hints").add(1),
                body -> ((com.fasterxml.jackson.databind.node.ObjectNode) body.get("rows").get(0)).putArray("hints").add("x".repeat(301)),
                body -> ((com.fasterxml.jackson.databind.node.ObjectNode) body.get("rows").get(0)).putArray("hints").add("a").add("b").add("c"),
                body -> {
                    body.put("status", "NEEDS_REVIEW");
                    ((com.fasterxml.jackson.databind.node.ObjectNode) body.get("rows").get(0)).put("status", "OK");
                },
                body -> body.put("status", "CORRECT").put("praise", "Em làm đúng rồi."),
                body -> {
                    body.put("status", "CORRECT");
                    body.get("rows").forEach(row -> ((com.fasterxml.jackson.databind.node.ObjectNode) row).put("status", "OK"));
                });
        for (var corrupt : corruptions) {
            var body = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(workReviewBody());
            corrupt.accept(body);
            server.expect(requestTo(URL + "/internal/v1/tutor/work-review"))
                    .andRespond(withSuccess(body.toString(), MediaType.APPLICATION_JSON));
            error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE, () -> service.reviewWork(workReviewRequest()));
            server.verify();
            server.reset();
        }
    }

    @Test void workReviewAcceptsUncertainFeedbackAndOnlyPraisesAllCorrectRows() {
        for (String body : new String[]{workReviewBody().replace("NEEDS_REVISION", "NEEDS_REVIEW"),
                workReviewBody().replace("NEEDS_REVISION", "CORRECT").replace("\"FIX\"", "\"OK\"").replace("\"UNSURE\"", "\"OK\"")
                        .replace("[\"Đếm tiếp từ 12.\"]", "[]")
                        .replace("\"praise\":\"\"", "\"praise\":\"Em đã làm đúng từng bước.\"").replace("\"alternative\":\"\"", "\"alternative\":\"Em cũng có thể gộp theo cách khác.\""),
                workReviewBody().replace("Em xem lại phép cộng nhé.", "x".repeat(500))
                        .replace("Em cộng lại hai nhóm.", "x".repeat(400)).replace("Đếm tiếp từ 12.", "x".repeat(300))
                        .replace("Em tự sửa rồi kiểm tra lại.", "x".repeat(300))}) {
            server.expect(requestTo(URL + "/internal/v1/tutor/work-review"))
                    .andRespond(withSuccess(body, MediaType.APPLICATION_JSON));
            assertEquals(2, service.reviewWork(workReviewRequest()).rows().size());
            server.verify();
            server.reset();
        }
    }

    @Test void workReviewAcceptsAllThirtyFiveRowsIncludingAFullLengthRowWithoutTruncating() throws Exception {
        var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        var response = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(workReviewBody());
        var rows = response.putArray("rows");
        var source = new java.util.ArrayList<String>();
        for (int index = 0; index < 35; index++) {
            String line = index == 0 ? "a".repeat(500) : "Dòng " + index;
            source.add(line);
            rows.addObject().put("lineIndex", index).put("sourceText", line).put("status", "UNSURE")
                    .put("feedback", "Em đối chiếu với đề nhé.").putArray("hints");
        }
        response.put("status", "NEEDS_REVIEW");
        server.expect(requestTo(URL + "/internal/v1/tutor/work-review"))
                .andExpect(jsonPath("$.workText").value(String.join("\n", source)))
                .andRespond(withSuccess(response.toString(), MediaType.APPLICATION_JSON));
        var result = service.reviewWork(new WorkReviewRequest("source-1234567890", "Có 12 bút.", String.join("\n", source), true, true));
        assertEquals(source, result.rows().stream().map(WorkReviewRow::sourceText).toList());
        server.verify();
    }

    private static String comprehensionResponse() {
        return """
            {"sessionId":"abcdefghijklmnopqrstuv","revision":0,"topic":"Thêm bút","goal":"Tìm số bút",
             "understandingSteps":3,"outline":["Dữ kiện","Câu hỏi","Đối chiếu","Một","Hai","Ba","Bốn","Năm","Sáu"],
             "stepIndex":0,"completed":[],"status":"READY","feedback":"",
             "step":{"kind":"UNDERSTAND","title":"Dữ kiện","explanation":"Đọc nguyên đề.",
             "question":"Đề cho biết gì?","choices":["Lan có 12 bút","Hỏi có tất cả bao nhiêu bút?"],
             "expression":"","unit":"","workExcerpt":""}}
            """;
    }

    private static String summaryResponse(int understanding, int index, String summary) throws Exception {
        var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        var response = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(comprehensionResponse());
        response.put("understandingSteps", understanding);
        response.put("stepIndex", index);
        response.set("outline", mapper.readTree("[\"Dữ kiện\",\"Câu hỏi\",\"Đối chiếu\",\"Tính\",\"Kiểm tra\"]"));
        String kind = understanding == 3 ? "UNDERSTAND" : "MATH";
        response.withObject("step").put("kind", kind);
        response.set("completed", mapper.readTree(index == 0 ? "[]" : """
            [{"kind":"%s","title":"Dữ kiện","expression":"","answer":"Lan có 12 bút","unit":"","explanation":"Đọc đề."},
             {"kind":"%s","title":"Câu hỏi","expression":"","answer":"Hỏi có tất cả bao nhiêu bút?","unit":"","explanation":"Đọc đề."}]
            """.formatted(kind, kind)));
        if (summary != null) response.set("summary", mapper.readTree(summary));
        return response.toString();
    }

    @Test void earnedSummaryQuotesArePreservedWithOwnerAndRevisionForwarding() throws Exception {
        String summary = """
            {"givens":["Lan có 12 bút","thêm 5 bút","Hai nhóm cùng màu"],"question":"Hỏi có tất cả bao nhiêu bút?"}
            """;
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson/answer"))
                .andExpect(jsonPath("$.owner").value("student-a"))
                .andExpect(jsonPath("$.revision").value(1))
                .andRespond(withSuccess(summaryResponse(3, 2, summary), MediaType.APPLICATION_JSON));
        var result = service.answer(new LessonAnswer("abcdefghijklmnopqrstuv", 1, "Hỏi có tất cả bao nhiêu bút?", false), "student-a");
        var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        assertEquals(mapper.readTree(summary), mapper.valueToTree(result).get("summary"));
        server.verify();
    }

    @ParameterizedTest @ValueSource(strings = {"false", "[]", "\"text\"", "{}", "{\"givens\":[],\"question\":\"Hỏi?\"}",
        "{\"givens\":[\" \"],\"question\":\"Hỏi?\"}", "{\"givens\":[1],\"question\":\"Hỏi?\"}",
        "{\"givens\":[\"Có 12 bút\"],\"question\":\" \"}", "{\"givens\":[\"Có 12 bút\"],\"question\":1}"})
    void malformedSummaryNeverCrossesThePublicBoundary(String summary) throws Exception {
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson/answer"))
                .andRespond(withSuccess(summaryResponse(3, 2, summary), MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE,
                () -> service.answer(new LessonAnswer("abcdefghijklmnopqrstuv", 1, "question", false), "student-a"));
        server.verify();
    }

    @Test void summaryCannotArriveEarlyOrWithoutComprehensionAndNeverExceedsCaps() throws Exception {
        String valid = "{\"givens\":[\"Có 12 bút\"],\"question\":\"Hỏi?\"}";
        for (String response : java.util.List.of(summaryResponse(3, 0, valid), summaryResponse(0, 2, valid),
                summaryResponse(3, 2, valid.replace("Có 12 bút", "a".repeat(201))),
                summaryResponse(3, 2, valid.replace("Hỏi?", "a".repeat(101))),
                summaryResponse(3, 2, "{\"givens\":[" + String.join(",", java.util.Collections.nCopies(13, "\"fact\"")) + "],\"question\":\"Hỏi?\"}"))) {
            server.expect(requestTo(URL + "/internal/v1/tutor/lesson/answer"))
                    .andRespond(withSuccess(response, MediaType.APPLICATION_JSON));
            error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE,
                    () -> service.answer(new LessonAnswer("abcdefghijklmnopqrstuv", 1, "question", false), "student-a"));
            server.verify();
            server.reset();
        }
    }

    @Test void summaryLimitsAndNullableOlderResponsesAreAccepted() throws Exception {
        String maximum = "{\"givens\":[" + String.join(",", java.util.Collections.nCopies(12, "\"" + "a".repeat(200) + "\""))
                + "],\"question\":\"" + "a".repeat(100) + "\"}";
        for (String summary : new String[]{null, "null", maximum}) {
            server.expect(requestTo(URL + "/internal/v1/tutor/lesson/answer"))
                    .andRespond(withSuccess(summaryResponse(3, 2, summary), MediaType.APPLICATION_JSON));
            assertEquals(2, service.answer(new LessonAnswer("abcdefghijklmnopqrstuv", 1, "question", false), "student-a").stepIndex());
            server.verify();
            server.reset();
        }
    }

    @Test void readingFirstResponseIsExplicitAndOnlyContainsComprehension() throws Exception {
        var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        var body = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(comprehensionResponse());
        body.put("preparingMath", true);
        body.putArray("outline").add("Dữ kiện").add("Câu hỏi").add("Đối chiếu");
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson"))
                .andExpect(jsonPath("$.owner").value("student-a"))
                .andExpect(jsonPath("$.startWithReading").value(true))
                .andRespond(withSuccess(mapper.writeValueAsString(body), MediaType.APPLICATION_JSON));
        var result = service.lesson(new LessonRequest("Lan có 12 bút, thêm 5 bút. Hỏi có tất cả bao nhiêu bút?", "", true, false, true, true), "student-a");
        assertTrue(result.preparingMath());
        assertEquals(3,result.outline().size());
        assertEquals("UNDERSTAND",result.step().kind());
        server.verify();
    }

    @ParameterizedTest @ValueSource(strings = {"\"true\"", "null", "0"})
    void invalidReadingPreparationFlagsAreRejected(String flag) throws Exception {
        var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        var body = (com.fasterxml.jackson.databind.node.ObjectNode) mapper.readTree(comprehensionResponse());
        body.set("preparingMath",mapper.readTree(flag));
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson"))
                .andRespond(withSuccess(mapper.writeValueAsString(body), MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE",HttpStatus.SERVICE_UNAVAILABLE,
                () -> service.lesson(new LessonRequest("Lan có 12 bút, thêm 5 bút?", "", true, false, true, true),"student-a"));
        server.verify();
    }

    @Test void comprehensionFlagAndBoundedNineStepOutlineReachThePublicClient() throws Exception {
        var request = new com.fasterxml.jackson.databind.ObjectMapper().readValue("""
            {"problemText":"Lan có 12 bút, thêm 5 bút. Hỏi có tất cả bao nhiêu bút?",
             "workText":"","problemConfirmed":true,"workConfirmed":false,"guidedUnderstanding":true}
            """, LessonRequest.class);
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson"))
                .andExpect(jsonPath("$.owner").value("student-a"))
                .andExpect(jsonPath("$.guidedUnderstanding").value(true))
                .andRespond(withSuccess(comprehensionResponse(), MediaType.APPLICATION_JSON));
        var result = service.lesson(request, "student-a");
        assertEquals(9, result.outline().size());
        assertTrue(result.step().toString().contains("UNDERSTAND"));
        server.verify();
    }

    @ParameterizedTest @ValueSource(strings = {"1", "\"3\"", "null", "4294967299"})
    void corruptComprehensionCountsAreRejected(String count) {
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson"))
                .andRespond(withSuccess(comprehensionResponse().replace("\"understandingSteps\":3", "\"understandingSteps\":" + count), MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE,
                () -> service.lesson(new LessonRequest("Lan có 12 bút.", "", true, false), "student-a"));
        server.verify();
    }

    @Test void comprehensionCannotContainArithmeticOrAMathPhaseLabel() {
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson"))
                .andRespond(withSuccess(comprehensionResponse().replace("\"expression\":\"\"", "\"expression\":\"12+5\""), MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE,
                () -> service.lesson(new LessonRequest("Lan có 12 bút.", "", true, false), "student-a"));
        server.verify();
        server.reset();
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson"))
                .andRespond(withSuccess(comprehensionResponse().replace("UNDERSTAND", "MATH"), MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE,
                () -> service.lesson(new LessonRequest("Lan có 12 bút.", "", true, false), "student-a"));
        server.verify();
    }

    @Test void structuredDivisionPreservesWrongWrittenNumbersThroughThePublicBoundary() {
        String response = """
            {"kind":"WORK","problemText":"","needsProblem":true,"lines":[{"text":"17843 : 3",
            "box":null,"uncertain":true,"division":{"dividend":"17843","divisor":"3",
            "quotient":"59947","rows":["028","014","023","02"]}}]}
            """;
        server.expect(requestTo(URL + "/internal/v1/tutor/inspect")).andRespond(withSuccess(response, MediaType.APPLICATION_JSON));
        var result = service.inspect(png(), true);
        assertEquals("59947", result.lines().getFirst().division().quotient());
        assertEquals(java.util.List.of("028", "014", "023", "02"), result.lines().getFirst().division().rows());
        server.verify();
    }

    @Test void divisionCheckRequiresConfirmationAndWorksWithoutAnyProviderRequest() {
        var division = new WrittenDivision("49572", "6", "8262", java.util.List.of("015", "037", "012", "00"));
        error("TRANSCRIPTION_CONFIRMATION_REQUIRED", HttpStatus.BAD_REQUEST,
                () -> service.checkDivision(new DivisionCheckRequest(division, false)));
        assertEquals("CORRECT", service.checkDivision(new DivisionCheckRequest(division, true)).status());
        server.verify();
    }

    @Test void lessonProxyInjectsOwnerAndExposesOnlyTheCurrentPublicStep() {
        String response = "{\"sessionId\":\"abcdefghijklmnopqrstuv\",\"revision\":0,\"topic\":\"Thêm bút\",\"goal\":\"Tìm số bút\",\"outline\":[\"Chọn cách làm\",\"Tính\"],\"stepIndex\":0,\"completed\":[],\"status\":\"READY\",\"feedback\":\"\",\"step\":{\"title\":\"Chọn cách làm\",\"explanation\":\"Xem số bút thay đổi.\",\"question\":\"Em chọn gì?\",\"choices\":[\"Cộng\",\"Trừ\"],\"expression\":\"\",\"unit\":\"\",\"workExcerpt\":\"\",\"correctChoice\":\"Cộng\"}}";
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson"))
                .andExpect(header("X-Internal-API-Key", "test-only-internal-key"))
                .andExpect(jsonPath("$.owner").value("student-a"))
                .andExpect(jsonPath("$.problemConfirmed").value(true))
                .andExpect(jsonPath("$.workConfirmed").value(false))
                .andRespond(withSuccess(response, MediaType.APPLICATION_JSON));
        LessonResponse result = service.lesson(new LessonRequest("Lan có 12 bút, được cho 5 bút.", "", true, false), "student-a");
        assertEquals(0, result.stepIndex());
        assertEquals(java.util.List.of("Cộng", "Trừ"), result.step().choices());
        assertFalse(result.toString().contains("correctChoice"));
        server.verify();
    }

    @Test void classroomSolutionFieldsAreBoundedAndFinalAnswerRequiresCompletion() {
        String response = """
                {"sessionId":"abcdefghijklmnopqrstuv","revision":2,"topic":"Tìm số bút","goal":"Gộp hai nhóm",
                 "outline":["Hiểu đề","Tính"],"stepIndex":2,"step":null,"status":"COMPLETE","feedback":"Đã xong",
                 "conclusion":"Đáp số: 17 bút.","completed":[
                  {"title":"Hiểu đề","expression":"","answer":"Cộng","unit":"","explanation":"Gộp hai nhóm."},
                  {"title":"Tính","expression":"12 + 5","answer":"17","unit":"bút","explanation":"Gộp hai nhóm.",
                   "solutionSentence":"Số bút có tất cả là:","calculationDetails":["12 + 5 = 17"],
                   "guidance":["Đọc điều được cho.","Gộp hai nhóm rồi viết lời giải."]}]}
                """;
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson/answer"))
                .andExpect(jsonPath("$.owner").value("student-a"))
                .andRespond(withSuccess(response, MediaType.APPLICATION_JSON));
        var result = service.answer(new LessonAnswer("abcdefghijklmnopqrstuv", 1, "17", false), "student-a");
        assertEquals("Đáp số: 17 bút.", result.conclusion());
        assertEquals("Số bút có tất cả là:", result.completed().get(1).solutionSentence());
        assertEquals(java.util.List.of("12 + 5 = 17"), result.completed().get(1).calculationDetails());
        assertEquals(java.util.List.of("Đọc điều được cho.", "Gộp hai nhóm rồi viết lời giải."), result.completed().get(1).guidance());
        server.verify();
        server.reset();
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson/answer"))
                .andRespond(withSuccess(response.replace("12 + 5 = 17", "x".repeat(501)), MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE,
                () -> service.answer(new LessonAnswer("abcdefghijklmnopqrstuv", 1, "17", false), "student-a"));
        server.verify();
    }

    @ParameterizedTest
    @ValueSource(strings = {"null", "false", "[1]", "[\" \"]", "[\"a\",\"b\",\"c\",\"d\",\"e\",\"f\",\"g\"]"})
    void rejectsMalformedTeachingFromTheProvider(String guidance) {
        String response = """
            {"sessionId":"abcdefghijklmnopqrstuv","revision":0,"topic":"Gộp hai nhóm","goal":"Tìm số bút",
             "outline":["Tính","Kiểm tra"],"stepIndex":0,"completed":[],"status":"READY","feedback":"",
             "step":{"title":"Tính","explanation":"Gộp hai nhóm.","question":"Có bao nhiêu bút?",
             "choices":[],"expression":"12 + 5","unit":"bút","workExcerpt":"","guidance":%s}}
            """.formatted(guidance);
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson")).andRespond(withSuccess(response, MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE,
                () -> service.lesson(new LessonRequest("Lan có 12 bút, thêm 5 bút.", "", true, false), "student-a"));
        server.verify();
    }

    @Test void unconfirmedSourceNeverCallsTheLessonProvider() {
        for (var request : java.util.List.of(
                new LessonRequest("Lan có 12 bút.", "", false, false),
                new LessonRequest("Lan có 12 bút.", "3/2 = 1", true, false),
                new LessonRequest("Lan có [?] bút.", "", true, false),
                new LessonRequest("Lan có 12 bút.", "3/[?]", true, true))) {
            error("TRANSCRIPTION_CONFIRMATION_REQUIRED", HttpStatus.BAD_REQUEST,
                    () -> service.lesson(request, "student-a"));
        }
        server.verify();
    }

    @Test void expiredLessonIsMappedToAnActionablePublicStatus() {
        server.expect(requestTo(URL + "/internal/v1/tutor/lesson/answer"))
                .andRespond(withStatus(HttpStatus.GONE));
        error("LESSON_EXPIRED", HttpStatus.GONE, () -> service.answer(new LessonAnswer("abcdefghijklmnopqrstuv", 0, "12", false), "student-a"));
        server.verify();
    }

    private static void error(String code, HttpStatus status, Runnable action) {
        ApiException ex = assertThrows(ApiException.class, action::run);
        assertEquals(code, ex.getCode());
        assertEquals(status, ex.getStatus());
        assertFalse(ex.getMessage().contains(URL));
        assertFalse(ex.getMessage().contains("test-only-internal-key"));
    }

    @Test void privacyIsRequiredBeforeSendingAnyImage() {
        error("PRIVACY_REQUIRED", HttpStatus.BAD_REQUEST, () -> service.read(png(), false));
        server.verify();
    }

    @Test void missingAndEmptyImagesAreRejected() {
        error("IMAGE_REQUIRED", HttpStatus.BAD_REQUEST, () -> service.read(null, true));
        error("IMAGE_REQUIRED", HttpStatus.BAD_REQUEST, () -> service.read(
                new MockMultipartFile("file", new byte[0]), true));
        server.verify();
    }

    @Test void oversizedImageIsRejectedBeforeCloudCall() {
        MockMultipartFile file = new MockMultipartFile("file", new byte[(int) MathTutorService.MAX_IMAGE_BYTES + 1]);
        error("IMAGE_TOO_LARGE", HttpStatus.PAYLOAD_TOO_LARGE, () -> service.read(file, true));
        server.verify();
    }

    @Test void claimedImageMimeDoesNotAllowTextUploads() {
        MockMultipartFile file = new MockMultipartFile("file", "page.png", "image/png", "not an image".getBytes());
        error("IMAGE_UNSUPPORTED", HttpStatus.UNPROCESSABLE_ENTITY, () -> service.read(file, true));
        server.verify();
    }

    @Test void detectedImageTypeOverridesClaimedFilenameAndMime() throws Exception {
        server.expect(requestTo(URL + "/internal/v1/tutor/read"))
                .andExpect(header("X-Internal-API-Key", "test-only-internal-key"))
                .andExpect(header("Content-Type", "image/png"))
                .andExpect(content().bytes(png().getBytes()))
                .andRespond(withSuccess(READ, MediaType.APPLICATION_JSON));
        assertTrue(service.read(png(), true).needsReview());
        server.verify();
    }

    @Test void jpegAndWebpAreSupported() {
        server.expect(requestTo(URL + "/internal/v1/tutor/read"))
                .andExpect(header("Content-Type", "image/jpeg"))
                .andRespond(withSuccess(READ, MediaType.APPLICATION_JSON));
        server.expect(requestTo(URL + "/internal/v1/tutor/read"))
                .andExpect(header("Content-Type", "image/webp"))
                .andRespond(withSuccess(READ, MediaType.APPLICATION_JSON));
        service.read(new MockMultipartFile("file", new byte[]{(byte) 255, (byte) 216, (byte) 255, 0}), true);
        service.read(new MockMultipartFile("file", "RIFF0000WEBP".getBytes(StandardCharsets.US_ASCII)), true);
        server.verify();
    }

    @Test void notebookInspectionPreservesBoundedRowsAndPrivacy() {
        error("PRIVACY_REQUIRED", HttpStatus.BAD_REQUEST, () -> service.inspect(png(), false));
        server.expect(requestTo(URL + "/internal/v1/tutor/inspect"))
                .andExpect(header("X-Internal-API-Key", "test-only-internal-key"))
                .andExpect(content().bytes(assertDoesNotThrow(() -> png().getBytes())))
                .andRespond(withSuccess(INSPECT, MediaType.APPLICATION_JSON));
        NotebookRead result = service.inspect(png(), true);
        assertEquals("WORK", result.kind());
        assertEquals(java.util.List.of(120, 300, 700, 410), result.lines().getFirst().box());
        assertTrue(result.needsProblem());
        assertFalse(result.needsCrop()); // Older runtimes omitted this optional flag.
        server.verify();
    }

    @Test void notebookInspectionForwardsExplicitCropRequirementWithoutPartialText() {
        String response = "{\"kind\":\"UNREADABLE\",\"problemText\":\"\",\"needsProblem\":false,\"needsCrop\":true,\"lines\":[]}";
        server.expect(requestTo(URL + "/internal/v1/tutor/inspect"))
                .andRespond(withSuccess(response, MediaType.APPLICATION_JSON));
        NotebookRead result = service.inspect(png(), true);
        assertTrue(result.needsCrop());
        assertEquals("UNREADABLE", result.kind());
        assertTrue(result.problemText().isEmpty());
        assertTrue(result.lines().isEmpty());
        server.verify();
    }

    @ParameterizedTest @ValueSource(strings = {"\"true\"", "null", "1", "[]"})
    void notebookInspectionRequiresAnActualBooleanCropFlag(String value) {
        server.expect(requestTo(URL + "/internal/v1/tutor/inspect"))
                .andRespond(withSuccess(INSPECT.replace("\"needsProblem\":true",
                        "\"needsProblem\":true,\"needsCrop\":" + value), MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE, () -> service.inspect(png(), true));
        server.verify();
    }

    @ParameterizedTest @ValueSource(booleans = {true, false})
    void notebookInspectionRejectsCropFlagWithPartialTranscript(boolean whitespaceOnly) {
        String response = whitespaceOnly
                ? "{\"kind\":\"UNREADABLE\",\"problemText\":\" \",\"needsProblem\":false,\"needsCrop\":true,\"lines\":[]}"
                : INSPECT.replace("\"needsProblem\":true", "\"needsProblem\":true,\"needsCrop\":true");
        server.expect(requestTo(URL + "/internal/v1/tutor/inspect"))
                .andRespond(withSuccess(response, MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE, () -> service.inspect(png(), true));
        server.verify();
    }

    @Test void notebookInspectionRejectsMalformedGeometry() {
        server.expect(requestTo(URL + "/internal/v1/tutor/inspect"))
                .andRespond(withSuccess(INSPECT.replace("[120,300,700,410]", "[700,300,120,410]"), MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE, () -> service.inspect(png(), true));
        server.verify();
    }

    @Test void coachForwardsOnlyASelectedStepFromTheWork() {
        CoachRequest request = new CoachRequest("", "2 + 5 = 7\n49 : 7 × 2 = 14", "CHECK_WORK",
                "Em chia trước.", "49 : 7 × 2 = 14", 0, "");
        server.expect(requestTo(URL + "/internal/v1/tutor/coach"))
                .andExpect(jsonPath("$.focusText").value("49 : 7 × 2 = 14"))
                .andRespond(withSuccess(GUIDE.replace("PLAN", "CHECK_WORK"), MediaType.APPLICATION_JSON));
        assertEquals("CHECK_WORK", service.coach(request).stage());
        server.verify();
    }

    @Test void coachRejectsFocusThatIsNotInThePhotographedWork() {
        CoachRequest request = new CoachRequest("", "2 + 5 = 7", "CHECK_WORK", "", "49 : 7", 0, "");
        error("TUTOR_INPUT_INVALID", HttpStatus.BAD_REQUEST, () -> service.coach(request));
        server.verify();
    }

    @Test void blankReadingRequiresReview() {
        server.expect(requestTo(URL + "/internal/v1/tutor/read"))
                .andRespond(withSuccess("{\"problemText\":\"\",\"needsReview\":true,\"notes\":\"Em nhập lại đề nhé.\"}", MediaType.APPLICATION_JSON));
        assertTrue(service.read(png(), true).problemText().isEmpty());
        server.verify();
    }

    @ParameterizedTest @ValueSource(strings = {
            "{}", "[]", "null", "not-json",
            "{\"problemText\":\"\",\"needsReview\":false,\"notes\":\"\"}",
            "{\"problemText\":\"Đề\",\"needsReview\":\"true\",\"notes\":\"\"}",
            "{\"problemText\":42,\"needsReview\":true,\"notes\":\"\"}"})
    void malformedReadResponsesNeverBecomeSuccess(String body) {
        server.expect(requestTo(URL + "/internal/v1/tutor/read"))
                .andRespond(withSuccess(body, MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE, () -> service.read(png(), true));
        server.verify();
    }

    @Test void readingRejectsNotesAboveThePublicLimit() {
        server.expect(requestTo(URL + "/internal/v1/tutor/read"))
                .andRespond(withSuccess(READ.replace("Em hãy kiểm tra lại đề nhé.", "a".repeat(501)), MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE, () -> service.read(png(), true));
        server.verify();
    }

    @Test void guideIsForwardedOnlyAfterConfirmationWithOptionalStringsNormalized() {
        server.expect(requestTo(URL + "/internal/v1/tutor/guide"))
                .andExpect(header("X-Internal-API-Key", "test-only-internal-key"))
                .andExpect(jsonPath("$.problemConfirmed").value(true))
                .andExpect(jsonPath("$.previousHint").value(""))
                .andRespond(withSuccess(GUIDE, MediaType.APPLICATION_JSON));
        GuideResponse response = service.guide(request());
        assertEquals("PLAN", response.stage());
        assertFalse(response.guarded());
        server.verify();
    }

    @Test void guideRejectsUnconfirmedProblemAndCheckWithoutStudentWork() {
        error("PROBLEM_CONFIRMATION_REQUIRED", HttpStatus.BAD_REQUEST, () -> service.guide(
                new GuideRequest("Đề toán", false, "PLAN", "", 0, "")));
        error("STUDENT_ATTEMPT_REQUIRED", HttpStatus.BAD_REQUEST, () -> service.guide(
                new GuideRequest("Đề toán", true, "CHECK_WORK", "  ", 0, "")));
        server.verify();
    }

    @Test void trimmedProblemMustHaveAtLeastThreeCharacters() {
        error("TUTOR_INPUT_INVALID", HttpStatus.BAD_REQUEST, () -> service.guide(
                new GuideRequest("  a  ", true, "PLAN", "", 0, "")));
        error("TUTOR_INPUT_INVALID", HttpStatus.BAD_REQUEST, () -> service.guide(
                new GuideRequest(null, true, "PLAN", "", 0, "")));
        server.verify();
    }

    @ParameterizedTest @ValueSource(strings = {
            "{\"stage\":\"NEXT_STEP\",\"hint\":\"Gợi ý\",\"question\":\"Em thử nhé?\",\"feedback\":\"\",\"guarded\":false}",
            "{\"stage\":\"PLAN\",\"hint\":\"\",\"question\":\"Em thử nhé?\",\"feedback\":\"\",\"guarded\":false}",
            "{\"stage\":\"PLAN\",\"hint\":\"Gợi ý\",\"question\":\"\",\"feedback\":\"\",\"guarded\":false}",
            "{\"stage\":\"PLAN\",\"hint\":\"Gợi ý\",\"question\":\"Em thử nhé?\",\"feedback\":\"\",\"guarded\":\"false\"}"})
    void guideRejectsChangedStageAndInvalidFieldTypes(String body) {
        server.expect(requestTo(URL + "/internal/v1/tutor/guide"))
                .andRespond(withSuccess(body, MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE, () -> service.guide(request()));
        server.verify();
    }

    @Test void guideRejectsOverlongGeneratedHints() {
        server.expect(requestTo(URL + "/internal/v1/tutor/guide"))
                .andRespond(withSuccess(GUIDE.replace("Khi cho bớt bút, số bút giảm đi.", "a".repeat(801)), MediaType.APPLICATION_JSON));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE, () -> service.guide(request()));
        server.verify();
    }

    @ParameterizedTest @ValueSource(ints = {401, 403, 429, 500, 503})
    void cloudFailuresHaveSafeUnavailableErrors(int status) {
        server.expect(requestTo(URL + "/internal/v1/tutor/guide"))
                .andRespond(withStatus(HttpStatus.valueOf(status)).body("provider secret at " + URL));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE, () -> service.guide(request()));
        server.verify();
    }

    @ParameterizedTest @ValueSource(ints = {400, 422})
    void upstreamValidationStatusIsPreservedWithoutInternalDetails(int status) {
        server.expect(requestTo(URL + "/internal/v1/tutor/read"))
                .andRespond(withStatus(HttpStatus.valueOf(status)).body("internal error " + URL));
        error("TUTOR_INPUT_INVALID", HttpStatus.valueOf(status), () -> service.read(png(), true));
        server.verify();
    }

    @Test void timeoutAndMissingConfigurationAreUnavailable() {
        server.expect(requestTo(URL + "/internal/v1/tutor/guide"))
                .andRespond(withException(new SocketTimeoutException("secret backend URL")));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE, () -> service.guide(request()));
        error("TUTOR_UNAVAILABLE", HttpStatus.SERVICE_UNAVAILABLE,
                () -> new MathTutorService(new RestTemplate(), URL, "").guide(request()));
        server.verify();
    }
}

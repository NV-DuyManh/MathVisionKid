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

    @BeforeEach void setUp() {
        RestTemplate http = new RestTemplate();
        server = MockRestServiceServer.bindTo(http).build();
        service = new MathTutorService(http, URL + "/", "test-only-internal-key");
    }

    private static MockMultipartFile png() {
        return new MockMultipartFile("file", "page.jpg", "image/jpeg",
                new byte[]{(byte) 0x89, 'P', 'N', 'G', 13, 10, 26, 10, 1});
    }

    private static GuideRequest request() {
        return new GuideRequest("Lan có 12 bút, cho bạn 3 bút. Hỏi còn bao nhiêu bút?", true, "PLAN", "", 0, null);
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

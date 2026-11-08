package com.mathvisionkids.api.quiz;

import com.fasterxml.jackson.databind.JsonNode;
import com.mathvisionkids.api.user.StudentRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.*;
import java.security.SecureRandom;
import java.time.Duration;
import java.util.*;

/** Related practice uses the same private verification boundary as the lesson. */
@Service
class QuizGenerator {
    static final String ADAPTIVE = "CHECKED_LESSON_VARIANT";
    static final String REVIEW = "CHECKED_SOURCE_REVIEW";
    static final String CHOICE_SKILL = "APPLY_CHECKED_LESSON_CHOICE";
    private final StudentRepository students;
    private final RestTemplate http;
    private final String baseUrl, key;
    private final boolean adaptiveEnabled;

    QuizGenerator(StudentRepository students, RestTemplateBuilder builder,
                  @Value("${ai.service.base-url}") String baseUrl, @Value("${ai.callback.api-key}") String key,
                  @Value("${ai.quiz.adaptive-enabled:true}") boolean adaptiveEnabled) {
        this.students = students;
        this.http = builder.setConnectTimeout(Duration.ofSeconds(3)).setReadTimeout(Duration.ofSeconds(55)).build();
        this.baseUrl = baseUrl.replaceAll("/+$", ""); this.key = key; this.adaptiveEnabled = adaptiveEnabled;
    }

    QuizMath.Verified generate(UUID student, String confirmedProblem) {
        return generate(student, confirmedProblem, Set.of());
    }

    QuizMath.Verified generate(UUID student, String confirmedProblem, Set<String> excludedAnswers) {
        var exact = QuizMath.analyzeConfirmed(confirmedProblem);
        if (exact.isPresent()) return QuizMath.generate(exact.get(), new SecureRandom(), excludedAnswers);
        if (!adaptiveEnabled) throw new QuizMath.UnsupportedProblem();
        var owner = students.findById(student).orElseThrow();
        var headers = new HttpHeaders(); headers.setContentType(MediaType.APPLICATION_JSON); headers.set("X-Internal-API-Key", key);
        try {
            var body = http.postForObject(baseUrl + "/internal/v1/tutor/quiz/variant", new HttpEntity<>(Map.of(
                    "owner", owner.getEmail(), "problemText", confirmedProblem,
                    "sourceFingerprint", QuizSources.fingerprint(confirmedProblem),
                    "excludedAnswers", excludedAnswers.stream().limit(200).toList()), headers), JsonNode.class);
            if (body == null || !QuizSources.fingerprint(confirmedProblem).equals(body.path("sourceFingerprint").asText())
                    || !"TUTOR_VERIFIED".equals(body.path("verification").asText()) || !body.path("review").isBoolean()) throw new IllegalArgumentException();
            var result = new QuizMath.Verified(body.path("review").asBoolean() ? REVIEW : ADAPTIVE,
                    body.path("review").asBoolean() ? "Ôn lại bài vừa học" : body.path("topic").asText(),
                    "CHOICE".equals(body.path("answerFormat").asText()) ? CHOICE_SKILL : "APPLY_CHECKED_LESSON_METHOD", owner.getGradeLevel() == null ? 4 : owner.getGradeLevel(),
                    body.path("questionText").asText(), body.path("unit").asText(), Rational.parse(body.path("answer").asText()),
                    body.path("solution").asText(), List.of(body.path("sourceFingerprint").asText(), "TUTOR_VERIFIED"));
            validateStored(result, confirmedProblem);
            if (ADAPTIVE.equals(result.code()) && excludedAnswers.contains(result.answer().toString())) throw new IllegalArgumentException();
            return result;
        } catch (HttpStatusCodeException ex) {
            if (ex.getStatusCode().value() == 422) throw new QuizMath.UnsupportedProblem();
            throw unavailable();
        } catch (RestClientException | IllegalArgumentException ex) { throw unavailable(); }
    }

    static boolean isAdaptive(String code) { return ADAPTIVE.equals(code) || REVIEW.equals(code); }

    static void validateStored(QuizMath.Verified draft, String source) {
        if (!isAdaptive(draft.code()) || draft.data() == null || draft.data().size() != 2
                || !QuizSources.fingerprint(source).equals(draft.data().getFirst()) || !"TUTOR_VERIFIED".equals(draft.data().get(1))
                || draft.question().isBlank() || draft.question().length() > 4000 || draft.question().contains("[?]")
                || draft.solution().isBlank() || draft.solution().length() > 16000 || draft.unit().length() > 30
                || draft.name().isBlank() || draft.name().length() > 120 || draft.grade() < 1 || draft.grade() > 5
                || draft.answer().numerator().abs().compareTo(java.math.BigInteger.TEN.pow(12)) > 0) throw new IllegalArgumentException("Invalid private Quiz draft");
        if (CHOICE_SKILL.equals(draft.skill())) {
            var matches = java.util.regex.Pattern.compile("(?m)^([A-D])\\. (.+)$").matcher(draft.question());
            int count = 0;
            while (matches.find()) {
                if (matches.group(1).charAt(0) != 'A' + count++) throw new IllegalArgumentException("Invalid checked choices");
            }
            if (count < 2 || count > 4 || !draft.answer().integer() || draft.answer().numerator().intValueExact() < 1
                    || draft.answer().numerator().intValueExact() > count) throw new IllegalArgumentException("Invalid checked choices");
        }
    }

    private static RuntimeException unavailable() {
        return QuizService.error("QUIZ_GENERATING", "Sao đang chuẩn bị câu luyện tập theo bài vừa học. Em chờ một chút nhé.", HttpStatus.CONFLICT);
    }
}

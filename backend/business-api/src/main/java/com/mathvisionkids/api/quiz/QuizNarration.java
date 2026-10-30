package com.mathvisionkids.api.quiz;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.*;
import java.time.Duration;
import java.util.*;

@Service
class QuizNarration {
    private final QuizService quizzes;
    private final RestTemplate http;
    private final String baseUrl, key;
    QuizNarration(QuizService quizzes, RestTemplateBuilder builder, @Value("${ai.service.base-url}") String baseUrl,
                  @Value("${ai.callback.api-key}") String key) {
        this.quizzes=quizzes; this.http=builder.setConnectTimeout(Duration.ofSeconds(5)).setReadTimeout(Duration.ofSeconds(40)).build();
        this.baseUrl=baseUrl.replaceAll("/+$", ""); this.key=key;
    }
    byte[] narrate(String principal, UUID id, String voice) {
        String text=quizzes.authorizedSolution(principal,id); // Always recheck ownership/unlock, even for cached audio.
        if (baseUrl.isBlank() || key.isBlank()) throw unavailable();
        var headers=new HttpHeaders(); headers.setContentType(MediaType.APPLICATION_JSON); headers.set("X-Internal-API-Key",key);
        headers.setAccept(List.of(MediaType.parseMediaType("audio/wav")));
        try {
            var response=http.postForEntity(baseUrl+"/internal/v1/tutor/quiz/narration",new HttpEntity<>(Map.of("owner",principal,"quizId",id.toString(),"text",text,"voice",voice),headers),byte[].class);
            byte[] bytes=response.getBody();
            if (bytes==null || bytes.length<=44 || bytes.length>8*1024*1024 || response.getHeaders().getContentType()==null
                    || !MediaType.parseMediaType("audio/wav").isCompatibleWith(response.getHeaders().getContentType())
                    || bytes[0]!='R' || bytes[1]!='I' || bytes[2]!='F' || bytes[3]!='F' || bytes[8]!='W' || bytes[9]!='A' || bytes[10]!='V' || bytes[11]!='E') throw unavailable();
            return bytes;
        } catch (HttpStatusCodeException ex) {
            if (ex.getStatusCode().value()==429) throw QuizService.error("QUIZ_AUDIO_BUSY","Giọng đọc đang bận. Em thử lại sau nhé.",HttpStatus.TOO_MANY_REQUESTS);
            throw unavailable();
        } catch (RestClientException ex) { throw unavailable(); }
    }
    private static RuntimeException unavailable() { return QuizService.error("QUIZ_AUDIO_UNAVAILABLE","Chưa nghe được lúc này. Em vẫn có thể đọc cách giải nhé.",HttpStatus.SERVICE_UNAVAILABLE); }
}

package com.mathvisionkids.api.quiz;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import org.junit.jupiter.api.Test;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.MediaType;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.client.MockRestServiceServer;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;

class QuizGeneratorTest {
    @Test void checkedTextChoicesKeepTheirAnswerKindThroughStorage() {
        String source = "Sắp xếp các số thập phân 1,25; 0,98; 3,56; 2,014 theo thứ tự từ bé đến lớn.";
        var draft = new QuizMath.Verified(QuizGenerator.ADAPTIVE, "Sắp xếp số", QuizGenerator.CHOICE_SKILL, 5,
                "Sắp xếp số mới\nA. 1; 2; 3; 4\nB. 4; 3; 2; 1", "", Rational.of(1),
                "So sánh từng cặp. Dãy tăng dần là 1; 2; 3; 4.", List.of(QuizSources.fingerprint(source), "TUTOR_VERIFIED"));
        QuizGenerator.validateStored(draft, source);
        var invalid = new QuizMath.Verified(draft.code(), draft.name(), draft.skill(), 5, draft.question(), "", Rational.of(5), draft.solution(), draft.data());
        assertThrows(IllegalArgumentException.class, () -> QuizGenerator.validateStored(invalid, source));
    }
    @Test void adaptiveDraftIsBoundToTheActualOwnerAndConfirmedSource() throws Exception {
        var student = new Student(); student.setEmail("quiz-fixture@test.invalid"); student.setGradeLevel(5);
        var students = mock(StudentRepository.class);
        UUID id = UUID.randomUUID(); when(students.findById(id)).thenReturn(Optional.of(student));
        var generator = new QuizGenerator(students,new RestTemplateBuilder(),"http://quiz-fixture","test-key",true);
        var http = (org.springframework.web.client.RestTemplate) ReflectionTestUtils.getField(generator,"http");
        var remote = MockRestServiceServer.bindTo(http).build();
        String source = "Điền vào chỗ chấm để 1,7 km² = ... ha";
        var response = Map.of("sourceFingerprint",QuizSources.fingerprint(source),"verification","TUTOR_VERIFIED",
                "review",false,"topic","Đổi đơn vị đo","questionText","Điền vào chỗ chấm để 2,7 km² = ... ha",
                "answer","270","unit","ha","solution","2,7 × 100 = 270 ha");
        remote.expect(requestTo("http://quiz-fixture/internal/v1/tutor/quiz/variant"))
                .andExpect(header("X-Internal-API-Key","test-key"))
                .andExpect(jsonPath("$.owner").value(student.getEmail()))
                .andExpect(jsonPath("$.problemText").value(source))
                .andRespond(withSuccess(new ObjectMapper().writeValueAsString(response),MediaType.APPLICATION_JSON));
        var result=generator.generate(id,source);
        assertEquals(QuizGenerator.ADAPTIVE,result.code());
        assertEquals(Rational.of(270),result.answer());
        QuizGenerator.validateStored(result,source);
        assertThrows(IllegalArgumentException.class,() -> QuizGenerator.validateStored(result,"Đề khác"));
        remote.verify();
        remote.reset();
        var mismatched = new HashMap<>(response);
        mismatched.put("sourceFingerprint","another-source");
        remote.expect(requestTo("http://quiz-fixture/internal/v1/tutor/quiz/variant"))
                .andRespond(withSuccess(new ObjectMapper().writeValueAsString(mismatched),MediaType.APPLICATION_JSON));
        assertEquals("QUIZ_GENERATING",assertThrows(ApiException.class,() -> generator.generate(id,source)).getCode());
    }

    @Test void exactSupportedProblemsDoNotDependOnAnExternalService() {
        var students=mock(StudentRepository.class);
        var generator=new QuizGenerator(students,new RestTemplateBuilder(),"http://unused","unused",true);
        assertEquals(QuizMath.CLASS_COMPLEMENT,generator.generate(UUID.randomUUID(),QuizMathTest.CLASS_EXAM).code());
        verifyNoInteractions(students);
    }
}

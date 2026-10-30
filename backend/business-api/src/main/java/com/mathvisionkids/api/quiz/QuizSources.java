package com.mathvisionkids.api.quiz;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import jakarta.persistence.*;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;

@Service
public class QuizSources {
    private final QuizSourceRepository sources;
    private final StudentRepository students;
    private final EntityManager em;
    private final QuizPreparationRepository preparations;
    public QuizSources(QuizSourceRepository sources, StudentRepository students, EntityManager em, QuizPreparationRepository preparations) {
        this.sources=sources; this.students=students; this.em=em; this.preparations=preparations;
    }
    UUID student(String principal) {
        var student = students.findByEmail(principal).filter(s -> "STUDENT".equals(s.getRole()) && Boolean.TRUE.equals(s.getActive()))
                .orElseThrow(() -> new ApiException("STUDENT_REQUIRED", "Em đăng nhập tài khoản học sinh nhé.", HttpStatus.FORBIDDEN));
        return student.getId();
    }
    void lockStudent(UUID id) { em.find(Student.class, id, LockModeType.PESSIMISTIC_WRITE); }
    Integer grade(UUID id) { return students.findById(id).map(Student::getGradeLevel).orElse(null); }
    static String fingerprint(String text) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(text.strip().replaceAll("\\s+", " ").getBytes(StandardCharsets.UTF_8))); }
        catch (NoSuchAlgorithmException ex) { throw new IllegalStateException(ex); }
    }
    @Transactional
    public void record(String principal, String type, String sourceId, String problem, boolean completed) {
        if (problem == null || problem.contains("[?]")) return;
        UUID student = student(principal); lockStudent(student);
        var existing = sources.findByStudentIdAndSourceTypeAndSourceId(student, type, sourceId);
        if (existing.isPresent()) {
            var value = existing.get();
            if (value.fingerprint.equals(fingerprint(problem))) {
                value.completed |= completed;
                if (value.preparationId==null) preparations.findFirstByStudentIdAndFingerprintOrderByUpdatedAtDesc(student,value.fingerprint).ifPresent(p -> value.preparationId=p.id);
            }
            return;
        }
        var value = new QuizSource(); value.studentId=student; value.sourceType=type; value.sourceId=sourceId;
        preparations.findFirstByStudentIdAndFingerprintOrderByUpdatedAtDesc(student,fingerprint(problem)).ifPresent(p -> value.preparationId=p.id);
        value.problemText=problem; value.fingerprint=fingerprint(problem); value.completed=completed; sources.save(value);
    }
    @Transactional
    public void complete(String principal, String sessionId) {
        UUID student = student(principal); lockStudent(student);
        sources.findByStudentIdAndSourceTypeAndSourceId(student,"LESSON",sessionId).ifPresent(source -> source.completed=true);
    }
    /** Quiz storage outages must not discard a successful Tutor response. Failure leaves Quiz unavailable, never forged. */
    public void warnUnavailable() { LoggerFactory.getLogger(QuizSources.class).warn("Quiz source persistence unavailable; Tutor response preserved"); }
}

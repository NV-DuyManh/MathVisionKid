package com.mathvisionkids.api.quiz;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.http.HttpStatus;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.*;
import static com.mathvisionkids.api.quiz.QuizDtos.*;
import static com.mathvisionkids.api.quiz.QuizService.error;

@Service
class QuizPreparations {
    private final QuizPreparationRepository rows;
    private final QuizSources identities;
    private final ObjectMapper json;
    private final QuizRepository quizzes;
    private final org.springframework.context.ApplicationEventPublisher events;
    QuizPreparations(QuizPreparationRepository rows,QuizSources identities,ObjectMapper json,QuizRepository quizzes,org.springframework.context.ApplicationEventPublisher events) {
        this.rows=rows; this.identities=identities; this.json=json; this.quizzes=quizzes; this.events=events;
    }
    @Transactional
    public Preparation prepare(String principal,Prepare request) {
        if(request.problemConfirmed() && (request.problemText()==null || request.problemText().strip().length()<3))
            throw error("QUIZ_INPUT_INVALID","Em kiểm tra đầy đủ đề bài trước nhé.",HttpStatus.BAD_REQUEST);
        UUID student=identities.student(principal); identities.lockStudent(student);
        var row=rows.findByStudentIdAndWorkflowKey(student,request.workflowKey()).orElseGet(() -> {
            var value=new QuizPreparation(); value.studentId=student; value.workflowKey=request.workflowKey(); value.revision=-1; return value;
        });
        String fingerprint=request.problemConfirmed() ? QuizSources.fingerprint(request.problemText()) : null;
        if (request.revision()<row.revision) return view(row);
        if (request.revision()==row.revision) {
            if (!request.problemConfirmed() && "INVALIDATED".equals(row.status)) return view(row);
            if (!Objects.equals(fingerprint,row.fingerprint)) throw error("QUIZ_REVISION_CONFLICT","Đề đã thay đổi. Em xác nhận lại đề mới nhé.",HttpStatus.CONFLICT);
            if (!"FAILED".equals(row.status) && QuizMath.VERSION.equals(row.generatorVersion)) return view(row);
        }
        if (!request.problemConfirmed() || !Objects.equals(row.fingerprint,fingerprint)) quizzes.invalidatePreparation(student,row.id);
        row.revision=request.revision(); row.updatedAt=Instant.now(); row.validatedDraft=null; row.errorCode=null;
        row.problemConfirmed=request.problemConfirmed();
        if(request.problemConfirmed()) row.confirmedProblemText=request.problemText();
        row.generatorVersion=QuizMath.VERSION; row.generatedAt=null; row.durationMs=null;
        if (!request.problemConfirmed()) {
            // Keep the old fingerprint as a tombstone so late completion cannot resurrect the old draft.
            row.status="INVALIDATED";
        } else {
            row.fingerprint=fingerprint;
            if(request.problemText()==null || request.problemText().strip().length()<3 || request.problemText().contains("[?]")) {
                row.status="UNSUPPORTED"; row.errorCode="QUIZ_UNSUPPORTED";
            } else row.status="GENERATING";
        }
        rows.saveAndFlush(row);
        if("GENERATING".equals(row.status)) events.publishEvent(new QuizGenerationWorker.Requested(row.id,row.revision));
        org.slf4j.LoggerFactory.getLogger(QuizPreparations.class).info("quiz_confirmed preparation={} revision={} fingerprint={} confirmed={} chars={} state={} version={}",row.id,row.revision,row.fingerprint,row.problemConfirmed,row.confirmedProblemText==null?0:row.confirmedProblemText.length(),row.status,QuizMath.VERSION);
        return view(row);
    }
    @Transactional(readOnly=true)
    public Preparation status(String principal,UUID id) {
        return view(rows.findByIdAndStudentId(id,identities.student(principal)).orElseThrow(() -> error("QUIZ_NOT_FOUND","Không tìm thấy câu đố của em.",HttpStatus.NOT_FOUND)));
    }
    QuizMath.Verified forSource(QuizSource source) {
        var preparation=source.preparationId==null
                ? rows.findFirstByStudentIdAndFingerprintOrderByUpdatedAtDesc(source.studentId,source.fingerprint)
                : rows.findByIdAndStudentId(source.preparationId,source.studentId);
        if (preparation.isEmpty()) return null; // Older clients retain the verified lazy-generation path.
        var row=preparation.get();
        if (!Objects.equals(row.fingerprint,source.fingerprint) || "INVALIDATED".equals(row.status))
            throw error("QUIZ_SOURCE_CHANGED","Đề đã được sửa. Em hoàn tất phần học theo đề mới để nhận Quiz nhé.",HttpStatus.CONFLICT);
        // The confirmation request may arrive after Tutor records its source.
        // Bind here too so a later edit always invalidates the correct published Quiz.
        if(source.preparationId==null) source.preparationId=row.id;
        // Upgrade old private drafts from the full immutable source, without rewriting history.
        if(!QuizMath.VERSION.equals(row.generatorVersion)) return null;
        if("GENERATING".equals(row.status)) throw error("QUIZ_GENERATING","Sao đang chuẩn bị câu đố. Em chờ một chút nhé.",HttpStatus.CONFLICT);
        if("UNSUPPORTED".equals(row.status)) throw error("QUIZ_UNSUPPORTED","Sao chưa kiểm chứng được quan hệ toán trong đề này. Em vẫn có thể lưu bài học nhé.",HttpStatus.UNPROCESSABLE_ENTITY);
        // Finish/retry may recover a failed background attempt using the same deterministic validator.
        if ("FAILED".equals(row.status)) return null;
        if (!"READY".equals(row.status)) return null;
        try { return decode(row); }
        catch (JsonProcessingException | IllegalArgumentException ex) { throw error("QUIZ_GENERATION_FAILED","Chưa mở được câu đố. Em thử chuẩn bị lại nhé.",HttpStatus.SERVICE_UNAVAILABLE); }
    }
    private QuizMath.Verified decode(QuizPreparation row) throws JsonProcessingException {
        var draft=json.readValue(row.validatedDraft,QuizMath.Verified.class);
        var checked=QuizMath.classify(draft.question(),true).orElseThrow(IllegalArgumentException::new);
        if (!checked.answer().equals(draft.answer()) || !checked.code().equals(draft.code()) || !checked.solution().equals(draft.solution())) throw new IllegalArgumentException();
        return checked;
    }
    private Preparation view(QuizPreparation row) { return new Preparation(row.id,row.revision,row.status,row.errorCode); }
}

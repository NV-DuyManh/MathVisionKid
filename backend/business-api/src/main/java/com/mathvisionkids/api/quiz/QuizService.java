package com.mathvisionkids.api.quiz;

import com.mathvisionkids.api.common.ApiException;
import org.springframework.data.domain.*;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.security.SecureRandom;
import java.time.*;
import java.util.*;
import static com.mathvisionkids.api.quiz.QuizDtos.*;

@Service
public class QuizService {
    private final QuizRepository quizzes;
    private final QuizSourceRepository sources;
    private final QuizAttemptRepository attempts;
    private final QuizSources identities;
    private final Clock clock;
    private final QuizPreparations preparations;
    @org.springframework.beans.factory.annotation.Autowired
    public QuizService(QuizRepository quizzes, QuizSourceRepository sources, QuizAttemptRepository attempts, QuizSources identities, QuizPreparations preparations) {
        this(quizzes,sources,attempts,identities,preparations,Clock.systemUTC());
    }
    QuizService(QuizRepository quizzes, QuizSourceRepository sources, QuizAttemptRepository attempts, QuizSources identities, QuizPreparations preparations, Clock clock) {
        this.quizzes=quizzes; this.sources=sources; this.attempts=attempts; this.identities=identities; this.preparations=preparations; this.clock=clock;
    }
    private Instant now() { return clock.instant().truncatedTo(java.time.temporal.ChronoUnit.MICROS); }
    @Transactional
    public Invitation fromLearning(String principal, FromLearning request) {
        UUID student=identities.student(principal); identities.lockStudent(student);
        var source=sources.findByStudentIdAndSourceTypeAndSourceId(student,request.sourceType(),request.sourceId()).filter(s -> s.completed)
                .orElseThrow(() -> error("QUIZ_SOURCE_NOT_COMPLETE", "Bài học chưa được xác nhận hoàn tất. Em có thể quay lại bài học hoặc trang chủ.", HttpStatus.CONFLICT));
        var previous=quizzes.findFirstByStudentIdAndSourceFingerprintOrderByCreatedAtAsc(student,source.fingerprint);
        if (previous.isPresent() && !"INVALIDATED".equals(previous.get().status)) return new Invitation(false, view(previous.get(),false));
        QuizMath.Verified prepared=preparations.forSource(source);
        if (previous.isPresent() && "INVALIDATED".equals(previous.get().status)) {
            if (prepared==null) throw error("QUIZ_SOURCE_CHANGED","Đề đã được sửa. Em xác nhận và hoàn tất phần học theo đề mới nhé.",HttpStatus.CONFLICT);
            // Returning to the same confirmed text may reuse unfinished work, never reset its timer/attempts.
            var q=quizzes.ownedForUpdate(previous.get().id,student).orElseThrow(QuizService::missing);
            if ("INVALIDATED".equals(q.status)) { q.status=q.startedAt==null ? "READY" : "IN_PROGRESS"; q.sourceType=source.sourceType; q.sourceId=source.sourceId; q.updatedAt=now(); }
        }
        if (previous.isPresent()) return new Invitation(false, view(previous.get(),false));
        // The trusted completed lesson supplies the difficulty. Profile grade is metadata,
        // not an access rule that can reject the very lesson this student just completed.
        QuizMath.Verified generated=prepared;
        try { if (generated==null) generated=QuizMath.generateFromConfirmed(source.problemText,new SecureRandom()); }
        catch (QuizMath.UnsupportedProblem ex) { throw error("QUIZ_UNSUPPORTED","Sao chưa kiểm chứng được quan hệ toán trong đề này. Em vẫn có thể lưu bài học nhé.",HttpStatus.UNPROCESSABLE_ENTITY); }
        catch (IllegalArgumentException ex) { throw error("QUIZ_GENERATION_FAILED","Chưa chuẩn bị được câu đố phù hợp. Em thử lại hoặc về trang chủ nhé.",HttpStatus.SERVICE_UNAVAILABLE); }
        var q=new Quiz(); q.studentId=student; q.sourceType=source.sourceType; q.sourceId=source.sourceId; q.sourceFingerprint=source.fingerprint;
        q.topicCode=generated.code(); q.topicName=generated.name(); q.skillCode=generated.skill(); q.gradeLevel=generated.grade();
        q.questionText=generated.question(); q.unit=generated.unit(); q.answerSpec=generated.answer().toString();
        q.validatedSolution=generated.solution(); q.createdAt=now(); q.updatedAt=q.createdAt;
        q.originalQuestionText=generated.question(); q.originalAnswerSpec=generated.answer().toString();
        q.originalValidatedSolution=generated.solution(); q.originalUnit=generated.unit();
        quizzes.saveAndFlush(q);
        org.slf4j.LoggerFactory.getLogger(QuizService.class).info("quiz_published quiz={} preparation={} source={} fingerprint={} state=READY version={}",q.id,source.preparationId,source.sourceId,source.fingerprint,QuizMath.VERSION);
        return new Invitation(true,view(q,false));
    }
    @Transactional(readOnly=true)
    public Library list(String principal, String group, int page, int size) {
        if (page<0 || size<1 || size>50 || !List.of("PENDING","IN_PROGRESS","COMPLETED").contains(group))
            throw error("QUIZ_INPUT_INVALID","Em chọn lại danh sách nhé.",HttpStatus.BAD_REQUEST);
        UUID student=identities.student(principal);
        Page<Quiz> result;
        var sort = Sort.by(Sort.Order.desc("createdAt"), Sort.Order.desc("id"));
        if ("PENDING".equals(group)) {
            result = quizzes.findPendingLibrary(student, List.of("READY", "DEFERRED"), PageRequest.of(page, size, sort));
        } else if ("IN_PROGRESS".equals(group)) {
            result = quizzes.findByStudentIdAndStatusIn(student, List.of("IN_PROGRESS"), PageRequest.of(page, size, sort));
        } else {
            result = quizzes.findCompletedLibrary(student, PageRequest.of(page, size, sort));
        }
        return new Library(result.stream().map(q -> view(q,false)).toList(),page,result.getTotalPages(),result.getTotalElements());
    }
    @Transactional(readOnly=true)
    public Counts counts(String principal) {
        UUID student=identities.student(principal);
        return new Counts(quizzes.countByStudentIdAndStatusIn(student,List.of("READY","DEFERRED","IN_PROGRESS")),quizzes.totalStars(student));
    }
    @Transactional(readOnly=true)
    public View get(String principal, UUID id) {
        return view(quizzes.findByIdAndStudentId(id,identities.student(principal)).filter(q -> !"INVALIDATED".equals(q.status)).orElseThrow(QuizService::missing),true);
    }
    @Transactional
    public View start(String principal, UUID id) {
        var q=locked(principal,id);
        if (!q.status.equals("COMPLETED")) {
            if (q.startedAt==null) q.startedAt=now();
            q.status="IN_PROGRESS"; q.updatedAt=now();
        }
        return view(q,true);
    }
    @Transactional
    public View replay(String principal, UUID id) {
        return replay(principal, id, "CHALLENGE");
    }
    @Transactional
    public View replay(String principal, UUID id, String requestedMode) {
        var q=locked(principal,id);
        if (!q.status.equals("COMPLETED") && q.firstCompletedAt == null)
            throw error("QUIZ_NOT_COMPLETED", "Quiz chưa hoàn thành, em hãy hoàn thành trước nhé.", HttpStatus.CONFLICT);
        String mode = requestedMode == null ? "CHALLENGE" : requestedMode.toUpperCase(Locale.ROOT);
        if ("REVIEW".equals(mode)) mode = "PRACTICE";
        if (!List.of("PRACTICE","CHALLENGE").contains(mode))
            throw error("QUIZ_INPUT_INVALID","Em chọn ôn lại bài cũ hoặc thử thách mới nhé.",HttpStatus.BAD_REQUEST);
        if ("IN_PROGRESS".equals(q.status) && q.replaying) {
            if (mode.equals(q.replayMode)) return view(q,true); // Network retry resumes the same timed run.
            throw error("QUIZ_REPLAY_ACTIVE","Em hoàn thành lượt đang làm trước khi chọn chế độ khác nhé.",HttpStatus.CONFLICT);
        }
        Instant now = now();
        if (q.firstCompletedAt == null) q.firstCompletedAt = q.completedAt != null ? q.completedAt : now;
        if ("PRACTICE".equals(mode)) {
            if (q.originalQuestionText != null) {
                q.questionText = q.originalQuestionText;
                q.answerSpec = q.originalAnswerSpec;
                q.validatedSolution = q.originalValidatedSolution;
                q.unit = q.originalUnit;
            }
            q.replayMode = "PRACTICE";
        } else {
            String base = q.originalQuestionText != null ? q.originalQuestionText : q.questionText;
            var source = QuizMath.analyzeConfirmed(base)
                    .or(() -> QuizMath.classify(base, true))
                    .orElseThrow(() -> error("QUIZ_VARIANT_UNSUPPORTED", "Dạng toán này chưa hỗ trợ tạo thử thách biến thể.", HttpStatus.UNPROCESSABLE_ENTITY));
            var seenAnswers = new HashSet<String>();
            seenAnswers.add(q.answerSpec);
            if (q.originalAnswerSpec != null) seenAnswers.add(q.originalAnswerSpec);
            attempts.findByQuizIdOrderByAttemptNumber(q.id).forEach(a -> {
                if (a.answerSpec != null) seenAnswers.add(a.answerSpec);
                else if (a.correct) {
                    // Pre-V23 history has no question/unit snapshot; accept only known unit suffixes.
                    for (String unit : List.of("","cây","quyển sách","viên kẹo","viên bi","bông hoa","quả bóng")) {
                        try { seenAnswers.add(QuizMath.answerInput(a.answer,unit).toString()); break; }
                        catch (IllegalArgumentException ex) { /* Try the next supported historical unit. */ }
                    }
                }
            });
            sources.findByStudentIdAndSourceTypeAndSourceId(q.studentId,q.sourceType,q.sourceId)
                .flatMap(s -> QuizMath.analyzeConfirmed(s.problemText)).ifPresent(s -> seenAnswers.add(s.answer().toString()));
            QuizMath.Verified variant;
            try { variant = QuizMath.generate(source, new SecureRandom(), seenAnswers); }
            catch (IllegalArgumentException ex) { throw error("QUIZ_VARIANTS_EXHAUSTED","Em đã khám phá hết biến thể hiện có. Em có thể ôn lại bài cũ nhé.",HttpStatus.CONFLICT); }
            q.questionText = variant.question();
            q.answerSpec = variant.answer().toString();
            q.validatedSolution = variant.solution();
            q.unit = variant.unit();
            q.replayMode = "CHALLENGE";
        }
        q.status = "IN_PROGRESS";
        q.replaying = true;
        q.startedAt = now;
        q.completedAt = null;
        q.solutionViewed = false;
        q.completedWithSolution = false;
        q.wrongAttempts = 0;
        q.lastSubmittedAt = null;
        q.updatedAt = now;
        quizzes.saveAndFlush(q);
        return view(q, true);
    }
    @Transactional
    public View defer(String principal, UUID id) {
        var q=locked(principal,id);
        if (!q.status.equals("COMPLETED")) { q.status=q.startedAt==null ? "DEFERRED" : "IN_PROGRESS"; q.updatedAt=now(); }
        // Time deliberately continues after the first start, including offline/background time.
        // Pausing cannot be used to solve off-clock and then claim three stars.
        return view(q,true);
    }
    @Transactional
    public Graded submit(String principal, UUID id, Submission request) {
        var q=locked(principal,id);
        var previous=attempts.findByQuizIdAndRequestId(id,request.requestId());
        if (previous.isPresent()) {
            if (!previous.get().answer.equals(request.answer().strip())) throw error("QUIZ_REQUEST_REUSED","Em gửi lại câu trả lời với lượt gửi mới nhé.",HttpStatus.CONFLICT);
            return new Graded(view(q,true),attempt(previous.get()));
        }
        if (!q.status.equals("IN_PROGRESS") || q.startedAt==null) throw error("QUIZ_NOT_ACTIVE","Em mở Quiz đang làm trước nhé.",HttpStatus.CONFLICT);
        Instant now=now();
        if (q.lastSubmittedAt!=null && Duration.between(q.lastSubmittedAt,now).toMillis()<800)
            throw error("QUIZ_TOO_FAST","Em chờ một chút rồi thử lại nhé.",HttpStatus.TOO_MANY_REQUESTS);
        Rational answer;
        try { answer=QuizMath.answerInput(request.answer(),q.unit); }
        catch (IllegalArgumentException ex) { throw error("QUIZ_ANSWER_INVALID","Em nhập một số, số thập phân hoặc phân số hợp lệ nhé.",HttpStatus.BAD_REQUEST); }
        var entry=new QuizAttempt(); entry.quizId=q.id; entry.requestId=request.requestId(); entry.answer=request.answer().strip();
        entry.attemptNumber=Math.toIntExact(attempts.countByQuizId(q.id))+1; entry.correct=answer.equals(Rational.parse(q.answerSpec));
        entry.submittedAt=now; entry.elapsedMillis=q.elapsedMillis(now); entry.replayMode=q.replayMode;
        entry.questionText=q.questionText; entry.answerSpec=q.answerSpec; entry.solutionViewed=q.solutionViewed; entry.runStartedAt=q.startedAt;
        if (entry.correct) {
            int earnedStars = "PRACTICE".equals(q.replayMode) ? 0 : stars(entry.elapsedMillis, q.solutionViewed);
            entry.stars = earnedStars;
            q.stars = Math.max(q.stars, earnedStars);
            q.status = "COMPLETED";
            q.replaying = false;
            q.completedAt = now;
            if (q.firstCompletedAt == null) q.firstCompletedAt = now;
            q.completedWithSolution = q.solutionViewed;
        } else {
            entry.stars = 0;
            q.wrongAttempts++;
        }
        attempts.saveAndFlush(entry); q.lastSubmittedAt=now; q.updatedAt=now;
        return new Graded(view(q,true),attempt(entry));
    }
    static int stars(long elapsedMillis, boolean viewed) { return viewed ? 0 : elapsedMillis<=30000 ? 3 : elapsedMillis<=60000 ? 2 : 1; }
    @Transactional
    public View reveal(String principal, UUID id) {
        var q=locked(principal,id);
        if (!q.status.equals("COMPLETED") && q.wrongAttempts<2) throw error("QUIZ_SOLUTION_LOCKED","Em thử tự giải thêm một lần nữa nhé.",HttpStatus.CONFLICT);
        // Completed independent work keeps its earned stars when reviewing the explanation.
        if (!q.status.equals("COMPLETED")) q.solutionViewed=true;
        q.updatedAt=now(); return view(q,true);
    }
    @Transactional(readOnly=true)
    public String authorizedSolution(String principal, UUID id) {
        var q=quizzes.findByIdAndStudentId(id,identities.student(principal)).filter(value -> !"INVALIDATED".equals(value.status)).orElseThrow(QuizService::missing);
        if (!q.solutionViewed && !q.status.equals("COMPLETED")) throw error("QUIZ_SOLUTION_LOCKED","Em mở Cách giải trước khi nghe nhé.",HttpStatus.CONFLICT);
        return q.validatedSolution;
    }
    private Quiz locked(String principal, UUID id) { return quizzes.ownedForUpdate(id,identities.student(principal)).filter(q -> !"INVALIDATED".equals(q.status)).orElseThrow(QuizService::missing); }
    private View view(Quiz q, boolean detail) {
        boolean published = q.solutionViewed || (q.status.equals("COMPLETED") && !q.replaying);
        return new View(q.id,q.sourceType,q.sourceId,q.topicCode,q.topicName,q.skillCode,q.gradeLevel,q.taxonomyVersion,
                q.verificationStatus,q.confidencePercent,q.startedAt == null ? "Một câu đố mới cùng dạng toán em vừa học. Bấm Bắt đầu để mở đề nhé." : q.questionText,
                q.unit,q.topicCode.equals("FRACTION_ADDITION_SUBTRACTION") ? "FRACTION" : "INTEGER",
                q.status,q.createdAt,q.startedAt,q.completedAt,now(),q.elapsedMillis(now()),q.stars,q.wrongAttempts,
                q.solutionViewed,q.completedWithSolution,q.wrongAttempts>=2 || (q.status.equals("COMPLETED") && !q.replaying),
                detail ? attempts.findByQuizIdOrderByAttemptNumber(q.id).stream().map(QuizService::attempt).toList() : List.of(),
                detail && published ? q.validatedSolution : null,detail && published ? q.answerSpec : null,
                q.replayMode, q.startedAt == null ? null : q.originalQuestionText != null ? q.originalQuestionText : q.questionText);
    }
    private static Attempt attempt(QuizAttempt a) { return new Attempt(a.attemptNumber,a.answer,a.correct,a.submittedAt,a.elapsedMillis,a.stars,a.replayMode,a.questionText,a.solutionViewed,a.runStartedAt); }
    private static ApiException missing() { return error("QUIZ_NOT_FOUND","Chưa tìm thấy Quiz của em.",HttpStatus.NOT_FOUND); }
    static ApiException error(String code, String message, HttpStatus status) { return new ApiException(code,message,status); }
}

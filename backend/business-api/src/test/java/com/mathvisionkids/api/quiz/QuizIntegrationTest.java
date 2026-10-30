package com.mathvisionkids.api.quiz;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.*;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import static com.mathvisionkids.api.quiz.QuizDtos.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest @AutoConfigureMockMvc @ActiveProfiles("test")
class QuizIntegrationTest {
    @Autowired QuizService service; @Autowired QuizSources sources; @Autowired QuizRepository quizzes;
    @Autowired QuizAttemptRepository attempts; @Autowired StudentRepository students;
    @Autowired MockMvc mvc; @Autowired ObjectMapper json;
    @Autowired com.mathvisionkids.api.tutoring.MathTutorService tutor;
    @Autowired QuizNarration speech;
    @Autowired QuizPreparations preparations;
    @Autowired QuizPreparationRepository prepared;
    String owner, other;
    Preparation prepareAndWait(String principal, Prepare request) {
        var response=preparations.prepare(principal,request);
        for(int i=0;i<300 && "GENERATING".equals(response.status());i++) {
            try { Thread.sleep(20); } catch(InterruptedException ex) { Thread.currentThread().interrupt(); throw new AssertionError(ex); }
            response=preparations.status(principal,response.preparationId());
        }
        assertNotEquals("GENERATING",response.status(),"Background generation must finish within its bounded wait");
        return response;
    }

    @BeforeEach void accounts() { owner=account(); other=account(); }
    String account() {
        var student=new Student(); student.setEmail("quiz-"+UUID.randomUUID()+"@test.invalid"); student.setRole("STUDENT");
        student.setDisplayName("Quiz test"); student.setGradeLevel(4); student.setPasswordHash("not-a-login-password"); students.saveAndFlush(student);
        return student.getEmail();
    }
    View ready() { return ready(UUID.randomUUID().toString()); }
    View ready(String sourceId) {
        sources.record(owner,"LESSON",sourceId,QuizMathTest.TREE,true);
        return service.fromLearning(owner,new FromLearning("LESSON",sourceId)).quiz();
    }
    String answer(UUID id) { return quizzes.findById(id).orElseThrow().answerSpec; }
    void allowNext(UUID id) { var q=quizzes.findById(id).orElseThrow(); q.lastSubmittedAt=Instant.now().minusSeconds(2); quizzes.saveAndFlush(q); }
    @Test void confirmedTextPreparesPrivatelyBeforeCompletionThenReusesTheSameVerifiedDraft() throws Exception {
        UUID workflow=UUID.randomUUID();
        var draft=prepareAndWait(owner,new Prepare(workflow,1,QuizMathTest.REPORTED_TREE,true));
        assertEquals("READY",draft.status()); assertEquals(0,service.counts(owner).pendingCount());
        var stored=prepared.findById(draft.preparationId()).orElseThrow();
        var generated=json.readValue(stored.validatedDraft,QuizMath.Verified.class);
        assertNotEquals(Rational.of(60),generated.answer());
        sources.record(owner,"LESSON","early",QuizMathTest.REPORTED_TREE,false);
        assertThrows(ApiException.class,() -> service.fromLearning(owner,new FromLearning("LESSON","early")));
        sources.complete(owner,"early"); var invitation=service.fromLearning(owner,new FromLearning("LESSON","early"));
        var saved=quizzes.findById(invitation.quiz().quizId()).orElseThrow();
        assertEquals(generated.question(),saved.questionText); assertEquals(generated.answer().toString(),saved.answerSpec);
        assertNull(invitation.quiz().correctAnswer()); assertNull(invitation.quiz().explanationText());
        service.defer(owner,saved.id); assertEquals(1,service.counts(owner).pendingCount());
        service.start(owner,saved.id);
        assertEquals(3,service.submit(owner,saved.id,new Submission(UUID.randomUUID(),saved.answerSpec)).quiz().stars());
        assertEquals(0,service.counts(owner).pendingCount());
    }
    @Test void editsInvalidateOldDraftAndPendingQuizWhileStaleRequestsCannotOverwriteTheNewRevision() {
        UUID workflow=UUID.randomUUID();
        prepareAndWait(owner,new Prepare(workflow,1,QuizMathTest.REPORTED_TREE,true));
        sources.record(owner,"WORK_REVIEW","old-review",QuizMathTest.REPORTED_TREE,true);
        var old=service.fromLearning(owner,new FromLearning("WORK_REVIEW","old-review")).quiz();
        prepareAndWait(owner,new Prepare(workflow,2,"",false));
        assertEquals(0,service.counts(owner).pendingCount()); assertThrows(ApiException.class,() -> service.get(owner,old.quizId()));
        assertThrows(ApiException.class,() -> service.start(owner,old.quizId()));
        assertEquals("QUIZ_SOURCE_CHANGED",assertThrows(ApiException.class,() -> service.fromLearning(owner,new FromLearning("WORK_REVIEW","old-review"))).getCode());
        var current=prepareAndWait(owner,new Prepare(workflow,3,QuizMathTest.CANDY,true));
        assertEquals(3,prepareAndWait(owner,new Prepare(workflow,1,QuizMathTest.REPORTED_TREE,true)).revision());
        var stored=prepared.findById(current.preparationId()).orElseThrow(); assertEquals(QuizSources.fingerprint(QuizMathTest.CANDY),stored.fingerprint);
        sources.record(owner,"WORK_REVIEW","new-review",QuizMathTest.CANDY,true);
        assertTrue(service.fromLearning(owner,new FromLearning("WORK_REVIEW","new-review")).offered());
    }
    @Test void duplicateConcurrentPreparationsHaveOnePrivateRowAndOneGeneratedQuestion() throws Exception {
        UUID workflow=UUID.randomUUID();
        try(var workers=Executors.newFixedThreadPool(2)) {
            var gate=new CountDownLatch(1);
            Callable<Preparation> run=() -> { gate.await(); return prepareAndWait(owner,new Prepare(workflow,1,QuizMathTest.REPORTED_TREE,true)); };
            var a=workers.submit(run); var b=workers.submit(run); gate.countDown();
            assertEquals(a.get(15,TimeUnit.SECONDS).preparationId(),b.get(15,TimeUnit.SECONDS).preparationId());
        }
        assertEquals(0,service.counts(owner).pendingCount());
    }
    @Test void failedBackgroundGenerationCanRetryAtTrustedCompletionWithoutBeingMislabelledUnsupported() {
        var response=prepareAndWait(owner,new Prepare(UUID.randomUUID(),1,QuizMathTest.REPORTED_TREE,true));
        var row=prepared.findById(response.preparationId()).orElseThrow(); row.status="FAILED"; row.errorCode="QUIZ_GENERATION_FAILED"; row.validatedDraft=null; prepared.saveAndFlush(row);
        sources.record(owner,"LESSON","retry-generation",QuizMathTest.REPORTED_TREE,true);
        var quiz=service.fromLearning(owner,new FromLearning("LESSON","retry-generation")).quiz();
        assertEquals("READY",quiz.status()); assertNotEquals("60",answer(quiz.quizId()));
        assertFalse(service.fromLearning(owner,new FromLearning("LESSON","retry-generation")).offered());
    }
    @Test void reconfirmingTheSameTextCannotResetElapsedTimeOrWrongAttemptsOrCreateAnotherQuiz() {
        UUID workflow=UUID.randomUUID(); prepareAndWait(owner,new Prepare(workflow,1,QuizMathTest.REPORTED_TREE,true));
        sources.record(owner,"LESSON","same-text-before-edit",QuizMathTest.REPORTED_TREE,true);
        var old=service.fromLearning(owner,new FromLearning("LESSON","same-text-before-edit")).quiz();
        var started=service.start(owner,old.quizId()); service.submit(owner,old.quizId(),new Submission(UUID.randomUUID(),"999999"));
        prepareAndWait(owner,new Prepare(workflow,2,"",false));
        prepareAndWait(owner,new Prepare(workflow,3,QuizMathTest.REPORTED_TREE,true));
        sources.record(owner,"LESSON","same-text-reconfirmed",QuizMathTest.REPORTED_TREE,true);
        var restored=service.fromLearning(owner,new FromLearning("LESSON","same-text-reconfirmed"));
        assertFalse(restored.offered()); assertEquals(old.quizId(),restored.quiz().quizId()); assertEquals(started.startedAt(),restored.quiz().startedAt());
        assertEquals(1,restored.quiz().wrongAttempts()); assertEquals("IN_PROGRESS",restored.quiz().status()); assertEquals(1,service.counts(owner).pendingCount());
    }
    @Test void malformedOrUnconfirmedInputCannotPrepareAndUntrustedWrongAnswerCannotBePublished() throws Exception {
        UUID workflow=UUID.randomUUID();
        assertEquals("INVALIDATED",prepareAndWait(owner,new Prepare(workflow,1,QuizMathTest.REPORTED_TREE,false)).status());
        assertEquals("UNSUPPORTED",prepareAndWait(owner,new Prepare(workflow,2,QuizMathTest.REPORTED_TREE.replace("16","[?]"),true)).status());
        assertEquals("UNSUPPORTED",prepareAndWait(owner,new Prepare(workflow,3,"Vườn có 1/3 số cây là cây táo.",true)).status());
        var ready=prepareAndWait(owner,new Prepare(workflow,4,QuizMathTest.REPORTED_TREE,true));
        var row=prepared.findById(ready.preparationId()).orElseThrow();
        var object=json.readTree(row.validatedDraft); ((com.fasterxml.jackson.databind.node.ObjectNode)object.get("answer")).put("numerator",999999);
        row.validatedDraft=json.writeValueAsString(object); prepared.saveAndFlush(row);
        sources.record(owner,"LESSON","untrusted-generated-answer",QuizMathTest.REPORTED_TREE,true);
        assertEquals("QUIZ_GENERATION_FAILED",assertThrows(ApiException.class,() -> service.fromLearning(owner,new FromLearning("LESSON","untrusted-generated-answer"))).getCode());
        assertEquals(0,service.counts(owner).pendingCount());
    }
    @Test void preparationEndpointDoesNotLeakQuestionsAnswersOrSolutionsAndEnforcesStudentRole() throws Exception {
        var request=json.writeValueAsString(new Prepare(UUID.randomUUID(),1,QuizMathTest.REPORTED_TREE,true));
        mvc.perform(post("/api/v1/student/quizzes/prepare").with(SecurityMockMvcRequestPostProcessors.user(owner).roles("STUDENT"))
            .contentType(MediaType.APPLICATION_JSON).content(request)).andExpect(status().isOk()).andExpect(jsonPath("status").value("GENERATING"))
            .andExpect(jsonPath("answer").doesNotExist()).andExpect(jsonPath("validatedDraft").doesNotExist()).andExpect(jsonPath("questionText").doesNotExist());
        for(String role:List.of("ADMIN","TEACHER")) mvc.perform(post("/api/v1/student/quizzes/prepare").with(SecurityMockMvcRequestPostProcessors.user(owner).roles(role))
            .contentType(MediaType.APPLICATION_JSON).content(request)).andExpect(status().isForbidden());
        var row=prepareAndWait(owner,new Prepare(UUID.randomUUID(),1,QuizMathTest.REPORTED_TREE,true));
        assertTrue(prepared.findByIdAndStudentId(row.preparationId(),students.findByEmail(other).orElseThrow().getId()).isEmpty());
    }
    @Test void sourcesCannotBeForgedAndIncompleteLessonsCannotCreateQuiz() {
        assertThrows(ApiException.class,() -> service.fromLearning(owner,new FromLearning("LESSON","forged")));
        sources.record(owner,"LESSON","incomplete",QuizMathTest.TREE,false);
        assertThrows(ApiException.class,() -> service.fromLearning(owner,new FromLearning("LESSON","incomplete")));
        sources.complete(owner,"incomplete"); assertTrue(service.fromLearning(owner,new FromLearning("LESSON","incomplete")).offered());
    }
    @Test void completedConfirmedLearningSuppliesDifficultyWithoutChangingTheStudentProfile() {
        var student=students.findByEmail(owner).orElseThrow(); student.setGradeLevel(3); students.saveAndFlush(student);
        sources.record(owner,"LESSON","confirmed-advanced-learning",QuizMathTest.TREE,true);
        var quiz=service.fromLearning(owner,new FromLearning("LESSON","confirmed-advanced-learning")).quiz();
        assertEquals("READY",quiz.status()); assertEquals(4,quiz.gradeLevel());
        assertEquals(3,students.findByEmail(owner).orElseThrow().getGradeLevel());
    }
    @Test void fullAnnotatedConfirmedTextIsStoredBeforeGenerationAndStatusIsOwned() {
        String original="  "+QuizMathTest.REPORTED_TREE+" (2 điểm)  ";
        var response=preparations.prepare(owner,new Prepare(UUID.randomUUID(),1,original,true));
        assertEquals("GENERATING",response.status());
        var row=prepared.findById(response.preparationId()).orElseThrow();
        assertEquals(original,row.confirmedProblemText); assertTrue(row.problemConfirmed);
        assertThrows(ApiException.class,() -> preparations.status(other,row.id));
        for(int i=0;i<300 && "GENERATING".equals(preparations.status(owner,row.id).status());i++) {
            try { Thread.sleep(20); } catch(InterruptedException ex) { throw new AssertionError(ex); }
        }
        assertEquals("READY",preparations.status(owner,row.id).status());
        sources.record(owner,"LESSON","actual-phone-score-suffix",original,true);
        var quiz=service.fromLearning(owner,new FromLearning("LESSON","actual-phone-score-suffix")).quiz();
        assertNotEquals("60",answer(quiz.quizId())); assertEquals("READY",quiz.status());
    }
    @Test void aLateConfirmationStillBindsThePublishedQuizSoEditsCannotLeaveItActive() {
        UUID workflow=UUID.randomUUID();
        sources.record(owner,"LESSON","confirmation-arrived-late",QuizMathTest.REPORTED_TREE,true);
        prepareAndWait(owner,new Prepare(workflow,1,QuizMathTest.REPORTED_TREE,true));
        var quiz=service.fromLearning(owner,new FromLearning("LESSON","confirmation-arrived-late")).quiz();
        assertEquals(1,service.counts(owner).pendingCount());
        prepareAndWait(owner,new Prepare(workflow,2,"",false));
        assertEquals(0,service.counts(owner).pendingCount());
        assertThrows(ApiException.class,() -> service.start(owner,quiz.quizId()));
    }
    @Test void actualTutorBoundaryPersistsConfirmedSourceAndOnlyMarksItCompleteAfterValidatedCompleteResponse() throws Exception {
        var http=(org.springframework.web.client.RestTemplate)org.springframework.test.util.ReflectionTestUtils.getField(tutor,"http");
        var remote=org.springframework.test.web.client.MockRestServiceServer.bindTo(http).build();
        String session=UUID.randomUUID().toString();
        Map<String,Object> step=Map.of("title","Tính tổng","explanation","Em cộng hai số.","question","Em tính được bao nhiêu?","choices",List.of(),"expression","12+8","unit","","workExcerpt","");
        var response=new HashMap<String,Object>(); response.put("sessionId",session); response.put("revision",0); response.put("topic","Cộng số"); response.put("goal","Tìm tổng");
        response.put("outline",List.of("Hiểu đề","Tính tổng")); response.put("stepIndex",0); response.put("completed",List.of()); response.put("status","READY"); response.put("feedback",""); response.put("step",step);
        remote.expect(org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo("http://localhost:8000/internal/v1/tutor/lesson"))
            .andRespond(org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess(json.writeValueAsString(response),MediaType.APPLICATION_JSON));
        mvc.perform(post("/api/v1/student/tutor/lesson").with(SecurityMockMvcRequestPostProcessors.user(owner).roles("STUDENT"))
            .contentType(MediaType.APPLICATION_JSON).content("{\"problemText\":\"Tính: 12 + 8\",\"workText\":\"\",\"problemConfirmed\":true,\"workConfirmed\":false}"))
            .andExpect(status().isOk());
        assertThrows(ApiException.class,() -> service.fromLearning(owner,new FromLearning("LESSON",session)));
        remote.verify(); remote.reset();
        response.put("revision",1); response.put("stepIndex",2); response.put("status","COMPLETE"); response.put("step",null);
        response.put("completed",List.of(Map.of("title","Hiểu đề","expression","","answer","Cộng","unit","","explanation","Tìm tổng hai số."),
            Map.of("title","Tính tổng","expression","12+8","answer","20","unit","","explanation","Em đã tìm tổng.")));
        remote.expect(org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo("http://localhost:8000/internal/v1/tutor/lesson/answer"))
            .andRespond(org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess(json.writeValueAsString(response),MediaType.APPLICATION_JSON));
        mvc.perform(post("/api/v1/student/tutor/lesson/answer").with(SecurityMockMvcRequestPostProcessors.user(owner).roles("STUDENT"))
            .contentType(MediaType.APPLICATION_JSON).content(json.writeValueAsString(Map.of("sessionId",session,"revision",0,"answer","20","hint",false))))
            .andExpect(status().isOk());
        assertTrue(service.fromLearning(owner,new FromLearning("LESSON",session)).offered()); remote.verify();
    }
    @Test void workReviewBoundaryRecordsSourceEvenWhenTheHandwrittenAnswerWasWrong() throws Exception {
        var http=(org.springframework.web.client.RestTemplate)org.springframework.test.util.ReflectionTestUtils.getField(tutor,"http");
        var remote=org.springframework.test.web.client.MockRestServiceServer.bindTo(http).build();
        String source="work-"+UUID.randomUUID();
        var response=Map.of("sourceId",source,"status","NEEDS_REVISION","summary","Em thử kiểm tra lại phép cộng nhé.","praise","","nextAction","Em cộng lại hàng đơn vị.","alternative","",
            "rows",List.of(Map.of("lineIndex",0,"sourceText","12+8=21","status","FIX","feedback","Em kiểm tra phép cộng này nhé.","hints",List.of("Em cộng lại hàng đơn vị."))));
        remote.expect(org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo("http://localhost:8000/internal/v1/tutor/work-review"))
            .andRespond(org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess(json.writeValueAsString(response),MediaType.APPLICATION_JSON));
        mvc.perform(post("/api/v1/student/tutor/work-review").with(SecurityMockMvcRequestPostProcessors.user(owner).roles("STUDENT"))
            .contentType(MediaType.APPLICATION_JSON).content(json.writeValueAsString(Map.of("sourceId",source,"problemText","Tính: 12 + 8","workText","12+8=21","problemConfirmed",true,"workConfirmed",true))))
            .andExpect(status().isOk()).andExpect(jsonPath("status").value("NEEDS_REVISION"));
        var q=service.fromLearning(owner,new FromLearning("WORK_REVIEW",source)).quiz();
        assertEquals("ARITHMETIC_ADDITION_SUBTRACTION",q.topicCode()); assertNotEquals("20",answer(q.quizId())); remote.verify();
    }
    @Test void duplicateSourcesAndConcurrentInvitationCallsOfferOnlyOnce() throws Exception {
        sources.record(owner,"LESSON","completed",QuizMathTest.TREE,true);
        try(var workers=Executors.newFixedThreadPool(2)) {
            var gate=new CountDownLatch(1);
            Callable<Invitation> create=() -> { gate.await(); return service.fromLearning(owner,new FromLearning("LESSON","completed")); };
            var a=workers.submit(create); var b=workers.submit(create); gate.countDown();
            var first=a.get(15,TimeUnit.SECONDS); var second=b.get(15,TimeUnit.SECONDS);
            assertEquals(first.quiz().quizId(),second.quiz().quizId()); assertNotEquals(first.offered(),second.offered());
        }
        assertEquals(1,service.counts(owner).pendingCount());
        sources.record(owner,"LESSON","second-session-same-problem",QuizMathTest.TREE,true);
        assertFalse(service.fromLearning(owner,new FromLearning("LESSON","second-session-same-problem")).offered());
    }
    @Test void secretAnswersAndAudioRemainLockedThroughTwoWrongAttemptsUntilExplicitReveal() throws Exception {
        var q=ready(); service.start(owner,q.quizId());
        for(int wrong=1;wrong<=2;wrong++) {
            var graded=service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),"999999"));
            assertEquals(wrong,graded.quiz().wrongAttempts()); assertEquals(0,graded.quiz().stars());
            assertNull(graded.quiz().explanationText()); assertNull(graded.quiz().correctAnswer());
            assertEquals(wrong==2,graded.quiz().canRevealSolution());
            assertThrows(ApiException.class,() -> service.authorizedSolution(owner,q.quizId()));
            if(wrong==1) assertThrows(ApiException.class,() -> service.reveal(owner,q.quizId()));
            allowNext(q.quizId());
        }
        var revealed=service.reveal(owner,q.quizId()); assertNotNull(revealed.explanationText());
        assertEquals(revealed.explanationText(),service.authorizedSolution(owner,q.quizId()));
        var completed=service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),answer(q.quizId()))).quiz();
        assertEquals("COMPLETED",completed.status()); assertTrue(completed.completedWithSolution()); assertEquals(0,completed.stars());
    }
    @Test void wrongThenCorrectStillRewardsIndependentWorkAndHistorySurvivesReload() {
        var q=ready(); service.start(owner,q.quizId());
        service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),"999999")); allowNext(q.quizId());
        var result=service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),answer(q.quizId()))).quiz();
        assertEquals(3,result.stars()); assertEquals(2,result.attempts().size());
        var reloaded=service.get(owner,q.quizId()); assertEquals(result.attempts(),reloaded.attempts());
        assertEquals(3,service.reveal(owner,q.quizId()).stars()); assertEquals(3,service.counts(owner).totalStars());
    }
    @Test void concurrentRepeatedSubmissionDoesNotDuplicateAttemptsOrRewards() throws Exception {
        var q=ready(); service.start(owner,q.quizId()); var request=new Submission(UUID.randomUUID(),answer(q.quizId()));
        try(var workers=Executors.newFixedThreadPool(2)) {
            var gate=new CountDownLatch(1);
            Callable<Graded> submit=() -> { gate.await(); return service.submit(owner,q.quizId(),request); };
            var a=workers.submit(submit); var b=workers.submit(submit); gate.countDown();
            assertEquals(3,a.get(15,TimeUnit.SECONDS).quiz().stars()); assertEquals(3,b.get(15,TimeUnit.SECONDS).quiz().stars());
        }
        assertEquals(1,attempts.countByQuizId(q.quizId())); assertEquals(3,service.counts(owner).totalStars());
        assertThrows(ApiException.class,() -> service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),request.answer())));
        assertThrows(ApiException.class,() -> service.submit(owner,q.quizId(),new Submission(request.requestId(),"changed")));
    }
    @Test void deferResumeAndStartNeverResetElapsedTimeAndCountsReflectUnfinishedWork() {
        var first=ready(); sources.record(owner,"WORK_REVIEW","review-1","Tính: 12 + 8",true);
        var second=service.fromLearning(owner,new FromLearning("WORK_REVIEW","review-1")).quiz();
        assertEquals(2,service.counts(owner).pendingCount()); service.defer(owner,first.quizId());
        assertEquals(2,service.list(owner,"PENDING",0,12).totalElements()); assertEquals(2,service.counts(owner).pendingCount());
        service.start(owner,first.quizId()); var entity=quizzes.findById(first.quizId()).orElseThrow();
        entity.startedAt=Instant.now().minusSeconds(90); quizzes.saveAndFlush(entity);
        service.defer(owner,first.quizId()); var resumed=service.start(owner,first.quizId()); assertTrue(resumed.elapsedMillis()>=90000);
        assertEquals(1,service.submit(owner,first.quizId(),new Submission(UUID.randomUUID(),answer(first.quizId()))).quiz().stars());
        assertEquals(1,service.counts(owner).pendingCount()); assertEquals(1,service.list(owner,"COMPLETED",0,12).totalElements());
        assertEquals("READY",service.get(owner,second.quizId()).status());
    }
    @Test void studentBCannotReadMutateGradeRevealOrNarrateStudentAQuiz() throws Exception {
        var q=ready();
        mvc.perform(get("/api/v1/student/quizzes/"+q.quizId()).with(SecurityMockMvcRequestPostProcessors.user(other).roles("STUDENT"))).andExpect(status().isNotFound());
        for(String action : List.of("start","resume","defer","pause","reveal-solution","submit","narration")) {
            String body=action.equals("submit") ? json.writeValueAsString(new Submission(UUID.randomUUID(),"48")) : action.equals("narration") ? "{\"voice\":\"vi-VN-NamMinhNeural\"}" : "{}";
            mvc.perform(post("/api/v1/student/quizzes/"+q.quizId()+"/"+action).with(SecurityMockMvcRequestPostProcessors.user(other).roles("STUDENT"))
                    .contentType(MediaType.APPLICATION_JSON).content(body)).andExpect(status().isNotFound());
        }
        assertEquals(0,service.counts(other).pendingCount());
    }
    @Test void apiRejectsAnonymousTeacherAdminAndRewardTimeOwnerForgery() throws Exception {
        var q=ready();
        mvc.perform(get("/api/v1/student/quizzes")).andExpect(status().isUnauthorized());
        for(String role: List.of("TEACHER","ADMIN")) mvc.perform(get("/api/v1/student/quizzes").with(SecurityMockMvcRequestPostProcessors.user(owner).roles(role))).andExpect(status().isForbidden());
        mvc.perform(get("/api/v1/student/quizzes/"+q.quizId()).with(SecurityMockMvcRequestPostProcessors.user(owner).roles("STUDENT")))
            .andExpect(status().isOk()).andExpect(header().string("Cache-Control","no-store"))
            .andExpect(jsonPath("correctAnswer").isEmpty()).andExpect(jsonPath("explanationText").isEmpty());
        service.start(owner,q.quizId());
        for(String field: List.of("stars","elapsedSeconds","studentId","isCorrect"))
            mvc.perform(post("/api/v1/student/quizzes/"+q.quizId()+"/submit").with(SecurityMockMvcRequestPostProcessors.user(owner).roles("STUDENT"))
                .contentType(MediaType.APPLICATION_JSON).content("{\"requestId\":\""+UUID.randomUUID()+"\",\"answer\":\"48\",\""+field+"\":3}"))
                .andExpect(status().isBadRequest());
        assertEquals(0,attempts.countByQuizId(q.quizId()));
        mvc.perform(post("/api/v1/student/quizzes/"+q.quizId()+"/narration").with(SecurityMockMvcRequestPostProcessors.user(owner).roles("STUDENT"))
            .contentType(MediaType.APPLICATION_JSON).content("{\"voice\":\"vi-VN-NamMinhNeural\"}" )).andExpect(status().isConflict());
        mvc.perform(get("/api/v1/student/quizzes?size=1000").with(SecurityMockMvcRequestPostProcessors.user(owner).roles("STUDENT"))).andExpect(status().isBadRequest());
    }
    @Test void quizSpeechUsesThePublishedQuizTextAndExistingInternalBoundaryWithoutFakeLessonSessions() throws Exception {
        var q=ready(); service.start(owner,q.quizId());
        service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),"999999")); allowNext(q.quizId());
        service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),"999998")); service.reveal(owner,q.quizId());
        String solution=service.authorizedSolution(owner,q.quizId());
        var http=(org.springframework.web.client.RestTemplate)org.springframework.test.util.ReflectionTestUtils.getField(speech,"http");
        var remote=org.springframework.test.web.client.MockRestServiceServer.bindTo(http).build();
        byte[] wav=new byte[48]; System.arraycopy("RIFF".getBytes(),0,wav,0,4); System.arraycopy("WAVE".getBytes(),0,wav,8,4);
        remote.expect(org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo("http://localhost:8000/internal/v1/tutor/quiz/narration"))
            .andExpect(org.springframework.test.web.client.match.MockRestRequestMatchers.header("X-Internal-API-Key","test-internal-key"))
            .andExpect(org.springframework.test.web.client.match.MockRestRequestMatchers.jsonPath("$.quizId").value(q.quizId().toString()))
            .andExpect(org.springframework.test.web.client.match.MockRestRequestMatchers.jsonPath("$.text").value(solution))
            .andExpect(org.springframework.test.web.client.match.MockRestRequestMatchers.jsonPath("$.sessionId").doesNotExist())
            .andRespond(org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess(wav,MediaType.parseMediaType("audio/wav")));
        mvc.perform(post("/api/v1/student/quizzes/"+q.quizId()+"/narration").with(SecurityMockMvcRequestPostProcessors.user(owner).roles("STUDENT"))
            .contentType(MediaType.APPLICATION_JSON).content("{\"voice\":\"vi-VN-HoaiMyNeural\"}"))
            .andExpect(status().isOk()).andExpect(header().string("Cache-Control","no-store")).andExpect(content().bytes(wav));
        remote.verify(); remote.reset();
        remote.expect(org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo("http://localhost:8000/internal/v1/tutor/quiz/narration"))
            .andRespond(org.springframework.test.web.client.response.MockRestResponseCreators.withStatus(org.springframework.http.HttpStatus.SERVICE_UNAVAILABLE));
        mvc.perform(post("/api/v1/student/quizzes/"+q.quizId()+"/narration").with(SecurityMockMvcRequestPostProcessors.user(owner).roles("STUDENT"))
            .contentType(MediaType.APPLICATION_JSON).content("{\"voice\":\"vi-VN-HoaiMyNeural\"}"))
            .andExpect(status().isServiceUnavailable());
        assertEquals(solution,service.get(owner,q.quizId()).explanationText()); remote.verify();
    }
    @Test void replayAllowsImprovingStarsWithoutInflatingPendingBadgeCount() {
        var q=ready(); service.start(owner,q.quizId());
        // Attempt 1: wrong, Attempt 2: wrong, reveal solution, then complete with solution -> 0 stars
        service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),"999999")); allowNext(q.quizId());
        service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),"999999")); allowNext(q.quizId());
        service.reveal(owner,q.quizId());
        var firstCompletion=service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),answer(q.quizId()))).quiz();
        assertEquals("COMPLETED",firstCompletion.status()); assertEquals(0,firstCompletion.stars());
        assertEquals(0,service.counts(owner).totalStars()); assertEquals(0,service.counts(owner).pendingCount());

        // Replay: must hide solution, reset in-progress, but NOT inflate pending badge count
        var replaying=service.replay(owner,q.quizId());
        assertEquals("IN_PROGRESS",replaying.status());
        assertNull(replaying.explanationText());
        assertEquals(0,service.counts(owner).pendingCount()); // Not inflated!

        // Now solve correctly on replay in <30s without viewing solution
        allowNext(q.quizId());
        var replayedResult=service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),answer(q.quizId()))).quiz();
        assertEquals("COMPLETED",replayedResult.status());
        assertEquals(3,replayedResult.stars()); // Upgraded to 3 stars!
        assertEquals(3,service.counts(owner).totalStars()); // Student star total upgraded!
        assertEquals(0,service.counts(owner).pendingCount());
        assertEquals(4,replayedResult.attempts().size());
        assertEquals(3,replayedResult.attempts().get(3).stars());
    }

    @Test void digitAppendEndToEndPreparationAndResolution() {
        String problem="Tìm một số biết rằng nếu viết thêm chữ số 6 vào bên phải số đó thì được số mới lớn hơn số phải tìm 537 đơn vị.";
        var prep=prepareAndWait(owner,new Prepare(UUID.randomUUID(),1,problem,true));
        assertEquals("READY",prep.status());
        sources.record(owner,"LESSON","digit-session",problem,true);
        var inv=service.fromLearning(owner,new FromLearning("LESSON","digit-session"));
        assertTrue(inv.offered());
        assertEquals(QuizMath.DIGIT_APPEND,inv.quiz().topicCode());
        assertEquals("INTEGER",inv.quiz().answerFormat());
        var started=service.start(owner,inv.quiz().quizId());
        assertEquals("IN_PROGRESS",started.status());
        var graded=service.submit(owner,inv.quiz().quizId(),new Submission(UUID.randomUUID(),answer(inv.quiz().quizId())));
        assertTrue(graded.attempt().correct());
        assertEquals("COMPLETED",graded.quiz().status());
        assertEquals(3,graded.quiz().stars());
    }

    @Test void practiceReplayRetainsQuestionAndDoesNotAwardNewStarsWhenAnswerDisclosed() {
        var q=ready(); service.start(owner,q.quizId());
        String originalQuestion = service.get(owner, q.quizId()).questionText();
        // Reveal solution and complete
        service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),"999999")); allowNext(q.quizId());
        service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),"999999")); allowNext(q.quizId());
        service.reveal(owner,q.quizId());
        String originalAns = answer(q.quizId());
        var firstComp = service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),originalAns)).quiz();
        assertEquals(0, firstComp.stars());
        assertTrue(firstComp.completedWithSolution());
        assertEquals(0, service.counts(owner).totalStars());

        // Ôn lại bài cũ (PRACTICE)
        var practiceView = service.replay(owner, q.quizId(), "PRACTICE");
        assertEquals("IN_PROGRESS", practiceView.status());
        assertEquals("PRACTICE", practiceView.replayMode());
        assertEquals(originalQuestion, practiceView.questionText());
        assertEquals(0, service.counts(owner).pendingCount());

        // Submit correct answer to the original question in < 30s
        allowNext(q.quizId());
        var practiceResult = service.submit(owner, q.quizId(), new Submission(UUID.randomUUID(), originalAns));
        assertTrue(practiceResult.attempt().correct());
        assertEquals(0, practiceResult.attempt().stars()); // NO stars granted for repeating known answer!
        assertEquals(0, practiceResult.quiz().stars()); // bestStars remains 0
        assertEquals(0, service.counts(owner).totalStars()); // totalStars not inflated
    }

    @Test void totalStarsTracksBestStarsAndDoesNotAccumulateAcrossReplays() {
        var q=ready(); service.start(owner,q.quizId());
        // Initial solve: simulate taking 70s (>60s) -> 1 star
        var quizEntity = quizzes.findById(q.quizId()).orElseThrow();
        quizEntity.startedAt = Instant.now().minusSeconds(75);
        quizzes.saveAndFlush(quizEntity);

        var firstResult = service.submit(owner, q.quizId(), new Submission(UUID.randomUUID(), answer(q.quizId()))).quiz();
        assertEquals(1, firstResult.stars());
        assertEquals(1, service.counts(owner).totalStars());

        // Replay Challenge 1: solves in <30s -> earns 3 stars
        var challenge1 = service.replay(owner, q.quizId(), "CHALLENGE");
        assertEquals("IN_PROGRESS", challenge1.status());
        assertEquals("CHALLENGE", challenge1.replayMode());
        assertNotEquals(answer(q.quizId()), firstResult.answerFormat()); // Variant has different data
        assertEquals(0, service.counts(owner).pendingCount()); // No pending badge inflation

        allowNext(q.quizId());
        var res1 = service.submit(owner, q.quizId(), new Submission(UUID.randomUUID(), answer(q.quizId()))).quiz();
        assertEquals(3, res1.stars());
        // CRITICAL CHECK: totalStars is 3, NOT 1 + 3 = 4!
        assertEquals(3, service.counts(owner).totalStars());

        // Replay Challenge 2: solves in 45s (31-60s) -> earns 2 stars
        var challenge2 = service.replay(owner, q.quizId(), "CHALLENGE");
        assertEquals("IN_PROGRESS", challenge2.status());
        var quizEntity2 = quizzes.findById(q.quizId()).orElseThrow();
        quizEntity2.startedAt = Instant.now().minusSeconds(45);
        quizzes.saveAndFlush(quizEntity2);

        allowNext(q.quizId());
        UUID reqId = UUID.randomUUID();
        var res2 = service.submit(owner, q.quizId(), new Submission(reqId, answer(q.quizId()))).quiz();
        // CRITICAL CHECK: bestStars remains 3 (max of 3 and 2)
        assertEquals(3, res2.stars());
        // CRITICAL CHECK: totalStars remains 3, NOT 3 + 2 = 5!
        assertEquals(3, service.counts(owner).totalStars());

        // Reusing request ID is idempotent and does not increment stars
        var replayedReq = service.submit(owner, q.quizId(), new Submission(reqId, answer(q.quizId())));
        assertEquals(3, replayedReq.quiz().stars());
        assertEquals(3, service.counts(owner).totalStars());
    }

    @Test void duplicateReplayCannotResetTimerQuestionOrSwitchModeWhileActive() {
        var q=ready(); service.start(owner,q.quizId());
        service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),answer(q.quizId())));
        var first=service.replay(owner,q.quizId(),"CHALLENGE");
        var retry=service.replay(owner,q.quizId(),"CHALLENGE");
        assertEquals(first.startedAt(),retry.startedAt());
        assertEquals(first.questionText(),retry.questionText());
        assertEquals("QUIZ_REPLAY_ACTIVE",assertThrows(ApiException.class,
            () -> service.replay(owner,q.quizId(),"PRACTICE")).getCode());
    }
    @Test void challengeNeverRepeatsAnyPreviouslyKnownAnswerIncludingTheLearningSource() {
        String problem="Tìm một số biết rằng nếu viết thêm chữ số 6 vào bên phải số đó thì được số mới lớn hơn số phải tìm 537 đơn vị.";
        sources.record(owner,"LESSON","digit-history",problem,true);
        var q=service.fromLearning(owner,new FromLearning("LESSON","digit-history")).quiz();
        service.start(owner,q.quizId());
        var seen=new HashSet<String>(); seen.add("59"); seen.add(answer(q.quizId()));
        service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),answer(q.quizId())));
        for(int i=0;i<50;i++) {
            var next=service.replay(owner,q.quizId(),"CHALLENGE");
            assertTrue(seen.add(answer(q.quizId())),"Repeated known answer on replay "+i);
            service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),answer(q.quizId())));
        }
    }
    @Test void editingPreparationDuringReplayPreservesCompletedHistoryAndBestStars() {
        UUID workflow=UUID.randomUUID(); prepareAndWait(owner,new Prepare(workflow,1,QuizMathTest.REPORTED_TREE,true));
        sources.record(owner,"LESSON","replay-edit",QuizMathTest.REPORTED_TREE,true);
        var q=service.fromLearning(owner,new FromLearning("LESSON","replay-edit")).quiz();
        service.start(owner,q.quizId()); service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),answer(q.quizId())));
        service.replay(owner,q.quizId(),"CHALLENGE");
        prepareAndWait(owner,new Prepare(workflow,2,"",false));
        assertEquals(3,service.counts(owner).totalStars());
        assertEquals("IN_PROGRESS",service.get(owner,q.quizId()).status());
        assertEquals(1,service.get(owner,q.quizId()).attempts().size());
    }
    @Test void readyViewDoesNotPublishTheQuestionBeforeStarting() {
        var q=ready();
        assertNotEquals(quizzes.findById(q.quizId()).orElseThrow().questionText,q.originalQuestionText());
    }

    @Test void immutableHistoryKeepsEachQuestionAndAssistedCompletionDoesNotEraseBestStars() {
        var q=ready(); var initial=service.start(owner,q.quizId());
        var first=service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),answer(q.quizId())));
        service.replay(owner,q.quizId(),"CHALLENGE");
        service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),"999999")); allowNext(q.quizId());
        service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),"999999")); allowNext(q.quizId());
        var revealed=service.reveal(owner,q.quizId());
        var done=service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),answer(q.quizId())));
        assertEquals(0,done.attempt().stars()); assertTrue(done.quiz().completedWithSolution()); assertEquals(3,done.quiz().stars());
        assertEquals(first.attempt(),done.quiz().attempts().get(0));
        assertEquals(initial.questionText(),done.quiz().attempts().get(0).questionText());
        assertEquals(revealed.questionText(),done.attempt().questionText()); assertTrue(done.attempt().solutionViewed());
        assertFalse(done.quiz().attempts().get(0).solutionViewed());
    }
    @Test void sameConfirmedProblemAcrossLessonAndReviewReusesQuizWithoutReadingANewDraft() {
        var first=ready();
        sources.record(owner,"WORK_REVIEW","same-across-source",QuizMathTest.TREE,true);
        var repeat=service.fromLearning(owner,new FromLearning("WORK_REVIEW","same-across-source"));
        assertFalse(repeat.offered()); assertEquals(first.quizId(),repeat.quiz().quizId());
        assertEquals(1,service.counts(owner).pendingCount());
    }

    @Test void legacyCorrectAttemptsWithDifferentVariantUnitsStillExcludeTheirAnswers() {
        var q=ready(); service.start(owner,q.quizId());
        String original=answer(q.quizId()); service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),original));
        var challenge=service.replay(owner,q.quizId(),"CHALLENGE"); String previous=answer(q.quizId());
        service.submit(owner,q.quizId(),new Submission(UUID.randomUUID(),previous+" "+challenge.unit()));
        for(var a:attempts.findByQuizIdOrderByAttemptNumber(q.quizId())) { a.answerSpec=null; a.questionText=null; attempts.saveAndFlush(a); }
        service.replay(owner,q.quizId(),"CHALLENGE");
        assertNotEquals(original,answer(q.quizId())); assertNotEquals(previous,answer(q.quizId()));
    }
}

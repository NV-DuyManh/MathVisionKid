package com.mathvisionkids.api.quiz;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.event.TransactionalEventListener;
import org.springframework.transaction.support.TransactionTemplate;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.UUID;

/** Generation starts only after the full confirmed text has committed. No cloud dependency. */
@Service
class QuizGenerationWorker {
    record Requested(UUID id,long revision) {}
    private final QuizPreparationRepository rows;
    private final QuizSources identities;
    private final ObjectMapper json;
    private final TransactionTemplate transaction;
    QuizGenerationWorker(QuizPreparationRepository rows,QuizSources identities,ObjectMapper json,PlatformTransactionManager manager) {
        this.rows=rows; this.identities=identities; this.json=json; this.transaction=new TransactionTemplate(manager);
    }
    @org.springframework.context.event.EventListener(org.springframework.boot.context.event.ApplicationReadyEvent.class)
    public void recover(org.springframework.boot.context.event.ApplicationReadyEvent event) {
        // Recover persisted work after a controlled restart; never recreate a published Quiz.
        for(var row:rows.findTop100ByStatusOrderByUpdatedAtAsc("GENERATING"))
            event.getApplicationContext().publishEvent(new Requested(row.id,row.revision));
    }
    @Async @TransactionalEventListener(fallbackExecution=true)
    public void generate(Requested request) {
        var source=rows.findById(request.id()).orElse(null);
        if(source==null || source.revision!=request.revision() || !"GENERATING".equals(source.status)) return;
        long start=System.nanoTime(); String draft=null,error=null,status="READY";
        try { draft=json.writeValueAsString(QuizMath.generateFromConfirmed(source.confirmedProblemText,new SecureRandom())); }
        catch(QuizMath.UnsupportedProblem ex) { status="UNSUPPORTED"; error="QUIZ_UNSUPPORTED"; }
        catch(Exception ex) { status="FAILED"; error="QUIZ_GENERATION_FAILED"; }
        final String result=draft,code=error,state=status;
        long elapsed=(System.nanoTime()-start)/1_000_000;
        transaction.executeWithoutResult(ignored -> {
            identities.lockStudent(source.studentId);
            var current=rows.findById(request.id()).orElseThrow();
            if(current.revision!=request.revision() || !"GENERATING".equals(current.status)) return;
            current.validatedDraft=result; current.errorCode=code; current.status=state;
            current.generatedAt=Instant.now(); current.updatedAt=current.generatedAt; current.durationMs=elapsed;
            rows.saveAndFlush(current);
            LoggerFactory.getLogger(QuizGenerationWorker.class).info("quiz_generation preparation={} revision={} fingerprint={} state={} reason={} durationMs={} version={}",current.id,current.revision,current.fingerprint,state,code,elapsed,QuizMath.VERSION);
        });
    }
}

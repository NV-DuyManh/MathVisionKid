package com.mathvisionkids.api.quiz;

import java.time.Instant;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class QuizActiveTimeTest {
    final Instant start=Instant.parse("2026-10-31T10:00:00Z");
    @Test void leavingForADayAddsNoTimeAndResumingContinuesTheSameCounter() {
        var quiz=new Quiz(); quiz.resume(start); quiz.pause(start.plusSeconds(3));
        assertEquals(3000,quiz.elapsedMillis(start.plusSeconds(86400)));
        quiz.resume(start.plusSeconds(86400)); quiz.pause(start.plusSeconds(86402));
        assertEquals(5000,quiz.elapsedMillis(start.plusSeconds(172800)));
    }
    @Test void crashedClientExpiresInsteadOfCountingForever() {
        var quiz=new Quiz(); quiz.resume(start);
        assertEquals(12000,quiz.elapsedMillis(start.plusSeconds(86400)));
        quiz.resume(start.plusSeconds(86400));
        assertEquals(13000,quiz.elapsedMillis(start.plusSeconds(86401)));
    }
    @Test void heartbeatsExtendTheLeaseWithoutDoubleCounting() {
        var quiz=new Quiz(); quiz.resume(start); quiz.resume(start.plusSeconds(4)); quiz.resume(start.plusSeconds(8));
        quiz.pause(start.plusSeconds(10)); assertEquals(10000,quiz.elapsedMillis(start.plusSeconds(1000)));
        quiz.pause(start.plusSeconds(1001)); assertEquals(10000,quiz.activeElapsedMillis);
    }
    @Test void completedTimeFreezesAndAClockBeforeStartCannotSubtractTime() {
        var quiz=new Quiz(); quiz.activeElapsedMillis=5000; quiz.resume(start);
        assertEquals(5000,quiz.elapsedMillis(start.minusSeconds(2)));
        quiz.pause(start.plusSeconds(2)); quiz.completedAt=start.plusSeconds(2);
        assertEquals(7000,quiz.elapsedMillis(start.plusSeconds(10000)));
    }
}

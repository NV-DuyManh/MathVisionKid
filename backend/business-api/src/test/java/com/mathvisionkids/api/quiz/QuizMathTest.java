package com.mathvisionkids.api.quiz;

import org.junit.jupiter.api.Test;
import java.util.Random;
import static org.junit.jupiter.api.Assertions.*;

class QuizMathTest {
    @Test void actualPhoneScoreDecorationAndEquivalentClausesDoNotGateGenerationOnATopicLabel() {
        for(String original:new String[]{REPORTED_TREE+" (2 điểm)",REPORTED_TREE+" (2,5 điểm)",
                REPORTED_TREE.replace(", 2/5","; 2/5").replace("còn lại là","còn lại gồm")+" (2 điểm)"}) {
            assertEquals(Rational.of(60),QuizMath.analyzeConfirmed(original).orElseThrow().answer());
            var quiz=QuizMath.generateFromConfirmed(original,new Random(42));
            assertNotEquals(Rational.of(60),quiz.answer());
            assertEquals(quiz.answer(),QuizMath.classify(quiz.question(),true).orElseThrow().answer());
        }
        assertThrows(QuizMath.UnsupportedProblem.class,() -> QuizMath.generateFromConfirmed(REPORTED_TREE+" Còn 2 cây chết.",new Random(42)));
    }
    static final String REPORTED_TREE="Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?";
    static final String CANDY="Bé Mạnh có một số viên kẹo. Trong đó, 1/4 số kẹo là kẹo dâu, 2/5 số kẹo là kẹo cam, còn lại là kẹo chanh. Biết có 14 viên kẹo chanh. Hỏi bé Mạnh có tất cả bao nhiêu viên kẹo?";
    static final String DIGIT_APPEND_VIDEO_A = "Tìm một số biết rằng nếu viết thêm chữ số 6 vào bên phải số đó thì được số mới lớn hơn số phải tìm 537 đơn vị.";
    static final String DIGIT_APPEND_WITH_PREFIX = "Đề: Tìm một số biết rằng nếu viết thêm chữ số 6 vào bên phải số đó ta được số mới lớn hơn số phải tìm 537 đơn vị.";

    @Test void digitAppendProblemFromVideoAClassifiesAndGeneratesVerifiedVariants() {
        for (String problem : new String[]{DIGIT_APPEND_VIDEO_A, DIGIT_APPEND_WITH_PREFIX,
                "Tìm một số tự nhiên biết rằng nếu viết thêm chữ số 6 vào bên phải số đó ta được số mới hơn số phải tìm 537 đơn vị.",
                "Tìm một số biết nếu thêm chữ số 6 vào bên phải số đó thì được số mới lớn hơn số ban đầu 537 đơn vị.",
                "Nếu viết thêm chữ số 6 vào bên phải một số thì được số mới lớn hơn số phải tìm 537 đơn vị. Tìm số đó."}) {
            var classified = QuizMath.classify(problem, true).orElseThrow();
            assertEquals(QuizMath.DIGIT_APPEND, classified.code());
            assertEquals(Rational.of(59), classified.answer());
            assertEquals(5, classified.grade());
            assertTrue(classified.solution().contains("537 − 6 = 531"));
            assertTrue(classified.solution().contains("531 ÷ 9 = 59"));
            assertEquals(Rational.of(59), QuizMath.analyzeConfirmed(problem).orElseThrow().answer());
        }
    }

    @Test void digitAppendGeneratesDozensOfValidVariantsWithDistinctIntegers() {
        var source = QuizMath.classify(DIGIT_APPEND_VIDEO_A, true).orElseThrow();
        for (int seed = 0; seed < 100; seed++) {
            var variant = QuizMath.generate(source, new Random(seed));
            assertNotEquals(source.question(), variant.question());
            assertNotEquals(source.answer(), variant.answer());
            assertEquals(QuizMath.DIGIT_APPEND, variant.code());
            var reclassified = QuizMath.classify(variant.question(), true).orElseThrow();
            assertEquals(variant.answer(), reclassified.answer());
            int d = Integer.parseInt(variant.data().get(0));
            long D = Long.parseLong(variant.data().get(1));
            long x = Long.parseLong(variant.data().get(2));
            assertEquals(9L * x + d, D);
            assertEquals(variant.answer(), Rational.of(x));
        }
    }

    @Test void exactReportedConfirmedProblemMustProduceAValidatedQuiz() {
        var source=QuizMath.classify(REPORTED_TREE,true).orElseThrow();
        assertEquals(QuizMath.REMAINDER,source.code()); assertEquals(Rational.of(60),source.answer());
        assertNotEquals(source.answer(),QuizMath.generate(source,new Random(42)).answer());
    }
    @Test void candyReferenceHasFortyWholeItems() {
        var source=QuizMath.classify(CANDY,true).orElseThrow();
        assertEquals(Rational.of(40),source.answer());
        assertEquals(Rational.of(10),source.answer().multiply(Rational.parse(source.data().get(0))));
        assertEquals(Rational.of(16),source.answer().multiply(Rational.parse(source.data().get(1))));
        assertEquals("14",source.data().get(2));
    }
    @Test void explicitFractionBarsParenthesesAndNewlinesAreNormalisedWithoutGuessingDigits() {
        for(String fraction : new String[]{"(1/3)","(1) / (3)","1\n/\n3","1 ⁄ 3","1 ∕ 3"})
            assertEquals(Rational.of(60),QuizMath.classify(REPORTED_TREE.replace("1/3",fraction),true).orElseThrow().answer());
        assertTrue(QuizMath.classify(REPORTED_TREE.replace("1/3","1\n3"),true).isEmpty());
    }
    @Test void deterministicFallbackStillProducesAVerifiedVariantWhenRandomChoicesAreAlwaysRejected() {
        var source=QuizMath.classify(REPORTED_TREE,true).orElseThrow();
        var variant=QuizMath.generate(source,new Random(){ @Override public int nextInt(int bound) { return bound-1; } });
        assertNotEquals(source.answer(),variant.answer());
        assertEquals(variant.answer(),QuizMath.classify(variant.question(),true).orElseThrow().answer());
    }
    static final String TREE="Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam là 16 cây. Hỏi trong vườn có tất cả bao nhiêu cây?";
    static final String BOOK="Thư viện có 1/4 số sách là sách truyện, 3/8 số sách là sách khoa học, còn lại là sách tham khảo. Biết có 18 quyển sách tham khảo. Hỏi thư viện có tất cả bao nhiêu quyển sách?";
    @Test void sourceAnswerIsDerivedFromConfirmedProblemNotStudentWork() {
        var tree=QuizMath.classify(TREE,true).orElseThrow();
        assertEquals(QuizMath.REMAINDER,tree.code()); assertEquals("60",tree.answer().toString());
        assertTrue(tree.solution().contains("11/15")); assertTrue(tree.solution().contains("4/15"));
    }
    @Test void libraryExampleIs48() { assertEquals("48",QuizMath.classify(BOOK,true).orElseThrow().answer().toString()); }
    @Test void hundredsOfVariantsHaveChangedDataAndIndependentlyValidatedIntegerPopulations() {
        var source=QuizMath.classify(REPORTED_TREE,true).orElseThrow();
        for (int seed=0;seed<1000;seed++) {
            var q=QuizMath.generate(source,new Random(seed));
            assertNotEquals(source.question(),q.question()); assertNotEquals(source.answer(),q.answer());
            assertNotEquals(source.data().get(0),q.data().get(0)); assertNotEquals(source.data().get(1),q.data().get(1));
            assertNotEquals(source.data().get(2),q.data().get(2));
            assertEquals(q.answer(),QuizMath.classify(q.question(),true).orElseThrow().answer());
            assertTrue(q.answer().multiply(Rational.parse(q.data().get(0))).integer());
            assertTrue(q.answer().multiply(Rational.parse(q.data().get(1))).integer());
            assertTrue(Rational.parse(q.data().get(2)).positive());
        }
    }
    @Test void variantsChangeTheContextEvenWhenTheSourceIsAlreadyBooksCandyOrMarbles() {
        var marbles=QuizMath.generate(QuizMath.classify(REPORTED_TREE,true).orElseThrow(),new Random(0)).question();
        for (String text : new String[]{REPORTED_TREE,BOOK,CANDY,marbles}) {
            var source=QuizMath.classify(text,true).orElseThrow();
            for (int seed=0;seed<100;seed++) {
                var variant=QuizMath.generate(source,new Random(seed));
                assertNotEquals(source.unit(),variant.unit(),variant.question());
                assertNotEquals(source.answer(),variant.answer());
                Rational a=Rational.parse(variant.data().get(0)), b=Rational.parse(variant.data().get(1));
                Rational rest=Rational.parse(variant.data().get(2));
                assertEquals(variant.answer(),variant.answer().multiply(a).add(variant.answer().multiply(b)).add(rest));
                assertEquals(variant.answer(),QuizMath.classify(variant.question(),true).orElseThrow().answer());
            }
            var fallback=QuizMath.generate(source,new Random(){ @Override public int nextInt(int bound) { return bound-1; } });
            assertNotEquals(source.unit(),fallback.unit());
            assertNotEquals(source.answer(),fallback.answer());
        }
    }
    @Test void uncertainIncompleteContradictoryAndUnsupportedSourcesFailClosed() {
        assertTrue(QuizMath.classify(TREE,false).isEmpty());
        for (String bad : new String[]{TREE.replace("16","[?]"),TREE.replace("16 cây.","cây."),TREE.replace("1/3","1/0"),
            TREE.replace("1/3","3/3"),TREE.replace("16 cây","17 cây"),TREE.replace("2/5 số cây","2/5 số cam"),
            TREE.replace("cây cam là 16","cây táo là 16"),TREE.replace("bao nhiêu cây?","bao nhiêu quyển sách?"),
            TREE.replace("Hỏi trong vườn", "Hỏi số cây táo"), TREE.replace("còn lại","sau đó"),TREE+" Còn 2 cây chết.",
            TREE.replace("có 1/3", "không có 1/3"), TREE.replace("cây xoài", "cây táo xanh"),
            "Một vườn có 1/3 số cây là táo. Hỏi có bao nhiêu cây?", "Diện tích hình tròn bán kính 5 cm?"})
        {
            assertTrue(QuizMath.classify(bad,true).isEmpty(),bad);
            assertTrue(QuizMath.analyzeConfirmed(bad).isEmpty(),bad);
        }
    }
    @Test void wrongProposedAnswerCannotPassTheValidator() {
        assertThrows(IllegalArgumentException.class,() -> QuizMath.remainderVerified("candidate","quyển sách",Rational.parse("1/4"),Rational.parse("3/8"),Rational.of(18),Rational.of(49)));
    }
    @Test void fractionInputsAreComparedExactlyAndUnitsAreWhitelisted() {
        assertEquals(Rational.of(48),QuizMath.answerInput("48 quyển","quyển sách"));
        assertEquals(Rational.of(48),QuizMath.answerInput("48,00 quyển sách","quyển sách"));
        assertEquals(Rational.of(59),QuizMath.answerInput("59", ""));
        assertEquals(Rational.of(59),QuizMath.answerInput("59 đơn vị", ""));
        assertEquals(Rational.of(59),QuizMath.answerInput("59 don vi", ""));
        assertEquals(Rational.parse("3/4"),Rational.parse("0.75"));
        assertThrows(IllegalArgumentException.class,() -> QuizMath.answerInput("48 người","quyển sách"));
        assertThrows(IllegalArgumentException.class,() -> Rational.parse("1/0"));
        assertThrows(IllegalArgumentException.class,() -> Rational.parse("48+0"));
    }
    @Test void arithmeticSkillsAndValidatedVariantsAreDistinct() {
        for (String source : new String[]{"Tính: 12 + 8","Tính 28 − 12","Tính: 6 × 8","Tính: 48 ÷ 6","Tính: 1/3 + 2/5","Tính: 3/4 − 1/8"}) {
            var verified=QuizMath.classify(source,true).orElseThrow();
            for(int seed=0;seed<30;seed++) { var q=QuizMath.generate(verified,new Random(seed)); assertEquals(verified.skill(),q.skill()); assertNotEquals(verified.answer(),q.answer()); assertTrue(q.grade()<=verified.grade()); }
        }
    }
    @Test void starBoundariesUseMillisecondsAndIndependentCorrectness() {
        assertEquals(3,QuizService.stars(0,false)); assertEquals(3,QuizService.stars(29999,false)); assertEquals(3,QuizService.stars(30000,false));
        assertEquals(2,QuizService.stars(30001,false)); assertEquals(2,QuizService.stars(60000,false)); assertEquals(1,QuizService.stars(60001,false));
        assertEquals(1,QuizService.stars(100000,false)); assertEquals(1,QuizService.stars(200000,false)); assertEquals(1,QuizService.stars(999999999,false)); assertEquals(0,QuizService.stars(1,true));
    }
    @Test void gradeUsesTheReasoningAndNumberRangeRatherThanJustTheOperator() {
        assertEquals(1,QuizMath.classify("12+8",true).orElseThrow().grade());
        assertEquals(2,QuizMath.classify("50+30",true).orElseThrow().grade());
        assertEquals(3,QuizMath.classify("99+99",true).orElseThrow().grade());
        assertEquals(2,QuizMath.classify("5×9",true).orElseThrow().grade());
        assertEquals(3,QuizMath.classify("6×8",true).orElseThrow().grade());
        assertEquals(4,QuizMath.classify("99×99",true).orElseThrow().grade());
        assertEquals(3,QuizMath.classify("48÷6",true).orElseThrow().grade());
        assertEquals(4,QuizMath.classify("144÷12",true).orElseThrow().grade());
    }

    @Test void digitAppendExhaustiveFallbackFindsTheLastFreshAnswerAndThenFailsClosed() {
        var source=QuizMath.analyzeConfirmed("Tìm một số biết rằng nếu viết thêm chữ số 6 vào bên phải số đó thì được số mới lớn hơn số phải tìm 537 đơn vị.").orElseThrow();
        var seen=new java.util.HashSet<String>(); for(int x=12;x<=99;x++) if(x!=77)seen.add(String.valueOf(x));
        var stuck=new Random(){ @Override public int nextInt(int bound){return 0;} };
        assertEquals(Rational.of(77),QuizMath.generate(source,stuck,seen).answer());
        seen.add("77"); assertThrows(IllegalArgumentException.class,() -> QuizMath.generate(source,stuck,seen));
    }
}

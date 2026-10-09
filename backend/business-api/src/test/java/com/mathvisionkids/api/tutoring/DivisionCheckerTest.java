package com.mathvisionkids.api.tutoring;

import java.util.List;
import java.util.ArrayList;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static com.mathvisionkids.api.tutoring.MathTutorDtos.*;

class DivisionCheckerTest {
    private DivisionCheckResponse check(String dividend, String divisor, String quotient, String... rows) {
        return DivisionChecker.check(new WrittenDivision(dividend, divisor, quotient, List.of(rows)));
    }

    @Test void firstOwnerPhotoIsCorrectWithLeadingZeroRows() {
        assertEquals("CORRECT", check("49572", "6", "8262", "015", "037", "012", "00").status());
    }

    @Test void secondPhotoKeepsWrongQuotientAndCorrectRowsUntilPupilRepairsIt() {
        var result = check("17843", "3", "59947", "028", "014", "023", "02");
        assertEquals("TRY_AGAIN", result.status());
        assertEquals("quotient", result.field());
        assertTrue(result.message().contains("lượt 3"));
        assertTrue(result.message().contains("14 chia 3"));
        assertFalse(result.message().contains("5947"));
        assertEquals("CORRECT", check("17843", "3", "5947", "028", "014", "023", "02").status());
    }

    @Test void thirdPhotoMustRepairBothMissingZeroAndMissingWorkingRow() {
        var first = check("87268", "3", "2989", "27", "0026", "008", "01");
        assertEquals("quotient", first.field());
        assertTrue(first.message().contains("chữ số 0"));
        assertFalse(first.message().contains("29089"));
        assertEquals("NEEDS_REVIEW", check("87268", "3", "29089", "27", "0026", "008", "01").status());
        var row = check("87268", "3", "29089", "27", "002", "0026", "008", "01");
        assertEquals("TRY_AGAIN", row.status());
        assertEquals(3, row.rowIndex());
        assertEquals("CORRECT", check("87268", "3", "29089", "27", "002", "0026", "028", "01").status());
    }

    @Test void unresolvedTranscriptionAndUnknownLayoutNeverReceiveACorrectVerdict() {
        assertEquals("NEEDS_REVIEW", check("87", "4", "2[?]", "07", "3").status());
        assertEquals("NEEDS_REVIEW", check("87", "4", "21", "-8", "07", "3").status());
        assertEquals("NEEDS_REVIEW", check("87", "4", "21", "07").status());
        assertEquals("NEEDS_REVIEW", check("87", "0", "21", "07", "3").status());
        assertEquals("NEEDS_REVIEW", check("1234567890123", "4", "21", "07", "3").status());
        assertEquals("CORRECT", check("87", "4", "21", "0 7", "3").status());
    }

    @Test void wrongIntermediateOrFinalRemainderPointsToTheExactRow() {
        assertEquals(0, check("87", "4", "21", "08", "3").rowIndex());
        assertEquals(1, check("87", "4", "21", "07", "4").rowIndex());
        assertEquals("CORRECT", check("0", "4", "0", "0").status());
        assertEquals("CORRECT", check("3", "12", "0", "3").status());
        assertEquals("CORRECT", check("1005", "5", "201", "00", "05", "0").status());
    }

    @Test void hintsExplainOnlyTheFlaggedTurnWithoutReplacingWrittenNumbers() {
        var written = new WrittenDivision("17843", "3", "59947", List.of("028", "014", "023", "02"));
        var wrongQuotient = DivisionChecker.check(written);
        assertEquals(2, wrongQuotient.hints().size());
        assertTrue(wrongQuotient.hints().getFirst().contains("số đang chia là 14"));
        assertFalse(String.join(" ", wrongQuotient.hints()).contains("5947"));
        assertEquals("59947", written.quotient());
        assertEquals(List.of("028", "014", "023", "02"), written.rows());

        var intermediate = check("17843", "3", "5947", "028", "015", "023", "02");
        assertEquals(1, intermediate.rowIndex());
        assertTrue(intermediate.hints().get(1).contains("(28 − 9 × 3) × 10 + 4"));
        assertFalse(intermediate.hints().get(1).contains("= 14"));
        var last = check("17843", "3", "5947", "028", "014", "023", "03");
        assertTrue(last.hints().get(1).contains("23 − 7 × 3"));
        assertTrue(last.hints().get(1).contains("không hạ thêm chữ số"));
        assertFalse(last.hints().get(1).contains("= 2"));
        assertTrue(check("17843", "3", "5947", "028", "014", "023", "02").hints().isEmpty());
        assertTrue(check("17843", "3", "5[?]47", "028", "014", "023", "02").hints().isEmpty());
    }

    @Test void hintHandlesZeroQuotientPositionsAndDifferentOperandWidths() {
        var zero = check("1005", "5", "21", "00", "05", "0");
        assertTrue(zero.hints().getFirst().contains("số đang chia là 0"));
        assertTrue(zero.hints().get(1).contains("kể cả khi chữ số đó là 0"));
        var wide = check("123456", "97", "1272", "263", "695", "166", "73");
        assertEquals("TRY_AGAIN", wide.status());
        assertEquals(0, wide.rowIndex());
        assertTrue(wide.hints().get(1).contains("(123 − 1 × 97) × 10 + 4"));
    }

    @Test void checkedRowsReconstructManyDifferentDivisionShapes() {
        // Independent fixture construction from quotient positions, including inner/trailing zeroes.
        for (long dividend : new long[]{0, 1, 99, 1005, 10000, 123456, 999999999999L}) {
            for (long divisor : new long[]{1, 3, 12, 97, 1000}) {
                String digits = Long.toString(dividend), quotient = Long.toString(dividend / divisor);
                int firstWidth = digits.length() - quotient.length() + 1;
                List<String> rows = new ArrayList<>();
                for (int width = firstWidth; width < digits.length(); width++) {
                    long prefixRemainder = Long.parseLong(digits.substring(0, width)) % divisor;
                    rows.add(Long.toString(prefixRemainder * 10 + (digits.charAt(width) - '0')));
                }
                rows.add(Long.toString(dividend % divisor));
                assertEquals("CORRECT", DivisionChecker.check(new WrittenDivision(digits,
                        Long.toString(divisor), quotient, rows)).status(), dividend + "/" + divisor);
                rows.set(rows.size() - 1, Long.toString(dividend % divisor + 1));
                assertNotEquals("CORRECT", DivisionChecker.check(new WrittenDivision(digits,
                        Long.toString(divisor), quotient, rows)).status());
            }
        }
    }
}

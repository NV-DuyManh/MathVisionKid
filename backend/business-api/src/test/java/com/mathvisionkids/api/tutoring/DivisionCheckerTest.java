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

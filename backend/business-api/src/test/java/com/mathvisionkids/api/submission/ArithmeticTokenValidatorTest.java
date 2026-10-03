package com.mathvisionkids.api.submission;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class ArithmeticTokenValidatorTest {
    private List<Map<String, Object>> arithmetic(String first, String op, String second, String result) {
        List<Map<String, Object>> tokens = new ArrayList<>();
        List<String> numbers = List.of(first, second, result);
        for (int row = 0; row < 3; row++) {
            String number = numbers.get(row);
            for (int position = 0; position < number.length(); position++) {
                tokens.add(new HashMap<>(Map.of("tokenId", row + "-" + position, "tokenClass", "digit", "value",
                        String.valueOf(number.charAt(position)), "row", row, "column", number.length() - position - 1)));
            }
        }
        tokens.add(new HashMap<>(Map.of("tokenId", "op", "tokenClass", "operator", "value", op, "row", 1)));
        return tokens;
    }
    private ArithmeticTokenValidator.Result check(List<Map<String, Object>> tokens) {
        return ArithmeticTokenValidator.validate(tokens, 6, List.of("VERTICAL_ADDITION", "VERTICAL_SUBTRACTION"));
    }

    @Test void carryOverflowAndBorrowAreCheckedWithIntegerArithmetic() {
        assertEquals(true, check(arithmetic("999999", "+", "1", "1000000")).validation().get("isValid"));
        assertEquals(true, check(arithmetic("50", "-", "17", "33")).validation().get("isValid"));
        var incorrect = check(arithmetic("50", "-", "17", "43"));
        assertEquals(false, incorrect.validation().get("isValid"));
        assertEquals(1, incorrect.evidence().get(0).get("columnIndex"));
        assertFalse(incorrect.evidence().get(0).containsKey("expectedAnswer"));
    }

    @Test void wrongOperatorRowCannotBeGradedAfterADigitConfirmation() {
        var tokens = arithmetic("12", "+", "22", "34");
        tokens.get(tokens.size() - 1).put("row", 0);
        tokens.get(0).put("humanConfirmed", true);
        assertNull(check(tokens).validation().get("isValid"));
        assertEquals("NEEDS_CONFIRMATION", check(tokens).status());
    }

    @Test void oversizedOrAmbiguousOrMultipleWorkCannotBecomeValid() {
        var oversized = arithmetic("1000000", "+", "1", "1000001");
        oversized.get(0).put("humanConfirmed", true);
        assertNull(check(oversized).validation().get("isValid"));
        assertNull(check(arithmetic("999999", "+", "1", "10000000")).validation().get("isValid"));
        var ambiguous = arithmetic("12", "+", "22", "34");
        ambiguous.get(1).put("ambiguity", true);
        assertNull(check(ambiguous).validation().get("isValid"));
        var multiple = arithmetic("12", "+", "22", "34");
        multiple.add(Map.of("tokenId", "extra", "tokenClass", "digit", "value", "1", "row", 3, "column", 0));
        assertNull(check(multiple).validation().get("isValid"));
        assertNull(check(arithmetic("12", "-", "22", "10")).validation().get("isValid"));
        assertNull(ArithmeticTokenValidator.validate(arithmetic("12", "-", "2", "10"), 6,
                List.of("VERTICAL_ADDITION")).validation().get("isValid"));
    }
}

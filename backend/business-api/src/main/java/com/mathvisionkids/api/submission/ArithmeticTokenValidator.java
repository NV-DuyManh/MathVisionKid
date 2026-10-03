package com.mathvisionkids.api.submission;

import java.math.BigInteger;
import java.util.*;

/** Deterministic revalidation of identified tokens after a student's correction. */
final class ArithmeticTokenValidator {
    record Result(String expression, Map<String, Object> validation, List<Map<String, Object>> evidence,
                  Map<String, Object> feedback, String status) {}

    static Result validate(List<Map<String, Object>> tokens, int maxDigits, List<String> allowedOperations) {
        if (tokens.stream().anyMatch(t -> Boolean.TRUE.equals(t.get("ambiguity")))) return uncertain();
        List<Map<String, Object>> operators = tokens.stream().filter(t -> "operator".equals(t.get("tokenClass"))).toList();
        if (operators.size() != 1) return uncertain();
        if (!(operators.get(0).get("row") instanceof Number operatorRow) || operatorRow.intValue() != 1) return uncertain();
        String operator = String.valueOf(operators.get(0).get("value"));
        if (!List.of("+", "-").contains(operator)) return uncertain();
        if (!allowedOperations.contains("+".equals(operator) ? "VERTICAL_ADDITION" : "VERTICAL_SUBTRACTION") ||
                maxDigits < 1 || maxDigits > 6) return uncertain();
        List<String> numbers = new ArrayList<>();
        for (int row = 0; row < 3; row++) {
            final int index = row;
            List<Map<String, Object>> digits = tokens.stream().filter(t -> "digit".equals(t.get("tokenClass")) &&
                    t.get("row") instanceof Number r && r.intValue() == index)
                    .sorted(Comparator.comparingInt(t -> -(t.get("column") instanceof Number c ? c.intValue() : -1))).toList();
            int limit = row == 2 && "+".equals(operator) ? maxDigits + 1 : maxDigits;
            if (digits.isEmpty() || digits.size() > limit) return uncertain();
            StringBuilder value = new StringBuilder();
            for (int position = 0; position < digits.size(); position++) {
                Map<String, Object> digit = digits.get(position);
                if (!(digit.get("column") instanceof Number column) || column.intValue() != digits.size() - position - 1 ||
                        !(digit.get("value") instanceof String v) || !v.matches("[0-9]")) return uncertain();
                value.append(digit.get("value"));
            }
            numbers.add(value.toString());
        }
        if (tokens.stream().anyMatch(t -> "digit".equals(t.get("tokenClass")) &&
                (!(t.get("row") instanceof Number row) || row.intValue() < 0 || row.intValue() > 2))) return uncertain();
        BigInteger first = new BigInteger(numbers.get(0));
        BigInteger second = new BigInteger(numbers.get(1));
        BigInteger expected = "+".equals(operator) ? first.add(second) : first.subtract(second);
        if (expected.signum() < 0) return uncertain();
        boolean valid = expected.equals(new BigInteger(numbers.get(2)));
        String expression = numbers.get(0) + " " + operator + " " + numbers.get(1) + " = " + numbers.get(2);
        List<Map<String, Object>> evidence = new ArrayList<>();
        if (!valid) {
            String expectedDigits = expected.toString();
            String observed = numbers.get(2);
            int width = Math.max(expectedDigits.length(), observed.length());
            for (int column = 0; column < width; column++) {
                char expectedDigit = column < expectedDigits.length() ? expectedDigits.charAt(expectedDigits.length() - column - 1) : '0';
                char observedDigit = column < observed.length() ? observed.charAt(observed.length() - column - 1) : '0';
                if (expectedDigit == observedDigit) continue;
                final int place = column;
                Map<String, Object> item = new HashMap<>();
                item.put("evidenceId", "confirmed-column-" + column);
                item.put("type", "COMPUTATION_ERROR");
                item.put("ruleId", "+".equals(operator) ? "ADD_COL_MISMATCH" : "SUB_COL_MISMATCH");
                item.put("columnIndex", column);
                item.put("placeValue", placeName(column));
                item.put("description", "Kết quả ở " + placeName(column).toLowerCase() + " chưa khớp.");
                tokens.stream().filter(t -> "digit".equals(t.get("tokenClass")) &&
                        t.get("row") instanceof Number r && r.intValue() == 2 &&
                        t.get("column") instanceof Number c && c.intValue() == place).findFirst().ifPresent(t -> {
                    item.put("tokenId", t.get("tokenId"));
                    item.put("boundingBox", t.get("boundingBox"));
                    item.put("observedText", t.get("value"));
                });
                evidence.add(item);
                break;
            }
        }
        Map<String, Object> validation = Map.of("isValid", valid, "diagnosisState", valid ? "VALID" : "INVALID", "evidence", evidence);
        Map<String, Object> feedback = new HashMap<>();
        feedback.put("title", valid ? "Bài làm chính xác!" : "Bài làm cần xem lại");
        feedback.put("hint", valid ? "Phép tính em đã xác nhận khớp với kết quả." : "Em hãy kiểm tra lại " +
                (evidence.isEmpty() ? "các bước tính" : String.valueOf(evidence.get(0).get("placeValue")).toLowerCase()) + " nhé.");
        feedback.put("revealAnswer", false);
        if (!evidence.isEmpty()) feedback.put("focusEvidenceId", evidence.get(0).get("evidenceId"));
        return new Result(expression, validation, evidence, feedback, "FEEDBACK_READY");
    }

    private static Result uncertain() {
        Map<String, Object> validation = new HashMap<>();
        validation.put("isValid", null);
        validation.put("diagnosisState", "UNCERTAIN");
        validation.put("evidence", List.of());
        return new Result(null, validation, List.of(), Map.of("title", "Cần kiểm tra lại ký tự", "hint",
                "Em hãy kiểm tra các ký tự và bố cục phép cộng hoặc trừ. MathVision chưa đủ thông tin để kết luận.",
                "revealAnswer", false), "NEEDS_CONFIRMATION");
    }

    private static String placeName(int column) {
        return "Hàng " + List.of("đơn vị", "chục", "trăm", "nghìn", "chục nghìn", "trăm nghìn", "triệu").get(column);
    }
}

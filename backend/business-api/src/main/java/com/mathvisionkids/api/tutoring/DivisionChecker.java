package com.mathvisionkids.api.tutoring;

import java.util.ArrayList;
import java.util.List;
import static com.mathvisionkids.api.tutoring.MathTutorDtos.*;

/** Checks compact primary-school division: brought-down partials, then final remainder.
 * Transcription is never changed. Explicit subtraction layouts need a separate review. */
final class DivisionChecker {
    private DivisionChecker() {}

    static DivisionCheckResponse check(WrittenDivision written) {
        if (!digits(written.dividend())) return review("dividend", null, "Em kiểm tra lại số bị chia; cần đọc rõ từng chữ số (tối đa 12 chữ số).");
        if (!digits(written.divisor())) return review("divisor", null, "Em kiểm tra lại số chia; cần đọc rõ từng chữ số (tối đa 12 chữ số).");
        long divisor = Long.parseLong(written.divisor());
        if (divisor == 0) return review("divisor", null, "Không thể chia cho 0. Em nhìn lại số chia trong ảnh nhé.");
        if (!digits(written.quotient())) return review("quotient", null, "Em điền hoặc sửa những chữ số chưa rõ ở thương trước nhé.");
        for (int i = 0; i < written.rows().size(); i++) {
            if (!digits(written.rows().get(i).replace(" ", "")))
                return review("rows", i, "Hàng này chưa rõ hoặc có phép trừ riêng. Mình đang kiểm tra cách viết gọn: mỗi hàng là số vừa hạ xuống, hàng cuối là số dư. Em đối chiếu lại nhé.");
        }

        String dividend = Long.toString(Long.parseLong(written.dividend()));
        List<Long> partials = new ArrayList<>();
        List<Long> expectedRows = new ArrayList<>();
        StringBuilder quotient = new StringBuilder();
        long partial = 0, remainder = 0;
        for (int i = 0; i < dividend.length(); i++) {
            partial = partial * 10 + (dividend.charAt(i) - '0');
            if (quotient.isEmpty() && partial < divisor && i < dividend.length() - 1) continue;
            partials.add(partial);
            quotient.append(partial / divisor);
            remainder = partial % divisor;
            if (i < dividend.length() - 1)
                expectedRows.add(remainder * 10 + (dividend.charAt(i + 1) - '0'));
            else expectedRows.add(remainder);
            partial = remainder;
        }
        String actualQuotient = Long.toString(Long.parseLong(written.quotient()));
        if (!actualQuotient.equals(quotient.toString())) {
            int digit = 0;
            while (digit < actualQuotient.length() && digit < quotient.length()
                    && actualQuotient.charAt(digit) == quotient.charAt(digit)) digit++;
            int step = Math.min(digit, partials.size() - 1);
            String hint = partials.get(step) < divisor
                    ? "Số đang chia nhỏ hơn số chia; em nhớ giữ vị trí của chữ số 0 trong thương."
                    : "Em chia, nhân rồi trừ để kiểm tra chữ số ở vị trí này; mỗi lượt chỉ viết một chữ số vào thương.";
            return new DivisionCheckResponse("TRY_AGAIN", "quotient", null,
                    "Em xem lại thương ở lượt " + (step + 1) + ": lấy " + partials.get(step) + " chia " + divisor + ". " + hint);
        }
        // Do not label a subtraction/product row as a wrong brought-down number.
        if (written.rows().size() != expectedRows.size())
            return review("rows", null, "Thương đã đúng. Mình cần " + expectedRows.size()
                    + " hàng theo cách viết gọn (kể cả hàng số dư cuối). Em kiểm tra hàng bị thiếu, thừa hoặc cách trình bày khác nhé.");
        for (int i = 0; i < expectedRows.size(); i++) {
            if (Long.parseLong(written.rows().get(i).replace(" ", "")) != expectedRows.get(i)) {
                String instruction = i == expectedRows.size() - 1
                        ? "Đây là số dư cuối; số dư phải nhỏ hơn số chia."
                        : "Lấy số dư của lượt này rồi hạ đúng một chữ số tiếp theo xuống.";
                return new DivisionCheckResponse("TRY_AGAIN", "rows", i,
                        "Em xem lại hàng " + (i + 1) + ", sau lượt lấy " + partials.get(i) + " chia " + divisor + ". " + instruction);
            }
        }
        return new DivisionCheckResponse("CORRECT", "", null,
                "Thương và các hàng tính em xác nhận đều đúng. Số dư cuối là " + remainder + ".");
    }

    private static boolean digits(String value) { return value != null && value.matches("[0-9]{1,12}"); }
    private static DivisionCheckResponse review(String field, Integer index, String message) {
        return new DivisionCheckResponse("NEEDS_REVIEW", field, index, message);
    }
}

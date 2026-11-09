package com.mathvisionkids.api.assignment;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.io.IOException;
import java.util.UUID;

@Data
public class AssignmentRequest {
    @NotNull
    private UUID classId;

    @NotBlank
    private String title;

    @NotBlank
    private String operationType;

    @NotNull(message = "Thang điểm tối đa là bắt buộc")
    @Min(value = 1, message = "Thang điểm tối đa phải lớn hơn hoặc bằng 1")
    @Max(value = 100, message = "Thang điểm tối đa không được vượt quá 100")
    @JsonDeserialize(using = MaxScoreDeserializer.class)
    private Integer maxScore;

    static class MaxScoreDeserializer extends JsonDeserializer<Integer> {
        @Override
        public Integer deserialize(JsonParser parser, DeserializationContext context) throws IOException {
            try {
                if (parser.currentToken().isNumeric()) {
                    return parser.getDecimalValue().intValueExact();
                }
                if (parser.hasToken(JsonToken.VALUE_STRING)) {
                    return Integer.valueOf(parser.getText().trim());
                }
            } catch (ArithmeticException | NumberFormatException invalidInteger) {
                return context.reportInputMismatch(Integer.class, "Expected an integer maxScore");
            }
            return context.reportInputMismatch(Integer.class, "Expected an integer maxScore");
        }
    }
}

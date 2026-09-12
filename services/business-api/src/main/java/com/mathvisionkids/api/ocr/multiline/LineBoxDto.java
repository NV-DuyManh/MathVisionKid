package com.mathvisionkids.api.ocr.multiline;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class LineBoxDto {
    @JsonProperty("line_id")
    private String lineId;
    private int x;
    private int y;
    private int width;
    private int height;
    private int order;
}

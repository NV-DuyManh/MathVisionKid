package com.mathvisionkids.api.ocr.multiline;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MultilineDetectResponse {
    private int width;
    private int height;
    private List<LineBoxDto> lines;
}

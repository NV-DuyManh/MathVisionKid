package com.mathvisionkids.api.storage;

import com.mathvisionkids.api.common.ApiException;
import java.nio.charset.StandardCharsets;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;

public final class ImageContentType {
    private ImageContentType() {}

    public static MediaType detect(byte[] image) {
        if (image.length >= 8 && image[0] == (byte) 0x89 && image[1] == 'P' && image[2] == 'N'
                && image[3] == 'G' && image[4] == 13 && image[5] == 10 && image[6] == 26 && image[7] == 10) {
            return MediaType.IMAGE_PNG;
        }
        if (image.length >= 3 && image[0] == (byte) 0xff && image[1] == (byte) 0xd8 && image[2] == (byte) 0xff) {
            return MediaType.IMAGE_JPEG;
        }
        if (image.length >= 12 && new String(image, 0, 4, StandardCharsets.US_ASCII).equals("RIFF")
                && new String(image, 8, 4, StandardCharsets.US_ASCII).equals("WEBP")) {
            return MediaType.parseMediaType("image/webp");
        }
        throw new ApiException("IMAGE_UNSUPPORTED", "Hãy chọn ảnh PNG, JPG hoặc WebP hợp lệ.", HttpStatus.UNPROCESSABLE_ENTITY);
    }
}

package com.mathvisionkids.api.submission;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.storage.ImageContentType;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import javax.imageio.ImageIO;
import javax.imageio.stream.MemoryCacheImageInputStream;
import javax.imageio.stream.MemoryCacheImageOutputStream;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.multipart.MultipartFile;

/** Validates the final cropped upload and strips metadata before private storage. */
record AssignedWebImage(byte[] bytes, String contentType, String inputDigest, String storedDigest) {
    private static final int MAX_BYTES = 8 * 1024 * 1024;
    private static final long MAX_PIXELS = 16_000_000;

    static AssignedWebImage read(MultipartFile file, boolean privacyConfirmed) {
        if (!privacyConfirmed) {
            throw new ApiException("PRIVACY_REQUIRED", "Em hãy xác nhận đã che thông tin riêng tư.", HttpStatus.BAD_REQUEST);
        }
        if (file == null || file.isEmpty()) throw invalid();
        if (file.getSize() > MAX_BYTES) throw tooLarge();
        try (var input = file.getInputStream()) {
            byte[] raw = input.readNBytes(MAX_BYTES + 1);
            if (raw.length > MAX_BYTES) throw tooLarge();
            MediaType type = ImageContentType.detect(raw);
            boolean jpeg = MediaType.IMAGE_JPEG.equals(type);
            if ((!jpeg && !MediaType.IMAGE_PNG.equals(type)) || !type.toString().equals(file.getContentType())) {
                throw invalid();
            }
            try (var stream = new MemoryCacheImageInputStream(new ByteArrayInputStream(raw))) {
                var readers = ImageIO.getImageReaders(stream);
                if (!readers.hasNext()) throw invalid();
                var reader = readers.next();
                try {
                    reader.setInput(stream, true, true);
                    int width = reader.getWidth(0), height = reader.getHeight(0);
                    if (width <= 0 || height <= 0 || (long) width * height > MAX_PIXELS) throw invalid();
                    var image = reader.read(0);
                    var output = new ByteArrayOutputStream();
                    try (var encoded = new MemoryCacheImageOutputStream(output)) {
                        if (!ImageIO.write(image, jpeg ? "jpeg" : "png", encoded)) throw invalid();
                    }
                    if (output.size() > MAX_BYTES) throw tooLarge();
                    byte[] stored = output.toByteArray();
                    return new AssignedWebImage(stored, type.toString(), sha256(raw), sha256(stored));
                } finally {
                    reader.dispose();
                }
            }
        } catch (IOException | IllegalArgumentException e) {
            throw invalid();
        }
    }

    static String sha256(byte[] bytes) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }

    private static ApiException invalid() {
        return new ApiException("IMAGE_INVALID", "Em hãy chọn ảnh JPG hoặc PNG hợp lệ.", HttpStatus.BAD_REQUEST);
    }

    private static ApiException tooLarge() {
        return new ApiException("IMAGE_TOO_LARGE", "Ảnh phải nhỏ hơn hoặc bằng 8 MB.", HttpStatus.PAYLOAD_TOO_LARGE);
    }
}

package com.mathvisionkids.api.studentprofile;

import com.mathvisionkids.api.auth.AuthResponse;
import com.mathvisionkids.api.auth.JwtUtil;
import com.mathvisionkids.api.auth.RefreshTokenService;
import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.UserRepository;
import jakarta.persistence.EntityManager;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import javax.imageio.ImageIO;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import static com.mathvisionkids.api.studentprofile.ProfileDtos.*;

@Service
public class StudentAccountService {
    private final StudentProfileService profiles;
    private final JdbcTemplate db;
    private final UserRepository users;
    private final EntityManager em;
    private final PasswordEncoder encoder;
    private final RefreshTokenService tokens;
    private final JwtUtil jwt;

    public StudentAccountService(StudentProfileService profiles, JdbcTemplate db, UserRepository users, EntityManager em,
                                 PasswordEncoder encoder, RefreshTokenService tokens, JwtUtil jwt) {
        this.profiles = profiles; this.db = db; this.users = users; this.em = em;
        this.encoder = encoder; this.tokens = tokens; this.jwt = jwt;
    }

    @Transactional
    public Profile photo(String principal, MultipartFile file) {
        var student = profiles.student(principal);
        byte[] image = thumbnail(file);
        users.lockSessions(student.getId()).orElseThrow();
        int updated = db.update("UPDATE student_profile_photos SET image_bytes = ?, updated_at = ? WHERE student_id = ?",
                image, Timestamp.from(Instant.now()), student.getId());
        if (updated == 0) db.update("INSERT INTO student_profile_photos(student_id, image_bytes, updated_at) VALUES (?, ?, ?)",
                student.getId(), image, Timestamp.from(Instant.now()));
        return profiles.get(principal);
    }

    private byte[] thumbnail(MultipartFile file) {
        if (file.isEmpty() || file.getSize() > 5 * 1024 * 1024)
            throw invalidPhoto("Em chọn ảnh JPG hoặc PNG nhỏ hơn 5 MB nhé.");
        try (var stream = ImageIO.createImageInputStream(new ByteArrayInputStream(file.getBytes()))) {
            var readers = ImageIO.getImageReaders(stream);
            if (!readers.hasNext()) throw invalidPhoto("Chưa đọc được ảnh. Em chọn ảnh JPG hoặc PNG khác nhé.");
            var reader = readers.next();
            try {
                reader.setInput(stream, true, true);
                String format = reader.getFormatName();
                if (!format.equalsIgnoreCase("jpeg") && !format.equalsIgnoreCase("png")) throw invalidPhoto("Em chọn ảnh JPG hoặc PNG nhé.");
                int width = reader.getWidth(0), height = reader.getHeight(0);
                if (width < 32 || height < 32 || (long) width * height > 16_000_000)
                    throw invalidPhoto("Ảnh quá nhỏ hoặc quá lớn. Em chọn ảnh khác nhé.");
                var original = reader.read(0);
                var square = new BufferedImage(256, 256, BufferedImage.TYPE_INT_RGB);
                var graphics = square.createGraphics();
                try {
                    graphics.setColor(java.awt.Color.WHITE); graphics.fillRect(0, 0, 256, 256);
                    graphics.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
                    int side = Math.min(width, height), x = (width - side) / 2, y = (height - side) / 2;
                    graphics.drawImage(original, 0, 0, 256, 256, x, y, x + side, y + side, null);
                } finally { graphics.dispose(); }
                // Re-encoding strips location/EXIF and never serves the original upload.
                var output = new ByteArrayOutputStream();
                if (!ImageIO.write(square, "jpeg", output)) throw invalidPhoto("Chưa lưu được ảnh. Em thử ảnh khác nhé.");
                return output.toByteArray();
            } finally { reader.dispose(); }
        } catch (IOException | IllegalArgumentException exception) {
            throw invalidPhoto("Chưa đọc được ảnh. Em chọn ảnh JPG hoặc PNG khác nhé.");
        }
    }

    @Transactional(noRollbackFor = ApiException.class)
    public AuthResponse password(String principal, PasswordChange request) {
        if (request.newPassword().getBytes(StandardCharsets.UTF_8).length > 72)
            throw new ApiException("PASSWORD_INPUT_INVALID", "Mật khẩu mới tối đa 72 byte, em dùng ít ký tự hơn nhé.", HttpStatus.BAD_REQUEST);
        var student = profiles.student(principal);
        users.lockSessions(student.getId()).orElseThrow();
        em.refresh(student);
        if (student.getGoogleSubject() != null || student.getFacebookSubject() != null)
            throw new ApiException("PASSWORD_PROVIDER_MANAGED", "Em đổi mật khẩu trong tài khoản đăng nhập đã liên kết nhé.", HttpStatus.CONFLICT);
        Instant now = Instant.now();
        var attempts = db.query("SELECT attempts FROM student_password_attempts WHERE student_id = ? AND started_at > ?",
                (r, n) -> r.getInt(1), student.getId(), Timestamp.from(now.minus(15, ChronoUnit.MINUTES)));
        if (!attempts.isEmpty() && attempts.getFirst() >= 5)
            throw new ApiException("PASSWORD_TRY_LATER", "Em đã nhập sai nhiều lần. Em thử lại sau 15 phút nhé.", HttpStatus.TOO_MANY_REQUESTS);
        if (!encoder.matches(request.currentPassword(), student.getPasswordHash())) {
            if (attempts.isEmpty()) {
                db.update("DELETE FROM student_password_attempts WHERE student_id = ?", student.getId());
                db.update("INSERT INTO student_password_attempts(student_id, attempts, started_at) VALUES (?, 1, ?)", student.getId(), Timestamp.from(now));
            } else db.update("UPDATE student_password_attempts SET attempts = attempts + 1 WHERE student_id = ?", student.getId());
            throw new ApiException("PASSWORD_CURRENT_INVALID", "Mật khẩu hiện tại chưa đúng. Em kiểm tra lại nhé.", HttpStatus.BAD_REQUEST);
        }
        if (request.currentPassword().equals(request.newPassword()))
            throw new ApiException("PASSWORD_INPUT_INVALID", "Em chọn mật khẩu mới khác mật khẩu hiện tại nhé.", HttpStatus.BAD_REQUEST);
        student.setPasswordHash(encoder.encode(request.newPassword()));
        tokens.deleteByUserId(student.getId());
        db.update("DELETE FROM student_password_attempts WHERE student_id = ?", student.getId());
        db.update("UPDATE password_reset_codes SET consumed = TRUE WHERE user_id = ?", student.getId());
        em.flush();
        return new AuthResponse(jwt.generateToken(student.getEmail(), student.getRole()), tokens.createRefreshToken(student.getId()));
    }

    private ApiException invalidPhoto(String message) {
        return new ApiException("PROFILE_PHOTO_INVALID", message, HttpStatus.UNPROCESSABLE_ENTITY);
    }
}

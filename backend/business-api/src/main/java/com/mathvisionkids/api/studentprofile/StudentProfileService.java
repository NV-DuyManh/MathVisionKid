package com.mathvisionkids.api.studentprofile;

import com.mathvisionkids.api.common.ApiException;
import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import jakarta.persistence.EntityManager;
import jakarta.persistence.LockModeType;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.annotation.Isolation;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URI;
import java.text.Normalizer;
import java.time.LocalDate;
import java.util.*;
import static com.mathvisionkids.api.studentprofile.ProfileDtos.*;

@Service
public class StudentProfileService {
    static final Set<String> AVATARS = Set.of("star", "planet", "leaf", "rocket", "moon", "sun");
    private static final int STAR_HISTORY_PAGE_SIZE = 10;
    private static final List<String> INITIAL_AVATARS = List.of("star", "planet", "leaf", "rocket", "moon", "sun");
    private record Preferences(String avatar, String alias, boolean visible, boolean reachedChallenger,
                               boolean nameHidden, String googleAvatarUrl, boolean photoVisible, UUID privacyRevision) {}
    private record Day(LocalDate date, long lessons, long quizzes, long games, long stars) {
        long total() { return lessons + quizzes + games; }
    }

    private final StudentRepository students;
    private final JdbcTemplate db;
    private final StudentRewards rewards;
    private final EntityManager em;

    public StudentProfileService(StudentRepository students, JdbcTemplate db, StudentRewards rewards, EntityManager em) {
        this.students = students;
        this.db = db;
        this.rewards = rewards;
        this.em = em;
    }

    Student student(String principal) {
        return students.findByEmail(principal)
                .filter(s -> Boolean.TRUE.equals(s.getActive()) && "STUDENT".equals(s.getRole()))
                .orElseThrow(() -> new ApiException("STUDENT_REQUIRED", "Em hãy đăng nhập tài khoản học sinh.", HttpStatus.FORBIDDEN));
    }

    @Transactional
    public Profile get(String principal) {
        Student student = student(principal);
        lockStudent(student.getId());
        rewards.lock();
        ensurePreferences(student.getId());
        return profile(student);
    }

    @Transactional
    public Profile update(String principal, Edit edit) {
        Student student = student(principal);
        UUID id = student.getId();
        String name = edit.displayName() == null ? null : Normalizer.normalize(edit.displayName().strip(), Normalizer.Form.NFC);
        if ((name != null && (!name.matches("[\\p{L}\\p{M}\\p{Nd}][\\p{L}\\p{M}\\p{Nd} .’'-]*")
                || name.split(" +", 51).length > 50)) || (edit.avatar() != null && !AVATARS.contains(edit.avatar()))) {
            throw invalid("Em kiểm tra tên hiển thị hoặc chọn một hình đại diện trong bộ sưu tập nhé.");
        }
        em.refresh(student, LockModeType.PESSIMISTIC_WRITE);
        rewards.lock();
        ensurePreferences(id);
        var current = preferences(id);
        boolean leaderboardVisible = edit.leaderboardVisible() == null ? current.visible() : edit.leaderboardVisible();
        boolean nameHidden = edit.leaderboardNameHidden() == null ? current.nameHidden() : edit.leaderboardNameHidden();
        boolean removePhoto = Boolean.TRUE.equals(edit.removePhoto());
        boolean sharePhoto = Boolean.TRUE.equals(edit.leaderboardPhotoVisible());
        boolean photoVisible = leaderboardVisible && !removePhoto && (edit.leaderboardPhotoVisible() == null
                ? current.photoVisible() : edit.leaderboardPhotoVisible());
        boolean changesPrivacy = leaderboardVisible != current.visible() || nameHidden != current.nameHidden()
                || photoVisible != current.photoVisible() || removePhoto;
        boolean expandsSharing = (leaderboardVisible && !current.visible()) || (!nameHidden && current.nameHidden())
                || (sharePhoto && !current.photoVisible());
        boolean stale = edit.privacyRevision() != null && !edit.privacyRevision().equals(current.privacyRevision());
        if (stale || (edit.privacyRevision() == null && expandsSharing) || (sharePhoto && !photoVisible)) {
            throw privacyConflict();
        }
        if (Boolean.TRUE.equals(edit.leaderboardVisible()) && student.getEmail().toLowerCase(Locale.ROOT).endsWith("@mathvision.local"))
            throw invalid("Tài khoản này không tham gia bảng xếp hạng.");
        String newSharedPhoto = null;
        if (sharePhoto && !current.photoVisible()) {
            newSharedPhoto = leaderboardAvatar(id, current.googleAvatarUrl());
            if (newSharedPhoto == null) throw privacyConflict();
        }
        if (name != null && !name.equals(student.getDisplayName())) {
            student.setDisplayName(name);
            students.saveAndFlush(student);
        }
        db.update("""
                UPDATE student_profile_preferences SET avatar = COALESCE(?, avatar), leaderboard_visible = ?,
                    leaderboard_name_hidden = ?, privacy_revision = ? WHERE student_id = ?
                """, edit.avatar(), leaderboardVisible, nameHidden,
                changesPrivacy ? UUID.randomUUID() : current.privacyRevision(), id);
        rewards.rememberChallengers();
        if (removePhoto) {
            db.update("DELETE FROM student_profile_photos WHERE student_id = ?", id);
            db.update("""
                    UPDATE student_profile_preferences SET google_avatar_url = NULL, google_avatar_enabled = FALSE
                    WHERE student_id = ?
                    """, id);
        }
        if (!photoVisible) {
            setLeaderboardAvatar(id, null);
        } else if (newSharedPhoto != null) {
            setLeaderboardAvatar(id, newSharedPhoto);
        }
        return profile(student);
    }

    private ApiException privacyConflict() {
        return new ApiException("PROFILE_PRIVACY_CONFLICT", "Quyền riêng tư hoặc ảnh đã thay đổi. Em tải lại hồ sơ rồi chọn lại nhé.", HttpStatus.CONFLICT);
    }

    void revokePhotoAfterReplacement(UUID id) {
        ensurePreferences(id);
        db.update("UPDATE student_profile_preferences SET leaderboard_avatar = NULL, privacy_revision = ? WHERE student_id = ?",
                UUID.randomUUID(), id);
    }

    void setLeaderboardAvatar(UUID id, String photo) {
        db.update("""
                UPDATE student_profile_preferences SET leaderboard_avatar = ?
                WHERE student_id = ? AND leaderboard_avatar IS DISTINCT FROM ?
                """, photo, id, photo);
    }

    private String leaderboardAvatar(UUID id, String googlePhoto) {
        var uploaded = db.query("SELECT image_bytes FROM student_profile_photos WHERE student_id = ?",
                (r, n) -> r.getBytes(1), id);
        if (uploaded.isEmpty()) return isGoogleAvatarUrl(googlePhoto) ? googlePhoto : null;
        try {
            var original = ImageIO.read(new ByteArrayInputStream(uploaded.getFirst()));
            if (original == null) return null;
            var thumbnail = new BufferedImage(64, 64, BufferedImage.TYPE_INT_RGB);
            var graphics = thumbnail.createGraphics();
            try {
                graphics.setRenderingHint(java.awt.RenderingHints.KEY_INTERPOLATION, java.awt.RenderingHints.VALUE_INTERPOLATION_BILINEAR);
                graphics.drawImage(original, 0, 0, 64, 64, null);
            } finally {
                graphics.dispose();
            }
            var output = new ByteArrayOutputStream();
            return ImageIO.write(thumbnail, "jpeg", output) ? jpegDataUrl(output.toByteArray()) : null;
        } catch (IOException exception) {
            return null;
        }
    }

    private static String jpegDataUrl(byte[] bytes) {
        return "data:image/jpeg;base64," + Base64.getEncoder().encodeToString(bytes);
    }

    @Transactional
    public void initialize(UUID id) {
        lockStudent(id);
        rewards.lock();
        ensurePreferences(id);
    }

    public static boolean isGoogleAvatarUrl(Object pictureClaim) {
        if (!(pictureClaim instanceof String url) || url.length() > 2048) return false;
        URI picture;
        try {
            picture = URI.create(url);
        } catch (IllegalArgumentException exception) {
            return false;
        }
        String host = picture.getHost();
        return "https".equals(picture.getScheme()) && host != null && host.endsWith(".googleusercontent.com")
                && picture.getUserInfo() == null && picture.getPort() == -1 && picture.getRawPath().startsWith("/");
    }

    @Transactional
    public void captureGoogleAvatar(UUID id, Object pictureClaim) {
        if (!isGoogleAvatarUrl(pictureClaim)) return;
        String url = (String) pictureClaim;
        lockStudent(id);
        ensurePreferences(id);
        db.update("""
                UPDATE student_profile_preferences SET google_avatar_url = ?, leaderboard_avatar = NULL, privacy_revision = ?
                WHERE student_id = ? AND google_avatar_enabled AND google_avatar_url IS DISTINCT FROM ?
                    AND NOT EXISTS (SELECT 1 FROM student_profile_photos WHERE student_id = ?)
                """, url, UUID.randomUUID(), id, url, id);
    }

    // Admin eligibility changes share the same student -> reward lock order as award/profile writes.
    // Capture both sides of the transition in the admin transaction, including pupils entering
    // the Top 200 without making another request or earning another star.
    @Transactional(propagation = org.springframework.transaction.annotation.Propagation.MANDATORY)
    public void changeRankingEligibility(UUID id, boolean active) {
        Student student = em.find(Student.class, id, LockModeType.PESSIMISTIC_WRITE);
        if (student == null) throw new ApiException("NOT_FOUND", "Student not found", HttpStatus.NOT_FOUND);
        em.refresh(student, LockModeType.PESSIMISTIC_WRITE);
        rewards.lock();
        rewards.rememberChallengers();
        student.setActive(active);
        students.saveAndFlush(student);
        rewards.rememberChallengers();
    }

    private void ensurePreferences(UUID id) {
        var aliases = db.queryForList("SELECT public_alias FROM student_profile_preferences WHERE student_id = ?", String.class, id);
        if (!aliases.isEmpty() && !aliases.getFirst().isBlank() && !aliases.getFirst().matches("Sao [a-f0-9]{12}")) return;
        rewards.lock();
        String alias = StudentAnimalAliases.next(new HashSet<>(db.queryForList("SELECT public_alias FROM student_profile_preferences", String.class)));
        if (aliases.isEmpty()) {
            String avatar = INITIAL_AVATARS.get(java.util.concurrent.ThreadLocalRandom.current().nextInt(INITIAL_AVATARS.size()));
            db.update("INSERT INTO student_profile_preferences(student_id, public_alias, avatar) VALUES (?, ?, ?)", id, alias, avatar);
        } else {
            db.update("UPDATE student_profile_preferences SET public_alias = ? WHERE student_id = ?", alias, id);
        }
    }

    private List<Day> days(UUID id) {
        return db.query("""
                SELECT activity_day,
                    SUM(CASE WHEN source = 'LESSON' THEN 1 ELSE 0 END) AS lessons,
                    SUM(CASE WHEN source = 'QUIZ' THEN 1 ELSE 0 END) AS quizzes,
                    SUM(CASE WHEN source = 'GAME' THEN 1 ELSE 0 END) AS games,
                    SUM(stars) AS stars
                FROM student_verified_activities WHERE student_id = ? GROUP BY activity_day ORDER BY activity_day DESC
                """, (r, n) -> new Day(r.getObject("activity_day", LocalDate.class), r.getLong("lessons"),
                r.getLong("quizzes"), r.getLong("games"), r.getLong("stars")), id);
    }

    private Stats stats(List<Day> days) {
        var today = LocalDate.now(StudentRewards.ZONE);
        var activeDays = new HashSet<LocalDate>();
        long lesson = 0, quiz = 0, game = 0, week = 0, month = 0, daily = 0;
        for (Day row : days) {
            activeDays.add(row.date());
            lesson += row.lessons();
            quiz += row.quizzes();
            game += row.games();
            if (!row.date().isBefore(today.minusDays(6))) week += row.total();
            if (!row.date().isBefore(today.minusDays(29))) month += row.total();
            if (row.date().equals(today)) daily += row.total();
        }
        int streak = 0;
        LocalDate cursor = activeDays.contains(today) ? today : today.minusDays(1);
        while (activeDays.contains(cursor)) {
            streak++;
            cursor = cursor.minusDays(1);
        }
        return new Stats(lesson, quiz, game, days.size(), week, month, daily, streak);
    }

    private Preferences preferences(UUID id) {
        return db.query("""
                SELECT avatar, public_alias, leaderboard_visible, reached_challenger, leaderboard_name_hidden, google_avatar_url,
                       leaderboard_visible AND leaderboard_avatar IS NOT NULL, privacy_revision
                FROM student_profile_preferences WHERE student_id = ?
                """, (r, n) -> new Preferences(r.getString(1), r.getString(2), r.getBoolean(3), r.getBoolean(4),
                r.getBoolean(5), r.getString(6), r.getBoolean(7), r.getObject(8, UUID.class)), id)
                .stream().findFirst().orElseThrow();
    }

    @Transactional(readOnly = true, isolation = Isolation.REPEATABLE_READ)
    public ActivityPage starHistory(String principal, long requestedPage) {
        if (requestedPage < 1) {
            throw new ApiException("INVALID_PAGE", "Số trang phải lớn hơn hoặc bằng 1.", HttpStatus.BAD_REQUEST);
        }
        UUID id = student(principal).getId();
        long total = db.queryForObject("""
                SELECT COUNT(*) FROM student_verified_activities WHERE student_id = ? AND stars > 0
                """, Long.class, id);
        long totalPages = Math.max(1, (total + STAR_HISTORY_PAGE_SIZE - 1) / STAR_HISTORY_PAGE_SIZE);
        long page = Math.min(requestedPage, totalPages);
        return new ActivityPage(starHistoryEntries(id, STAR_HISTORY_PAGE_SIZE, (page - 1) * STAR_HISTORY_PAGE_SIZE),
                page, totalPages);
    }

    private List<Activity> starHistoryEntries(UUID id, int size, long offset) {
        return db.query("""
                SELECT source, completed_at, stars FROM student_verified_activities
                WHERE student_id = ? AND stars > 0 ORDER BY completed_at DESC, source, event_id LIMIT ? OFFSET ?
                """, (r, n) -> new Activity(r.getString(1), r.getTimestamp(2).toInstant(), r.getInt(3)), id, size, offset);
    }

    private Profile profile(Student student) {
        UUID id = student.getId();
        var prefs = preferences(id);
        var classes = db.query("""
                SELECT c.class_id, c.name FROM classrooms c JOIN classroom_students cs ON cs.class_id = c.class_id
                WHERE cs.student_id = ? ORDER BY c.name, c.class_id
                """, (r, n) -> new Classroom(r.getObject(1, UUID.class), r.getString(2)), id);
        var history = starHistoryEntries(id, 20, 0);
        var days = days(id);
        var stats = stats(days);
        long stars = days.stream().mapToLong(Day::stars).sum();
        Long globalPosition = position(id, StudentRewards.GLOBAL_RANKING);
        Long position = student.getGradeLevel() == null ? null : position(id, gradeRanking(), student.getGradeLevel());
        var rank = StudentRank.at(stars, globalPosition);
        String photo = db.query("SELECT image_bytes FROM student_profile_photos WHERE student_id = ?",
                (r, n) -> jpegDataUrl(r.getBytes(1)), id)
                .stream().findFirst().orElse(prefs.googleAvatarUrl());
        return new Profile(student.getDisplayName(), student.getGradeLevel(), student.getCreatedAt(), classes, prefs.avatar(),
                prefs.visible(), prefs.alias(), null, stars, rank, prefs.reachedChallenger() ? "Huyền Thoại" : rank.name(),
                position, stats, List.of(), history, photo, student.getGoogleSubject() == null && student.getFacebookSubject() == null,
                prefs.nameHidden(), student.getGoogleSubject() != null, prefs.photoVisible(), prefs.privacyRevision());
    }

    private Long position(UUID student, String ranking, Object... filters) {
        var arguments = new ArrayList<>(Arrays.asList(filters));
        arguments.add(student);
        return db.queryForList("SELECT position FROM (" + ranking + ") ranked WHERE student_id = ?",
                Long.class, arguments.toArray()).stream().findFirst().orElse(null);
    }

    @Transactional(readOnly = true, isolation = Isolation.REPEATABLE_READ)
    public Leaderboard leaderboard(String principal, UUID classroom) {
        return leaderboard(principal, classroom, false);
    }

    @Transactional(readOnly = true, isolation = Isolation.REPEATABLE_READ)
    public Leaderboard leaderboard(String principal, UUID classroom, boolean allGrades) {
        if (allGrades && classroom != null) throw invalid("Em chỉ có thể xem một phạm vi xếp hạng mỗi lần.");
        Student student = student(principal);
        UUID id = student.getId();
        Integer grade = allGrades ? null : student.getGradeLevel();
        if (!allGrades && grade == null) return new Leaderboard(List.of(), null, null);
        String ranking = allGrades
                ? "SELECT g.*, g.position AS global_position FROM (" + StudentRewards.GLOBAL_RANKING + ") g"
                : gradeRanking();
        Object[] filters = allGrades ? new Object[0] : new Object[] { grade };
        if (classroom != null) {
            if (db.queryForObject("SELECT COUNT(*) FROM classroom_students WHERE class_id = ? AND student_id = ?",
                    Long.class, classroom, id) == 0) {
                throw new ApiException("CLASS_NOT_FOUND", "Em chưa tham gia lớp này.", HttpStatus.NOT_FOUND);
            }
            ranking = """
                    SELECT g.*, ROW_NUMBER() OVER (ORDER BY g.position) AS class_position
                    FROM (%s) g JOIN classroom_students cs ON cs.student_id = g.student_id WHERE cs.class_id = ?
                    """.formatted(ranking);
            filters = new Object[] { grade, classroom };
        }
        String order = classroom == null ? "position" : "class_position";
        var entries = db.query("SELECT ranked.*, p.leaderboard_avatar FROM (" + ranking + ") ranked "
                        + "JOIN student_profile_preferences p ON p.student_id = ranked.student_id ORDER BY ranked." + order + " LIMIT 200",
                (r, n) -> new Entry(r.getLong(order), r.getString("board_name"), r.getString("avatar"), r.getLong("stars"),
                        StudentRank.at(r.getLong("stars"), r.getLong("global_position")), id.equals(r.getObject("student_id", UUID.class)),
                        r.getString("leaderboard_avatar")), filters);
        String ownRanking = classroom == null ? ranking : "SELECT student_id, class_position AS position FROM (" + ranking + ") by_class";
        return new Leaderboard(entries, position(id, ownRanking, filters), grade);
    }

    private String gradeRanking() {
        return """
                SELECT g.student_id, g.public_alias, g.board_name, g.avatar, g.stars, g.position AS global_position,
                    ROW_NUMBER() OVER (ORDER BY g.position) AS position
                FROM (%s) g JOIN students s ON s.student_id = g.student_id
                    WHERE s.grade_level = ?
                """.formatted(StudentRewards.GLOBAL_RANKING);
    }

    void lockStudent(UUID id) {
        em.find(Student.class, id, LockModeType.PESSIMISTIC_WRITE);
    }

    static ApiException invalid(String message) {
        return new ApiException("PROFILE_INPUT_INVALID", message, HttpStatus.BAD_REQUEST);
    }
}

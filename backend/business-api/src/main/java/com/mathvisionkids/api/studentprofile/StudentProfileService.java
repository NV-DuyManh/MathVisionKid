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

import java.text.Normalizer;
import java.time.LocalDate;
import java.util.*;
import static com.mathvisionkids.api.studentprofile.ProfileDtos.*;

@Service
public class StudentProfileService {
    static final Set<String> AVATARS = Set.of("star", "planet", "leaf", "rocket", "moon", "sun");
    private record Preferences(String avatar, String alias, boolean visible, String title, boolean reachedChallenger) {}
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

    @Transactional(readOnly = true, isolation = Isolation.REPEATABLE_READ)
    public Profile get(String principal) {
        return profile(student(principal));
    }

    @Transactional
    public Profile update(String principal, Edit edit) {
        Student student = student(principal);
        UUID id = student.getId();
        String name = Normalizer.normalize(edit.displayName().strip(), Normalizer.Form.NFC);
        if (!name.matches("[\\p{L}\\p{M}][\\p{L}\\p{M} .’'-]{0,39}") || !AVATARS.contains(edit.avatar())) {
            throw invalid("Em kiểm tra tên hiển thị hoặc chọn một hình đại diện trong bộ sưu tập nhé.");
        }
        lockStudent(id);
        student.setDisplayName(name);
        students.saveAndFlush(student);
        rewards.lock();
        if (Boolean.TRUE.equals(edit.leaderboardVisible()) && student.getEmail().toLowerCase(Locale.ROOT).endsWith("@mathvision.local"))
            throw invalid("Tài khoản này không tham gia bảng xếp hạng.");
        String title = edit.selectedTitle();
        if (title != null && titles(stats(days(id))).stream().noneMatch(t -> t.unlocked() && t.id().equals(title)))
            throw invalid("Em hãy chọn danh hiệu đã mở khóa.");
        int updated = db.update("""
                UPDATE student_profile_preferences SET avatar = ?, leaderboard_visible = ?, selected_title = ? WHERE student_id = ?
                """, edit.avatar(), edit.leaderboardVisible(), title, id);
        if (updated == 0) db.update("""
                INSERT INTO student_profile_preferences(student_id, avatar, public_alias, leaderboard_visible, selected_title)
                VALUES (?, ?, ?, ?, ?)
                """, id, edit.avatar(), "Sao " + UUID.randomUUID().toString().replace("-", "").substring(0, 12),
                edit.leaderboardVisible(), title);
        rewards.rememberChallengers();
        if (Boolean.TRUE.equals(edit.removePhoto())) db.update("DELETE FROM student_profile_photos WHERE student_id = ?", id);
        return profile(student);
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

    private List<Title> titles(Stats s) {
        return List.of(
                title("rookie", "Tân Binh Tri Thức", "Phổ biến", "Hoàn thành bài học đầu tiên", s.lessons(), 1),
                title("luyen-khi", "Luyện Khí", "Phổ biến", "Hoàn thành 3 bài học", s.lessons(), 3),
                title("truc-co", "Trúc Cơ", "Hiếm", "Giải đúng 5 Quiz", s.quizzes(), 5),
                title("kim-dan", "Kim Đan", "Hiếm", "Thắng 5 lượt chơi có xác minh", s.games(), 5),
                title("nguyen-anh", "Nguyên Anh", "Sử thi", "Học trong 14 ngày khác nhau", s.days(), 14),
                title("scholar", "Học Bá", "Sử thi", "Hoàn thành 20 bài học", s.lessons(), 20),
                title("master", "Đại Sư Toán Học", "Huyền thoại", "Hoàn thành 30 bài học, 30 Quiz và 30 lượt chơi", Math.min(s.lessons(), Math.min(s.quizzes(), s.games())), 30));
    }

    private Title title(String id, String name, String rarity, String description, long progress, long goal) {
        return new Title(id, name, rarity, description, Math.min(progress, goal), goal, progress >= goal);
    }

    private Profile profile(Student student) {
        UUID id = student.getId();
        var prefs = db.query("""
                SELECT avatar, public_alias, leaderboard_visible, selected_title, reached_challenger
                FROM student_profile_preferences WHERE student_id = ?
                """, (r, n) -> new Preferences(r.getString(1), r.getString(2), r.getBoolean(3), r.getString(4), r.getBoolean(5)), id)
                .stream().findFirst().orElse(new Preferences("star", "", false, null, false));
        var classes = db.query("""
                SELECT c.class_id, c.name FROM classrooms c JOIN classroom_students cs ON cs.class_id = c.class_id
                WHERE cs.student_id = ? ORDER BY c.name, c.class_id
                """, (r, n) -> new Classroom(r.getObject(1, UUID.class), r.getString(2)), id);
        var history = db.query("""
                SELECT source, completed_at, stars FROM student_verified_activities
                WHERE student_id = ? AND stars > 0 ORDER BY completed_at DESC, source, event_id LIMIT 20
                """, (r, n) -> new Activity(r.getString(1), r.getTimestamp(2).toInstant(), r.getInt(3)), id);
        var days = days(id);
        var stats = stats(days);
        long stars = days.stream().mapToLong(Day::stars).sum();
        Long position = position(id, StudentRewards.GLOBAL_RANKING);
        var rank = StudentRank.at(stars, position);
        String photo = db.query("SELECT image_bytes FROM student_profile_photos WHERE student_id = ?",
                (r, n) -> "data:image/jpeg;base64," + Base64.getEncoder().encodeToString(r.getBytes(1)), id)
                .stream().findFirst().orElse(null);
        return new Profile(student.getDisplayName(), student.getGradeLevel(), student.getCreatedAt(), classes, prefs.avatar(),
                prefs.visible(), prefs.alias(), prefs.title(), stars, rank, prefs.reachedChallenger() ? "Thách Đấu" : rank.name(),
                position, stats, titles(stats), history, photo, student.getGoogleSubject() == null && student.getFacebookSubject() == null);
    }

    private Long position(UUID student, String ranking, Object... filters) {
        var arguments = new ArrayList<>(Arrays.asList(filters));
        arguments.add(student);
        return db.queryForList("SELECT position FROM (" + ranking + ") ranked WHERE student_id = ?",
                Long.class, arguments.toArray()).stream().findFirst().orElse(null);
    }

    @Transactional(readOnly = true, isolation = Isolation.REPEATABLE_READ)
    public Leaderboard leaderboard(String principal, UUID classroom) {
        Student student = student(principal);
        UUID id = student.getId();
        String ranking = StudentRewards.GLOBAL_RANKING;
        Object[] filters = {};
        if (classroom != null) {
            if (db.queryForObject("SELECT COUNT(*) FROM classroom_students WHERE class_id = ? AND student_id = ?",
                    Long.class, classroom, id) == 0) {
                throw new ApiException("CLASS_NOT_FOUND", "Em chưa tham gia lớp này.", HttpStatus.NOT_FOUND);
            }
            ranking = """
                    SELECT g.*, ROW_NUMBER() OVER (ORDER BY g.position) AS class_position
                    FROM (%s) g JOIN classroom_students cs ON cs.student_id = g.student_id WHERE cs.class_id = ?
                    """.formatted(ranking);
            filters = new Object[] { classroom };
        }
        String order = classroom == null ? "position" : "class_position";
        var entries = db.query("SELECT * FROM (" + ranking + ") ranked ORDER BY " + order + " LIMIT 200",
                (r, n) -> new Entry(r.getLong(order), r.getString("public_alias"), r.getString("avatar"), r.getLong("stars"),
                        StudentRank.at(r.getLong("stars"), r.getLong("position")), id.equals(r.getObject("student_id", UUID.class))), filters);
        String ownRanking = classroom == null ? ranking : "SELECT student_id, class_position AS position FROM (" + ranking + ") by_class";
        return new Leaderboard(entries, position(id, ownRanking, filters));
    }

    void lockStudent(UUID id) {
        em.find(Student.class, id, LockModeType.PESSIMISTIC_WRITE);
    }

    static ApiException invalid(String message) {
        return new ApiException("PROFILE_INPUT_INVALID", message, HttpStatus.BAD_REQUEST);
    }
}

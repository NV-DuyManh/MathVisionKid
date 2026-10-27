package com.mathvisionkids.validation;

import com.mathvisionkids.api.BusinessApiApplication;
import com.mathvisionkids.api.user.*;
import jakarta.servlet.Filter;
import org.springframework.boot.SpringApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

/** Standalone browser-test harness: H2 memory only, loopback only, no development seed mutation. */
public class AdminOverhaulPreview {
    @Configuration(proxyBeanMethods = false)
    public static class HarnessConfig {
        @Bean Filter isolatedDatabaseMarker() {
            return (request, response, chain) -> {
                ((jakarta.servlet.http.HttpServletResponse) response).setHeader("X-Mathvision-Test-Database", "h2-memory");
                chain.doFilter(request, response);
            };
        }
    }
    public static void main(String[] args) {
        String password = System.getenv("MVK_OVERHAUL_PASSWORD");
        if (password == null || password.length() < 12) throw new IllegalStateException("MVK_OVERHAUL_PASSWORD is required");
        var context = new SpringApplication(BusinessApiApplication.class, HarnessConfig.class).run(
            "--spring.profiles.active=test", "--server.address=127.0.0.1", "--server.port=18080",
            "--spring.datasource.url=jdbc:h2:mem:admin_overhaul;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
            "--spring.datasource.driver-class-name=org.h2.Driver", "--spring.datasource.username=sa", "--spring.datasource.password=",
            "--spring.jpa.hibernate.ddl-auto=create-drop", "--spring.flyway.enabled=false",
            "--spring.main.banner-mode=off", "--logging.level.root=ERROR",
            "--app.cors.allowed-origins=http://localhost:15172,http://localhost:15173,http://localhost:15174,http://127.0.0.1:15172,http://127.0.0.1:15173,http://127.0.0.1:15174");
        var users = context.getBean(UserRepository.class);
        var students = context.getBean(StudentRepository.class);
        var teachers = context.getBean(TeacherRepository.class);
        var encoder = context.getBean(PasswordEncoder.class);
        new TransactionTemplate(context.getBean(PlatformTransactionManager.class)).execute(status -> {
            User admin = new User();
            admin.setEmail("admin.demo@mathvision.local"); admin.setDisplayName("Quản trị viên Demo");
            admin.setRole("ADMIN"); admin.setActive(true); admin.setPasswordHash(encoder.encode(password)); users.save(admin);
            Teacher teacher = new Teacher();
            teacher.setEmail("lan.teacher@mathvision.local"); teacher.setDisplayName("Cô Lan");
            teacher.setRole("TEACHER"); teacher.setActive(true); teacher.setPasswordHash(encoder.encode(password)); teachers.save(teacher);
            Student student = new Student();
            student.setEmail("minh.student@mathvision.local"); student.setDisplayName("Nguyễn Bình Minh");
            student.setGradeLevel(3); student.setRole("STUDENT"); student.setActive(true); student.setPasswordHash(encoder.encode(password)); students.save(student);
            return null;
        });
        System.out.println("ADMIN_OVERHAUL_TEST_READY");
    }
}

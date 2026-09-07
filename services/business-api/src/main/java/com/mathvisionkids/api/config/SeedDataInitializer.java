package com.mathvisionkids.api.config;

import com.mathvisionkids.api.user.Student;
import com.mathvisionkids.api.user.StudentRepository;
import com.mathvisionkids.api.user.Teacher;
import com.mathvisionkids.api.user.TeacherRepository;
import com.mathvisionkids.api.user.User;
import com.mathvisionkids.api.user.UserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;

@Configuration
@Profile("dev")
public class SeedDataInitializer {

    @Bean
    public CommandLineRunner initData(UserRepository userRepository, 
                                      TeacherRepository teacherRepository,
                                      StudentRepository studentRepository, 
                                      PasswordEncoder passwordEncoder) {
        return args -> {
            String devPassword = passwordEncoder.encode("MathVision123!");

            if (userRepository.findByEmail("lan.teacher@mathvision.local").isEmpty()) {
                Teacher teacher = new Teacher();
                teacher.setEmail("lan.teacher@mathvision.local");
                teacher.setPasswordHash(devPassword);
                teacher.setRole("TEACHER");
                teacher.setDisplayName("Ms. Lan");
                teacherRepository.save(teacher);
            }

            if (userRepository.findByEmail("minh.student@mathvision.local").isEmpty()) {
                Student student = new Student();
                student.setEmail("minh.student@mathvision.local");
                student.setPasswordHash(devPassword);
                student.setRole("STUDENT");
                student.setDisplayName("Minh (Student)");
                student.setGradeLevel(3);
                studentRepository.save(student);
            }
            
            System.out.println("Dev seed data initialized successfully.");
        };
    }
}

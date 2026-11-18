package com.mathvisionkids.api.studentprofile;

import com.mathvisionkids.api.common.ApiException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
class StudentUsageLimitConfig implements WebMvcConfigurer {
    private final ParentControlService controls;

    StudentUsageLimitConfig(ParentControlService controls) {
        this.controls = controls;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new HandlerInterceptor() {
            @Override
            public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
                var principal = request.getUserPrincipal();
                if (principal != null && request.isUserInRole("STUDENT") && controls.status(principal.getName()).dailyLimitReached()) {
                    throw new ApiException("STUDENT_DAILY_LIMIT", "Hôm nay em đã dùng hết thời gian.", HttpStatus.TOO_MANY_REQUESTS);
                }
                return true;
            }
        }).addPathPatterns("/api/v1/student/**", "/api/v1/ocr/**")
                .excludePathPatterns("/api/v1/student/parent-control/**", "/api/v1/student/app-usage/**", "/api/v1/student/profile");
    }
}

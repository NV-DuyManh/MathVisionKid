package com.mathvisionkids.api.config;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import java.io.IOException;
import java.util.UUID;

@Component
public class RequestIdFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        
        HttpServletRequest req = (HttpServletRequest) request;
        HttpServletResponse res = (HttpServletResponse) response;

        String requestId = req.getHeader("X-Request-ID");
        if (requestId == null || requestId.isEmpty()) {
            requestId = UUID.randomUUID().toString();
        }
        
        req.setAttribute("X-Request-ID", requestId);
        res.setHeader("X-Request-ID", requestId);
        boolean quiz=req.getRequestURI().startsWith("/api/v1/student/quizzes");
        boolean tutor=req.getRequestURI().startsWith("/api/v1/student/tutor/lesson");
        if(quiz) {
            res.setHeader("X-MathVision-Instance",com.mathvisionkids.api.quiz.QuizRuntimeIdentity.INSTANCE);
            res.setHeader("X-Quiz-Generator",com.mathvisionkids.api.quiz.QuizMath.VERSION);
        }
        long started=System.nanoTime();
        try { chain.doFilter(request, response); }
        finally {
            if(quiz || tutor) {
                String agent=String.valueOf(req.getHeader("User-Agent"));
                String platform=agent.matches("(?is).*(iPhone|Darwin|CFNetwork|Expo).*")?"ios":"other";
                String client=String.valueOf(req.getHeader("X-MathVision-Client")).replaceAll("[^a-zA-Z0-9_.:-]","");
                if(client.length()>100) client=client.substring(0,100);
                String trace=String.valueOf(requestId).replaceAll("[^a-zA-Z0-9_-]","");
                if(trace.length()>100) trace=trace.substring(0,100);
                org.slf4j.LoggerFactory.getLogger(RequestIdFilter.class).info("{}_http request={} method={} route={} status={} durationMs={} remote={} platform={} client={} instance={}",quiz?"quiz":"tutor",trace,req.getMethod(),req.getRequestURI(),res.getStatus(),(System.nanoTime()-started)/1_000_000,req.getRemoteAddr(),platform,client,com.mathvisionkids.api.quiz.QuizRuntimeIdentity.INSTANCE);
            }
        }
    }
}

package com.mathvisionkids.api.auth;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.core.MethodParameter;
import org.springframework.core.ResolvableType;
import org.springframework.http.MediaType;
import org.springframework.http.HttpEntity;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.http.server.ServletServerHttpRequest;
import org.springframework.http.server.ServletServerHttpResponse;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.mvc.method.annotation.ResponseBodyAdvice;

@RestControllerAdvice
public class WebSessionResponseAdvice implements ResponseBodyAdvice<Object> {
    private final WebSessionService sessions;

    public WebSessionResponseAdvice(WebSessionService sessions) {
        this.sessions = sessions;
    }

    @Override
    public boolean supports(MethodParameter method, Class<? extends HttpMessageConverter<?>> converter) {
        var type = ResolvableType.forMethodParameter(method);
        return type.resolve() == AuthResponse.class || type.as(HttpEntity.class).getGeneric().resolve() == AuthResponse.class;
    }

    @Override
    public Object beforeBodyWrite(Object body, MethodParameter method, MediaType type,
                                  Class<? extends HttpMessageConverter<?>> converter,
                                  ServerHttpRequest request, ServerHttpResponse response) {
        if (!(body instanceof AuthResponse credentials) || !(request instanceof ServletServerHttpRequest servlet)
                || !(response instanceof ServletServerHttpResponse outgoing)) return body;
        HttpServletRequest incoming = servlet.getServletRequest();
        var client = WebSessionService.client(incoming);
        return client == null ? body : sessions.establish(credentials, client, incoming, outgoing.getServletResponse());
    }
}

package org.jejuro.miraero.mock_server.global.interceptor;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.jejuro.miraero.mock_server.global.exception.BusinessException;
import org.jejuro.miraero.mock_server.global.exception.ErrorCode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class ClientSecretInterceptor implements HandlerInterceptor {

    private static final String CLIENT_SECRET_HEADER = "X-Client-Secret";

    @Value("${mock.oauth.client-secret}")
    private String clientSecret;

    @Override
    public boolean preHandle(
            HttpServletRequest request,
            HttpServletResponse response,
            Object handler
    ) {
        String provided = request.getHeader(CLIENT_SECRET_HEADER);
        if (provided == null || !provided.equals(clientSecret)) {
            throw new BusinessException(ErrorCode.INVALID_CLIENT_SECRET);
        }
        return true;
    }
}

package org.jejuro.miraero.mock_server.global.interceptor;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.global.exception.BusinessException;
import org.jejuro.miraero.mock_server.global.exception.ErrorCode;
import org.jejuro.miraero.mock_server.oauth.service.OAuthService;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.HandlerMapping;

@Component
@RequiredArgsConstructor
public class BearerTokenInterceptor implements HandlerInterceptor {

    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";
    private static final String KB_USER_ID_VARIABLE = "kbUserId";

    private final OAuthService oAuthService;

    @Override
    public boolean preHandle(
            HttpServletRequest request,
            HttpServletResponse response,
            Object handler
    ) {
        String header = request.getHeader(AUTHORIZATION_HEADER);
        if (header == null || !header.startsWith(BEARER_PREFIX)) {
            throw new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN);
        }

        Long tokenKbUserId = oAuthService.resolveKbUserId(header.substring(BEARER_PREFIX.length()));
        Long pathKbUserId = extractPathKbUserId(request);

        if (pathKbUserId != null && !pathKbUserId.equals(tokenKbUserId)) {
            throw new BusinessException(ErrorCode.TOKEN_USER_MISMATCH);
        }
        return true;
    }

    @SuppressWarnings("unchecked")
    private Long extractPathKbUserId(HttpServletRequest request) {
        Object variables = request.getAttribute(HandlerMapping.URI_TEMPLATE_VARIABLES_ATTRIBUTE);
        if (!(variables instanceof Map)) {
            return null;
        }
        Object value = ((Map<String, String>) variables).get(KB_USER_ID_VARIABLE);
        if (value == null) {
            return null;
        }
        return Long.valueOf(value.toString());
    }
}

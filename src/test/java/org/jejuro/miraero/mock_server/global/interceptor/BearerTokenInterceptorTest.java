package org.jejuro.miraero.mock_server.global.interceptor;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

import java.util.Map;
import org.jejuro.miraero.mock_server.global.exception.BusinessException;
import org.jejuro.miraero.mock_server.oauth.service.OAuthService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.web.servlet.HandlerMapping;

@ExtendWith(MockitoExtension.class)
class BearerTokenInterceptorTest {

    @Mock
    private OAuthService oAuthService;

    private BearerTokenInterceptor interceptor;

    @BeforeEach
    void setUp() {
        interceptor = new BearerTokenInterceptor(oAuthService);
    }

    @Test
    @DisplayName("토큰의 사용자와 경로의 사용자가 같으면 통과한다")
    void preHandle_success() {
        when(oAuthService.resolveKbUserId("valid-token")).thenReturn(10001L);
        MockHttpServletRequest request = createRequest("Bearer valid-token", "10001");

        boolean result = interceptor.preHandle(request, new MockHttpServletResponse(), new Object());

        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("Authorization 헤더가 없으면 예외가 발생한다")
    void preHandle_missingHeader() {
        MockHttpServletRequest request = createRequest(null, "10001");

        assertThatThrownBy(
                () -> interceptor.preHandle(request, new MockHttpServletResponse(), new Object()))
                .isInstanceOf(BusinessException.class);
    }

    @Test
    @DisplayName("토큰의 사용자와 경로의 사용자가 다르면 예외가 발생한다")
    void preHandle_userMismatch() {
        when(oAuthService.resolveKbUserId("valid-token")).thenReturn(10001L);
        MockHttpServletRequest request = createRequest("Bearer valid-token", "20002");

        assertThatThrownBy(
                () -> interceptor.preHandle(request, new MockHttpServletResponse(), new Object()))
                .isInstanceOf(BusinessException.class);
    }

    private MockHttpServletRequest createRequest(String authorization, String kbUserId) {
        MockHttpServletRequest request = new MockHttpServletRequest();
        if (authorization != null) {
            request.addHeader("Authorization", authorization);
        }
        request.setAttribute(
                HandlerMapping.URI_TEMPLATE_VARIABLES_ATTRIBUTE,
                Map.of("kbUserId", kbUserId));
        return request;
    }
}

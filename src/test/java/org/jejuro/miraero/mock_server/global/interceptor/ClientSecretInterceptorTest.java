package org.jejuro.miraero.mock_server.global.interceptor;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.jejuro.miraero.mock_server.global.exception.BusinessException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.test.util.ReflectionTestUtils;

class ClientSecretInterceptorTest {

    private static final String EXPECTED_SECRET = "test-secret-value";

    private ClientSecretInterceptor interceptor;

    @BeforeEach
    void setUp() {
        interceptor = new ClientSecretInterceptor();
        ReflectionTestUtils.setField(interceptor, "clientSecret", EXPECTED_SECRET);
    }

    @Test
    @DisplayName("올바른 시크릿이면 통과한다")
    void preHandle_success() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("X-Client-Secret", EXPECTED_SECRET);

        boolean result = interceptor.preHandle(request, new MockHttpServletResponse(), new Object());

        assertThat(result).isTrue();
    }

    @Test
    @DisplayName("헤더가 없으면 예외가 발생한다")
    void preHandle_missingHeader() {
        MockHttpServletRequest request = new MockHttpServletRequest();

        assertThatThrownBy(
                () -> interceptor.preHandle(request, new MockHttpServletResponse(), new Object()))
                .isInstanceOf(BusinessException.class);
    }

    @Test
    @DisplayName("시크릿 값이 다르면 예외가 발생한다")
    void preHandle_wrongSecret() {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("X-Client-Secret", "wrong-value");

        assertThatThrownBy(
                () -> interceptor.preHandle(request, new MockHttpServletResponse(), new Object()))
                .isInstanceOf(BusinessException.class);
    }
}

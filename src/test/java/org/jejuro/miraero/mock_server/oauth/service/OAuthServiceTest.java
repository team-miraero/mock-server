package org.jejuro.miraero.mock_server.oauth.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

import org.jejuro.miraero.mock_server.global.exception.BusinessException;
import org.jejuro.miraero.mock_server.kbuser.domain.KbUser;
import org.jejuro.miraero.mock_server.kbuser.mapper.KbUserMapper;
import org.jejuro.miraero.mock_server.oauth.dto.response.TokenResponse;
import org.jejuro.miraero.mock_server.oauth.store.OAuthStore;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

@ExtendWith(MockitoExtension.class)
class OAuthServiceTest {

    private static final String EMAIL = "miraero01@test.com";
    private static final Long KB_USER_ID = 10001L;

    @Mock
    private KbUserMapper kbUserMapper;

    private OAuthService oAuthService;

    @BeforeEach
    void setUp() {
        oAuthService = new OAuthService(kbUserMapper, new OAuthStore());
        ReflectionTestUtils.setField(oAuthService, "authorizationCodeTtlSeconds", 300L);
        ReflectionTestUtils.setField(oAuthService, "accessTokenTtlSeconds", 3600L);
    }

    @Test
    @DisplayName("인증코드를 발급하고 토큰으로 교환하면 kbUserId를 반환한다")
    void issueAndExchange() {
        KbUser kbUser = new KbUser();
        ReflectionTestUtils.setField(kbUser, "kbUserId", KB_USER_ID);
        when(kbUserMapper.findByEmail(EMAIL)).thenReturn(kbUser);

        String code = oAuthService.issueAuthorizationCode(EMAIL);
        TokenResponse token = oAuthService.exchangeToken(code);

        assertThat(token.getKbUserId()).isEqualTo(KB_USER_ID);
        assertThat(token.getAccessToken()).isNotBlank();
        assertThat(oAuthService.resolveKbUserId(token.getAccessToken())).isEqualTo(KB_USER_ID);
    }

    @Test
    @DisplayName("등록되지 않은 이메일이면 예외가 발생한다")
    void issue_userNotFound() {
        when(kbUserMapper.findByEmail("nobody@example.com")).thenReturn(null);

        assertThatThrownBy(() -> oAuthService.issueAuthorizationCode("nobody@example.com"))
                .isInstanceOf(BusinessException.class);
    }

    @Test
    @DisplayName("인증코드는 1회만 교환할 수 있다")
    void exchange_codeIsSingleUse() {
        KbUser kbUser = new KbUser();
        ReflectionTestUtils.setField(kbUser, "kbUserId", KB_USER_ID);
        when(kbUserMapper.findByEmail(EMAIL)).thenReturn(kbUser);

        String code = oAuthService.issueAuthorizationCode(EMAIL);
        oAuthService.exchangeToken(code);

        assertThatThrownBy(() -> oAuthService.exchangeToken(code))
                .isInstanceOf(BusinessException.class);
    }

    @Test
    @DisplayName("유효하지 않은 액세스 토큰이면 예외가 발생한다")
    void resolve_invalidToken() {
        assertThatThrownBy(() -> oAuthService.resolveKbUserId("not-a-token"))
                .isInstanceOf(BusinessException.class);
    }
}

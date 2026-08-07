package org.jejuro.miraero.mock_server.oauth.service;

import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.global.exception.BusinessException;
import org.jejuro.miraero.mock_server.global.exception.ErrorCode;
import org.jejuro.miraero.mock_server.kbuser.domain.KbUser;
import org.jejuro.miraero.mock_server.kbuser.mapper.KbUserMapper;
import org.jejuro.miraero.mock_server.oauth.dto.response.TokenResponse;
import org.jejuro.miraero.mock_server.oauth.store.OAuthStore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class OAuthService {

    private final KbUserMapper kbUserMapper;
    private final OAuthStore oAuthStore;

    @Value("${mock.oauth.authorization-code-ttl-seconds:300}")
    private long authorizationCodeTtlSeconds;

    @Value("${mock.oauth.access-token-ttl-seconds:3600}")
    private long accessTokenTtlSeconds;

    public String issueAuthorizationCode(String email) {
        KbUser kbUser = kbUserMapper.findByEmail(email);
        if (kbUser == null) {
            throw new BusinessException(ErrorCode.KB_USER_NOT_FOUND);
        }

        String code = UUID.randomUUID().toString();
        oAuthStore.saveAuthorizationCode(code, kbUser.getKbUserId(), authorizationCodeTtlSeconds);
        return code;
    }

    public TokenResponse exchangeToken(String authorizationCode) {
        Long kbUserId = oAuthStore.consumeAuthorizationCode(authorizationCode);
        if (kbUserId == null) {
            throw new BusinessException(ErrorCode.INVALID_AUTHORIZATION_CODE);
        }

        String accessToken = UUID.randomUUID().toString();
        oAuthStore.saveAccessToken(accessToken, kbUserId, accessTokenTtlSeconds);

        return TokenResponse.builder()
                .accessToken(accessToken)
                .expiresIn(accessTokenTtlSeconds)
                .kbUserId(kbUserId)
                .build();
    }

    public Long resolveKbUserId(String accessToken) {
        Long kbUserId = oAuthStore.findKbUserIdByAccessToken(accessToken);
        if (kbUserId == null) {
            throw new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN);
        }
        return kbUserId;
    }

    public long getAuthorizationCodeTtlSeconds() {
        return authorizationCodeTtlSeconds;
    }
}

package org.jejuro.miraero.mock_server.oauth.dto.response;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class TokenResponse {

    private String accessToken;
    private Long expiresIn;
    private Long kbUserId;
}

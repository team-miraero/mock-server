package org.jejuro.miraero.mock_server.oauth.dto.response;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class AuthorizeResponse {

    private String authorizationCode;
    private Long expiresIn;
}

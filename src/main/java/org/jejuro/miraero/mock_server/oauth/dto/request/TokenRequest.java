package org.jejuro.miraero.mock_server.oauth.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
public class TokenRequest {

    @NotBlank(message = "인증코드는 필수입니다.")
    private String authorizationCode;
}

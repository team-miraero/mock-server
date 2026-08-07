package org.jejuro.miraero.mock_server.oauth.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.oauth.dto.request.AuthorizeRequest;
import org.jejuro.miraero.mock_server.oauth.dto.request.TokenRequest;
import org.jejuro.miraero.mock_server.oauth.dto.response.AuthorizeResponse;
import org.jejuro.miraero.mock_server.oauth.dto.response.TokenResponse;
import org.jejuro.miraero.mock_server.oauth.service.OAuthService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/mock/oauth")
public class OAuthController {

    private final OAuthService oAuthService;

    @PostMapping("/authorize")
    public AuthorizeResponse authorize(@Valid @RequestBody AuthorizeRequest request) {
        String code = oAuthService.issueAuthorizationCode(request.getEmail());

        return AuthorizeResponse.builder()
                .authorizationCode(code)
                .expiresIn(oAuthService.getAuthorizationCodeTtlSeconds())
                .build();
    }

    @PostMapping("/token")
    public TokenResponse token(@Valid @RequestBody TokenRequest request) {
        return oAuthService.exchangeToken(request.getAuthorizationCode());
    }
}

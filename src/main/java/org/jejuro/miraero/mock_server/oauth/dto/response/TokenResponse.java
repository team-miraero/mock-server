package org.jejuro.miraero.mock_server.oauth.dto.response;

import java.time.LocalDate;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class TokenResponse {

    private String accessToken;
    private Long expiresIn;
    private Long kbUserId;

    // 마이데이터 연동 시 본인확인 정보로 함께 내려주는 프로필. 실제 마이데이터도
    // 연동 시점에 이 정보를 제공하므로 별도 조회 API 없이 토큰 응답에 싣는다.
    private String name;
    private LocalDate birthDate;
    private Long monthlyIncome;
    private String companyName;
}

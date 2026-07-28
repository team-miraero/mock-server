package org.jejuro.miraero.mock_server.account.dto.response;


import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Getter
@Builder
public class AccountResponse {
    private Long accountId;

    // 금융기관 내부 사용자 식별자
    private Long kbUserId;

    // 금융기관 코드
    private String financialInstitutionCode;

    // 계좌 유형 (CHECKING, SAVING, DEPOSIT)
    private String accountType;

    // 계좌명
    private String accountName;

    // 계좌번호
    private String accountNumber;

    // 잔액
    private Long balance;

    // 계좌상태
    private String accountStatus;

    // 개설일
    private LocalDate openedAt;

    // 만기일
    private LocalDate maturityAt;

    // 이자율
    private BigDecimal interestRate;

    // 월 납입 한도
    private Long monthlyPaymentLimit;
}

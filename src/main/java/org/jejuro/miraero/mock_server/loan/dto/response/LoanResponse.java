package org.jejuro.miraero.mock_server.loan.dto.response;

import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Getter
@Builder
public class LoanResponse {
    private Long loanId;
    private Long kbUserId;
    private String loanName;
    private Long loanAmount;
    private Long remainingAmount;
    private BigDecimal interestRate;
    private LocalDate loanStartDate;
    private LocalDate maturityDate;
}

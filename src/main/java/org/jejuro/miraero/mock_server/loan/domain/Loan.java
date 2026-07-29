package org.jejuro.miraero.mock_server.loan.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.ToString;
import org.apache.ibatis.type.Alias;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Getter
@NoArgsConstructor
@ToString
@Alias("Loan")
public class Loan {
    private Long loanId;
    private Long kbUserId;
    private String loanName;
    private Long loanAmount;
    private Long remainingAmount;
    private BigDecimal interestRate;
    private LocalDate loanStartDate;
    private LocalDate maturityDate;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}

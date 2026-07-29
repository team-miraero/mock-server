package org.jejuro.miraero.mock_server.loan.controller;

import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.loan.dto.response.LoanResponse;
import org.jejuro.miraero.mock_server.loan.service.LoanService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/mock/loans")
public class LoanController {
    private final LoanService service;

    @GetMapping("/{kbUserId}")
    public List<LoanResponse> getLoans(
            @PathVariable Long kbUserId
    ){
        return service.getLoans(kbUserId)
                .stream()
                .map(loan ->
                        LoanResponse.builder()
                                .loanId(loan.getLoanId())
                                .kbUserId(loan.getKbUserId())
                                .loanName(loan.getLoanName())
                                .loanAmount(loan.getLoanAmount())
                                .remainingAmount(loan.getRemainingAmount())
                                .interestRate(loan.getInterestRate())
                                .loanStartDate(loan.getLoanStartDate())
                                .maturityDate(loan.getMaturityDate())
                                .build()
                ).toList();
    }
}

package org.jejuro.miraero.mock_server.account.controller;


import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.account.dto.response.AccountResponse;
import org.jejuro.miraero.mock_server.account.service.AccountService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/mock/accounts")
public class AccountController {

    private final AccountService service;

    @GetMapping("/{kbUserId}")
    public List<AccountResponse> getAccounts(
            @PathVariable Long kbUserId
    ){
        return service.getAccounts(kbUserId)
                .stream()
                .map(account ->
                        AccountResponse.builder()
                                .accountId(account.getAccountId())
                                .kbUserId(account.getKbUserId())
                                .financialInstitutionCode(account.getFinancialInstitutionCode())
                                .accountType(account.getAccountType())
                                .accountName(account.getAccountName())
                                .accountNumber(account.getAccountNumber())
                                .balance(account.getBalance())
                                .accountStatus(account.getAccountStatus())
                                .openedAt(account.getOpenedAt())
                                .maturityAt(account.getMaturityAt())
                                .interestRate(account.getInterestRate())
                                .monthlyPaymentLimit(account.getMonthlyPaymentLimit())
                                .build()
                        ).toList();
    }
}

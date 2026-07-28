package org.jejuro.miraero.mock_server.account.service;


import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.account.domain.Account;
import org.jejuro.miraero.mock_server.account.mapper.AccountMapper;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class AccountService {
    private final AccountMapper mapper;

    public List<Account> getAccounts(
            Long kbUserId
    ){
        return mapper.findAccounts(kbUserId);
    }
}

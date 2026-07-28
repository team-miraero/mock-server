package org.jejuro.miraero.mock_server.account.mapper;


import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.jejuro.miraero.mock_server.account.domain.Account;

import java.util.List;

@Mapper
public interface AccountMapper {

    List<Account> findAccounts(
            @Param("kbUserId") Long kbUserId
    );
}

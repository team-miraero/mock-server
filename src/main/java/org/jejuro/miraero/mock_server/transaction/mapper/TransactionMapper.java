package org.jejuro.miraero.mock_server.transaction.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.jejuro.miraero.mock_server.transaction.domain.Transaction;

import java.util.List;

@Mapper
public interface TransactionMapper {
    List<Transaction> findTransactions(@Param("kbUserId") Long kbUserId);
}

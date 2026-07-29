package org.jejuro.miraero.mock_server.transaction.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.jejuro.miraero.mock_server.transaction.domain.Transaction;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface TransactionMapper {
    List<Transaction> findTransactions(@Param("kbUserId") Long kbUserId);

    int insertTransaction(
            @Param("kbUserId") Long kbUserId,
            @Param("accountId") Long accountId,
            @Param("cardId") Long cardId,
            @Param("prepaidInstrumentId") Long prepaidInstrumentId,
            @Param("transactionType") String transactionType,
            @Param("amount") Long amount,
            @Param("balanceAfter") Long balanceAfter,
            @Param("transactedAt") LocalDateTime transactedAt,
            @Param("merchantName") String merchantName,
            @Param("categoryName") String categoryName
    );
}

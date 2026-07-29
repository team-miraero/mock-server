package org.jejuro.miraero.mock_server.transaction.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.ToString;
import org.apache.ibatis.type.Alias;

import java.time.LocalDateTime;

@Getter
@NoArgsConstructor
@ToString
@Alias("Transaction")
public class Transaction {
    private Long transactionId;
    private Long kbUserId;
    private Long accountId;
    private Long cardId;
    private Long prepaidInstrumentId;
    private String transactionType;
    private Long amount;
    private Long balanceAfter;
    private LocalDateTime transactedAt;
    private String merchantName;
    private String categoryName;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}

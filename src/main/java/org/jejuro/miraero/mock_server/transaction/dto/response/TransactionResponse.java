package org.jejuro.miraero.mock_server.transaction.dto.response;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
@Builder
public class TransactionResponse {
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
}

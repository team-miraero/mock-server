package org.jejuro.miraero.mock_server.transaction.dto.response;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class TransferResponse {

    private Long withdrawalTransactionId;
    private Long depositTransactionId;
    private String status;
}
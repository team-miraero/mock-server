package org.jejuro.miraero.mock_server.transaction.dto.request;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TransferRequest {

    private Long kbUserId;

    @NotNull(message = "출금 계좌는 필수입니다.")
    private Long withdrawalAccountId;

    @NotNull(message = "입금 계좌는 필수입니다.")
    private Long depositAccountId;

    @NotNull(message = "금액은 필수입니다.")
    @Positive(message = "금액은 0보다 커야 합니다.")
    private Long amount;

    @NotNull
    private LocalDateTime transactedAt;

    private String merchantName;
    private String categoryName;
}

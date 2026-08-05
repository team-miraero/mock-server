package org.jejuro.miraero.mock_server.transaction.service;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.LocalDateTime;
import org.jejuro.miraero.mock_server.account.domain.Account;
import org.jejuro.miraero.mock_server.account.mapper.AccountMapper;
import org.jejuro.miraero.mock_server.transaction.dto.request.TransferRequest;
import org.jejuro.miraero.mock_server.transaction.mapper.TransactionMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

@ExtendWith(MockitoExtension.class)
class TransactionServiceTest {

    @Mock
    private TransactionMapper transactionMapper;
    @Mock
    private AccountMapper accountMapper;

    private TransactionService transactionService;

    @BeforeEach
    void setUp() {
        transactionService = new TransactionService(transactionMapper, accountMapper);
    }

    @Test
    @DisplayName("이체는 출금·입금 거래를 모두 TRANSFER 유형으로 생성한다")
    void transfer_usesTransferTypeForBothSides() {
        when(accountMapper.findById(201L)).thenReturn(createAccount(1000000L));
        when(accountMapper.findById(202L)).thenReturn(createAccount(0L));

        transactionService.transfer(TransferRequest.builder()
                .kbUserId(10001L)
                .withdrawalAccountId(201L)
                .depositAccountId(202L)
                .amount(500000L)
                .transactedAt(LocalDateTime.of(2026, 8, 26, 10, 0))
                .merchantName("미래로 저금통")
                .categoryName(null)
                .build());

        verify(transactionMapper, times(2)).insertTransaction(
                any(), any(), any(), any(), eq("TRANSFER"), any(), any(), any(), any(), any());
        verify(transactionMapper, never()).insertTransaction(
                any(), any(), any(), any(), eq("DEPOSIT"), any(), any(), any(), any(), any());
        verify(transactionMapper, never()).insertTransaction(
                any(), any(), any(), any(), eq("WITHDRAWAL"), any(), any(), any(), any(), any());
    }

    private Account createAccount(Long balance) {
        Account account = new Account();
        ReflectionTestUtils.setField(account, "balance", balance);
        return account;
    }
}

package org.jejuro.miraero.mock_server.transaction.service;

import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.account.domain.Account;
import org.jejuro.miraero.mock_server.account.mapper.AccountMapper;
import org.jejuro.miraero.mock_server.global.exception.BusinessException;
import org.jejuro.miraero.mock_server.global.exception.ErrorCode;
import org.jejuro.miraero.mock_server.transaction.domain.Transaction;
import org.jejuro.miraero.mock_server.transaction.dto.request.TransferRequest;
import org.jejuro.miraero.mock_server.transaction.dto.response.TransferResponse;
import org.jejuro.miraero.mock_server.transaction.mapper.TransactionMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Objects;

@Service
@RequiredArgsConstructor
public class TransactionService {
    private final TransactionMapper transactionMapper;
    private final AccountMapper accountMapper;

    public List<Transaction> getTransactions(Long kbUserId) {
        return transactionMapper.findTransactions(kbUserId);
    }


    @Transactional
    public TransferResponse transfer(TransferRequest req) {

        validateRequest(req);

        accountMapper.decreaseBalance(
                req.getWithdrawalAccountId(),
                req.getAmount()
        );

        accountMapper.increaseBalance(
                req.getDepositAccountId(),
                req.getAmount()
        );

        transactionMapper.insertTransaction(
                req.getKbUserId(),
                req.getWithdrawalAccountId(),
                null,
                null,
                "TRANSFER",
                req.getAmount(),
                null,
                req.getTransactedAt(),
                req.getMerchantName(),
                req.getCategoryName()
        );

        transactionMapper.insertTransaction(
                req.getKbUserId(),
                req.getDepositAccountId(),
                null,
                null,
                "TRANSFER",
                req.getAmount(),
                null,
                req.getTransactedAt(),
                req.getMerchantName(),
                req.getCategoryName()
        );

        return TransferResponse.builder()
                .withdrawalTransactionId(req.getWithdrawalAccountId())
                .depositTransactionId(req.getDepositAccountId())
                .status("SUCCESS")
                .build();
    }

    private void validateRequest(TransferRequest req) {

        if (Objects.equals(
                req.getWithdrawalAccountId(),
                req.getDepositAccountId()
        )) {
            throw new BusinessException(ErrorCode.SAME_ACCOUNT_TRANSFER);
        }

        Account withdrawalAccount =
                accountMapper.findById(req.getWithdrawalAccountId());

        if (withdrawalAccount == null) {
            throw new BusinessException(ErrorCode.ACCOUNT_NOT_FOUND);
        }

        Account depositAccount =
                accountMapper.findById(req.getDepositAccountId());

        if (depositAccount == null) {
            throw new BusinessException(ErrorCode.ACCOUNT_NOT_FOUND);
        }

        if (withdrawalAccount.getBalance() < req.getAmount()) {
            throw new BusinessException(ErrorCode.INSUFFICIENT_BALANCE);
        }
    }
}

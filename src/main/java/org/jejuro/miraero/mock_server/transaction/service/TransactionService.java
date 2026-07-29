package org.jejuro.miraero.mock_server.transaction.service;

import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.transaction.domain.Transaction;
import org.jejuro.miraero.mock_server.transaction.mapper.TransactionMapper;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class TransactionService {
    private final TransactionMapper mapper;

    public List<Transaction> getTransactions(Long kbUserId) {
        return mapper.findTransactions(kbUserId);
    }
}

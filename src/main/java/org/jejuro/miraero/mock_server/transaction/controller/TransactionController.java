package org.jejuro.miraero.mock_server.transaction.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import org.jejuro.miraero.mock_server.transaction.dto.request.TransferRequest;
import org.jejuro.miraero.mock_server.transaction.dto.response.TransactionResponse;
import org.jejuro.miraero.mock_server.transaction.dto.response.TransferResponse;
import org.jejuro.miraero.mock_server.transaction.service.TransactionService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/mock/transactions")
public class TransactionController {
    private final TransactionService service;

    @GetMapping("/{kbUserId}")
    public List<TransactionResponse> getTransactions(
            @PathVariable Long kbUserId
    ){
        return service.getTransactions(kbUserId)
                .stream()
                .map(t ->
                        TransactionResponse.builder()
                                .transactionId(t.getTransactionId())
                                .kbUserId(t.getKbUserId())
                                .accountId(t.getAccountId())
                                .cardId(t.getCardId())
                                .prepaidInstrumentId(t.getPrepaidInstrumentId())
                                .transactionType(t.getTransactionType())
                                .amount(t.getAmount())
                                .balanceAfter(t.getBalanceAfter())
                                .transactedAt(t.getTransactedAt())
                                .merchantName(t.getMerchantName())
                                .categoryName(t.getCategoryName())
                                .build()
                ).toList();
    }

    @PostMapping("/transfers")
    public ResponseEntity<TransferResponse> transfer(@Valid @RequestBody TransferRequest req) {
        TransferResponse response = service.transfer(req);
        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(response);
    }
}

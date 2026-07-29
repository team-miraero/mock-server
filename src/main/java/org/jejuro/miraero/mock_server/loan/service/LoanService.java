package org.jejuro.miraero.mock_server.loan.service;

import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.loan.domain.Loan;
import org.jejuro.miraero.mock_server.loan.mapper.LoanMapper;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class LoanService {
    private final LoanMapper mapper;

    public List<Loan> getLoans(Long kbUserId) {
        return mapper.findLoans(kbUserId);
    }
}

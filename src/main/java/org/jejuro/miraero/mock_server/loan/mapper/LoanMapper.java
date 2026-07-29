package org.jejuro.miraero.mock_server.loan.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.jejuro.miraero.mock_server.loan.domain.Loan;

import java.util.List;

@Mapper
public interface LoanMapper {
    List<Loan> findLoans(@Param("kbUserId") Long kbUserId);
}

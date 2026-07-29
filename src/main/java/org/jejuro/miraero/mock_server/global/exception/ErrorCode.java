package org.jejuro.miraero.mock_server.global.exception;


import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;

@Getter
@RequiredArgsConstructor
public enum ErrorCode {

    INVALID_REQUEST(
            HttpStatus.BAD_REQUEST,
            "잘못된 요청입니다."
    ),

    RESOURCE_NOT_FOUND(
            HttpStatus.NOT_FOUND,
            "요청한 데이터를 찾을 수 없습니다."
    ),

    INTERNAL_SERVER_ERROR(
            HttpStatus.INTERNAL_SERVER_ERROR,
            "서버 오류가 발생했습니다."
    ),

    ACCOUNT_NOT_FOUND(
            HttpStatus.NOT_FOUND,
            "계좌를 찾을 수 없습니다."
    ),

    INSUFFICIENT_BALANCE(
            HttpStatus.BAD_REQUEST,
            "잔액이 부족합니다."
    ),
    SAME_ACCOUNT_TRANSFER(
            HttpStatus.BAD_REQUEST,
            "출금 계좌와 입금 계좌가 같습니다."
    );

    private final HttpStatus status;
    private final String message;
}

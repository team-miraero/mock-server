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
    ),
    KB_USER_NOT_FOUND(
            HttpStatus.NOT_FOUND,
            "등록되지 않은 사용자입니다."
    ),
    INVALID_AUTHORIZATION_CODE(
            HttpStatus.BAD_REQUEST,
            "인증코드가 유효하지 않거나 만료되었습니다."
    ),
    INVALID_ACCESS_TOKEN(
            HttpStatus.UNAUTHORIZED,
            "액세스 토큰이 유효하지 않거나 만료되었습니다."
    ),
    TOKEN_USER_MISMATCH(
            HttpStatus.FORBIDDEN,
            "토큰에 허용되지 않은 사용자의 데이터입니다."
    ),
    INVALID_CLIENT_SECRET(
            HttpStatus.UNAUTHORIZED,
            "클라이언트 인증에 실패했습니다."
    );

    private final HttpStatus status;
    private final String message;
}

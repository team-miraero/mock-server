# Miraero Mock Server

Miraero 금융 데이터 연동 테스트를 위한 Mock 금융 서버입니다.

실제 금융기관 API 연동 환경을 모사하여 계좌, 카드, 거래내역, 대출 등의 금융 데이터를 제공합니다.

Miraero Backend는 본 Mock Server를 통해 금융 데이터 조회 및 금융 거래 흐름을 테스트할 수 있습니다.

---

# 1. Tech Stack

* Java 17
* Spring
* MyBatis
* MySQL 8.0
* Docker

---

# 2. 실행 방법

## 2.1 Docker 실행

### .env 파일
docker-compose.yml 파일과 같은 디렉토리에 .env 파일을 생성하여 설정
```bash
MYSQL_ROOT_PASSWORD=
MYSQL_DATABASE=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_PORT=
```

MySQL 컨테이너 실행

```bash
docker compose up -d
```

컨테이너 확인

```bash
docker ps
```

---

## 2.2 Application 실행

Gradle 실행

```bash
./gradlew bootRun
```

또는 IDE에서 Spring Boot Application 실행

서버 기본 주소:

```
http://localhost:9000
```

---

# 3. Database

Mock Server는 금융기관 데이터를 관리합니다.

## Table

| Table              | Description |
| ------------------ | ----------- |
| kb_user            | 금융 사용자 정보   |
| account            | 계좌 정보       |
| card               | 카드 정보       |
| loan               | 대출 정보       |
| transaction        | 거래 내역       |
| prepaid_instrument | 선불 금융수단 정보  |

---

# 4. API 사용 방법

## 4.1 사용자 기준

모든 금융 데이터는 `kbUserId` 기준으로 관리됩니다.

예:

```
kbUserId = 1
```

해당 사용자의:

* 계좌
* 카드
* 거래내역
* 대출

데이터를 조회할 수 있습니다.

---

# 5. Account API

## 계좌 조회

### Request

```
GET /api/accounts/{kbUserId}
```

---

### Response

```json
[
  {
    "accountId": 1,
    "kbUserId" : 1,
    "financialInstitutionCode" : "004",
    "accountName": "KB 입출금통장",
    "accountNumber": "1234567890",
    "accountType": "SAVINGS",
    "balance": 1000000,
    "accountStatus": "ACTIVE",
    "openedAt" : "2020-01-01",
    "maturityAt" : null,
    "interestRate" : 1.2,
    "monthlyPaymentLimit" : null
  }
]
```

---

# 6. Card API

## 카드 조회

### Request

```
GET /api/cards/{kbUserId}
```

---

### Response

```json
[
  {
    "cardId": 1,
    "kbUserId": 1,
    "cardName": "KB 신용카드",
    "cardType": "CREDIT",
    "financialInstitutionCode" : "004"
  }
]
```

---

# 7. Transaction API

## 거래내역 조회

### Request

```
GET /api/transactions/{kbUserId}
```

---

### Response

```json
[
  {
    "transactionId": 1,
    "kbUserId" : 1,
    "accountId": 1,
    "cardId" : null,
    "prepaidInstrumentId": null,
    "transactionType": "WITHDRAWAL",
    "amount": 50000,
    "balanceAfter": 965000,
    "transactedAt": "2026-07-29T10:30:00",
    "merchantName": "스타벅스",
    "categoryName": "카페"
  }
]
```

---

# 8. Transfer API

Miraero에서 금융 거래 발생 시 Mock 금융 서버에 이체 요청을 보낼 수 있습니다.

이체 요청이 처리되면:

1. 출금 계좌 잔액 감소
2. 입금 계좌 잔액 증가
3. 출금 거래 생성
4. 입금 거래 생성

이 수행됩니다.

---

## 이체 요청

### Request

```
POST /api/transfers
```

---

### Body

```json
{
  "kbUserId": 10001,
  "withdrawalAccountNumber": "101",
  "depositAccountNumber": "102",
  "status": "SUCCESS"
}
```

---

### 처리 결과

출금 거래:

```json
{
  "transactionType": "WITHDRAWAL",
  "amount": 300000,
  "categoryName": "이체"
}
```

입금 거래:

```json
{
  "transactionType": "DEPOSIT",
  "amount": 300000,
  "categoryName": "이체"
}
```

---

# 9. Miraero Backend 연동 흐름

```
Miraero Backend
        |
        | HTTP API
        ↓
Mock Server
        |
        ↓
MySQL(Mock-Mysql)
```

---

## 금융 데이터 조회

```
Miraero
   |
   | GET /accounts
   |
   ↓
Mock Server
   |
   ↓
계좌 데이터 반환
```

---

## 금융 거래 처리

```
Miraero
   |
   | POST /transfers
   |
   ↓
Mock Server

- 계좌 잔액 변경
- Transaction 생성
```

---

# 10. 개발 참고사항

## Id
`account_id`는 Mock Server 내부 식별자입니다.

Miraero DB의 `account_id`와 다를 수 있으므로 외부 통신 시 ex_account_id를 사용하시길 바랍니다.

다른 테이블의 id 들도 동일하게 참고바랍니다.

---

## User Mapping

Miraero User와 Mock 금융 사용자는 별도로 관리합니다.

예:

```
Miraero User
    |
    | Mapping
    ↓
kb_user
```

연동 후 이름, 생년월일, 이메일 등으로 식별되어 발급받은 `kbUserId`를 기준으로 금융 데이터를 조회합니다.

---

# 11. Package Structure

```
mock-server
 ├── account
 │    ├── controller
 │    ├── service
 │    ├── mapper
 │    └── domain
 │
 ├── card
 │
 ├── transaction
 │
 ├── loan
 │
 ├── prepaidinstrument
 │
 └── global
```

---

# 12. API Base URL

Local:

```
http://localhost:9000
```

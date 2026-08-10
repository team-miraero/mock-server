# Miraero Mock Server

Miraero 금융 데이터 연동 테스트를 위한 Mock 금융 서버입니다.

실제 금융기관(KB) API 연동 환경을 모사하여 OAuth 인증, 계좌·카드·대출·거래·선불수단 조회, 계좌 이체 기능을 제공합니다.

Miraero Backend는 본 Mock Server를 통해 마이데이터 연동 흐름(인증코드 발급 → 토큰 교환 → 데이터 조회)과 금융 거래 흐름을 실제 규격에 가깝게 테스트할 수 있습니다.

---

# 1. Tech Stack

* Java 17
* Spring Boot 3.5.4
* MyBatis
* MySQL 8.0
* Docker

---

# 2. 실행 방법

## 2.1 Docker 실행 (MySQL)

`docker-compose.yml`과 같은 디렉토리에 `.env` 파일을 생성한다 (`.env.example` 참고).

```bash
# MySQL
MYSQL_PORT=
MYSQL_ROOT_PASSWORD=
MYSQL_DATABASE=
MYSQL_USER=
MYSQL_PASSWORD=

# Mock OAuth (server-to-server auth for /mock/oauth/**)
MOCK_OAUTH_CLIENT_SECRET=
```

| 키 | 설명 |
| --- | --- |
| `MYSQL_PORT` | 로컬에 이미 3306을 쓰는 MySQL이 있으면 다른 포트(예: 3307)로 지정 |
| `MOCK_OAUTH_CLIENT_SECRET` | backend가 `/mock/oauth/**` 호출 시 보내야 하는 고정 비밀값. **backend `.env`와 정확히 같은 값**이어야 하며 Git으로 공유하지 않는다(별도 채널로 직접 전달) |

MySQL 컨테이너 실행:

```bash
docker compose up -d
```

컨테이너 확인:

```bash
docker ps
```

시드 데이터를 초기 상태로 되돌리려면 볼륨을 지우고 재기동한다 (`docker/mysql/init/schema.sql`은 빈 볼륨에서만 실행됨):

```bash
docker compose down -v
docker compose up -d
```

## 2.2 Application 실행

`application.yml`이 `.env`의 값을 환경변수로 참조하므로(비밀값을 코드에 남기지 않기 위함), **`.env`를 export한 뒤** 애플리케이션을 실행해야 한다.

터미널:

```bash
set -a; source .env; set +a
./gradlew bootRun
```

IntelliJ 등 IDE에서 실행할 경우, Run Configuration의 **Environment variables**에 `.env`와 같은 값(`MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MOCK_OAUTH_CLIENT_SECRET`)을 직접 넣어야 한다. 이걸 빠뜨리면 `NumberFormatException` 또는 설정 값 해석 실패로 애플리케이션 기동 자체가 실패한다 — 의도된 동작이다(비밀값 누락 시 조용히 열려있는 상태로 뜨는 것을 막기 위함).

서버 기본 주소:

```
http://localhost:9000
```

---

# 3. Database

| Table | Description |
| --- | --- |
| `kb_user` | KB 사용자 정보 (`email`로 미래로 backend와 식별 매핑) |
| `account` | 계좌 정보 |
| `card` | 카드 정보 |
| `loan` | 대출 정보 |
| `transaction` | 거래 내역 |
| `prepaid_instrument` | 선불 금융수단 정보 |

모든 금융 데이터는 `kbUserId` 기준으로 관리된다.

---

# 4. 인증 흐름

이 서버는 두 종류의 요청 보호를 갖고 있고, **경로별로 요구하는 게 다르다.**

| 경로 | 요구하는 것 | 목적 |
| --- | --- | --- |
| `POST /mock/oauth/authorize`<br>`POST /mock/oauth/token` | `X-Client-Secret` 헤더 | 미래로 backend만 이 엔드포인트를 호출할 수 있게 함. 이메일은 비밀값이 아니므로, 이 검증이 없으면 이메일만 알아도 남의 kbUserId로 토큰을 발급받을 수 있음 |
| `GET /mock/accounts/**`<br>`GET /mock/cards/**`<br>`GET /mock/loans/**`<br>`GET /mock/transactions/**`<br>`GET /mock/prepaid-instruments/**`<br>`POST /mock/transactions/transfers` | `Authorization: Bearer <token>` 헤더 | 유효한 토큰이 있어야 조회 가능. 경로에 `{kbUserId}`가 있는 요청은 **토큰이 가리키는 사용자와 경로의 kbUserId가 일치해야** 함(다르면 403) |

## 4.1 전체 흐름

```
① POST /mock/oauth/authorize   (X-Client-Secret 필요)
   body: { "email": "miraero01@test.com" }
   → { "authorizationCode": "...", "expiresIn": 300 }
        │
        ▼ (5분 이내, 1회만 사용 가능)
② POST /mock/oauth/token       (X-Client-Secret 필요)
   body: { "authorizationCode": "..." }
   → { "accessToken": "...", "expiresIn": 3600, "kbUserId": 10001 }
        │
        ▼ (1시간 유효)
③ GET /mock/accounts/10001     (Authorization: Bearer <accessToken>)
   → 계좌 목록
```

## 4.2 실패 케이스

| 상황 | 응답 |
| --- | --- |
| `X-Client-Secret` 헤더 없음/불일치 | `401 INVALID_CLIENT_SECRET` |
| 등록되지 않은 이메일로 인증코드 요청 | `404 KB_USER_NOT_FOUND` |
| 존재하지 않거나 이미 사용된/만료된 인증코드로 토큰 교환 | `400 INVALID_AUTHORIZATION_CODE` |
| `Authorization` 헤더 없음/형식 오류/만료된 토큰 | `401 INVALID_ACCESS_TOKEN` |
| 유효한 토큰이지만 다른 사용자의 kbUserId 경로를 요청 | `403 TOKEN_USER_MISMATCH` |

인증코드는 **1회용**이다 — 토큰 교환에 성공하는 즉시 서버 메모리에서 삭제되며, 같은 코드로 재교환을 시도하면 `INVALID_AUTHORIZATION_CODE`가 발생한다.

---

# 5. API 목록

## 5.1 OAuth API

### 인증코드 발급

```
POST /mock/oauth/authorize
X-Client-Secret: <공유 비밀값>
Content-Type: application/json
```

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `email` | String | Y | `kb_user.email`과 일치해야 함 |

**Response**

```json
{
  "authorizationCode": "8f14e45f-ceea-4bd4-8e1e-1a7c8b7a5c9d",
  "expiresIn": 300
}
```

### 토큰 교환

```
POST /mock/oauth/token
X-Client-Secret: <공유 비밀값>
Content-Type: application/json
```

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `authorizationCode` | String | Y | `/authorize` 응답의 `authorizationCode` |

**Response**

```json
{
  "accessToken": "3b1c2e6a-7f4d-4a9b-9e2c-6d5f1a8b3c7e",
  "expiresIn": 3600,
  "kbUserId": 10001
}
```

## 5.2 Account API

### 계좌 조회

```
GET /mock/accounts/{kbUserId}
Authorization: Bearer <accessToken>
```

**Path Parameter**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `kbUserId` | Long | 토큰이 가리키는 kbUserId와 일치해야 함 |

**Response**

```json
[
  {
    "accountId": 201,
    "kbUserId": 10001,
    "financialInstitutionCode": "004",
    "accountType": "CHECKING",
    "accountName": "KB 입출금통장",
    "accountNumber": "1001234567",
    "balance": 2480000,
    "accountStatus": "ACTIVE",
    "openedAt": "2023-01-10",
    "maturityAt": null,
    "interestRate": 0.1000,
    "monthlyPaymentLimit": null
  },
  {
    "accountId": 231,
    "kbUserId": 10001,
    "financialInstitutionCode": "004",
    "accountType": "CHECKING",
    "accountName": "KB 비상금통장",
    "accountNumber": "1001345678",
    "balance": 1200000,
    "accountStatus": "ACTIVE",
    "openedAt": "2023-06-15",
    "maturityAt": null,
    "interestRate": 0.1000,
    "monthlyPaymentLimit": null
  }
]
```

(위 `balance`는 실제 시드 DB에서 조회한 값 — kbUserId 10001 기준. 응답은 예적금까지 포함해 4건이며 위는 입출금계좌 2건만 발췌한 것이다)

모든 사용자는 입출금계좌를 2개 갖는다. 주계좌(`KB 입출금통장`)에만 급여·고정지출·생활비 거래가 흐르고, 보조계좌(`KB 비상금통장`)는 거래 없이 잔액만 보유한다.

`accountType` 예시 값: `CHECKING`, `SAVINGS`, `DEPOSIT`, `INSTALLMENT` (시드 데이터 기준. DB에 별도 CHECK 제약은 없음)

## 5.3 Card API

### 카드 조회

```
GET /mock/cards/{kbUserId}
Authorization: Bearer <accessToken>
```

**Response**

```json
[
  {
    "cardId": 1,
    "kbUserId": 10001,
    "cardName": "KB 신용카드",
    "cardType": "CREDIT",
    "financialInstitutionCode": "004"
  }
]
```

현재 시드 데이터에는 카드가 없다 (계좌·거래 중심으로만 시드됨). 빈 배열이 정상 응답이다.

## 5.4 Loan API

### 대출 조회

```
GET /mock/loans/{kbUserId}
Authorization: Bearer <accessToken>
```

**Response**

```json
[
  {
    "loanId": 1,
    "kbUserId": 10001,
    "loanName": "KB 학자금대출",
    "loanAmount": 10000000,
    "remainingAmount": 6500000,
    "interestRate": 3.5,
    "loanStartDate": "2024-03-01",
    "maturityDate": "2029-03-01"
  }
]
```

현재 시드 데이터에는 대출이 없다. 빈 배열이 정상 응답이다.

## 5.5 Transaction API

### 거래내역 조회

```
GET /mock/transactions/{kbUserId}
Authorization: Bearer <accessToken>
```

**Response**

```json
[
  {
    "transactionId": 30163,
    "kbUserId": 10001,
    "accountId": 201,
    "cardId": null,
    "prepaidInstrumentId": null,
    "transactionType": "DEPOSIT",
    "amount": 2850000,
    "balanceAfter": 3897270,
    "transactedAt": "2026-05-25T10:00:00",
    "merchantName": "급여",
    "categoryName": null
  },
  {
    "transactionId": 30164,
    "kbUserId": 10001,
    "accountId": 201,
    "cardId": null,
    "prepaidInstrumentId": null,
    "transactionType": "PAYMENT",
    "amount": 16900,
    "balanceAfter": 3880370,
    "transactedAt": "2026-05-25T10:20:00",
    "merchantName": "멜론",
    "categoryName": "문화"
  }
]
```

(실제 시드 DB에서 조회한 kbUserId 10001의 첫 급여 입금과 그 직후 지출)

`transactionType`은 스키마상 `DEPOSIT`, `WITHDRAWAL`, `PAYMENT`, `TRANSFER`, `REFUND` 5종이 허용되지만, **현재 코드가 실제로 생성하는 값은 3종뿐이다**: 시드 데이터의 `DEPOSIT`(수입)·`PAYMENT`(지출), 그리고 `/transfers` 호출로 생성되는 `TRANSFER`(계좌 간 이체). `WITHDRAWAL`·`REFUND`는 스키마상 허용되나 현재 어떤 코드 경로도 생성하지 않는다.

### 이체 요청

계좌 간 자금 이동 시 사용한다 (예: 미래로 페이스메이커가 급여계좌 → 저금통으로 자동이체할 때).

```
POST /mock/transactions/transfers
Authorization: Bearer <accessToken>
Content-Type: application/json
```

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `kbUserId` | Long | N | 참고용. 아래 "이체 인가 관련 주의" 참고 |
| `withdrawalAccountId` | Long | Y | 출금 계좌의 내부 `account_id` |
| `depositAccountId` | Long | Y | 입금 계좌의 내부 `account_id` (출금 계좌와 달라야 함) |
| `amount` | Long | Y | 이체 금액. 0보다 커야 함 |
| `transactedAt` | LocalDateTime | Y | 거래 일시 |
| `merchantName` | String | N | 거래처명 (예: "미래로 저금통") |
| `categoryName` | String | N | 카테고리명 |

```json
{
  "kbUserId": 10001,
  "withdrawalAccountId": 201,
  "depositAccountId": 202,
  "amount": 500000,
  "transactedAt": "2026-08-25T10:00:00",
  "merchantName": "미래로 저금통",
  "categoryName": null
}
```

**Response** (`201 Created`)

```json
{
  "withdrawalTransactionId": 201,
  "depositTransactionId": 202,
  "status": "SUCCESS"
}
```

처리되면:
1. 출금 계좌 잔액 감소
2. 입금 계좌 잔액 증가
3. 출금 계좌에 `TRANSFER` 유형 거래 생성
4. 입금 계좌에 `TRANSFER` 유형 거래 생성

**오류**

| 상황 | 응답 |
| --- | --- |
| 출금 계좌 = 입금 계좌 | `400 SAME_ACCOUNT_TRANSFER` |
| 존재하지 않는 계좌 ID | `404 ACCOUNT_NOT_FOUND` |
| 출금 계좌 잔액 부족 | `400 INSUFFICIENT_BALANCE` |

**이체 인가 관련 주의**: 이 엔드포인트는 URL에 `{kbUserId}` 경로 변수가 없다(고정 경로 `/transfers`). Bearer 인터셉터는 경로에 `kbUserId`가 있을 때만 토큰의 사용자와 대조하므로, **이 엔드포인트는 유효한 토큰만 있으면 통과되고 body의 `kbUserId`와 토큰 소유자가 같은지는 검증하지 않는다.** 백엔드가 항상 정당한 사용자의 토큰으로만 이 API를 호출한다는 전제 위에서 동작한다.

## 5.6 Prepaid Instrument API

### 선불 금융수단 조회

```
GET /mock/prepaid-instruments/{kbUserId}
Authorization: Bearer <accessToken>
```

**Response**

```json
[
  {
    "prepaidInstrumentId": 1,
    "kbUserId": 10001,
    "prepaidInstrumentName": "KB Pay 포인트",
    "prepaidInstrumentType": "POINT",
    "financialInstitutionCode": "004"
  }
]
```

현재 시드 데이터에는 선불수단이 없다. 빈 배열이 정상 응답이다.

---

# 6. 오류 응답 형식

모든 오류는 아래 형식으로 반환된다 (`GlobalExceptionHandler`).

```json
{
  "code": "ACCOUNT_NOT_FOUND",
  "message": "계좌를 찾을 수 없습니다."
}
```

## 전체 에러코드

| code | HTTP Status | message |
| --- | --- | --- |
| `INVALID_REQUEST` | 400 | 잘못된 요청입니다. |
| `RESOURCE_NOT_FOUND` | 404 | 요청한 데이터를 찾을 수 없습니다. |
| `INTERNAL_SERVER_ERROR` | 500 | 서버 오류가 발생했습니다. |
| `ACCOUNT_NOT_FOUND` | 404 | 계좌를 찾을 수 없습니다. |
| `INSUFFICIENT_BALANCE` | 400 | 잔액이 부족합니다. |
| `SAME_ACCOUNT_TRANSFER` | 400 | 출금 계좌와 입금 계좌가 같습니다. |
| `KB_USER_NOT_FOUND` | 404 | 등록되지 않은 사용자입니다. |
| `INVALID_AUTHORIZATION_CODE` | 400 | 인증코드가 유효하지 않거나 만료되었습니다. |
| `INVALID_ACCESS_TOKEN` | 401 | 액세스 토큰이 유효하지 않거나 만료되었습니다. |
| `TOKEN_USER_MISMATCH` | 403 | 토큰에 허용되지 않은 사용자의 데이터입니다. |
| `INVALID_CLIENT_SECRET` | 401 | 클라이언트 인증에 실패했습니다. |

`@Valid` 검증 실패 시에는 `INVALID_REQUEST` 코드에 해당 필드의 검증 메시지가 담긴다 (예: `"이메일은 필수입니다."`).

---

# 7. Miraero Backend 연동 흐름

```
Miraero Backend
        |
        | ① POST /mock/oauth/authorize, /token (X-Client-Secret)
        ↓
Mock Server ── OAuthStore(메모리)에 인증코드·토큰 저장
        |
        | ② GET/POST (Authorization: Bearer)
        ↓
Mock Server
        |
        ↓
MySQL (mock-mysql)
```

## 연동 및 데이터 조회

```
Miraero Backend
   |
   | POST /mock/oauth/authorize → 인증코드
   | POST /mock/oauth/token     → 액세스토큰 + kbUserId
   |
   ↓
Mock Server
   |
   | GET /mock/accounts/{kbUserId} 등 (Bearer)
   ↓
계좌·거래 데이터 반환
```

## 금융 거래 처리

```
Miraero Backend
   |
   | POST /mock/transactions/transfers (Bearer)
   |
   ↓
Mock Server
   - 계좌 잔액 변경
   - 양쪽 계좌에 TRANSFER 거래 생성
```

---

# 8. 개발 참고사항

## Id

`account_id` 등은 Mock Server 내부 식별자다. Miraero backend DB의 내부 ID와 다르므로, backend는 이 값을 `ex_account_id`(외부 식별자)로 저장하고 자체 `account_id`와 분리해서 관리한다. 다른 테이블의 id도 동일하다.

## User Mapping

Miraero User와 Mock 금융 사용자는 별도로 관리되며, **이메일로 매핑**된다.

```
Miraero User (email)
    |
    | POST /mock/oauth/authorize { email }
    ↓
kb_user.email 조회 → kbUserId 발급
```

이후 조회는 이메일이 아니라 발급받은 `kbUserId` + 액세스토큰 기준으로 이루어진다.

## transaction_type 실제 사용 현황

스키마 코멘트는 `DEPOSIT, WITHDRAWAL, PAYMENT, TRANSFER, REFUND` 5종을 명시하지만, 현재 코드가 실제로 생성하는 값은 `DEPOSIT`(시드: 수입), `PAYMENT`(시드: 고정지출·생활비), `TRANSFER`(이체 API)뿐이다.

## 문자 인코딩

`docker/mysql/init/schema.sql` 최상단에 `SET NAMES utf8mb4;`가 있다. 이게 없으면 Docker 초기화 스크립트가 한글 데이터를 다른 문자셋으로 잘못 해석해 DB에 영구적으로 깨진 채 저장하는 문제가 있었다 (클라이언트 쪽 `SET NAMES`로는 복구 불가 — 저장 시점의 문제이기 때문). 이 파일을 수정할 때 이 줄을 지우지 않는다.

---

# 9. Package Structure

```
mock-server
 ├── account
 │    ├── controller / service / mapper / domain / dto
 ├── card
 ├── loan
 ├── transaction
 │    └── (계좌 이체 포함)
 ├── prepaidinstrument
 ├── kbuser
 │    └── 이메일 기반 사용자 조회
 ├── oauth
 │    ├── controller / service / store / dto
 │    └── OAuthStore가 인증코드·액세스토큰을 메모리에 보관
 └── global
      ├── config      (WebMvcConfig — 인터셉터 등록)
      ├── interceptor (ClientSecretInterceptor, BearerTokenInterceptor)
      ├── exception
      └── response
```

---

# 10. API Base URL

Local:

```
http://localhost:9000
```

---

# 11. 테스트 계정

모든 계정은 `POST /mock/oauth/authorize`에 아래 이메일을 넣어 연동한다.

모든 사용자는 **동일한 기간(2026-05-01 ~ 2026-08-10)의 거래내역**과 **입출금계좌 2개**를 갖는다. 마이데이터는 서비스 가입 시점과 무관하게 은행에 쌓인 거래내역 전체를 수신하므로, 사용자별로 보유 기간이 다를 이유가 없다.

| kbUserId | 이메일 | 월소득 | 예적금 | 특징 | 검증 목적 |
| --- | --- | --- | --- | --- | --- |
| 10001 | miraero01@test.com | 285만 | 적금·예금 | 표준 사회초년생 | 기본 시나리오 |
| 10002 | miraero02@test.com | 220만 | 적금 | 저소득 | 여유자금 소액 |
| 10003 | miraero03@test.com | 520만 | 예금·적금 | 고소득 | 코호트 상위 |
| 10004 | miraero04@test.com | 260만 | 적금 | 학자금 대출상환 25만 | 고정지출에 대출 포함 |
| 10005 | miraero05@test.com | 300만 | 적금 | 월세 75만 | 고정지출 과다 |
| 10006 | miraero06@test.com | 270만 | 적금 | 부모 동거, 주거비 없음 | 소득 대비 여유 큼 |
| 10007 | miraero07@test.com | 290만 | 적금 | 과소비 | **사이클 기준 여유자금 음수** |
| 10008 | miraero08@test.com | 310만 | 적금·예금 | 적금·펀드 자동이체 3건 | 저축이 고정지출로 차감되는지 |
| 10009 | miraero09@test.com | 330만 | 적금 | 프리랜서, 수입 3건 | **급여일 역추론 실패 → 폴백 경로** |
| 10010 | miraero10@test.com | 250만 | **없음** | 신규 가입, 저축 안 함 | **목표에 연결할 자산 없음** |
| 10011 | miraero11@test.com | 240만 | 적금 | 이번 달 예산 소진 | **여유자금 정확히 0원** |

10001·10002·10004·10006·10007은 연령·소득 구간이 겹쳐 또래평균 코호트를 형성한다.

**여유자금은 조회 시점에 따라 달라진다.** 백엔드는 `마지막 급여일 ~ 다음 급여일` 구간으로 계산하는데, 시드 데이터가 8/10에서 끊기므로 현재 주기(7/25~8/25)는 절반만 채워져 있다. 그래서 사이클 전체로는 여유자금이 음수인 10007도 **지금 조회하면 +81만원**으로 나온다. "쓸 돈이 하나도 남지 않은" 화면을 보려면 10011을 쓴다 (현재 주기 기준 정확히 0원).

| kbUserId | 현재 주기(7/25~) 기준 | 한 사이클(6/25~7/24) 기준 |
| --- | --- | --- |
| 10011 김빠듯 | **0** | 108,070 |
| 10002 이초년 | 544,110 | 100,700 |
| 10004 최학자 | 725,510 | 780 |
| 10010 뉴가입 | 794,680 | -32,140 |
| 10007 오소비 | 810,610 | **-183,260** |
| 10003 박고소 | 2,101,640 | 789,120 |

각 계좌의 상세(계좌번호·잔액 등)는 `docker/mysql/init/schema.sql`의 시드 데이터, 또는 `tools/generate-seed.py` 상단 `DATA_START`/`DATA_END` 값을 바꿔 재생성한 결과를 참고한다.

#!/usr/bin/env python3
"""
generate-seed.py — 목 금융 데이터(`kb_user` 21건, `account` 60건,
`transaction` 약 9,490건) 생성기.

무엇을 하는가
-------------
`docker/mysql/init/schema.sql`에 그대로 붙여넣을 세 개의 `INSERT` 문
(`kb_user`, `account`, `transaction`)을 표준 출력으로 만들어낸다. 3,100여 건의
`balance_after` 누적, `transaction_id` 대역, 급여-고정지출 순서를 손으로
맞추면 반드시 틀리기 때문에 이 스크립트로 생성한다. Docker init 스크립트는
`.sql` 파일만 실행하므로(파이썬을 실행할 수 없으므로) `schema.sql`에는 이
스크립트의 출력을 "그대로 복사해 넣은 리터럴 SQL"이 최종 산출물로 커밋되어
있다. 즉 이 스크립트를 실행하지 않아도 `docker compose up`은 정상 동작한다 —
이 스크립트는 재생성이 필요할 때(날짜 갱신, 사용자 추가 등)만 쓴다.

`account.balance`는 손으로 고정하지 않는다. 각 계좌의 시간순 마지막 거래
`balance_after`를 스크립트가 직접 추적해서 그 값을 `account.balance`로 쓴다
(거래가 없는 계좌 — 저축/예금/적금, 그리고 보조 입출금계좌 — 만 원래 시드
값을 유지한다). 그래야 `account.balance`(현재 잔액)와 `transaction` 원장을
합산한 값이 항상 일치한다.

기간 모델
---------
거래는 `DATA_START` ~ `DATA_END` 구간에 대해 **전 사용자 공통으로** 생성한다.
마이데이터 연동은 서비스 가입 시점과 무관하게 은행에 쌓인 거래내역 전체를
수신하므로, 사용자별로 보유 기간이 다를 이유가 없다.

`DATA_END`는 "미래 거래"를 만들지 않기 위한 상한이다. 백엔드의 급여 조회
쿼리에는 `transacted_at <= NOW()` 가드가 있지만 지출 합산 쿼리에는 없어서,
아직 발생하지 않은 지출이 여유자금 계산에 그대로 집계되기 때문이다.

급여일(`PAYDAY`)은 25일 고정이다. 백엔드
`AvailableMoneyServiceImpl.resolveOriginalPayDay`가 최근 급여 3건의 일자를
보고 급여일을 역추론하므로, 매월 같은 일자에 급여가 찍혀야 다음 급여일이
정확히 계산된다. 고정지출(주거/통신/보험/구독/저축/투자)은 급여일 이후
1~9일에 배치되고, 첫 급여일 이전 구간(`DATA_START` ~ 첫 급여일 전날)에는
생활비만 배치된다 — 그 구간의 고정지출은 직전 달 급여 주기에 속해
구간 밖이기 때문이며, 덕분에 "급여가 고정지출보다 선행" 불변조건이
자연스럽게 유지된다.

계좌 구성
---------
모든 사용자는 입출금계좌를 2개 갖는다. 주계좌(급여계좌)에 급여·고정지출·
생활비가 모두 흐르고, 보조계좌(비상금)에는 **거래를 넣지 않는다**. 백엔드의
지출 합산 쿼리가 `account_id`가 아니라 `user_id` 기준이라, 보조계좌에 지출을
넣으면 소비 분석·여유자금 계산에 그대로 섞이기 때문이다. 보조계좌는 목표가
밀렸을 때 자금을 끌어오는("끌어쓰기") 대상으로 노출되는 것이 목적이므로
잔액만 유의미하게 보유한다.

예적금은 10010(뉴가입)만 미보유다. 저축 계좌가 없으므로 10010의 고정지출
에서도 저축·투자 자동이체를 함께 뺀다.

여유자금 목표
-------------
화면에 뜨는 여유자금은 '마지막 급여일~다음 급여일' 구간 기준인데, 데이터가
`DATA_END`에서 끊기므로 이 구간은 늘 부분적으로만 채워진다. 그래서 한 사이클
전체로는 여유자금이 음수인 사용자도 시연 시점 화면에서는 양수로 보인다.
화면값 자체가 시나리오인 경우(10011: 여유자금 0원)에만 프로필에
`available_now`를 지정해 해당 구간 변동지출을 역산 보정한다.

사용 방법
---------
표준 라이브러리(`datetime`, `random`)만 사용한다. 추가 설치 불필요.

    cd miraero-mock-server
    python3 tools/generate-seed.py > /tmp/seed_values.sql

- 표준 출력(stdout): `INSERT INTO \\`kb_user\\` ... VALUES ...;`,
  `INSERT INTO \\`account\\` ... VALUES ...;`, `INSERT INTO \\`transaction\\` ...
  VALUES ...;` 세 문장을 순서대로 출력한다. `schema.sql`의 해당 세 블록을
  이 출력으로 통째로 교체하면 된다.
- 표준 에러(stderr): 사용자별/구간별 수입·고정지출·생활비·여유자금 요약과
  전수 sanity-check(카테고리·타입 규칙, 급여 선행, 잔액 비음수, ID 대역 미충돌,
  미래 거래 없음, 계좌 최종 잔액) 통과 여부.
  `python3 tools/generate-seed.py 1>/dev/null`로 요약만 볼 수 있다.

기간 갱신
---------
아래 `DATA_START` / `DATA_END` 두 상수만 바꾸면 전체 거래 기간이 이동한다.
급여일과 구간 분할은 두 상수로부터 자동 계산된다. 시연 직전에 데이터를
"오늘까지"로 되돌리고 싶으면 `DATA_END`를 그날로 바꾸고 다시 실행하면 된다.

현재 커밋된 `schema.sql`의 시드는 `DATA_START = 2026-03-01`,
`DATA_END = 2026-08-10`으로 생성한 결과다.

시연 페르소나
-------------
10012~10016(탁민주), 10017~10021(송승윤)은 시연 시나리오용이다. 진행률
단계마다 계정을 나눴을 뿐 같은 사람이므로 소비 패턴 파라미터는 계정별로
`scale`만 다르다. 탁민주는 저축계좌 잔액이 곧 목표 진행률이고, 송승윤은
월세가 없어 여유자금이 넉넉한데도 예산을 초과 소비해 적립이 안 되는
상태에서 점차 회복하는 흐름을 `scale` 차등으로 표현한다.
"""

import datetime
import random
import sys
from collections import Counter

# =================================================================
# 데이터 구간 — 이 두 상수만 바꾸면 전체 거래 기간이 이동한다.
# DATA_END는 "미래 거래를 만들지 않기 위한" 상한이다(포함).
# =================================================================
DATA_START = datetime.date(2026, 3, 1)
DATA_END = datetime.date(2026, 8, 10)

# 급여일. 백엔드가 최근 급여 3건의 일자로 급여일을 역추론하므로 매월 고정이어야 한다.
PAYDAY = 25

ONE_DAY = datetime.timedelta(days=1)


def salary_dates(start, end, payday):
    """start~end 구간에 들어오는 매월 payday 날짜를 순서대로 반환한다."""
    out = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        try:
            d = datetime.date(year, month, payday)
        except ValueError:
            d = None
        if d is not None and start <= d <= end:
            out.append(d)
        month += 1
        if month > 12:
            month = 1
            year += 1
    return out


SALARY_DATES = salary_dates(DATA_START, DATA_END, PAYDAY)


def build_segments():
    """생활비를 흩뿌릴 구간들을 급여일 경계로 나눠 반환한다.

    첫 구간(DATA_START ~ 첫 급여일 전날)은 직전 달 급여 주기의 꼬리라
    생활비만 들어간다."""
    segs = []
    prev = DATA_START
    for s in SALARY_DATES:
        if s > prev:
            segs.append((prev, s - ONE_DAY))
        prev = s
    segs.append((prev, DATA_END))
    return segs


SEGMENTS = build_segments()


FIXED_CATS = {'주거', '통신', '보험', '구독', '대출상환', '저축', '투자'}


def dt(base_date, offset, hour, minute):
    d = base_date + datetime.timedelta(days=offset)
    return datetime.datetime(d.year, d.month, d.day, hour, minute)


def tune_available_now(rows, monthly_income, target, uid):
    """현재 급여주기의 여유자금이 정확히 target이 되도록 변동지출을 보정한다.

    화면에 뜨는 여유자금은 '마지막 급여일 ~ 다음 급여일' 구간의 계산 결과인데,
    데이터가 DATA_END에서 끊기므로 이 구간은 항상 부분적으로만 채워진다. 그래서
    한 사이클 전체 기준으로 지출을 맞춰도 시연 시점 화면값은 전혀 다른 값이 된다.
    '여유자금이 바닥난 사용자'처럼 화면값 자체가 시나리오인 경우에만 쓴다."""
    period_start = datetime.datetime.combine(SALARY_DATES[-1], datetime.time(8, 0))
    current = [r for r in rows if r['transacted_at'] >= period_start and r['ttype'] == 'PAYMENT']
    fixed_now = sum(r['amount'] for r in current if r['category'] in FIXED_CATS)
    var_rows = [r for r in current if r['category'] not in FIXED_CATS]
    var_now = sum(r['amount'] for r in var_rows)

    target_var = monthly_income - fixed_now - target
    assert var_rows and var_now > 0, f"user {uid}: 보정할 변동지출이 없다"
    assert target_var > 0, \
        f"user {uid}: 고정지출({fixed_now})만으로 이미 소득({monthly_income})을 넘어 target={target} 불가"

    factor = target_var / var_now
    for r in var_rows:
        r['amount'] = max(100, int(round(r['amount'] * factor / 10)) * 10)

    # 반올림 잔차는 가장 큰 건에 흡수시켜 합계를 정확히 맞춘다.
    biggest = max(var_rows, key=lambda r: r['amount'])
    biggest['amount'] += target_var - sum(r['amount'] for r in var_rows)
    assert biggest['amount'] > 0, f"user {uid}: 보정 후 금액이 0 이하"


def sqlval(v):
    if v is None:
        return 'NULL'
    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"
    return str(v)


# =================================================================
# kb_user / account 정적 시드 데이터.
# account의 balance만 아래에서 계좌별 원장 최종 balance_after로 덮어쓴다
# (거래가 없는 계좌 — 저축/예금/적금, 보조 입출금계좌 — 는 이 기본값을 그대로 쓴다).
# =================================================================
KB_USERS = [
    (10001, '김미래', '2001-03-15', 'miraero01@test.com', 'KB금융그룹', 2850000),
    (10002, '이초년', '2002-07-22', 'miraero02@test.com', '스타트업A', 2200000),
    (10003, '박고소', '1997-02-10', 'miraero03@test.com', '대기업B', 5200000),
    (10004, '최학자', '2000-11-05', 'miraero04@test.com', '중소기업C', 2600000),
    (10005, '정월세', '2001-09-18', 'miraero05@test.com', 'IT기업D', 3000000),
    (10006, '한본가', '2002-04-30', 'miraero06@test.com', '공공기관E', 2700000),
    (10007, '오소비', '2001-06-12', 'miraero07@test.com', '유통사F', 2900000),
    (10008, '신저축', '2000-01-25', 'miraero08@test.com', '금융사G', 3100000),
    (10009, '프리랜', '1998-08-08', 'miraero09@test.com', None, 3300000),
    (10010, '뉴가입', '2003-03-03', 'miraero10@test.com', '스타트업H', 2500000),
    (10011, '김빠듯', '2001-12-09', 'miraero11@test.com', '중소기업I', 2400000),

    # --- 시연 시나리오용 페르소나 ---
    # 진행률 단계(0/28/59/82/98%, 0/20/45/70/92%)마다 계정을 따로 둔다.
    # 백엔드 account.ex_account_id가 전역 UNIQUE라 여러 계정이 같은 목서버
    # 계좌를 동기화하면 기존 행을 덮어쓰기 때문에 kb_user를 계정마다 나눈다.
    (10012, '탁민주', '1999-04-18', 'minjoo1@naver.com', '중견기업J', 2850000),
    (10013, '탁민주', '1999-04-18', 'minjoo2@naver.com', '중견기업J', 2850000),
    (10014, '탁민주', '1999-04-18', 'minjoo3@naver.com', '중견기업J', 2850000),
    (10015, '탁민주', '1999-04-18', 'minjoo4@naver.com', '중견기업J', 2850000),
    (10016, '탁민주', '1999-04-18', 'minjoo5@naver.com', '중견기업J', 2850000),
    (10017, '송승윤', '2002-10-07', 'lssyl1@naver.com', '스타트업K', 2400000),
    (10018, '송승윤', '2002-10-07', 'lssyl2@naver.com', '스타트업K', 2400000),
    (10019, '송승윤', '2002-10-07', 'lssyl3@naver.com', '스타트업K', 2400000),
    (10020, '송승윤', '2002-10-07', 'lssyl4@naver.com', '스타트업K', 2400000),
    (10021, '송승윤', '2002-10-07', 'lssyl5@naver.com', '스타트업K', 2400000),
]

INCOME_BY_USER = {u[0]: u[5] for u in KB_USERS}

# (account_id, kb_user_id, fi_code, account_type, account_name, account_number,
#  default_balance, status, opened_at, maturity_at, interest_rate, monthly_payment_limit)
# default_balance는 그 계좌에 거래가 하나도 없을 때만 최종 balance로 쓰인다.
ACCOUNTS_META = [
    # --- 주계좌(급여계좌) — 급여·고정지출·생활비가 전부 이 계좌로 흐른다 ---
    (201, 10001, '004', 'CHECKING', 'KB 입출금통장', '1001234567', 3400000, 'ACTIVE', '2023-01-10', None, '0.1000', None),
    (203, 10002, '004', 'CHECKING', 'KB 입출금통장', '1002234567', 820000, 'ACTIVE', '2024-03-02', None, '0.1000', None),
    (204, 10003, '004', 'CHECKING', 'KB 입출금통장', '1003234567', 12400000, 'ACTIVE', '2021-05-11', None, '0.1000', None),
    (206, 10004, '004', 'CHECKING', 'KB 입출금통장', '1004234567', 1450000, 'ACTIVE', '2023-09-14', None, '0.1000', None),
    (207, 10005, '004', 'CHECKING', 'KB 입출금통장', '1005234567', 2100000, 'ACTIVE', '2023-04-20', None, '0.1000', None),
    (208, 10006, '004', 'CHECKING', 'KB 입출금통장', '1006234567', 5300000, 'ACTIVE', '2024-01-08', None, '0.1000', None),
    (209, 10007, '004', 'CHECKING', 'KB 입출금통장', '1007234567', 310000, 'ACTIVE', '2023-11-30', None, '0.1000', None),
    (210, 10008, '004', 'CHECKING', 'KB 입출금통장', '1008234567', 4200000, 'ACTIVE', '2022-08-19', None, '0.1000', None),
    (212, 10009, '004', 'CHECKING', 'KB 입출금통장', '1009234567', 2750000, 'ACTIVE', '2022-12-05', None, '0.1000', None),
    (213, 10010, '004', 'CHECKING', 'KB 입출금통장', '1010234567', 640000, 'ACTIVE', '2026-07-20', None, '0.1000', None),
    (241, 10011, '004', 'CHECKING', 'KB 입출금통장', '1011234567', 700000, 'ACTIVE', '2024-07-11', None, '0.1000', None),

    # --- 예적금 — 목표 자산 연결(goal_asset ACCOUNT) 시나리오용. 거래내역 없음 ---
    # 10010(뉴가입)만 예적금을 갖지 않는다 ("연결할 자산이 없는 사용자" 시연 케이스).
    (202, 10001, '004', 'SAVINGS', 'KB 청년적금', '1009876543', 1200000, 'ACTIVE', '2025-06-01', '2027-06-01', '3.5000', 500000),
    (214, 10001, '004', 'DEPOSIT', 'KB 목돈예치예금', '1001987654', 2000000, 'ACTIVE', '2024-11-01', '2026-11-01', '3.0000', None),
    (215, 10002, '004', 'SAVINGS', 'KB 씨앗적금', '1002987654', 350000, 'ACTIVE', '2025-09-01', '2027-09-01', '3.6000', 200000),
    (205, 10003, '004', 'DEPOSIT', 'KB 정기예금', '1003987654', 20000000, 'ACTIVE', '2025-01-05', '2027-01-05', '3.2000', None),
    (216, 10003, '004', 'SAVINGS', 'KB 골드적금', '1003876543', 5000000, 'ACTIVE', '2024-06-01', '2026-06-01', '3.4000', 1000000),
    (217, 10004, '004', 'SAVINGS', 'KB 학자금상환적금', '1004987654', 600000, 'ACTIVE', '2025-03-01', '2027-03-01', '3.5000', 300000),
    (218, 10005, '004', 'SAVINGS', 'KB 전세마련적금', '1005987654', 900000, 'ACTIVE', '2024-08-01', '2027-08-01', '3.7000', 400000),
    (219, 10006, '004', 'SAVINGS', 'KB 청년희망적금', '1006987654', 2000000, 'ACTIVE', '2024-02-01', '2027-02-01', '4.0000', 500000),
    (220, 10007, '004', 'SAVINGS', 'KB 자유적금', '1007987654', 50000, 'ACTIVE', '2024-12-01', '2026-12-01', '3.0000', 300000),
    (211, 10008, '004', 'INSTALLMENT', 'KB 목돈모으기적금', '1008987654', 3600000, 'ACTIVE', '2025-02-01', '2027-02-01', '3.8000', 600000),
    (221, 10008, '004', 'DEPOSIT', 'KB 정기예금', '1008876543', 3000000, 'ACTIVE', '2025-04-01', '2027-04-01', '3.2000', None),
    (222, 10009, '004', 'SAVINGS', 'KB 프리랜서적금', '1009987654', 700000, 'ACTIVE', '2024-10-01', '2026-10-01', '3.5000', 400000),
    (223, 10011, '004', 'SAVINGS', 'KB 새출발적금', '1011987654', 420000, 'ACTIVE', '2025-11-01', '2027-11-01', '3.6000', 200000),

    # --- 보조 입출금계좌(비상금) — 거래 없음, 목표가 밀렸을 때 끌어쓰기 대상 ---
    # 지출 합산이 user_id 기준이라 여기에 지출을 넣으면 소비 분석에 섞이므로 잔액만 둔다.
    (231, 10001, '004', 'CHECKING', 'KB 비상금통장', '1001345678', 1200000, 'ACTIVE', '2023-06-15', None, '0.1000', None),
    (232, 10002, '004', 'CHECKING', 'KB 비상금통장', '1002345678', 350000, 'ACTIVE', '2024-05-20', None, '0.1000', None),
    (233, 10003, '004', 'CHECKING', 'KB 비상금통장', '1003345678', 3000000, 'ACTIVE', '2021-09-03', None, '0.1000', None),
    (234, 10004, '004', 'CHECKING', 'KB 비상금통장', '1004345678', 500000, 'ACTIVE', '2023-11-27', None, '0.1000', None),
    (235, 10005, '004', 'CHECKING', 'KB 비상금통장', '1005345678', 800000, 'ACTIVE', '2023-08-09', None, '0.1000', None),
    (236, 10006, '004', 'CHECKING', 'KB 비상금통장', '1006345678', 1500000, 'ACTIVE', '2024-04-16', None, '0.1000', None),
    (237, 10007, '004', 'CHECKING', 'KB 비상금통장', '1007345678', 300000, 'ACTIVE', '2024-02-22', None, '0.1000', None),
    (238, 10008, '004', 'CHECKING', 'KB 비상금통장', '1008345678', 2000000, 'ACTIVE', '2022-12-01', None, '0.1000', None),
    (239, 10009, '004', 'CHECKING', 'KB 비상금통장', '1009345678', 1000000, 'ACTIVE', '2023-03-14', None, '0.1000', None),
    (240, 10010, '004', 'CHECKING', 'KB 비상금통장', '1010345678', 600000, 'ACTIVE', '2026-07-28', None, '0.1000', None),
    (242, 10011, '004', 'CHECKING', 'KB 비상금통장', '1011345678', 180000, 'ACTIVE', '2024-09-05', None, '0.1000', None),
    # --- 시연 페르소나: 탁민주(10012~10016) — 급여/비상금/저축계좌 3개씩 ---
    # 저축계좌 잔액이 곧 목표 진행률이다(목표 2,000만원 대비 0/28/59/82/98%).
    # 백엔드는 이 계좌를 ACCOUNT 타입 목표 자산으로 연결한다.
    (301, 10012, '004', 'CHECKING', 'KB 입출금통장', '2012123456', 2100000, 'ACTIVE', '2023-05-02', None, '0.1000', None),
    (302, 10012, '004', 'CHECKING', 'KB 비상금통장', '2012223456', 800000, 'ACTIVE', '2024-02-14', None, '0.1000', None),
    (303, 10012, '004', 'SAVINGS', 'KB 전세드림적금', '2012323456', 0, 'ACTIVE', '2024-09-01', '2028-08-31', '3.8000', 1000000),
    (304, 10013, '004', 'CHECKING', 'KB 입출금통장', '2013123456', 2300000, 'ACTIVE', '2023-05-02', None, '0.1000', None),
    (305, 10013, '004', 'CHECKING', 'KB 비상금통장', '2013223456', 900000, 'ACTIVE', '2024-02-14', None, '0.1000', None),
    (306, 10013, '004', 'SAVINGS', 'KB 전세드림적금', '2013323456', 5600000, 'ACTIVE', '2024-09-01', '2028-08-31', '3.8000', 1000000),
    (307, 10014, '004', 'CHECKING', 'KB 입출금통장', '2014123456', 2500000, 'ACTIVE', '2023-05-02', None, '0.1000', None),
    (308, 10014, '004', 'CHECKING', 'KB 비상금통장', '2014223456', 1000000, 'ACTIVE', '2024-02-14', None, '0.1000', None),
    (309, 10014, '004', 'SAVINGS', 'KB 전세드림적금', '2014323456', 11800000, 'ACTIVE', '2024-09-01', '2028-08-31', '3.8000', 1000000),
    (310, 10015, '004', 'CHECKING', 'KB 입출금통장', '2015123456', 2400000, 'ACTIVE', '2023-05-02', None, '0.1000', None),
    (311, 10015, '004', 'CHECKING', 'KB 비상금통장', '2015223456', 1100000, 'ACTIVE', '2024-02-14', None, '0.1000', None),
    (312, 10015, '004', 'SAVINGS', 'KB 전세드림적금', '2015323456', 16400000, 'ACTIVE', '2024-09-01', '2028-08-31', '3.8000', 1000000),
    (313, 10016, '004', 'CHECKING', 'KB 입출금통장', '2016123456', 2600000, 'ACTIVE', '2023-05-02', None, '0.1000', None),
    (314, 10016, '004', 'CHECKING', 'KB 비상금통장', '2016223456', 1200000, 'ACTIVE', '2024-02-14', None, '0.1000', None),
    (315, 10016, '004', 'SAVINGS', 'KB 전세드림적금', '2016323456', 19600000, 'ACTIVE', '2024-09-01', '2028-08-31', '3.8000', 1000000),

    # --- 시연 페르소나: 송승윤(10017~10021) — 급여/비상금 2개씩 ---
    # 목표 자산은 저금통(MONEY_BOX)이라 예적금 계좌가 없다.
    (316, 10017, '004', 'CHECKING', 'KB 입출금통장', '2017123456', 1400000, 'ACTIVE', '2025-11-03', None, '0.1000', None),
    (317, 10017, '004', 'CHECKING', 'KB 비상금통장', '2017223456', 400000, 'ACTIVE', '2026-01-20', None, '0.1000', None),
    (318, 10018, '004', 'CHECKING', 'KB 입출금통장', '2018123456', 1300000, 'ACTIVE', '2025-11-03', None, '0.1000', None),
    (319, 10018, '004', 'CHECKING', 'KB 비상금통장', '2018223456', 450000, 'ACTIVE', '2026-01-20', None, '0.1000', None),
    (320, 10019, '004', 'CHECKING', 'KB 입출금통장', '2019123456', 1500000, 'ACTIVE', '2025-11-03', None, '0.1000', None),
    (321, 10019, '004', 'CHECKING', 'KB 비상금통장', '2019223456', 500000, 'ACTIVE', '2026-01-20', None, '0.1000', None),
    (322, 10020, '004', 'CHECKING', 'KB 입출금통장', '2020123456', 1600000, 'ACTIVE', '2025-11-03', None, '0.1000', None),
    (323, 10020, '004', 'CHECKING', 'KB 비상금통장', '2020223456', 550000, 'ACTIVE', '2026-01-20', None, '0.1000', None),
    (324, 10021, '004', 'CHECKING', 'KB 입출금통장', '2021123456', 1700000, 'ACTIVE', '2025-11-03', None, '0.1000', None),
    (325, 10021, '004', 'CHECKING', 'KB 비상금통장', '2021223456', 600000, 'ACTIVE', '2026-01-20', None, '0.1000', None),
]


# ---------------------------------------------------------------
# 생활비 생성기: 카테고리별 소액·빈번 거래 풀에서 count건을 뽑아
# (date, hour, minute, amount, merchant, category) 튜플로 만든다.
# ---------------------------------------------------------------

MERCHANTS = {
    '식비': [
        ('GS25 편의점', 3000, 8000, (7, 23)),
        ('CU 편의점', 3000, 8000, (7, 23)),
        ('구내식당', 6000, 9000, (11, 13)),
        ('배달의민족', 15000, 25000, (11, 21)),
        ('요기요', 15000, 25000, (11, 21)),
        ('김밥천국', 7000, 12000, (11, 20)),
        ('이마트', 20000, 45000, (18, 20)),
        ('국밥집', 9000, 13000, (11, 20)),
        ('분식점', 6000, 11000, (12, 19)),
        ('파스타집', 12000, 22000, (18, 20)),
    ],
    '카페': [
        ('스타벅스', 4500, 6000, (7, 20)),
        ('이디야커피', 3800, 5000, (7, 20)),
        ('투썸플레이스', 5000, 6500, (7, 20)),
        ('컴포즈커피', 3000, 4200, (7, 20)),
        ('메가커피', 2800, 4000, (7, 20)),
    ],
    '교통': [
        ('지하철', 1550, 1550, (6, 10)),
        ('버스', 1200, 1550, (6, 22)),
        ('택시', 5000, 12000, (18, 24)),
    ],
    '쇼핑': [
        ('무신사', 20000, 60000, (12, 22)),
        ('올리브영', 10000, 30000, (12, 22)),
        ('다이소', 5000, 15000, (12, 22)),
        ('쿠팡', 15000, 50000, (12, 22)),
    ],
    '문화': [
        ('CGV', 13000, 16000, (18, 22)),
        ('멜론', 10900, 10900, (10, 20)),
        ('전시회', 15000, 25000, (11, 18)),
    ],
    '의료': [
        ('연세의원', 15000, 35000, (10, 18)),
        ('약국', 5000, 15000, (10, 19)),
    ],
    '기타': [
        ('경조사비', 10000, 50000, (10, 20)),
        ('잡화점', 3000, 10000, (10, 20)),
        ('소액기부', 5000, 20000, (10, 20)),
    ],
}

# 30일 기준 78건. 카드로 대부분 결제하는 사회초년생 기준으로, 이 건수에
# 사용자별 scale을 곱한 값이 월 변동지출이 된다(scale 1.0에서 약 85만원).
STD_COUNTS = dict(식비=32, 카페=14, 교통=18, 쇼핑=6, 문화=3, 의료=2, 기타=3)


def scaled_counts(counts, span_days):
    """30일 기준 건수를 구간 길이에 비례해 환산한다."""
    factor = span_days / 30.0
    return {cat: max(1, int(round(cnt * factor))) for cat, cnt in counts.items()}


def gen_lifestyle(rng, category, count, start, end, scale, used_slots):
    """start~end(양끝 포함) 사이 임의 시각에 count건의 생활비 거래를 만든다."""
    pool = MERCHANTS[category]
    span = (end - start).days + 1
    out = []
    for _ in range(count):
        merchant, lo, hi, (h1, h2) = rng.choice(pool)
        amount = int(round(rng.randint(lo, hi) * scale / 10)) * 10
        for _try in range(80):
            day = start + datetime.timedelta(days=rng.randint(0, span - 1))
            hour = rng.randint(h1, min(h2, 23))
            minute = rng.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
            key = (day, hour, minute)
            if key not in used_slots:
                used_slots.add(key)
                break
        out.append((day, hour, minute, amount, merchant, category))
    return out


def make_lifestyle(rng, counts, start, end, scale=1.0, category_scale=None):
    span = (end - start).days + 1
    per_cat = scaled_counts(counts, span)
    category_scale = category_scale or {}
    used_slots = set()
    items = []
    for cat, cnt in per_cat.items():
        items += gen_lifestyle(
            rng, cat, cnt, start, end,
            scale * category_scale.get(cat, 1.0),
            used_slots,
        )
    return items


# =================================================================
# 사용자 프로필
# income/fixed의 offset은 급여일 기준 상대 일수다.
#
# `end_balance`는 시작 잔액이 아니라 **구간 종료 시점(DATA_END)의 잔액**이다.
# 시작 잔액은 여기서 전체 순증감을 빼서 역산한다. 화면에 실제로 보이는 값은
# "지금 잔액"이므로 그쪽을 고정해야 페르소나(저소득/과소비/고소득)가 의도대로
# 드러나고, 구간 길이를 바꿔도 최종 잔액이 흔들리지 않는다.
#
# `scale`은 변동지출 강도다. 여유자금(소득 - 고정지출 - 변동지출)이 이 값으로
# 결정되므로 페르소나별 저축 여력을 여기서 조절한다.
# =================================================================
USER_PROFILES = [
    # ---------- 10001 (표준) ----------
    dict(
        kb_user_id=10001, account_id=201, end_balance=2480000,
        income=[(0, 10, 0, 2850000, '급여')],
        fixed=[
            (1, 9, 0, 450000, '행복주택 월세', '주거'),
            (1, 10, 0, 500000, 'KB 청년적금', '저축'),
            (2, 10, 0, 100000, 'KB 적립식펀드', '투자'),
            (3, 9, 0, 55000, 'KB통신', '통신'),
            (7, 9, 0, 62000, '실손보험', '보험'),
            (9, 9, 0, 13900, '넷플릭스', '구독'),
        ],
        counts=STD_COUNTS, scale=1.55,
    ),
    # ---------- 10002 (저소득) ----------
    dict(
        kb_user_id=10002, account_id=203, end_balance=1150000,
        income=[(0, 10, 0, 2200000, '급여')],
        fixed=[
            (1, 9, 0, 700000, '행복주택 월세', '주거'),
            (2, 10, 0, 100000, '청년희망적금', '저축'),
            (3, 10, 0, 20000, '소액적립펀드', '투자'),
            (3, 9, 0, 45000, '알뜰폰 요금', '통신'),
            (7, 9, 0, 35000, '실손보험', '보험'),
            (9, 9, 0, 9000, '넷플릭스', '구독'),
        ],
        counts=STD_COUNTS, scale=1.75,
    ),
    # ---------- 10003 (고소득) ----------
    dict(
        kb_user_id=10003, account_id=204, end_balance=13200000,
        income=[(0, 10, 0, 5200000, '급여')],
        fixed=[
            (1, 9, 0, 900000, '아파트 관리비 및 대출이자', '주거'),
            (1, 10, 0, 400000, '목돈모으기적금', '저축'),
            (2, 10, 0, 300000, 'ETF 자동투자', '투자'),
            (3, 9, 0, 80000, '프리미엄 통신료', '통신'),
            (7, 9, 0, 150000, '종신보험', '보험'),
            (9, 9, 0, 35000, 'OTT 및 음악 구독', '구독'),
        ],
        counts=STD_COUNTS, scale=2.86,
    ),
    # ---------- 10004 (대출상환 포함) ----------
    dict(
        kb_user_id=10004, account_id=206, end_balance=1540000,
        income=[(0, 10, 0, 2600000, '급여')],
        fixed=[
            (1, 9, 0, 500000, '행복주택 월세', '주거'),
            (1, 10, 0, 200000, 'KB 청년적금', '저축'),
            (2, 9, 30, 250000, '학자금대출 상환', '대출상환'),
            (3, 9, 0, 50000, 'KB통신', '통신'),
            (7, 9, 0, 45000, '실손보험', '보험'),
            (9, 9, 0, 12900, '넷플릭스', '구독'),
        ],
        counts=STD_COUNTS, scale=1.60,
    ),
    # ---------- 10005 (주거비 과다) ----------
    dict(
        kb_user_id=10005, account_id=207, end_balance=1760000,
        income=[(0, 10, 0, 3000000, '급여')],
        fixed=[
            (1, 9, 0, 750000, '역세권 원룸 월세', '주거'),
            (1, 10, 0, 400000, 'KB 청년적금', '저축'),
            (2, 10, 0, 100000, 'KB 적립식펀드', '투자'),
            (3, 9, 0, 55000, 'KB통신', '통신'),
            (7, 9, 0, 60000, '실손보험', '보험'),
            (9, 9, 0, 15900, '넷플릭스+유튜브', '구독'),
        ],
        counts=STD_COUNTS, scale=1.76,
    ),
    # ---------- 10006 (부모동거, 주거비 없음) ----------
    dict(
        kb_user_id=10006, account_id=208, end_balance=4900000,
        income=[(0, 10, 0, 2700000, '급여')],
        fixed=[
            (1, 10, 0, 300000, 'KB 청년적금', '저축'),
            (2, 10, 0, 100000, 'KB 적립식펀드', '투자'),
            (3, 9, 0, 50000, 'KB통신', '통신'),
            (7, 9, 0, 40000, '실손보험', '보험'),
            (9, 9, 0, 12900, '넷플릭스', '구독'),
        ],
        # 주거비가 없는 만큼 생활비 건수를 조금 늘린다.
        counts=dict(식비=34, 카페=15, 교통=19, 쇼핑=6, 문화=3, 의료=2, 기타=3), scale=1.72,
    ),
    # ---------- 10007 (과소비, 여유자금 음수) ----------
    dict(
        kb_user_id=10007, account_id=209, end_balance=900000,
        income=[(0, 10, 0, 2900000, '급여')],
        fixed=[
            (1, 9, 0, 500000, '오피스텔 월세', '주거'),
            (1, 10, 0, 100000, 'KB 청년적금', '저축'),
            (2, 10, 0, 50000, 'KB 적립식펀드', '투자'),
            (3, 9, 0, 60000, 'KB통신', '통신'),
            (7, 9, 0, 55000, '실손보험', '보험'),
            (9, 9, 0, 25900, '각종 구독 서비스', '구독'),
        ],
        counts=STD_COUNTS, scale=1.40,
        # 쇼핑/문화에 큰 금액을 몰아 과소비 성향을 만든다.
        category_scale={'쇼핑': 6.0, '문화': 3.0},
    ),
    # ---------- 10008 (저축·투자 자동이체 3건) ----------
    dict(
        kb_user_id=10008, account_id=210, end_balance=3850000,
        income=[(0, 10, 0, 3100000, '급여')],
        fixed=[
            (1, 9, 0, 550000, '오피스텔 월세', '주거'),
            (1, 10, 0, 300000, 'KB 목돈모으기적금', '저축'),
            (2, 10, 0, 150000, 'KB ETF 자동투자', '투자'),
            (2, 10, 30, 100000, 'KB 적립식펀드', '투자'),
            (3, 9, 0, 55000, 'KB통신', '통신'),
            (7, 9, 0, 50000, '실손보험', '보험'),
            (9, 9, 0, 15900, '넷플릭스', '구독'),
        ],
        counts=dict(식비=30, 카페=14, 교통=18, 쇼핑=6, 문화=3, 의료=2, 기타=3), scale=1.79,
    ),
    # ---------- 10009 (프리랜서, 불규칙 수입) ----------
    # 수입 상호에 '급여/월급/수당'이 없어 백엔드 급여일 역추론이 실패한다.
    # 급여일이 없는 사용자의 폴백 경로(이번 달 1일~다음 달 1일)를 시연하기 위한 케이스다.
    dict(
        kb_user_id=10009, account_id=212, end_balance=2960000,
        income=[
            (0, 10, 0, 1200000, '프로젝트A 대금'),
            (10, 15, 0, 900000, '프로젝트B 대금'),
            (20, 11, 0, 1200000, '프리랜서 정산'),
        ],
        fixed=[
            (1, 9, 0, 400000, '오피스텔 월세', '주거'),
            (2, 10, 0, 200000, 'KB 청년적금', '저축'),
            (3, 9, 0, 50000, 'KB통신', '통신'),
            (7, 9, 0, 45000, '실손보험', '보험'),
        ],
        counts=STD_COUNTS, scale=2.47,
    ),
    # ---------- 10010 (뉴가입, 예적금 미보유) ----------
    # 거래내역은 다른 사용자와 동일한 기간을 갖는다 — 마이데이터는 서비스 가입
    # 시점과 무관하게 은행 거래내역 전체를 수신하기 때문이다. 대신 예적금 계좌가
    # 없어 저축·투자 자동이체가 고정지출에서 빠진다("아직 모으고 있지 않은 사용자").
    dict(
        kb_user_id=10010, account_id=213, end_balance=1030000,
        income=[(0, 10, 0, 2500000, '급여')],
        fixed=[
            (1, 9, 0, 550000, '원룸 월세', '주거'),
            (3, 9, 0, 52000, 'KB통신', '통신'),
            (7, 9, 0, 38000, '실손보험', '보험'),
            (9, 9, 0, 13900, '넷플릭스', '구독'),
        ],
        counts=STD_COUNTS, scale=1.99,
    ),
    # ---------- 10011 (이번 달 여유자금 소진) ----------
    # `available_now=0`이라 현재 급여주기의 여유자금이 정확히 0원으로 계산된다.
    # 다른 사용자들은 주기가 아직 절반쯤 남아 여유자금이 넉넉하게 잡히므로,
    # "쓸 돈이 하나도 남지 않은 상태"를 보여주려면 이 사용자가 필요하다.
    dict(
        kb_user_id=10011, account_id=241, end_balance=800000,
        income=[(0, 10, 0, 2400000, '급여')],
        fixed=[
            (1, 9, 0, 620000, '반지하 원룸 월세', '주거'),
            (2, 10, 0, 150000, 'KB 새출발적금', '저축'),
            (3, 9, 0, 48000, 'KB통신', '통신'),
            (7, 9, 0, 41000, '실손보험', '보험'),
            (9, 9, 0, 13900, '넷플릭스', '구독'),
        ],
        counts=STD_COUNTS, scale=1.60,
        available_now=0,
    ),

    # =========================================================
    # 시연 페르소나
    # 진행률 단계마다 계정을 나눴을 뿐 같은 사람이므로, 소비 패턴을 결정하는
    # income/fixed/scale은 5개 계정이 완전히 동일하다. 단계별 차이는 저축계좌
    # 잔액(탁민주)과 백엔드 저금통 잔액(송승윤)에서만 만들어진다.
    # =========================================================
    # ---------- 10012 (탁민주 — 전세 자기부담금 목표, 성실형) ----------
    dict(
        kb_user_id=10012, account_id=301, end_balance=2100000,
        income=[(0, 10, 0, 2850000, '급여')],
        fixed=[
            (1, 9, 0, 550000, '원룸 월세', '주거'),
            (1, 10, 0, 830000, 'KB 전세드림적금', '저축'),
            (3, 9, 0, 52000, 'KB통신', '통신'),
            (7, 9, 0, 58000, '실손보험', '보험'),
            (9, 9, 0, 13900, '넷플릭스', '구독'),
        ],
        counts=STD_COUNTS, scale=1.35,
    ),
    # ---------- 10013 (탁민주 — 전세 자기부담금 목표, 성실형) ----------
    dict(
        kb_user_id=10013, account_id=304, end_balance=2300000,
        income=[(0, 10, 0, 2850000, '급여')],
        fixed=[
            (1, 9, 0, 550000, '원룸 월세', '주거'),
            (1, 10, 0, 830000, 'KB 전세드림적금', '저축'),
            (3, 9, 0, 52000, 'KB통신', '통신'),
            (7, 9, 0, 58000, '실손보험', '보험'),
            (9, 9, 0, 13900, '넷플릭스', '구독'),
        ],
        counts=STD_COUNTS, scale=1.35,
    ),
    # ---------- 10014 (탁민주 — 전세 자기부담금 목표, 성실형) ----------
    dict(
        kb_user_id=10014, account_id=307, end_balance=2500000,
        income=[(0, 10, 0, 2850000, '급여')],
        fixed=[
            (1, 9, 0, 550000, '원룸 월세', '주거'),
            (1, 10, 0, 830000, 'KB 전세드림적금', '저축'),
            (3, 9, 0, 52000, 'KB통신', '통신'),
            (7, 9, 0, 58000, '실손보험', '보험'),
            (9, 9, 0, 13900, '넷플릭스', '구독'),
        ],
        counts=STD_COUNTS, scale=1.20,
    ),
    # ---------- 10015 (탁민주 — 전세 자기부담금 목표, 성실형) ----------
    dict(
        kb_user_id=10015, account_id=310, end_balance=2400000,
        income=[(0, 10, 0, 2850000, '급여')],
        fixed=[
            (1, 9, 0, 550000, '원룸 월세', '주거'),
            (1, 10, 0, 830000, 'KB 전세드림적금', '저축'),
            (3, 9, 0, 52000, 'KB통신', '통신'),
            (7, 9, 0, 58000, '실손보험', '보험'),
            (9, 9, 0, 13900, '넷플릭스', '구독'),
        ],
        counts=STD_COUNTS, scale=1.35,
    ),
    # ---------- 10016 (탁민주 — 전세 자기부담금 목표, 성실형) ----------
    dict(
        kb_user_id=10016, account_id=313, end_balance=2600000,
        income=[(0, 10, 0, 2850000, '급여')],
        fixed=[
            (1, 9, 0, 550000, '원룸 월세', '주거'),
            (1, 10, 0, 830000, 'KB 전세드림적금', '저축'),
            (3, 9, 0, 52000, 'KB통신', '통신'),
            (7, 9, 0, 58000, '실손보험', '보험'),
            (9, 9, 0, 13900, '넷플릭스', '구독'),
        ],
        counts=STD_COUNTS, scale=1.35,
    ),
    # ---------- 10017 (송승윤 — 비상금 목표, 불안정형) ----------
    # 시작 시점. 여유자금 알림을 신경 쓰지 않고 예산을 넘겨 쓴다
    # 월세가 없어 고정지출이 적고 여유자금은 넉넉한데, 변동지출이 예산을 넘겨
    # 적립이 안 되는 구조다. "돈이 없어서"가 아니라 "관리를 안 해서" 못 모은다.
    # 저금통 자동이체는 서브레저라 계좌 이체가 없으므로 거래로 넣지 않는다.
    dict(
        kb_user_id=10017, account_id=316, end_balance=4600000,
        income=[(0, 10, 0, 2400000, '급여')],
        fixed=[
            (3, 9, 0, 61000, 'KB통신', '통신'),
            (7, 9, 0, 39000, '실손보험', '보험'),
            (9, 9, 0, 13900, '유튜브 프리미엄', '구독'),
        ],
        counts=STD_COUNTS, scale=1.85,
    ),
    # ---------- 10018 (송승윤 — 비상금 목표, 불안정형) ----------
    # 최악 구간. 하루 예산의 두 배를 써서 적립이 전혀 되지 않는다
    # 월세가 없어 고정지출이 적고 여유자금은 넉넉한데, 변동지출이 예산을 넘겨
    # 적립이 안 되는 구조다. "돈이 없어서"가 아니라 "관리를 안 해서" 못 모은다.
    # 저금통 자동이체는 서브레저라 계좌 이체가 없으므로 거래로 넣지 않는다.
    dict(
        kb_user_id=10018, account_id=318, end_balance=3400000,
        income=[(0, 10, 0, 2400000, '급여')],
        fixed=[
            (3, 9, 0, 61000, 'KB통신', '통신'),
            (7, 9, 0, 39000, '실손보험', '보험'),
            (9, 9, 0, 13900, '유튜브 프리미엄', '구독'),
        ],
        counts=STD_COUNTS, scale=2.05,
    ),
    # ---------- 10019 (송승윤 — 비상금 목표, 불안정형) ----------
    # 줄이는 중이지만 아직 예산을 근소하게 넘긴다
    # 월세가 없어 고정지출이 적고 여유자금은 넉넉한데, 변동지출이 예산을 넘겨
    # 적립이 안 되는 구조다. "돈이 없어서"가 아니라 "관리를 안 해서" 못 모은다.
    # 저금통 자동이체는 서브레저라 계좌 이체가 없으므로 거래로 넣지 않는다.
    dict(
        kb_user_id=10019, account_id=320, end_balance=5400000,
        income=[(0, 10, 0, 2400000, '급여')],
        fixed=[
            (3, 9, 0, 61000, 'KB통신', '통신'),
            (7, 9, 0, 39000, '실손보험', '보험'),
            (9, 9, 0, 13900, '유튜브 프리미엄', '구독'),
        ],
        counts=STD_COUNTS, scale=1.65,
    ),
    # ---------- 10020 (송승윤 — 비상금 목표, 불안정형) ----------
    # 예산 안으로 들어와 적립이 시작된다
    # 월세가 없어 고정지출이 적고 여유자금은 넉넉한데, 변동지출이 예산을 넘겨
    # 적립이 안 되는 구조다. "돈이 없어서"가 아니라 "관리를 안 해서" 못 모은다.
    # 저금통 자동이체는 서브레저라 계좌 이체가 없으므로 거래로 넣지 않는다.
    dict(
        kb_user_id=10020, account_id=322, end_balance=6800000,
        income=[(0, 10, 0, 2400000, '급여')],
        fixed=[
            (3, 9, 0, 61000, 'KB통신', '통신'),
            (7, 9, 0, 39000, '실손보험', '보험'),
            (9, 9, 0, 13900, '유튜브 프리미엄', '구독'),
        ],
        counts=STD_COUNTS, scale=1.35,
    ),
    # ---------- 10021 (송승윤 — 비상금 목표, 불안정형) ----------
    # 안정적으로 관리해 매일 꾸준히 적립된다
    # 월세가 없어 고정지출이 적고 여유자금은 넉넉한데, 변동지출이 예산을 넘겨
    # 적립이 안 되는 구조다. "돈이 없어서"가 아니라 "관리를 안 해서" 못 모은다.
    # 저금통 자동이체는 서브레저라 계좌 이체가 없으므로 거래로 넣지 않는다.
    dict(
        kb_user_id=10021, account_id=324, end_balance=7800000,
        income=[(0, 10, 0, 2400000, '급여')],
        fixed=[
            (3, 9, 0, 61000, 'KB통신', '통신'),
            (7, 9, 0, 39000, '실손보험', '보험'),
            (9, 9, 0, 13900, '유튜브 프리미엄', '구독'),
        ],
        counts=STD_COUNTS, scale=1.05,
    ),
]


# =================================================================
# 거래 생성 — 사용자별로 급여/고정지출/생활비를 만들고 시간순 정렬한다.
# =================================================================
per_user_rows = {}
summary_lines = []

for prof in USER_PROFILES:
    uid = prof['kb_user_id']
    acc = prof['account_id']
    rows = []

    for cycle_no, pay_date in enumerate(SALARY_DATES, start=1):
        cycle_income = 0
        cycle_fixed = 0

        for (off, hh, mm, amount, merchant) in prof['income']:
            when = pay_date + datetime.timedelta(days=off)
            if when > DATA_END:
                continue
            rows.append(dict(kb_user_id=uid, account_id=acc, ttype='DEPOSIT',
                             amount=amount, transacted_at=dt(pay_date, off, hh, mm),
                             merchant=merchant, category=None))
            cycle_income += amount

        for (off, hh, mm, amount, merchant, category) in prof['fixed']:
            when = pay_date + datetime.timedelta(days=off)
            if when > DATA_END:
                continue
            rows.append(dict(kb_user_id=uid, account_id=acc, ttype='PAYMENT',
                             amount=amount, transacted_at=dt(pay_date, off, hh, mm),
                             merchant=merchant, category=category))
            cycle_fixed += amount

        summary_lines.append(
            f"user {uid} cycle{cycle_no} payday={pay_date} income={cycle_income} fixed={cycle_fixed}"
        )

    lifestyle_total = 0
    for seg_no, (seg_start, seg_end) in enumerate(SEGMENTS):
        rng = random.Random(f"{uid}-seg{seg_no}")
        items = make_lifestyle(
            rng, prof['counts'], seg_start, seg_end,
            scale=prof['scale'], category_scale=prof.get('category_scale'),
        )
        for (day, hh, mm, amount, merchant, category) in items:
            rows.append(dict(kb_user_id=uid, account_id=acc, ttype='PAYMENT',
                             amount=amount,
                             transacted_at=datetime.datetime(day.year, day.month, day.day, hh, mm),
                             merchant=merchant, category=category))
            lifestyle_total += amount
        summary_lines.append(
            f"user {uid} seg{seg_no} {seg_start}~{seg_end} n={len(items)}"
        )

    rows.sort(key=lambda r: r['transacted_at'])

    if prof.get('available_now') is not None:
        tune_available_now(rows, INCOME_BY_USER[uid], prof['available_now'], uid)

    per_user_rows[uid] = rows
    summary_lines.append(f"user {uid} lifestyle_total={lifestyle_total} rows={len(rows)}")


# =================================================================
# transaction_id 대역 할당 — 순차적으로, 각 사용자는 건수를 다음
# hundred 경계까지 올림한 폭을 받는다.
# =================================================================
next_band_start = 30101
band_allocations = {}
for prof in USER_PROFILES:
    uid = prof['kb_user_id']
    count = len(per_user_rows[uid])
    id_start = next_band_start
    id_end = id_start + count - 1
    band_allocations[uid] = id_start
    next_band_start = (id_end // 100) * 100 + 101


# =================================================================
# ID 부여 + 잔액 누적
# =================================================================
all_rows = []
account_final_balance = {}

for prof in USER_PROFILES:
    uid = prof['kb_user_id']
    rows = per_user_rows[uid]

    next_id = band_allocations[uid]
    for row in rows:
        row['tx_id'] = next_id
        next_id += 1

    # 목표로 삼는 건 "지금 잔액"이므로, 전체 순증감을 빼서 시작 잔액을 역산한다.
    net_flow = sum(r['amount'] if r['ttype'] == 'DEPOSIT' else -r['amount'] for r in rows)
    start_balance = prof['end_balance'] - net_flow
    assert start_balance >= 0, \
        f"user {uid}: start_balance {start_balance} < 0 (end_balance too low for net_flow {net_flow})"

    balance = start_balance
    min_balance = balance
    for row in rows:
        if row['ttype'] == 'DEPOSIT':
            balance += row['amount']
        else:
            balance -= row['amount']
        row['balance_after'] = balance
        min_balance = min(min_balance, balance)

    assert balance == prof['end_balance'], \
        f"user {uid}: final {balance} != end_balance {prof['end_balance']}"

    all_rows.extend(rows)
    account_final_balance[prof['account_id']] = balance
    summary_lines.append(
        f"user {uid} TOTAL: count={len(rows)} "
        f"id_range=[{band_allocations[uid]}-{next_id - 1}] "
        f"start={start_balance} final={balance} min_seen={min_balance} "
        f"net_flow={net_flow}"
    )

all_rows.sort(key=lambda r: r['tx_id'])


# =================================================================
# sanity checks
# =================================================================
ids = [r['tx_id'] for r in all_rows]
assert len(ids) == len(set(ids)), "duplicate transaction_id detected"

for r in all_rows:
    assert r['ttype'] in ('DEPOSIT', 'PAYMENT'), r
    if r['ttype'] == 'DEPOSIT':
        assert r['category'] is None, ('DEPOSIT with category', r)
    else:
        assert r['category'] is not None, ('PAYMENT without category', r)

# 구간을 벗어난 거래(특히 미래 거래)가 없어야 한다.
for r in all_rows:
    d = r['transacted_at'].date()
    assert DATA_START <= d <= DATA_END, ('transaction out of range', r)

# 급여가 고정지출보다 선행해야 한다.
first_income = {}
first_fixed = {}
for r in all_rows:
    uid = r['kb_user_id']
    if r['ttype'] == 'DEPOSIT':
        if uid not in first_income or r['transacted_at'] < first_income[uid]:
            first_income[uid] = r['transacted_at']
    if r['category'] in FIXED_CATS:
        if uid not in first_fixed or r['transacted_at'] < first_fixed[uid]:
            first_fixed[uid] = r['transacted_at']
for uid in first_income:
    if uid in first_fixed:
        assert first_fixed[uid] >= first_income[uid], \
            f"user {uid}: first_fixed {first_fixed[uid]} < first_income {first_income[uid]}"

neg = [r for r in all_rows if r['balance_after'] < 0]
assert not neg, f"negative balance_after rows: {neg[:3]}"

known_account_ids = {a[0] for a in ACCOUNTS_META}
used_account_ids = {r['account_id'] for r in all_rows}
assert used_account_ids <= known_account_ids, \
    f"unknown account_id in transactions: {used_account_ids - known_account_ids}"

# 모든 사용자가 입출금계좌 2개를 갖는지 확인한다 (끌어쓰기 시연 전제).
checking_per_user = Counter(a[1] for a in ACCOUNTS_META if a[3] == 'CHECKING')
for (uid, *_rest) in KB_USERS:
    assert checking_per_user[uid] == 2, \
        f"user {uid}: CHECKING account count {checking_per_user[uid]} != 2"

# 계좌번호는 전 계좌에서 유일해야 한다.
numbers = [a[5] for a in ACCOUNTS_META]
assert len(numbers) == len(set(numbers)), "duplicate account_number detected"


# =================================================================
# kb_user / account / transaction INSERT 문 생성
# =================================================================
kb_user_lines = []
for (kb_user_id, name, birth_date, email, company, income) in KB_USERS:
    kb_user_lines.append(
        f"({kb_user_id}, {sqlval(name)}, {sqlval(birth_date)}, {sqlval(email)}, "
        f"{sqlval(company)}, {income})"
    )

account_lines = []
account_balance_report = []
for (account_id, kb_user_id, fi, atype, name, number, default_balance,
     status, opened, maturity, rate, limit_) in sorted(ACCOUNTS_META):
    balance = account_final_balance.get(account_id, default_balance)
    has_ledger = account_id in account_final_balance
    account_balance_report.append(
        f"account {account_id} (user {kb_user_id}, {atype}): balance={balance} "
        f"({'ledger final balance_after' if has_ledger else 'no transactions, kept seed default'})"
    )
    account_lines.append(
        f"({account_id}, {kb_user_id}, {sqlval(fi)}, {sqlval(atype)}, {sqlval(name)}, "
        f"{sqlval(number)}, {balance}, {sqlval(status)}, {sqlval(opened)}, {sqlval(maturity)}, "
        f"{rate}, {sqlval(limit_)})"
    )

tx_lines = []
for r in all_rows:
    ts_str = r['transacted_at'].strftime('%Y-%m-%d %H:%M:%S')
    tx_lines.append(
        f"({r['tx_id']}, {r['kb_user_id']}, {r['account_id']}, NULL, NULL, '{r['ttype']}', "
        f"{r['amount']}, {r['balance_after']}, '{ts_str}', {sqlval(r['merchant'])}, {sqlval(r['category'])})"
    )

# ---- stdout: 붙여넣을 SQL (kb_user -> account -> transaction 순서) ----
print("INSERT INTO `kb_user` (`kb_user_id`, `name`, `birth_date`, `email`, `company_name`, `monthly_income`)")
print("VALUES " + ",\n       ".join(kb_user_lines) + ";")
print()
print("INSERT INTO `account` (`account_id`, `kb_user_id`, `financial_institution_code`, `account_type`,")
print("                       `account_name`, `account_number`, `balance`, `account_status`,")
print("                       `opened_at`, `maturity_at`, `interest_rate`, `monthly_payment_limit`)")
print("VALUES " + ",\n       ".join(account_lines) + ";")
print()
print("INSERT INTO `transaction` (`transaction_id`, `kb_user_id`, `account_id`, `card_id`,")
print("                           `prepaid_instrument_id`, `transaction_type`, `amount`,")
print("                           `balance_after`, `transacted_at`, `merchant_name`, `category_name`)")
print("VALUES")
print(",\n".join(tx_lines) + ";")

# ---- stderr: 요약 + sanity 통과 여부 ----
print("ALL SANITY CHECKS PASSED", file=sys.stderr)
print("\n".join(summary_lines), file=sys.stderr)
print(f"\nDATA RANGE = {DATA_START} ~ {DATA_END} (PAYDAY={PAYDAY})", file=sys.stderr)
print(f"SALARY DATES = {SALARY_DATES}", file=sys.stderr)
print(f"SEGMENTS = {SEGMENTS}", file=sys.stderr)
print(f"TOTAL ROWS = {len(all_rows)}", file=sys.stderr)
actual_min = min(r['transacted_at'] for r in all_rows)
actual_max = max(r['transacted_at'] for r in all_rows)
print(f"ACTUAL TX RANGE = {actual_min} ~ {actual_max}", file=sys.stderr)
cats = set(r['category'] for r in all_rows if r['category'] is not None)
print(f"DISTINCT CATEGORIES ({len(cats)}) = {sorted(cats)}", file=sys.stderr)
per_user = Counter(r['kb_user_id'] for r in all_rows)
print(f"PER USER COUNTS = {dict(sorted(per_user.items()))}", file=sys.stderr)
ttypes = Counter(r['ttype'] for r in all_rows)
print(f"TYPE COUNTS = {dict(ttypes)}", file=sys.stderr)
print(f"BAND ALLOCATIONS = {band_allocations}", file=sys.stderr)
print(f"ACCOUNTS = {len(ACCOUNTS_META)} (CHECKING per user = 2)", file=sys.stderr)
print("\nACCOUNT BALANCES (account.balance == ledger final balance_after):", file=sys.stderr)
print("\n".join(account_balance_report), file=sys.stderr)

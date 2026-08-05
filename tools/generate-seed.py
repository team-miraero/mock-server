#!/usr/bin/env python3
"""
generate-seed.py — Task M1 목 금융 데이터(`kb_user` 10건, `account` 22건,
`transaction` 605건) 생성기.

무엇을 하는가
-------------
`docker/mysql/init/schema.sql`에 그대로 붙여넣을 세 개의 `INSERT` 문
(`kb_user`, `account`, `transaction`)을 표준 출력으로 만들어낸다. 605건의
`balance_after` 누적, `transaction_id` 대역, 급여-고정지출 순서를 손으로
맞추면 반드시 틀리기 때문에 이 스크립트로 생성한다. Docker init 스크립트는
`.sql` 파일만 실행하므로(파이썬을 실행할 수 없으므로) `schema.sql`에는 이
스크립트의 출력을 "그대로 복사해 넣은 리터럴 SQL"이 최종 산출물로 커밋되어
있다. 즉 이 스크립트를 실행하지 않아도 `docker compose up`은 정상 동작한다 —
이 스크립트는 재생성이 필요할 때(날짜 갱신, 사용자 추가 등)만 쓴다.

`account.balance`는 손으로 고정하지 않는다. 각 계좌의 시간순 마지막 거래
`balance_after`를 스크립트가 직접 추적해서 그 값을 `account.balance`로 쓴다
(거래가 없는 계좌 — 저축/예금/적금 등 — 만 원래 시드 값을 유지한다). 그래야
`account.balance`(현재 잔액)와 `transaction` 원장을 합산한 값이 항상 일치한다.

사용 방법
---------
표준 라이브러리(`datetime`, `random`)만 사용한다. 추가 설치 불필요.

    cd miraero-mock-server
    python3 tools/generate-seed.py > /tmp/seed_values.sql

- 표준 출력(stdout): `INSERT INTO \`kb_user\` ... VALUES ...;`,
  `INSERT INTO \`account\` ... VALUES ...;`, `INSERT INTO \`transaction\` ...
  VALUES ...;` 세 문장을 순서대로 출력한다. `schema.sql`의 해당 세 블록을
  이 출력으로 통째로 교체하면 된다.
- 표준 에러(stderr): 사용자별/사이클별 수입·고정지출·생활비·여유자금 요약과
  전수 sanity-check(카테고리·타입 규칙, 급여 선행, 잔액 비음수, ID 대역 미충돌,
  계좌 최종 잔액) 통과 여부. `python3 tools/generate-seed.py 1>/dev/null`로
  요약만 볼 수 있다.

사이클 기점 날짜 갱신
----------------------
아래 `CYCLE_ANCHOR` 상수 하나가 "가장 최근 사이클(1개월치 사용자들의 유일한
사이클, 3개월치 사용자들의 마지막 사이클)의 급여일"이다. 이 값만 바꾸면
전체 사용자의 모든 사이클 날짜가 함께 이동한다 (3개월치 사용자는
`CYCLE_ANCHOR`, `CYCLE_ANCHOR - 1개월`, `CYCLE_ANCHOR - 2개월`을 사용).
날짜가 오래돼 시연 직전 데이터를 최신으로 되돌리고 싶을 때 이 상수만
갱신하고 다시 실행하면 된다.

현재 커밋된 `schema.sql`의 시드는 `CYCLE_ANCHOR = date(2026, 7, 25)`로 생성한
결과다 (즉 이 스크립트를 지금 그대로 실행하면 `schema.sql`에 이미 들어있는
것과 동일한 SQL이 나온다).
"""

import datetime
import random
import sys
from collections import Counter

# =================================================================
# 사이클 기점 — 이 값 하나만 바꾸면 전체 날짜가 이동한다.
# =================================================================
CYCLE_ANCHOR = datetime.date(2026, 7, 25)


def shift_months(base: datetime.date, months_before: int) -> datetime.date:
    """base로부터 months_before개월 전 같은 '일(day)'의 날짜를 반환한다.
    사이클은 항상 25일에 시작하므로 말일 보정이 필요 없다."""
    total = base.year * 12 + (base.month - 1) - months_before
    year, month0 = divmod(total, 12)
    return datetime.date(year, month0 + 1, base.day)


def dt(base_date, offset, hour, minute):
    d = base_date + datetime.timedelta(days=offset)
    return datetime.datetime(d.year, d.month, d.day, hour, minute)


def sqlval(v):
    if v is None:
        return 'NULL'
    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"
    return str(v)


# =================================================================
# kb_user / account 정적 시드 데이터 (Task M1 브리프 Step 2 값 그대로).
# account의 balance만 아래에서 계좌별 원장 최종 balance_after로 덮어쓴다
# (거래가 없는 계좌 — 저축/예금/적금 — 는 이 기본값을 그대로 쓴다).
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
]

# (account_id, kb_user_id, fi_code, account_type, account_name, account_number,
#  default_balance, status, opened_at, maturity_at, interest_rate, monthly_payment_limit)
# default_balance는 그 계좌에 거래가 하나도 없을 때만 최종 balance로 쓰인다.
ACCOUNTS_META = [
    (201, 10001, '004', 'CHECKING', 'KB 입출금통장', '1001234567', 3400000, 'ACTIVE', '2023-01-10', None, '0.1000', None),
    (202, 10001, '004', 'SAVINGS', 'KB 청년적금', '1009876543', 1200000, 'ACTIVE', '2025-06-01', '2027-06-01', '3.5000', 500000),
    (203, 10002, '004', 'CHECKING', 'KB 입출금통장', '1002234567', 820000, 'ACTIVE', '2024-03-02', None, '0.1000', None),
    (204, 10003, '004', 'CHECKING', 'KB 입출금통장', '1003234567', 12400000, 'ACTIVE', '2021-05-11', None, '0.1000', None),
    (205, 10003, '004', 'DEPOSIT', 'KB 정기예금', '1003987654', 20000000, 'ACTIVE', '2025-01-05', '2027-01-05', '3.2000', None),
    (206, 10004, '004', 'CHECKING', 'KB 입출금통장', '1004234567', 1450000, 'ACTIVE', '2023-09-14', None, '0.1000', None),
    (207, 10005, '004', 'CHECKING', 'KB 입출금통장', '1005234567', 2100000, 'ACTIVE', '2023-04-20', None, '0.1000', None),
    (208, 10006, '004', 'CHECKING', 'KB 입출금통장', '1006234567', 5300000, 'ACTIVE', '2024-01-08', None, '0.1000', None),
    (209, 10007, '004', 'CHECKING', 'KB 입출금통장', '1007234567', 310000, 'ACTIVE', '2023-11-30', None, '0.1000', None),
    (210, 10008, '004', 'CHECKING', 'KB 입출금통장', '1008234567', 4200000, 'ACTIVE', '2022-08-19', None, '0.1000', None),
    (211, 10008, '004', 'INSTALLMENT', 'KB 목돈모으기적금', '1008987654', 3600000, 'ACTIVE', '2025-02-01', '2027-02-01', '3.8000', 600000),
    (212, 10009, '004', 'CHECKING', 'KB 입출금통장', '1009234567', 2750000, 'ACTIVE', '2022-12-05', None, '0.1000', None),
    (213, 10010, '004', 'CHECKING', 'KB 입출금통장', '1010234567', 640000, 'ACTIVE', '2026-07-20', None, '0.1000', None),
    # 목표 자산 연결(goal_asset ACCOUNT) 시나리오용 추가 계좌 — 거래내역 없음, 시드 balance 그대로 유지.
    # 10010(신규가입)만 CHECKING 1개로 둔다 ("아직 적금이 없다"가 엣지케이스 서사이므로 추가 안 함).
    (214, 10001, '004', 'DEPOSIT', 'KB 목돈예치예금', '1001987654', 2000000, 'ACTIVE', '2024-11-01', '2026-11-01', '3.0000', None),
    (215, 10002, '004', 'SAVINGS', 'KB 씨앗적금', '1002987654', 350000, 'ACTIVE', '2025-09-01', '2027-09-01', '3.6000', 200000),
    (216, 10003, '004', 'SAVINGS', 'KB 골드적금', '1003876543', 5000000, 'ACTIVE', '2024-06-01', '2026-06-01', '3.4000', 1000000),
    (217, 10004, '004', 'SAVINGS', 'KB 학자금상환적금', '1004987654', 600000, 'ACTIVE', '2025-03-01', '2027-03-01', '3.5000', 300000),
    (218, 10005, '004', 'SAVINGS', 'KB 전세마련적금', '1005987654', 900000, 'ACTIVE', '2024-08-01', '2027-08-01', '3.7000', 400000),
    (219, 10006, '004', 'SAVINGS', 'KB 청년희망적금', '1006987654', 2000000, 'ACTIVE', '2024-02-01', '2027-02-01', '4.0000', 500000),
    (220, 10007, '004', 'SAVINGS', 'KB 자유적금', '1007987654', 50000, 'ACTIVE', '2024-12-01', '2026-12-01', '3.0000', 300000),
    (221, 10008, '004', 'DEPOSIT', 'KB 정기예금', '1008876543', 3000000, 'ACTIVE', '2025-04-01', '2027-04-01', '3.2000', None),
    (222, 10009, '004', 'SAVINGS', 'KB 프리랜서적금', '1009987654', 700000, 'ACTIVE', '2024-10-01', '2026-10-01', '3.5000', 400000),
]


# ---------------------------------------------------------------
# 생활비 생성기: 카테고리별 소액·빈번 거래 풀에서 count건을 뽑아
# (offset, hour, minute, amount, merchant, category) 튜플로 만든다.
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


def gen_lifestyle(rng, category, count, cycle_len, scale=1.0):
    pool = MERCHANTS[category]
    out = []
    used_slots = set()
    for _ in range(count):
        merchant, lo, hi, (h1, h2) = rng.choice(pool)
        amount = int(round(rng.randint(lo, hi) * scale / 10)) * 10
        for _try in range(50):
            offset = rng.randint(1, cycle_len - 2)
            hour = rng.randint(h1, h2)
            minute = rng.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
            key = (offset, hour, minute)
            if key not in used_slots:
                used_slots.add(key)
                break
        out.append((offset, hour, minute, amount, merchant, category))
    return out


STD_COUNTS = dict(식비=12, 카페=7, 교통=6, 쇼핑=3, 문화=2, 의료=1, 기타=2)  # 33건


def make_lifestyle(rng, counts, cycle_len=30, scale=1.0):
    items = []
    for cat, cnt in counts.items():
        items += gen_lifestyle(rng, cat, cnt, cycle_len, scale=scale)
    return items


# =================================================================
# 사용자 프로필 (사이클 시작일은 모두 CYCLE_ANCHOR 기준 상대값)
# =================================================================
users = []

# ---------- 10001 (표준, 3사이클) ----------
fixed_10001 = [
    (1, 9, 0, 450000, '행복주택 월세', '주거'),
    (1, 10, 0, 500000, 'KB 청년적금', '저축'),
    (2, 10, 0, 100000, 'KB 적립식펀드', '투자'),
    (3, 9, 0, 55000, 'KB통신', '통신'),
    (7, 9, 0, 62000, '실손보험', '보험'),
    (9, 9, 0, 13900, '넷플릭스', '구독'),
]
cycles_10001 = []
for i, start in enumerate([shift_months(CYCLE_ANCHOR, 2), shift_months(CYCLE_ANCHOR, 1), CYCLE_ANCHOR]):
    rng = random.Random(f'10001-{i}')
    income = [(0, 10, 0, 2850000, '급여')]
    lifestyle = make_lifestyle(rng, STD_COUNTS, scale=1.0)
    cycles_10001.append((start, income, fixed_10001, lifestyle))
users.append(dict(kb_user_id=10001, account_id=201, start_balance=3400000, count=120, cycles=cycles_10001))

# ---------- 10002 (저소득, 1사이클) ----------
fixed_10002 = [
    (1, 9, 0, 700000, '행복주택 월세', '주거'),
    (2, 10, 0, 100000, '청년희망적금', '저축'),
    (3, 10, 0, 20000, '소액적립펀드', '투자'),
    (3, 9, 0, 45000, '알뜰폰 요금', '통신'),
    (7, 9, 0, 35000, '실손보험', '보험'),
    (9, 9, 0, 9000, '넷플릭스', '구독'),
]
rng = random.Random('10002-0')
income = [(0, 10, 0, 2200000, '급여')]
lifestyle = make_lifestyle(rng, STD_COUNTS, scale=1.0)
users.append(dict(kb_user_id=10002, account_id=203, start_balance=820000, count=40,
                   cycles=[(CYCLE_ANCHOR, income, fixed_10002, lifestyle)]))

# ---------- 10003 (고소득, 1사이클) ----------
fixed_10003 = [
    (1, 9, 0, 900000, '아파트 관리비 및 대출이자', '주거'),
    (1, 10, 0, 400000, '목돈모으기적금', '저축'),
    (2, 10, 0, 300000, 'ETF 자동투자', '투자'),
    (3, 9, 0, 80000, '프리미엄 통신料', '통신'),
    (7, 9, 0, 150000, '종신보험', '보험'),
    (9, 9, 0, 35000, 'OTT 및 음악 구독', '구독'),
]
rng = random.Random('10003-0')
income = [(0, 10, 0, 5200000, '급여')]
lifestyle = make_lifestyle(rng, STD_COUNTS, scale=2.6)
users.append(dict(kb_user_id=10003, account_id=204, start_balance=12400000, count=40,
                   cycles=[(CYCLE_ANCHOR, income, fixed_10003, lifestyle)]))

# ---------- 10004 (대출상환 포함, 1사이클) ----------
fixed_10004 = [
    (1, 9, 0, 500000, '행복주택 월세', '주거'),
    (1, 10, 0, 200000, 'KB 청년적금', '저축'),
    (2, 9, 30, 250000, '학자금대출 상환', '대출상환'),
    (3, 9, 0, 50000, 'KB통신', '통신'),
    (7, 9, 0, 45000, '실손보험', '보험'),
    (9, 9, 0, 12900, '넷플릭스', '구독'),
]
rng = random.Random('10004-0')
income = [(0, 10, 0, 2600000, '급여')]
lifestyle = make_lifestyle(rng, STD_COUNTS, scale=0.95)
users.append(dict(kb_user_id=10004, account_id=206, start_balance=1450000, count=40,
                   cycles=[(CYCLE_ANCHOR, income, fixed_10004, lifestyle)]))

# ---------- 10005 (주거비 과다, 3사이클) ----------
fixed_10005 = [
    (1, 9, 0, 750000, '역세권 원룸 월세', '주거'),
    (1, 10, 0, 400000, 'KB 청년적금', '저축'),
    (2, 10, 0, 100000, 'KB 적립식펀드', '투자'),
    (3, 9, 0, 55000, 'KB통신', '통신'),
    (7, 9, 0, 60000, '실손보험', '보험'),
    (9, 9, 0, 15900, '넷플릭스+유튜브', '구독'),
]
cycles_10005 = []
for i, start in enumerate([shift_months(CYCLE_ANCHOR, 2), shift_months(CYCLE_ANCHOR, 1), CYCLE_ANCHOR]):
    rng = random.Random(f'10005-{i}')
    income = [(0, 10, 0, 3000000, '급여')]
    lifestyle = make_lifestyle(rng, STD_COUNTS, scale=1.05)
    cycles_10005.append((start, income, fixed_10005, lifestyle))
users.append(dict(kb_user_id=10005, account_id=207, start_balance=2100000, count=120, cycles=cycles_10005))

# ---------- 10006 (부모동거, 주거 없음, 1사이클) ----------
fixed_10006 = [
    (1, 10, 0, 300000, 'KB 청년적금', '저축'),
    (2, 10, 0, 100000, 'KB 적립식펀드', '투자'),
    (3, 9, 0, 50000, 'KB통신', '통신'),
    (7, 9, 0, 40000, '실손보험', '보험'),
    (9, 9, 0, 12900, '넷플릭스', '구독'),
]
counts_10006 = dict(식비=13, 카페=7, 교통=6, 쇼핑=3, 문화=2, 의료=1, 기타=2)  # 34건 (주거 제외분 보충)
rng = random.Random('10006-0')
income = [(0, 10, 0, 2700000, '급여')]
lifestyle = make_lifestyle(rng, counts_10006, scale=1.0)
users.append(dict(kb_user_id=10006, account_id=208, start_balance=5300000, count=40,
                   cycles=[(CYCLE_ANCHOR, income, fixed_10006, lifestyle)]))

# ---------- 10007 (과소비, 3사이클, 여유자금 음수) ----------
fixed_10007 = [
    (1, 9, 0, 500000, '오피스텔 월세', '주거'),
    (1, 10, 0, 100000, 'KB 청년적금', '저축'),
    (2, 10, 0, 50000, 'KB 적립식펀드', '투자'),
    (3, 9, 0, 60000, 'KB통신', '통신'),
    (7, 9, 0, 55000, '실손보험', '보험'),
    (9, 9, 0, 25900, '각종 구독 서비스', '구독'),
]
counts_10007_small = dict(식비=12, 카페=7, 교통=6, 의료=1, 기타=2)  # 28건 소액/빈번
# 나머지 쇼핑3 + 문화2 = 5건은 과소비 특성을 위해 큰 금액으로 고정 배치
big_ticket_by_cycle = [
    [(6, 15, 0, 700000, '백화점 명품관', '쇼핑'), (14, 20, 0, 650000, '온라인 해외직구', '쇼핑'),
     (22, 16, 0, 260000, '편집숍', '쇼핑'), (11, 19, 0, 300000, '오마카세 파인다이닝', '문화'),
     (26, 20, 0, 110000, '콘서트 티켓', '문화')],
    [(5, 15, 0, 750000, '백화점 명품관', '쇼핑'), (16, 20, 0, 680000, '온라인 해외직구', '쇼핑'),
     (24, 16, 0, 240000, '편집숍', '쇼핑'), (9, 19, 0, 310000, '오마카세 파인다이닝', '문화'),
     (20, 20, 0, 130000, '뮤지컬 티켓', '문화')],
    [(7, 15, 0, 720000, '백화점 명품관', '쇼핑'), (15, 20, 0, 670000, '온라인 해외직구', '쇼핑'),
     (23, 16, 0, 250000, '편집숍', '쇼핑'), (12, 19, 0, 290000, '오마카세 파인다이닝', '문화'),
     (27, 20, 0, 140000, '팝업스토어', '문화')],
]
cycles_10007 = []
for i, start in enumerate([shift_months(CYCLE_ANCHOR, 2), shift_months(CYCLE_ANCHOR, 1), CYCLE_ANCHOR]):
    rng = random.Random(f'10007-{i}')
    income = [(0, 10, 0, 2900000, '급여')]
    lifestyle = make_lifestyle(rng, counts_10007_small, scale=1.0) + big_ticket_by_cycle[i]
    cycles_10007.append((start, income, fixed_10007, lifestyle))
# 시작 잔액은 계좌 시드값(310,000)이 아니라 1,000,000으로 둔다. 3개월 연속 마이너스
# 여유자금이라 시드 balance를 그대로 시작점으로 쓰면 마지막 사이클에서 balance_after가
# 음수로 떨어진다. balance_after는 account.balance와 일치할 필요가 없다는 결정에 따라
# 이 계좌만 더 넉넉한 시작 잔액으로 시뮬레이션한다 (계좌 시드 자체는 브리프 값 그대로 둔다).
users.append(dict(kb_user_id=10007, account_id=209, start_balance=1000000, count=120, cycles=cycles_10007))

# ---------- 10008 (적금·펀드 자동이체 3건, 1사이클) ----------
fixed_10008 = [
    (1, 9, 0, 550000, '오피스텔 월세', '주거'),
    (1, 10, 0, 300000, 'KB 목돈모으기적금', '저축'),
    (2, 10, 0, 150000, 'KB ETF 자동투자', '투자'),
    (2, 10, 30, 100000, 'KB 적립식펀드', '투자'),
    (3, 9, 0, 55000, 'KB통신', '통신'),
    (7, 9, 0, 50000, '실손보험', '보험'),
    (9, 9, 0, 15900, '넷플릭스', '구독'),
]
counts_10008 = dict(식비=11, 카페=7, 교통=6, 쇼핑=3, 문화=2, 의료=1, 기타=2)  # 32건 (고정지출 7건 보충분 조정)
rng = random.Random('10008-0')
income = [(0, 10, 0, 3100000, '급여')]
lifestyle = make_lifestyle(rng, counts_10008, scale=1.0)
users.append(dict(kb_user_id=10008, account_id=210, start_balance=4200000, count=40,
                   cycles=[(CYCLE_ANCHOR, income, fixed_10008, lifestyle)]))

# ---------- 10009 (프리랜서, 불규칙 수입 3건, 고정지출 4건, 1사이클) ----------
fixed_10009 = [
    (1, 9, 0, 400000, '오피스텔 월세', '주거'),
    (3, 9, 0, 50000, 'KB통신', '통신'),
    (7, 9, 0, 45000, '실손보험', '보험'),
    (2, 10, 0, 200000, 'KB 청년적금', '저축'),
]
rng = random.Random('10009-0')
income = [
    (0, 10, 0, 1200000, '프로젝트A 대금'),
    (10, 15, 0, 900000, '프로젝트B 대금'),
    (20, 11, 0, 1200000, '프리랜서 정산'),
]
lifestyle = make_lifestyle(rng, STD_COUNTS, scale=0.95)
users.append(dict(kb_user_id=10009, account_id=212, start_balance=2750000, count=40,
                   cycles=[(CYCLE_ANCHOR, income, fixed_10009, lifestyle)]))

# ---------- 10010 (신규가입, 데이터 부족 엣지케이스, 5건) ----------
income = [(0, 10, 0, 2500000, '급여')]
fixed_10010 = [
    (1, 9, 0, 550000, '원룸 월세', '주거'),
]
lifestyle = [
    (4, 12, 30, 22000, '이마트', '식비'),
    (11, 13, 0, 15000, '김밥천국', '식비'),
    (18, 19, 30, 18000, '배달의민족', '식비'),
]
users.append(dict(kb_user_id=10010, account_id=213, start_balance=640000, count=5,
                   cycles=[(CYCLE_ANCHOR, income, fixed_10010, lifestyle)]))

# =================================================================
# transaction_id 대역 할당 — 순차적으로, 각 사용자는 count를 다음
# hundred 경계까지 올림한 폭을 받는다.
# 예: 10001이 120건이면 30101~30220을 쓰고, 다음 사용자는 30301부터 시작한다.
# =================================================================
next_band_start = 30101
band_allocations = {}
for u in users:
    id_start = next_band_start
    id_end = id_start + u['count'] - 1
    band_allocations[u['kb_user_id']] = id_start
    hundred_block_start = (id_end // 100) * 100
    next_band_start = hundred_block_start + 101

# =================================================================
# 생성
# =================================================================
all_rows = []
summary_lines = []
account_final_balance = {}  # account_id -> 시간순 마지막 거래의 balance_after

for u in users:
    kb_user_id = u['kb_user_id']
    account_id = u['account_id']
    next_id = band_allocations[kb_user_id]
    rows_this_user = []
    cycle_num = 0

    for (start, income_items, fixed_items, lifestyle_items) in u['cycles']:
        cycle_num += 1
        cycle_len = 30
        income_total = sum(x[3] for x in income_items)
        fixed_total = sum(x[3] for x in fixed_items)
        lifestyle_total = sum(x[3] for x in lifestyle_items)
        surplus = income_total - fixed_total - lifestyle_total
        n_items = len(income_items) + len(fixed_items) + len(lifestyle_items)
        summary_lines.append(
            f"user {kb_user_id} cycle{cycle_num} start={start} n={n_items} income={income_total} "
            f"fixed={fixed_total} lifestyle={lifestyle_total} surplus={surplus}"
        )

        for (off, hh, mm, amount, merchant) in income_items:
            ts = dt(start, off, hh, mm)
            rows_this_user.append(dict(tx_id=next_id, kb_user_id=kb_user_id, account_id=account_id,
                                        ttype='DEPOSIT', amount=amount, transacted_at=ts,
                                        merchant=merchant, category=None))
            next_id += 1

        for (off, hh, mm, amount, merchant, category) in fixed_items:
            ts = dt(start, off, hh, mm)
            rows_this_user.append(dict(tx_id=next_id, kb_user_id=kb_user_id, account_id=account_id,
                                        ttype='PAYMENT', amount=amount, transacted_at=ts,
                                        merchant=merchant, category=category))
            next_id += 1

        for (off, hh, mm, amount, merchant, category) in lifestyle_items:
            ts = dt(start, off, hh, mm)
            rows_this_user.append(dict(tx_id=next_id, kb_user_id=kb_user_id, account_id=account_id,
                                        ttype='PAYMENT', amount=amount, transacted_at=ts,
                                        merchant=merchant, category=category))
            next_id += 1

    expected_end = band_allocations[kb_user_id] + u['count'] - 1
    actual_end = next_id - 1
    assert actual_end == expected_end, f"user {kb_user_id}: id band mismatch {actual_end} != {expected_end}"
    assert len(rows_this_user) == u['count'], f"user {kb_user_id}: count mismatch {len(rows_this_user)} != {u['count']}"

    balance = u['start_balance']
    min_balance = balance
    for row in sorted(rows_this_user, key=lambda r: (r['transacted_at'], r['tx_id'])):
        if row['ttype'] == 'DEPOSIT':
            balance += row['amount']
        else:
            balance -= row['amount']
        row['balance_after'] = balance
        min_balance = min(min_balance, balance)

    all_rows.extend(rows_this_user)
    # 이 계좌의 "현재 잔액"은 시간순 마지막 거래의 balance_after다.
    account_final_balance[account_id] = balance
    summary_lines.append(f"user {kb_user_id} TOTAL: count={len(rows_this_user)} "
                          f"id_range=[{band_allocations[kb_user_id]}-{expected_end}] "
                          f"final_balance={balance} min_balance_seen={min_balance}")

all_rows.sort(key=lambda r: r['tx_id'])

# ---- sanity checks (assert 후 stderr에 결과 출력) ----
ids = [r['tx_id'] for r in all_rows]
assert len(ids) == len(set(ids)), "duplicate transaction_id detected"

FIXED_CATS = {'주거', '통신', '보험', '구독', '대출상환', '저축', '투자'}
for r in all_rows:
    assert r['ttype'] in ('DEPOSIT', 'PAYMENT'), r
    if r['ttype'] == 'DEPOSIT':
        assert r['category'] is None, ('DEPOSIT with category', r)
    else:
        assert r['category'] is not None, ('PAYMENT without category', r)

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

# every account_id referenced by a transaction must exist in ACCOUNTS_META
known_account_ids = {a[0] for a in ACCOUNTS_META}
used_account_ids = {r['account_id'] for r in all_rows}
assert used_account_ids <= known_account_ids, f"unknown account_id in transactions: {used_account_ids - known_account_ids}"

# =================================================================
# kb_user / account / transaction INSERT 문 생성
# =================================================================

kb_user_lines = []
for (kb_user_id, name, birth_date, email, company, income) in KB_USERS:
    line = (f"({kb_user_id}, {sqlval(name)}, {sqlval(birth_date)}, {sqlval(email)}, "
            f"{sqlval(company)}, {income})")
    kb_user_lines.append(line)

account_lines = []
account_balance_report = []
for (account_id, kb_user_id, fi, atype, name, number, default_balance,
     status, opened, maturity, rate, limit_) in ACCOUNTS_META:
    balance = account_final_balance.get(account_id, default_balance)
    has_ledger = account_id in account_final_balance
    account_balance_report.append(
        f"account {account_id} (user {kb_user_id}): balance={balance} "
        f"({'ledger final balance_after' if has_ledger else 'no transactions, kept seed default'})"
    )
    line = (f"({account_id}, {kb_user_id}, {sqlval(fi)}, {sqlval(atype)}, {sqlval(name)}, "
            f"{sqlval(number)}, {balance}, {sqlval(status)}, {sqlval(opened)}, {sqlval(maturity)}, "
            f"{rate}, {sqlval(limit_)})")
    account_lines.append(line)

tx_lines = []
for r in all_rows:
    ts_str = r['transacted_at'].strftime('%Y-%m-%d %H:%M:%S')
    line = (f"({r['tx_id']}, {r['kb_user_id']}, {r['account_id']}, NULL, NULL, '{r['ttype']}', "
            f"{r['amount']}, {r['balance_after']}, '{ts_str}', {sqlval(r['merchant'])}, {sqlval(r['category'])})")
    tx_lines.append(line)

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
print(f"\nTOTAL ROWS = {len(all_rows)}", file=sys.stderr)
cats = set(r['category'] for r in all_rows if r['category'] is not None)
print(f"DISTINCT CATEGORIES ({len(cats)}) = {sorted(cats)}", file=sys.stderr)
per_user = Counter(r['kb_user_id'] for r in all_rows)
print(f"PER USER COUNTS = {dict(sorted(per_user.items()))}", file=sys.stderr)
ttypes = Counter(r['ttype'] for r in all_rows)
print(f"TYPE COUNTS = {dict(ttypes)}", file=sys.stderr)
print(f"BAND ALLOCATIONS = {band_allocations}", file=sys.stderr)
print(f"CYCLE_ANCHOR = {CYCLE_ANCHOR}", file=sys.stderr)
print("\nACCOUNT BALANCES (account.balance == ledger final balance_after):", file=sys.stderr)
print("\n".join(account_balance_report), file=sys.stderr)

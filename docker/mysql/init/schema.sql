CREATE TABLE `kb_user` (
                           `kb_user_id` BIGINT NOT NULL AUTO_INCREMENT
        COMMENT 'KB 목서버 사용자 ID',

                           `name` VARCHAR(30) NOT NULL
                               COMMENT '사용자 이름',

                           `birth_date` DATE NOT NULL
                               COMMENT '생년월일',

                           `company_name` VARCHAR(100) NULL
        COMMENT '직장명',

                           `monthly_income` BIGINT NULL
        COMMENT '월 소득',

                           CONSTRAINT `pk_kb_user`
                               PRIMARY KEY (`kb_user_id`),

                           CONSTRAINT `ck_kb_user_monthly_income`
                               CHECK (
                                   `monthly_income` IS NULL
                                       OR `monthly_income` >= 0
                                   )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `account` (
                           `account_id` BIGINT NOT NULL AUTO_INCREMENT
        COMMENT '목서버 내부 계좌 ID',

                           `kb_user_id` BIGINT NOT NULL
                               COMMENT 'KB 사용자 ID',

                           `financial_institution_code` VARCHAR(10) NOT NULL
                               COMMENT '금융기관 코드',

                           `account_type` VARCHAR(30) NOT NULL
                               COMMENT 'CHECKING, SAVINGS, DEPOSIT, INSTALLMENT, ISA, CMA',

                           `account_name` VARCHAR(100) NOT NULL
                               COMMENT '계좌 또는 금융상품명',

                           `account_number` VARCHAR(30) NOT NULL
                               COMMENT '계좌번호',

                           `balance` BIGINT NOT NULL
                               COMMENT '현재 잔액 또는 평가금액',

                           `account_status` VARCHAR(20) NOT NULL
                               COMMENT 'ACTIVE, DORMANT, CLOSED, MATURED',

                           `opened_at` DATE NOT NULL
                               COMMENT '개설일',

                           `maturity_at` DATE NULL
        COMMENT '만기일',

                           `interest_rate` DECIMAL(7,4) NULL
        COMMENT '금리',

                           `monthly_payment_limit` BIGINT NULL
        COMMENT '월 납입 한도',

                           `created_at` DATETIME NOT NULL
                               DEFAULT CURRENT_TIMESTAMP
                               COMMENT '생성 일시',

                           `updated_at` DATETIME NOT NULL
                               DEFAULT CURRENT_TIMESTAMP
                               ON UPDATE CURRENT_TIMESTAMP
        COMMENT '수정 일시',

                           CONSTRAINT `pk_account`
                               PRIMARY KEY (`account_id`),

                           CONSTRAINT `uk_account_institution_number`
                               UNIQUE (
                                       `financial_institution_code`,
                                       `account_number`
                                   ),

                           CONSTRAINT `fk_account_kb_user`
                               FOREIGN KEY (`kb_user_id`)
                                   REFERENCES `kb_user` (`kb_user_id`)
                                   ON DELETE CASCADE,

                           CONSTRAINT `ck_account_type`
                               CHECK (`account_type` IN (
                                                         'CHECKING',
                                                         'SAVINGS',
                                                         'DEPOSIT',
                                                         'INSTALLMENT',
                                                         'ISA',
                                                         'CMA'
                                   )),

                           CONSTRAINT `ck_account_status`
                               CHECK (`account_status` IN (
                                                           'ACTIVE',
                                                           'DORMANT',
                                                           'CLOSED',
                                                           'MATURED'
                                   )),

                           CONSTRAINT `ck_account_balance`
                               CHECK (`balance` >= 0),

                           CONSTRAINT `ck_account_interest_rate`
                               CHECK (
                                   `interest_rate` IS NULL
                                       OR `interest_rate` >= 0
                                   ),

                           CONSTRAINT `ck_account_monthly_payment_limit`
                               CHECK (
                                   `monthly_payment_limit` IS NULL
                                       OR `monthly_payment_limit` >= 0
                                   ),

                           CONSTRAINT `ck_account_maturity_date`
                               CHECK (
                                   `maturity_at` IS NULL
                                       OR `opened_at` <= `maturity_at`
                                   )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE `card` (
                        `card_id` BIGINT NOT NULL AUTO_INCREMENT,
                        `kb_user_id` BIGINT NOT NULL,
                        `card_name` VARCHAR(100) NOT NULL COMMENT '카드 상품명',
                        `card_type` VARCHAR(20) NOT NULL COMMENT 'CREDIT, CHECK, PREPAID',
                        `financial_institution_code` VARCHAR(10) NOT NULL,
                        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                        CONSTRAINT `PK_CARD`
                            PRIMARY KEY (`card_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `prepaid_instrument` (
                                      `prepaid_instrument_id` BIGINT NOT NULL AUTO_INCREMENT,
                                      `kb_user_id` BIGINT NOT NULL,
                                      `prepaid_instrument_name` VARCHAR(100) NOT NULL COMMENT 'KB Pay 머니, 포인트 등',
                                      `prepaid_instrument_type` VARCHAR(30) NOT NULL COMMENT 'PAY_MONEY, CASH, POINT, PREPAID_CARD',
                                      `financial_institution_code` VARCHAR(10) NOT NULL,
                                      `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                      `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                                      CONSTRAINT `PK_PREPAID_INSTRUMENT`
                                          PRIMARY KEY (`prepaid_instrument_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `loan` (
                        `loan_id` BIGINT NOT NULL AUTO_INCREMENT
        COMMENT '목서버 내부 대출 ID',

                        `kb_user_id` BIGINT NOT NULL
                            COMMENT 'KB 사용자 ID',

                        `financial_institution_code` VARCHAR(10) NOT NULL
                            COMMENT '금융기관 코드',

                        `loan_name` VARCHAR(40) NOT NULL
                            COMMENT '대출 상품명',

                        `loan_amount` BIGINT NOT NULL
                            COMMENT '최초 대출 금액',

                        `remaining_amount` BIGINT NOT NULL
                            COMMENT '남은 대출 금액',

                        `interest_rate` DECIMAL(7,4) NOT NULL
                            COMMENT '대출 금리',

                        `loan_start_date` DATE NOT NULL
                            COMMENT '대출 실행일',

                        `maturity_date` DATE NOT NULL
                            COMMENT '만기일',

                        `created_at` DATETIME NOT NULL
                            DEFAULT CURRENT_TIMESTAMP
                            COMMENT '생성 일시',

                        `updated_at` DATETIME NOT NULL
                            DEFAULT CURRENT_TIMESTAMP
                            ON UPDATE CURRENT_TIMESTAMP
        COMMENT '수정 일시',

                        CONSTRAINT `pk_loan`
                            PRIMARY KEY (`loan_id`),

                        CONSTRAINT `fk_loan_kb_user`
                            FOREIGN KEY (`kb_user_id`)
                                REFERENCES `kb_user` (`kb_user_id`)
                                ON DELETE CASCADE,

                        CONSTRAINT `ck_loan_amount`
                            CHECK (`loan_amount` > 0),

                        CONSTRAINT `ck_loan_remaining_amount`
                            CHECK (`remaining_amount` >= 0),

                        CONSTRAINT `ck_loan_remaining_less_than_amount`
                            CHECK (`remaining_amount` <= `loan_amount`),

                        CONSTRAINT `ck_loan_interest_rate`
                            CHECK (`interest_rate` >= 0),

                        CONSTRAINT `ck_loan_date`
                            CHECK (`loan_start_date` <= `maturity_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `transaction` (
                               `transaction_id` BIGINT NOT NULL AUTO_INCREMENT,
                               `kb_user_id` BIGINT NOT NULL,

                               `account_id` BIGINT NULL,
                               `card_id` BIGINT NULL,
                               `prepaid_instrument_id` BIGINT NULL,

                               `transaction_type` VARCHAR(30) NOT NULL
                                   COMMENT 'DEPOSIT, WITHDRAWAL, PAYMENT, TRANSFER, REFUND',

                               `amount` BIGINT NOT NULL
                                   COMMENT '거래금액',

                               `balance_after` BIGINT NULL
        COMMENT '거래 후 잔액',

                               `transacted_at` DATETIME NOT NULL,

                               `merchant_name` VARCHAR(100) NULL
        COMMENT '가맹점',

                               `category_name` VARCHAR(50) NOT NULL
                                   COMMENT '식비, 쇼핑 등',

                               `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                               `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                                   ON UPDATE CURRENT_TIMESTAMP,

                               CONSTRAINT `PK_TRANSACTION`
                                   PRIMARY KEY (`transaction_id`),

                               INDEX `idx_transaction_user_time`
                                   (`kb_user_id`, `transacted_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
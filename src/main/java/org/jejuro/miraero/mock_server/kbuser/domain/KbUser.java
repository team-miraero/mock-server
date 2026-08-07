package org.jejuro.miraero.mock_server.kbuser.domain;

import java.time.LocalDate;
import lombok.Getter;

@Getter
public class KbUser {
    private Long kbUserId;
    private String name;
    private LocalDate birthDate;
    private String email;
    private String companyName;
    private Long monthlyIncome;
}

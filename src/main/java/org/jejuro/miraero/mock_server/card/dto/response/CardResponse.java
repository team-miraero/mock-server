package org.jejuro.miraero.mock_server.card.dto.response;


import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
@Builder
public class CardResponse {
    private Long cardId;
    private Long kbUserId;
    private String cardName;
    private String cardType;
    private String financialInstitutionCode;
}

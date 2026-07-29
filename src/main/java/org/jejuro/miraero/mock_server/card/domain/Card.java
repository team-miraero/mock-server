package org.jejuro.miraero.mock_server.card.domain;


import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import org.apache.ibatis.type.Alias;

import java.time.LocalDateTime;

@Getter
@NoArgsConstructor
@ToString
@Alias("Card")
public class Card {
    private Long cardId;
    private Long kbUserId;
    private String cardName;
    private String cardType;
    private String financialInstitutionCode;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}

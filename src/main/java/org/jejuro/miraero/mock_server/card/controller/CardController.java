package org.jejuro.miraero.mock_server.card.controller;

import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.card.dto.response.CardResponse;
import org.jejuro.miraero.mock_server.card.service.CardService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/mock/cards")
public class CardController {
    private final CardService service;

    @GetMapping("/{kbUserId}")
    public List<CardResponse> getCards(
            @PathVariable Long kbUserId
    ){
        return service.getCards(kbUserId)
                .stream()
                .map(card ->
                        CardResponse.builder()
                                .cardId(card.getCardId())
                                .kbUserId(kbUserId)
                                .cardType(card.getCardType())
                                .cardName(card.getCardName())
                                .financialInstitutionCode(card.getFinancialInstitutionCode())
                                .build()
                        ).toList();
    }
}

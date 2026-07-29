package org.jejuro.miraero.mock_server.card.service;


import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.card.domain.Card;
import org.jejuro.miraero.mock_server.card.mapper.CardMapper;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class CardService {
    private final CardMapper mapper;

    public List<Card> getCards(Long kbUserId){
        return mapper.findCards(kbUserId);
    }

}

package org.jejuro.miraero.mock_server.card.mapper;


import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.jejuro.miraero.mock_server.card.domain.Card;

import java.util.List;

@Mapper
public interface CardMapper {
    List<Card> findCards(@Param("kbUserId") Long kbUserId);
}

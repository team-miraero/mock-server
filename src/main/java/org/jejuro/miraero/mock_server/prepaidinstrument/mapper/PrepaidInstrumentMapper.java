package org.jejuro.miraero.mock_server.prepaidinstrument.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.jejuro.miraero.mock_server.prepaidinstrument.domain.PrepaidInstrument;

import java.util.List;

@Mapper
public interface PrepaidInstrumentMapper {
    List<PrepaidInstrument> findPrepaidInstruments(@Param("kbUserId") Long kbUserId);
}

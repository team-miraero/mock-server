package org.jejuro.miraero.mock_server.prepaidinstrument.service;

import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.prepaidinstrument.domain.PrepaidInstrument;
import org.jejuro.miraero.mock_server.prepaidinstrument.mapper.PrepaidInstrumentMapper;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class PrepaidInstrumentService {
    private final PrepaidInstrumentMapper mapper;

    public List<PrepaidInstrument> getPrepaidInstruments(Long kbUserId) {
        return mapper.findPrepaidInstruments(kbUserId);
    }
}

package org.jejuro.miraero.mock_server.prepaidinstrument.dto.response;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
@Builder
public class PrepaidInstrumentResponse {
    private Long prepaidInstrumentId;
    private Long kbUserId;
    private String prepaidInstrumentName;
    private String prepaidInstrumentType;
    private String financialInstitutionCode;
}

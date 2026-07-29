package org.jejuro.miraero.mock_server.prepaidinstrument.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.ToString;
import org.apache.ibatis.type.Alias;

import java.time.LocalDateTime;

@Getter
@NoArgsConstructor
@ToString
@Alias("PrepaidInstrument")
public class PrepaidInstrument {
    private Long prepaidInstrumentId;
    private Long kbUserId;
    private String prepaidInstrumentName;
    private String prepaidInstrumentType;
    private String financialInstitutionCode;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}

package org.jejuro.miraero.mock_server.prepaidinstrument.controller;

import lombok.RequiredArgsConstructor;
import org.jejuro.miraero.mock_server.prepaidinstrument.dto.response.PrepaidInstrumentResponse;
import org.jejuro.miraero.mock_server.prepaidinstrument.service.PrepaidInstrumentService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/mock/prepaid-instruments")
public class PrepaidInstrumentController {
    private final PrepaidInstrumentService service;

    @GetMapping("/{kbUserId}")
    public List<PrepaidInstrumentResponse> getPrepaidInstruments(
            @PathVariable Long kbUserId
    ){
        return service.getPrepaidInstruments(kbUserId)
                .stream()
                .map(pi ->
                        PrepaidInstrumentResponse.builder()
                                .prepaidInstrumentId(pi.getPrepaidInstrumentId())
                                .kbUserId(pi.getKbUserId())
                                .prepaidInstrumentName(pi.getPrepaidInstrumentName())
                                .prepaidInstrumentType(pi.getPrepaidInstrumentType())
                                .financialInstitutionCode(pi.getFinancialInstitutionCode())
                                .build()
                ).toList();
    }
}

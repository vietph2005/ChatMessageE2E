package org.example.chat.unit;

import org.example.chat.application.service.SafetyCodeService;
import org.example.chat.domain.model.HandshakeVerification;
import org.example.chat.domain.repository.HandshakeRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class SafetyCodeServiceTest {

    @Mock
    private HandshakeRepository handshakeRepository;

    @InjectMocks
    private SafetyCodeService safetyCodeService;

    @Test
    @DisplayName("Should generate QR verification URI payload containing conversation ID and safety code")
    void shouldGenerateQrPayload() {
        HandshakeVerification handshake = HandshakeVerification.builder()
                .conversationId("conv_abc")
                .safetyCode("842910")
                .fullFingerprintHex("abcdef1234567890")
                .layer4Status(HandshakeVerification.LayerStatus.CONFIRMED)
                .build();

        when(handshakeRepository.findByConversationId("conv_abc")).thenReturn(Optional.of(handshake));

        SafetyCodeService.SafetyCodeVerificationResult result = safetyCodeService.generateSafetyCodeInfo("conv_abc");

        assertNotNull(result);
        assertEquals("842910", result.safetyCode());
        assertTrue(result.qrPayload().contains("conv_abc"));
        assertTrue(result.qrPayload().contains("842910"));
        assertTrue(result.isConfirmed());
    }
}

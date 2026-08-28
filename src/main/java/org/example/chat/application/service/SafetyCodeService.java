package org.example.chat.application.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.domain.exception.DomainException;
import org.example.chat.domain.model.HandshakeVerification;
import org.example.chat.domain.repository.HandshakeRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;

@Slf4j
@Service
@RequiredArgsConstructor
public class SafetyCodeService {

    private final HandshakeRepository handshakeRepository;

    public SafetyCodeVerificationResult generateSafetyCodeInfo(String conversationId) {
        HandshakeVerification handshake = handshakeRepository.findByConversationId(conversationId)
                .orElseThrow(() -> new DomainException("HANDSHAKE_NOT_FOUND", "Handshake not found for conversation", HttpStatus.NOT_FOUND));

        String qrPayload = String.format("e2e-safety-v1://verify?conv=%s&code=%s&fp=%s",
                conversationId, handshake.getSafetyCode(), handshake.getFullFingerprintHex());

        return new SafetyCodeVerificationResult(
                handshake.getSafetyCode(),
                handshake.getFullFingerprintHex(),
                qrPayload,
                handshake.getLayer4Status() == HandshakeVerification.LayerStatus.CONFIRMED
        );
    }

    public record SafetyCodeVerificationResult(
            String safetyCode,
            String fullFingerprintHex,
            String qrPayload,
            boolean isConfirmed
    ) {}
}

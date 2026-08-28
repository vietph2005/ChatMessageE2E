package org.example.chat.domain.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class HandshakeVerification {
    private String id;
    private String conversationId;
    private String initiatorId;
    private String recipientId;
    private String initiatorPublicKey;
    private String recipientPublicKey;

    private LayerStatus layer1Status; // Google ID
    private LayerStatus layer2Status; // Consent
    private LayerStatus layer3Status; // Key exchange
    private LayerStatus layer4Status; // Safety code match

    private String safetyCode; // 6-digit visual code
    private String fullFingerprintHex;

    private Instant layer1VerifiedAt;
    private Instant layer2AcceptedAt;
    private Instant layer3ExchangedAt;
    private Instant layer4ConfirmedAt;
    private Instant completedAt;

    public enum LayerStatus {
        PENDING,
        VERIFIED,
        ACCEPTED,
        REJECTED,
        EXCHANGED,
        CONFIRMED,
        FAILED
    }
}

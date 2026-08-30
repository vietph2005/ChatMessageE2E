package org.example.chat.infrastructure.persistence.mongodb.document;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "handshake_verifications")
public class HandshakeVerificationDocument {
    @Id
    private String id;

    @Indexed(unique = true)
    private String conversationId;

    private String initiatorId;
    private String recipientId;
    private String initiatorPublicKey;
    private String recipientPublicKey;

    private String layer1Status;
    private String layer2Status;
    private String layer3Status;
    private String layer4Status;

    private String safetyCode;
    private String fullFingerprintHex;
    private Integer version;

    private Instant layer1VerifiedAt;
    private Instant layer2AcceptedAt;
    private Instant layer3ExchangedAt;
    private Instant layer4ConfirmedAt;
    private Instant completedAt;
}

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
public class EncryptedMessage {
    private String id;
    private String conversationId;
    private String senderId;
    private String recipientId;
    private MessageType messageType;
    private String ciphertext;
    private String initializationVector;
    private String mediaUrl;
    private boolean isRevoked;
    private Instant revokedAt;
    private int sequenceNumber;
    private Instant sentAt;
    private Instant deliveredAt;
    private Instant readAt;

    public enum MessageType {
        TEXT,
        IMAGE
    }
}

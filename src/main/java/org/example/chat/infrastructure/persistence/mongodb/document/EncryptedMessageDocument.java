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
@Document(collection = "encrypted_messages")
public class EncryptedMessageDocument {
    @Id
    private String id;

    @Indexed
    private String conversationId;

    @Indexed
    private String senderId;

    @Indexed
    private String recipientId;

    private String messageType;
    private String ciphertext;
    private String initializationVector;
    private String mediaUrl;
    private boolean isRevoked;
    private Instant revokedAt;
    private int sequenceNumber;

    @Indexed
    private Instant sentAt;

    private Instant deliveredAt;
    private Instant readAt;
}

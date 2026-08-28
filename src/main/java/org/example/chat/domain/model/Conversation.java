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
public class Conversation {
    private String id;
    private String participantAId; // Initiator
    private String participantBId; // Recipient
    private ConversationStatus status;
    private String lastMessageId;
    private String lastMessageSnippet;
    private Instant lastMessageAt;
    private Instant createdAt;
    private Instant updatedAt;

    public enum ConversationStatus {
        INITIATING,
        PENDING_ACCEPTANCE,
        HANDSHAKE_IN_PROGRESS,
        VERIFIED_ACTIVE,
        BLOCKED
    }
}

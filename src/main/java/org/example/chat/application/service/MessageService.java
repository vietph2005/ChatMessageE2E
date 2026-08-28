package org.example.chat.application.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.domain.exception.DomainException;
import org.example.chat.domain.model.Conversation;
import org.example.chat.domain.model.EncryptedMessage;
import org.example.chat.domain.repository.ConversationRepository;
import org.example.chat.domain.repository.MessageRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class MessageService {

    private final MessageRepository messageRepository;
    private final ConversationRepository conversationRepository;

    public EncryptedMessage sendEncryptedMessage(
            String senderId,
            String conversationId,
            String recipientId,
            EncryptedMessage.MessageType messageType,
            String ciphertext,
            String initializationVector,
            String mediaUrl) {

        Conversation conversation = conversationRepository.findById(conversationId)
                .orElseThrow(() -> new DomainException("CONVERSATION_NOT_FOUND", "Conversation not found: " + conversationId, HttpStatus.NOT_FOUND));

        // FR-006: Enforce 4-layer verification completion before messaging is permitted
        if (conversation.getStatus() != Conversation.ConversationStatus.VERIFIED_ACTIVE) {
            log.warn("[MessageSecurity] Blocked attempt to send message to unverified conversation: {} (status: {})",
                    conversationId, conversation.getStatus());
            throw new DomainException("UNVERIFIED_CONVERSATION", "Cannot transmit messages until all 4 verification layers are complete", HttpStatus.FORBIDDEN);
        }

        if (senderId == null || (!senderId.equals(conversation.getParticipantAId()) && !senderId.equals(conversation.getParticipantBId()))) {
            throw new DomainException("UNAUTHORIZED_SENDER", "You are not a participant in this conversation", HttpStatus.FORBIDDEN);
        }

        int nextSequence = messageRepository.countByConversationId(conversationId) + 1;

        EncryptedMessage message = EncryptedMessage.builder()
                .conversationId(conversationId)
                .senderId(senderId)
                .recipientId(recipientId)
                .messageType(messageType != null ? messageType : EncryptedMessage.MessageType.TEXT)
                .ciphertext(ciphertext)
                .initializationVector(initializationVector)
                .mediaUrl(mediaUrl)
                .isRevoked(false)
                .sequenceNumber(nextSequence)
                .sentAt(Instant.now())
                .build();

        EncryptedMessage saved = messageRepository.save(message);

        // Update conversation last message metadata (preserving Zero-Knowledge: snippet is opaque placeholder)
        conversation.setLastMessageId(saved.getId());
        conversation.setLastMessageSnippet(messageType == EncryptedMessage.MessageType.IMAGE ? "[Encrypted Image]" : "[Encrypted Message]");
        conversation.setLastMessageAt(saved.getSentAt());
        conversation.setUpdatedAt(Instant.now());
        conversationRepository.save(conversation);

        log.debug("[MessageService] Encrypted message persisted (ID: {}, Seq: {})", saved.getId(), saved.getSequenceNumber());
        return saved;
    }

    public EncryptedMessage revokeMessage(String userId, String conversationId, String messageId) {
        EncryptedMessage message = messageRepository.findById(messageId)
                .orElseThrow(() -> new DomainException("MESSAGE_NOT_FOUND", "Message not found: " + messageId, HttpStatus.NOT_FOUND));

        if (!userId.equals(message.getSenderId())) {
            throw new DomainException("UNAUTHORIZED_REVOCATION", "Only the sender can unsend this message", HttpStatus.FORBIDDEN);
        }

        message.setRevoked(true);
        message.setRevokedAt(Instant.now());
        message.setCiphertext("UNSENT_TOMBSTONE");
        message.setMediaUrl(null);

        EncryptedMessage updated = messageRepository.save(message);
        log.info("[MessageService] Message unsent for everyone (ID: {})", messageId);
        return updated;
    }

    public List<EncryptedMessage> getConversationMessages(String userId, String conversationId) {
        Conversation conversation = conversationRepository.findById(conversationId)
                .orElseThrow(() -> new DomainException("CONVERSATION_NOT_FOUND", "Conversation not found: " + conversationId, HttpStatus.NOT_FOUND));

        if (!userId.equals(conversation.getParticipantAId()) && !userId.equals(conversation.getParticipantBId())) {
            throw new DomainException("UNAUTHORIZED_ACCESS", "You are not a participant in this conversation", HttpStatus.FORBIDDEN);
        }

        return messageRepository.findByConversationIdOrderBySentAtAsc(conversationId);
    }
}

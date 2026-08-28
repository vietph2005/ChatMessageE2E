package org.example.chat.infrastructure.persistence.mongodb.repository;

import lombok.RequiredArgsConstructor;
import org.example.chat.domain.model.EncryptedMessage;
import org.example.chat.domain.repository.MessageRepository;
import org.example.chat.infrastructure.persistence.mongodb.document.EncryptedMessageDocument;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Component
@RequiredArgsConstructor
public class MessageRepositoryImpl implements MessageRepository {

    private final SpringDataMongoMessageRepository mongoRepository;

    @Override
    public EncryptedMessage save(EncryptedMessage m) {
        EncryptedMessageDocument doc = toDocument(m);
        EncryptedMessageDocument saved = mongoRepository.save(doc);
        return toDomain(saved);
    }

    @Override
    public Optional<EncryptedMessage> findById(String id) {
        return mongoRepository.findById(id).map(this::toDomain);
    }

    @Override
    public List<EncryptedMessage> findByConversationIdOrderBySentAtAsc(String conversationId) {
        return mongoRepository.findByConversationIdOrderBySentAtAsc(conversationId).stream()
                .map(this::toDomain)
                .collect(Collectors.toList());
    }

    @Override
    public int countByConversationId(String conversationId) {
        return mongoRepository.countByConversationId(conversationId);
    }

    private EncryptedMessageDocument toDocument(EncryptedMessage m) {
        return EncryptedMessageDocument.builder()
                .id(m.getId())
                .conversationId(m.getConversationId())
                .senderId(m.getSenderId())
                .recipientId(m.getRecipientId())
                .messageType(m.getMessageType() != null ? m.getMessageType().name() : null)
                .ciphertext(m.getCiphertext())
                .initializationVector(m.getInitializationVector())
                .mediaUrl(m.getMediaUrl())
                .isRevoked(m.isRevoked())
                .revokedAt(m.getRevokedAt())
                .sequenceNumber(m.getSequenceNumber())
                .sentAt(m.getSentAt())
                .deliveredAt(m.getDeliveredAt())
                .readAt(m.getReadAt())
                .build();
    }

    private EncryptedMessage toDomain(EncryptedMessageDocument doc) {
        return EncryptedMessage.builder()
                .id(doc.getId())
                .conversationId(doc.getConversationId())
                .senderId(doc.getSenderId())
                .recipientId(doc.getRecipientId())
                .messageType(doc.getMessageType() != null ? EncryptedMessage.MessageType.valueOf(doc.getMessageType()) : null)
                .ciphertext(doc.getCiphertext())
                .initializationVector(doc.getInitializationVector())
                .mediaUrl(doc.getMediaUrl())
                .isRevoked(doc.isRevoked())
                .revokedAt(doc.getRevokedAt())
                .sequenceNumber(doc.getSequenceNumber())
                .sentAt(doc.getSentAt())
                .deliveredAt(doc.getDeliveredAt())
                .readAt(doc.getReadAt())
                .build();
    }
}

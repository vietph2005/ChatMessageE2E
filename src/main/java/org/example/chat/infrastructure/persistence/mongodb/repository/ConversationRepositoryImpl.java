package org.example.chat.infrastructure.persistence.mongodb.repository;

import lombok.RequiredArgsConstructor;
import org.example.chat.domain.model.Conversation;
import org.example.chat.domain.repository.ConversationRepository;
import org.example.chat.infrastructure.persistence.mongodb.document.ConversationDocument;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Component
@RequiredArgsConstructor
public class ConversationRepositoryImpl implements ConversationRepository {

    private final SpringDataMongoConversationRepository mongoRepository;

    @Override
    public Conversation save(Conversation conversation) {
        ConversationDocument doc = toDocument(conversation);
        ConversationDocument saved = mongoRepository.save(doc);
        return toDomain(saved);
    }

    @Override
    public Optional<Conversation> findById(String id) {
        return mongoRepository.findById(id).map(this::toDomain);
    }

    @Override
    public Optional<Conversation> findBetweenParticipants(String participantAId, String participantBId) {
        return mongoRepository.findBetween(participantAId, participantBId).map(this::toDomain);
    }

    @Override
    public List<Conversation> findUserConversations(String userId) {
        return mongoRepository.findByUser(userId).stream()
                .map(this::toDomain)
                .collect(Collectors.toList());
    }

    private ConversationDocument toDocument(Conversation c) {
        return ConversationDocument.builder()
                .id(c.getId())
                .participantAId(c.getParticipantAId())
                .participantBId(c.getParticipantBId())
                .status(c.getStatus() != null ? c.getStatus().name() : null)
                .lastMessageId(c.getLastMessageId())
                .lastMessageSnippet(c.getLastMessageSnippet())
                .lastMessageAt(c.getLastMessageAt())
                .createdAt(c.getCreatedAt())
                .updatedAt(c.getUpdatedAt())
                .build();
    }

    private Conversation toDomain(ConversationDocument doc) {
        return Conversation.builder()
                .id(doc.getId())
                .participantAId(doc.getParticipantAId())
                .participantBId(doc.getParticipantBId())
                .status(doc.getStatus() != null ? Conversation.ConversationStatus.valueOf(doc.getStatus()) : null)
                .lastMessageId(doc.getLastMessageId())
                .lastMessageSnippet(doc.getLastMessageSnippet())
                .lastMessageAt(doc.getLastMessageAt())
                .createdAt(doc.getCreatedAt())
                .updatedAt(doc.getUpdatedAt())
                .build();
    }
}
